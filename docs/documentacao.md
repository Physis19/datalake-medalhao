# Documentação técnica

## Visão geral

O projeto simula um e-commerce com duas fontes independentes, vendas e marketing, e as refina
até um modelo analítico. Cada camada tem uma responsabilidade.

| Camada | Responsabilidade | Formato | Local |
|---|---|---|---|
| Bronze | Guardar o que chegou | CSV e JSON originais | `s3://bronze/` |
| Silver | Tipar, padronizar e validar | Parquet | `s3://silver/` |
| Gold | Modelar para análise | Parquet | `s3://gold/` |
| Consumo | Servir o dashboard | DuckDB | `data/gold/gold.db` |

## Etapas

`python run.py` executa na ordem abaixo e para na primeira falha. Cada script também roda sozinho.

### Setup: `setup_storage.py`

Cria os buckets. Pode rodar mais de uma vez.

### 00: geração (`00_generate_data.py`)

| Arquivo | Linhas | Conteúdo |
|---|---:|---|
| `customers.csv` | 300 | Clientes em 12 estados e 3 segmentos |
| `products.csv` | 80 | 4 categorias com 5 subcategorias cada |
| `orders.csv` | 2.000 | Pedidos de 01/06/2024 a 31/05/2026 |
| `campaigns.json` | 8 | Campanhas em 5 canais |
| `events.json` | 5.000 | Impressões, cliques e conversões |

A seed e o período são fixos. Ninguém compra ou interage antes de se cadastrar, e os eventos
ficam dentro da vigência da campanha. Os e-mails usam o domínio reservado `example.com`.

### 01: Bronze (`01_ingest_bronze.py`)

Envia cada arquivo sem abrir como tabela. Os metadados do objeto guardam `ingested-at`,
`source-file` e `sha256`. A camada guarda a última carga, sem histórico de versões.

### 02: Silver (`02_process_silver.py`)

Lê tudo como texto, converte e valida. A linha inválida recebe o primeiro motivo aplicável e
vai para `s3://silver/_quality/rejeicoes.parquet`.

| Entidade | Motivos de rejeição |
|---|---|
| Clientes | id inválido, nome ausente, data de cadastro inválida |
| Produtos | id inválido, nome ou categoria ausente, custo inválido, preço inválido |
| Pedidos | id, cliente, produto, quantidade, preço, desconto, data ou status inválido; anterior ao cadastro; total que não confere |
| Campanhas | id inválido, canal ausente, vigência ou orçamento inválido |
| Eventos | id, cliente, campanha, tipo ou data inválida; anterior ao cadastro; fora da vigência |
| Todas | chave duplicada (fica a primeira linha válida) |

Desconto vazio vale zero. Desconto ilegível é rejeitado. Com os dados gerados o arquivo de
rejeições fica vazio: as regras são exercitadas com dados inválidos nos testes.

### 03: Gold (`03_build_gold.py`)

Constrói o esquema estrela. O grão de `fact_sales` é **um pedido**.

```
                 dim_date
                    │
dim_customer ── fact_sales ── dim_product
                    │
               dim_campaign
```

| Tabela | Chave | Colunas |
|---|---|---|
| `fact_sales` | `order_key` | chaves das dimensões, `quantity`, `order_value`, `revenue`, `cost`, `profit`, `discount`, `status` |
| `dim_date` | `date_key` | `full_date`, `day`, `month`, `month_name`, `quarter`, `year`, `week`, `day_of_week`, `is_weekend` |
| `dim_customer` | `customer_key` | `name`, `city`, `state`, `segment` |
| `dim_product` | `product_key` | `name`, `category`, `subcategory`, `cost`, `price` |
| `dim_campaign` | `campaign_key` | `name`, `channel`, `budget` |

| Métrica | Pedido entregue | Cancelado ou devolvido |
|---|---|---|
| `order_value` | total com desconto | total com desconto |
| `revenue` | total com desconto | 0 |
| `cost` | quantidade × custo do produto | 0 (supõe que o produto volta ao estoque) |
| `profit` | `revenue - cost` | 0 |

Para ticket médio, filtre `status = 'entregue'`, senão os zeros entram na média.

**Atribuição:** cada pedido recebe a campanha do último clique ou conversão do mesmo cliente
nos 30 dias anteriores. Impressão não conta. Como o pedido não tem horário, evento do mesmo
dia também não conta. Sem evento, a chave é `0` (Sem campanha), o que evita nulos na junção.

### 04: consultas (`04_query_gold.py`)

Lê os Parquets direto do S3, com a extensão `httpfs` do DuckDB, e roda os arquivos de `sql/`.

### 05: materialização (`05_create_duckdb.py`)

Grava a Gold num arquivo DuckDB temporário e o renomeia para `gold.db` no fim.

## Superset

A imagem em `superset/Dockerfile` adiciona o driver do DuckDB. Ao subir, `iniciar.sh` prepara
o banco interno, cria o admin e importa o dashboard de `superset/dashboard/`. O SQL dos
datasets é injetado a partir de `sql/` por `empacotar.py`.

- O `gold.db` é montado somente para leitura.
- Depois de mudar `sql/` ou o dashboard, rode `docker compose up -d --build`.
- Ao reiniciar, o layout do dashboard volta ao que está versionado. Exporte o que editar na interface.
- Trocar a senha no `.env` não altera um admin já criado. Use `superset fab reset-password`.

## Testes

`python -m pytest` cobre reprodutibilidade, fidelidade da Bronze, rejeições da Silver, limites
da janela de atribuição, conciliação de receita, custo e lucro com a origem, chaves do modelo,
execução das 11 consultas e versão do DuckDB. Não testa Docker nem a interface do Superset.

## Decisões

- **RustFS:** compatível com S3, licença Apache 2.0. O código usa a API S3 padrão.
- **Parquet:** colunar, comprimido e com tipos, adequado a leitura analítica.
- **DuckDB:** consulta Parquet e S3 sem servidor de banco.
- **Janela de 30 dias:** escolha de regra de negócio. Mudar o valor muda o resultado dos canais.
- **Carga completa:** simples e repetível neste volume. Em produção seria incremental.
