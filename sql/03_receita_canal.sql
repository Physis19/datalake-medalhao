-- Como a receita se distribui entre os canais atribuídos?
SELECT
    c.channel AS canal,
    COUNT(*) AS total_pedidos,
    ROUND(SUM(f.revenue), 2) AS receita_total,
    ROUND(AVG(f.revenue), 2) AS ticket_medio
FROM fact_sales f
JOIN dim_campaign c USING (campaign_key)
WHERE f.status = 'entregue'
GROUP BY c.channel
ORDER BY receita_total DESC
