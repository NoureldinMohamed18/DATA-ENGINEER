"""
extract.py
-----------
Project 3 - Extract step.

Scrapes book listings from https://books.toscrape.com — a website built
specifically for practicing web scraping (its robots.txt allows full
crawling, so this is a legal, ethical target to learn on).

For each book on a listing page, we extract:
    - title
    - price (as raw text, e.g. "£51.77")
    - star rating (as text class, e.g. "Three")
    - availability text
    - product page URL

Usage:
    python extract.py               # scrapes live from the internet
    python extract.py --offline     # parses the local sample_page.html fixture instead
                                     # (useful for testing without network access)
"""

import argparse
import time
import requests
import json
from bs4 import BeautifulSoup
from pathlib import Path

BASE_URL = "https://books.toscrape.com/"
CATALOGUE_URL = BASE_URL + "catalogue/page-{}.html"
RAW_OUTPUT = Path("data/raw_books.json")

def parse_listing_page(html:str)->list[dict]:
    """Parse a single catalogue page's HTML and return a list of book dicts."""
    soup=BeautifulSoup(html,'html.parser')
    books=[]
    for article in soup.select("article.product_pod"):
        title=article.h3.a['title']
        price_text=article.select_one("p.price_color").get_text(strip=True)
        availability=article.select_one('p.instock.avalilability').get_text(strip=True)
        rating_classes = article.select_one("p.star-rating")["class"]
        rating_word = [c for c in rating_classes if c != "star-rating"][0]
        relative_url = article.h3.a["href"]
        product_url = BASE_URL + "catalogue/" + relative_url.replace("../../../", "")
        
        books.append({
            'title':title,
            "price_text":price_text,
             "rating_word": rating_word,
            "availability_text": availability,
            "product_url": product_url,
        })
    return books
    
def scrape_live(num_pages:int =5)->list[dict]:
    """Scrape `num_pages` catalogue pages from the live site, being polite about rate limits."""
    all_books=[]
    session=requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (educational scraping project)"})
    
    for page in range(1, num_pages + 1):
        url = CATALOGUE_URL.format(page)
        print(f"[EXTRACT] Fetching {url}")
        response = session.get(url, timeout=10)

        if response.status_code != 200:
            print(f"[EXTRACT] Page {page} returned {response.status_code}, stopping.")
            break

        page_books = parse_listing_page(response.text)
        all_books.extend(page_books)
        print(f"[EXTRACT]   -> {len(page_books)} books found on page {page}")

        time.sleep(1) 
        
    return all_books

def scrape_offline() -> list[dict]:
    """Parse the local sample_page.html fixture — no network required."""
    html = Path("sample_page.html").read_text(encoding="utf-8")
    books = parse_listing_page(html)
    print(f"[EXTRACT] Parsed {len(books)} books from local sample_page.html")
    return books

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Parse local sample_page.html instead of scraping live")
    parser.add_argument("--pages", type=int, default=5, help="Number of catalogue pages to scrape (live mode only)")
    args=parser.parse_args()
    
    if args.offline :
        books=scrape_offline
    else:
        books=scrape_live
        
    Path("data").mkdir(exist_ok=True)
    RAW_OUTPUT.write_text(json.dumps(books, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[EXTRACT] Saved {len(books)} raw records -> {RAW_OUTPUT}")
    
if __name__=="__main__":
    main()
    