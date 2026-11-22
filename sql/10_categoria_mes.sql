-- Como cada categoria varia ao longo dos meses?
SELECT
    p.category AS categoria,
    d.year AS ano,
    d.month AS mes,
    d.month_name AS mes_nome,
    COUNT(*) AS total_pedidos,
    ROUND(SUM(f.revenue), 2) AS receita_total
FROM fact_sales f
JOIN dim_date d USING (date_key)
JOIN dim_product p USING (product_key)
WHERE f.status = 'entregue'
GROUP BY p.category, d.year, d.month, d.month_name
ORDER BY p.category, d.year, d.month
