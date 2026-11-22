"""Cria o .env com senhas aleatórias. Não sobrescreve um .env existente."""

import os
import secrets
from pathlib import Path

ARQUIVO = Path(__file__).resolve().parent / ".env"


def main():
    if ARQUIVO.exists():
        print(".env já existe, nada foi alterado.")
        return
    linhas = [
        "RUSTFS_ACCESS_KEY=datalake",
        f"RUSTFS_SECRET_KEY={secrets.token_hex(20)}",
        f"SUPERSET_SECRET_KEY={secrets.token_hex(32)}",
        f"SUPERSET_ADMIN_PASSWORD={secrets.token_hex(8)}",
    ]
    with os.fdopen(os.open(ARQUIVO, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as arquivo:
        arquivo.write("\n".join(linhas) + "\n")
    print(".env criado. A senha do Superset está em SUPERSET_ADMIN_PASSWORD.")


if __name__ == "__main__":
    main()
