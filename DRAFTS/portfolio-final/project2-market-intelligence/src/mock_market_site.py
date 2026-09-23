"""
mock_market_site.py
--------------------
المشروع ده بيراقب أسعار منتجات بتتغير مع الوقت. عشان المشروع يشتغل offline وبشكل قابل للتكرار
(مش معتمد على موقع حقيقي ممكن يتغير هيكله أو يمنع الـ scraping)، بنعمل "موقع وهمي" بيولّد
صفحة HTML لأسعار منتجات، والأسعار دي بتتغير شوية في كل مرة تتنفذ (زي ما بيحصل في السوق الحقيقي).

في مشروع حقيقي 100%: هتستبدل الدالة generate_market_page() باستدعاء
    requests.get("https://real-competitor-site.com/prices")
والباقي (scraper.py, database, analysis) هيفضل شغال بنفس الشكل بالظبط.
"""

import random
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATE_FILE = os.path.join(DATA_DIR, "_market_state.txt")

PRODUCTS = [
    ("MP001", "Laptop Pro 14", "Electronics", 850),
    ("MP002", "Wireless Earbuds", "Electronics", 65),
    ("MP003", "Smart Watch", "Electronics", 180),
    ("MP004", "Office Desk", "Furniture", 220),
    ("MP005", "Ergonomic Chair", "Furniture", 310),
    ("MP006", "LED Monitor 27\"", "Electronics", 240),
    ("MP007", "Bluetooth Speaker", "Electronics", 45),
    ("MP008", "Bookshelf", "Furniture", 130),
]


def _load_or_init_prices():
    """
    بيحافظ على 'حالة' الأسعار بين كل تشغيلة والتانية (عشان يحاكي تغير تدريجي حقيقي في السوق
    مش أسعار عشوائية تمامًا في كل مرة). بيتخزن في ملف نصي بسيط.
    """
    if os.path.exists(STATE_FILE):
        prices = {}
        with open(STATE_FILE, "r") as f:
            for line in f:
                pid, price = line.strip().split(",")
                prices[pid] = float(price)
        return prices
    else:
        return {p[0]: float(p[3]) for p in PRODUCTS}


def _save_prices(prices):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        for pid, price in prices.items():
            f.write(f"{pid},{price}\n")


def generate_market_page() -> str:
    """
    يولّد صفحة HTML جديدة بأسعار محدّثة (كل تشغيلة الأسعار بتتغير بنسبة صغيرة عشوائية
    عشان تحاكي تقلب السوق الحقيقي، زيادة أو نقصان).
    """
    prices = _load_or_init_prices()

    for pid, *_ in PRODUCTS:
        change_pct = random.uniform(-0.08, 0.08)  # تغير بين -8% و +8%
        prices[pid] = round(prices[pid] * (1 + change_pct), 2)
        prices[pid] = max(prices[pid], 5.0)  # حماية من سعر سالب أو صفر

    _save_prices(prices)

    rows_html = ""
    for pid, name, category, _ in PRODUCTS:
        stock_status = random.choice(["In Stock", "In Stock", "In Stock", "Low Stock", "Out of Stock"])
        rows_html += f"""
    <tr class="product-row" data-id="{pid}">
        <td class="pname">{name}</td>
        <td class="pcategory">{category}</td>
        <td class="pprice">${prices[pid]}</td>
        <td class="pstock">{stock_status}</td>
    </tr>"""

    timestamp = datetime.now().isoformat()
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Market Watch - Live Prices</title></head>
<body>
<h1>Market Watch</h1>
<p class="timestamp">Last updated: {timestamp}</p>
<table id="market-table">
<thead><tr><th>Product</th><th>Category</th><th>Price</th><th>Stock</th></tr></thead>
<tbody>{rows_html}
</tbody>
</table>
</body>
</html>"""
    return html


if __name__ == "__main__":
    html = generate_market_page()
    path = os.path.join(DATA_DIR, "market_page_latest.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] صفحة السوق الوهمية اتولدت في: {path}")
