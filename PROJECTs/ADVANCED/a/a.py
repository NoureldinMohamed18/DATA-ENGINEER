"""
Project A: E-Commerce Full ETL Pipeline
=========================================
بيانات من 3 مصادر:
  1. Orders CSV
  2. Customers API (JSONPlaceholder - مجاني)
  3. Products Scraping (books.toscrape.com)

Transform:
  - دمج الـ 3 مصادر في DataFrame واحد
  - تنظيف شامل + Data Quality check
  - Star Schema في SQLite

Output:
  - SQLite database بـ Star Schema
  - rejected_rows.csv
  - quality_report.json
  - summary HTML report
"""

import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup
import json
import os
import time
import logging
from datetime import datetime
from pathlib import Path

# ── Setup ──────────────────────────────────────────────
BASE = Path(__file__).parent if '__file__' in dir() else Path('.')
(BASE / 'data').mkdir(exist_ok=True)
(BASE / 'output').mkdir(exist_ok=True)
(BASE / 'logs').mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(BASE / 'logs' / 'pipeline.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger('EcommerceETL')


# ══════════════════════════════════════════════════════
# EXTRACT
# ══════════════════════════════════════════════════════

def extract_orders_csv():
    """Extract: قراءة الأوردرات من CSV"""
    log.info("Extract [1/3] Orders CSV...")
    path = BASE / 'data' / 'orders.csv'

    if not path.exists():
        # بنعمل بيانات تجريبية واقعية
        import random
        from datetime import timedelta
        random.seed(42)

        statuses    = ['completed', 'pending', 'cancelled', 'refunded']
        channels    = ['website', 'mobile_app', 'phone', 'store']
        categories  = ['Electronics', 'Books', 'Clothing', 'Home', 'Sports']

        rows = []
        base_date = datetime(2024, 1, 1)
        for i in range(1, 301):
            rows.append({
                'order_id':    f'ORD-{i:04d}',
                'customer_id': random.randint(1, 50),
                'product_id':  random.randint(1, 30),
                'quantity':    random.choice([1,1,1,2,2,3,-1,0,99]),   # فيها أخطاء
                'unit_price':  round(random.uniform(10, 500), 2),
                'status':      random.choice(statuses),
                'channel':     random.choice(channels),
                'order_date':  (base_date + timedelta(days=random.randint(0,179))).strftime('%Y-%m-%d'),
                'category':    random.choice(categories),
            })
        pd.DataFrame(rows).to_csv(path, index=False)

    df = pd.read_csv(path)
    log.info(f"  ✅ Orders: {len(df)} rows, {df.columns.tolist()}")
    return df


def extract_customers_api():
    """Extract: جلب بيانات العملاء من API"""
    log.info("Extract [2/3] Customers API...")
    try:
        resp = requests.get('https://jsonplaceholder.typicode.com/users', timeout=10)
        resp.raise_for_status()
        users = resp.json()

        customers = []
        for u in users:
            customers.append({
                'customer_id': u['id'],
                'name':        u['name'],
                'email':       u['email'],
                'city':        u['address']['city'],
                'company':     u['company']['name'],
                'phone':       u['phone'],
            })

        # نكرر العملاء عشان يكفوا الـ 50 customer_id في الأوردرات
        base = pd.DataFrame(customers)
        extended = pd.concat([base] * 5, ignore_index=True)
        extended['customer_id'] = range(1, len(extended)+1)
        extended = extended[extended['customer_id'] <= 50]

        log.info(f"  ✅ Customers: {len(extended)} records from API")
        return extended

    except Exception as e:
        log.warning(f"  ⚠️  API failed: {e} — using fallback")
        rows = [{'customer_id': i, 'name': f'Customer {i}', 'email': f'c{i}@email.com',
                 'city': 'Cairo', 'company': 'N/A', 'phone': 'N/A'} for i in range(1, 51)]
        return pd.DataFrame(rows)


def extract_products_scraping():
    """Extract: سكرابينج بيانات المنتجات"""
    log.info("Extract [3/3] Products Scraping...")
    products = []

    for page in range(1, 4):
        try:
            url  = f"http://books.toscrape.com/catalogue/page-{page}.html"
            resp = requests.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')

            RATING = {'One':1,'Two':2,'Three':3,'Four':4,'Five':5}
            for i, book in enumerate(soup.select('article.product_pod')):
                price = float(''.join(c for c in book.select_one('.price_color').text if c.isdigit() or c=='.'))
                products.append({
                    'product_id':   (page-1)*20 + i + 1,
                    'product_name': book.select_one('h3 a')['title'][:50],
                    'price':        price,
                    'rating':       RATING.get(book.select_one('p.star-rating')['class'][1], 0),
                    'in_stock':     'In stock' in book.select_one('.availability').text,
                    'scraped_page': page
                })
            time.sleep(0.5)

        except Exception as e:
            log.warning(f"  ⚠️  Scraping page {page} failed: {e}")

    df = pd.DataFrame(products[:30])  # أول 30 منتج بس
    log.info(f"  ✅ Products: {len(df)} scraped")
    return df


# ══════════════════════════════════════════════════════
# TRANSFORM
# ══════════════════════════════════════════════════════

def transform(orders_df, customers_df, products_df):
    log.info("Transform: cleaning and merging...")
    rejected = []

    # ── Clean Orders ──
    # quantity
    bad_qty = orders_df[(orders_df['quantity'] <= 0) | (orders_df['quantity'] > 50)].copy()
    bad_qty['rejection_reason'] = 'invalid quantity'
    rejected.append(bad_qty)
    orders_df = orders_df[(orders_df['quantity'] > 0) & (orders_df['quantity'] <= 50)].copy()

    # duplicates
    orders_df = orders_df.drop_duplicates(subset=['order_id'])

    # date
    orders_df['order_date'] = pd.to_datetime(orders_df['order_date'], errors='coerce')
    bad_date = orders_df[orders_df['order_date'].isna()].copy()
    bad_date['rejection_reason'] = 'invalid date'
    rejected.append(bad_date)
    orders_df = orders_df[orders_df['order_date'].notna()].copy()

    # total
    orders_df['total_amount'] = orders_df['quantity'] * orders_df['unit_price']

    # ── Merge ──
    df = orders_df.merge(customers_df, on='customer_id', how='left')
    if not products_df.empty and 'product_id' in products_df.columns:
        df = df.merge(products_df[['product_id','product_name','rating']],
                      on='product_id', how='left')
    else:
        df['product_name'] = 'N/A'
        df['rating']       = 0

    # ── Save rejected ──
    if rejected:
        all_rej = pd.concat(rejected, ignore_index=True).dropna(how='all')
        all_rej.to_csv(BASE / 'data' / 'rejected_rows.csv', index=False)
        log.info(f"  ⚠️  {len(all_rej)} rows rejected → rejected_rows.csv")

    log.info(f"  ✅ Transform done: {len(df)} clean rows")
    return df


# ══════════════════════════════════════════════════════
# LOAD — Star Schema
# ══════════════════════════════════════════════════════

def load(df, products_df, customers_df):
    log.info("Load: building Star Schema in SQLite...")
    db = str(BASE / 'data' / 'ecommerce.db')
    if os.path.exists(db): os.remove(db)

    conn = sqlite3.connect(db)

    # Dimensions
    customers_df.to_sql('dim_customers', conn, if_exists='replace', index=False)
    if not products_df.empty:
        products_df.to_sql('dim_products', conn, if_exists='replace', index=False)

    # dim_time
    time_df = df[['order_date']].drop_duplicates().copy()
    time_df['year']    = time_df['order_date'].dt.year
    time_df['month']   = time_df['order_date'].dt.month
    time_df['day']     = time_df['order_date'].dt.day
    time_df['weekday'] = time_df['order_date'].dt.day_name()
    time_df['quarter'] = time_df['order_date'].dt.quarter
    time_df['order_date'] = time_df['order_date'].dt.strftime('%Y-%m-%d')
    time_df.to_sql('dim_time', conn, if_exists='replace', index=False)

    # dim_channels
    ch_df = df[['channel']].drop_duplicates().reset_index(drop=True)
    ch_df.insert(0, 'channel_id', range(1, len(ch_df)+1))
    ch_df.to_sql('dim_channels', conn, if_exists='replace', index=False)

    # Fact
    fact = df.copy()
    fact['order_date_str'] = fact['order_date'].dt.strftime('%Y-%m-%d')
    ch_map = ch_df.rename(columns={'channel':'channel'})
    fact = fact.merge(ch_map, on='channel', how='left')

    fact_cols = ['order_id','customer_id','product_id','order_date_str',
                 'channel_id','quantity','unit_price','total_amount','status','category']
    fact[fact_cols].to_sql('fact_orders', conn, if_exists='replace', index=False)

    conn.commit()

    # Quick validation
    counts = {}
    for t in ['fact_orders','dim_customers','dim_products','dim_time','dim_channels']:
        counts[t] = pd.read_sql(f"SELECT COUNT(*) as n FROM {t}", conn).iloc[0,0]
    conn.close()

    for t, n in counts.items():
        log.info(f"  ✅ {t}: {n} rows")

    return db


# ══════════════════════════════════════════════════════
# QUALITY REPORT
# ══════════════════════════════════════════════════════

def quality_report(df, db):
    log.info("Quality: generating report...")
    conn = sqlite3.connect(db)

    report = {
        'generated_at':   datetime.now().strftime('%Y-%m-%d %H:%M'),
        'total_orders':   int(pd.read_sql("SELECT COUNT(*) as n FROM fact_orders", conn).iloc[0,0]),
        'total_revenue':  float(pd.read_sql("SELECT SUM(total_amount) as s FROM fact_orders", conn).iloc[0,0]),
        'null_counts':    df.isnull().sum().to_dict(),
        'status_dist':    df['status'].value_counts().to_dict(),
        'channel_dist':   df['channel'].value_counts().to_dict(),
        'top_categories': df.groupby('category')['total_amount'].sum().nlargest(5).to_dict(),
    }
    conn.close()

    with open(BASE / 'output' / 'quality_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    log.info(f"  ✅ Quality report saved")
    return report


# ══════════════════════════════════════════════════════
# HTML SUMMARY
# ══════════════════════════════════════════════════════

def generate_summary(report):
    log.info("Output: generating HTML summary...")

    rows = ''
    for cat, val in report['top_categories'].items():
        rows += f'<tr><td>{cat}</td><td>${val:,.2f}</td></tr>'

    status_rows = ''
    for s, n in report['status_dist'].items():
        status_rows += f'<tr><td>{s}</td><td>{n}</td></tr>'

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>E-Commerce Pipeline Report</title>
<style>
  body{{font-family:Arial,sans-serif;background:#f8fafc;margin:0;padding:20px}}
  .wrap{{max-width:900px;margin:auto}}
  h1{{color:#1e3a8a;text-align:center}}
  .kpis{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:24px 0}}
  .kpi{{background:white;border-radius:10px;padding:20px;text-align:center;box-shadow:0 2px 6px rgba(0,0,0,.08)}}
  .kpi-v{{font-size:26px;font-weight:bold;color:#2563eb}}
  .kpi-l{{color:#64748b;margin-top:4px;font-size:13px}}
  .card{{background:white;border-radius:10px;padding:20px;margin-bottom:16px;box-shadow:0 2px 6px rgba(0,0,0,.08)}}
  h2{{color:#1e293b;border-bottom:2px solid #e2e8f0;padding-bottom:8px}}
  table{{width:100%;border-collapse:collapse}}
  th{{background:#2563eb;color:white;padding:10px;text-align:left}}
  td{{padding:10px;border-bottom:1px solid #f1f5f9}}
  tr:hover{{background:#f8fafc}}
  .ts{{color:#64748b;font-size:12px;text-align:center;margin-top:20px}}
</style></head><body>
<div class="wrap">
  <h1>🛒 E-Commerce ETL Pipeline Report</h1>
  <div class="kpis">
    <div class="kpi"><div class="kpi-v">{report['total_orders']:,}</div><div class="kpi-l">Total Orders</div></div>
    <div class="kpi"><div class="kpi-v">${report['total_revenue']:,.0f}</div><div class="kpi-l">Total Revenue</div></div>
    <div class="kpi"><div class="kpi-v">{len(report['status_dist'])}</div><div class="kpi-l">Order Statuses</div></div>
  </div>
  <div class="card"><h2>Top Categories by Revenue</h2>
    <table><tr><th>Category</th><th>Revenue</th></tr>{rows}</table></div>
  <div class="card"><h2>Orders by Status</h2>
    <table><tr><th>Status</th><th>Count</th></tr>{status_rows}</table></div>
  <p class="ts">Generated: {report['generated_at']} | E-Commerce ETL Pipeline v1.0</p>
</div></body></html>"""

    with open(BASE / 'output' / 'summary.html', 'w', encoding='utf-8') as f:
        f.write(html)
    log.info(f"  ✅ HTML summary saved → output/summary.html")


# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════

def run():
    log.info("=" * 60)
    log.info("🚀 Project A: E-Commerce Full ETL Pipeline")
    log.info("=" * 60)
    start = datetime.now()

    # Extract
    orders_df    = extract_orders_csv()
    customers_df = extract_customers_api()
    products_df  = extract_products_scraping()

    # Transform
    clean_df = transform(orders_df, customers_df, products_df)

    # Load
    db = load(clean_df, products_df, customers_df)

    # Quality + Summary
    report = quality_report(clean_df, db)
    generate_summary(report)

    secs = (datetime.now() - start).seconds
    log.info(f"\n✅ Pipeline finished in {secs}s")
    log.info(f"   DB      → data/ecommerce.db")
    log.info(f"   Report  → output/summary.html")
    log.info(f"   Quality → output/quality_report.json")

if __name__ == '__main__':
    run()
