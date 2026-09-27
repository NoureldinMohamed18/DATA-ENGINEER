-- analysis_queries.sql
-- Business questions answered using the star schema warehouse.

-- ============================================================
-- Q1: Does it rain more where sales are higher or lower?
-- Business question this project was built to answer.
-- ============================================================
SELECT
    dr.region_name,
    SUM(fs.total_amount)                         AS total_revenue,
    ROUND(AVG(fs.temperature_c), 1)              AS avg_temperature,
    SUM(fs.rained)                                AS rainy_days_with_sales,
    COUNT(*)                                      AS total_orders
FROM fact_sales fs
JOIN dim_region dr ON fs.region_id = dr.region_id
GROUP BY dr.region_name
ORDER BY total_revenue DESC;


-- ============================================================
-- Q2: Average order value on rainy days vs non-rainy days.
-- ============================================================
SELECT
    CASE WHEN rained = 1 THEN 'Rainy day' ELSE 'Dry day' END AS day_type,
    ROUND(AVG(total_amount), 2) AS avg_order_value,
    COUNT(*) AS num_orders
FROM fact_sales
GROUP BY day_type;


-- ============================================================
-- Q3: Revenue by product, broken down by month.
-- ============================================================
SELECT
    dp.product_name,
    dd.year,
    dd.month,
    SUM(fs.total_amount) AS revenue
FROM fact_sales fs
JOIN dim_product dp ON fs.product_id = dp.product_id
JOIN dim_date dd     ON fs.date_key = dd.date_key
GROUP BY dp.product_name, dd.year, dd.month
ORDER BY revenue DESC
LIMIT 15;


-- ============================================================
-- Q4: Which region has the strongest correlation-like pattern
-- between temperature and order value? (simple average-based view;
-- a real correlation coefficient would need a stats library)
-- ============================================================
SELECT
    dr.region_name,
    ROUND(AVG(CASE WHEN fs.temperature_c >= 22 THEN fs.total_amount END), 2) AS avg_sale_hot_days,
    ROUND(AVG(CASE WHEN fs.temperature_c <  22 THEN fs.total_amount END), 2) AS avg_sale_cooler_days
FROM fact_sales fs
JOIN dim_region dr ON fs.region_id = dr.region_id
GROUP BY dr.region_name;
