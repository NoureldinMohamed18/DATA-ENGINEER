"""
Project D: Multi-Source News & Content Aggregator
===================================================
بيسكرب محتوى من مصادر متعددة، بيحلله، وبيعمل
trending analysis وتقرير شامل

المهارات المتقدمة:
  - Multi-source scraping (pagination + different structures)
  - Text analysis (word frequency, length stats)
  - Trending detection
  - MongoDB للـ documents الغير منتظمة
  - SQLite للـ structured analytics
  - Dashboard HTML متقدم
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import json
import re
import os
import time
import logging
from datetime import datetime
from pathlib import Path
from collections import Counter

BASE = Path(__file__).parent if '__file__' in dir() else Path('.')
(BASE / 'data').mkdir(exist_ok=True)
(BASE / 'output').mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
log = logging.getLogger('NewsAggregator')

# Common words to ignore in trending analysis
STOP_WORDS = {'the','a','an','and','or','but','in','on','at','to','for',
              'of','with','by','from','is','was','are','were','be','been',
              'have','has','had','do','does','did','will','would','could',
              'should','may','might','this','that','these','those','it','its'}


# ══════════════════════════════════════════════════════
# EXTRACT — 3 مصادر مختلفة
# ══════════════════════════════════════════════════════

def extract_quotes(max_pages=5):
    """Source 1: Quotes (كـ articles simulation)"""
    log.info("Extract [1/3]: Quotes source...")
    items = []

    for page in range(1, max_pages+1):
        try:
            url  = f"http://quotes.toscrape.com/page/{page}/"
            resp = requests.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            quotes = soup.select('div.quote')
            if not quotes: break

            for q in quotes:
                text   = q.select_one('span.text').text.strip().strip('"').strip('\u201c\u201d')
                author = q.select_one('small.author').text.strip()
                tags   = [t.text for t in q.select('a.tag')]
                items.append({
                    'source':   'quotes_toscrape',
                    'title':    text[:100],
                    'author':   author,
                    'tags':     tags,
                    'tag_str':  ', '.join(tags),
                    'word_count': len(text.split()),
                    'page':     page,
                })
            time.sleep(0.3)
        except Exception as e:
            log.warning(f"  Quotes page {page}: {e}")

    log.info(f"  ✅ Quotes: {len(items)} items")
    return items


def extract_books(max_pages=3):
    """Source 2: Books (كـ product articles)"""
    log.info("Extract [2/3]: Books source...")
    items = []
    RATING = {'One':1,'Two':2,'Three':3,'Four':4,'Five':5}

    for page in range(1, max_pages+1):
        try:
            url  = f"http://books.toscrape.com/catalogue/page-{page}.html"
            resp = requests.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')

            for book in soup.select('article.product_pod'):
                title  = book.select_one('h3 a')['title']
                price  = float(''.join(c for c in book.select_one('.price_color').text if c.isdigit() or c=='.'))
                rating = RATING.get(book.select_one('p.star-rating')['class'][1], 0)
                stock  = 'In stock' in book.select_one('.availability').text

                items.append({
                    'source':      'books_toscrape',
                    'title':       title,
                    'author':      'N/A',
                    'tags':        ['book', 'literature'],
                    'tag_str':     'book, literature',
                    'word_count':  len(title.split()),
                    'price':       price,
                    'rating':      rating,
                    'in_stock':    stock,
                    'page':        page,
                })
            time.sleep(0.3)
        except Exception as e:
            log.warning(f"  Books page {page}: {e}")

    log.info(f"  ✅ Books: {len(items)} items")
    return items


def extract_api_posts():
    """Source 3: JSONPlaceholder posts كـ articles"""
    log.info("Extract [3/3]: API posts...")
    try:
        resp  = requests.get('https://jsonplaceholder.typicode.com/posts', timeout=10)
        posts = resp.json()
        items = []
        for p in posts:
            body = p['body']
            items.append({
                'source':     'jsonplaceholder_api',
                'title':      p['title'],
                'author':     f"User_{p['userId']}",
                'tags':       ['api', 'post'],
                'tag_str':    'api, post',
                'word_count': len(body.split()),
                'body_len':   len(body),
                'user_id':    p['userId'],
                'post_id':    p['id'],
            })
        log.info(f"  ✅ API Posts: {len(items)} items")
        return items
    except Exception as e:
        log.warning(f"  API failed: {e}")
        return []


# ══════════════════════════════════════════════════════
# TRANSFORM
# ══════════════════════════════════════════════════════

def transform(all_items):
    log.info("Transform: processing and analyzing content...")

    df = pd.DataFrame(all_items)

    # Fill missing columns
    for col in ['price','rating','in_stock','body_len','user_id','post_id']:
        if col not in df.columns:
            df[col] = None

    # Clean
    df['title']  = df['title'].str.strip().str[:150]
    df['author'] = df['author'].fillna('Unknown')

    # Remove empty titles
    df = df[df['title'].str.len() > 3]

    # Content scoring
    df['content_score'] = (
        df['word_count'].clip(0, 50) / 50 * 40 +
        df['rating'].fillna(3) / 5 * 40 +
        df['tag_str'].str.split(',').str.len().clip(0,5) / 5 * 20
    ).round(1)

    # Scraped at
    df['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')

    # Trending words analysis
    all_words = []
    for title in df['title']:
        words = re.findall(r'\b[a-z]{4,}\b', title.lower())
        all_words.extend([w for w in words if w not in STOP_WORDS])
    word_freq = Counter(all_words)

    # Tag each item with trending score
    def trending_score(title):
        words  = re.findall(r'\b[a-z]{4,}\b', title.lower())
        scores = [word_freq.get(w, 0) for w in words if w not in STOP_WORDS]
        return sum(scores) / max(len(scores), 1)

    df['trending_score'] = df['title'].apply(trending_score).round(2)

    log.info(f"  ✅ {len(df)} items processed")
    log.info(f"  Top trending words: {word_freq.most_common(5)}")
    return df, word_freq


# ══════════════════════════════════════════════════════
# LOAD
# ══════════════════════════════════════════════════════

def load(df, word_freq):
    log.info("Load: saving to SQLite...")
    db = str(BASE / 'data' / 'news_aggregator.db')
    if os.path.exists(db): os.remove(db)
    conn = sqlite3.connect(db)

    # Main content table
    df_save = df.drop(columns=['tags'], errors='ignore')
    df_save.to_sql('content', conn, if_exists='replace', index=False)

    # Source stats
    source_stats = df.groupby('source').agg(
        count=('title','count'),
        avg_words=('word_count','mean'),
        avg_score=('content_score','mean')
    ).reset_index()
    source_stats.to_sql('source_stats', conn, if_exists='replace', index=False)

    # Trending words
    trending_df = pd.DataFrame(word_freq.most_common(50), columns=['word','frequency'])
    trending_df.to_sql('trending_words', conn, if_exists='replace', index=False)

    conn.commit()
    conn.close()
    log.info(f"  ✅ {len(df)} items saved")

    # Save word freq as JSON
    with open(BASE/'data'/'trending_words.json', 'w') as f:
        json.dump(dict(word_freq.most_common(30)), f, indent=2)


# ══════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════

def generate_dashboard(df, word_freq):
    log.info("Output: generating dashboard...")

    # Top content
    top_content = df.nlargest(10, 'content_score')[['title','source','content_score','trending_score']]
    top_rows = ''.join(
        f'<tr><td>{r.title[:60]}...</td><td><span class="badge">{r.source.split("_")[0]}</span></td>'
        f'<td>{r.content_score}</td><td>{r.trending_score}</td></tr>'
        for _, r in top_content.iterrows()
    )

    # Source breakdown
    src_stats = df.groupby('source').agg(count=('title','count'), avg_score=('content_score','mean')).reset_index()
    src_rows = ''.join(
        f'<tr><td>{r.source}</td><td>{r["count"]}</td><td>{r.avg_score:.1f}</td></tr>'
        for _, r in src_stats.iterrows()
    )

    # Top words
    word_rows = ''.join(
        f'<tr><td><b>{w}</b></td><td>{f}</td>'
        f'<td><div style="background:#2563eb;height:10px;width:{int(f/max(word_freq.values())*150)}px;border-radius:2px"></div></td></tr>'
        for w, f in word_freq.most_common(10)
    )

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Content Aggregator Dashboard</title>
<style>
  body{{font-family:Arial,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:20px}}
  .wrap{{max-width:1100px;margin:auto}}
  h1{{color:#60a5fa;text-align:center;margin-bottom:4px}}
  .sub{{text-align:center;color:#64748b;margin-bottom:24px;font-size:13px}}
  .kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px}}
  .kpi{{background:#1e293b;border-radius:10px;padding:18px;text-align:center;border:1px solid #334155}}
  .kpi-v{{font-size:26px;font-weight:bold;color:#60a5fa}}
  .kpi-l{{color:#64748b;font-size:12px;margin-top:4px}}
  .grid{{display:grid;grid-template-columns:1.5fr 1fr;gap:16px}}
  .card{{background:#1e293b;border-radius:10px;padding:20px;border:1px solid #334155;margin-bottom:16px}}
  h2{{color:#93c5fd;border-bottom:1px solid #334155;padding-bottom:8px;margin-top:0;font-size:15px}}
  table{{width:100%;border-collapse:collapse}}
  th{{background:#0f172a;color:#60a5fa;padding:9px;text-align:left;font-size:12px}}
  td{{padding:9px;border-bottom:1px solid #1e293b;font-size:12px}}
  tr:hover{{background:#0f172a}}
  .badge{{background:#2563eb;color:white;padding:2px 8px;border-radius:10px;font-size:11px}}
  .footer{{text-align:center;color:#475569;font-size:12px;margin-top:20px}}
</style></head><body>
<div class="wrap">
  <h1>📰 Content Aggregator Dashboard</h1>
  <p class="sub">3 sources · scraped {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
  <div class="kpis">
    <div class="kpi"><div class="kpi-v">{len(df)}</div><div class="kpi-l">Total Items</div></div>
    <div class="kpi"><div class="kpi-v">{df['source'].nunique()}</div><div class="kpi-l">Sources</div></div>
    <div class="kpi"><div class="kpi-v">{len(word_freq)}</div><div class="kpi-l">Unique Words</div></div>
    <div class="kpi"><div class="kpi-v">{df['content_score'].mean():.1f}</div><div class="kpi-l">Avg Score</div></div>
  </div>
  <div class="grid">
    <div>
      <div class="card"><h2>🏆 Top Content by Score</h2>
        <table><tr><th>Title</th><th>Source</th><th>Score</th><th>Trending</th></tr>{top_rows}</table>
      </div>
    </div>
    <div>
      <div class="card"><h2>📦 Source Breakdown</h2>
        <table><tr><th>Source</th><th>Count</th><th>Avg Score</th></tr>{src_rows}</table>
      </div>
      <div class="card"><h2>🔥 Trending Words</h2>
        <table><tr><th>Word</th><th>Freq</th><th>Trend</th></tr>{word_rows}</table>
      </div>
    </div>
  </div>
  <p class="footer">News Aggregator ETL — Project D</p>
</div></body></html>"""

    with open(BASE/'output'/'dashboard.html','w',encoding='utf-8') as f:
        f.write(html)
    log.info("  ✅ Dashboard → output/dashboard.html")


# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════

def run():
    log.info("="*60)
    log.info("🚀 Project D: Multi-Source News Aggregator")
    log.info("="*60)

    quotes = extract_quotes(max_pages=5)
    books  = extract_books(max_pages=3)
    posts  = extract_api_posts()

    all_items      = quotes + books + posts
    df, word_freq  = transform(all_items)
    load(df, word_freq)
    generate_dashboard(df, word_freq)

    log.info("\n✅ Done!")
    log.info(f"  DB        → data/news_aggregator.db")
    log.info(f"  Dashboard → output/dashboard.html")

if __name__ == '__main__':
    run()
