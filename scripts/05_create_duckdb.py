"""
05_create_duckdb.py: materializa a Gold em data/gold/gold.db para o Superset.

Grava num arquivo temporário e troca no fim: se falhar, o banco anterior continua.
"""

import os
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
import storage


def materializar(tabelas, destino=config.DB_PATH):
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_name("gold.tmp.db")
    temporario.unlink(missing_ok=True)
    # O nome do catálogo vem do arquivo, por isso o SQL não qualifica tabelas
    with duckdb.connect(str(temporario)) as con:
        for nome, df in tabelas.items():
            con.register("origem", df)
            con.execute(f"CREATE TABLE {nome} AS SELECT * FROM origem")
            con.unregister("origem")
    temporario.chmod(0o644)  # o Superset lê com outro usuário
    os.replace(temporario, destino)


def main():
    s3 = storage.cliente()
    materializar({
        t: storage.ler_parquet(s3, config.BUCKET_GOLD, f"{t}.parquet") for t in config.TABELAS_GOLD
    })
    print(f"  banco gravado em {config.DB_PATH.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
