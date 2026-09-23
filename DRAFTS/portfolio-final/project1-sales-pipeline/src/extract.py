"""
extract.py
----------
مرحلة الـ E في ETL: مسؤول عن سحب البيانات الخام من 3 مصادر مختلفة زي ما بيحصل في أي شركة حقيقية:

  1) CSV Export        -> من نظام مبيعات داخلي (Pandas.read_csv)
  2) REST API          -> بيانات المنتجات (هنا محاكاة، لكن الكود مكتوب بنفس شكل استدعاء API حقيقي)
  3) Web Scraping      -> صفحة منافس بـ BeautifulSoup

كل دالة هنا "pure extraction" بمعنى إنها بس بتجيب البيانات زي ما هي من غير أي تنظيف.
التنظيف هيحصل في transform.py — كده كل مرحلة ليها مسؤولية واحدة (Single Responsibility)
وهي فلسفة أساسية في تصميم أي ETL pipeline احترافي.
"""

import pandas as pd
import json
import os
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def extract_sales_csv() -> pd.DataFrame:
    """
    يسحب بيانات المبيعات من ملف CSV (Source 1).
    في الواقع العملي: ده ممكن يكون ملف بييجي يوميًا من نظام ERP أو POS.
    """
    path = os.path.join(DATA_DIR, "sales_export.csv")
    df = pd.read_csv(path)
    print(f"[EXTRACT] sales_export.csv -> {len(df)} صف تم سحبه")
    return df


def extract_products_api() -> pd.DataFrame:
    """
    يسحب بيانات المنتجات من API خارجي (Source 2).

    ملاحظة: هنا بنقرأ من ملف JSON محلي عشان نحاكي رد الـ API من غير الاعتماد على إنترنت.
    لو عايز تستبدلها بـ API حقيقي، الكود بيبقى شكله كده:

        import requests
        response = requests.get("https://api.example.com/products")
        data = response.json()["data"]
        df = pd.DataFrame(data)

    الفكرة إن باقي الكود (transform.py) مش هيتغير خالص، لأنه بيستقبل DataFrame
    بغض النظر عن مصدره الأصلي — وده مبدأ مهم في تصميم الـ pipelines.
    """
    path = os.path.join(DATA_DIR, "products_from_api.json")
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if payload.get("status") != "success":
        raise ValueError("API response status is not 'success' — تحقق من الاتصال بالـ API")

    df = pd.DataFrame(payload["data"])
    print(f"[EXTRACT] products API -> {len(df)} منتج تم سحبه")
    return df


def extract_competitor_prices() -> pd.DataFrame:
    """
    يعمل Web Scraping لصفحة أسعار المنافس (Source 3) باستخدام BeautifulSoup.
    ده بالظبط نفس الأسلوب اللي هتستخدمه لو الصفحة كانت لايف على الإنترنت،
    الفرق الوحيد إننا بنقرأ ملف HTML محفوظ محليًا بدل ما نعمل requests.get() على URL حقيقي.
    """
    path = os.path.join(DATA_DIR, "competitor_prices.html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr", class_="product-row")

    records = []
    for row in rows:
        product_id = row.get("data-id")
        name = row.find("td", class_="pname").text.strip()
        category = row.find("td", class_="pcategory").text.strip()
        price_text = row.find("td", class_="pprice").text.strip()
        price = float(price_text.replace("$", ""))

        records.append({
            "product_id": product_id,
            "product_name": name,
            "category": category,
            "competitor_price": price
        })

    df = pd.DataFrame(records)
    print(f"[EXTRACT] competitor_prices.html (scraping) -> {len(df)} صف تم استخراجه")
    return df


def run_extraction():
    """يشغل كل عمليات الـ extraction ويرجع dictionary فيه الـ 3 DataFrames."""
    print("=" * 60)
    print("بدء مرحلة الـ EXTRACT")
    print("=" * 60)

    sales_df = extract_sales_csv()
    products_df = extract_products_api()
    competitor_df = extract_competitor_prices()

    print("\n[SUCCESS] تمت كل عمليات السحب بنجاح.\n")
    return {
        "sales": sales_df,
        "products": products_df,
        "competitor": competitor_df
    }


if __name__ == "__main__":
    data = run_extraction()
    for name, df in data.items():
        print(f"\n--- {name} (أول 3 صفوف) ---")
        print(df.head(3))
