-- queries.sql
-- Analytical queries demonstrating JOINs, sub-queries, and aggregate functions.
-- Each query is documented with the business question it answers.

-- ============================================================
-- Q1: What is each customer's favorite product (by total spend)?
-- Demonstrates: INNER JOIN across 3 tables, GROUP BY, aggregate SUM
-- ============================================================

SELECT 
    o.customer_id,
    p.product_name,
    SUM(o.total_amount) AS total_spent
FROM orders o 
INNER JOIN product p o.product_id=p.product_id
GROUP BY o.customer_id,p.product_name
ORDER BY o.customer_id,total_spent DESC;

-- ============================================================
-- Q2: Which customers spent more than the average order value?
-- Demonstrates: Sub-query in the WHERE clause
-- ============================================================
SELECT 
    o.order_id,
    o.customer_id,
    o.total_amount
FROM orders o 
WHERE o.total_amount > (
    SELECT AVG(total_amount) FROM orders
)
ORDER BY o.total_amount DESC;

-- ============================================================
-- Q3: Total revenue and order count per product, per region.
-- Demonstrates: JOIN + GROUP BY on multiple columns + HAVING
-- ============================================================
SELECT
    p.product_name,
    o.region,
    COUNT(o.order_id) AS order_count,
    SUM(o.total_amount) AS total_revenue
FROM orders o 
INNER JOIN product p on o.product_id=p.product_id
GROUP BY p.product_name ,o.region
HAVING SUM(o.total_amount) >1000
ORDER BY total_revenue DESC;

-- ============================================================
-- Q4: Which product generates the highest revenue overall?
-- Demonstrates: Simple aggregate + ORDER BY + LIMIT
-- ============================================================
SELECT
    p.product_name,
    SUM(o.total_amount) AS total_revenue
FROM orders o
INNER JOIN products p ON o.product_id = p.product_id
GROUP BY p.product_name
ORDER BY total_revenue DESC
LIMIT 1;


-- ============================================================
-- Q5: List customers who have never ordered a "Laptop".
-- Demonstrates: Sub-query with NOT IN (anti-join pattern)
-- ============================================================
SELECT DISTINCT customer_id
FROM orders
WHERE customer_id NOT IN (
    SELECT o.customer_id
    FROM orders o
    INNER JOIN products p ON o.product_id = p.product_id
    WHERE p.product_name = 'Laptop'
);


-- ============================================================
-- Q6: Rank regions by total revenue (highest first).
-- Demonstrates: GROUP BY + aggregate + ORDER BY, used as a
-- foundation for a "self-join" style ranking if needed later.
-- ============================================================
SELECT
    region,
    SUM(total_amount) AS revenue,
    COUNT(order_id)   AS orders
FROM orders
GROUP BY region
ORDER BY revenue DESC;