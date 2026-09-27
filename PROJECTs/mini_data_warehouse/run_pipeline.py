"""
run_pipeline.py
-----------------
Project 5: Mini Data Warehouse with an Orchestrated (DAG-based) Pipeline.

Combines two independent data sources -- sales data and weather data --
exactly like the "umbrella sales vs weather" example from the Data Pipeline
material (Session 2, Figure 1.5/1.6):

    extract_sales -----\
                         >--- join_data ---> load_warehouse
    extract_weather ---/

extract_sales and extract_weather are independent of each other (no edge
between them), so a real orchestrator could run them in parallel. join_data
can only start once BOTH extracts are done. load_warehouse can only start
once join_data is done. This dependency structure is expressed explicitly
using the DAG engine in dag_engine.py, instead of just writing five
functions in a row and hoping the order never needs to change.

Usage:
    python run_pipeline.py
"""

import sqlite3
import pandas as pd
from pathlib import Path

from dag_engine import DAG

SALES_CSV = Path("data/sales.csv")
WEATHER_CSV = Path("data/weather.csv")
JOINED_CSV = Path("data/joined.csv")
DB_PATH = Path("warehouse.db")
SCHEMA_PATH = Path("sql/star_schema.sql")

# Shared in-memory state between DAG tasks (kept intentionally simple --
# a real orchestrator like Airflow would pass data via XComs or a shared store)
_state = {}


def extract_sales():
    df = pd.read_csv(SALES_CSV, parse_dates=["order_date"])
    _state["sales"] = df
    print(f"    -> {len(df)} sales records loaded")


def extract_weather():
    df = pd.read_csv(WEATHER_CSV, parse_dates=["date"])
    _state["weather"] = df
    print(f"    -> {len(df)} weather records loaded")


def join_data():
    sales = _state["sales"]
    weather = _state["weather"]

    # Join sales with weather on (date, region) -- the same kind of "combine
    # data sets" step shown in the umbrella-sales example.
    joined = sales.merge(
        weather,
        left_on=["order_date", "region"],
        right_on=["date", "region"],
        how="left",
    )
    joined = joined.drop(columns=["date"])
    _state["joined"] = joined
    joined.to_csv(JOINED_CSV, index=False)
    print(f"    -> Joined dataset: {len(joined)} rows -> {JOINED_CSV}")


def load_warehouse():
    joined = _state["joined"]

    if DB_PATH.exists():
        DB_PATH.unlink()  # rebuild fresh each run, so the pipeline stays repeatable

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    # --- dim_date ---
    dates = joined["order_date"].dt.date.astype(str).unique()
    dim_date = pd.DataFrame({"date_key": dates})
    dim_date["day"] = pd.to_datetime(dim_date["date_key"]).dt.day
    dim_date["month"] = pd.to_datetime(dim_date["date_key"]).dt.month
    dim_date["year"] = pd.to_datetime(dim_date["date_key"]).dt.year
    dim_date.to_sql("dim_date", conn, if_exists="append", index=False)

    # --- dim_region ---
    regions = sorted(joined["region"].unique())
    dim_region = pd.DataFrame({"region_id": range(1, len(regions) + 1), "region_name": regions})
    dim_region.to_sql("dim_region", conn, if_exists="append", index=False)
    region_map = dict(zip(dim_region["region_name"], dim_region["region_id"]))

    # --- dim_product ---
    products = sorted(joined["product"].unique())
    dim_product = pd.DataFrame({"product_id": range(1, len(products) + 1), "product_name": products})
    dim_product.to_sql("dim_product", conn, if_exists="append", index=False)
    product_map = dict(zip(dim_product["product_name"], dim_product["product_id"]))

    # --- fact_sales ---
    fact = pd.DataFrame({
        "date_key": joined["order_date"].dt.date.astype(str),
        "region_id": joined["region"].map(region_map),
        "product_id": joined["product"].map(product_map),
        "quantity": joined["quantity"],
        "total_amount": joined["total_amount"],
        "temperature_c": joined["temperature_c"],
        "rained": joined["rained"],
    })
    fact.to_sql("fact_sales", conn, if_exists="append", index=False)

    conn.commit()
    conn.close()
    print(f"    -> Loaded {len(fact)} fact rows + {len(dim_date)} dates, "
          f"{len(dim_region)} regions, {len(dim_product)} products -> {DB_PATH}")


def main():
    dag = DAG()
    dag.add_task("extract_sales", extract_sales)
    dag.add_task("extract_weather", extract_weather)
    dag.add_task("join_data", join_data, depends_on=["extract_sales", "extract_weather"])
    dag.add_task("load_warehouse", load_warehouse, depends_on=["join_data"])

    dag.run()


if __name__ == "__main__":
    main()
