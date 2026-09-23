"""
backfill_history.py
--------------------
عشان نقدر نعمل تحليل اتجاهات (trend analysis) حقيقي، محتاجين بيانات تاريخية بتمتد على أيام
مش بس ثواني. الملف ده بيولّد تاريخ واقعي (30 يوم مثلاً) لكل منتج، وكأن الـ scraper اشتغل
مرة كل يوم على مدار شهر.

في الإنتاج الحقيقي: مش هتحتاج الملف ده خالص، لأن الـ scheduler (انظر scheduler.py) هيبني
التاريخ ده طبيعيًا يوم ورا يوم. الملف ده بس لتوليد بيانات تجريبية واقعية للعرض والتحليل الفوري.
"""

import sqlite3
import os
import random
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "output", "market_watch.db")

from mock_market_site import PRODUCTS
from scraper import init_database

random.seed(7)


def backfill(days: int = 30):
    init_database()
    conn = sqlite3.connect(DB_PATH)

    # نمسح أي بيانات قديمة عشان الـ backfill يبدأ نظيف (idempotent)
    conn.execute("DELETE FROM price_history")
    conn.commit()

    records = []
    start_date = datetime.now() - timedelta(days=days)

    # نبدأ من السعر الأساسي لكل منتج ونخليه يمشي بشكل عشوائي واقعي (random walk) على مدار الأيام
    current_prices = {p[0]: float(p[3]) for p in PRODUCTS}

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)

        for pid, name, category, _ in PRODUCTS:
            change_pct = random.uniform(-0.05, 0.05)
            current_prices[pid] = round(max(current_prices[pid] * (1 + change_pct), 5.0), 2)

            # نضيف كمان "حدث سعري" مقصود لمنتج معين في يوم معين، عشان يظهر في تحليل الـ alerts لاحقًا
            if pid == "MP001" and day_offset == days - 3:
                current_prices[pid] = round(current_prices[pid] * 1.18, 2)  # قفزة سعر مقصودة +18%
            if pid == "MP005" and day_offset == days - 2:
                current_prices[pid] = round(current_prices[pid] * 0.85, 2)  # هبوط سعر مقصود -15%

            stock = random.choice(["In Stock", "In Stock", "In Stock", "Low Stock", "Out of Stock"])

            records.append({
                "product_id": pid,
                "product_name": name,
                "category": category,
                "price": current_prices[pid],
                "stock_status": stock,
                "scraped_at": current_date.isoformat(timespec="seconds")
            })

    conn.executemany("""
        INSERT INTO price_history (product_id, product_name, category, price, stock_status, scraped_at)
        VALUES (:product_id, :product_name, :category, :price, :stock_status, :scraped_at)
    """, records)
    conn.commit()
    conn.close()

    print(f"[BACKFILL] تم إنشاء {len(records)} سجل تاريخي على مدار {days} يوم")
    print("[BACKFILL] أحداث مقصودة: MP001 (Laptop Pro 14) قفزة سعر +18%, MP005 (Ergonomic Chair) هبوط -15%")


if __name__ == "__main__":
    backfill(days=30)
