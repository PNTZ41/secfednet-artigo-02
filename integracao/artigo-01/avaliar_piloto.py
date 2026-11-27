"""Audita o split do piloto e compara FedAvg com regressão logística centralizada."""

import argparse
import csv
import hashlib
import json
import math
import platform
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

import numpy as np

import piloto_fedavg as piloto


ALFA_DIRICHLET = 0.5
MAX_TENTATIVAS_DIRICHLET = 100
DESLOCAMENTO_SEED_DIRICHLET = 1000


def chaves_vetores(features):
    # Compara o vetor inteiro sem arredondamento, tratando -0.0 e 0.0 como iguais.
    canonicos = features.copy(order="C")
    canonicos[canonicos == 0.0] = 0.0
    tipo = np.dtype((np.void, canonicos.shape[1] * canonicos.itemsize))
    return canonicos.view(tipo).ravel()


def auditar_nao_finitos(caminho, registros_finitos, total):
    excluidos = np.ones(total, dtype=bool)
    excluidos[registros_finitos - 1] = False
    grupos = defaultdict(set)
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.reader(arquivo)
        cabecalho = next(leitor)
        coluna = next(i for i, nome in enumerate(cabecalho) if nome.strip() == "Label")
        for i, linha in enumerate(linha for linha in leitor if linha):
            if excluidos[i]:
                valores = map(float, linha[:coluna] + linha[coluna + 1:])
                chave = tuple(None if math.isnan(valor) else valor for valor in valores)
                grupos[chave].add(linha[coluna])
    return len(grupos), sum(len(rotulos) > 1 for rotulos in grupos.values())


def treinar_centralizado(features, rotulos):
    pesos = np.zeros(features.shape[1])
    intercepto = 0.0
    for _ in range(piloto.RODADAS * piloto.PASSOS_LOCAIS):
        erros = piloto.sigmoid(features @ pesos + intercepto) - rotulos
        pesos -= piloto.TAXA * (features.T @ erros) / len(rotulos)
        intercepto -= piloto.TAXA * erros.mean()
    return pesos, intercepto


def medir(rotulos, previstos):
    matriz = np.bincount(2 * rotulos + previstos, minlength=4).reshape(2, 2)
    acertos = matriz.diagonal()
    reais, preditos = matriz.sum(axis=1), matriz.sum(axis=0)
    return {
        "macro_f1": float(np.mean(2 * acertos / (reais + preditos))),
        "recall_por_classe": dict(zip(piloto.CLASSES, (acertos / reais).tolist())),
        "falsos_positivos_ddos": int(matriz[0, 1]),
        "falsos_negativos_ddos": int(matriz[1, 0]),
        "matriz_real_por_previsto": matriz.tolist(),
    }


def distribuir_dirichlet(rotulos, seed):
    rng = np.random.default_rng(seed)
    concentracao = np.full(piloto.CLIENTES, ALFA_DIRICHLET)
    indices_por_classe = [np.flatnonzero(rotulos == i) for i in range(len(piloto.CLASSES))]
    for tentativa in range(1, MAX_TENTATIVAS_DIRICHLET + 1):
        partes_por_classe = []
        for indices in indices_por_classe:
            probabilidades = rng.dirichlet(concentracao)
            tamanhos = rng.multinomial(len(indices), probabilidades)
            partes_por_classe.append(np.split(rng.permutation(indices), np.cumsum(tamanhos)[:-1]))
        clientes = [np.sort(np.concatenate(partes)) for partes in zip(*partes_por_classe, strict=True)]
        if all(len(indices) > 0 for indices in clientes):
            return clientes, tentativa
    raise RuntimeError(f"Clientes vazios após {MAX_TENTATIVAS_DIRICHLET} tentativas com seed {seed}")


def comparar(seed, features, rotulos, unicos, chaves, *, com_dirichlet=False):
    # Altera apenas a semente em memória para reutilizar a divisão original do piloto.
    with patch.object(piloto, "SEED", seed):
        clientes, teste = piloto.dividir_dataset(rotulos[unicos])
    clientes = [unicos[indices] for indices in clientes]
    treino = np.concatenate(clientes)
    teste = unicos[teste]
    assert np.array_equal(np.sort(np.concatenate((treino, teste))), unicos)

    treino_bruto = features[treino]
    media, escala = treino_bruto.mean(axis=0), treino_bruto.std(axis=0)
    escala[escala == 0.0] = 1.0
    x_treino = (treino_bruto - media) / escala
    x_teste = (features[teste] - media) / escala
    y_treino, y_teste = rotulos[treino], rotulos[teste]

    cortes_clientes = np.cumsum([len(indices) for indices in clientes[:-1]])
    clientes_normalizados = list(zip(np.split(x_treino, cortes_clientes),
                                    np.split(y_treino, cortes_clientes)))
    pesos_fed, vies_fed = piloto.fedavg(clientes_normalizados)
    pesos_central, vies_central = treinar_centralizado(x_treino, y_treino)
    scores_fed = piloto.sigmoid(x_teste @ pesos_fed + vies_fed)
    scores_central = piloto.sigmoid(x_teste @ pesos_central + vies_central)
    classe_fed = scores_fed >= piloto.LIMIAR
    classe_central = scores_central >= piloto.LIMIAR

    resultado = {
        "seed": seed,
        "treino_por_cliente": [piloto.contar_classes(rotulos[idx]) for idx in clientes],
        "teste_por_classe": piloto.contar_classes(y_teste),
        "vetores_brutos_compartilhados": int(np.intersect1d(chaves[treino], chaves[teste]).size),
        "vetores_padronizados_compartilhados": int(
            np.intersect1d(chaves_vetores(x_treino), chaves_vetores(x_teste)).size),
        "previsoes_discordantes": int(np.count_nonzero(classe_fed != classe_central)),
        "maior_diferenca_absoluta_de_score": float(np.max(np.abs(scores_fed - scores_central))),
        "fedavg": medir(y_teste, classe_fed),
        "centralizada": medir(y_teste, classe_central),
    }
    if com_dirichlet:
        seed_distribuicao = DESLOCAMENTO_SEED_DIRICHLET + seed
        clientes_dirichlet, tentativa = distribuir_dirichlet(y_treino, seed_distribuicao)
        atribuicoes = np.sort(np.concatenate(clientes_dirichlet))
        if not np.array_equal(atribuicoes, np.arange(len(y_treino))):
            raise ValueError("A distribuição Dirichlet deve atribuir cada exemplo de treino uma vez")
        dados_clientes = [(x_treino[idx], y_treino[idx]) for idx in clientes_dirichlet]
        pesos_dirichlet, vies_dirichlet = piloto.fedavg(dados_clientes)
        scores_dirichlet = piloto.sigmoid(x_teste @ pesos_dirichlet + vies_dirichlet)
        resultado["dirichlet"] = {
            "alfa_por_classe": ALFA_DIRICHLET,
            "seed_distribuicao": seed_distribuicao,
            "tentativa_aceita": tentativa,
            "treino_por_cliente": [piloto.contar_classes(rotulos) for _, rotulos in dados_clientes],
            "treino_atribuido_exatamente_uma_vez": True,
            **medir(y_teste, scores_dirichlet >= piloto.LIMIAR),
        }
    return resultado, (media, escala, pesos_fed, vies_fed)


def conferir_checkpoint(modelo, checkpoint_path, features_limpas, nomes, sha):
    media, escala, pesos, vies = modelo
    media_total = features_limpas.mean(axis=0)
    escala_total = features_limpas.std(axis=0)
    escala_total[escala_total == 0.0] = 1.0
    with np.load(checkpoint_path, allow_pickle=False) as checkpoint:
        assert checkpoint["csv_sha256"].item() == sha
        assert checkpoint["ordem_features"].tolist() == nomes
        assert checkpoint["classes"].tolist() == list(piloto.CLASSES)
        assert checkpoint["limiar"].item() == piloto.LIMIAR
        assert np.array_equal(checkpoint["media"], media)
        assert np.array_equal(checkpoint["escala"], escala)
        assert np.allclose(checkpoint["pesos"], pesos, rtol=1e-12, atol=1e-12)
        assert np.isclose(checkpoint["intercepto"], vies, rtol=1e-12, atol=1e-12)
        return {
            "media_e_escala_iguais_a_recalculo_so_treino": True,
            "medias_diferentes_se_incluir_teste": int(np.count_nonzero(
                ~np.isclose(media, media_total, rtol=1e-12, atol=1e-12))),
            "escalas_diferentes_se_incluir_teste": int(np.count_nonzero(
                ~np.isclose(escala, escala_total, rtol=1e-12, atol=1e-12))),
            "pesos_e_intercepto_reproduzidos": True,
        }


def avaliar(caminho, seeds, *, com_dirichlet=False):
    with caminho.open("rb") as arquivo:
        sha = hashlib.file_digest(arquivo, "sha256").hexdigest()
    nomes, features, rotulos, registros, total = piloto.ler_csv(caminho)
    unicos, conflitos_piloto = piloto.selecionar_unicos(features, rotulos)
    chaves = chaves_vetores(features)
    por_classe = [np.unique(chaves[rotulos == i]) for i in range(len(piloto.CLASSES))]
    conflitos_finitos = np.intersect1d(*por_classe, assume_unique=True).size
    unicos_finitos = np.union1d(*por_classe).size
    vetores_nao_finitos, conflitos_nao_finitos = auditar_nao_finitos(caminho, registros, total)
    resultados = []
    for seed in seeds:
        resultado, modelo = comparar(seed, features, rotulos, unicos, chaves, com_dirichlet=com_dirichlet)
        if seed == piloto.SEED:
            pasta = Path(__file__).resolve().parent / "artefatos"
            original = json.loads((pasta / "metricas.json").read_text(encoding="utf-8"))
            assert original["treino_por_cliente"] == resultado["treino_por_cliente"]
            assert original["teste_por_classe"] == resultado["teste_por_classe"]
            assert original["matriz_confusao_real_por_previsto"] == resultado["fedavg"]["matriz_real_por_previsto"]
            resultado["checkpoint_original"] = conferir_checkpoint(
                modelo, pasta / "checkpoint.npz", features[unicos], nomes, sha)
        resultados.append(resultado)
    return {
        "csv_sha256": sha,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "auditoria_csv": {
            "registros": total,
            "numero_features": len(nomes),
            "registros_finitos": len(features),
            "vetores_finitos_distintos": int(unicos_finitos),
            "vetores_finitos_com_rotulos_conflitantes": int(conflitos_finitos),
            "registros_finitos_com_rotulos_conflitantes_removidos": conflitos_piloto,
            "registros_nao_finitos": total - len(features),
            "vetores_nao_finitos_distintos": vetores_nao_finitos,
            "vetores_nao_finitos_com_rotulos_conflitantes": conflitos_nao_finitos,
            "registros_utilizados": len(unicos),
        },
        "configuracao": {
            "mapa_classes": dict(enumerate(piloto.CLASSES)),
            "taxa_de_aprendizado": piloto.TAXA,
            "limiar": piloto.LIMIAR,
            "clientes_simulados": piloto.CLIENTES,
            "rodadas_fedavg": piloto.RODADAS,
            "passos_locais_por_rodada": piloto.PASSOS_LOCAIS,
            "passos_centralizados": piloto.RODADAS * piloto.PASSOS_LOCAIS,
        },
        "comparacoes": resultados,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--seeds", type=int, nargs="+", default=[piloto.SEED, 41, 89])
    parser.add_argument("--dirichlet", action="store_true", help="inclui FedAvg com Dirichlet por classe")
    args = parser.parse_args()
    resultado = avaliar(args.csv, args.seeds, com_dirichlet=args.dirichlet)
    print(json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
