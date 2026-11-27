"""Audita capturas CICIDS2017 sem normalizar, treinar, excluir dados ou salvar índices."""
import argparse
import csv
import hashlib
import io
import ipaddress
import json
import platform
import resource
import struct
import time
import zipfile
from array import array
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

SHA_ZIP = "97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883"
DIAS = ["monday.csv", "tuesday.csv", "wednesday.csv", "thursday.csv", "friday.csv"]
SPLITS = ["treino", "validacao", "teste"]
META = ("id", "Flow ID", "Src IP", "Src Port", "Dst IP", "Dst Port", "Protocol", "Timestamp")
ROTULOS = ("Label", "Attempted Category")
TIPOS = ["id_local_escopado", "flow_id_direcional", "grupo_bidirecional", "vetor_float64", "flow_id_timestamp"]
PARES = [(0, 1), (0, 2), (1, 2)]
EPOCH = datetime(1970, 1, 1)
MICROSSEGUNDO = timedelta(microseconds=1)


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def escrever(p, j):
    p.write_text(json.dumps(j, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def tabela(p, rows):
    assert rows
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def pct(n, total):
    return 100 * n / total if total else None


def intern(d, chave):
    valor = d.get(chave)
    if valor is None:
        valor = len(d)
        d[chave] = valor
    return valor


class LeituraComHash(io.RawIOBase):
    def __init__(self, stream):
        self.stream, self.hash = stream, hashlib.sha256()

    def readable(self):
        return True

    def readinto(self, buffer):
        dados = self.stream.read(len(buffer))
        self.hash.update(dados)
        buffer[:len(dados)] = dados
        return len(dados)


class Catalogo:
    def __init__(self):
        self.vetores, self.grupos, self.fluxos, self.ips = {}, {}, {}, {}
        self.rotulos = {"BENIGN": 0}

    def ip_valido(self, ip):
        if ip not in self.ips:
            try:
                ipaddress.ip_address(ip)
                self.ips[ip] = True
            except ValueError:
                self.ips[ip] = False
        return self.ips[ip]


def vetor(valores):
    """Retorna bytes float64 little-endian, sem arredondar; inválidos não têm chave."""
    a = np.asarray(valores, dtype="<f8")
    if not np.isfinite(a).all():
        return None
    a[a == 0.0] = 0.0
    return a.tobytes()


def ingerir(nome, header, leitor, catalogo, features):
    dia = DIAS.index(nome)
    campos = {n: header.index(n) for n in META + ROTULOS}
    fi = [header.index(n) for n in features]
    assert len(fi) == 81
    pack = struct.Struct("<81d").pack
    codigos = {k: array("q") for k in TIPOS if k != "flow_id_timestamp"}
    labels, tempos, ids_brutos = array("h"), array("q"), array("q")
    qualidade = np.zeros((81, 3), dtype=np.int64)
    linha_qualidade, problemas, tentativas, nominais = Counter(), Counter(), Counter(), Counter()
    total = 0
    ids_sequenciais = True
    tmin = tmax = None
    for numero, row in enumerate(leitor, 1):
        total += 1
        if len(row) != len(header):
            raise ValueError(f"{nome} registro {numero}: largura {len(row)}")
        try:
            ident = int(row[campos["id"]])
            if not 0 <= ident < 1_000_000_000:
                raise ValueError()
        except ValueError:
            ident = -1
            problemas["id_invalido_bruto"] += 1
        ids_brutos.append(ident)
        ids_sequenciais &= ident == numero
        try:
            t = datetime.fromisoformat(row[campos["Timestamp"]])
            if t.tzinfo is not None or t.date().isoformat() != f"2017-07-0{3 + dia}":
                raise ValueError()
            # Mesmo pressuposto UTC do piloto; datetime sem offset não prova o fuso.
            micros = (t - EPOCH) // MICROSSEGUNDO
            tmin = t if tmin is None or t < tmin else tmin
            tmax = t if tmax is None or t > tmax else tmax
        except ValueError:
            problemas["timestamp_invalido_bruto"] += 1
            micros = -1
        label = row[campos["Label"]].strip()
        flag = row[campos["Attempted Category"]].strip()
        attempt = flag != "-1" or label.endswith(" - Attempted")
        problemas["flag_sufixo_attempted_divergentes"] += int((flag != "-1") != label.endswith(" - Attempted"))
        if attempt:
            tentativas[label] += 1
            continue
        if not label:
            raise ValueError(f"{nome} registro {numero}: rótulo vazio; binário indeterminado")
        nominais[label] += 1
        labels.append(intern(catalogo.rotulos, label))
        tempos.append(micros)
        codigos["id_local_escopado"].append(dia * 1_000_000_000 + ident if ident >= 0 else -1)
        valores = []
        flags = [False, False, False]
        for j, coluna in enumerate(fi):
            s = row[coluna].strip()
            if not s:
                qualidade[j, 0] += 1
                flags[0] = True
                valores.append(0.0)
                continue
            try:
                v = float(s)
            except ValueError:
                qualidade[j, 1] += 1
                flags[1] = True
                valores.append(0.0)
                continue
            if not (-float("inf") < v < float("inf")):
                qualidade[j, 2] += 1
                flags[2] = True
            valores.append(0.0 if v == 0.0 else v)
        for k, ruim in zip(["vazio", "invalido", "nao_finito"], flags, strict=True):
            linha_qualidade[k] += int(ruim)
        ruim = any(flags)
        linha_qualidade["qualquer_problema"] += int(ruim)
        codigos["vetor_float64"].append(-1 if ruim else intern(catalogo.vetores, pack(*valores)))
        md = {n: row[campos[n]] for n in META}
        for n, s in md.items():
            problemas[f"vazio_{n}"] += int(not s.strip())
            problemas[f"espaco_lateral_{n}"] += int(s != s.strip())
        valido = True
        try:
            origem = (md["Src IP"], int(md["Src Port"]))
            destino = (md["Dst IP"], int(md["Dst Port"]))
            protocolo = int(md["Protocol"])
            if not (0 <= origem[1] <= 65535 and 0 <= destino[1] <= 65535 and 0 <= protocolo <= 255
                    and catalogo.ip_valido(origem[0]) and catalogo.ip_valido(destino[0])):
                raise ValueError()
            # Mesma chave literal do piloto: protocolo e endpoints ordenados, sem direção.
            g = (protocolo, *sorted((origem, destino)))
        except ValueError:
            valido = False
            problemas["grupo_metadados_invalidos"] += 1
        codigos["grupo_bidirecional"].append(intern(catalogo.grupos, g) if valido else -1)
        try:
            ip1, ip2, p1, p2, proto = md["Flow ID"].split("-")
            parsed = (ip1, ip2, int(p1), int(p2), int(proto))
            direto = (origem[0], destino[0], origem[1], destino[1], protocolo) if valido else None
            reverso = (destino[0], origem[0], destino[1], origem[1], protocolo) if valido else None
            if parsed not in (direto, reverso):
                raise ValueError()
            problemas["flow_id_sentido_reverso"] += int(parsed == reverso and parsed != direto)
            chave_flow = f"{ip1}-{ip2}-{int(p1)}-{int(p2)}-{int(proto)}"
            flow = intern(catalogo.fluxos, chave_flow)
        except ValueError:
            flow = -1
            problemas["flow_id_nao_interpretavel_ou_inconsistente"] += 1
        codigos["flow_id_direcional"].append(flow)
        if numero % 100000 == 0:
            print(nome, numero, "registros lidos", flush=True)
    arrays = {k: np.asarray(v) for k, v in codigos.items()}
    arrays.update(rotulo=np.asarray(labels), tempo=np.asarray(tempos))
    raws = np.asarray(ids_brutos)
    fid = arrays["flow_id_direcional"]
    valid = (fid >= 0) & (arrays["tempo"] >= 0)
    unicos, inv, cont = np.unique(fid[valid], return_inverse=True, return_counts=True)
    mins = np.full(len(unicos), np.iinfo(np.int64).max, dtype=np.int64)
    maxs = np.full(len(unicos), -1, dtype=np.int64)
    np.minimum.at(mins, inv, arrays["tempo"][valid])
    np.maximum.at(maxs, inv, arrays["tempo"][valid])
    stats = {"arquivo": nome, "conjunto": SPLITS[0 if dia < 3 else dia - 2], "brutas": total,
        "nao_attempted": len(labels), "attempted": dict(tentativas), "classes": dict(nominais),
        "qualidade_linhas": dict(linha_qualidade), "problemas_metadados": dict(problemas),
        "id_min": int(raws.min()), "id_max": int(raws.max()), "ids_distintos": int(np.unique(raws).size),
        "id_igual_numero_registro_em_todas_linhas": bool(ids_sequenciais),
        "primeiro_timestamp": tmin.isoformat() if tmin else None,
        "ultimo_timestamp": tmax.isoformat() if tmax else None,
        "flow_ids_distintos": len(unicos), "flow_ids_com_mais_um_timestamp": int((mins != maxs).sum()),
        "linhas_nesses_flow_ids": int(cont[mins != maxs].sum())}
    print(nome, "concluído:", len(labels), "não-Attempted", flush=True)
    return arrays, stats, qualidade


def chaves(d, tipo):
    if tipo != "flow_id_timestamp":
        return d[tipo], d[tipo] >= 0
    # Âncora adicional de evento; separada dos vetores, não é feature.
    a = np.empty(len(d["rotulo"]), dtype=[("flow", "<i8"), ("tempo", "<i8")])
    a["flow"], a["tempo"] = d["flow_id_direcional"], d["tempo"]
    return a.view("V16").ravel(), (a["flow"] >= 0) & (a["tempo"] >= 0)


def cruzar(a, b, tipo, classes):
    ka, va = chaves(a, tipo)
    kb, vb = chaves(b, tipo)
    comuns = np.intersect1d(ka[va], kb[vb])
    ma, mb = va & np.isin(ka, comuns), vb & np.isin(kb, comuns)
    la = np.zeros((len(comuns), len(classes)), dtype=np.int64)
    lb = np.zeros_like(la)
    np.add.at(la, (np.searchsorted(comuns, ka[ma]), a["rotulo"][ma]), 1)
    np.add.at(lb, (np.searchsorted(comuns, kb[mb]), b["rotulo"][mb]), 1)
    result = {"tipo": tipo, "chaves_comuns": len(comuns), "linhas_a": int(ma.sum()),
              "linhas_b": int(mb.sum()), "pct_linhas_a": pct(int(ma.sum()), len(ma)),
              "pct_linhas_b": pct(int(mb.sum()), len(mb)),
              "linhas_sem_chave_a": int((~va).sum()), "linhas_sem_chave_b": int((~vb).sum())}
    conflitos, combinacoes = [], []
    for escala, x, y, nomes in [("nominal", la, lb, classes),
            ("binario", np.column_stack((la[:, 0], la[:, 1:].sum(1))),
             np.column_stack((lb[:, 0], lb[:, 1:].sum(1))), ["BENIGN", "ATTACK"])]:
        na, nb = x.sum(1), y.sum(1)
        pares_opostos = na * nb - (x * y).sum(1)
        com_conflito = pares_opostos > 0
        conflitos.append({"escala": escala, "chaves_com_conflito": int(com_conflito.sum()),
            "linhas_a_em_chaves_conflitantes": int(na[com_conflito].sum()),
            "linhas_b_em_chaves_conflitantes": int(nb[com_conflito].sum()),
            "linhas_a_com_rotulo_oposto_no_outro_lado": int((x * ((nb[:, None] - y) > 0)).sum()),
            "linhas_b_com_rotulo_oposto_no_outro_lado": int((y * ((na[:, None] - x) > 0)).sum()),
            "pares_de_linhas_com_rotulos_diferentes": int(pares_opostos.sum())})
        combinados = x.T @ y
        for i, n in enumerate(nomes):
            for j, m in enumerate(nomes):
                if i != j and combinados[i, j]:
                    combinacoes.append({"escala": escala, "rotulo_a": n, "rotulo_b": m,
                                        "pares_linhas": int(combinados[i, j])})
    return result, conflitos, combinacoes, ma, mb


def suporte(d, mascara, classes):
    contagens = np.bincount(d["rotulo"][mascara], minlength=len(classes))
    return [("nominal", c, int(n)) for c, n in zip(classes, contagens, strict=True)] + [
        ("binario", "BENIGN", int(contagens[0])), ("binario", "ATTACK", int(contagens[1:].sum()))]


def simular(datasets, classes):
    cenarios = {"sem_exclusao": [np.ones(len(d["rotulo"]), dtype=bool) for d in datasets]}
    cenarios["qualidade_numerica_todos_conjuntos"] = [d["vetor_float64"] >= 0 for d in datasets]
    for tipo in ["vetor_float64", "grupo_bidirecional"]:
        mascaras = [np.ones(len(datasets[0]["rotulo"]), dtype=bool)]
        anteriores = np.array([], dtype=np.int64)
        for i, d in enumerate(datasets):
            k, v = chaves(d, tipo)
            if i:
                mascaras.append(~(v & np.isin(k, anteriores)))
            anteriores = np.union1d(anteriores, k[v])
        cenarios[f"sequencial_{tipo}"] = mascaras
        for i, j in PARES:
            k, v = chaves(datasets[i], tipo)
            l, w = chaves(datasets[j], tipo)
            masks = [np.ones(len(d["rotulo"]), dtype=bool) for d in datasets]
            masks[j] &= ~(w & np.isin(l, k[v]))
            cenarios[f"par_{SPLITS[i]}_x_{SPLITS[j]}_{tipo}"] = masks
    rows = []
    for nome, masks in cenarios.items():
        for s, d, keep in zip(SPLITS, datasets, masks, strict=True):
            original = suporte(d, np.ones(len(keep), dtype=bool), classes)
            novo = suporte(d, keep, classes)
            for (escala, c, antes), (_, _, depois) in zip(original, novo, strict=True):
                excluido = antes - depois
                rows.append({"cenario": nome, "conjunto": s, "escala": escala, "classe": c,
                    "antes": antes, "depois": depois, "excluidas": excluido,
                    "pct_da_classe_excluida": pct(excluido, antes),
                    "pct_composicao_antes": pct(antes, len(keep)),
                    "pct_composicao_depois": pct(depois, int(keep.sum())),
                    "suporte_zerou": antes > 0 and depois == 0,
                    "perda_ge_10pct": antes > 0 and excluido / antes >= .1,
                    "perda_ge_50pct": antes > 0 and excluido / antes >= .5,
                    "suporte_final_menor_100": 0 < depois < 100})
    # Não escreve máscaras ou índices: todas as saídas são agregadas.
    for tipo in ["vetor_float64", "grupo_bidirecional"]:
        masks = cenarios[f"sequencial_{tipo}"]
        for i, j in PARES:
            a, va = chaves(datasets[i], tipo)
            b, vb = chaves(datasets[j], tipo)
            assert not np.intersect1d(a[va & masks[i]], b[vb & masks[j]]).size
    return rows


def analisar(datasets, classes, destino):
    pares, conflitos, combinacoes, afetadas, unicos = [], [], [], [], []
    for s, d in zip(SPLITS, datasets, strict=True):
        for tipo in TIPOS:
            k, v = chaves(d, tipo)
            u, c = np.unique(k[v], return_counts=True)
            unicos.append({"conjunto": s, "tipo": tipo, "linhas_com_chave": int(v.sum()),
                "chaves_distintas": len(u), "chaves_repetidas": int((c > 1).sum()),
                "linhas_em_chaves_repetidas": int(c[c > 1].sum()), "excesso_de_linhas": int((c - 1).sum())})
    for i, j in PARES:
        for tipo in TIPOS:
            par = f"{SPLITS[i]}_x_{SPLITS[j]}"
            r, c, comb, ma, mb = cruzar(datasets[i], datasets[j], tipo, classes)
            pares.append({"par": par, **r})
            conflitos.extend({"par": par, "tipo": tipo, **v} for v in c)
            combinacoes.extend({"par": par, "tipo": tipo, **v} for v in comb)
            for lado, d, mask in [("a", datasets[i], ma), ("b", datasets[j], mb)]:
                for (escala, cl, total), (_, _, n) in zip(suporte(d, np.ones(len(mask), dtype=bool), classes),
                                                        suporte(d, mask, classes), strict=True):
                    afetadas.append({"par": par, "tipo": tipo, "lado": lado,
                        "conjunto": SPLITS[i if lado == "a" else j], "escala": escala, "classe": cl,
                        "total_classe": total, "linhas_afetadas": n, "pct_classe_afetada": pct(n, total)})
            print(par, tipo, "chaves", r["chaves_comuns"], "linhas", r["linhas_a"], r["linhas_b"], flush=True)
    simulacoes = simular(datasets, classes)
    tabela(destino / "cruzamentos.csv", pares)
    tabela(destino / "conflitos.csv", conflitos)
    # É possível não haver conflitos em um fixture; mantém cabeçalho explícito.
    if combinacoes:
        tabela(destino / "pares_rotulos_conflitantes.csv", combinacoes)
    else:
        (destino / "pares_rotulos_conflitantes.csv").write_text("par,tipo,escala,rotulo_a,rotulo_b,pares_linhas\n")
    tabela(destino / "linhas_afetadas_por_classe.csv", afetadas)
    tabela(destino / "chaves_por_conjunto.csv", unicos)
    tabela(destino / "simulacoes_por_classe.csv", simulacoes)
    return pares, conflitos, simulacoes


def auditar(args):
    inicio = time.monotonic()
    assert sha(args.zip) == SHA_ZIP
    previo = json.loads(args.inventario_anterior.read_text())
    contrato = json.loads(args.contrato.read_text())
    features = previo["ordem_features"]
    assert features == contrato["ordem_features"] and len(features) == len(set(features)) == 81
    args.saida.mkdir(parents=True, exist_ok=False)
    cat = Catalogo()
    dias, stats, qualidades = [], [], []
    with zipfile.ZipFile(args.zip) as z:
        assert set(n for n in z.namelist() if n.endswith('.csv')) == set(DIAS)
        header_ref = None
        for n in DIAS:
            with z.open(n) as raw:
                h = LeituraComHash(raw)
                with io.TextIOWrapper(io.BufferedReader(h), encoding="utf-8-sig", newline="") as f:
                    reader = csv.reader(f)
                    header = next(reader)
                    assert len(header) == len(set(header)) == 91
                    assert [c for c in header if c not in META + ROTULOS] == features
                    if header_ref is None:
                        header_ref = header
                    assert header == header_ref
                    d, s, q = ingerir(n, header, reader, cat, features)
            s["csv_sha256"] = h.hash.hexdigest()
            ref = next(v for v in previo["csvs"] if v["arquivo"] == n)
            assert s["csv_sha256"] == ref["sha256"]
            assert s["classes"] == ref["nao_attempted"] and s["brutas"] == ref["linhas"]
            dias.append(d)
            stats.append(s)
            qualidades.append(q)
    datasets = [{k: np.concatenate([d[k] for d in dias[:3]]) for k in dias[0]}, dias[3], dias[4]]
    classes = list(cat.rotulos)
    assert [len(d["rotulo"]) for d in datasets] == [1184428, 360079, 543490]
    # Libera os catálogos de conteúdo antes de cruzar; igualdade já foi codificada sem hash.
    del cat, dias
    rows = []
    for arquivo, qualidade, n in [(s["arquivo"], q, s["nao_attempted"]) for s, q in zip(stats, qualidades, strict=True)] + [
            (s, np.sum(qualidades[:3], axis=0) if i == 0 else qualidades[i + 2], len(datasets[i]["rotulo"]))
            for i, s in enumerate(SPLITS)]:
        for feature, (vazio, invalido, nao_finito) in zip(features, qualidade, strict=True):
            rows.append({"escopo": arquivo, "populacao": "nao_Attempted", "linhas": n, "feature": feature,
                "vazios": int(vazio), "invalidos": int(invalido), "nao_finitos": int(nao_finito),
                "pct_celulas_problematicas": pct(int(vazio + invalido + nao_finito), n)})
    tabela(args.saida / "qualidade_por_feature.csv", rows)
    pares, conflitos, simulacoes = analisar(datasets, classes, args.saida)
    resumo = {"zip_sha256": SHA_ZIP, "hash_script": sha(Path(__file__)),
        "hash_inventario_anterior": sha(args.inventario_anterior), "hash_contrato": sha(args.contrato),
        "python": platform.python_version(), "numpy": np.__version__, "plataforma": platform.platform(),
        "ordem_features": features, "classes_nominais": classes, "rotulos_binarios": {"BENIGN": 0, "demais_sem_Attempted": 1},
        "capturas": stats, "totais_referencia": dict(zip(SPLITS, [1184428, 360079, 543490])),
        "cruzamentos": pares, "conflitos": conflitos,
        "simulacoes_totais": [{"cenario": x["cenario"], "conjunto": x["conjunto"], "antes": sum(
            y["antes"] for y in simulacoes if y["cenario"] == x["cenario"] and y["conjunto"] == x["conjunto"] and y["escala"] == "binario"),
            "depois": sum(y["depois"] for y in simulacoes if y["cenario"] == x["cenario"] and y["conjunto"] == x["conjunto"] and y["escala"] == "binario")}
            for x in simulacoes if x["escala"] == "binario" and x["classe"] == "BENIGN"],
        "limites": ["sem normalizacao ou comparacao de vetores padronizados", "sem treino",
                   "sem indices novos ou alteracao do split original", "simulacoes removem dos conjuntos posteriores e preservam treino",
                   "flow ID e grupo nao provam evento duplicado", "vetores invalidos sem chave; nao imputados nem considerados iguais",
                   "binario BENIGN/ATTACK difere do piloto BENIGN/DDoS"],
        "tempo_total_s": time.monotonic() - inicio,
        "pico_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    escrever(args.saida / "resultado.json", resumo)
    print("AUDITORIA CONCLUÍDA", resumo["tempo_total_s"], "s; RSS", resumo["pico_rss_kib"], "KiB", flush=True)


def sintetico(destino):
    destino.mkdir(parents=True, exist_ok=False)
    features = [f"f{i}" for i in range(81)]
    header = list(META) + features + list(ROTULOS)
    cat = Catalogo()
    def row(ident, grupo, valor, label, dia, reverso=False, attempt=False, problema=None):
        origem = ("10.0.0.1", 1000 + grupo)
        alvo = ("10.0.0.2", 80)
        if reverso:
            origem, alvo = alvo, origem
        fid = f"{origem[0]}-{alvo[0]}-{origem[1]}-{alvo[1]}-6"
        v = [str(valor), "-0.0"] + ["0"] * 79
        if problema:
            v[2] = problema
        return [str(ident), fid, origem[0], str(origem[1]), alvo[0], str(alvo[1]), "6",
                f"2017-07-0{dia} 12:00:00"] + v + [label, "0" if attempt else "-1"]
    train = [row(1, 1, 1, "BENIGN", 3), row(2, 2, 2, "DoS Hulk", 3), row(3, 3, 1, "DoS Hulk", 3)]
    val = [row(1, 4, 3, "BENIGN", 6), row(2, 1, 1, "Botnet", 6, reverso=True),
           row(3, 5, 5, "BENIGN", 6, problema="nan"), row(4, 6, 6, "BENIGN", 6, problema=" "),
           row(5, 7, 7, "BENIGN", 6, problema="nao_numero"),
           row(6, 8, 8, "Botnet - Attempted", 6, attempt=True)]
    test = [row(1, 9, 1, "BENIGN", 7), row(2, 4, 4, "BENIGN", 7)]
    ds = []
    for nome, rows in [(DIAS[0], train), (DIAS[3], val), (DIAS[4], test)]:
        d, s, q = ingerir(nome, header, rows, cat, features)
        ds.append(d)
        if nome == DIAS[3]:
            assert len(d["rotulo"]) == 5 and q[:, 0].sum() == q[:, 1].sum() == q[:, 2].sum() == 1
    classes = list(cat.rotulos)
    r, c, _, a, b = cruzar(ds[0], ds[1], "vetor_float64", classes)
    assert r["chaves_comuns"] == 1 and r["linhas_a"] == 2 and r["linhas_b"] == 1
    assert c[0]["chaves_com_conflito"] == 1 and c[0]["pares_de_linhas_com_rotulos_diferentes"] == 2
    assert c[1]["chaves_com_conflito"] == 1 and c[1]["pares_de_linhas_com_rotulos_diferentes"] == 1
    assert c[0]["linhas_a_com_rotulo_oposto_no_outro_lado"] == 2
    assert c[1]["linhas_a_com_rotulo_oposto_no_outro_lado"] == 1
    assert cruzar(ds[0], ds[1], "grupo_bidirecional", classes)[0]["chaves_comuns"] == 1
    assert cruzar(ds[0], ds[1], "flow_id_direcional", classes)[0]["chaves_comuns"] == 0
    assert cruzar(ds[1], ds[2], "flow_id_direcional", classes)[0]["chaves_comuns"] == 1
    for i, j in PARES:
        assert cruzar(ds[i], ds[j], "id_local_escopado", classes)[0]["chaves_comuns"] == 0
        assert cruzar(ds[i], ds[j], "flow_id_timestamp", classes)[0]["chaves_comuns"] == 0
    assert vetor([0.0, 1.0]) == vetor([-0.0, 1.0])
    assert vetor([1., 2.]) != vetor([1., np.nextafter(2., 3.)])
    assert vetor([float('nan')]) is None
    _, _, simulacoes = analisar(ds, classes, destino)
    for cenario in ["sequencial_vetor_float64", "sequencial_grupo_bidirecional"]:
        for conjunto, esperado in [("treino", 3), ("validacao", 4), ("teste", 1)]:
            assert sum(r["depois"] for r in simulacoes if r["cenario"] == cenario
                       and r["conjunto"] == conjunto and r["escala"] == "binario") == esperado
    escrever(destino / "teste.json", {"status": "OK", "testes": ["duplicatas e linhas versus chaves",
        "conflitos binarios e nominais", "IDs locais repetidos entre capturas nao sao comuns",
        "FlowID recorrente com timestamps diferentes nao e mesmo evento", "chave bidirecional invariante a reversao",
        "canonicalizacao -0.0 sem arredondamento", "vazios invalidos e nao finitos separados",
        "Attempted excluido e simulacoes reconciliadas/disjuntas"]})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="modo", required=True)
    s = subs.add_parser("sintetico")
    s.add_argument("saida", type=Path)
    a = subs.add_parser("auditar")
    a.add_argument("zip", type=Path)
    a.add_argument("inventario_anterior", type=Path)
    a.add_argument("contrato", type=Path)
    a.add_argument("saida", type=Path)
    args = parser.parse_args()
    if args.modo == "sintetico":
        sintetico(args.saida)
    else:
        auditar(args)
