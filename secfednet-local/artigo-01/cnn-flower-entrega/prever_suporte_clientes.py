"""Calcula somente o suporte de uma proposta de fatias do teste congelado."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from avaliar_corrigido import ler_sexta, sha256
from avaliar_piloto import chaves_vetores
from piloto_fedavg import CLASSES, contar_classes


SEED = 2405


def blocos_indivisiveis(grupos, x):
    # Une grupos de fluxo ligados por pelo menos um vetor idêntico na entrada da CNN.
    _, ids = np.unique(grupos, return_inverse=True)
    pais = list(range(int(ids.max()) + 1))

    def raiz(i):
        while pais[i] != i:
            pais[i] = pais[pais[i]]
            i = pais[i]
        return i

    _, vetores = np.unique(chaves_vetores(x), return_inverse=True)
    ordem = np.argsort(vetores, kind="stable")
    repetidos = vetores[ordem[1:]] == vetores[ordem[:-1]]
    for a, b in zip(ids[ordem[:-1][repetidos]], ids[ordem[1:][repetidos]], strict=True):
        pais[raiz(a)] = raiz(b)
    componentes = np.array([raiz(i) for i in ids])
    ordem = np.argsort(componentes, kind="stable")
    return np.split(ordem, np.flatnonzero(np.diff(componentes[ordem])) + 1)


def repartir(blocos, rotulos, suporte_treino):
    total = np.bincount(rotulos, minlength=len(CLASSES))
    metas = (suporte_treino / suporte_treino.sum(axis=0)) * total
    atribuicoes = [[] for _ in suporte_treino]
    acumulado = np.zeros_like(suporte_treino)
    rng = np.random.default_rng(SEED)
    ordem = sorted(rng.permutation(len(blocos)), key=lambda i: -len(blocos[i]))
    for i in ordem:
        bloco = blocos[i]
        classes = np.bincount(rotulos[bloco], minlength=len(CLASSES))
        aptos = (np.logical_or(classes == 0, metas > 0)).all(axis=1)
        if not aptos.any():
            raise ValueError("Bloco incompatível com todos os suportes de treino")
        antes = (acumulado - metas) / total
        depois = (acumulado + classes - metas) / total
        custo = ((depois ** 2) - (antes ** 2)).sum(axis=1)
        cliente = int(np.argmin(np.where(aptos, custo, np.inf)))
        atribuicoes[cliente].append(bloco)
        acumulado[cliente] += classes
    return [np.sort(np.concatenate(blocos)) if blocos else np.empty(0, dtype=int)
            for blocos in atribuicoes], metas


def prever(dados_dir, piloto):
    artefatos = piloto / "artefatos"
    particao = json.loads((artefatos / "particao.json").read_bytes())
    contrato = json.loads((artefatos / "contrato.json").read_bytes())
    caminho_zip = dados_dir / "CICIDS2017_improved.zip"
    caminho_split = dados_dir / "split_cronologico.npz"
    assert sha256(caminho_zip) == contrato["zip_sha256"]
    assert sha256(caminho_split) == contrato["split_sha256"]
    dados = ler_sexta(caminho_zip)
    with np.load(caminho_split, allow_pickle=False) as manifesto:
        treino, teste = [np.flatnonzero(np.isin(dados.linhas, manifesto[f"linhas_{nome}"]))
                         for nome in ("treino", "teste")]
        assert np.array_equal(dados.linhas[teste], manifesto["linhas_teste"])
        assert dados.colunas == contrato["ordem_features"]
    assert not np.intersect1d(treino, teste).size
    assert not np.intersect1d(dados.grupos[treino], dados.grupos[teste]).size
    checkpoint = torch.load(artefatos / "checkpoint_cnn1d.pt", map_location="cpu", weights_only=True)
    assert checkpoint["contrato"] == contrato
    x = ((dados.x[teste] - checkpoint["media"].numpy()) / checkpoint["escala"].numpy()).astype(np.float32)
    y = dados.y[teste]
    assert contar_classes(y) == particao["teste"]
    suporte_treino = np.array([[c[classe] for classe in CLASSES] for c in particao["contagens_clientes"]])
    blocos = blocos_indivisiveis(dados.grupos[teste], x)
    clientes, metas = repartir(blocos, y, suporte_treino)
    assert np.array_equal(np.sort(np.concatenate(clientes)), np.arange(len(teste)))

    vistos_grupos, vistos_vetores = set(), set()
    chaves = chaves_vetores(x)
    clientes_saida = []
    for i, indices in enumerate(clientes):
        grupos = set(dados.grupos[teste[indices]].tolist())
        vetores = {chave.tobytes() for chave in np.unique(chaves[indices])}
        assert not vistos_grupos.intersection(grupos) and not vistos_vetores.intersection(vetores)
        vistos_grupos.update(grupos)
        vistos_vetores.update(vetores)
        clientes_saida.append({
            "cliente": i, "treino": dict(zip(CLASSES, suporte_treino[i].tolist())),
            "alvo_teste": dict(zip(CLASSES, metas[i].tolist())),
            "teste": contar_classes(y[indices]), "total_teste": len(indices),
            "linhas_teste_sha256": hashlib.sha256(dados.linhas[teste[indices]].astype("<i8").tobytes()).hexdigest(),
        })
    return {"provisorio": True, "seed": SEED, "split_sha256": contrato["split_sha256"],
            "grupos_de_fluxo_no_teste": len(vistos_grupos), "blocos_indivisiveis": len(blocos),
            "total_teste": len(teste), "teste_global": contar_classes(y),
            "grupos_compartilhados_entre_clientes": 0, "vetores_compartilhados_entre_clientes": 0,
            "clientes": clientes_saida}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dados_corrigidos", type=Path)
    parser.add_argument("piloto", type=Path)
    args = parser.parse_args()
    print(json.dumps(prever(args.dados_corrigidos, args.piloto), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
