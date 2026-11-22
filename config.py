"""Configurações do projeto. Credenciais vêm do .env (veja criar_env.py)."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "gold" / "gold.db"
SQL_DIR = ROOT / "sql"

S3_ENDPOINT = f"127.0.0.1:{os.getenv('RUSTFS_PORT', '9000')}"
S3_ACCESS_KEY = os.getenv("RUSTFS_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("RUSTFS_SECRET_KEY", "")
S3_REGION = "us-east-1"

BUCKET_BRONZE = "bronze"
BUCKET_SILVER = "silver"
BUCKET_GOLD = "gold"

FONTES = [
    "ecommerce/customers.csv",
    "ecommerce/products.csv",
    "ecommerce/orders.csv",
    "marketing/campaigns.json",
    "marketing/events.json",
]
TABELAS_GOLD = ["fact_sales", "dim_date", "dim_customer", "dim_product", "dim_campaign"]
