import requests
import pandas as pd
import sqlite3

url = "https://jsonplaceholder.typicode.com/users"
try:
    # محاولة سحب البيانات مع تجاهل أخطاء شهادة الـ SSL وإضافة مهلة زمنية (timeout)
    response = requests.get(url, verify=False, timeout=10)
    response.raise_for_status()
    raw_data = response.json()
    print("✅ تم سحب البيانات من الـ API بنجاح، عدد السجلات:", len(raw_data))
except Exception as e:
    print(f"⚠️ تعذر الاتصال بالـ API ({e})، جاري استخدام بيانات تجريبية بديلة...")
    # بيانات بديلة بنفس الهيكل عشان تكمل الـ Pipeline بدون توقف
    raw_data = [
        {"id": 1, "name": "Ahmed Ali", "email": "ahmed@example.com", "address": {"city": "Cairo"}, "company": {"name": "Tech Corp"}},
        {"id": 2, "name": "Sara Omar", "email": "sara@example.com", "address": {"city": "Alexandria"}, "company": {"name": "Data Systems"}},
        {"id": 3, "name": "Mohamed Hassan", "email": "mohamed@example.com", "address": {"city": "Giza"}, "company": {"name": "Cloud Ltd"}}
    ]
    
cleaned_records=[]
for user in raw_data:
    cleaned_records.append({
        "user_id":user["id"],
        "name": user["name"],
        "email":user["email"],
        "city":user["address"]["city"],
        "company_name":user["company"]["name"]
    })
    
df=pd.DataFrame(cleaned_records)
df["name"] = df["name"].str.strip()
df["email"] = df["email"].str.strip().str.lower()
df = df.dropna()
print("\n--- شكل البيانات بعد التنظيف ---")
print(df.head())

conn=sqlite3.connect("company_data.db")
cursor =conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS dim_users (
    user_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    city TEXT,
    company_name TEXT
)
''')
df.to_sql("dim_users",conn,if_exists="replace",index=False)
conn.commit()

print("\n✅ تم حفظ البيانات في قاعدة البيانات بنجاح!")
cursor.execute("SELECT user_id, name, city FROM dim_users LIMIT 3")
results = cursor.fetchall()
print("\n--- عينة من الداتا من داخل SQL ---")
for row in results:
    print(row)

# 4. Data Modeling: إضافة Fact Table للطلبات
cursor.execute('''
CREATE TABLE IF NOT EXISTS fact_orders (
    order_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    order_amount REAL,
    order_date TEXT,
    FOREIGN KEY (user_id) REFERENCES dim_users(user_id)
)
''')

# بيانات تجريبية لعمليات شراء قام بها المستخدمين
orders_data = [
    (101, 1, 250.0, "2026-08-01"),
    (102, 1, 150.5, "2026-08-05"),
    (103, 2, 500.0, "2026-08-10"),
    (104, 3, 75.0,  "2026-08-12"),
    (105, 2, 300.0, "2026-08-15")
]

cursor.executemany('''
INSERT OR REPLACE INTO fact_orders (order_id, user_id, order_amount, order_date)
VALUES (?, ?, ?, ?)
''', orders_data)
conn.commit()

print("\n✅ تم إنشاء وتعبئة Fact Table بنجاح!")

# 5. Advanced SQL Query: استعلام تحليلي يربط الجدولين ويحسب إجمالي مشتريات كل عميل
query = '''
SELECT 
    u.name,
    u.city,
    COUNT(o.order_id) AS total_orders,
    SUM(o.order_amount) AS total_spent
FROM dim_users u
JOIN fact_orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.name, u.city
ORDER BY total_spent DESC;
'''

cursor.execute(query)
report = cursor.fetchall()

print("\n--- تقرير المبيعات التحليلي (SQL JOIN + GROUP BY) ---")
for row in report:
    print(f"العميل: {row[0]} | المدينة: {row[1]} | عدد الطلبات: {row[2]} | إجمالي المدفوع: ${row[3]}")

conn.close()
