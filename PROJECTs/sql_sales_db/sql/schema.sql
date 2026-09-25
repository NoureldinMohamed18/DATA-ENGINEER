-- schema.sql
-- Normalized relational schema for the sales database.
-- customers and products are dimension-like tables; orders is the fact-like table
-- referencing both via foreign keys.

DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;

CREATE TABLE customer(
    customer_id TEXT PRIMARY KEY
);
CREATE TABLE products (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL UNIQUE
);

CREATE TABLE orders (
    order_id     TEXT PRIMARY KEY,
    customer_id  TEXT NOT NULL,
    product_id   INTEGER NOT NULL,
    region       TEXT,
    order_date   TEXT NOT NULL,
    quantity     INTEGER NOT NULL,
    unit_price   REAL NOT NULL,
    total_amount REAL NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id)  REFERENCES products(product_id)
);
