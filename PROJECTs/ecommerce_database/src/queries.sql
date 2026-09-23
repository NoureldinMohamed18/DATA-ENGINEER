-- ============================================================
-- Advanced SQL Queries for E-Commerce Database
-- ============================================================
-- This file contains intermediate to advanced SQL queries
-- covering JOINs, Subqueries, CTEs, Window Functions, and Views.
-- ============================================================

-- ------------------------------------------------------------
-- SECTION 1: BASIC JOINS
-- ------------------------------------------------------------
-- 1.1 List all orders with customer names (INNER JOIN)
SELECT 
    o.order_id
    c.first_name || ""||c.last_name AS customer_name,
    o.order_date,
    o.status,
    o.total_amount
from orders o
inner join customers c on o.customer_id = c.customer_id
order by o.order_date desc;

-- 1.2 All orders with product details (Multi-table JOIN)
SELECT 
    o.order_id,
    c.first_name || ' ' || c.last_name AS customer,
    p.product_name,
    cat.category_name,
    oi.quantity,
    oi.unit_price,
    oi.discount,
    oi.line_total
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
JOIN categories cat ON p.category_id = cat.category_id
ORDER BY o.order_id;

-- 1.3 LEFT JOIN: All customers and their orders (even those with no orders)
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    COUNT(o.order_id) AS total_orders,
    COALESCE(SUM(o.total_amount), 0) AS total_spent
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id
ORDER BY total_spent DESC;

-- ------------------------------------------------------------
-- SECTION 2: SUBQUERIES (Nested Queries)
-- ------------------------------------------------------------

-- 2.1 Find customers who spent more than the average
select
    first_name ||' '|| last_name as customer_name,
    total_spent
from(
    select
        c.customer_id,
        c.first_name,
        c.last_name,
        sum(o.total_amount) as total_spent
    from customer c
    JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id
)customer_totals
WHERE total_spent > (
    SELECT AVG(total_amount) FROM orders
);

-- 2.2 Products with above-average price in their category
SELECT 
    p.product_name,
    cat.category_name,
    p.price,
    avg_cat.avg_price
FROM products p
JOIN categories cat ON p.category_id = cat.category_id
JOIN (
    SELECT category_id, AVG(price) AS avg_price
    FROM products
    GROUP BY category_id
) avg_cat ON p.category_id = avg_cat.category_id
WHERE p.price > avg_cat.avg_price;

-- 2.3 Find the most popular product (most quantity sold)
SELECT product_name, total_sold
FROM products p
JOIN (
    SELECT product_id, SUM(quantity) AS total_sold
    FROM order_items
    GROUP BY product_id
    ORDER BY total_sold DESC
    LIMIT 1
) popular ON p.product_id = popular.product_id;

-- ------------------------------------------------------------
-- SECTION 3: COMMON TABLE EXPRESSIONS (CTEs)
-- ------------------------------------------------------------
-- 3.1 Monthly revenue report using CTE
WITH monthly_revenue as (
    SELECT 
        strftime('%Y-%m', order_date) AS month,
        COUNT(*) as order_count,
        sum(total_amount) as revenue
    from orders
    where sataus != "Cancelled"
    GROUP BY strftime('%Y-%m', order_date)
)
SELECT 
    month,
    order_count,
    ROUND(revenue, 2) AS revenue,
    ROUND(AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m
FROM MonthlyRevenue
ORDER BY month;

-- 3.2 Customer segmentation using CTE
WITH CustomerStats AS (
    SELECT 
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        COUNT(o.order_id) AS order_count,
        SUM(o.total_amount) AS total_spent,
        MAX(o.order_date) AS last_order_date,
        JULIANDAY('now') - JULIANDAY(MAX(o.order_date)) AS days_since_last_order
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id
)
SELECT 
    customer_name,
    order_count,
    ROUND(total_spent, 2) AS total_spent,
    days_since_last_order,
    CASE 
        WHEN total_spent > 150 AND days_since_last_order < 60 THEN 'VIP'
        WHEN total_spent > 100 THEN 'Loyal'
        WHEN total_spent > 0 THEN 'Regular'
        ELSE 'Inactive'
    END AS segment
FROM CustomerStats
ORDER BY total_spent DESC;

-- ------------------------------------------------------------
-- SECTION 4: WINDOW FUNCTIONS
-- ------------------------------------------------------------

-- 4.1 Rank products by price within each category
SELECT
    cat.category_name,
    p.product_name,
    p.price,
    RANK() OVER(PARTITION BY p.category_id order by p.price desc) as price_rank,
    dense_rank() over(partition by p.category_id order by p.price desc) as dense_rank
from products p
join categories cat on p.category_id = cat.catgory_id
-- 4.2 Running total of revenue per customer
SELECT 
    o.order_id,
    c.first_name || ' ' || c.last_name AS customer,
    o.order_date,
    o.total_amount,
    SUM(o.total_amount) OVER (
        PARTITION BY o.customer_id 
        ORDER BY o.order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
ORDER BY customer, o.order_date;

-- 4.3 Compare each order to the customer's average order value
SELECT 
    o.order_id,
    c.first_name || ' ' || c.last_name AS customer,
    o.total_amount,
    ROUND(AVG(o.total_amount) OVER (PARTITION BY o.customer_id), 2) AS customer_avg,
    o.total_amount - AVG(o.total_amount) OVER (PARTITION BY o.customer_id) AS diff_from_avg
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id;

-- ------------------------------------------------------------
-- SECTION 5: VIEWS
-- ------------------------------------------------------------

-- 5.1 Create a view for order details
CREATE VIEW IF NOT EXISTS vw_order_details AS
SELECT 
    o.order_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.email,
    c.city,
    o.order_date,
    o.status AS order_status,
    p.product_name,
    cat.category_name,
    oi.quantity,
    oi.unit_price,
    oi.discount,
    oi.line_total,
    pay.payment_method,
    pay.status AS payment_status
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
JOIN categories cat ON p.category_id = cat.category_id
LEFT JOIN payments pay ON o.order_id = pay.order_id;

-- 5.2 Query the view
SELECT * FROM vw_order_details WHERE order_id = 1;

-- 5.3 Create a view for daily sales summary
CREATE VIEW IF NOT EXISTS vw_daily_sales AS
SELECT 
    DATE(order_date) AS sale_date,
    COUNT(DISTINCT order_id) AS orders_count,
    COUNT(DISTINCT customer_id) AS unique_customers,
    SUM(total_amount) AS daily_revenue,
    AVG(total_amount) AS avg_order_value
FROM orders
WHERE status != 'Cancelled'
GROUP BY DATE(order_date);

-- ------------------------------------------------------------
-- SECTION 6: STORED PROCEDURES (Simulated with SQLite scripts)
-- ------------------------------------------------------------

-- 6.1 Get customer order history
-- Usage: Replace ? with customer_id
SELECT 
    o.order_id,
    o.order_date,
    o.status,
    o.total_amount,
    GROUP_CONCAT(p.product_name, ', ') AS products
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.customer_id = 1  -- Replace with parameter
GROUP BY o.order_id
ORDER BY o.order_date DESC;

-- 6.2 Update order total (trigger simulation)
-- Calculate correct total from order_items
SELECT 
    o.order_id,
    o.total_amount AS current_total,
    SUM(oi.line_total) AS calculated_total
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id
HAVING ABS(o.total_amount - SUM(oi.line_total)) > 0.01;