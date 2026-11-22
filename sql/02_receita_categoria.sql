-- Quais categorias geram mais receita e lucro?
SELECT
    p.category AS categoria,
    COUNT(*) AS total_pedidos,
    SUM(f.quantity) AS unidades_vendidas,
    ROUND(SUM(f.revenue), 2) AS receita_total,
    ROUND(SUM(f.profit), 2) AS lucro_total,
    ROUND(100.0 * SUM(f.profit) / SUM(f.revenue), 2) AS margem_pct
FROM fact_sales f
JOIN dim_product p USING (product_key)
WHERE f.status = 'entregue'
GROUP BY p.category
ORDER BY receita_total DESC
