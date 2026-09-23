-- ============================================================
-- E-Commerce Database Schema
-- ============================================================
-- This script creates a complete relational database for an
-- online store with customers, products, orders, and payments.
-- ============================================================

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS customers;

-- ============================================================
-- 1. CUSTOMERS TABLE
-- ============================================================
CREATE TABLE customers(
    customer_id integer primary key autoincrement,
    first_name  VARCHAR(50) not null,
    last_name   varchar(50) not null,
    email       varchar(100) unique not null,
    phone           VARCHAR(20),
    city            VARCHAR(50),
    country         VARCHAR(50) DEFAULT 'Egypt',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active       BOOLEAN DEFAULT 1
);

-- ============================================================
-- 2. CATEGORIES TABLE
-- ============================================================
CREATE TABLE categories (
    category_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name   VARCHAR(50) NOT NULL UNIQUE,
    description     TEXT
);

-- ============================================================
-- 3. PRODUCTS TABLE
-- ============================================================
CReATE TABLE products(
    product_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name    VARCHAR(100) NOT NULL,
    category_id     INTEGER NOT NULL,
    price           DECIMAL(10, 2) NOT NULL CHECK (price > 0),
    stock_quantity  INTEGER DEFAULT 0 CHECK (stock_quantity >= 0),
    description     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ============================================================
-- 4. ORDERS TABLE
-- ============================================================
CREATE TABLE orders (
    order_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL,
    order_date      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status          VARCHAR(20) DEFAULT 'Pending' 
        CHECK (status IN ('Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled')),
    shipping_city   VARCHAR(50),
    total_amount    DECIMAL(12, 2) DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ============================================================
-- 5. ORDER_ITEMS TABLE (Junction: Orders <-> Products)
-- ============================================================
CREATE TABLE order_items (
    item_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL,
    product_id      INTEGER NOT NULL,
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    unit_price      DECIMAL(10, 2) NOT NULL,
    discount        DECIMAL(5, 2) DEFAULT 0 CHECK (discount >= 0 AND discount <= 1),
    line_total      DECIMAL(12, 2) GENERATED ALWAYS AS 
        (quantity * unit_price * (1 - discount)) STORED,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ============================================================
-- 6. PAYMENTS TABLE
-- ============================================================
CREATE TABLE payments (
    payment_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL UNIQUE,
    payment_date    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    amount          DECIMAL(12, 2) NOT NULL,
    payment_method  VARCHAR(20) DEFAULT 'Cash'
        CHECK (payment_method IN ('Cash', 'Credit Card', 'Debit Card', 'PayPal', 'Bank Transfer')),
    status          VARCHAR(20) DEFAULT 'Completed'
        CHECK (status IN ('Pending', 'Completed', 'Failed', 'Refunded')),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ============================================================
-- INSERT SAMPLE DATA
-- ============================================================

-- Categories
INSERT INTO categories (category_name, description) VALUES
('Electronics', 'Gadgets, devices, and electronic accessories'),
('Clothing', 'Men, women, and kids apparel'),
('Home & Garden', 'Furniture, decor, and gardening tools'),
('Books', 'Physical and digital books'),
('Sports', 'Sporting goods and fitness equipment');

-- Customers
INSERT INTO customers (first_name, last_name, email, phone, city, country) VALUES
('Ahmed', 'Ali', 'ahmed.ali@email.com', '01001234567', 'Cairo', 'Egypt'),
('Fatima', 'Hassan', 'fatima.h@email.com', '01011234568', 'Alexandria', 'Egypt'),
('Omar', 'Khaled', 'omar.k@email.com', '01021234569', 'Giza', 'Egypt'),
('Sara', 'Mahmoud', 'sara.m@email.com', '01031234570', 'Cairo', 'Egypt'),
('Mohamed', 'Adel', 'mohamed.a@email.com', '01041234571', 'Alexandria', 'Egypt'),
('Layla', 'Youssef', 'layla.y@email.com', '01051234572', 'Giza', 'Egypt'),
('Karim', 'Samir', 'karim.s@email.com', '01061234573', 'Cairo', 'Egypt'),
('Nour', 'Ahmed', 'nour.a@email.com', '01071234574', 'Alexandria', 'Egypt');

-- Products
INSERT INTO products (product_name, category_id, price, stock_quantity, description) VALUES
('Wireless Mouse', 1, 25.00, 150, 'Ergonomic wireless mouse with USB receiver'),
('Mechanical Keyboard', 1, 75.00, 80, 'RGB backlit mechanical keyboard'),
('Cotton T-Shirt', 2, 15.00, 300, '100% organic cotton t-shirt'),
('Running Shoes', 5, 60.00, 120, 'Lightweight running shoes size 42'),
('Coffee Table', 3, 120.00, 45, 'Modern minimalist coffee table'),
('Python Programming Book', 4, 35.00, 200, 'Learn Python from scratch'),
('Yoga Mat', 5, 20.00, 100, 'Non-slip exercise yoga mat'),
('LED Desk Lamp', 3, 30.00, 75, 'Adjustable LED desk lamp with USB port'),
('Bluetooth Speaker', 1, 45.00, 90, 'Portable waterproof Bluetooth speaker'),
('Winter Jacket', 2, 85.00, 60, 'Warm winter jacket with hood');

-- Orders
INSERT INTO orders (customer_id, order_date, status, shipping_city, total_amount) VALUES
(1, '2024-01-15 10:30:00', 'Delivered', 'Cairo', 100.00),
(2, '2024-01-16 14:15:00', 'Shipped', 'Alexandria', 60.00),
(3, '2024-01-17 09:00:00', 'Processing', 'Giza', 155.00),
(4, '2024-01-18 16:45:00', 'Delivered', 'Cairo', 35.00),
(5, '2024-01-19 11:20:00', 'Pending', 'Alexandria', 120.00),
(1, '2024-02-01 13:00:00', 'Delivered', 'Cairo', 45.00),
(6, '2024-02-05 08:30:00', 'Shipped', 'Giza', 75.00),
(7, '2024-02-10 15:45:00', 'Processing', 'Cairo', 200.00),
(8, '2024-02-12 10:00:00', 'Delivered', 'Alexandria', 30.00),
(3, '2024-03-01 12:00:00', 'Pending', 'Giza', 90.00);

-- Order Items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount) VALUES
(1, 1, 2, 25.00, 0.00),
(1, 2, 1, 75.00, 0.10),
(2, 4, 1, 60.00, 0.00),
(3, 2, 2, 75.00, 0.00),
(3, 9, 1, 45.00, 0.05),
(4, 6, 1, 35.00, 0.00),
(5, 5, 1, 120.00, 0.00),
(6, 9, 1, 45.00, 0.00),
(7, 2, 1, 75.00, 0.00),
(8, 10, 2, 85.00, 0.15),
(8, 3, 1, 15.00, 0.00),
(9, 8, 1, 30.00, 0.00),
(10, 9, 2, 45.00, 0.00);

-- Payments
INSERT INTO payments (order_id, payment_date, amount, payment_method, status) VALUES
(1, '2024-01-15 10:35:00', 100.00, 'Credit Card', 'Completed'),
(2, '2024-01-16 14:20:00', 60.00, 'Cash', 'Completed'),
(3, '2024-01-17 09:05:00', 155.00, 'Credit Card', 'Pending'),
(4, '2024-01-18 16:50:00', 35.00, 'PayPal', 'Completed'),
(5, '2024-01-19 11:25:00', 120.00, 'Cash', 'Pending'),
(6, '2024-02-01 13:05:00', 45.00, 'Credit Card', 'Completed'),
(7, '2024-02-05 08:35:00', 75.00, 'Debit Card', 'Completed'),
(8, '2024-02-10 15:50:00', 200.00, 'Credit Card', 'Pending'),
(9, '2024-02-12 10:05:00', 30.00, 'Cash', 'Completed'),
(10, '2024-03-01 12:05:00', 90.00, 'Bank Transfer', 'Pending');
