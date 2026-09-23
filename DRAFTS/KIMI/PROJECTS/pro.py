
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    مشروع المستوى السهل: محلل بيانات المبيعات              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ المحتوى المغطى:                                                             ║
║ • Pandas Basics (DataFrames, Filtering, GroupBy, Missing Data)               ║
║ • SQL Basics (CREATE, INSERT, SELECT, Aggregation)                           ║
║ • Web Scraping Basics (BeautifulSoup - جمع بيانات من موقع تجريبي)          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import pandas as pd
import numpy as np
import sqlite3  
import requests
from bs4 import BeautifulSoup
# ─────────────────────────────────────────────────────────────────────────────
# الجزء الأول: إنشاء بيانات تجريبية للمبيعات (Pandas Basics)
# ─────────────────────────────────────────────────────────────────────────────
# إنشاء قاموس (Dictionary) يحتوي على بيانات الموظفين والمبيعات
# كل مفتاح في القاموس بيمثل اسم العمود، والقيمة هي قائمة بالبيانات
data = {
    "Employee_ID": [101, 102, 103, 104, 105, 106, 107],
    "Name": ["Ahmed", "Sara", "Mohamed", "Fatima", "Omar", "Laila", "Khaled"],
    "Department": ["IT", "Sales", "IT", "HR", "Sales", "HR", "IT"],
    "Salary": [5000, 4500, 6000, 3800, 4700, 3900, np.nan],  # np.nan = قيمة رقمية غير موجودة (Missing Data)
    "Join_Date": ["2020-01-15", "2019-06-20", "2021-03-10", "2018-11-05", "2022-07-01", "2020-09-12", "2023-01-10"],
    "Sales_Q1": [120, 150, 200, 90, 180, 95, 210]  # مبيعات الربع الأول
}
df=pd.DataFrame(data)
print("=" * 60)
print("[1] بيانات الموظفين الأصلية:")
print(df)
print("=" * 60)
print("\n[2] أول 5 صفوف من البيانات (head):")
print(df.head())
print("=" * 60)
print("\n[3] معلومات عن البيانات (info):")
print(df.info())
print("=" * 60)
print("\n[4] معلومات عن العمودين (describe):")
print(df.describe())
print("=" * 60)
print("\n[5] الكشف عن القيم الناقصة (isnull):")
print(df.isnull())
print("=" * 60)
mean_salary=df["Salary"].mean()
df['Salary']=df["Salary"].fillna(mean_salary)
print("=" * 60)
print("[6] البيانات بعد تعبئة القيم الناقصة:")
print(df[['Name', 'Salary']])
# ─────────────────────────────────────────────────────────────────────────────
# [PANDAS] إضافة عمود جديد: حساب الراتب بعد زيادة 10%
# العمليات الحسابية في Pandas متجهية (Vectorized): بتتطبق على كل الصفوف مرة واحدة بكفاءة
# ─────────────────────────────────────────────────────────────────────────────
df['Salary_after_increase']=df['Salary']*1.10
print("\n[7] البيانات بعد زيادة الراتب بنسبة 10%:")
print(df[['Name', 'Salary', 'Salary_after_increase']])
# ─────────────────────────────────────────────────────────────────────────────
# [PANDAS] فلترة البيانات: اختيار موظفي قسم IT اللي مبيعاتهم أكبر من 150
# الشرط بين قوسين مربعين [] وبنستخدم & للربط بين شرطين
# ─────────────────────────────────────────────────────────────────────────────
it_employees=df[(df["Department"]=="IT") & (df["Sales_Q1"]>150)]
print("\n[8] موظفي قسم IT اللي مبيعاتهم أكبر من 150:")
print(it_employees)
# ─────────────────────────────────────────────────────────────────────────────
# [PANDAS] جمع البيانات: جمع المبيعات لكل قسم
# المعامل groupby() هيكون فيها العمود اللي بتحطها هيكون فيها القيم اللي بتحطها هيكون فيها العمليات اللي بتحطها هيكون فيها النتيجة
# ─────────────────────────────────────────────────────────────────────────────
sales_by_department=df.groupby("Department").agg({
    "Salary": "mean",
    "Sales_Q1": "sum",
    'Emplyees_ID': "count"
}).rename(columns={'Emplyees_ID': "Number of Employees"})
print("\n[9] مبيعات كل قسم:")
print(sales_by_department)

# ─────────────────────────────────────────────────────────────────────────────
# الجزء الثاني: تخزين البيانات في قاعدة بيانات SQLite (SQL Basics)
# ─────────────────────────────────────────────────────────────────────────────
conn=sqlite3.connect("sales_data.db")
cursor=conn.cursor()
# [SQL - DDL] إنشاء جدول الموظفين
# CREATE TABLE بيعرف الجدول ونوع البيانات لكل عمود
# PRIMARY KEY: مفتاح رئيسي فريد لكل صف
# REAL: نوع بيانات عشري
# TEXT: نوع بيانات نصي
# DATE: نوع بيانات التاريخ
cursor.execute("""
CREATE TABLE IF NOT EXISTS employees (
    Employee_ID INTEGER PRIMARY KEY,
    Name TEXT NOT NULL,
    Department TEXT NOT NULL,
    Salary REAL NOT NULL,
    Join_Date DATE NOT NULL,
    Sales_Q1 INTEGER NOT NULL
)
""")
conn.commit()
# [SQL - DML] إدخال البيانات من DataFrame إلى جدول SQL
# to_sql() بتاخد DataFrame وتحوله لصفوف في جدول SQL
# if_exists="replace" لو الجدول موجود هيمسحه ويعيد إنشاؤه
# index=False عشان ما يحفظش عمود الاندكس من pandas كعمود منفصل
df.to_sql("employees", conn, if_exists="replace", index=False)
print("[11] تم إدخال البيانات في جدول employees")
# [SQL - DQL] استعلام: متوسط المبيعات لكل قسم
# SELECT: اختيار الأعمدة
# AVG(): دالة تجميعية لحساب المتوسط
# GROUP BY: تجميع النتائج حسب القسم
query="""
SELECT Department, AVG(Sales_Q1) AS Average_Sales,
sum(Salary) AS Total_Salary,
count(*) AS Number_of_Employees
FROM employees
GROUP BY Department
ORDER BY Total_Salary DESC
"""
result=pd.read_sql_query(query, conn)
print("\n[12] متوسط المبيعات لكل قسم:")
print(result)
cursor.execute("update employees set Salary=Salary*1.10 where Name='Ahmed'")
conn.commit()
# [SQL - DQL] فلترة بسيطة: موظفو Sales اللي راتبهم أكبر من 4000
query2 = "SELECT * FROM employees WHERE Department = 'Sales' AND Salary > 4000"
sales_high = pd.read_sql(query2, conn)
print("\n[14] موظفو Sales براتب > 4000:")
print(sales_high)
print("\n[15] Web Scraping - جلب بيانات من موقع تجريبي...")
try:
    url="https://jsonplaceholder.typicode.com/users"
    response=requests.get(url)
    response.raise_for_status()
    if response.status_code == 200:
        user_data=response.json()

        scraped_data=[]
        for user in user_data[:3]:
            scraped_data.append({
                "ID":user["id"],
                "Name":user["username"],
                "Email":user["email"],
                "city":user["address"]["city"],
            })
        df_scraped=pd.DataFrame(scraped_data)
        print("\nبيانات مستخدمين من API (Scraping):")
        print(df_scraped)

        df_scraped.to_csv("scraped_data.csv", index=False,encoding="utf-8-sig")
        print("\n[16] تم حفظ بيانات مستخدمين من API (Scraping) في scraped_data.csv")
    else:
        print(f"Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

conn.close()
print("\n[17] تم إغلاق الاتصال بقاعدة البيانات")