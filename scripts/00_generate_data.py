"""
00_generate_data.py: gera dados sintéticos das duas fontes.

A mesma seed, com período fixo, gera sempre os mesmos arquivos.
"""

import random
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

SEED = 42
START = date(2024, 6, 1)
END = date(2026, 5, 31)

SEGMENTS = ["Pessoa Física", "Pessoa Jurídica", "Revendedor"]
CITIES = {
    "AL": ["Maceió", "Arapiraca"], "BA": ["Salvador", "Feira de Santana"],
    "CE": ["Fortaleza", "Juazeiro do Norte"], "MA": ["São Luís", "Imperatriz"],
    "MG": ["Belo Horizonte", "Uberlândia"], "PB": ["João Pessoa", "Campina Grande"],
    "PE": ["Recife", "Caruaru"], "PI": ["Teresina", "Parnaíba"],
    "RJ": ["Rio de Janeiro", "Niterói"], "RN": ["Natal", "Mossoró"],
    "SE": ["Aracaju", "Lagarto"], "SP": ["São Paulo", "Campinas"],
}
CATEGORIES = {
    "Eletrônicos": ["Smartphone", "Notebook", "Tablet", "Fone de Ouvido", "Smartwatch"],
    "Roupas": ["Camiseta", "Calça Jeans", "Vestido", "Jaqueta", "Tênis"],
    "Casa": ["Cadeira", "Mesa", "Luminária", "Tapete", "Almofada"],
    "Esportes": ["Bicicleta", "Haltere", "Corda de Pular", "Tapete de Yoga", "Garrafa"],
}
CHANNELS = ["Email", "Instagram", "Google Ads", "Facebook", "WhatsApp"]
ORDER_STATUSES = ["entregue", "entregue", "entregue", "cancelado", "devolvido"]
EVENT_TYPES = ["clique", "clique", "clique", "conversao", "impressao"]


def dia_entre(rng, inicio, fim):
    return inicio + timedelta(days=rng.randint(0, (fim - inicio).days))


def generate_customers(rng, fake, n=300):
    linhas = []
    for i in range(1, n + 1):
        state = rng.choice(list(CITIES))
        linhas.append({
            "customer_id": i,
            "name": fake.name(),
            "email": f"cliente{i}@example.com",
            "city": rng.choice(CITIES[state]),
            "state": state,
            "segment": rng.choice(SEGMENTS),
            "created_at": dia_entre(rng, START - timedelta(days=365), END - timedelta(days=365)),
        })
    return pd.DataFrame(linhas)


def generate_products(rng, n=80):
    tipos = [(cat, sub) for cat, subs in CATEGORIES.items() for sub in subs]
    linhas = []
    for i in range(n):
        category, subcategory = tipos[i % len(tipos)]
        cost = round(rng.uniform(15, 800), 2)
        linhas.append({
            "product_id": i + 1,
            "name": f"{subcategory} Modelo {i // len(tipos) + 1}",
            "category": category,
            "subcategory": subcategory,
            "cost": cost,
            "price": round(cost * rng.uniform(1.3, 2.5), 2),
        })
    return pd.DataFrame(linhas)


def generate_orders(rng, customers, products, n=2000):
    clientes = customers.to_dict("records")
    produtos = products.to_dict("records")
    linhas = []
    for i in range(1, n + 1):
        cliente, produto = rng.choice(clientes), rng.choice(produtos)
        qty = rng.randint(1, 5)
        discount = rng.choice([0, 0, 0, 0.05, 0.10, 0.15])
        linhas.append({
            "order_id": i,
            "customer_id": cliente["customer_id"],
            "product_id": produto["product_id"],
            "quantity": qty,
            "unit_price": produto["price"],
            "discount": discount,
            "total_price": round(qty * produto["price"] * (1 - discount), 2),
            # Ninguém compra antes de se cadastrar
            "order_date": dia_entre(rng, max(START, cliente["created_at"]), END),
            "status": rng.choice(ORDER_STATUSES),
        })
    return pd.DataFrame(linhas)


def generate_campaigns(rng, n=8):
    passo = (END - START).days // n
    linhas = []
    for i in range(1, n + 1):
        start = START + timedelta(days=(i - 1) * passo)
        channel = CHANNELS[(i - 1) % len(CHANNELS)]
        linhas.append({
            "campaign_id": i,
            "name": f"Campanha {channel} {i}",
            "channel": channel,
            "start_date": start,
            "end_date": min(END, start + timedelta(days=rng.randint(75, 150))),
            "budget": round(rng.uniform(500, 10000), 2),
        })
    return pd.DataFrame(linhas)


def generate_events(rng, customers, campaigns, n=5000):
    clientes = customers.to_dict("records")
    campanhas = campaigns.to_dict("records")
    linhas = []
    for i in range(1, n + 1):
        campanha = rng.choice(campanhas)
        dia = dia_entre(rng, campanha["start_date"], campanha["end_date"])
        # Só interage quem já é cliente, e dentro da vigência da campanha
        cliente = rng.choice([c for c in clientes if c["created_at"] <= dia])
        momento = datetime.combine(dia, time()) + timedelta(seconds=rng.randrange(86400))
        linhas.append({
            "event_id": i,
            "customer_id": cliente["customer_id"],
            "campaign_id": campanha["campaign_id"],
            "event_type": rng.choice(EVENT_TYPES),
            "timestamp": momento.isoformat(),
        })
    return pd.DataFrame(linhas)


def generate_all():
    rng = random.Random(SEED)
    fake = Faker("pt_BR")
    fake.seed_instance(SEED)
    customers = generate_customers(rng, fake)
    products = generate_products(rng)
    campaigns = generate_campaigns(rng)
    return {
        "ecommerce/customers.csv": customers,
        "ecommerce/products.csv": products,
        "ecommerce/orders.csv": generate_orders(rng, customers, products),
        "marketing/campaigns.json": campaigns,
        "marketing/events.json": generate_events(rng, customers, campaigns),
    }


def main(destino=config.RAW_DIR):
    for nome, df in generate_all().items():
        caminho = destino / nome
        caminho.parent.mkdir(parents=True, exist_ok=True)
        if caminho.suffix == ".csv":
            df.to_csv(caminho, index=False)
        else:
            df.astype({c: str for c in ("start_date", "end_date") if c in df}).to_json(
                caminho, orient="records", indent=2, force_ascii=False
            )
        print(f"  {nome}  ({len(df)} linhas)")


if __name__ == "__main__":
    main()
