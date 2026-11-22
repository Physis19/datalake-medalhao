-- Quanto se perde em cancelamentos e devoluções?
SELECT
    p.category AS categoria,
    COUNT(*) AS total_pedidos,
    COUNT(*) FILTER (WHERE f.status = 'entregue') AS entregues,
    COUNT(*) FILTER (WHERE f.status = 'cancelado') AS cancelados,
    COUNT(*) FILTER (WHERE f.status = 'devolvido') AS devolvidos,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.status = 'cancelado') / COUNT(*), 2) AS taxa_cancelamento_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.status = 'devolvido') / COUNT(*), 2) AS taxa_devolucao_pct,
    ROUND(COALESCE(SUM(f.order_value) FILTER (WHERE f.status <> 'entregue'), 0), 2) AS valor_nao_realizado
FROM fact_sales f
JOIN dim_product p USING (product_key)
GROUP BY p.category
ORDER BY valor_nao_realizado DESC
