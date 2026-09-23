"""
scraper.py
----------
مسؤول عن جزئين:
  1) استخراج بيانات الأسعار من صفحة الـ HTML (BeautifulSoup) — نفس أسلوب web scraping
     المستخدم في المشروع الأول.
  2) تخزين كل قراءة (snapshot) في جدول SQL تاريخي (price_history) بدل ما نكتفي بآخر قراءة بس.

ليه بنحتفظ بالتاريخ كامل مش بس آخر سعر؟
  لأن الهدف من "Market Intelligence" هو رصد الاتجاه (trend) عبر الوقت — مفهوم الـ
  "Time-Variant" اللي اتشرح في سلايدز Data Warehousing (كل قراءة جديدة بتتضاف كسجل جديد،
  مش بتستبدل القديم، عشان نقدر نحلل التاريخ كامل لاحقًا).
"""

import sqlite3
import os
from datetime import datetime
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(BASE_DIR, "output", "market_watch.db")


def init_database():
    """ينشئ جدول price_history لو مش موجود. كل صف هنا = قراءة سعر في لحظة معينة (snapshot)."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock_status TEXT,
            scraped_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_price_history_product
        ON price_history(product_id, scraped_at)
    """)
    conn.commit()
    conn.close()


def scrape_market_page(html_path: str = None) -> list[dict]:
    """يقرأ صفحة الـ HTML ويستخرج بيانات كل منتج منها."""
    if html_path is None:
        html_path = os.path.join(DATA_DIR, "market_page_latest.html")

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr", class_="product-row")

    scraped_at = datetime.now().isoformat(timespec="seconds")
    records = []
    for row in rows:
        product_id = row.get("data-id")
        name = row.find("td", class_="pname").text.strip()
        category = row.find("td", class_="pcategory").text.strip()
        price_text = row.find("td", class_="pprice").text.strip().replace("$", "")
        stock = row.find("td", class_="pstock").text.strip()

        records.append({
            "product_id": product_id,
            "product_name": name,
            "category": category,
            "price": float(price_text),
            "stock_status": stock,
            "scraped_at": scraped_at
        })

    return records


def save_snapshot(records: list[dict]):
    """يحفظ كل السجلات المستخرجة كـ snapshot جديد في price_history (بدون حذف أي بيانات قديمة)."""
    conn = sqlite3.connect(DB_PATH)
    conn.executemany("""
        INSERT INTO price_history (product_id, product_name, category, price, stock_status, scraped_at)
        VALUES (:product_id, :product_name, :category, :price, :stock_status, :scraped_at)
    """, records)
    conn.commit()
    conn.close()


def run_scrape_cycle():
    """دورة كاملة: توليد صفحة سوق جديدة -> استخراجها -> تخزينها."""
    from mock_market_site import generate_market_page

    print(f"[SCRAPE] بدء دورة سحب جديدة - {datetime.now().isoformat(timespec='seconds')}")

    # في الواقع الحقيقي: دي هتبقى requests.get(real_url).text بدل التوليد المحلي
    html = generate_market_page()
    html_path = os.path.join(DATA_DIR, "market_page_latest.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    init_database()
    records = scrape_market_page(html_path)
    save_snapshot(records)

    print(f"[SCRAPE] تم حفظ {len(records)} سجل في price_history")
    return records


if __name__ == "__main__":
    run_scrape_cycle()
