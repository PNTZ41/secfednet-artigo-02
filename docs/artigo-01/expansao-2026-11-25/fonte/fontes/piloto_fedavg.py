"""Treina e executa um piloto binário FedAvg com clientes simulados em CPU."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


CLASSES = ("BENIGN", "DDoS")
SEED = 23
CLIENTES = 3
RODADAS = 8
PASSOS_LOCAIS = 2
TAXA = 0.2
LIMIAR = 0.5


def ler_csv(caminho):
    linhas, rotulos, registros = [], [], []
    mapa = {nome: i for i, nome in enumerate(CLASSES)}
    total = 0
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.reader(arquivo)
        cabecalho = next(leitor)
        coluna_rotulo, = (i for i, nome in enumerate(cabecalho) if nome.strip() == "Label")
        nomes = cabecalho[:coluna_rotulo] + cabecalho[coluna_rotulo + 1:]
        for linha in leitor:
            if not linha:
                continue
            total += 1
            if len(linha) != len(cabecalho):
                raise ValueError(f"Largura inválida na linha física {leitor.line_num}")
            rotulo = mapa[linha[coluna_rotulo]]
            valores = list(map(float, linha[:coluna_rotulo] + linha[coluna_rotulo + 1:]))
            if all(map(math.isfinite, valores)):
                linhas.append(valores)
                rotulos.append(rotulo)
                registros.append(total)
    if not linhas:
        raise ValueError("O CSV não contém registros com features finitas")
    return nomes, np.array(linhas), np.array(rotulos), np.array(registros), total


def selecionar_unicos(features, rotulos):
    # Agrupa vetores numéricos idênticos antes da divisão entre treino e teste.
    _, primeiros, grupos = np.unique(features, axis=0, return_index=True, return_inverse=True)
    consistentes = np.ones(len(primeiros), dtype=bool)
    consistentes[grupos[rotulos != rotulos[primeiros][grupos]]] = False
    descartados_por_conflito = int(np.count_nonzero(~consistentes[grupos]))
    return np.sort(primeiros[consistentes]), descartados_por_conflito


def dividir_dataset(rotulos):
    rng = np.random.default_rng(SEED)
    por_classe = [rng.permutation(np.flatnonzero(rotulos == i)) for i in range(len(CLASSES))]
    if min(map(len, por_classe)) < 5:
        raise ValueError("São necessários pelo menos cinco vetores distintos por classe")
    cortes = [len(indices) // 5 for indices in por_classe]
    teste = np.concatenate([indices[:corte] for indices, corte in zip(por_classe, cortes)])
    partes = [np.array_split(indices[corte:], CLIENTES) for indices, corte in zip(por_classe, cortes)]
    clientes = [np.concatenate(partes_cliente) for partes_cliente in zip(*partes)]
    return clientes, teste


def sigmoid(logits):
    return 1.0 / (1.0 + np.exp(-np.clip(logits, -500.0, 500.0)))


def fedavg(clientes):
    pesos = np.zeros(clientes[0][0].shape[1])
    intercepto = 0.0
    n_treino = sum(len(y) for _, y in clientes)
    for _ in range(RODADAS):
        soma_pesos = np.zeros_like(pesos)
        soma_interceptos = 0.0
        for x, y in clientes:
            local_pesos = pesos.copy()
            local_intercepto = intercepto
            for _ in range(PASSOS_LOCAIS):
                erros = sigmoid(x @ local_pesos + local_intercepto) - y
                local_pesos -= TAXA * (x.T @ erros) / len(y)
                local_intercepto -= TAXA * erros.mean()
            soma_pesos += len(y) * local_pesos
            soma_interceptos += len(y) * local_intercepto
        pesos = soma_pesos / n_treino
        intercepto = soma_interceptos / n_treino
    return pesos, intercepto


def prever(features, *, media, escala, pesos, intercepto, classes, limiar):
    score = float(sigmoid(((features - media) / escala) @ pesos + intercepto))
    classe_id = int(score >= limiar)
    return {"classe_id": classe_id, "classe": str(classes[classe_id]), "score": score}


def contar_classes(rotulos):
    return {nome: int(np.count_nonzero(rotulos == i)) for i, nome in enumerate(CLASSES)}


def gravar_json(caminho, dados):
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                       encoding="utf-8")


def treinar(caminho_csv, saida):
    with caminho_csv.open("rb") as arquivo:
        sha256 = hashlib.file_digest(arquivo, "sha256").hexdigest()
    nomes, features, rotulos, registros, total = ler_csv(caminho_csv)
    unicos, conflitos = selecionar_unicos(features, rotulos)
    clientes, teste = dividir_dataset(rotulos[unicos])
    clientes = [unicos[indices] for indices in clientes]
    teste = unicos[teste]
    treino = features[np.concatenate(clientes)]
    media, escala = treino.mean(axis=0), treino.std(axis=0)
    escala[escala == 0.0] = 1.0
    pesos, intercepto = fedavg([((features[idx] - media) / escala, rotulos[idx]) for idx in clientes])
    modelo = dict(media=media, escala=escala, pesos=pesos, intercepto=intercepto,
                  classes=CLASSES, limiar=LIMIAR)

    scores = sigmoid(((features[teste] - media) / escala) @ pesos + intercepto)
    y = rotulos[teste]
    previstos = scores >= LIMIAR
    matriz = np.bincount(2 * y + previstos, minlength=4).reshape(2, 2)
    exemplo = teste[y == 1].min()
    metricas = {
        "csv_sha256": sha256,
        "numpy": np.__version__,
        "linhas_csv": total,
        "linhas_descartadas_nao_finitas": total - len(features),
        "linhas_descartadas_rotulos_conflitantes": conflitos,
        "duplicatas_numericas_descartadas": len(features) - conflitos - len(unicos),
        "seed": SEED,
        "rodadas": RODADAS,
        "passos_locais_por_rodada": PASSOS_LOCAIS,
        "taxa_de_aprendizado": TAXA,
        "treino_por_cliente": [contar_classes(rotulos[indices]) for indices in clientes],
        "teste_por_classe": contar_classes(y),
        "mapa_classes": dict(enumerate(CLASSES)),
        "ordem_features": nomes,
        "limiar": LIMIAR,
        "matriz_confusao_real_por_previsto": matriz.tolist(),
        "acuracia_teste": float(np.mean(previstos == y)),
        "exemplo_registro_dados": int(registros[exemplo]),
        "exemplo_rotulo_real": CLASSES[rotulos[exemplo]],
        "exemplo_previsao_em_memoria": prever(features[exemplo], **modelo),
    }

    saida.mkdir(parents=True, exist_ok=True)
    np.savez(saida / "checkpoint.npz", **modelo, ordem_features=nomes, csv_sha256=sha256)
    gravar_json(saida / "metricas.json", metricas)
    gravar_json(saida / "exemplo_entrada.json", {"features": features[exemplo].tolist()})
    print(f"Treino: {len(treino)} registros. Teste: {len(teste)} registros. "
          f"Acurácia no teste: {metricas['acuracia_teste']:.4%}.")


def prever_do_checkpoint(caminho_checkpoint, caminho_entrada):
    with np.load(caminho_checkpoint, allow_pickle=False) as checkpoint:
        nomes = checkpoint["ordem_features"]
        modelo = {campo: checkpoint[campo]
                  for campo in ("media", "escala", "pesos", "intercepto", "classes", "limiar")}
    valores = json.loads(caminho_entrada.read_text(encoding="utf-8"))["features"]
    if (not isinstance(valores, list) or len(valores) != len(nomes)
            or any(type(valor) not in (int, float) or not math.isfinite(valor) for valor in valores)):
        raise ValueError(f"'features' deve conter {len(nomes)} números finitos na ordem do checkpoint")
    return prever(np.array(valores, dtype=np.float64), **modelo)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    comandos = parser.add_subparsers(dest="comando", required=True)
    treino = comandos.add_parser("treinar")
    treino.add_argument("csv", type=Path)
    treino.add_argument("saida", type=Path)
    predicao = comandos.add_parser("prever")
    predicao.add_argument("checkpoint", type=Path)
    predicao.add_argument("entrada", type=Path)
    args = parser.parse_args()
    if args.comando == "treinar":
        treinar(args.csv, args.saida)
    else:
        print(json.dumps(prever_do_checkpoint(args.checkpoint, args.entrada), allow_nan=False))


if __name__ == "__main__":
    main()
