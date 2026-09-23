"""
Web Scraper Module
==================
Scrapes product data from a sample e-commerce website.
For demo purposes, this scrapes from httpbin.org or uses
mock data if no internet connection is available.

In production, replace with real targets like:
- Amazon (requires headers, handling pagination)
- eBay (API preferred)
- Noon.com, Jumia.eg, etc.
"""

import requests
import json
import os
import random
from bs4 import BeautifulSoup
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def scrape_products():
    """
    Generate mock product data for demonstration.
    In a real scenario, this would scrape an actual website.
    """
    categories = ['Electronics', 'Clothing', 'Home', 'Books', 'Sports']
    products = []

    sample_products = [
        ("Wireless Earbuds", "Electronics", 49.99),
        ("Smart Watch", "Electronics", 129.99),
        ("Cotton T-Shirt", "Clothing", 19.99),
        ("Running Shoes", "Sports", 79.99),
        ("Coffee Maker", "Home", 59.99),
        ("Python Crash Course", "Books", 29.99),
        ("Yoga Mat", "Sports", 24.99),
        ("LED Desk Lamp", "Home", 34.99),
        ("Bluetooth Speaker", "Electronics", 39.99),
        ("Winter Jacket", "Clothing", 89.99),
        ("Mechanical Keyboard", "Electronics", 74.99),
        ("Cookware Set", "Home", 99.99),
        ("Data Science Handbook", "Books", 44.99),
        ("Dumbbells Set", "Sports", 54.99),
        ("Sneakers", "Clothing", 69.99),
    ]

    for idx, (name, category, price) in enumerate(sample_products, 1):
        products.append({
            "id": idx,
            "name": name,
            "category": category,
            "price": price,
            "rating": round(random.uniform(3.0, 5.0), 1),
            "in_stock": random.choice([True, True, True, False]),
            "source": "mock_scraper"
        })

    return products

def scrape_web():
    """
    Attempt to scrape from a demo HTML page.
    Falls back to mock data if connection fails.
    """
    try:
        url="https://httpbin.org/html"
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response=requests.get(url,headers=headers,timeout=10)
        response.raise_for_status()
        soup=BeautifulSoup(response.text,'html.parser')
         # Extract title as demo
        title = soup.find('title')
        print(f"[SCRAPER] Successfully connected. Page title: {title.text if title else 'N/A'}")

        # For a real scraper, you would parse actual product elements:
        # products = []
        # for item in soup.find_all('div', class_='product'):
        #     name = item.find('h2').text
        #     price = item.find('span', class_='price').text
        #     products.append({...})

        # Return mock data for this demo
        print("[SCRAPER] Using mock data for demonstration...")
        return scrape_products()

    except Exception as e:
        print(f"[SCRAPER] Connection failed: {e}")
        print("[SCRAPER] Falling back to mock data...")
        return scrape_products()
    
def save_products(products, filename="products.json"):
    """Save scraped products to JSON file."""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"[SCRAPER] Saved {len(products)} products to {filepath}")
    return filepath

def load_products(filename="products.json"):
    """Load products from JSON file."""
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def main():
    print("=" * 50)
    print("WEB SCRAPER")
    print("=" * 50)
    products = scrape_web()
    save_products(products)
    print(f"\n[DONE] Scraped {len(products)} products successfully!")
    return products
if __name__ == "__main__":
    main()