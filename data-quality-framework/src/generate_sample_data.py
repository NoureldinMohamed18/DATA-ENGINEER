"""
generate_sample_data.py
------------------------
يولّد ملف CSV "وسخ" فيه أنواع مشاكل شائعة (nulls, duplicates, outliers, wrong types)
عشان نستخدمه لاختبار وعرض إطار عمل فحص جودة البيانات (Data Quality Framework).

في الاستخدام الحقيقي: العميل هيجيبلك ملفه هو، مش هتحتاج الملف ده.
ده بس لأغراض العرض والاختبار.
"""

import csv
import random
from datetime import datetime, timedelta
import os

random.seed(11)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

rows = []
start = datetime(2024, 1, 1)

for i in range(1, 501):
    age = random.randint(18, 65)
    salary = round(random.uniform(3000, 25000), 2)
    email = f"user{i}@example.com"
    signup_date = (start + timedelta(days=random.randint(0, 500))).strftime("%Y-%m-%d")
    department = random.choice(["Sales", "Engineering", "Marketing", "HR", "Finance"])

    # حقن مشاكل جودة بيانات مقصودة
    if random.random() < 0.05:
        age = None  # قيمة فاضية
    if random.random() < 0.03:
        age = 150  # outlier غير منطقي
    if random.random() < 0.04:
        salary = -500  # قيمة سالبة غلط
    if random.random() < 0.03:
        email = f"user{i}_example.com"  # إيميل بصيغة غلط (من غير @)
    if random.random() < 0.02:
        department = ""  # فاضي

    rows.append({
        "employee_id": f"E{str(i).zfill(4)}",
        "age": age,
        "salary": salary,
        "email": email,
        "signup_date": signup_date,
        "department": department
    })

# صفوف مكررة بالكامل
rows.extend(random.sample(rows, 15))
random.shuffle(rows)

path = os.path.join(DATA_DIR, "sample_employees.csv")
with open(path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"[OK] تم توليد {len(rows)} صف في {path}")
print("المشاكل المزروعة: nulls في age, outliers (age=150), salary سالبة, إيميلات غلط, صفوف مكررة")
