"""Monta o zip de importação do dashboard, usando os mesmos SQL de sql/."""

import sys
import zipfile
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
DATASETS = {
    "receita_mensal": "01_receita_mensal",
    "receita_categoria": "02_receita_categoria",
    "receita_canal": "03_receita_canal",
    "top_produtos": "04_top_produtos",
    "receita_por_cliente": "06_receita_por_cliente",
    "receita_lucro_atribuicao": "07_receita_lucro_atribuicao",
}


def main(destino):
    origem = AQUI / "dashboard"
    with zipfile.ZipFile(destino, "w") as pacote:
        for arquivo in sorted(origem.rglob("*.yaml")):
            relativo = arquivo.relative_to(origem)
            conteudo = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
            if relativo.parts[0] == "datasets":
                consulta = AQUI.parent / "sql" / f"{DATASETS[arquivo.stem]}.sql"
                conteudo["sql"] = consulta.read_text(encoding="utf-8")
            pacote.writestr(f"dashboard/{relativo.as_posix()}", yaml.safe_dump(conteudo, allow_unicode=True))


if __name__ == "__main__":
    main(sys.argv[1])
