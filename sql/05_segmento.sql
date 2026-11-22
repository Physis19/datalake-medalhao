-- Como cada segmento de cliente compra?
SELECT
    cu.segment AS segmento,
    COUNT(DISTINCT f.customer_key) AS clientes,
    COUNT(*) AS total_pedidos,
    ROUND(SUM(f.revenue), 2) AS receita_total,
    ROUND(AVG(f.revenue), 2) AS ticket_medio
FROM fact_sales f
JOIN dim_customer cu USING (customer_key)
WHERE f.status = 'entregue'
GROUP BY cu.segment
ORDER BY receita_total DESC
