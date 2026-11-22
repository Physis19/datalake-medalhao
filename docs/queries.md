# Consultas analíticas

O SQL fica em `sql/` e é o mesmo no pipeline, nos testes e no dashboard. Para rodar todas: `python scripts/04_query_gold.py`.

## 1. Receita mensal

**Pergunta:** Como a receita evoluiu no tempo?

**SQL:** [01_receita_mensal.sql](../sql/01_receita_mensal.sql)

**No dashboard:** Linha

**Como ler:** O crescimento vem em parte do gerador: a base de clientes cresce ao longo do período.

## 2. Receita por categoria

**Pergunta:** Quais categorias geram mais receita e lucro?

**SQL:** [02_receita_categoria.sql](../sql/02_receita_categoria.sql)

**No dashboard:** Barras

**Como ler:** Compare receita com margem: a maior receita não é necessariamente a melhor margem.

## 3. Receita por canal atribuído

**Pergunta:** Como a receita se distribui entre os canais atribuídos?

**SQL:** [03_receita_canal.sql](../sql/03_receita_canal.sql)

**No dashboard:** Rosca

**Como ler:** Mede receita associada ao último toque. Não é taxa de conversão nem ROI.

## 4. Top 10 produtos

**Pergunta:** Quais são os 10 produtos com maior receita?

**SQL:** [04_top_produtos.sql](../sql/04_top_produtos.sql)

**No dashboard:** Tabela

**Como ler:** O ranking é por receita, não por unidades.

## 5. Desempenho por segmento

**Pergunta:** Como cada segmento de cliente compra?

**SQL:** [05_segmento.sql](../sql/05_segmento.sql)

**Como ler:** Conta só clientes com pedido entregue.

## 6. Receita histórica por cliente

**Pergunta:** Quanto cada cliente comprador já trouxe de receita, por segmento?

**SQL:** [06_receita_por_cliente.sql](../sql/06_receita_por_cliente.sql)

**No dashboard:** Barras

**Como ler:** Não é LTV: não projeta compras futuras nem desconta custo.

## 7. Receita e lucro por atribuição

**Pergunta:** Quanta receita e lucro vêm de pedidos com e sem campanha atribuída?

**SQL:** [07_receita_lucro_atribuicao.sql](../sql/07_receita_lucro_atribuicao.sql)

**No dashboard:** Barras agrupadas

**Como ler:** É o cruzamento das duas fontes. Não prova que a campanha causou a venda, e o lucro não desconta a verba.

## 8. Receita por estado

**Pergunta:** Quais estados concentram mais receita?

**SQL:** [08_receita_estado.sql](../sql/08_receita_estado.sql)

**Como ler:** Compare também o número de clientes antes de concluir que um estado compra mais.

## 9. Descontos, volume e margem

**Pergunta:** Como volume e margem variam por faixa de desconto?

**SQL:** [09_descontos.sql](../sql/09_descontos.sql)

**Como ler:** Há mais pedidos sem desconto porque o gerador sorteia 0% com mais frequência. Não mede o efeito do desconto no volume.

## 10. Categoria por mês

**Pergunta:** Como cada categoria varia ao longo dos meses?

**SQL:** [10_categoria_mes.sql](../sql/10_categoria_mes.sql)

**Como ler:** Serve para procurar sazonalidade. O gerador não simula nenhuma, então as oscilações são ruído.

## 11. Cancelamentos e devoluções

**Pergunta:** Quanto se perde em cancelamentos e devoluções?

**SQL:** [11_cancelamento_devolucao.sql](../sql/11_cancelamento_devolucao.sql)

**Como ler:** Usa order_value, porque revenue é zero nesses pedidos.
