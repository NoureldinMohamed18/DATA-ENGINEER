import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3

html_doc = """
<html><body>
<div class="product" data-category="Laptops"><h2 class="title">Dell XPS 13</h2><span
class="price">$1200.50</span><span class="rating">4.8</span></div>
<div class="product" data-category="Laptops"><h2 class="title">MacBook Air M2</h2><span
class="price">$1099.00</span><span class="rating">4.9</span></div>
<div class="product" data-category="Phones"><h2 class="title">iPhone 15 Pro</h2><span
class="price">$999.00</span><span class="rating">4.7</span></div>
<div class="product" data-category="Phones"><h2 class="title">Samsung S24 Ultra</h2><span
class="price">$1199.99</span><span class="rating">4.6</span></div>
<div class="product" data-category="Accessories"><h2 class="title">Sony WH-1000XM5</h2><span
class="price">None</span><span class="rating">4.5</span></div>
</body></html>
"""

soup=BeautifulSoup(html_doc,'html.praser')
items=[]
for div in soup.find_all('div',class_='product'):
    name=div.finf('h2',class_='tittle').text
    p_raw=div.find('span',class_='price').text.replace('$','')
    items.append({
        'name':name,
        'category':div.get('data-category'),
    'price':float(p_raw) if p_raw !='None' else None,
    'rating':float(div.find('span',class_='rating').text)    
    })
    
df=pd.DataFrame(items)
df['price']=df['price'].fillna(df['price'].mean())

conn=sqlite3.connect("e-commerce.db")
cursor=conn.cursor()
cursor.executescript("""
CREATE TABLE IF NOT EXISTS categories (
category_id INTEGER PRIMARY KEY AUTOINCREMENT,
category_name TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS products (
product_id INTEGER PRIMARY KEY AUTOINCREMENT,
product_name TEXT NOT NULL,
category_id INTEGER,
price REAL CHECK(price >= 0),
rating REAL,
FOREIGN KEY(category_id) REFERENCES categories(category_id)
);
CREATE TABLE IF NOT EXISTS sales (
sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
product_id INTEGER,
quantity INTEGER CHECK(quantity > 0),
sale_date DATE,
FOREIGN KEY(product_id) REFERENCES products(product_id)
);
""")

for cat in df['category'].unique():
    cursor.execute("INSERT OR IGNORE INTO categories (category_name) VALUES (?)", (cat,))
conn.commit()
cat_map = dict(cursor.execute("SELECT category_name, category_id FROM categories").fetchall())
for _, row in df.iterrows():
    cursor.execute("INSERT INTO products (product_name, category_id, price, rating) VALUES (?, ?,?, ?)",
(row['name'], cat_map[row['category']], row['price'], row['rating']))
conn.commit()
sales_data = [(1, 3, '2026-08-01'), (2, 5, '2026-08-02'), (3, 2, '2026-08-03'), (4, 4, '2026-08-04'), (1, 2, '2026-08-05')]
cursor.executemany("INSERT INTO sales (product_id, quantity, sale_date) VALUES (?, ?, ?)",sales_data)
conn.commit()

cursor.executescript("""
CREATE VIEW IF NOT EXISTS vw_product_revenue_rankings AS
WITH SalesSummary AS (
SELECT
p.product_id, p.product_name, c.category_name, p.price,
COALESCE(SUM(s.quantity), 0) AS total_units_sold,
COALESCE(SUM(s.quantity * p.price), 0) AS total_revenue
FROM products p
JOIN categories c ON p.category_id = c.category_id
LEFT JOIN sales s ON p.product_id = s.product_id
GROUP BY p.product_id, p.product_name, c.category_name, p.price
)
SELECT
product_name, category_name, total_units_sold, ROUND(total_revenue, 2) AS total_revenue,
ROUND(AVG(total_revenue) OVER (PARTITION BY category_name), 2) AS avg_category_revenue,
RANK() OVER (ORDER BY total_revenue DESC) AS overall_revenue_rank,
DENSE_RANK() OVER (PARTITION BY category_name ORDER BY total_revenue DESC) AS category_rank
FROM SalesSummary;
""")

print(":تقرير اإليرادات والتصنيف")
print(pd.read_sql_query("SELECT * FROM vw_product_revenue_rankings", conn))
conn.close()

