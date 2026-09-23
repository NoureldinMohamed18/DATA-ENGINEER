"""
ETL Pipeline for Data Warehouse
===============================
Extracts from CSV and JSON, transforms with Pandas,
and loads into a Star Schema SQLite Data Warehouse.
"""
import pandas as pd
import sqlite3
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
DB_PATH = os.path.join(DATA_DIR, 'warehouse.db')

def extract():
    """Extract data from multiple sources."""
    print("[EXTRACT] Loading data sources...")
    
    df_csv = pd.read_csv(os.path.join(DATA_DIR, 'source1.csv'))
    print(f"[EXTRACT] CSV: {len(df_csv)} rows")
    
    with open(os.path.join(DATA_DIR, 'source2.json'), 'r', encoding='utf-8') as f:
        data_json = json.load(f)
    df_json = pd.DataFrame(data_json)
    print(f"[EXTRACT] JSON: {len(df_json)} rows")
    
    # دمج المصدرين بشكل صحيح
    df = pd.concat([df_csv, df_json], ignore_index=True)
    print(f"[EXTRACT] Combined: {len(df)} total rows")
    return df

def transform(df):
    """Clean and transform data for Star Schema."""
    print("[TRANSFORM] Cleaning data...")
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df['year'] = df['transaction_date'].dt.year
    df['month'] = df['transaction_date'].dt.month
    df['day'] = df['transaction_date'].dt.day
    df['quarter'] = df['transaction_date'].dt.quarter
    df['total_amount'] = df['quantity'] * df['unit_price']
    df['discount'] = df['total_amount'].apply(
        lambda x: 0.10 if x > 100 else (0.05 if x > 50 else 0)
    )
    df['net_amount'] = df['total_amount'] * (1 - df['discount'])
    
    for col in ['product_name', 'category', 'customer_name', 'city']:
        df[col] = df[col].str.strip().str.title()
        
    print("[TRANSFORM] Transformation complete.")
    return df

def reset_and_create_star(conn):
    """حذف وتجميع الجداول لضمان النظافة والبناء الصحيح للـ Auto-increment Keys."""
    cursor = conn.cursor()
    
    # مسح الجداول لو كانت موجودة مسبقاً
    cursor.execute("DROP TABLE IF EXISTS fact_sales")
    cursor.execute("DROP TABLE IF EXISTS dim_date")
    cursor.execute("DROP TABLE IF EXISTS dim_product")
    cursor.execute("DROP TABLE IF EXISTS dim_customer")
    
    # إعادة إنشاء هيكل الـ Star Schema
    cursor.execute("""
        CREATE TABLE dim_date (
            date_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_date DATE UNIQUE NOT NULL,
            year INTEGER,
            month INTEGER,
            month_name TEXT,
            day INTEGER,
            quarter INTEGER,
            day_of_week TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE dim_product (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT UNIQUE NOT NULL,
            category TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE dim_customer (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            city TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE fact_sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE,
            date_id INTEGER,
            product_id INTEGER,
            customer_id INTEGER,
            quantity INTEGER,
            unit_price REAL,
            total_amount REAL,
            discount REAL,
            net_amount REAL,
            FOREIGN KEY (date_id) REFERENCES dim_date(date_id),
            FOREIGN KEY (product_id) REFERENCES dim_product(product_id),
            FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id)
        )
    """)
    
    conn.commit()
    print("[LOAD] Star Schema tables created freshly.")

def load_dimensions(conn, df):
    """Load dimension tables while preserving Auto-Increment IDs."""
    # dim_date
    dates_df = df[['transaction_date', 'year', 'month', 'day', 'quarter']].drop_duplicates()
    dates_df['month_name'] = dates_df['transaction_date'].dt.strftime('%B')
    dates_df['day_of_week'] = dates_df['transaction_date'].dt.strftime('%A')
    dates_df = dates_df.rename(columns={'transaction_date': 'full_date'})
    dates_df['full_date'] = dates_df['full_date'].dt.strftime('%Y-%m-%d')
    dates_df = dates_df.drop_duplicates(subset=['full_date'])
    dates_df.to_sql('dim_date', conn, if_exists='append', index=False)
    print(f"[LOAD] Loaded {len(dates_df)} dates.")
    
    # dim_product
    products_df = df[['product_name', 'category']].drop_duplicates()
    products_df.to_sql('dim_product', conn, if_exists='append', index=False)
    print(f"[LOAD] Loaded {len(products_df)} products.")
    
    # dim_customer
    customers_df = df[['customer_name', 'city']].drop_duplicates()
    customers_df.to_sql('dim_customer', conn, if_exists='append', index=False)
    print(f"[LOAD] Loaded {len(customers_df)} customers.")

def load_facts(conn, df):
    """Load fact table with surrogate keys."""
    date_map = pd.read_sql("SELECT date_id, full_date FROM dim_date", conn)
    date_map['full_date'] = pd.to_datetime(date_map['full_date'])
    product_map = pd.read_sql("SELECT product_id, product_name FROM dim_product", conn)
    customer_map = pd.read_sql("SELECT customer_id, customer_name, city FROM dim_customer", conn)
    
    df = df.merge(date_map, left_on='transaction_date', right_on='full_date', how='left')
    df = df.merge(product_map, on='product_name', how='left')
    df = df.merge(customer_map, on=['customer_name', 'city'], how='left')
    
    facts = df[['transaction_id', 'date_id', 'product_id', 'customer_id',
                'quantity', 'unit_price', 'total_amount', 'discount', 'net_amount']]
    facts = facts.drop_duplicates(subset=['transaction_id'])
    facts.to_sql('fact_sales', conn, if_exists='append', index=False)
    print(f"[LOAD] Loaded {len(facts)} sales records.")

def run_olap_queries(conn):
    """Run OLAP analytical queries."""
    print("\n[ANALYSIS] Running OLAP queries...")

    print("\n--- ROLL-UP: Sales by Category ---")
    df = pd.read_sql("""
        SELECT dp.category, ROUND(SUM(fs.net_amount), 2) as revenue, COUNT(*) as transactions
        FROM fact_sales fs
        JOIN dim_product dp ON fs.product_id = dp.product_id
        GROUP BY dp.category
        ORDER BY revenue DESC
    """, conn)
    print(df.to_string(index=False))

    print("\n--- DRILL-DOWN: Sales by Category & Month ---")
    df = pd.read_sql("""
        SELECT dp.category, dd.month_name, ROUND(SUM(fs.net_amount), 2) as revenue
        FROM fact_sales fs
        JOIN dim_product dp ON fs.product_id = dp.product_id
        JOIN dim_date dd ON fs.date_id = dd.date_id
        GROUP BY dp.category, dd.month_name
        ORDER BY dp.category, dd.month
    """, conn)
    print(df.to_string(index=False))

    print("\n--- SLICE: Electronics Transactions ---")
    df = pd.read_sql("""
        SELECT fs.transaction_id, dp.product_name, fs.quantity, fs.net_amount
        FROM fact_sales fs
        JOIN dim_product dp ON fs.product_id = dp.product_id
        WHERE dp.category = 'Electronics'
    """, conn)
    print(df.to_string(index=False))

    print("\n--- TOP CUSTOMERS ---")
    df = pd.read_sql("""
        SELECT dc.customer_name, dc.city, ROUND(SUM(fs.net_amount), 2) as total_spent
        FROM fact_sales fs
        JOIN dim_customer dc ON fs.customer_id = dc.customer_id
        GROUP BY dc.customer_id
        ORDER BY total_spent DESC
        LIMIT 5
    """, conn)
    print(df.to_string(index=False))

def main():
    print("=" * 60)
    print("ETL PIPELINE - DATA WAREHOUSE")
    print("=" * 60)
    df = extract()
    df = transform(df)
    conn = sqlite3.connect(DB_PATH)
    reset_and_create_star(conn)
    load_dimensions(conn, df)
    load_facts(conn, df)
    run_olap_queries(conn)
    conn.close()
    print("\n[DONE] ETL Pipeline completed successfully!")
    print(f"Database saved to: {DB_PATH}")

if __name__ == "__main__":
    main()