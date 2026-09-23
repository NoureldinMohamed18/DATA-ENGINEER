"""
load.py
-------
مرحلة الـ L في ETL: بناء قاعدة بيانات SQLite بتصميم Star Schema.

ليه Star Schema بالظبط؟ (زي ما اتشرح في سلايدز الـ Data Warehousing بتاعتك)
  - Fact Table في النص (fact_sales) فيها الأرقام (measures): quantity, total_amount, profit_margin
  - Dimension Tables حواليها فيها السياق (context): المنتج، العميل، الوقت، المنطقة
  - ده بيخلي أي query تحليلي (زي "مبيعات كل شهر لكل فئة منتج") بسيط وسريع،
    لأنك بتعمل JOIN واحد بس بين الـ fact والـ dimension المطلوبة بدل ما تدور جوه جدول كبير واحد.

الجداول اللي هنبنيها:
  dim_product   -> بيانات المنتج (اسم، فئة، مورد)
  dim_customer  -> بيانات العميل
  dim_date      -> تفكيك التاريخ لسنة/شهر/يوم/ربع (مهم جدًا لتقارير زمنية)
  dim_region    -> المناطق
  fact_sales    -> جدول الحقائق: مرتبط بالـ 4 dimensions فوق + الأرقام الفعلية
"""

import pandas as pd
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "output", "sales_warehouse.db")


def build_dimension_tables(df: pd.DataFrame):
    """يبني جداول الـ dimensions من الجدول المدموج، كل واحدة بمفتاح صناعي (surrogate key)."""

    # --- dim_product ---
    dim_product = (
        df[["product_id", "product_name", "category", "supplier", "cost_price"]]
        .drop_duplicates(subset="product_id")
        .reset_index(drop=True)
    )
    dim_product.insert(0, "product_key", range(1, len(dim_product) + 1))

    # --- dim_customer ---
    dim_customer = (
        df[["customer_id"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim_customer.insert(0, "customer_key", range(1, len(dim_customer) + 1))

    # --- dim_region ---
    dim_region = (
        df[["region"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim_region.insert(0, "region_key", range(1, len(dim_region) + 1))

    # --- dim_date --- (Role-Playing / Time dimension، بنفكك التاريخ لأجزاء مفيدة للتحليل)
    unique_dates = df["order_date"].drop_duplicates().reset_index(drop=True)
    dim_date = pd.DataFrame({"full_date": unique_dates})
    dim_date["date_key"] = range(1, len(dim_date) + 1)
    dim_date["year"] = dim_date["full_date"].dt.year
    dim_date["month"] = dim_date["full_date"].dt.month
    dim_date["day"] = dim_date["full_date"].dt.day
    dim_date["quarter"] = dim_date["full_date"].dt.quarter
    dim_date["day_name"] = dim_date["full_date"].dt.day_name()
    dim_date = dim_date[["date_key", "full_date", "year", "month", "day", "quarter", "day_name"]]

    return dim_product, dim_customer, dim_region, dim_date


def build_fact_table(df: pd.DataFrame, dim_product, dim_customer, dim_region, dim_date):
    """
    يبني fact_sales عن طريق استبدال الأعمدة الوصفية بمفاتيحها الصناعية (surrogate keys)
    من كل dimension table — ده هو جوهر تصميم الـ Star Schema.
    """
    fact = df.merge(dim_product[["product_key", "product_id"]], on="product_id", how="left")
    fact = fact.merge(dim_customer[["customer_key", "customer_id"]], on="customer_id", how="left")
    fact = fact.merge(dim_region[["region_key", "region"]], on="region", how="left")
    fact = fact.merge(dim_date[["date_key", "full_date"]], left_on="order_date", right_on="full_date", how="left")

    fact_sales = fact[[
        "order_id", "date_key", "product_key", "customer_key", "region_key",
        "quantity", "unit_price", "total_amount", "profit_margin",
        "competitor_price", "price_diff_vs_competitor"
    ]].copy()

    fact_sales.insert(0, "sales_key", range(1, len(fact_sales) + 1))
    return fact_sales


def run_load(clean_data: dict):
    print("=" * 60)
    print("بدء مرحلة الـ LOAD")
    print("=" * 60)

    df = clean_data["clean_sales_full"]

    dim_product, dim_customer, dim_region, dim_date = build_dimension_tables(df)
    fact_sales = build_fact_table(df, dim_product, dim_customer, dim_region, dim_date)

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # لو الملف موجود من تشغيل سابق، بنمسحه ونبني من جديد (idempotent pipeline)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)

    dim_product.to_sql("dim_product", conn, index=False)
    dim_customer.to_sql("dim_customer", conn, index=False)
    dim_region.to_sql("dim_region", conn, index=False)
    dim_date.to_sql("dim_date", conn, index=False)
    fact_sales.to_sql("fact_sales", conn, index=False)

    # إضافة indexes على المفاتيح الأجنبية في fact_sales لتسريع الـ JOINs (زي ما اتشرح في سلايدز Advanced SQL)
    cursor = conn.cursor()
    for col in ["date_key", "product_key", "customer_key", "region_key"]:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_fact_{col} ON fact_sales({col});")
    conn.commit()

    print(f"[LOAD] dim_product   -> {len(dim_product)} صف")
    print(f"[LOAD] dim_customer  -> {len(dim_customer)} صف")
    print(f"[LOAD] dim_region    -> {len(dim_region)} صف")
    print(f"[LOAD] dim_date      -> {len(dim_date)} صف")
    print(f"[LOAD] fact_sales    -> {len(fact_sales)} صف")
    print(f"\n[SUCCESS] قاعدة البيانات جاهزة في: {DB_PATH}")

    conn.close()
    return DB_PATH


if __name__ == "__main__":
    from extract import run_extraction
    from transform import run_transformation

    raw = run_extraction()
    clean = run_transformation(raw)
    run_load(clean)
