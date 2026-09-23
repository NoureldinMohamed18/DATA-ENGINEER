# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              مشروع المستوى المتوسط: نظام إدارة المخزون والمبيعات               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ المحتوى المغطى:                                                               ║
║ • Advanced Pandas (Merge, Concat, Pivot, Time Series, Apply, Transform)      ║
║ • Advanced SQL (JOINs, Subqueries, Views, Window Functions, CTEs)             ║
║ • NoSQL MongoDB (CRUD, Aggregation, Indexing)                                ║
║ • Python APIs (Flask REST API, JSON, HTTP Methods)                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING
from flask import Flask, jsonify, request

print("=" * 70)
print("          مشروع المستوى المتوسط: نظام إدارة المخزون والمبيعات")
print("=" * 70)

# ═══════════════════════════════════════════════════════════════════════════════
# الجزء الأول: Advanced Pandas - دمج وتحليل بيانات متعددة
# ═══════════════════════════════════════════════════════════════════════════════

# إنشاء DataFrame للمنتجات
products_df = pd.DataFrame({
    "product_id": ["P001", "P002", "P003", "P004", "P005"],
    "product_name": ["Laptop", "Mouse", "Keyboard", "Monitor", "Headset"],
    "category": ["Electronics", "Accessories", "Accessories", "Electronics", "Accessories"],
    "unit_price": [1200, 25, 45, 300, 80],
    "supplier_id": ["S01", "S02", "S02", "S01", "S03"]
})

# إنشاء DataFrame للموردين
suppliers_df = pd.DataFrame({
    "supplier_id": ["S01", "S02", "S03"],
    "supplier_name": ["TechCorp", "GadgetHub", "AudioMax"],
    "country": ["USA", "China", "Germany"]
})

# إنشاء DataFrame للمبيعات مع تواريخ (Time Series)
# pd.date_range() بتنشئ سلسلة تواريخ منتظمة
# periods=10: عدد التواريخ، freq="D": يومياً (Daily)
dates = pd.date_range(start="2024-01-01", periods=10, freq="D")
sales_df = pd.DataFrame({
    "sale_id": range(1, 11),
    "product_id": ["P001", "P002", "P001", "P003", "P004", "P005", "P002", "P001", "P004", "P003"],
    "quantity": [2, 10, 1, 5, 3, 4, 8, 2, 1, 6],
    "sale_date": dates,
    "region": ["North", "South", "North", "East", "West", "South", "North", "East", "West", "South"]
})

print("\n[1] بيانات المنتجات:")
print(products_df)

print("\n[2] بيانات الموردين:")
print(suppliers_df)

print("\n[3] بيانات المبيعات:")
print(sales_df)

# ─────────────────────────────────────────────────────────────────────────────
# [ADVANCED PANDAS] pd.merge(): دمج DataFrames (مشابه لـ SQL JOIN)
# how="inner": يعني يجيب الصفوف الموجودة في الجدولين (Inner Join)
# on="supplier_id": العمود المشترك اللي بندمج بناءً عليه
# ─────────────────────────────────────────────────────────────────────────────
products_with_suppliers = pd.merge(
    products_df, 
    suppliers_df, 
    on="supplier_id", 
    how="inner"
)
print("\n[4] دمج المنتجات مع الموردين (Inner Join):")
print(products_with_suppliers)

# ─────────────────────────────────────────────────────────────────────────────
# [ADVANCED PANDAS] دمج المبيعات مع المنتجات عشان نحسب الإيرادات
# how="left": Left Join عشان نحافظ على كل المبيعات
# ─────────────────────────────────────────────────────────────────────────────
sales_products = pd.merge(sales_df, products_df, on="product_id", how="left")
sales_products["revenue"] = sales_products["quantity"] * sales_products["unit_price"]
print("\n[5] المبيعات مع الإيرادات:")
print(sales_products[["sale_id", "product_name", "quantity", "unit_price", "revenue"]])

# ─────────────────────────────────────────────────────────────────────────────
# [ADVANCED PANDAS] Pivot Table: جدول محوري لتحليل المبيعات حسب المنطقة والفئة
# values="revenue": القيم اللي بنحللها
# index="region": الصفوف، columns="category": الأعمدة
# aggfunc="sum": دالة التجميع، fill_value=0: ملء الفارغ بصفر
# ─────────────────────────────────────────────────────────────────────────────
pivot_revenue = sales_products.pivot_table(
    values="revenue", 
    index="region", 
    columns="category", 
    aggfunc="sum",
    fill_value=0
)
print("\n[6] Pivot Table - الإيرادات حسب المنطقة والفئة:")
print(pivot_revenue)

# ─────────────────────────────────────────────────────────────────────────────
# [ADVANCED PANDAS] Time Series Analysis: تحليل المبيعات الزمني
# set_index("sale_date") بيخلي عمود التاريخ هو الفهرس (Index)
# resample("W"): إعادة التجميع أسبوعياً (Weekly)
# ─────────────────────────────────────────────────────────────────────────────
sales_ts = sales_products.set_index("sale_date")
daily_revenue = sales_ts["revenue"].resample("W").sum()
print("\n[7] الإيرادات الأسبوعية (Time Series):")
print(daily_revenue)

# ─────────────────────────────────────────────────────────────────────────────
# [ADVANCED PANDAS] apply() & transform()
# apply(): بتطبق دالة على كل عنصر في العمود
# transform(): بتطبق دالة وترجع نفس شكل البيانات الأصلي
# ─────────────────────────────────────────────────────────────────────────────

def price_category(price):
    if price > 500:
        return "Premium"
    elif price > 50:
        return "Standard"
    else:
        return "Budget"

products_df["price_category"] = products_df["unit_price"].apply(price_category)
print("\n[8] تصنيف المنتجات باستخدام apply():")
print(products_df[["product_name", "unit_price", "price_category"]])

# transform(): حساب نسبة كل مبيعة من إجمالي مبيعات المنتج
sales_products["pct_of_product_total"] = (
    sales_products.groupby("product_id")["quantity"]
    .transform(lambda x: x / x.sum() * 100)
)
print("\n[9] نسبة كل عملية بيع من إجمالي مبيعات المنتج (transform):")
print(sales_products[["product_id", "quantity", "pct_of_product_total"]].round(2))

# ─────────────────────────────────────────────────────────────────────────────
# [ADVANCED PANDAS] pd.concat(): دمج DataFrames عمودياً
# ignore_index=True: إعادة ترقيم الصفوف من جديد
# ─────────────────────────────────────────────────────────────────────────────
new_sales = pd.DataFrame({
    "sale_id": [11, 12],
    "product_id": ["P005", "P002"],
    "quantity": [3, 15],
    "sale_date": [pd.Timestamp("2024-01-15"), pd.Timestamp("2024-01-16")],
    "region": ["North", "East"]
})
all_sales = pd.concat([sales_df, new_sales], ignore_index=True)
print(f"\n[10] عدد الصفوف قبل concat: {len(sales_df)}، بعد: {len(all_sales)}")


# ═══════════════════════════════════════════════════════════════════════════════
# الجزء الثاني: Advanced SQL - استعلامات متقدمة
# ═══════════════════════════════════════════════════════════════════════════════

conn = sqlite3.connect("inventory_medium.db")
cursor = conn.cursor()

# إنشاء الجداول
cursor.executescript("""
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS sales;
    DROP TABLE IF EXISTS categories;
    
    CREATE TABLE categories (
        cat_id INTEGER PRIMARY KEY,
        cat_name TEXT NOT NULL
    );
    
    CREATE TABLE products (
        product_id TEXT PRIMARY KEY,
        product_name TEXT,
        category_id INTEGER,
        unit_price REAL,
        FOREIGN KEY (category_id) REFERENCES categories(cat_id)
    );
    
    CREATE TABLE sales (
        sale_id INTEGER PRIMARY KEY,
        product_id TEXT,
        quantity INTEGER,
        sale_date TEXT,
        region TEXT,
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
""")
conn.commit()

# إدخال البيانات
categories_data = [(1, "Electronics"), (2, "Accessories")]
cursor.executemany("INSERT INTO categories VALUES (?, ?)", categories_data)

products_data = [
    ("P001", "Laptop", 1, 1200),
    ("P002", "Mouse", 2, 25),
    ("P003", "Keyboard", 2, 45),
    ("P004", "Monitor", 1, 300),
    ("P005", "Headset", 2, 80)
]
cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products_data)

sales_data = [
    (1, "P001", 2, "2024-01-01", "North"),
    (2, "P002", 10, "2024-01-02", "South"),
    (3, "P001", 1, "2024-01-03", "North"),
    (4, "P003", 5, "2024-01-04", "East"),
    (5, "P004", 3, "2024-01-05", "West"),
    (6, "P005", 4, "2024-01-06", "South"),
    (7, "P002", 8, "2024-01-07", "North"),
    (8, "P001", 2, "2024-01-08", "East"),
    (9, "P004", 1, "2024-01-09", "West"),
    (10, "P003", 6, "2024-01-10", "South")
]
cursor.executemany("INSERT INTO sales VALUES (?, ?, ?, ?, ?)", sales_data)
conn.commit()

print("\n[11] تم إنشاء الجداول وإدخال البيانات في SQLite")

# [ADVANCED SQL] JOIN + Aggregation
query_join = """
    SELECT 
        c.cat_name AS Category,
        p.product_name,
        SUM(s.quantity * p.unit_price) AS Total_Revenue,
        SUM(s.quantity) AS Total_Quantity
    FROM sales s
    INNER JOIN products p ON s.product_id = p.product_id
    INNER JOIN categories c ON p.category_id = c.cat_id
    GROUP BY c.cat_name, p.product_name
    ORDER BY Total_Revenue DESC
"""
print("\n[12] JOIN + Aggregation:")
print(pd.read_sql(query_join, conn))

# [ADVANCED SQL] Subquery
query_sub = """
    SELECT product_name, unit_price
    FROM products
    WHERE unit_price > (
        SELECT AVG(unit_price) FROM products
    )
"""
print("\n[13] Subquery - منتجات فوق متوسط السعر:")
print(pd.read_sql(query_sub, conn))

# [ADVANCED SQL] CTE (Common Table Expression)
query_cte = """
    WITH ProductSales AS (
        SELECT 
            p.product_id,
            p.product_name,
            SUM(s.quantity) AS total_sold
        FROM products p
        LEFT JOIN sales s ON p.product_id = s.product_id
        GROUP BY p.product_id, p.product_name
    )
    SELECT 
        product_name,
        total_sold,
        CASE 
            WHEN total_sold >= 10 THEN 'High'
            WHEN total_sold >= 5 THEN 'Medium'
            ELSE 'Low'
        END AS sales_grade
    FROM ProductSales
    ORDER BY total_sold DESC
"""
print("\n[14] CTE - تصنيف المنتجات:")
print(pd.read_sql(query_cte, conn))

# [ADVANCED SQL] View
cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_monthly_sales AS
    SELECT 
        strftime('%Y-%m', sale_date) AS month,
        region,
        SUM(quantity) AS total_qty
    FROM sales
    GROUP BY strftime('%Y-%m', sale_date), region
""")
conn.commit()
print("\n[15] تم إنشاء View:")
print(pd.read_sql("SELECT * FROM v_monthly_sales", conn))

# [ADVANCED SQL] Window Functions
query_window = """
    SELECT 
        product_name,
        unit_price,
        ROW_NUMBER() OVER (ORDER BY unit_price DESC) AS price_rank,
        RANK() OVER (ORDER BY unit_price DESC) AS price_dense_rank
    FROM products
"""
print("\n[16] Window Functions:")
print(pd.read_sql(query_window, conn))

conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# الجزء الثالث: MongoDB - NoSQL Database
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[17] MongoDB Operations:")

try:
    client = MongoClient("localhost", 27017, serverSelectionTimeoutMS=2000)
    client.admin.command('ping')
    
    db = client["inventory_db"]
    products_col = db["products_nosql"]
    
    # مسح البيانات القديمة
    products_col.delete_many({})
    
    nosql_products = [
        {
            "product_id": "P001",
            "product_name": "Laptop",
            "specs": {"ram": "16GB", "cpu": "i7", "storage": "512GB SSD"},
            "tags": ["electronics", "computing", "premium"],
            "price": 1200,
            "in_stock": True
        },
        {
            "product_id": "P002",
            "product_name": "Mouse",
            "specs": {"type": "wireless", "dpi": 16000},
            "tags": ["accessories", "wireless"],
            "price": 25,
            "in_stock": True
        },
        {
            "product_id": "P003",
            "product_name": "Keyboard",
            "specs": {"type": "mechanical", "switches": "Cherry MX"},
            "tags": ["accessories", "gaming"],
            "price": 45,
            "in_stock": False
        }
    ]
    products_col.insert_many(nosql_products)
    print("    تم إدخال 3 منتجات في MongoDB")
    
    # find() مع شرط: المنتجات المتوفرة وسعرها > 30
    available = products_col.find({"in_stock": True, "price": {"$gt": 30}})
    print("\n    منتجات متوفرة وسعرها > 30:")
    for doc in available:
        print(f"      - {doc['product_name']}: ${doc['price']}")
    
    # Aggregation Pipeline: تجميع وتحليل
    pipeline = [
        {"$match": {"in_stock": True}},
        {"$group": {"_id": "$specs.type", "count": {"$sum": 1}, "avg_price": {"$avg": "$price"}}},
        {"$sort": {"avg_price": -1}}
    ]
    agg_result = list(products_col.aggregate(pipeline))
    print("\n    Aggregation - متوسط السعر حسب النوع:")
    for r in agg_result:
        print(f"      {r['_id']}: count={r['count']}, avg=${r['avg_price']:.2f}")
    
    # Indexing: إنشاء فهرس لتحسين الأداء
    products_col.create_index([("price", ASCENDING)])
    print("\n    تم إنشاء Index على حقل price")
    
    # update_one(): تحديث مستند واحد
    products_col.update_one(
        {"product_id": "P003"},
        {"$set": {"in_stock": True, "price": 50}}
    )
    print("    تم تحديث منتج P003")
    
    client.close()
    
except Exception as e:
    print(f"    [تنبيه] MongoDB غير متاح: {e}")
    print("    لتشغيل المشروع: شغل MongoDB locally على port 27017")


# ═══════════════════════════════════════════════════════════════════════════════
# الجزء الرابع: Flask REST API - بناء واجهة برمجية
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[18] Flask REST API - بناء API للمنتجات:")

app = Flask(__name__)  # إنشاء تطبيق Flask

# بيانات وهمية في الذاكرة (In-Memory Database)
api_products = [
    {"id": 1, "name": "Laptop", "price": 1200, "stock": 15},
    {"id": 2, "name": "Mouse", "price": 25, "stock": 100},
    {"id": 3, "name": "Keyboard", "price": 45, "stock": 50}
]

# GET /products: جلب كل المنتجات
@app.route("/products", methods=["GET"])
def get_products():
    return jsonify({
        "status": "success",
        "count": len(api_products),
        "data": api_products
    })

# GET /products/<id>: جلب منتج محدد
@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = next((p for p in api_products if p["id"] == product_id), None)
    if product:
        return jsonify({"status": "success", "data": product})
    return jsonify({"status": "error", "message": "Product not found"}), 404

# POST /products: إضافة منتج جديد
@app.route("/products", methods=["POST"])
def create_product():
    data = request.get_json()
    new_product = {
        "id": len(api_products) + 1,
        "name": data.get("name"),
        "price": data.get("price"),
        "stock": data.get("stock", 0)
    }
    api_products.append(new_product)
    return jsonify({"status": "success", "data": new_product}), 201

# PUT /products/<id>: تحديث منتج كامل
@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json()
    product = next((p for p in api_products if p["id"] == product_id), None)
    if product:
        product["name"] = data.get("name", product["name"])
        product["price"] = data.get("price", product["price"])
        product["stock"] = data.get("stock", product["stock"])
        return jsonify({"status": "success", "data": product})
    return jsonify({"status": "error", "message": "Product not found"}), 404

# DELETE /products/<id>: حذف منتج
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    global api_products
    api_products = [p for p in api_products if p["id"] != product_id]
    return jsonify({"status": "success", "message": "Product deleted"})

print("""
    ✅ API Endpoints جاهزة:
       • GET    /products         -> جلب كل المنتجات
       • GET    /products/<id>    -> جلب منتج محدد
       • POST   /products         -> إضافة منتج (Body: JSON)
       • PUT    /products/<id>    -> تحديث منتج (Body: JSON)
       • DELETE /products/<id>    -> حذف منتج
    
    لتشغيل السيرفر:
       app.run(debug=True, port=5000)
    
    لتجربة API:
       curl http://localhost:5000/products
       curl -X POST -H "Content-Type: application/json" -d '{\"name\":\"Monitor\",\"price\":300,\"stock\":10}' http://localhost:5000/products
""")

print("\n" + "=" * 70)
print("          ✓ تم إنهاء مشروع المستوى المتوسط")
print("=" * 70)