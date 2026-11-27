"""Audita sexta-feira do CICIDS2017 corrigido e avalia um teste cronológico fixo."""

import argparse
import csv
import hashlib
import io
import json
import math
import zipfile
from array import array
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

from avaliar_piloto import chaves_vetores, medir, treinar_centralizado
import piloto_fedavg as piloto


MEMBRO = "friday.csv"
METADADOS = ("id", "Flow ID", "Src IP", "Src Port", "Dst IP", "Dst Port", "Protocol", "Timestamp")
ROTULACAO = ("Label", "Attempted Category")
FRACAO_TESTE = 0.20


@dataclass
class Dados:
    x: np.ndarray
    y: np.ndarray
    tempos: np.ndarray
    grupos: np.ndarray
    linhas: np.ndarray
    colunas: list[str]
    auditoria: dict


def sha256(caminho):
    with caminho.open("rb") as fonte:
        return hashlib.file_digest(fonte, "sha256").hexdigest()


def ler_sexta(caminho):
    valores, rotulos, tempos, grupos, linhas = array("d"), [], [], [], []
    grupos_por_chave = {}
    rotulos_brutos, filtros, janelas_brutas, janelas_elegiveis = (Counter() for _ in range(4))
    classes = dict(zip(piloto.CLASSES, range(len(piloto.CLASSES))))
    with zipfile.ZipFile(caminho) as arquivo:
        with arquivo.open(MEMBRO) as origem, io.TextIOWrapper(origem, encoding="utf-8-sig", newline="") as csv_file:
            leitor = csv.reader(csv_file)
            cabecalho = next(leitor)
            campos = {nome: cabecalho.index(nome) for nome in METADADOS + ROTULACAO}
            indices = [i for i, nome in enumerate(cabecalho) if nome not in campos]
            colunas = [cabecalho[i] for i in indices]
            for numero, linha in enumerate(leitor, 1):
                if len(linha) != len(cabecalho):
                    raise ValueError(f"Largura inválida no registro {numero}")
                instante = datetime.fromisoformat(linha[campos["Timestamp"]])
                if instante.tzinfo is not None or instante.date().isoformat() != "2017-07-07":
                    raise ValueError(f"Timestamp fora do formato UTC esperado no registro {numero}")
                rotulo = linha[campos["Label"]].strip()
                rotulos_brutos[rotulo] += 1
                janela = instante.replace(minute=instante.minute // 15 * 15, second=0, microsecond=0)
                chave_janela = (janela.isoformat(sep=" "), rotulo)
                if rotulo in classes:
                    janelas_brutas[chave_janela] += 1
                if linha[campos["Attempted Category"]].strip() != "-1" or rotulo.endswith(" - Attempted"):
                    filtros["tentativa"] += 1
                    continue
                if rotulo not in classes:
                    filtros["fora_das_classes_binarias"] += 1
                    continue
                medidas = [float(linha[i]) for i in indices]
                if not all(map(math.isfinite, medidas)):
                    filtros[f"nao_finitas_{rotulo}"] += 1
                    continue
                if any(not linha[campos[nome]].strip() for nome in METADADOS):
                    raise ValueError(f"Metadado vazio no registro elegível {numero}")
                origem = (linha[campos["Src IP"]], int(linha[campos["Src Port"]]))
                destino = (linha[campos["Dst IP"]], int(linha[campos["Dst Port"]]))
                grupo = (int(linha[campos["Protocol"]]), *sorted((origem, destino)))
                grupos.append(grupos_por_chave.setdefault(grupo, len(grupos_por_chave)))
                valores.extend(medidas)
                rotulos.append(classes[rotulo])
                tempos.append(instante)
                linhas.append(numero)
                janelas_elegiveis[chave_janela] += 1

    janelas = sorted({janela for janela, _ in janelas_brutas})
    auditoria = {
        "rotulos_brutos": dict(rotulos_brutos),
        "exclusoes_antes_do_split": dict(filtros),
        "janelas_utc": [{"inicio": janela,
                         "brutos": {c: janelas_brutas[janela, c] for c in piloto.CLASSES},
                         "elegiveis": {c: janelas_elegiveis[janela, c] for c in piloto.CLASSES}}
                        for janela in janelas],
    }
    return Dados(np.asarray(valores).reshape(-1, len(colunas)), np.asarray(rotulos, dtype=np.int64),
                 np.asarray(tempos, dtype="datetime64[us]").view(np.int64),
                 np.asarray(grupos, dtype=np.int64), np.asarray(linhas, dtype=np.int64), colunas, auditoria)


def ultima_ocorrencia(codigos, tempos):
    ultimos = np.full(int(codigos.max()) + 1, np.iinfo(np.int64).min, dtype=np.int64)
    np.maximum.at(ultimos, codigos, tempos)
    return ultimos[codigos]


def escolher_corte(dados, vetores):
    # Um registro de treino só é elegível após a última ocorrência do seu grupo e do seu vetor.
    liberacao = np.maximum(ultima_ocorrencia(dados.grupos, dados.tempos),
                           ultima_ocorrencia(vetores, dados.tempos))
    candidatos = np.unique(dados.tempos)
    validos = np.ones(len(candidatos), dtype=bool)
    desvios = np.zeros(len(candidatos))
    for classe in range(len(piloto.CLASSES)):
        mascara = dados.y == classe
        instantes = np.sort(dados.tempos[mascara])
        no_teste = len(instantes) - np.searchsorted(instantes, candidatos)
        validos &= (candidatos > liberacao[mascara].min()) & (no_teste > 0)
        desvios += (no_teste / len(instantes) - FRACAO_TESTE) ** 2
    if not validos.any():
        return None
    melhor = np.argmin(np.where(validos, desvios, np.inf))
    corte = int(candidatos[melhor])
    return corte, np.flatnonzero(dados.tempos >= corte), np.flatnonzero(liberacao < corte)


def intersecoes(grupos, vetores, treino, teste):
    return {"grupos": int(np.intersect1d(grupos[treino], grupos[teste]).size),
            "vetores": int(np.intersect1d(vetores[treino], vetores[teste]).size)}


def auditar(dados, vetores, hash_zip, split_path):
    resultado = {**dados.auditoria, "zip_sha256": hash_zip, "membro": MEMBRO,
                 "ordem_features": dados.colunas, "elegiveis": piloto.contar_classes(dados.y)}
    escolha = escolher_corte(dados, vetores) if np.unique(dados.y).size == 2 else None
    if escolha is None:
        return {**resultado, "estado": "sem corte cronológico com as duas classes após a auditoria"}
    corte, teste, treino = escolha
    antes = np.flatnonzero(dados.tempos < corte)
    removidos = np.setdiff1d(antes, treino, assume_unique=True)
    grupos_teste = np.isin(dados.grupos[antes], dados.grupos[teste])
    vetores_teste = np.isin(vetores[antes], vetores[teste])
    assert not any(intersecoes(dados.grupos, vetores, treino, teste).values())
    assert np.array_equal(removidos, antes[grupos_teste | vetores_teste])
    assert treino.size >= piloto.CLIENTES and set(dados.y[treino]) == set(dados.y[teste]) == {0, 1}

    manifesto = dict(zip_sha256=hash_zip, membro=MEMBRO, ordem_features=dados.colunas,
                     corte_utc_us=corte, linhas_treino=dados.linhas[treino], linhas_teste=dados.linhas[teste])
    if split_path.exists():
        with np.load(split_path, allow_pickle=False) as existente:
            if not all(np.array_equal(existente[k], v) for k, v in manifesto.items()):
                raise ValueError("O manifesto existente difere da nova auditoria")
    else:
        with split_path.open("xb") as saida:
            np.savez_compressed(saida, **manifesto)

    pares = [np.unique(vetores[dados.y == i]) for i in range(len(piloto.CLASSES))]
    return {**resultado, "estado": "teste congelado", "split_sha256": sha256(split_path),
            "corte_utc": np.datetime_as_string(np.datetime64(corte, "us")) + "Z",
            "treino_bruto_antes_do_corte": piloto.contar_classes(dados.y[antes]),
            "treino_descartado_por_intersecao": piloto.contar_classes(dados.y[removidos]),
            "linhas_treino_com_grupo_compartilhado": int(grupos_teste.sum()),
            "linhas_treino_com_vetor_compartilhado": int(vetores_teste.sum()),
            "linhas_treino_com_ambos": int((grupos_teste & vetores_teste).sum()),
            "intersecoes_antes": intersecoes(dados.grupos, vetores, antes, teste),
            "intersecoes_finais": intersecoes(dados.grupos, vetores, treino, teste),
            "vetores_com_rotulos_conflitantes_no_universo_elegivel": int(np.intersect1d(*pares).size),
            "repeticoes_de_vetores_no_teste": int(len(teste) - len(np.unique(vetores[teste]))),
            "treino": piloto.contar_classes(dados.y[treino]), "teste": piloto.contar_classes(dados.y[teste])}


def padronizar(dados, treino, teste):
    teste_bruto = dados.x[teste]
    ajustes = []
    while True:
        if set(dados.y[treino]) != {0, 1} or len(treino) < piloto.CLIENTES:
            raise ValueError("A auditoria dos vetores padronizados deixou o treino sem suporte")
        x = dados.x[treino]
        media, escala = x.mean(axis=0), x.std(axis=0)
        escala[escala == 0.0] = 1.0
        x_treino, x_teste = (x - media) / escala, (teste_bruto - media) / escala
        chaves_treino = chaves_vetores(x_treino)
        comuns = np.intersect1d(chaves_treino, chaves_vetores(x_teste))
        if not comuns.size:
            return treino, x_treino, x_teste, ajustes
        coincidiu = np.isin(chaves_treino, comuns)
        ajustes.append({"vetores_em_comum": int(comuns.size),
                        "treino_removido": piloto.contar_classes(dados.y[treino[coincidiu]])})
        treino = treino[~coincidiu]


def comparar(dados, vetores, hash_zip, split_path):
    with np.load(split_path, allow_pickle=False) as congelado:
        assert congelado["zip_sha256"].item() == hash_zip
        assert congelado["membro"].item() == MEMBRO
        assert congelado["ordem_features"].tolist() == dados.colunas
        corte = congelado["corte_utc_us"].item()
        treino, teste = [np.flatnonzero(np.isin(dados.linhas, congelado[k]))
                         for k in ("linhas_treino", "linhas_teste")]
        assert np.array_equal(dados.linhas[treino], congelado["linhas_treino"])
        assert np.array_equal(dados.linhas[teste], congelado["linhas_teste"])
    assert np.array_equal(teste, np.flatnonzero(dados.tempos >= corte))
    assert np.all(dados.tempos[treino] < corte)
    assert set(dados.y[treino]) == set(dados.y[teste]) == {0, 1}
    assert not any(intersecoes(dados.grupos, vetores, treino, teste).values())

    treino, x_treino, x_teste, ajustes = padronizar(dados, treino, teste)
    y = dados.y[treino]

    rng = np.random.default_rng(piloto.SEED)
    por_classe = [np.array_split(rng.permutation(np.flatnonzero(y == i)), piloto.CLIENTES)
                  for i in range(len(piloto.CLASSES))]
    indices_clientes = [np.concatenate(partes) for partes in zip(*por_classe, strict=True)]
    assert np.array_equal(np.sort(np.concatenate(indices_clientes)), np.arange(len(treino)))
    clientes = [(x_treino[idx], y[idx]) for idx in indices_clientes]
    modelos = {"FedAvg": piloto.fedavg(clientes), "Centralizada": treinar_centralizado(x_treino, y)}
    metricas = {}
    for nome, (pesos, intercepto) in modelos.items():
        previstos = piloto.sigmoid(x_teste @ pesos + intercepto) >= piloto.LIMIAR
        metricas[nome] = medir(dados.y[teste], previstos)
        metricas[nome]["fpr"] = metricas[nome]["falsos_positivos_ddos"] / np.count_nonzero(dados.y[teste] == 0)
    return {"zip_sha256": hash_zip, "split_sha256": sha256(split_path),
            "treino": piloto.contar_classes(y), "teste": piloto.contar_classes(dados.y[teste]),
            "clientes": [piloto.contar_classes(rotulos) for _, rotulos in clientes],
            "ajustes_por_vetores_padronizados": ajustes, "vetores_padronizados_em_comum": 0,
            "linhas_treino_final_sha256": hashlib.sha256(dados.linhas[treino].astype("<i8").tobytes()).hexdigest(),
            "contribuicoes_gradiente_por_metodo": len(treino) * piloto.RODADAS * piloto.PASSOS_LOCAIS,
            "metricas": metricas}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("etapa", choices=("auditar", "comparar"))
    parser.add_argument("zip", type=Path)
    parser.add_argument("split", type=Path)
    args = parser.parse_args()
    dados = ler_sexta(args.zip)
    _, vetores = np.unique(chaves_vetores(dados.x), return_inverse=True)
    etapa = auditar if args.etapa == "auditar" else comparar
    resultado = etapa(dados, vetores.ravel(), sha256(args.zip), args.split)
    print(json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
