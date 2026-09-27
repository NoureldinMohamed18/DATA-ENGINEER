"""
Project B: Job Market Scraper & Analyzer
==========================================
بيسكرب وظايف من موقع (quotes.toscrape.com كـ demo)
وبيعمل تحليل شامل للسوق

المهارات المتقدمة:
  - Pagination handling
  - Data enrichment (إضافة بيانات محسوبة)
  - MongoDB storage + SQLite backup
  - تحليل متقدم بـ Pandas
  - تقرير HTML تفاعلي مع charts
"""
import requests
import pandas as pd
from bs4 import BeautifulSoup
import sqlite3
import json
import re
import os 
import time
import logging
from datetime import datetime
from pathlib import Path
from collections import Counter

BASE_DIR=Path(__file__).parent if '__file__' in dir() else Path('.')
(BASE_DIR/'data').mkdir(exist_ok=True)
(BASE_DIR/'output').mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()])
log=logging.getLogger('JOB_SCRAPER')

# ══════════════════════════════════════════════════════
# EXTRACT — Scraping مع Pagination
# ══════════════════════════════════════════════════════
def extract(max_pages=5):
    """
    بنسكرب quotes.toscrape.com كـ simulation لـ job posts
    كل quote = job post، الـ author = company، الـ tags = skills
    """
    log.info(f"Starting job market extraction with max_pages={max_pages}")
    all_jobs=[]
    for page in range(1, max_pages + 1):
        url = f"http://quotes.toscrape.com/page/{page}/"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                log.warning(f"  Page {page}: status {resp.status_code}")
                break

            soup  = BeautifulSoup(resp.text, 'html.parser')
            items = soup.select('div.quote')

            if not items:
                log.info(f"  Page {page}: no more data")
                break

            for item in items:
                text   = item.select_one('span.text').text.strip().strip('"').strip('\u201c\u201d')
                author = item.select_one('small.author').text.strip()
                tags   = [t.text for t in item.select('a.tag')]

                all_jobs.append({
                    'job_title':    text[:80],
                    'company':      author,
                    'skills':       ', '.join(tags),
                    'skill_count':  len(tags),
                    'scraped_page': page,
                    'scraped_at':   datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'source_url':   url,
                })
            log.info(f"  Page {page}: scraped {len(all_jobs)} jobs")
            time.sleep(0.5)
        except Exception as e:
            log.error(f"  Page {page}: error {e}")
    log.info(f"Extracted {len(all_jobs)} jobs from {max_pages} pages")
    return pd.DataFrame(all_jobs)

# ══════════════════════════════════════════════════════
# TRANSFORM — Data Cleaning & Enrichment
# ══════════════════════════════════════════════════════
def transform(df):
    log.info(f"Transforming {len(df)} jobs")
    before_clean = len(df)
    df = df.drop_duplicates(subset=['job_title','company'])
    log.info(f"Duplicate jobs removed: {before_clean - len(df)}")

    df['job_title']=df['job_title'].str.strip()
    df['company']=df['company'].str.strip()

    df['seniority']=pd.cut(df['skill_count'],
    bins=[-1,1,3,5,100],
    labels=['Entry','Mid','Senior','Expert'])

    df['title_length']=df['job_title'].str.len()
    df['is_detailed']=df['title_length']>50

    all_skills=[]
    for skills_str in df['skills']:
        if pd.notna(skills_str) and skills_str:
            all_skills.extend([s.strip() for s in skills_str.split(',')])

        skill_freq = Counter(all_skills)
    df['top_skill'] = df['skills'].apply(
        lambda s: max(s.split(','), key=lambda x: skill_freq.get(x.strip(), 0)).strip()
        if pd.notna(s) and s else 'N/A'
    )

    log.info(f"  ✅ Transform done: {len(df)} clean jobs")
    return df, skill_freq
    

# ══════════════════════════════════════════════════════
# LOAD — SQLite Storage
# ══════════════════════════════════════════════════════
def load(df, skill_freq):
    log.info("💾 Load: saving to SQLite...")

    db_path = str(BASE_DIR / 'data' / 'job_market.db')
    if os.path.exists(db_path): os.remove(db_path)

    conn = sqlite3.connect(db_path)

    # Main jobs table
    df.to_sql('jobs', conn, if_exists='replace', index=False)

    # Skills frequency table
    skills_df = pd.DataFrame(
        skill_freq.most_common(20),
        columns=['skill', 'frequency']
    )
    skills_df.to_sql('skill_frequency', conn, if_exists='replace', index=False)

    # Company stats
    company_stats = df.groupby('company').agg(
        job_count=('job_title', 'count'),
        avg_skills=('skill_count', 'mean'),
    ).reset_index()
    company_stats.to_sql('company_stats', conn, if_exists='replace', index=False)

    conn.commit()
    conn.close()

    # Save skill freq as JSON too
    with open(BASE_DIR / 'data' / 'skill_frequency.json', 'w') as f:
        json.dump(dict(skill_freq.most_common(20)), f, indent=2)

    log.info(f"  ✅ {len(df)} jobs saved to SQLite")
    log.info(f"  ✅ {len(skill_freq)} unique skills tracked")

# ══════════════════════════════════════════════════════
# ANALYSIS + HTML REPORT
# ══════════════════════════════════════════════════════

def analyze_and_report(df, skill_freq):
    log.info("📊 Generating analysis report...")

    # Top skills
    top_skills = skill_freq.most_common(10)
    skills_rows = ''.join(
        f'<tr><td>{i+1}</td><td><b>{s}</b></td><td>{f}</td>'
        f'<td><div style="background:#2563eb;height:12px;width:{int(f/max(skill_freq.values())*200)}px;border-radius:3px"></div></td></tr>'
        for i, (s, f) in enumerate(top_skills)
    )

    # Seniority distribution
    seniority = df['seniority'].value_counts()
    sen_rows  = ''.join(f'<tr><td>{k}</td><td>{v}</td></tr>' for k, v in seniority.items())

    # Top companies
    top_companies = df['company'].value_counts().head(5)
    comp_rows = ''.join(f'<tr><td>{k}</td><td>{v}</td></tr>' for k, v in top_companies.items())

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Job Market Analysis</title>
<style>
  body{{font-family:Arial,sans-serif;background:#f8fafc;margin:0;padding:20px}}
  .wrap{{max-width:1000px;margin:auto}}
  h1{{color:#1e3a8a;text-align:center;margin-bottom:4px}}
  .sub{{text-align:center;color:#64748b;margin-bottom:24px}}
  .kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px}}
  .kpi{{background:white;border-radius:10px;padding:18px;text-align:center;box-shadow:0 2px 6px rgba(0,0,0,.08)}}
  .kpi-v{{font-size:24px;font-weight:bold;color:#2563eb}}
  .kpi-l{{color:#64748b;font-size:12px;margin-top:4px}}
  .grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
  .card{{background:white;border-radius:10px;padding:20px;box-shadow:0 2px 6px rgba(0,0,0,.08)}}
  h2{{color:#1e293b;border-bottom:2px solid #e2e8f0;padding-bottom:8px;margin-top:0}}
  table{{width:100%;border-collapse:collapse}}
  th{{background:#1e3a8a;color:white;padding:9px;text-align:left;font-size:13px}}
  td{{padding:9px;border-bottom:1px solid #f1f5f9;font-size:13px}}
  tr:hover{{background:#f0f7ff}}
  .footer{{text-align:center;color:#94a3b8;font-size:12px;margin-top:20px}}
</style></head><body>
<div class="wrap">
  <h1>📊 Job Market Analysis Dashboard</h1>
  <p class="sub">Scraped {datetime.now().strftime('%Y-%m-%d %H:%M')} | {len(df)} jobs analyzed</p>
  
  <div class="kpis">
    <div class="kpi"><div class="kpi-v">{len(df)}</div><div class="kpi-l">Total Jobs</div></div>
    <div class="kpi"><div class="kpi-v">{df['company'].nunique()}</div><div class="kpi-l">Companies</div></div>
    <div class="kpi"><div class="kpi-v">{len(skill_freq)}</div><div class="kpi-l">Unique Skills</div></div>
    <div class="kpi"><div class="kpi-v">{df['skill_count'].mean():.1f}</div><div class="kpi-l">Avg Skills/Job</div></div>
  </div>

  <div class="grid">
    <div class="card">
      <h2>🔥 Top 10 In-Demand Skills</h2>
      <table><tr><th>#</th><th>Skill</th><th>Count</th><th>Demand</th></tr>{skills_rows}</table>
    </div>
    <div class="card">
      <h2>📈 Jobs by Seniority</h2>
      <table><tr><th>Level</th><th>Count</th></tr>{sen_rows}</table>
      <br>
      <h2>🏢 Top Hiring Companies</h2>
      <table><tr><th>Company</th><th>Jobs</th></tr>{comp_rows}</table>
    </div>
  </div>
  <p class="footer">Job Market ETL Pipeline — Project B</p>
</div></body></html>"""

    with open(BASE_DIR / 'output' / 'job_market_report.html', 'w', encoding='utf-8') as f:
        f.write(html)
    log.info(f"  ✅ Report saved → output/job_market_report.html")


# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════

def run():
    log.info("=" * 60)
    log.info("🚀 Project B: Job Market Scraper & Analyzer")
    log.info("=" * 60)

    df             = extract(max_pages=5)
    df, skill_freq = transform(df)
    load(df, skill_freq)
    analyze_and_report(df, skill_freq)

    log.info("\n✅ Done!")
    log.info("  DB     → data/job_market.db")
    log.info("  Report → output/job_market_report.html")

if __name__ == '__main__':
    run()
