"""
generate_raw_data.py
---------------------
هذا الملف مسؤول فقط عن توليد بيانات خام "وسخة" (messy) تحاكي 3 مصادر بيانات حقيقية:

1) sales_export.csv        -> إكسبورت من نظام مبيعات داخلي (فيه أخطاء نموذجية: قيم فاضية، تكرار، تنسيق تواريخ مختلف)
2) products_from_api.json  -> يحاكي رد API خارجي بيرجع بيانات المنتجات (بديل عن استدعاء API حقيقي عشان المشروع يشتغل offline)
3) competitor_prices.html  -> صفحة HTML بسيطة تحاكي موقع منافس هنعمله scrape لاحقًا لمقارنة الأسعار

ملاحظة مهمة: في مشروع حقيقي هتستبدل الجزء الخاص بالـ API بـ requests.get() فعلي،
وهتستبدل ملف الـ HTML بـ requests.get(real_url).text
لكن عشان المشروع يفضل شغال دايمًا من غير ما يعتمد على إنترنت أو API ممكن يقفل،
بنعمل simulation واقعي جدًا للبيانات.
"""

import csv
import json
import random
from datetime import datetime, timedelta
import os

random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ---------------------------------------------------------------
# 1) sales_export.csv  (Source 1: Internal messy CSV)
# ---------------------------------------------------------------
products = [
    ("P001", "Wireless Mouse", "Electronics"),
    ("P002", "Mechanical Keyboard", "Electronics"),
    ("P003", "USB-C Hub", "Electronics"),
    ("P004", "Office Chair", "Furniture"),
    ("P005", "Standing Desk", "Furniture"),
    ("P006", "Notebook Set", "Stationery"),
    ("P007", "Gel Pen Pack", "Stationery"),
    ("P008", "Desk Lamp", "Furniture"),
    ("P009", "Webcam HD", "Electronics"),
    ("P010", "Monitor Stand", "Furniture"),
]

customers = [f"C{str(i).zfill(3)}" for i in range(1, 41)]
regions = ["Cairo", "Alexandria", "Giza", "Mansoura", "Aswan"]

date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y"]  # عمدًا تنسيقات مختلفة عشان تحاكي الفوضى الحقيقية

rows = []
start_date = datetime(2024, 1, 1)

for i in range(1, 1201):
    product = random.choice(products)
    customer = random.choice(customers)
    region = random.choice(regions)
    qty = random.randint(1, 10)
    unit_price = round(random.uniform(15, 450), 2)
    order_date = start_date + timedelta(days=random.randint(0, 400))
    fmt = random.choice(date_formats)
    date_str = order_date.strftime(fmt)

    # حقن أخطاء واقعية بشكل مقصود (زي أي بيانات حقيقية جاية من نظام قديم)
    if random.random() < 0.03:
        qty = ""  # قيمة فاضية
    if random.random() < 0.02:
        unit_price = -abs(unit_price)  # سعر سالب غلط
    if random.random() < 0.015:
        customer = ""  # عميل غير معروف
    if random.random() < 0.02:
        region = None  # منطقة فاضية

    rows.append({
        "order_id": f"ORD{str(i).zfill(5)}",
        "order_date": date_str,
        "customer_id": customer,
        "product_id": product[0],
        "product_name": product[1],
        "region": region if region else "",
        "quantity": qty,
        "unit_price": unit_price
    })

# حقن صفوف مكررة عمدًا (مشكلة شائعة جدًا في exports حقيقية)
duplicates = random.sample(rows, 25)
rows.extend(duplicates)
random.shuffle(rows)

csv_path = os.path.join(DATA_DIR, "sales_export.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"[OK] sales_export.csv  -> {len(rows)} صف تم إنشاؤه في {csv_path}")

# ---------------------------------------------------------------
# 2) products_from_api.json  (Source 2: يحاكي رد REST API خارجي)
# ---------------------------------------------------------------
api_products = []
for pid, name, category in products:
    api_products.append({
        "product_id": pid,
        "product_name": name,
        "category": category,
        "supplier": random.choice(["GlobalTech", "OfficePlus", "NileSupply"]),
        "cost_price": round(random.uniform(10, 300), 2),
        "in_stock": random.choice([True, True, True, False])  # الأغلب متاح
    })

api_json_path = os.path.join(DATA_DIR, "products_from_api.json")
with open(api_json_path, "w", encoding="utf-8") as f:
    json.dump({"status": "success", "data": api_products}, f, ensure_ascii=False, indent=2)

print(f"[OK] products_from_api.json -> {len(api_products)} منتج تم إنشاؤه في {api_json_path}")

# ---------------------------------------------------------------
# 3) competitor_prices.html  (Source 3: صفحة نحتاج نعمل لها scraping)
# ---------------------------------------------------------------
html_rows = ""
for pid, name, category in products:
    competitor_price = round(random.uniform(15, 470), 2)
    html_rows += f"""
    <tr class="product-row" data-id="{pid}">
        <td class="pname">{name}</td>
        <td class="pcategory">{category}</td>
        <td class="pprice">${competitor_price}</td>
    </tr>"""

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Competitor Store - Price List</title></head>
<body>
<h1>Competitor Store Prices</h1>
<table id="price-table">
<thead>
<tr><th>Product</th><th>Category</th><th>Price</th></tr>
</thead>
<tbody>
{html_rows}
</tbody>
</table>
</body>
</html>"""

html_path = os.path.join(DATA_DIR, "competitor_prices.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"[OK] competitor_prices.html -> تم إنشاؤه في {html_path}")
print("\nتم توليد كل مصادر البيانات الخام بنجاح. الخطوة الجاية: extract.py")
