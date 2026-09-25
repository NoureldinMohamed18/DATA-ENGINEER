# SQL Sales Database + Analytical Queries

Takes the cleaned sales data from **Project 1** and loads it into a proper
normalized relational database (SQLite), then answers real business questions
using SQL — JOINs, sub-queries, and aggregate functions.

## Schema (ER design)

```
customers                products                  orders
------------             --------------------      ---------------------------------
customer_id (PK)         product_id (PK)            order_id (PK)
                          product_name               customer_id (FK -> customers)
                                                      product_id  (FK -> products)
                                                      region
                                                      order_date
                                                      quantity
                                                      unit_price
                                                      total_amount
```

`orders` is the fact-like table; `customers` and `products` are simple
dimension tables it references via foreign keys. This is a small-scale
version of the star-schema thinking used later in Project 5.

See [`sql/schema.sql`](sql/schema.sql) for the full DDL.

## What each script does

| File | Purpose |
|---|---|
| `build_database.py` | Reads `clean_sales.csv`, creates the schema, splits the flat data into `customers` / `products` / `orders`, and inserts it |
| `sql/schema.sql` | Table definitions with primary keys and foreign keys |
| `sql/queries.sql` | 6 analytical queries, each documented with the business question it answers |
| `run_queries.py` | Runs every query in `queries.sql` against `sales.db` and prints the results |

## Queries included

1. **Each customer's spend per product** — `INNER JOIN` across orders + products, `GROUP BY`
2. **Customers who spent above the average order value** — sub-query in `WHERE`
3. **Revenue per product per region (filtered)** — `JOIN` + `GROUP BY` on multiple columns + `HAVING`
4. **Single highest-revenue product** — aggregate + `ORDER BY` + `LIMIT`
5. **Customers who never bought a "Laptop"** — anti-join pattern with `NOT IN` sub-query
6. **Regions ranked by total revenue** — `GROUP BY` + aggregate + `ORDER BY`

Full SQL with comments is in [`sql/queries.sql`](sql/queries.sql).

## How to run it

```bash
pip install -r requirements.txt

# 1. Build the database from the clean CSV (rebuilds sales.db fresh each time)
python build_database.py

# 2. Run all analytical queries and see the results
python run_queries.py
```

## Why normalize instead of just querying the CSV directly?

The raw clean data repeats `product` name and `region` text on every row.
Splitting it into `customers` / `products` / `orders` with foreign keys:
- avoids inconsistent spelling of the same product across rows
- lets you add customer or product details later without touching `orders`
- mirrors how real production databases are structured, which is what SQL
  interview questions (JOINs, keys, normalization) actually test

## Skills demonstrated

- Designing a simple normalized relational schema with foreign keys
- Loading a flat CSV into multiple related SQL tables from Python (SQLite)
- Writing INNER JOINs, sub-queries, GROUP BY / HAVING, and aggregate functions
- Separating "build the database" from "query the database" as distinct steps

## Project structure

```
project2_sql_sales_db/
├── build_database.py     # loads clean_sales.csv into sales.db
├── run_queries.py        # executes and prints every query in queries.sql
├── clean_sales.csv       # input, produced by Project 1
├── sql/
│   ├── schema.sql        # table definitions
│   └── queries.sql       # 6 documented analytical queries
├── sales.db              # generated SQLite database (after running build_database.py)
└── requirements.txt
```
