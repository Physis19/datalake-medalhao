"""Roda o pipeline inteiro e para na primeira falha."""

import subprocess
import sys

from config import ROOT

ETAPAS = [
    "setup_storage.py",
    "scripts/00_generate_data.py",
    "scripts/01_ingest_bronze.py",
    "scripts/02_process_silver.py",
    "scripts/03_build_gold.py",
    "scripts/04_query_gold.py",
    "scripts/05_create_duckdb.py",
]

if __name__ == "__main__":
    for etapa in ETAPAS:
        print(f"\n### {etapa}", flush=True)
        codigo = subprocess.run([sys.executable, str(ROOT / etapa)]).returncode
        if codigo:
            sys.exit(f"Falhou em {etapa}")
    print("\nPipeline concluído.")
