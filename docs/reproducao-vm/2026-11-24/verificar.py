"""Verifica evidências entregues sem dataset, dependências externas ou treino."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


PASTA = Path(__file__).resolve().parent
REPO = PASTA.parents[2]
BASE = Path("secfednet-local/artigo-01/cnn-scaffold")
EXEC = Path("codigo/secfednet-local/artigo-01/execucoes")
CURTO = EXEC / "scaffold-curto-vm-20261124-221130"
LONGO = EXEC / "scaffold-20-vm-20261124-222013"


def exigir(condicao, mensagem):
    if not condicao:
        raise ValueError(mensagem)


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def ler(p):
    return json.loads(p.read_text(encoding="utf-8"))


def manifesto(p):
    itens = {}
    for linha in p.read_text().splitlines():
        digest, nome = linha.split(maxsplit=1)
        relativo = Path(nome)
        exigir(not relativo.is_absolute() and ".." not in relativo.parts,
               f"Caminho inseguro: {nome}")
        exigir(nome not in itens, f"Caminho repetido: {nome}")
        exigir(len(digest) == 64 and all(c in "0123456789abcdef" for c in digest),
               f"Hash inválido: {nome}")
        itens[nome] = digest
    return itens


def validar_metricas(m):
    (vn, fp), (fn, vp) = m["matriz_real_por_previsto"]
    exigir(m["suporte"] == {"BENIGN": vn + fp, "DDoS": fn + vp}, "Suporte incoerente")
    exigir(vn + fp == 40776 and fn + vp == 10039, "Validação alterada")
    f1_b = 2 * vn / (2 * vn + fp + fn)
    f1_d = 2 * vp / (2 * vp + fp + fn)
    for chave, valor in [("fpr", fp / (vn + fp)), ("recall_ddos", vp / (fn + vp)),
                         ("macro_f1_binario", (f1_b + f1_d) / 2)]:
        exigir(math.isclose(m[chave], valor, abs_tol=1e-12, rel_tol=0), chave)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--acervo", type=Path, help="Raiz do backup secfednet-repro (opcional)")
    args = ap.parse_args()
    itens = manifesto(PASTA / "SHA256_REPRODUCAO")
    encontrados = {str(p.relative_to(PASTA)) for p in PASTA.rglob("*") if p.is_file()}
    exigir(encontrados == set(itens) | {"SHA256_REPRODUCAO"}, "Manifesto não fecha a seleção")
    exigir(set((PASTA / "LISTA_ARQUIVOS.txt").read_text().splitlines()) == encontrados,
           "Lista de arquivos divergente")
    for nome, digest in itens.items():
        exigir(sha(PASTA / nome) == digest, f"Hash da seleção: {nome}")
    antigos = manifesto(REPO / "SHA256_ENTREGA")
    for nome, digest in antigos.items():
        exigir(sha(REPO / nome) == digest, f"Baseline alterada: {nome}")
    inventario = ler(PASTA / "ACERVO.json")
    hashes_vm = {a["path"]: a["sha256"] for a in inventario["arquivos"]}
    exigir(len(hashes_vm) == 256, "Inventário incompleto")
    for nome in inventario["selecionados_da_vm"]:
        exigir(sha(PASTA / nome) == hashes_vm[nome], f"Original VM alterado: {nome}")

    # Confere novamente os hashes históricos contra a consulta da origem VM.
    contagens = []
    for pasta, historico, prefixo, esperado in [
        (CURTO, "SHA256_ARTEFATOS", BASE / "ensaio-01", (21, 6, 0)),
        (LONGO, "SHA256_ARTEFATOS_20", BASE / "ensaio-20-rodadas", (101, 9, 3)),
    ]:
        iguais = diferentes = ausentes = 0
        for nome, digest in manifesto(REPO / BASE / historico).items():
            relativo = Path(nome).relative_to(prefixo)
            obtido = hashes_vm.get(str(pasta / relativo))
            if obtido is None:
                ausentes += 1
            elif obtido == digest:
                iguais += 1
            else:
                diferentes += 1
        exigir((iguais, diferentes, ausentes) == esperado, f"Histórico {historico}")
        contagens.append({"manifesto": historico, "iguais": iguais,
                          "diferentes": diferentes, "ausentes_no_wrapper": ausentes})

    pontos = []
    for pasta, rodadas in [(CURTO, 2), (LONGO, 20)]:
        resultado = ler(PASTA / pasta / "execucao/resultados.json")
        exigir(resultado["teste_global_avaliado"] is False, "Uso indevido do teste global")
        exigir(resultado["teto_fpr"] == 0.01, "Teto alterado")
        for metodo in resultado["resultados"]:
            for nome in ["calibrado_validacao", "limiar_05"]:
                validar_metricas(metodo[nome])
            m = metodo["calibrado_validacao"]
            exigir(m["fpr"] <= 0.01, "Teto de FPR excedido")
            pontos.append({"metodo": metodo["nome"], "rodadas": rodadas, **m})
    exigir(sha(PASTA / LONGO / "execucao/resultados.json") ==
           sha(REPO / BASE / "ensaio-20-rodadas/execucao/resultados.json"), "Métricas finais")
    linhas_csv = 0
    for rel in ["curvas.csv", "fedavg_sgd/curva.csv", "scaffold/curva.csv"]:
        with (PASTA / LONGO / "execucao" / rel).open(newline="") as f:
            atual = list(csv.DictReader(f))
        with (REPO / BASE / "ensaio-20-rodadas/execucao" / rel).open(newline="") as f:
            ref = list(csv.DictReader(f))
        exigir(atual == ref, f"Curva CSV divergente: {rel}")
        if rel == "curvas.csv":
            linhas_csv = len(atual)
            exigir(linhas_csv == 40, "Curva incompleta")
    for metodo in ["fedavg_sgd", "scaffold"]:
        curva = ler(PASTA / LONGO / "execucao" / metodo / "curva.json")
        exigir(len(curva) == 20, "Rodadas incompletas")
        for r, ponto in enumerate(curva, 1):
            validar_metricas(ponto["validacao_calibrada"])
            exigir(ponto["rodada"] == r, "Ordem das rodadas")
            exigir(ponto["bytes_parametros_acumulados"] == r * 45960, "Bytes parâmetros")
            exigir(ponto["bytes_controles_acumulados"] == r * (45960 if metodo == "scaffold" else 0),
                   "Bytes controles")
            exigir(ponto["bytes_brutos_acumulados"] == ponto["bytes_parametros_acumulados"] +
                   ponto["bytes_controles_acumulados"], "Soma dos bytes")
    saida = ler(PASTA / "pacote-inferencia/cnn1d/saida_verificada.json")
    exigir(saida == ler(REPO / "integracao/artigo-01/contrato-cnn/exemplo_saida.json"),
           "Inferência diverge do exemplo versionado")
    exigir(saida["classe_id"] == 1 and saida["classe"] == "DDoS" and len(saida["embedding"]) == 16,
           "Contrato de inferência")
    acervo_conferido = 0
    if args.acervo:
        for arquivo in inventario["arquivos"]:
            p = args.acervo / arquivo["path"]
            exigir(p.is_file() and p.stat().st_size == arquivo["bytes"] and
                   sha(p) == arquivo["sha256"], f"Backup: {p}")
            acervo_conferido += 1
    print(json.dumps({"status": "OK", "arquivos_selecao": len(encontrados),
                      "baseline_hashes": len(antigos), "curvas_linhas": linhas_csv,
                      "historicos": contagens, "acervo_arquivos_recalculados": acervo_conferido,
                      "pontos": pontos, "limite": "Sem treino; métricas recalculadas das matrizes. "
                      "Sem --acervo, igualdade binária usa hashes consultados na VM."},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
