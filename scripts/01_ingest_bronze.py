"""
01_ingest_bronze.py: camada Bronze.

Envia os arquivos byte a byte. O controle (horário, origem, hash) fica nos
metadados do objeto, para não alterar o conteúdo que veio da fonte.
"""

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
import storage


def ingest(s3, raw_dir=config.RAW_DIR):
    ingested_at = datetime.now(timezone.utc).isoformat()
    for nome in config.FONTES:
        conteudo = (raw_dir / nome).read_bytes()
        s3.put_object(
            Bucket=config.BUCKET_BRONZE,
            Key=nome,
            Body=conteudo,
            Metadata={
                "ingested-at": ingested_at,
                "source-file": nome,
                "sha256": hashlib.sha256(conteudo).hexdigest(),
            },
        )
        print(f"  s3://{config.BUCKET_BRONZE}/{nome}  ({len(conteudo)} bytes)")


if __name__ == "__main__":
    ingest(storage.cliente())
