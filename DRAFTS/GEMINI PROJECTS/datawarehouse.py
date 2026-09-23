import pandas as pd
import numpy as np
import sqlite3
# 1. Data Generation
np.random.seed(42)
date_range = pd.date_range(start="2025-01-01", end="2025-12-31", freq="D")
n_records = len(date_range) * 3
df_source = pd.DataFrame({
    'transaction_date': np.random.choice(date_range, size=n_records),
    'product_id': np.random.choice([101, 102, 103, 104, 105], size=n_records),
    'customer_id': np.random.choice([1, 2, 3, 4, 5, 6, 7, 8], size=n_records),
    'store_location': np.random.choice(['Cairo', 'Alexandria', 'Giza'], size=n_records),
    'units_sold': np.random.randint(1, 10, size=n_records),
    'unit_price': np.random.choice([50.0, 120.0, 250.0, 450.0, 800.0], size=n_records)
})
df_source['total_amount'] = df_source['units_sold'] * df_source['unit_price']
df_source = df_source.sort_values('transaction_date').reset_index(drop=True)
# 2. Star Schema Modeling
dim_date = pd.DataFrame({'full_date': date_range})
dim_date['date_key'] = dim_date['full_date'].dt.strftime('%Y%m%d').astype(int)
dim_date['year'] = dim_date['full_date'].dt.year
dim_date['quarter'] = dim_date['full_date'].dt.quarter
dim_date['month'] = dim_date['full_date'].dt.month
dim_date['is_weekend'] = dim_date['full_date'].dt.dayofweek.isin([4, 5]).astype(int)
dim_product = pd.DataFrame({
    'product_id': [101, 102, 103, 104, 105],
    'product_name': ['Smartphone', 'Laptop', 'Tablet', 'Smartwatch', 'Headphones'],
    'category': ['Electronics', 'Computers', 'Computers', 'Wearables', 'Audio']
})
df_source['date_key'] = pd.to_datetime(df_source['transaction_date']).dt.strftime('%Y%m%d').astype(int)
fact_sales = df_source[['date_key', 'product_id', 'customer_id', 'store_location', 'units_sold','unit_price', 'total_amount']].copy()
# 3. Store to Warehouse DB
dw_conn = sqlite3.connect("enterprise_dw.db")
dim_date.to_sql("Dim_Date", dw_conn, if_exists="replace", index=False)
dim_product.to_sql("Dim_Product", dw_conn, if_exists="replace", index=False)
fact_sales.to_sql("Fact_Sales", dw_conn, if_exists="replace", index=False)
# 4. Time Series & Pivot Tables
ts_df = df_source.set_index('transaction_date')

monthly_sales = ts_df['total_amount'].resample('M').sum()
weekly_moving_avg = ts_df['total_amount'].resample('D').sum().rolling(window=7).mean()
pivot_rep = pd.pivot_table(
    df_source,
    values='total_amount',
    index=['store_location'],
    columns=['product_id'],
    aggfunc=['sum', 'mean'],
    margins=True,
    margins_name='Total'
)
print("--- Monthly Sales Resampling ---")
print(monthly_sales.head(6))
print("--- Pivot Table Multilevel ---")
print(pivot_rep)
dw_conn.close()