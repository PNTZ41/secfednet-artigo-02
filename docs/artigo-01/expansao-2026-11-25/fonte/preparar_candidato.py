"""Materializa somente protocolo CANDIDATO; sexta serve apenas à auditoria."""
import argparse
import csv
import hashlib
import io
import json
import resource
import sys
import time
import zipfile
from array import array
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "fontes"))
import auditar_split as audit

SPLITS = audit.SPLITS
TOTAIS = [1184424, 360078, 543490]


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def harray(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def gravar(p, x):
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def codificar(a, pool):
    # Reusa a canonicalização do piloto em cada dtype efetivamente auditado.
    c = np.array(a, order="C", copy=True)
    c[c == 0] = 0.0
    return np.asarray([audit.intern(pool, r.tobytes()) for r in c], dtype=np.int64)


def colisao_adicional(a, b, tipo, ma, mb):
    ra, rb = a["vetor_float64"][ma], b["vetor_float64"][mb]
    ka, kb = a[tipo][ma], b[tipo][mb]
    comuns = np.intersect1d(ka, kb)
    ia, ib = np.searchsorted(comuns, ka), np.searchsorted(comuns, kb)
    mina = np.full(len(comuns), np.iinfo(np.int64).max, dtype=np.int64)
    minb = mina.copy()
    maxa, maxb = np.full(len(comuns), -1, dtype=np.int64), np.full(len(comuns), -1, dtype=np.int64)
    np.minimum.at(mina, ia, ra); np.maximum.at(maxa, ia, ra)
    np.minimum.at(minb, ib, rb); np.maximum.at(maxb, ib, rb)
    na, nb = np.bincount(ia, minlength=len(comuns)), np.bincount(ib, minlength=len(comuns))
    ua, ca = np.unique(ra, return_counts=True)
    ub, cb = np.unique(rb, return_counts=True)
    _, ai, bi = np.intersect1d(ua, ub, return_indices=True)
    pares_iguais_raw = int((ca[ai] * cb[bi]).sum())
    return {"chaves_com_colisao_adicional": int((np.minimum(mina, minb) != np.maximum(maxa, maxb)).sum()),
        "linhas_a_colisao_adicional": int(((minb[ia] != maxb[ia]) | (ra != minb[ia])).sum()),
        "linhas_b_colisao_adicional": int(((mina[ib] != maxa[ib]) | (rb != mina[ib])).sum()),
        "pares_adicionais_raw_diferente": int((na * nb).sum()) - pares_iguais_raw}


def preparar(arquivo, saida):
    inicio = time.monotonic()
    assert sha(arquivo) == audit.SHA_ZIP
    ref = json.loads((RAIZ / "auditoria_referencia/resultado.json").read_text())
    features = ref["ordem_features"]
    assert features == json.loads((RAIZ / "contrato_features_referencia.json").read_text())["ordem_features"]
    classes = ["BENIGN"] + sorted(c for c in ref["classes_nominais"] if c != "BENIGN")
    saida.mkdir(parents=True, exist_ok=False)
    dados = saida / "dados"
    dados.mkdir()
    xraw = [np.lib.format.open_memmap(dados / f"{s}_bruto_f64.npy", mode="w+", dtype="<f8", shape=(n, 81))
            for s, n in zip(SPLITS, TOTAIS, strict=True)]
    registros = [array("q") for _ in SPLITS]
    capturas = [array("b") for _ in SPLITS]
    labels = [array("h") for _ in SPLITS]
    rawcodes = [array("q") for _ in SPLITS]
    pool, pos, tentativas, exclusoes = {}, [0, 0, 0], {}, []
    arqs = []
    with zipfile.ZipFile(arquivo) as z:
        for dia, nome in enumerate(audit.DIAS):
            split = 0 if dia < 3 else dia - 2
            ti = []
            with z.open(nome) as raw:
                digest = audit.LeituraComHash(raw)
                with io.TextIOWrapper(io.BufferedReader(digest), encoding="utf-8-sig", newline="") as f:
                    reader = csv.reader(f)
                    header = next(reader)
                    assert len(header) == len(set(header)) == 91
                    assert [c for c in header if c not in audit.META + audit.ROTULOS] == features
                    fi = [header.index(c) for c in features]
                    li, ai = header.index("Label"), header.index("Attempted Category")
                    for numero, row in enumerate(reader, 1):
                        assert len(row) == 91
                        label = row[li].strip()
                        if row[ai].strip() != "-1" or label.endswith(" - Attempted"):
                            ti.append(numero)
                            continue
                        vals = np.asarray([float(row[i]) for i in fi], dtype="<f8")
                        bad = ~np.isfinite(vals)
                        if bad.any():
                            exclusoes.append({"arquivo": nome, "registro_csv1": numero, "rotulo": label,
                                              "features": [features[i] for i in np.flatnonzero(bad)]})
                            continue
                        key = audit.vetor(vals)
                        xraw[split][pos[split]] = vals
                        registros[split].append(numero)
                        capturas[split].append(dia)
                        labels[split].append(classes.index(label))
                        rawcodes[split].append(audit.intern(pool, key))
                        pos[split] += 1
                        if numero % 100000 == 0:
                            print(nome, numero, flush=True)
            h = digest.hash.hexdigest()
            prev = next(c for c in ref["capturas"] if c["arquivo"] == nome)
            assert h == prev["csv_sha256"]
            nfinite = sum(c == dia for c in capturas[split])
            removidos = [e["registro_csv1"] for e in exclusoes if e["arquivo"] == nome]
            finitos = np.asarray(registros[split])[np.asarray(capturas[split]) == dia]
            assert np.array_equal(np.sort(np.concatenate([finitos, ti, removidos]).astype(np.int64)),
                                  np.arange(1, prev["brutas"] + 1))
            tentativas[nome] = np.asarray(ti, dtype=np.int64)
            arqs.append({"arquivo": nome, "sha256": h, "linhas_finitas_nao_attempted": nfinite,
                         "attempted": len(ti), "nao_finitos": len(removidos)})
            print(nome, "materializado", nfinite, flush=True)
    assert pos == TOTAIS
    assert len(exclusoes) == 5 and all(e["rotulo"] == "BENIGN" for e in exclusoes)
    del pool
    d = [{"rotulo": np.asarray(labels[i]), "vetor_float64": np.asarray(rawcodes[i])} for i in range(3)]
    masks = [np.ones(TOTAIS[0], dtype=bool),
             ~np.isin(d[1]["vetor_float64"], d[0]["vetor_float64"]),
             ~np.isin(d[2]["vetor_float64"], np.concatenate([d[0]["vetor_float64"], d[1]["vetor_float64"]]))]
    assert [int(m.sum()) for m in masks] == [1184424, 328429, 429801]
    gravar(saida / "exclusoes_qualidade.json", exclusoes)
    arrays = {}
    impactos = []
    for i, s in enumerate(SPLITS):
        y = (d[i]["rotulo"] != 0).astype(np.uint8)
        np.save(dados / f"{s}_y.npy", y)
        np.save(dados / f"{s}_nominal.npy", d[i]["rotulo"])
        arrays.update({f"{s}_captura_idx0": np.asarray(capturas[i]), f"{s}_csv_registro1": np.asarray(registros[i]),
            f"{s}_rotulo_nominal_idx0": d[i]["rotulo"], f"{s}_y_binario": y,
            f"{s}_principal": np.ones(TOTAIS[i], dtype=bool), f"{s}_sensibilidade_raw64": masks[i]})
        for c, label in enumerate(classes):
            a, b = int((d[i]["rotulo"] == c).sum()), int(((d[i]["rotulo"] == c) & masks[i]).sum())
            impactos.append({"conjunto": s, "tipo": label, "principal": a, "sensibilidade": b,
                             "excluidas_sensibilidade": a - b, "pct_tipo_excluido": 100 * (a-b)/a if a else None})
    # Uma única transformação: treino idêntico no principal e na sensibilidade.
    media = xraw[0].mean(axis=0, dtype=np.float64)
    escala = xraw[0].std(axis=0, dtype=np.float64, ddof=0)
    constantes = np.flatnonzero(escala == 0).tolist()
    escala[escala == 0] = 1.0
    np.savez_compressed(saida / "preprocessamento.npz", media=media, escala=escala, ordem_features=features)
    for tipo, dtype in [("normalizado_float64", np.dtype("<f8")), ("modelo_float32", np.dtype("<f4"))]:
        pool = {}
        for i, s in enumerate(SPLITS):
            cod = np.empty(TOTAIS[i], dtype=np.int64)
            out = np.lib.format.open_memmap(dados / f"{s}_x_f32.npy", mode="w+", dtype="<f4", shape=(TOTAIS[i],81)) if dtype.itemsize == 4 else None
            for start in range(0, TOTAIS[i], 32768):
                end = min(start + 32768, TOTAIS[i])
                x = ((xraw[i][start:end] - media) / escala).astype(dtype)
                assert np.isfinite(x).all()
                cod[start:end] = codificar(x, pool)
                if out is not None:
                    out[start:end] = x
            if out is not None:
                out.flush()
            d[i][tipo] = cod
            print(s, tipo, "auditado", flush=True)
        del pool
    inter, conf = [], []
    for cenario in ["principal", "sensibilidade_raw64"]:
        ds = d if cenario == "principal" else [{k: v[masks[i]] for k,v in x.items()} for i,x in enumerate(d)]
        for i,jj in audit.PARES:
            for tipo in ["vetor_float64", "normalizado_float64", "modelo_float32"]:
                r,c,_,ma,mb = audit.cruzar(ds[i], ds[jj], tipo, classes)
                extra = colisao_adicional(ds[i], ds[jj], tipo, ma, mb)
                if cenario == "sensibilidade_raw64" and tipo == "vetor_float64":
                    assert r["chaves_comuns"] == 0
                if cenario == "principal" and tipo == "vetor_float64":
                    prev = next(p for p in ref["cruzamentos"] if p["par"] == f"{SPLITS[i]}_x_{SPLITS[jj]}" and p["tipo"] == tipo)
                    assert all(r[k] == prev[k] for k in ["chaves_comuns","linhas_a","linhas_b"])
                inter.append({"cenario": cenario,"par": f"{SPLITS[i]}_x_{SPLITS[jj]}",**r,**extra})
                conf.extend({"cenario": cenario,"par":f"{SPLITS[i]}_x_{SPLITS[jj]}","representacao":tipo,**v} for v in c)
                print(cenario, SPLITS[i], SPLITS[jj], tipo, r["chaves_comuns"], "adicionais", extra["chaves_com_colisao_adicional"], flush=True)
    for i,s in enumerate(SPLITS):
        arrays[f"{s}_raw_code"] = d[i]["vetor_float64"]
        arrays[f"{s}_norm64_code"] = d[i]["normalizado_float64"]
        arrays[f"{s}_modelo32_code"] = d[i]["modelo_float32"]
    for nome, indices in tentativas.items():
        arrays[f"{nome[:-4]}_attempted_csv1"] = indices
    np.savez_compressed(saida / "manifesto_indices_candidato.npz", **arrays)
    audit.tabela(saida / "impacto_sensibilidade_por_tipo.csv", impactos)
    audit.tabela(saida / "intersecoes_representacoes.csv", inter)
    audit.tabela(saida / "conflitos_representacoes.csv", conf)
    for a in xraw:
        a.flush()
    dados_hash = {str(p.relative_to(saida)):sha(p) for p in dados.iterdir() if p.is_file()}
    gravar(saida / "manifesto_candidato.json", {"estado":"CANDIDATO_NAO_FINAL", "classes":{"0":"BENIGN","1":"ATTACK"},
        "zip_sha256":audit.SHA_ZIP,"arquivos":arqs,"ordem_features":features,"classes_nominais":classes,
        "principal":dict(zip(SPLITS,TOTAIS)),"sensibilidade_raw64":dict(zip(SPLITS,[int(m.sum()) for m in masks])),
        "indice_semantica":"arrays alinhados ao principal finito; captura_idx0 referencia DIAS; csv_registro1 exclui cabecalho; mascaras bool nao sao protocolo final",
        "capturas_ordem":audit.DIAS,"ordem_linhas":"captura e ordem original de registro; sem ordenacao por timestamp",
        "preprocessamento":{"ajustado_em":"treino principal = treino sensibilidade", "media_desvio_dtype":"float64","ddof":0,
            "escala_zero_vira":1,"colunas_constantes":constantes,"entrada_modelo":"float32","clipping":"nenhum"},
        "indices_sha256":sha(saida/'manifesto_indices_candidato.npz'),"preprocessamento_sha256":sha(saida/'preprocessamento.npz'),
        "dados_hash":dados_hash,"avaliacao_sexta":"PROIBIDA nesta rodada; dados apenas para qualidade, manifesto e intersecoes",
        "exclusao_grupo":"apenas diagnostico da auditoria_referencia; nao aplicada", "rotulos_conflitantes":"preservados na fonte e nos arrays nominais",
        "tempo_s":time.monotonic()-inicio,"pico_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
    print("MANIFESTO CANDIDATO CONCLUÍDO", flush=True)


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("zip",type=Path);p.add_argument("saida_nova",type=Path)
    a=p.parse_args();preparar(a.zip,a.saida_nova)
