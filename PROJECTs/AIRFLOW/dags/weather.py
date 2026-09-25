"""
Weather Data Pipeline DAG
=========================
A production-ready Airflow DAG that:
1. Fetches weather data from a public API
2. Cleans and validates the data
3. Loads it into SQLite
4. Sends a confirmation email
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import requests
import sqlite3
import os

DATA_DIR = '/opt/airflow/data'
DB_PATH = os.path.join(DATA_DIR, 'weather.db')
default_args={
    'owner':'data_engineer',
    'depends_on_past':False,
    'email':['noureldeenisco22@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}
dag=DAG(
    'weather_data_pipeline',
    default_args=default_args,
    description='Daily weather data extraction and loading',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
    tags=['weather', 'etl', 'demo'],
)
def extract_weather(**context):
    """Fetch weather data from Open-Meteo API."""
    print("[TASK] Extracting weather data...")

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': 30.0444,
        'longitude': 31.2357,
        'daily': ['temperature_2m_max', 'temperature_2m_min', 'precipitation_sum'],
        'timezone': 'Africa/Cairo'
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    context['ti'].xcom_push(key='weather_data', value=data)
    print(f"[TASK] Extracted data for {len(data['daily']['time'])} days")
    return data

def transform_weather(**context):
    """Clean and structure the weather data."""
    print("[TASK] Transforming weather data...")

    ti = context['ti']
    data = ti.xcom_pull(task_ids='extract_weather', key='weather_data')

    daily = data['daily']
    records = []

    for i in range(len(daily['time'])):
        records.append({
            'date': daily['time'][i],
            'temp_max': daily['temperature_2m_max'][i],
            'temp_min': daily['temperature_2m_min'][i],
            'precipitation': daily['precipitation_sum'][i],
            'city': 'Cairo',
            'country': 'Egypt',
            'loaded_at': datetime.now().isoformat()
        })

    ti.xcom_push(key='clean_records', value=records)
    print(f"[TASK] Transformed {len(records)} records")
    return records


def load_weather(**context):
    """Load cleaned data into SQLite."""
    print("[TASK] Loading data into database...")

    ti = context['ti']
    records = ti.xcom_pull(task_ids='transform_weather', key='clean_records')

    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS weather_daily (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            temp_max REAL,
            temp_min REAL,
            precipitation REAL,
            city TEXT,
            country TEXT,
            loaded_at TEXT
        )
    """)

    inserted = 0
    for rec in records:
        try:
            conn.execute("""
                INSERT INTO weather_daily (date, temp_max, temp_min, precipitation, city, country, loaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (rec['date'], rec['temp_max'], rec['temp_min'], 
                  rec['precipitation'], rec['city'], rec['country'], rec['loaded_at']))
            inserted += 1
        except sqlite3.IntegrityError:
            print(f"[SKIP] Date {rec['date']} already exists.")

    conn.commit()
    conn.close()

    print(f"[TASK] Loaded {inserted} new records into {DB_PATH}")
    return inserted


def validate_data(**context):
    """Validate that data was loaded correctly."""
    print("[TASK] Validating loaded data...")

    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM weather_daily").fetchone()[0]
    latest = conn.execute("SELECT MAX(date) FROM weather_daily").fetchone()[0]
    conn.close()

    print(f"[TASK] Validation: {count} total records. Latest: {latest}")

    if count == 0:
        raise ValueError("No data found in database!")

    return {'total_records': count, 'latest_date': latest}

# ============================================================
# TASK DEFINITIONS
# ============================================================

t1_extract=PythonOperator(
    task_id="extract_weather",
    python_callable=extract_weather,
    dag=dag,
)
t2_transform=PythonOperator(
    task_id="transform_weather",
    python_callable=transform_weather,
    dag=dag,
)
t3_load=PythonOperator(
    task_id="load_weather",
    python_callable=load_weather,
    dag=dag,
)
t4_validate=PythonOperator(
    task_id="validate_data",
    python_callable= validate_data,
    dag=dag,
)
t5_email = EmailOperator(
    task_id='send_success_email',
    to=['noureldeenisco22@gmail.com.com'],
    subject='Airflow: Weather Pipeline Success',
    html_content="""
    <h3>Weather Pipeline Completed Successfully</h3>
    <p>The daily weather data pipeline has finished execution.</p>
    <p>Check the Airflow UI for details.</p>
    """,
    dag=dag,
)
t1_extract >> t2_transform >> t3_load >> t4_validate >> t5_email

