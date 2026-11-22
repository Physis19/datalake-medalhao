-- Quanta receita e lucro vêm de pedidos com e sem campanha atribuída?
SELECT
    CASE WHEN f.campaign_key = 0 THEN 'Sem campanha' ELSE 'Atribuído a campanha' END AS origem,
    c.channel AS canal,
    COUNT(*) AS total_pedidos,
    ROUND(SUM(f.revenue), 2) AS receita_total,
    ROUND(AVG(f.revenue), 2) AS ticket_medio,
    ROUND(SUM(f.profit), 2) AS lucro_total
FROM fact_sales f
JOIN dim_campaign c USING (campaign_key)
WHERE f.status = 'entregue'
GROUP BY origem, c.channel
ORDER BY receita_total DESC
