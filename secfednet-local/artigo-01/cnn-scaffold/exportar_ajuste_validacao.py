"""Exporta os dois subconjuntos congelados, sem materializar o teste reservado."""

import argparse
import csv
import io
import json
from pathlib import Path
import zipfile

import numpy as np

from retomar_fedavg_10 import LOCAL, PARTICAO, REFERENCIA, conferir_sha256, exigir


SUPORTE = {"ajuste": (163096, 40155), "validacao": (40776, 10039)}
METADADOS = {"id", "Flow ID", "Src IP", "Src Port", "Dst IP", "Dst Port",
             "Protocol", "Timestamp", "Label", "Attempted Category"}
CLASSES = {"BENIGN": 0, "DDoS": 1}


def exportar(fonte, saida):
    exigir(not saida.exists(), f"Destino já existe: {saida}")
    configuracao = json.loads((REFERENCIA / "configuracao.json").read_text())
    protocolo = json.loads(PARTICAO.with_name("protocolo.json").read_text())
    conferir_sha256(fonte, protocolo["zip_sha256"])
    conferir_sha256(PARTICAO, configuracao["manifesto_validacao_sha256"])
    global_npz = LOCAL / "cicids2017-corrigido/split_cronologico.npz"
    conferir_sha256(global_npz, protocolo["split_global_sha256"])
    with np.load(PARTICAO, allow_pickle=False) as m, np.load(global_npz, allow_pickle=False) as g:
        nomes = m["ordem_features"]
        exigir(nomes.tolist() == configuracao["contrato"]["ordem_features"] == g["ordem_features"].tolist()
               and len(nomes) == len(set(nomes)) == 81, "Ordem das 81 colunas divergente")
        ids = {nome: m[nome] for nome in SUPORTE}
        todos = np.concatenate(list(ids.values()))
        exigir(len(np.unique(todos)) == todos.size, "IDs duplicados nas máscaras internas")
        exigir(not np.intersect1d(todos, g["linhas_teste"]).size and
               np.isin(todos, g["linhas_treino"]).all(), "Máscaras fora do treino cronológico")
        membro = g["membro"].item()

    destino = {int(id_linha): (nome, i) for nome, vetor in ids.items() for i, id_linha in enumerate(vetor)}
    xs = {nome: np.empty((len(vetor), 81), dtype=np.float64) for nome, vetor in ids.items()}
    ys = {nome: np.empty(len(vetor), dtype=np.int64) for nome, vetor in ids.items()}
    with zipfile.ZipFile(fonte) as zip_file, zip_file.open(membro) as arquivo:
        with io.TextIOWrapper(arquivo, encoding="utf-8-sig", newline="") as stream:
            leitor = csv.reader(stream)
            cabecalho = next(leitor)
            exigir(len(cabecalho) == len(set(cabecalho)) == 91 and METADADOS <= set(cabecalho),
                   "Cabeçalho fora do contrato")
            pos = [i for i, coluna in enumerate(cabecalho) if coluna not in METADADOS]
            exigir([cabecalho[i] for i in pos] == nomes.tolist(), "Colunas do CSV fora de ordem")
            rotulo, categoria = map(cabecalho.index, ("Label", "Attempted Category"))
            for numero, linha in enumerate(leitor, 1):
                alvo = destino.pop(numero, None)
                if alvo is None:
                    continue
                exigir(len(linha) == len(cabecalho), f"Largura inválida no registro interno {numero}")
                y = linha[rotulo].strip()
                exigir(y in CLASSES and linha[categoria].strip() == "-1",
                       f"Classe inesperada no registro interno {numero}")
                nome, i = alvo
                xs[nome][i] = [float(linha[j]) for j in pos]
                ys[nome][i] = CLASSES[y]
                if not destino:
                    break
    exigir(not destino, f"IDs internos ausentes: {len(destino)}")
    exportados = {"ordem_features": nomes}
    for nome, suporte in SUPORTE.items():
        exigir(np.isfinite(xs[nome]).all(), f"Valor não finito em {nome}")
        exigir(tuple(np.bincount(ys[nome], minlength=2)) == suporte, f"Suporte divergente em {nome}")
        exportados.update({f"ids_{nome}": ids[nome], f"x_{nome}": xs[nome], f"y_{nome}": ys[nome]})
    with saida.open("xb") as arquivo:
        np.savez_compressed(arquivo, **exportados)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_corrigido", type=Path)
    parser.add_argument("saida", type=Path)
    args = parser.parse_args()
    exportar(args.zip_corrigido, args.saida)
