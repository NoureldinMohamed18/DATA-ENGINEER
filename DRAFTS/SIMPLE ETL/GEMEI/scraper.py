import requests
from bs4 import BeautifulSoup
import pandas as pd

url ="https://books.toscrape.com/"
header={"User-Agent": "Mozilla/5.0"}

try:
    response=requests.get(url,headers=headers,timeout=10)
    response.raise_for_status()
    soup=BeautifulSoup(response.text,"html.parser")
    
    book_data=[]
    articles = soup.find_all("article",class_="product_pod")
    
    for article in articles[:5]:
        title = article.h3.a["title"]
        price = article.find("p", class_="price_color").text.replace("£", "").strip()
        availability = article.find("p", class_="instock availability").text.strip()
        
        book_data.append({
            "title":title,
            "price_gdp":float(price),
            "in_stock":True if "in stock" in availability else False
        })
    print("WEB SCRAPING")
except Exception as e:
    print(f"⚠️ تعذر الاتصال بالموقع ({e})، جاري استخدام بيانات تجريبية بديلة...")
    books_data = [
        {"title": "A Light in the Attic", "price_gbp": 51.77, "in_stock": True},
        {"title": "Tipping the Velvet", "price_gbp": 53.74, "in_stock": True},
        {"title": "Soumission", "price_gbp": 50.10, "in_stock": True}
    ]
    
    
df_books = pd.DataFrame(books_data)
df_books["price_usd"] = df_books["price_gbp"] * 1.3
print("\n--- جدول البيانات بعد المعالجة (Pandas) ---")
print(df_books)
json_documents = df_books.to_dict(orient="records")
print("\n--- شكل الـ Documents الجاهزة للـ NoSQL / MongoDB ---")
for doc in json_documents:
    print(doc)