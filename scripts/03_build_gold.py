"""
03_build_gold.py: camada Gold, em esquema estrela.

Grão de fact_sales: um pedido. Receita, custo e lucro só existem para pedido
entregue; order_value guarda o valor de qualquer pedido.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
import storage

ATTRIBUTION_DAYS = 30
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def date_key(serie):
    return serie.dt.strftime("%Y%m%d").astype("int64")


def build_dim_date(orders):
    """Uma linha por dia do calendário, inclusive fins de semana."""
    dias = pd.Series(pd.date_range(orders["order_date"].min(), orders["order_date"].max(), freq="D"))
    return pd.DataFrame({
        "date_key": date_key(dias),
        "full_date": dias.dt.date,
        "day": dias.dt.day,
        "month": dias.dt.month,
        "month_name": dias.dt.month.map(lambda m: MESES[m - 1]),
        "quarter": dias.dt.quarter,
        "year": dias.dt.year,
        "week": dias.dt.isocalendar().week.astype("int64"),
        "day_of_week": dias.dt.dayofweek.map(lambda d: DIAS[d]),
        "is_weekend": dias.dt.dayofweek >= 5,
    })


def build_dim_customer(customers):
    colunas = ["customer_id", "name", "city", "state", "segment"]
    return customers[colunas].rename(columns={"customer_id": "customer_key"})


def build_dim_product(products):
    colunas = ["product_id", "name", "category", "subcategory", "cost", "price"]
    return products[colunas].rename(columns={"product_id": "product_key"})


def build_dim_campaign(campaigns):
    sem_campanha = pd.DataFrame([
        {"campaign_id": 0, "name": "Sem Campanha", "channel": "Sem campanha", "budget": 0.0}
    ])
    df = pd.concat([sem_campanha, campaigns[["campaign_id", "name", "channel", "budget"]]],
                   ignore_index=True)
    return df.rename(columns={"campaign_id": "campaign_key"})


def associate_campaign(orders, events):
    """
    Último clique ou conversão do cliente nos 30 dias anteriores ao pedido.
    O pedido só tem data, então eventos do próprio dia não entram: não dá para
    saber se vieram antes da compra.
    """
    relevantes = events[events["event_type"].isin(["clique", "conversao"])]
    eventos = relevantes[["customer_id", "timestamp", "campaign_id", "event_id"]].copy()
    eventos["timestamp"] = eventos["timestamp"].astype("datetime64[ns]")
    pedidos = orders[["order_id", "customer_id", "order_date"]].copy()
    pedidos["order_date"] = pedidos["order_date"].astype("datetime64[ns]")

    resultado = pd.merge_asof(
        pedidos.sort_values(["order_date", "order_id"]),
        eventos.sort_values(["timestamp", "event_id"]),
        left_on="order_date",
        right_on="timestamp",
        by="customer_id",
        direction="backward",
        allow_exact_matches=False,
        tolerance=pd.Timedelta(days=ATTRIBUTION_DAYS),
    )
    resultado["campaign_key"] = resultado["campaign_id"].fillna(0).astype("int64")
    return resultado[["order_id", "campaign_key"]]


def build_fact_sales(orders, products, events):
    fato = (
        orders
        .merge(products[["product_id", "cost"]], on="product_id", validate="many_to_one")
        .merge(associate_campaign(orders, events), on="order_id", validate="one_to_one")
    )
    if len(fato) != len(orders):
        raise ValueError("A fato perdeu pedidos na junção com produtos")

    entregue = fato["status"].eq("entregue")
    fato["date_key"] = date_key(fato["order_date"])
    fato["order_value"] = fato["total_price"]
    fato["revenue"] = fato["total_price"].where(entregue, 0.0)
    fato["cost"] = (fato["quantity"] * fato["cost"]).where(entregue, 0.0).round(2)
    fato["profit"] = (fato["revenue"] - fato["cost"]).round(2)
    fato = fato.rename(columns={
        "order_id": "order_key", "customer_id": "customer_key", "product_id": "product_key",
    })
    return fato[["order_key", "date_key", "customer_key", "product_key", "campaign_key",
                 "quantity", "order_value", "revenue", "cost", "profit", "discount", "status"]]


def build_all(silver):
    orders = silver["ecommerce/orders"]
    products = silver["ecommerce/products"]
    if orders.empty:
        raise ValueError("Nenhum pedido válido na Silver. Confira _quality/rejeicoes.parquet")
    return {
        "dim_date": build_dim_date(orders),
        "dim_customer": build_dim_customer(silver["ecommerce/customers"]),
        "dim_product": build_dim_product(products),
        "dim_campaign": build_dim_campaign(silver["marketing/campaigns"]),
        "fact_sales": build_fact_sales(orders, products, silver["marketing/events"]),
    }


def main():
    s3 = storage.cliente()
    nomes = [Path(f).with_suffix("").as_posix() for f in config.FONTES]
    silver = {n: storage.ler_parquet(s3, config.BUCKET_SILVER, f"{n}.parquet") for n in nomes}
    for tabela, df in build_all(silver).items():
        storage.salvar_parquet(s3, df, config.BUCKET_GOLD, f"{tabela}.parquet")


if __name__ == "__main__":
    main()
