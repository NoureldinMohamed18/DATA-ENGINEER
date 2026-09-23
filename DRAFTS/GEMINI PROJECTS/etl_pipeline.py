from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import sqlite3
from pymongo import MongoClient

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}
dag = DAG(
    'end_to_end_retail_market_pipeline',
    default_args=default_args,
    description='Automated ETL Pipeline scraping web data, extracting API metrics, loading to DW& MongoDB',
    schedule_interval='@daily',
    catchup=False
)
def task_scrape_market_prices(**kwargs):
    items = [
        {"item": "Umbrella Pro", "price": 25.0, "category": "Seasonal"},
        {"item": "Raincoat Ultra", "price": 45.0, "category": "Seasonal"},
        {"item": "Sun Hat Classic", "price": 18.0, "category": "Apparel"}
]
    pd.DataFrame(items).to_csv("/tmp/staging_market_data.csv", index=False)
    
def task_fetch_weather_metrics(**kwargs):
    weather = [
        {"city": "Cairo", "condition": "Rainy", "rainfall_mm": 12.0},
        {"city": "Alexandria", "condition": "Stormy", "rainfall_mm": 24.5}
        ]
    pd.DataFrame(weather).to_csv("/tmp/staging_weather_data.csv", index=False)
    
def task_integrate_and_transform(**kwargs):
    df_m = pd.read_csv("/tmp/staging_market_data.csv")
    df_w = pd.read_csv("/tmp/staging_weather_data.csv")
    df_combined = df_m.assign(key=1).merge(df_w.assign(key=1), on='key').drop('key', axis=1)
    df_combined['predicted_demand'] = df_combined.apply(
    lambda r: r['rainfall_mm'] * 15 if r['category'] == 'Seasonal' else 20, axis=1
    )
    df_combined.to_csv("/tmp/transformed_demand_data.csv", index=False)   

def task_load_dw_and_datalake(**kwargs):
    df = pd.read_csv("/tmp/transformed_demand_data.csv")
    conn = sqlite3.connect("enterprise_dw.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS MarketDemandFact (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT, item TEXT, price REAL, rainfall_mm REAL, predicted_demand REAL, processed_at
    DATE
    )
    """)
    
    for _, r in df.iterrows():
        cursor.execute("INSERT INTO MarketDemandFact (city, item, price, rainfall_mm,predicted_demand, processed_at) VALUES (?, ?, ?, ?, ?, ?)",
        (r['city'], r['item'], r['price'], r['rainfall_mm'],
        r['predicted_demand'], datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
    client = MongoClient("mongodb://localhost:27017/")
    db = client["raw_datalake"]
    db["market_demand_logs"].insert_many(df.to_dict(orient="records"))
    
def task_data_quality_check(**kwargs):
    df = pd.read_csv("/tmp/transformed_demand_data.csv")
    assert df.isnull().sum().sum() == 0, "Quality Error: Null values found!"
    assert (df['predicted_demand'] >= 0).all(), "Quality Error: Invalid negative demand!"
    
t1 = PythonOperator(task_id='scrape_market_prices', python_callable=task_scrape_market_prices,
dag=dag)
t2 = PythonOperator(task_id='fetch_weather_metrics', python_callable=task_fetch_weather_metrics,
dag=dag)
t3 = PythonOperator(task_id='integrate_and_transform',
python_callable=task_integrate_and_transform, dag=dag)
t4 = PythonOperator(task_id='load_dw_and_datalake', python_callable=task_load_dw_and_datalake,
dag=dag)
t5 = PythonOperator(task_id='data_quality_check', python_callable=task_data_quality_check,
dag=dag)
[t1, t2] >> t3 >> t4 >> t5