"""CNN-1D e inferência do checkpoint local do Artigo 01."""

import argparse
import json
import math
from pathlib import Path

import torch
from torch import nn


FORMATO = "secfednet-cnn1d-v1"
NUM_FEATURES = 81
DIM_EMBEDDING = 16


class CNN1D(nn.Module):
    def __init__(self):
        super().__init__()
        self.convolucoes = nn.Sequential(
            nn.Conv1d(1, 8, kernel_size=5, stride=3, padding=2),
            nn.ReLU(),
            nn.Conv1d(8, 12, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(4),
            nn.Flatten(),
        )
        self.embedding = nn.Sequential(nn.Linear(48, DIM_EMBEDDING), nn.ReLU())
        self.saida = nn.Linear(DIM_EMBEDDING, 1)

    def forward(self, x):
        vetor = self.embedding(self.convolucoes(x.unsqueeze(1)))
        return self.saida(vetor).squeeze(1), vetor


@torch.inference_mode()
def prever(modelo, contrato, media, escala, valores):
    if (not isinstance(valores, list) or len(valores) != NUM_FEATURES
            or any(type(v) not in (float, int) or not math.isfinite(v) for v in valores)):
        raise ValueError("features deve conter 81 números finitos na ordem do contrato")
    x = ((torch.tensor(valores, dtype=torch.float64) - media) / escala).float().unsqueeze(0)
    if not torch.isfinite(x).all():
        raise ValueError("Padronização gerou um valor não finito em float32")
    modelo.eval()
    logit, vetor = modelo(x)
    score = torch.sigmoid(logit).item()
    classe = int(score >= contrato["limiar"])
    return {"classe_id": classe, "classe": contrato["classes"][str(classe)],
            "score": score, "embedding": vetor[0].tolist()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("entrada", type=Path)
    args = parser.parse_args()
    torch.set_num_threads(2)
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    contrato = checkpoint["contrato"]
    if contrato["formato"] != FORMATO or len(contrato["ordem_features"]) != NUM_FEATURES:
        raise ValueError("Formato ou ordem de features incompatível com a CNN-1D")
    modelo = CNN1D()
    modelo.load_state_dict(checkpoint["state_dict"])
    entrada = json.loads(args.entrada.read_text(encoding="utf-8"))
    resultado = prever(modelo, contrato, checkpoint["media"], checkpoint["escala"], entrada["features"])
    print(json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
