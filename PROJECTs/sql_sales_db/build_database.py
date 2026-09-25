"""
build_database.py
-------------------
Project 2: SQL Sales Database + Analytical Queries

Takes the clean sales data from Project 1 (clean_sales.csv) and loads it into
a proper relational SQLite database with a normalized schema:

    customers (customer_id)
    products  (product_id, product_name)
    orders    (order_id, customer_id, product_id, region, order_date, quantity, unit_price, total_amount)

This demonstrates going from a flat CSV to a normalized relational design —
exactly what "Python for Databases" (SQLite from Python) covers.
"""
import sqlite3
import pandas as pd
from pathlib import Path
DB_PATH = Path("sales.db")
CSV_PATH = Path("clean_sales.csv")
SCHEMA_PATH = Path("sql/schema.sql")

def create_schema(conn:sqlite3.Connection)->None:
    """Create normalized tables from schema.sql."""
    schema_sql=SCHEMA_PATH.read_text(encoding='utf-8')
    conn.executescript(schema_sql)
    print("[SCHEMA] Tables created: customers, products, orders")
    
def load_data(conn:sqlite3.Connection)->None:
    df=pd.read_csv(CSV_PATH)
    customer=df[['customer_id']].drop_duplicates().reset_index(drop=True)
    customer.to_sql('customers',conn,if_exists='append',index=False)
    print(f"[LOAD] Inserted {len(customer)} customers")
    
    unique_products=sorted(df['product'].unique())
    product=pd.DataFrame({
        "product_id":range(1,len(unique_products)+1),
        'products_name':unique_products,
    })
    product.to_sql("products", conn, if_exists="append", index=False)
    print(f"[LOAD] Inserted {len(product)} products")
    
    product_map=dict(zip(product['product_name'],product['product_id']))
    df["product_id"] = df["product"].map(product_map)
    orders = df[[
        "order_id", "customer_id", "product_id", "region",
        "order_date", "quantity", "unit_price", "total_amount"
    ]]
    orders.to_sql("orders", conn, if_exists="append", index=False)
    print(f"[LOAD] Inserted {len(orders)} orders")
    
def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
    
    conn=sqlite3.connect(DB_PATH)
    try:
        create_schema(conn)
        load_data(conn)
        conn.commit()
        print(f"\n[DONE] Database built at {DB_PATH}")
    finally:
        conn.close()
        
if __name__=="__main__":
    main()
    