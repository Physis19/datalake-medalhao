"""04_query_gold.py: roda as consultas de sql/ direto nos Parquets do RustFS."""

import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
import storage


def literal(valor):
    return "'" + str(valor).replace("'", "''") + "'"


def conectar():
    storage.cliente()  # falha cedo se faltar o .env
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"""
        CREATE SECRET datalake (
            TYPE s3,
            KEY_ID {literal(config.S3_ACCESS_KEY)},
            SECRET {literal(config.S3_SECRET_KEY)},
            ENDPOINT {literal(config.S3_ENDPOINT)},
            REGION {literal(config.S3_REGION)},
            USE_SSL false,
            URL_STYLE 'path'
        )
    """)
    for tabela in config.TABELAS_GOLD:
        origem = literal(f"s3://{config.BUCKET_GOLD}/{tabela}.parquet")
        con.execute(f"CREATE VIEW {tabela} AS SELECT * FROM read_parquet({origem})")
    return con


def main():
    with conectar() as con:
        for arquivo in sorted(config.SQL_DIR.glob("*.sql")):
            sql = arquivo.read_text(encoding="utf-8")
            print(f"\n== {arquivo.stem}: {sql.splitlines()[0].lstrip('- ')}")
            print(con.execute(sql).df().to_string(index=False, max_rows=14))


if __name__ == "__main__":
    main()
