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
import os
from datetime import datetime
base_dir=os.path.dirname(os.path.dirname(os.path.aspath(__file__)))
data_dir=os.path.join(base_dir,'data')
state_file=os.path.join(data_dir,"_market_state.txt")
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

def load_or_init_prices():
    """
        بيحافظ على 'حالة' الأسعار بين كل تشغيلة والتانية (عشان يحاكي تغير تدريجي حقيقي في السوق
        مش أسعار عشوائية تمامًا في كل مرة). بيتخزن في ملف نصي بسيط.
        """
    if os.path.exists(state_file):
        prices={}
        with open(state_file,"r") as f:
            for line in f:
                pid,price=line.strip().split(",")
                prices[pid]=float(price)
        return prices
    else:
        return {p[0]:float(p[3]) for p in PRODUCTS}

def save_prices(prices):
    os.makedirs(data_dir,exist_ok=True)
    with open(state_file,"w") as f:
        for pid,price in prices.items():
            f.write(f"{pid},{price}\n")

def generate_market_page()->str:
    """
    يولّد صفحة HTML جديدة بأسعار محدّثة (كل تشغيلة الأسعار بتتغير بنسبة صغيرة عشوائية
    عشان تحاكي تقلب السوق الحقيقي، زيادة أو نقصان).
    """
    prices=load_or_init_prices()
    for pid,name,category,price in PRODUCTS:
        change_pct=random.uniform(-0.08,0.08)
        prices[pid]=round(prices[pid]*(1+change_pct),2)
        prices[pid]=max(prices[pid],5.0)
    save_prices(prices)
    rows_html=""
    for pid,name,category,price in PRODUCTS:
        stock_status=random.choice(["In Stock","In Stock","In Stock","Low Stock","Out of Stock"])
        rows_html+=f"""
        <tr class="product-row" data-id="{pid}">
        <td class="pname">{name}</td>
        <td class="pcategory">{category}</td>
        <td class="pprice">${prices[pid]}</td>
        <td class="pstock">{stock_status}</td>
    </tr>"""
    timestamp=datetime.now().isoformat()
    html=f"""<!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>Market Watch - Live Prices</title></head>
    <body>
    <h1>Market Watch</h1>
    <p class="timestamp">Last updated: {timestamp}</p>
    <table>
    <thead>
    <tr><th>Product Name</th><th>Category</th><th>Price</th><th>Stock Status</th></tr>
    </thead>
    <tbody>{rows_html}</tbody>
    </table>
    </body>
    </html>"""
    return html

if __name__=="__main__":
    html=generate_market_page()
    path=os.path.join(data_dir,"market_page_latest.html")
    with open(path,"w",encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Market page generated and saved to {path}")