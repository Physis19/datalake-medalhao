"""Leitura e escrita no storage S3 (RustFS)."""

import io

import boto3
import pandas as pd
from botocore.config import Config

import config


def cliente():
    if not config.S3_ACCESS_KEY or not config.S3_SECRET_KEY:
        raise SystemExit("Credenciais ausentes. Rode primeiro: python criar_env.py")
    return boto3.client(
        "s3",
        endpoint_url=f"http://{config.S3_ENDPOINT}",
        aws_access_key_id=config.S3_ACCESS_KEY,
        aws_secret_access_key=config.S3_SECRET_KEY,
        region_name=config.S3_REGION,
        config=Config(s3={"addressing_style": "path"}),
    )


def ler_bytes(s3, bucket, key):
    return s3.get_object(Bucket=bucket, Key=key)["Body"].read()


def ler_parquet(s3, bucket, key):
    return pd.read_parquet(io.BytesIO(ler_bytes(s3, bucket, key)))


def salvar_parquet(s3, df, bucket, key):
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine="pyarrow")
    s3.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())
    print(f"  s3://{bucket}/{key}  ({len(df)} linhas)")
