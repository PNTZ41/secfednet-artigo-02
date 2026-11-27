"""Prepara nova pasta de execução; não instala pacotes nem executa treino."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('destino', type=Path)
    p.add_argument('--zip', type=Path, required=True)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--uv', type=Path, required=True)
    p.add_argument('--python', type=Path, required=True)
    p.add_argument('--cache', type=Path, required=True)
    a = p.parse_args()
    if a.destino.exists():
        p.error('O destino precisa ser novo.')
    for f in [a.zip, a.uv, a.python]:
        if not f.is_file():
            p.error(f'Insumo/executável ausente: {f}')
    if not (a.repo / '.git').exists():
        p.error('Repo precisa ser clone ou worktree Git para consulta do estado.')
    with a.zip.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    if digest != '97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883':
        p.error('SHA-256 do dataset divergente.')
    root = Path(__file__).resolve().parent
    cfg = json.loads((root / 'controle/config.json').read_text())
    cfg.update(zip_path_vm=str(a.zip.resolve()), repo_estado=str(a.repo.resolve()),
               uv_vm=str(a.uv.resolve()), python_vm=str(a.python.resolve()), cache_uv=str(a.cache.resolve()))
    a.destino.mkdir(parents=True)
    for name in ['fonte', 'controle']:
        shutil.copytree(root / name, a.destino / name)
    (a.destino / 'controle/config.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'destino': str(a.destino.resolve()), 'zip_sha256': digest,
                      'estado': 'preparado; nenhuma instalação ou execução iniciada'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
