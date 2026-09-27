"""
Project E: Retail Analytics Platform (Advanced Capstone)
==========================================================
أكبر وأشمل مشروع — بيجمع كل المهارات:

  ✅ 4 مصادر بيانات (CSV + 2 APIs + Scraping)
  ✅ Data Quality Monitor كامل
  ✅ Star Schema متقدم في SQLite
  ✅ MongoDB للـ raw documents
  ✅ Excel report متعدد الـ sheets مع charts
  ✅ HTML Dashboard تفاعلي
  ✅ Pipeline logging كامل
  ✅ Config-driven architecture
  ✅ Error handling شامل
"""

import pandas as pd
import requests 
import json
from bs4 import BeautifulSoup
import random
import os
import logging
from datetime import datetime,timedelta
import sqlite3
import time
from pathlib import Path
from collections import defaultdict

try:
    import pymongo
    MONGO=True
except ImportError:
    MONGO=False

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import BarChart, Reference, LineChart
    EXCEL = True
except ImportError:
    EXCEL = False

# ── Config ──────────────────────────────────────────
BASE=Path(__file__).parent if "__file__" in dir() else Path('.')
for d in ['data','output','logs']:
    (BASE/d).mkdir(exist_ok=True)

CONFIG={
    'sources':{
        "sales_csv":str(BASE/'data'/'retail_sales.csv'),
        "exchange_api":"https://api.frankfurter.app/latest?from=USD&to=EUR,GBP,SAR",
        'countries_api':"https://restcountries.com/v3.1/alpha?codes=eg,sa,ae,jo,kw",
        "scrape_url":"http://books.toscrape.com/catalogue/page-{}.html",
    },
    'quality':{
        'quantity':{'min':1,'max':200},
        'unit_price':{'min':1,'max':100000},
    },
    'db':{
        'sqlite3':str(BASE/'data'/'retail_plattform.db'),
    }
}
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(BASE/'logs'/'platform.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log=logging.getLogger('RetailPlatform')

# ══════════════════════════════════════════════════════
# DATA GENERATOR
# ══════════════════════════════════════════════════════

def generate_sales_csv():
    """بنعمل بيانات مبيعات retail واقعية ومعقدة"""
    path = Path(CONFIG['sources']['sales_csv'])
    if path.exists():
        return

    random.seed(2024)
    categories  = ['Electronics','Clothing','Food','Books','Sports','Home','Beauty']
    products    = {
        'Electronics': ['Laptop','Phone','Tablet','Headphones','Camera'],
        'Clothing':    ['T-Shirt','Jeans','Dress','Jacket','Shoes'],
        'Food':        ['Coffee','Tea','Chocolate','Nuts','Honey'],
        'Books':       ['Novel','Science','History','Self-Help','Comics'],
        'Sports':      ['Yoga Mat','Dumbbells','Resistance Band','Bottle','Shoes'],
        'Home':        ['Pillow','Blanket','Lamp','Clock','Mirror'],
        'Beauty':      ['Cream','Perfume','Shampoo','Lipstick','Serum'],
    }
    salespeople = ['Ahmed','Fatma','Mohamed','Sara','Omar','Rana']
    cities      = ['Cairo','Alexandria','Giza','Riyadh','Dubai','Amman']
    channels    = ['online','store','phone','app']
    
    rows = []
    base = datetime(2024, 1, 1)
    for i in range(600):
        cat     = random.choice(categories)
        product = random.choice(products[cat])
        qty     = random.choice([1,1,2,2,3,4,5,-1,0,150])   # أخطاء مقصودة
        price   = round(random.uniform(5, 2000), 2)
        rows.append({
            'order_id':    f'R-{i+1:05d}',
            'date':        (base + timedelta(days=random.randint(0,364))).strftime('%Y-%m-%d'),
            'product':     product,
            'category':    cat,
            'quantity':    qty,
            'unit_price':  price,
            'salesperson': random.choice(salespeople),
            'city':        random.choice(cities),
            'channel':     random.choice(channels),
            'customer_id': random.randint(1, 200),
            'return':      random.random() < 0.05,
        })
    pd.DataFrame(rows).to_csv(path, index=False)
    log.info(f"  Generated {len(rows)} rows → {path.name}")

# ══════════════════════════════════════════════════════
# EXTRACT LAYER
# ══════════════════════════════════════════════════════
class Extractor:
    def sales_csv(self):
        log.info("Extract [1/4]: Sales CSV...")
        generate_sales_csv()
        df=pd.read_csv(CONFIG['sources']['sales_csv'])
        log.info(f"  ✅ {len(df)} rows")
        return df

    def exchange_rates(self):
        log.info("Extract [2/4]: Exchange rates API...")
        try:
            r=requests.get(CONFIG['sources']['exchange_api'],timeout=10)
            d=r.json()
            rates={c:v for c,v in d['rates'].items()}
            rates['USD']=1.0
            rates['date']=d['date']
            log.info("  ✅ {len(rates)-1} currencies")
            return rates 
        except:
            log.warning("  ⚠️  Using fallback rates")
            return {'EUR':0.92,'GBP':0.79,'SAR':3.75,'USD':1.0,'date':datetime.now().strftime('%Y-%m-%d')}

    def country_info(self):
        log.info("Extract [3/4]: Country API...")
        try:
            r=requests.get(CONFIG['sources']['countries_api'],timeout=10)
            countries=r.json()
            rows=[]
            for c in countries:
                rows.append({
                    'country_code':c.get('cca2',''),
                    'country_name': c.get('name',{}).get('common',''),
                    'population':   c.get('population',0),
                    'region':       c.get('region',''),
                    'subregion':    c.get('subregion',''),
                })
            log.info(f"  ✅ {len(rows)} countries")
            return pd.DataFrame(rows)
        except:
            log.warning("  ⚠️  Using fallback countries")
            return pd.DataFrame([
                {'country_code':'EG','country_name':'Egypt','population':104000000,'region':'Africa','subregion':'Northern Africa'},
                {'country_code':'SA','country_name':'Saudi Arabia','population':35000000,'region':'Asia','subregion':'Western Asia'},
            ])

    def scrape_products(self,pages=2):
        log.info("Extract [4/4]: Product scraping...")
        products=[]
        RATING={'One':1,'Two':2,'Three':3,'Four':4,'Five':5}
        for page in range(1,pages+1):
            try:
                url=CONFIG['sources']['scrpae_url'].format(page)
                resp=requests.get(url,timneout=10)
                soup=BeautifulSoup(resp.text,'html.parser')
                for b in soup.select('article.product_pod'):
                    price = float(''.join(c for c in b.select_one('.price_color').text if c.isdigit() or c=='.'))
                    products.append({
                        'product_name': b.select_one('h3 a')['title'][:50],
                        'market_price': price,
                        'market_rating': RATING.get(b.select_one('p.star-rating')['class'][1],0),
                        'in_stock': 'In stock' in b.select_one('.availability').text
                    })
                time.sleep(0.5)
            except Exception as e:
                log.warning(f"  Page {page}: {e}")
        log.info(f"  ✅ {len(products)} products scraped")
        return pd.DataFrame(products)

# ══════════════════════════════════════════════════════
# TRANSFORM LAYER
# ══════════════════════════════════════════════════════
class Transformer:
    def __init__(self,config):
        self.rules=config['quality']
    
    def validate(self,df):
        rejected=[]
        # Quantity
        r = self.rules['quantity']
        bad = df[(df['quantity'] < r['min']) | (df['quantity'] > r['max'])].copy()
        bad['reason'] = 'invalid_quantity'
        rejected.append(bad)
        df = df[(df['quantity'] >= r['min']) & (df['quantity'] <= r['max'])].copy()

        # Price
        r = self.rules['unit_price']
        bad2 = df[(df['unit_price'] < r['min']) | (df['unit_price'] > r['max'])].copy()
        bad2['reason'] = 'invalid_price'
        rejected.append(bad2)
        df = df[(df['unit_price'] >= r['min']) & (df['unit_price'] <= r['max'])].copy()

        # Duplicates
        df = df.drop_duplicates(subset=['order_id'])

        # Date
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        bad3 = df[df['date'].isna()].copy()
        bad3['reason'] = 'invalid_date'
        rejected.append(bad3)
        df = df[df['date'].notna()].copy()

        if rejected:
            all_rej = pd.concat(rejected, ignore_index=True).dropna(how='all')
            all_rej.to_csv(BASE/'data'/'rejected_rows.csv', index=False)
            log.info(f"  ⚠️  {len(all_rej)} rows rejected")

        log.info(f"  ✅ {len(df)} rows after validation")
        return df

    def enrich(self, df, rates):
        # Revenue
        df['total_revenue'] = (df['quantity'] * df['unit_price']).round(2)
        df['total_eur']     = (df['total_revenue'] * rates.get('EUR', 0.92)).round(2)
        df['total_gbp']     = (df['total_revenue'] * rates.get('GBP', 0.79)).round(2)

        # Date features
        df['year']    = df['date'].dt.year
        df['month']   = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['weekday'] = df['date'].dt.day_name()
        df['week']    = df['date'].dt.isocalendar().week.astype(int)

        # Segmentation
        df['revenue_segment'] = pd.cut(df['total_revenue'],
            bins=[0,100,500,2000,float('inf')],
            labels=['Low','Medium','High','Premium'])

        # Return flag
        df['is_return'] = df['return'].astype(bool)
        df['net_revenue'] = df['total_revenue'] * (~df['is_return']).astype(int)

        log.info("  ✅ Data enriched")
        return df

# ══════════════════════════════════════════════════════
# LOAD LAYER
# ══════════════════════════════════════════════════════
class Loader:
    def __init__(self, db_path):
        self.db = db_path
        if os.path.exists(db_path): os.remove(db_path)

    def to_sqlite(self, df):
        log.info("Load [SQLite]: building Star Schema...")
        conn = sqlite3.connect(self.db)

        # dim_products
        prod = df[['product','category']].drop_duplicates().reset_index(drop=True)
        prod.insert(0,'product_id', range(1,len(prod)+1))
        prod.to_sql('dim_products', conn, if_exists='replace', index=False)

        # dim_salespersons
        sales = df[['salesperson']].drop_duplicates().reset_index(drop=True)
        sales.insert(0,'sp_id', range(1,len(sales)+1))
        sales.to_sql('dim_salespersons', conn, if_exists='replace', index=False)

        # dim_cities
        cities = df[['city']].drop_duplicates().reset_index(drop=True)
        cities.insert(0,'city_id', range(1,len(cities)+1))
        cities.to_sql('dim_cities', conn, if_exists='replace', index=False)

        # dim_time
        time_df = df[['date','year','month','quarter','weekday','week']].drop_duplicates('date').copy()
        time_df['date_str'] = time_df['date'].dt.strftime('%Y-%m-%d')
        time_df = time_df.drop(columns=['date'])
        time_df.to_sql('dim_time', conn, if_exists='replace', index=False)

        # dim_channels
        ch = df[['channel']].drop_duplicates().reset_index(drop=True)
        ch.insert(0,'ch_id', range(1,len(ch)+1))
        ch.to_sql('dim_channels', conn, if_exists='replace', index=False)

        # fact_sales
        fact = df.merge(prod, on=['product','category'])
        fact = fact.merge(sales, on='salesperson')
        fact = fact.merge(cities, on='city')
        fact = fact.merge(ch, on='channel')
        time_map = time_df[['date_str']].reset_index().rename(columns={'index':'time_id'})
        fact['date_str'] = fact['date'].dt.strftime('%Y-%m-%d')
        fact = fact.merge(time_map, on='date_str')

        fact_cols = ['order_id','customer_id','product_id','sp_id','city_id','ch_id','time_id',
                     'quantity','unit_price','total_revenue','total_eur','net_revenue',
                     'revenue_segment','is_return','year','month','quarter']
        fact[fact_cols].to_sql('fact_sales', conn, if_exists='replace', index=False)

        conn.commit()

        # Validation queries
        for t in ['fact_sales','dim_products','dim_salespersons','dim_cities','dim_time','dim_channels']:
            n = pd.read_sql(f"SELECT COUNT(*) as n FROM {t}", conn).iloc[0,0]
            log.info(f"  ✅ {t}: {n} rows")

        conn.close()
        return fact

    def to_mongodb(self, df):
        if not MONGO:
            return
        try:
            client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
            client.server_info()
            col = client['retail_platform']['raw_sales']
            col.drop()
            docs = json.loads(df.to_json(orient='records', date_format='iso'))
            col.insert_many(docs)
            log.info(f"  ✅ MongoDB: {len(docs)} documents")
        except:
            log.info("  ⚠️  MongoDB not available")


# ══════════════════════════════════════════════════════
# ANALYTICS + REPORTS
# ══════════════════════════════════════════════════════

def generate_analytics(df):
    """بنعمل تحليلات شاملة وبنرجعها"""
    conn = sqlite3.connect(CONFIG['db']['sqlite3'])

    analytics = {
        'total_revenue':    df['total_revenue'].sum(),
        'net_revenue':      df['net_revenue'].sum(),
        'total_orders':     len(df),
        'avg_order_value':  df['total_revenue'].mean(),
        'return_rate':      df['is_return'].mean() * 100,
        'by_category':      df.groupby('category')['total_revenue'].sum().nlargest(5).to_dict(),
        'by_channel':       df.groupby('channel')['total_revenue'].sum().to_dict(),
        'by_salesperson':   df.groupby('salesperson')['total_revenue'].sum().nlargest(5).to_dict(),
        'monthly_revenue':  df.groupby('month')['total_revenue'].sum().to_dict(),
        'by_segment':       df['revenue_segment'].value_counts().to_dict(),
        'by_city':          df.groupby('city')['total_revenue'].sum().nlargest(5).to_dict(),
    }
    conn.close()
    return analytics


def generate_html_dashboard(analytics):
    log.info("Output: generating HTML dashboard...")

    def table_rows(d):
        return ''.join(f'<tr><td>{k}</td><td>${v:,.0f}</td></tr>' for k,v in d.items())

    cat_rows  = table_rows(analytics['by_category'])
    ch_rows   = table_rows(analytics['by_channel'])
    sp_rows   = table_rows(analytics['by_salesperson'])
    city_rows = table_rows(analytics['by_city'])

    seg_rows = ''.join(
        f'<tr><td>{k}</td><td>{v}</td></tr>'
        for k,v in analytics['by_segment'].items() if k is not None
    )

    monthly_bars = ''
    max_rev = max(analytics['monthly_revenue'].values()) if analytics['monthly_revenue'] else 1
    months  = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    for m, rev in sorted(analytics['monthly_revenue'].items()):
        h = int(rev / max_rev * 120)
        monthly_bars += f'<div class="bar-wrap"><div class="bar" style="height:{h}px" title="${rev:,.0f}"></div><div class="bar-label">{months[int(m)-1]}</div></div>'

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Retail Analytics Platform</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:Arial,sans-serif;background:#f1f5f9;color:#1e293b}}
  .header{{background:linear-gradient(135deg,#1e3a8a,#2563eb);color:white;padding:28px;text-align:center}}
  .header h1{{font-size:26px;margin-bottom:6px}}
  .header p{{opacity:.8;font-size:13px}}
  .wrap{{max-width:1200px;margin:24px auto;padding:0 20px}}
  .kpis{{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:24px}}
  .kpi{{background:white;border-radius:10px;padding:18px;text-align:center;box-shadow:0 2px 6px rgba(0,0,0,.07)}}
  .kpi-v{{font-size:22px;font-weight:bold;color:#2563eb}}
  .kpi-l{{color:#64748b;font-size:12px;margin-top:4px}}
  .grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:16px}}
  .grid2{{display:grid;grid-template-columns:2fr 1fr;gap:16px;margin-bottom:16px}}
  .card{{background:white;border-radius:10px;padding:20px;box-shadow:0 2px 6px rgba(0,0,0,.07)}}
  h2{{color:#1e293b;font-size:14px;margin-bottom:14px;padding-bottom:8px;border-bottom:2px solid #e2e8f0}}
  table{{width:100%;border-collapse:collapse}}
  th{{background:#2563eb;color:white;padding:9px;text-align:left;font-size:12px}}
  td{{padding:9px;border-bottom:1px solid #f1f5f9;font-size:12px}}
  tr:hover{{background:#f8fafc}}
  .chart{{display:flex;align-items:flex-end;gap:8px;height:140px;padding:10px 0}}
  .bar-wrap{{display:flex;flex-direction:column;align-items:center;flex:1}}
  .bar{{background:linear-gradient(to top,#1e3a8a,#2563eb);border-radius:3px 3px 0 0;width:100%;min-height:4px;transition:.3s}}
  .bar-label{{font-size:10px;color:#64748b;margin-top:4px}}
  .footer{{text-align:center;color:#94a3b8;font-size:12px;padding:20px}}
  .badge{{background:#dbeafe;color:#1e40af;padding:2px 8px;border-radius:10px;font-size:11px}}
</style></head><body>
<div class="header">
  <h1>🛍️ Retail Analytics Platform</h1>
  <p>End-to-End Data Pipeline · Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div>
<div class="wrap">
  <div class="kpis">
    <div class="kpi"><div class="kpi-v">${analytics['total_revenue']:,.0f}</div><div class="kpi-l">Total Revenue</div></div>
    <div class="kpi"><div class="kpi-v">${analytics['net_revenue']:,.0f}</div><div class="kpi-l">Net Revenue</div></div>
    <div class="kpi"><div class="kpi-v">{analytics['total_orders']:,}</div><div class="kpi-l">Total Orders</div></div>
    <div class="kpi"><div class="kpi-v">${analytics['avg_order_value']:,.0f}</div><div class="kpi-l">Avg Order Value</div></div>
    <div class="kpi"><div class="kpi-v">{analytics['return_rate']:.1f}%</div><div class="kpi-l">Return Rate</div></div>
  </div>

  <div class="card" style="margin-bottom:16px">
    <h2>📅 Monthly Revenue Trend</h2>
    <div class="chart">{monthly_bars}</div>
  </div>

  <div class="grid3">
    <div class="card"><h2>🗂️ Revenue by Category</h2>
      <table><tr><th>Category</th><th>Revenue</th></tr>{cat_rows}</table></div>
    <div class="card"><h2>📱 Revenue by Channel</h2>
      <table><tr><th>Channel</th><th>Revenue</th></tr>{ch_rows}</table></div>
    <div class="card"><h2>🏆 Top Salespersons</h2>
      <table><tr><th>Name</th><th>Revenue</th></tr>{sp_rows}</table></div>
  </div>

  <div class="grid2">
    <div class="card"><h2>🏙️ Revenue by City</h2>
      <table><tr><th>City</th><th>Revenue</th></tr>{city_rows}</table></div>
    <div class="card"><h2>💎 Order Segments</h2>
      <table><tr><th>Segment</th><th>Orders</th></tr>{seg_rows}</table></div>
  </div>
</div>
<div class="footer">Retail Analytics Platform — Project E (Advanced Capstone)</div>
</body></html>"""

    with open(BASE/'output'/'retail_dashboard.html','w',encoding='utf-8') as f:
        f.write(html)
    log.info("  ✅ Dashboard → output/retail_dashboard.html")


def generate_excel_report(df, analytics):
    if not EXCEL:
        log.info("  ⚠️  openpyxl not installed — skipping Excel")
        return

    log.info("Output: generating Excel report...")
    wb   = openpyxl.Workbook()
    blue = PatternFill("solid", fgColor="1E3A8A")
    wf   = Font(bold=True, color="FFFFFF")
    ctr  = Alignment(horizontal='center')

    def set_header(ws, headers, row=1):
        for c, h in enumerate(headers, 1):
            cell = ws.cell(row, c, h)
            cell.fill = blue; cell.font = wf; cell.alignment = ctr
            ws.column_dimensions[get_column_letter(c)].width = max(len(h)+4, 14)

    # Sheet 1: Executive Summary
    ws1 = wb.active; ws1.title = "Executive Summary"
    ws1['A1'] = "Retail Analytics Platform — Executive Summary"
    ws1['A1'].font = Font(size=16, bold=True, color="1E3A8A")
    ws1['A2'] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ws1['A2'].font = Font(color="64748b")

    summary = [
        ["","Metric","Value"],
        ["","Total Revenue", f"${analytics['total_revenue']:,.2f}"],
        ["","Net Revenue",   f"${analytics['net_revenue']:,.2f}"],
        ["","Total Orders",  analytics['total_orders']],
        ["","Avg Order",     f"${analytics['avg_order_value']:,.2f}"],
        ["","Return Rate",   f"{analytics['return_rate']:.1f}%"],
    ]
    for r, row in enumerate(summary, 4):
        for c, val in enumerate(row, 1):
            cell = ws1.cell(r, c, val)
            if r == 4:
                cell.fill = blue; cell.font = wf
            elif c == 2:
                cell.font = Font(bold=True)

    # Sheet 2: Category Analysis
    ws2 = wb.create_sheet("By Category")
    cat_df = df.groupby('category').agg(
        orders=('order_id','count'), revenue=('total_revenue','sum'),
        avg_price=('unit_price','mean'), units=('quantity','sum')
    ).reset_index().sort_values('revenue', ascending=False)
    set_header(ws2, ['Category','Orders','Revenue','Avg Price','Units'])
    for r, row in cat_df.iterrows():
        ws2.cell(r+2,1,row['category']); ws2.cell(r+2,2,int(row['orders']))
        ws2.cell(r+2,3,round(row['revenue'],2)); ws2.cell(r+2,4,round(row['avg_price'],2))
        ws2.cell(r+2,5,int(row['units']))

    # Chart for categories
    chart = BarChart()
    chart.title = "Revenue by Category"
    chart.style = 10
    data = Reference(ws2, min_col=3, min_row=1, max_row=len(cat_df)+1)
    cats = Reference(ws2, min_col=1, min_row=2, max_row=len(cat_df)+1)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    ws2.add_chart(chart, "G2")

    # Sheet 3: Monthly Trend
    ws3 = wb.create_sheet("Monthly Trend")
    monthly = df.groupby(['year','month']).agg(revenue=('total_revenue','sum'), orders=('order_id','count')).reset_index()
    set_header(ws3, ['Year','Month','Revenue','Orders'])
    for r, row in monthly.iterrows():
        ws3.cell(r+2,1,int(row['year'])); ws3.cell(r+2,2,int(row['month']))
        ws3.cell(r+2,3,round(row['revenue'],2)); ws3.cell(r+2,4,int(row['orders']))

    line = LineChart()
    line.title = "Monthly Revenue Trend"
    line.style = 12
    data = Reference(ws3, min_col=3, min_row=1, max_row=len(monthly)+1)
    line.add_data(data, titles_from_data=True)
    ws3.add_chart(line, "F2")

    # Sheet 4: Raw Data sample
    ws4 = wb.create_sheet("Data Sample")
    sample = df.head(100).copy()
    sample['date'] = sample['date'].dt.strftime('%Y-%m-%d')
    cols = ['order_id','date','product','category','quantity','unit_price','total_revenue','salesperson','city','channel']
    set_header(ws4, cols)
    for r, row in sample.iterrows():
        for c, col in enumerate(cols, 1):
            ws4.cell(r+2, c, str(row[col]))

    path = str(BASE/'output'/'retail_report.xlsx')
    wb.save(path)
    log.info(f"  ✅ Excel → output/retail_report.xlsx")


# ══════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════

def run():
    log.info("="*65)
    log.info("🚀 Project E: Retail Analytics Platform (Advanced Capstone)")
    log.info("="*65)
    start = datetime.now()

    # Extract
    ext          = Extractor()
    sales_df     = ext.sales_csv()
    rates        = ext.exchange_rates()
    countries_df = ext.country_info()
    products_df  = ext.scrape_products(pages=2)

    # Transform
    trx      = Transformer(CONFIG)
    clean_df = trx.validate(sales_df)
    clean_df = trx.enrich(clean_df, rates)

    # Load
    loader = Loader(CONFIG['db']['sqlite3'])
    fact   = loader.to_sqlite(clean_df)
    loader.to_mongodb(clean_df)

    # Analytics + Reports
    analytics = generate_analytics(clean_df)
    generate_html_dashboard(analytics)
    generate_excel_report(clean_df, analytics)

    duration = (datetime.now() - start).seconds
    log.info(f"\n{'='*65}")
    log.info(f"✅ Platform complete in {duration}s")
    log.info(f"   Dashboard → output/retail_dashboard.html")
    log.info(f"   Excel     → output/retail_report.xlsx")
    log.info(f"   Database  → data/retail_platform.db")
    log.info(f"   Logs      → logs/platform.log")
    log.info(f"{'='*65}")

if __name__ == '__main__':
    run()
