"""Reconcilia tabelas agregadas e, opcionalmente, compara uma execução anterior."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def executar(pasta, anterior=None):
    def ler(nome):
        with (pasta / nome).open() as f:
            return list(csv.DictReader(f))
    j = json.loads((pasta / "resultado.json").read_text())
    afetadas, sims = ler("linhas_afetadas_por_classe.csv"), ler("simulacoes_por_classe.csv")
    pares, conflitos = ler("cruzamentos.csv"), ler("conflitos.csv")
    assert len(pares) == 15 and len(conflitos) == 30 and len(ler("qualidade_por_feature.csv")) == 648
    assert j["totais_referencia"] == {"treino": 1184428, "validacao": 360079, "teste": 543490}
    for p in pares:
        for lado in ["a", "b"]:
            for escala in ["nominal", "binario"]:
                linhas = [r for r in afetadas if r["par"] == p["par"] and r["tipo"] == p["tipo"]
                          and r["lado"] == lado and r["escala"] == escala]
                assert sum(int(r["linhas_afetadas"]) for r in linhas) == int(p["linhas_" + lado])
        c = {r["escala"]: r for r in conflitos if r["par"] == p["par"] and r["tipo"] == p["tipo"]}
        assert int(c["nominal"]["chaves_com_conflito"]) >= int(c["binario"]["chaves_com_conflito"])
        assert int(c["nominal"]["pares_de_linhas_com_rotulos_diferentes"]) >= int(c["binario"]["pares_de_linhas_com_rotulos_diferentes"])
        for r in c.values():
            assert int(r["chaves_com_conflito"]) <= int(p["chaves_comuns"])
            for lado in ["a", "b"]:
                assert int(r[f"linhas_{lado}_com_rotulo_oposto_no_outro_lado"]) <= int(
                    r[f"linhas_{lado}_em_chaves_conflitantes"]) <= int(p["linhas_" + lado])
        if p["tipo"] in ["vetor_float64", "grupo_bidirecional"]:
            posterior = p["par"].split("_x_")[1]
            removidas = sum(int(r["excluidas"]) for r in sims if r["cenario"] ==
                "par_" + p["par"] + "_" + p["tipo"] and r["conjunto"] == posterior and r["escala"] == "binario")
            assert removidas == int(p["linhas_b"])
    for r in sims:
        antes, depois, excluidas = [int(r[k]) for k in ["antes", "depois", "excluidas"]]
        assert antes - excluidas == depois and 0 <= depois <= antes
        if antes:
            assert math.isclose(float(r["pct_da_classe_excluida"]), excluidas / antes * 100, abs_tol=1e-10)
    for total in j["simulacoes_totais"]:
        for escala in ["nominal", "binario"]:
            r = [x for x in sims if x["cenario"] == total["cenario"] and
                 x["conjunto"] == total["conjunto"] and x["escala"] == escala]
            assert sum(int(x["antes"]) for x in r) == total["antes"]
            assert sum(int(x["depois"]) for x in r) == total["depois"]
            assert math.isclose(sum(float(x["pct_composicao_depois"]) for x in r), 100, abs_tol=1e-8)
    comparacoes = []
    if anterior:
        for p in sorted(pasta.glob("*.csv")):
            assert p.read_bytes() == (anterior / p.name).read_bytes(), p.name
            comparacoes.append({"arquivo": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
        old = json.loads((anterior / "resultado.json").read_text())
        for k in j.keys() - {"tempo_total_s", "pico_rss_kib"}:
            assert old[k] == j[k], k
    print(json.dumps({"status": "OK", "checagens": ["contagens binárias e nominais",
        "antes - excluídas = depois e percentuais", "exclusão por par corresponde às linhas posteriores afetadas",
        "conflitos nominais abrangem binários e linhas estão contidas no cruzamento"],
        "csvs_identicos_a_execucao_anterior": comparacoes}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("resultados", type=Path)
    p.add_argument("--comparar", type=Path)
    a = p.parse_args()
    executar(a.resultados, a.comparar)
