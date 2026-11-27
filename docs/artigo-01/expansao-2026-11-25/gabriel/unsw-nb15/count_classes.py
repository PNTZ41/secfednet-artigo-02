#!/usr/bin/env python3
"""SecFedNet: count UNSW-NB15 classes from original ZIP or CSV directory."""
import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter
from pathlib import Path

SOURCE = "https://research.unsw.edu.au/projects/unsw-nb15-dataset"
SCHEMA = """id dur proto service state spkts dpkts sbytes dbytes rate sttl dttl sload dload sloss dloss sinpkt dinpkt sjit djit swin stcpb dtcpb dwin tcprtt synack ackdat smean dmean trans_depth response_body_len ct_srv_src ct_state_ttl ct_dst_ltm ct_src_dport_ltm ct_dst_sport_ltm ct_dst_src_ltm is_ftp_login ct_ftp_cmd ct_flw_http_mthd ct_src_ltm ct_srv_dst is_sm_ips_ports attack_cat label""".split()
EXPECTED = {
    "Normal": (56000, 37000), "Analysis": (2000, 677),
    "Backdoor": (1746, 583), "DoS": (12264, 4089),
    "Exploits": (33393, 11132), "Fuzzers": (18184, 6062),
    "Generic": (40000, 18871), "Reconnaissance": (10491, 3496),
    "Shellcode": (1133, 378), "Worms": (130, 44),
}

def load(source, name):
    if source.is_dir():
        return (source / name).read_bytes()
    with zipfile.ZipFile(source) as archive:
        members = [n for n in archive.namelist() if Path(n).name == name]
        if len(members) != 1:
            raise ValueError(f"Expected exactly one {name}; found {members}")
        return archive.read(members[0])

def audit(data, index):
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""))
    if reader.fieldnames != SCHEMA:
        raise ValueError("Unexpected CSV schema")
    counts, binary, ids = Counter(), Counter(), set()
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise ValueError(f"Malformed row {reader.line_num}")
        cat, label = row["attack_cat"], row["label"]
        if cat not in EXPECTED or label not in ("0", "1"):
            raise ValueError(f"Unknown label at row {reader.line_num}")
        if (cat == "Normal") != (label == "0"):
            raise ValueError(f"Inconsistent label at row {reader.line_num}")
        record_id = int(row["id"])
        if record_id in ids:
            raise ValueError(f"Duplicate ID at row {reader.line_num}")
        ids.add(record_id)
        counts[cat] += 1
        binary[label] += 1
    if dict(counts) != {k: v[index] for k, v in EXPECTED.items()}:
        raise ValueError(f"Unexpected distribution: {dict(counts)}")
    return {"rows": sum(counts.values()), "columns": SCHEMA,
            "counts": dict(counts), "binary": dict(binary),
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data), "duplicates": 0, "inconsistent": 0}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="ZIP archive or directory containing both CSVs")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.out_dir.exists():
        raise FileExistsError(f"Output already exists: {args.out_dir}")
    splits = {}
    for index, split in enumerate(("training", "testing")):
        name = f"UNSW_NB15_{split}-set.csv"
        splits[split] = audit(load(args.source, name), index)
        splits[split]["filename"] = name
    args.out_dir.mkdir(parents=True, exist_ok=False)
    for task, key, classes in (("multiclass", "counts", EXPECTED),
                               ("binary", "binary", ("0", "1"))):
        with (args.out_dir / f"class_counts_{task}.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["class", "train", "test", "total"])
            for cat in classes:
                a, b = (splits[s][key][cat] for s in ("training", "testing"))
                writer.writerow([cat, a, b, a+b])
            a, b = (splits[s]["rows"] for s in ("training", "testing"))
            writer.writerow(["TOTAL", a, b, a+b])
    report = {"project": "SecFedNet", "dataset": "UNSW-NB15",
              "official_source": SOURCE, "input": args.source.name,
              "provenance_note": "Local files supplied by user; upstream authenticity not independently verified.",
              "preprocessing": "none", "feature_count": 42,
              "splits": splits, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.out_dir / "dataset_audit.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    with (args.out_dir / "SHA256SUMS").open("w", encoding="utf-8") as f:
        for path in sorted(args.out_dir.glob("*")):
            if path.name != "SHA256SUMS":
                f.write(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n")
    print(f"Audit passed: {args.out_dir}")

if __name__ == "__main__":
    main()
