"""
02_process_silver.py: camada Silver.

Tipa, padroniza e valida. Linha inválida não derruba o pipeline nem some:
vai para _quality/rejeicoes.parquet com o motivo.
"""

import io
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
import storage

STATUS = ["entregue", "cancelado", "devolvido"]
EVENTOS = ["clique", "conversao", "impressao"]


def inteiro(serie):
    numero = pd.to_numeric(serie, errors="coerce")
    return numero.where(numero % 1 == 0).astype("Int64")


def numero(serie):
    return pd.to_numeric(serie, errors="coerce").astype("float64")


def data(serie):
    return pd.to_datetime(serie, errors="coerce", format="ISO8601").astype("datetime64[ns]")


def texto(serie):
    return serie.astype("string").str.strip().replace("", pd.NA)


def separar(df, entidade, chave, regras):
    """Cada linha recebe o primeiro motivo aplicável. Duplicata é avaliada entre as válidas."""
    motivo = pd.Series(pd.NA, index=df.index, dtype="string")
    for descricao, invalida in regras.items():
        motivo[invalida.fillna(True).astype(bool) & motivo.isna()] = descricao
    validas = df[motivo.isna()]
    motivo[validas.index[validas[chave].duplicated()]] = "duplicada"

    rejeitadas = pd.DataFrame({
        "entidade": entidade,
        "chave": df.loc[motivo.notna(), chave].astype("string"),
        "motivo": motivo[motivo.notna()],
    })
    limpas = df[motivo.isna()].reset_index(drop=True)
    inteiros = {c: "int64" for c in limpas if str(limpas[c].dtype) == "Int64"}
    return limpas.astype(inteiros), rejeitadas


def process_customers(bruto):
    df = bruto.copy()
    df["customer_id"] = inteiro(df["customer_id"])
    for coluna in ("name", "city", "segment"):
        df[coluna] = texto(df[coluna])
    df["email"] = texto(df["email"]).str.lower()
    df["state"] = texto(df["state"]).str.upper()
    df["created_at"] = data(df["created_at"])
    return separar(df, "customers", "customer_id", {
        "id inválido": df["customer_id"].isna(),
        "nome ausente": df["name"].isna(),
        "data de cadastro inválida": df["created_at"].isna(),
    })


def process_products(bruto):
    df = bruto.copy()
    df["product_id"] = inteiro(df["product_id"])
    for coluna in ("name", "category", "subcategory"):
        df[coluna] = texto(df[coluna])
    for coluna in ("cost", "price"):
        df[coluna] = numero(df[coluna]).round(2)
    return separar(df, "products", "product_id", {
        "id inválido": df["product_id"].isna(),
        "nome ou categoria ausente": df["name"].isna() | df["category"].isna(),
        "custo inválido": ~(df["cost"] > 0),
        "preço inválido": ~(df["price"] > 0),
    })


def process_orders(bruto, customers, products):
    df = bruto.copy()
    for coluna in ("order_id", "customer_id", "product_id", "quantity"):
        df[coluna] = inteiro(df[coluna])
    for coluna in ("unit_price", "total_price"):
        df[coluna] = numero(df[coluna]).round(2)
    # Desconto vazio é zero; desconto ilegível é erro
    df["discount"] = numero(texto(df["discount"]).fillna("0"))
    df["order_date"] = data(df["order_date"])
    df["status"] = texto(df["status"]).str.lower()

    cadastro = df["customer_id"].map(customers.set_index("customer_id")["created_at"])
    esperado = df["quantity"].astype("float64") * df["unit_price"] * (1 - df["discount"])
    return separar(df, "orders", "order_id", {
        "id inválido": df["order_id"].isna(),
        "cliente inexistente": ~df["customer_id"].isin(customers["customer_id"]),
        "produto inexistente": ~df["product_id"].isin(products["product_id"]),
        "quantidade inválida": ~(df["quantity"] > 0),
        "preço inválido": ~(df["unit_price"] > 0),
        "desconto inválido": ~df["discount"].between(0, 1, inclusive="left"),
        "data inválida": df["order_date"].isna(),
        "pedido antes do cadastro": df["order_date"] < cadastro,
        "status desconhecido": ~df["status"].isin(STATUS),
        "total não confere": ~((df["total_price"] - esperado).abs() <= 0.011),
    })


def process_campaigns(bruto):
    df = bruto.copy()
    df["campaign_id"] = inteiro(df["campaign_id"])
    for coluna in ("name", "channel"):
        df[coluna] = texto(df[coluna])
    for coluna in ("start_date", "end_date"):
        df[coluna] = data(df[coluna])
    df["budget"] = numero(df["budget"]).round(2)
    return separar(df, "campaigns", "campaign_id", {
        # O id 0 é reservado para "Sem Campanha" na Gold
        "id inválido": ~(df["campaign_id"] > 0),
        "canal ausente": df["channel"].isna(),
        "vigência inválida": ~(df["start_date"] <= df["end_date"]),
        "orçamento inválido": ~(df["budget"] >= 0),
    })


def process_events(bruto, customers, campaigns):
    df = bruto.copy()
    for coluna in ("event_id", "customer_id", "campaign_id"):
        df[coluna] = inteiro(df[coluna])
    df["timestamp"] = data(df["timestamp"])
    df["event_type"] = texto(df["event_type"]).str.lower()

    campanha = campaigns.set_index("campaign_id")
    inicio = df["campaign_id"].map(campanha["start_date"])
    fim = df["campaign_id"].map(campanha["end_date"])
    cadastro = df["customer_id"].map(customers.set_index("customer_id")["created_at"])
    return separar(df, "events", "event_id", {
        "id inválido": df["event_id"].isna(),
        "cliente inexistente": ~df["customer_id"].isin(customers["customer_id"]),
        "campanha inexistente": ~df["campaign_id"].isin(campaigns["campaign_id"]),
        "tipo desconhecido": ~df["event_type"].isin(EVENTOS),
        "data inválida": df["timestamp"].isna(),
        "evento antes do cadastro": df["timestamp"] < cadastro,
        "fora da vigência": ~df["timestamp"].dt.normalize().between(inicio, fim),
    })


def process_all(brutos):
    customers, r1 = process_customers(brutos["ecommerce/customers.csv"])
    products, r2 = process_products(brutos["ecommerce/products.csv"])
    orders, r3 = process_orders(brutos["ecommerce/orders.csv"], customers, products)
    campaigns, r4 = process_campaigns(brutos["marketing/campaigns.json"])
    events, r5 = process_events(brutos["marketing/events.json"], customers, campaigns)
    limpos = {
        "ecommerce/customers": customers,
        "ecommerce/products": products,
        "ecommerce/orders": orders,
        "marketing/campaigns": campaigns,
        "marketing/events": events,
    }
    return limpos, pd.concat([r1, r2, r3, r4, r5], ignore_index=True)


def parse(nome, conteudo):
    if nome.endswith(".csv"):
        return pd.read_csv(io.BytesIO(conteudo), dtype="string")
    return pd.DataFrame(json.loads(conteudo)).astype("string")


def main():
    s3 = storage.cliente()
    brutos = {n: parse(n, storage.ler_bytes(s3, config.BUCKET_BRONZE, n)) for n in config.FONTES}
    limpos, rejeicoes = process_all(brutos)
    for nome, df in limpos.items():
        storage.salvar_parquet(s3, df, config.BUCKET_SILVER, f"{nome}.parquet")
    storage.salvar_parquet(s3, rejeicoes, config.BUCKET_SILVER, "_quality/rejeicoes.parquet")


if __name__ == "__main__":
    main()
