"""
Project C: Financial Data Pipeline
====================================
بيانات مالية من API حقيقي (exchangerate + REST countries)
مع تحليل متقدم وحفظ في MongoDB + SQLite

المهارات:
  - Multiple APIs
  - Data enrichment chains
  - MongoDB aggregation advanced
  - SQLite analytical queries
  - Excel report احترافي
"""
import requests
import sqlite3
import json
import pandas as pd
import os
import logging
from datetime import datetime,timedelta
from pathlib import Path

try:
    import pymongo
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

BASE = Path(__file__).parent if '__file__' in dir() else Path('.')
(BASE / 'data').mkdir(exist_ok=True)
(BASE / 'output').mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
log = logging.getLogger('FinancialPipeline')

#--------------------------------------------------------------
# EXTRACT
#--------------------------------------------------------------
def extract_exchange_rates():
    """AP1 : Exchange Rate API"""
    log.info('Extracting exchange rates...')
    currencies = ['EUR','GBP','JPY','SAR','AED','CAD','AUD']
    try:
        url=f'https://api.exchangerate.host/latest?base=USD&symbols={",".join(currencies)}'
        resp=requests.get(url)
        data =resp.json()
        rates=[{'currency': c, 'rate_vs_usd': r, 'date': data['date']}
                 for c, r in data['rates'].items()]
        log.info(f"  ✅ {len(rates)} currencies fetched")
        return pd.DataFrame(rates)
    except Exception as e:
        log.warning(f"  ⚠️  API failed: {e}")
        fallback = [
            {'currency':'EUR','rate_vs_usd':0.92,'date':datetime.now().strftime('%Y-%m-%d')},
            {'currency':'GBP','rate_vs_usd':0.79,'date':datetime.now().strftime('%Y-%m-%d')},
            {'currency':'JPY','rate_vs_usd':149.5,'date':datetime.now().strftime('%Y-%m-%d')},
            {'currency':'SAR','rate_vs_usd':3.75,'date':datetime.now().strftime('%Y-%m-%d')},
        ]
        return pd.DataFrame(fallback)

def extract_country_data():
    """API 2: بيانات الدول من REST Countries"""
    log.info("Extract [2/3]: Country data API...")
    try:
        resp = requests.get('https://restcountries.com/v3.1/region/middle-east', timeout=10)
        countries = resp.json()
        rows = []
        for c in countries:
            rows.append({
                'country':     c.get('name',{}).get('common',''),
                'capital':     c.get('capital',['N/A'])[0] if c.get('capital') else 'N/A',
                'population':  c.get('population', 0),
                'area_km2':    c.get('area', 0),
                'currency':    list(c.get('currencies',{}).keys())[0] if c.get('currencies') else 'N/A',
                'region':      c.get('subregion',''),
                'gdp_proxy':   c.get('population',0) * 10000  # تقدير بسيط
            })
        df = pd.DataFrame(rows)
        log.info(f"  ✅ {len(df)} countries fetched")
        return df
    except Exception as e:
        log.warning(f"  ⚠️  API failed: {e}")
        return pd.DataFrame([
            {'country':'Egypt','capital':'Cairo','population':104000000,'area_km2':1002450,'currency':'EGP','region':'Northern Africa','gdp_proxy':1040000000000},
            {'country':'Saudi Arabia','capital':'Riyadh','population':35000000,'area_km2':2149690,'currency':'SAR','region':'Western Asia','gdp_proxy':350000000000},
        ])


def generate_transactions():
    """توليد بيانات معاملات مالية تجريبية"""
    log.info("Extract [3/3]: Generating transaction data...")
    import random
    random.seed(99)

    types    = ['transfer', 'payment', 'withdrawal', 'deposit', 'investment']
    statuses = ['completed', 'pending', 'failed', 'reversed']
    currencies = ['USD', 'EUR', 'GBP', 'SAR', 'AED']
    
    rows = []
    base = datetime(2024, 1, 1)
    for i in range(500):
        amount = round(random.uniform(50, 50000), 2)
        rows.append({
            'txn_id':       f'TXN-{i+1:05d}',
            'amount':       amount,
            'currency':     random.choice(currencies),
            'txn_type':     random.choice(types),
            'status':       random.choice(statuses),
            'txn_date':     (base + timedelta(days=random.randint(0,179))).strftime('%Y-%m-%d'),
            'customer_id':  random.randint(1, 100),
            'country':      random.choice(['Egypt','Saudi Arabia','UAE','Kuwait','Jordan']),
            'fee':          round(amount * random.uniform(0.001, 0.02), 2),
        })
    
    df = pd.DataFrame(rows)
    log.info(f"  ✅ {len(df)} transactions generated")
    return df

# ══════════════════════════════════════════════════════
# TRANSFORM
# ══════════════════════════════════════════════════════

def transform(txn_df, rates_df, countries_df):
    log.info("Transform: enriching financial data...")

    # نحول الـ rates لـ dict
    rate_map = dict(zip(rates_df['currency'], rates_df['rate_vs_usd']))
    rate_map['USD'] = 1.0

    # Validation
    rejected = txn_df[txn_df['amount'] <= 0].copy()
    rejected['rejection_reason'] = 'invalid amount'
    txn_df = txn_df[txn_df['amount'] > 0].copy()

    bad_dates = txn_df[pd.to_datetime(txn_df['txn_date'], errors='coerce').isna()].copy()
    bad_dates['rejection_reason'] = 'invalid date'
    txn_df = txn_df[pd.to_datetime(txn_df['txn_date'], errors='coerce').notna()].copy()

    if len(rejected) + len(bad_dates) > 0:
        pd.concat([rejected, bad_dates]).to_csv(BASE/'data'/'rejected.csv', index=False)

    # Convert all amounts to USD
    txn_df['amount_usd'] = txn_df.apply(
        lambda r: r['amount'] / rate_map.get(r['currency'], 1.0), axis=1
    ).round(2)

    # Net amount after fee
    txn_df['net_amount_usd'] = (txn_df['amount_usd'] - txn_df['fee']).round(2)

    # Date features
    txn_df['txn_date'] = pd.to_datetime(txn_df['txn_date'])
    txn_df['month']    = txn_df['txn_date'].dt.month
    txn_df['quarter']  = txn_df['txn_date'].dt.quarter
    txn_df['weekday']  = txn_df['txn_date'].dt.day_name()

    # Risk flag
    txn_df['is_high_value'] = txn_df['amount_usd'] > 10000
    txn_df['is_failed']     = txn_df['status'] == 'failed'

    # Merge country data
    txn_df = txn_df.merge(
        countries_df[['country','population','currency']].rename(columns={'currency':'country_currency'}),
        on='country', how='left'
    )

    log.info(f"  ✅ {len(txn_df)} transactions ready")
    return txn_df


# ══════════════════════════════════════════════════════
# LOAD
# ══════════════════════════════════════════════════════

def load_sqlite(txn_df, rates_df, countries_df):
    log.info("Load [SQLite]: saving all data...")
    db = str(BASE / 'data' / 'financial.db')
    if os.path.exists(db): os.remove(db)

    conn = sqlite3.connect(db)
    txn_df.to_sql('transactions', conn, if_exists='replace', index=False)
    rates_df.to_sql('exchange_rates', conn, if_exists='replace', index=False)
    countries_df.to_sql('countries', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()
    log.info(f"  ✅ SQLite saved: {len(txn_df)} transactions")


def load_mongodb(txn_df):
    if not MONGO_AVAILABLE:
        log.info("  ⚠️  pymongo not installed — skipping MongoDB")
        return
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
        client.server_info()
        db  = client['financial_analytics']
        col = db['transactions']
        col.drop()
        docs = txn_df.to_dict('records')
        for d in docs:
            for k,v in d.items():
                if hasattr(v, 'item'): d[k] = v.item()
        col.insert_many(docs)
        log.info(f"  ✅ MongoDB: {len(docs)} documents inserted")

        # Aggregation
        result = list(col.aggregate([
            {"$group": {"_id":"$txn_type", "total":{"$sum":"$amount_usd"}, "count":{"$sum":1}}},
            {"$sort": {"total":-1}}
        ]))
        log.info("  MongoDB Aggregation — Revenue by type:")
        for r in result:
            log.info(f"    {r['_id']}: ${r['total']:,.0f} ({r['count']} txns)")
    except Exception as e:
        log.warning(f"  ⚠️  MongoDB not available: {e}")


# ══════════════════════════════════════════════════════
# EXCEL REPORT
# ══════════════════════════════════════════════════════

def generate_excel(txn_df, rates_df):
    if not EXCEL_AVAILABLE:
        log.info("  ⚠️  openpyxl not installed — skipping Excel")
        return

    log.info("Output: generating Excel report...")
    wb    = openpyxl.Workbook()
    blue  = PatternFill("solid", fgColor="1E3A8A")
    wfont = Font(bold=True, color="FFFFFF")
    center= Alignment(horizontal='center')

    # Sheet 1: Summary
    ws = wb.active
    ws.title = "Summary"
    summary_data = [
        ["Metric", "Value"],
        ["Total Transactions", len(txn_df)],
        ["Total Volume (USD)", f"${txn_df['amount_usd'].sum():,.0f}"],
        ["Completed", len(txn_df[txn_df['status']=='completed'])],
        ["Failed", len(txn_df[txn_df['status']=='failed'])],
        ["High Value (>$10k)", len(txn_df[txn_df['is_high_value']])],
        ["Avg Transaction (USD)", f"${txn_df['amount_usd'].mean():,.0f}"],
    ]
    for r, row in enumerate(summary_data, 1):
        for c, val in enumerate(row, 1):
            cell = ws.cell(r, c, val)
            if r == 1:
                cell.fill = blue
                cell.font = wfont
                cell.alignment = center
        ws.column_dimensions[get_column_letter(1)].width = 28
        ws.column_dimensions[get_column_letter(2)].width = 20

    # Sheet 2: By Type
    ws2 = wb.create_sheet("By Type")
    by_type = txn_df.groupby('txn_type').agg(
        count=('txn_id','count'), total_usd=('amount_usd','sum'), avg_usd=('amount_usd','mean')
    ).reset_index()
    headers = ['Transaction Type','Count','Total USD','Avg USD']
    for c, h in enumerate(headers, 1):
        cell = ws2.cell(1, c, h)
        cell.fill = blue; cell.font = wfont
    for r, row in by_type.iterrows():
        ws2.cell(r+2, 1, row['txn_type'])
        ws2.cell(r+2, 2, int(row['count']))
        ws2.cell(r+2, 3, round(row['total_usd'], 2))
        ws2.cell(r+2, 4, round(row['avg_usd'], 2))

    # Sheet 3: Exchange Rates
    ws3 = wb.create_sheet("Exchange Rates")
    for c, h in enumerate(['Currency','Rate vs USD','Date'], 1):
        cell = ws3.cell(1, c, h)
        cell.fill = blue; cell.font = wfont
    for r, row in rates_df.iterrows():
        ws3.cell(r+2, 1, row['currency'])
        ws3.cell(r+2, 2, row['rate_vs_usd'])
        ws3.cell(r+2, 3, row['date'])

    path = str(BASE / 'output' / 'financial_report.xlsx')
    wb.save(path)
    log.info(f"  ✅ Excel saved → output/financial_report.xlsx")


# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════

def run():
    log.info("=" * 60)
    log.info("🚀 Project C: Financial Data Pipeline")
    log.info("=" * 60)

    rates_df    = extract_exchange_rates()
    countries_df= extract_country_data()
    txn_df      = generate_transactions()

    txn_df = transform(txn_df, rates_df, countries_df)

    load_sqlite(txn_df, rates_df, countries_df)
    load_mongodb(txn_df)
    generate_excel(txn_df, rates_df)

    # Quick analysis print
    log.info("\n📊 Quick Analysis:")
    log.info(f"  Total volume: ${txn_df['amount_usd'].sum():,.0f} USD")
    log.info(f"  By status:\n{txn_df.groupby('status')['amount_usd'].sum().to_string()}")
    log.info(f"  By country:\n{txn_df.groupby('country')['amount_usd'].sum().nlargest(5).to_string()}")

    log.info("\n✅ Pipeline complete!")

if __name__ == '__main__':
    run()
