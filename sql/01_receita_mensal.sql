-- Como a receita evoluiu no tempo?
SELECT
    d.year || '-' || LPAD(CAST(d.month AS VARCHAR), 2, '0') AS periodo,
    d.month_name AS mes,
    d.year AS ano,
    COUNT(*) AS total_pedidos,
    ROUND(SUM(f.revenue), 2) AS receita_total,
    ROUND(AVG(f.revenue), 2) AS ticket_medio
FROM fact_sales f
JOIN dim_date d USING (date_key)
WHERE f.status = 'entregue'
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month
