-- star_schema.sql
-- A small Star Schema: one fact table (fact_sales) surrounded by dimension
-- tables (dim_date, dim_region, dim_product). This is the standard shape
-- for a data warehouse: dimensions describe "who/what/when/where", the
-- fact table stores the measurable events (sales) and links to each dimension.

DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_region;
DROP TABLE IF EXISTS dim_product;

CREATE TABLE dim_date (
    date_key      TEXT PRIMARY KEY,   -- e.g. '2026-01-15'
    day           INTEGER,
    month         INTEGER,
    year          INTEGER
);

CREATE TABLE dim_region (
    region_id     INTEGER PRIMARY KEY,
    region_name   TEXT NOT NULL UNIQUE
);

CREATE TABLE dim_product (
    product_id    INTEGER PRIMARY KEY,
    product_name  TEXT NOT NULL UNIQUE
);

CREATE TABLE fact_sales (
    sale_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    date_key        TEXT NOT NULL,
    region_id       INTEGER NOT NULL,
    product_id      INTEGER NOT NULL,
    quantity        INTEGER NOT NULL,
    total_amount    REAL NOT NULL,
    temperature_c   REAL,             -- enriched from the weather source
    rained          INTEGER,          -- enriched from the weather source
    FOREIGN KEY (date_key)   REFERENCES dim_date(date_key),
    FOREIGN KEY (region_id)  REFERENCES dim_region(region_id),
    FOREIGN KEY (product_id) REFERENCES dim_product(product_id)
);
