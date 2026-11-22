-- Como volume e margem variam por faixa de desconto?
SELECT
    CAST(ROUND(f.discount * 100) AS INTEGER) || '%' AS faixa_desconto,
    COUNT(*) AS total_pedidos,
    SUM(f.quantity) AS unidades_vendidas,
    ROUND(SUM(f.revenue), 2) AS receita_total,
    ROUND(SUM(f.profit), 2) AS lucro_total,
    ROUND(AVG(f.profit), 2) AS lucro_medio_pedido,
    ROUND(100.0 * SUM(f.profit) / SUM(f.revenue), 2) AS margem_pct
FROM fact_sales f
WHERE f.status = 'entregue'
GROUP BY f.discount
ORDER BY f.discount
