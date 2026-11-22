-- Quais são os 10 produtos com maior receita?
SELECT
    p.name AS produto,
    p.category AS categoria,
    SUM(f.quantity) AS unidades,
    ROUND(SUM(f.revenue), 2) AS receita
FROM fact_sales f
JOIN dim_product p USING (product_key)
WHERE f.status = 'entregue'
GROUP BY f.product_key, p.name, p.category
ORDER BY receita DESC, f.product_key
LIMIT 10
