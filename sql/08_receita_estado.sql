-- Quais estados concentram mais receita?
SELECT
    cu.state AS estado,
    COUNT(DISTINCT f.customer_key) AS clientes,
    COUNT(*) AS total_pedidos,
    ROUND(SUM(f.revenue), 2) AS receita_total,
    ROUND(SUM(f.profit), 2) AS lucro_total,
    ROUND(AVG(f.revenue), 2) AS ticket_medio
FROM fact_sales f
JOIN dim_customer cu USING (customer_key)
WHERE f.status = 'entregue'
GROUP BY cu.state
ORDER BY receita_total DESC
