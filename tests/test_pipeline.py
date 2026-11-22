"""Testes das regras. Não precisam de Docker."""

import hashlib
import importlib.util
import io
import re
import sys
from pathlib import Path

import duckdb
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import config


def carregar(nome):
    spec = importlib.util.spec_from_file_location(f"etapa_{nome}", ROOT / "scripts" / f"{nome}.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


gerador, bronze, silver, gold, materializacao = (
    carregar(n) for n in ("00_generate_data", "01_ingest_bronze", "02_process_silver",
                          "03_build_gold", "05_create_duckdb")
)


@pytest.fixture(scope="module")
def raw(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("raw")
    gerador.main(pasta)
    return pasta


@pytest.fixture(scope="module")
def processado(raw):
    return silver.process_all({n: silver.parse(n, (raw / n).read_bytes()) for n in config.FONTES})


@pytest.fixture(scope="module")
def tabelas(processado):
    return gold.build_all(processado[0])


def test_gerador_e_reproduzivel(raw, tmp_path):
    gerador.main(tmp_path)
    for nome in config.FONTES:
        assert (raw / nome).read_bytes() == (tmp_path / nome).read_bytes()


def test_catalogo_cobre_todas_as_subcategorias():
    produtos = gerador.generate_all()["ecommerce/products.csv"]
    assert produtos["category"].value_counts().to_dict() == {c: 20 for c in gerador.CATEGORIES}
    assert produtos["subcategory"].nunique() == 20
    assert produtos["name"].is_unique


def test_dados_gerados_respeitam_cadastro_e_vigencia(processado):
    limpos, rejeicoes = processado
    assert rejeicoes.empty
    assert len(limpos["ecommerce/orders"]) == 2000
    assert len(limpos["marketing/events"]) == 5000


def test_bronze_preserva_os_bytes(raw):
    class S3Falso:
        objetos = {}

        def put_object(self, **kw):
            self.objetos[kw["Key"]] = kw

    s3 = S3Falso()
    bronze.ingest(s3, raw)
    for nome in config.FONTES:
        original = (raw / nome).read_bytes()
        assert s3.objetos[nome]["Body"] == original
        assert s3.objetos[nome]["Metadata"]["sha256"] == hashlib.sha256(original).hexdigest()


@pytest.mark.parametrize("coluna, valor, motivo", [
    ("order_id", "abc", "id inválido"),
    ("customer_id", "999", "cliente inexistente"),
    ("product_id", "", "produto inexistente"),
    ("quantity", "0", "quantidade inválida"),
    ("quantity", "1.5", "quantidade inválida"),
    ("unit_price", "x", "preço inválido"),
    ("discount", "x", "desconto inválido"),
    ("discount", "1.2", "desconto inválido"),
    ("order_date", "31/02/2025", "data inválida"),
    ("order_date", "2020-01-01", "pedido antes do cadastro"),
    ("status", "perdido", "status desconhecido"),
    ("total_price", "999", "total não confere"),
    ("total_price", "", "total não confere"),
])
def test_silver_rejeita_com_motivo(coluna, valor, motivo):
    clientes = pd.DataFrame({"customer_id": [1], "created_at": [pd.Timestamp("2024-01-01")]})
    produtos = pd.DataFrame({"product_id": [1]})
    pedido = {"order_id": "1", "customer_id": "1", "product_id": "1", "quantity": "2",
              "unit_price": "10", "discount": "", "total_price": "20",
              "order_date": "2025-01-10", "status": " ENTREGUE "}
    pedido[coluna] = valor
    # Passa pelo CSV, como no pipeline
    conteudo = pd.DataFrame([pedido]).to_csv(index=False).encode()
    bruto = silver.parse("orders.csv", conteudo)
    validos, rejeitados = silver.process_orders(bruto, clientes, produtos)
    assert validos.empty
    assert rejeitados["motivo"].tolist() == [motivo]


def test_silver_padroniza_e_remove_duplicata(raw):
    bruto = pd.read_csv(io.BytesIO((raw / "ecommerce/customers.csv").read_bytes()), dtype="string")
    bruto.loc[0, "state"] = " al "
    validos, rejeitados = silver.process_customers(pd.concat([bruto, bruto.head(1)], ignore_index=True))
    assert validos.loc[0, "state"] == "AL"
    assert rejeitados["motivo"].tolist() == ["duplicada"]


@pytest.mark.parametrize("momento, tipo, esperado", [
    ("2025-03-30 12:00", "clique", 7),
    ("2025-03-30 12:00", "impressao", 0),
    ("2025-03-01 00:00", "conversao", 7),   # exatamente 30 dias
    ("2025-02-28 23:59", "clique", 0),      # fora da janela
    ("2025-03-31 00:00", "clique", 0),      # mesmo dia do pedido
    ("2025-04-01 12:00", "clique", 0),      # depois do pedido
])
def test_janela_de_atribuicao(momento, tipo, esperado):
    pedidos = pd.DataFrame({"order_id": [1], "customer_id": [1],
                            "order_date": [pd.Timestamp("2025-03-31")]})
    eventos = pd.DataFrame({"event_id": [1], "customer_id": [1], "campaign_id": [7],
                            "timestamp": [pd.Timestamp(momento)], "event_type": [tipo]})
    assert gold.associate_campaign(pedidos, eventos)["campaign_key"].tolist() == [esperado]


def test_atribuicao_usa_ultimo_evento_do_proprio_cliente():
    pedidos = pd.DataFrame({"order_id": [1], "customer_id": [1],
                            "order_date": [pd.Timestamp("2025-03-31")]})
    eventos = pd.DataFrame({
        "event_id": [1, 2, 3], "customer_id": [1, 1, 2], "campaign_id": [4, 5, 6],
        "timestamp": pd.to_datetime(["2025-03-10", "2025-03-20", "2025-03-29"]),
        "event_type": ["clique"] * 3,
    })
    assert gold.associate_campaign(pedidos, eventos)["campaign_key"].tolist() == [5]


def test_receita_custo_e_lucro_vem_da_origem(raw, tabelas):
    pedidos = pd.read_csv(raw / "ecommerce/orders.csv")
    produtos = pd.read_csv(raw / "ecommerce/products.csv")
    entregues = pedidos[pedidos["status"] == "entregue"].merge(produtos, on="product_id")
    receita = entregues["total_price"].sum()
    custo = (entregues["quantity"] * entregues["cost"]).sum()

    fato = tabelas["fact_sales"]
    assert fato["revenue"].sum() == pytest.approx(receita, abs=0.01)
    assert fato["cost"].sum() == pytest.approx(custo, abs=0.01)
    assert fato["profit"].sum() == pytest.approx(receita - custo, abs=0.01)
    assert (fato.loc[fato["status"] != "entregue", ["revenue", "cost", "profit"]] == 0).all().all()


def test_chaves_do_modelo(tabelas):
    fato = tabelas["fact_sales"]
    assert fato["order_key"].is_unique
    for dimensao in ("date", "customer", "product", "campaign"):
        chave = f"{dimensao}_key"
        assert tabelas[f"dim_{dimensao}"][chave].is_unique
        assert fato[chave].isin(tabelas[f"dim_{dimensao}"][chave]).all()


def test_todas_as_consultas_rodam(tabelas, tmp_path):
    banco = tmp_path / "gold.db"
    materializacao.materializar(tabelas, banco)
    with duckdb.connect(str(banco), read_only=True) as con:
        consultas = sorted(config.SQL_DIR.glob("*.sql"))
        assert len(consultas) == 11
        for arquivo in consultas:
            assert con.execute(arquivo.read_text(encoding="utf-8")).fetchall(), arquivo.name


def test_duckdb_igual_no_pipeline_e_no_superset():
    versoes = [re.search(r"duckdb==([\d.]+)", (ROOT / p).read_text()).group(1)
               for p in ("requirements.txt", "superset/Dockerfile")]
    assert versoes[0] == versoes[1]
