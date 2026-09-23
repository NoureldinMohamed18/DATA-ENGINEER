# End-to-End Sales Data Pipeline

مشروع Data Engineering متكامل: بيسحب بيانات من 3 مصادر مختلفة (CSV, API, Web Scraping)،
بينضفها، بيبني منها Data Warehouse بتصميم Star Schema، وبيقدمها عن طريق REST API.

## المشكلة اللي المشروع بيحلها

أي شركة عندها بيانات مبيعات متفرقة في أماكن مختلفة: نظام داخلي (CSV export)، بيانات منتجات
من API خارجي، وأسعار المنافسين اللي محتاجة scraping. المشروع ده بيوحّد كل المصادر دي في
مكان واحد منظم وجاهز للتحليل والتقارير.

## البنية المعمارية (Architecture)

```
[CSV File]  ─┐
[API/JSON]  ─┼──▶  EXTRACT  ──▶  TRANSFORM  ──▶  LOAD (Star Schema)  ──▶  Flask API
[Web Scrape]─┘
```

### مراحل الـ Pipeline

1. **Extract** (`extract.py`): سحب البيانات الخام من الـ 3 مصادر بدون أي تعديل
2. **Transform** (`transform.py`): تنظيف، توحيد التواريخ، فصل السجلات الغلط، دمج المصادر
3. **Load** (`load.py`): بناء Star Schema (fact table + 4 dimension tables) في SQLite
4. **Serve** (`api.py`): Flask API بيقدم البيانات لأي تطبيق أو Dashboard

## هيكل قاعدة البيانات (Star Schema)

```
                dim_date
                    │
dim_product ── fact_sales ── dim_customer
                    │
                dim_region
```

- **fact_sales**: الأرقام (quantity, total_amount, profit_margin, competitor comparisons)
- **dim_product / dim_customer / dim_region / dim_date**: السياق الوصفي لكل عملية بيع

## طريقة معالجة البيانات الغلط

بدل ما نمسح أي سجل فيه مشكلة (quantity فاضية، سعر سالب، عميل غير معروف، تاريخ غير صالح)،
بنفصله في ملف `logs/rejected_records.csv` مع عمود `rejection_reason` يوضح السبب بالظبط.
كده تقدر تراجع البيانات دي لاحقًا بدل ما تضيع.

## طريقة التشغيل

```bash
# 1. تثبيت المكتبات
pip install pandas beautifulsoup4 flask

# 2. توليد بيانات تجريبية (خطوة تحضيرية، مرة واحدة فقط)
python src/generate_raw_data.py

# 3. تشغيل الـ Pipeline بالكامل
python src/main.py

# 4. تشغيل الـ API
python src/api.py
```

## الـ Endpoints المتاحة

| Endpoint | الوصف |
|---|---|
| `GET /api/sales/summary` | إجمالي المبيعات والأرباح |
| `GET /api/sales/by-category` | المبيعات مجمعة حسب فئة المنتج |
| `GET /api/sales/by-region` | المبيعات مجمعة حسب المنطقة |
| `GET /api/sales/monthly` | اتجاه المبيعات شهريًا |
| `GET /api/products/top?limit=5` | أعلى المنتجات مبيعًا |
| `GET /api/products/price-comparison` | مقارنة أسعارنا بأسعار المنافس |

## التقنيات المستخدمة

Python, Pandas, SQLite, SQL (Star Schema Design), BeautifulSoup, Flask, REST API, Logging

## كيف تعرضه للعميل / الشركة

لو بتعرضه لعميل فريلانس: ركّز على إن ده حل مشكلة حقيقية (بيانات متفرقة → تقارير جاهزة).
لو بتعرضه لشركة: ركّز على التصميم (Star Schema، فصل المسؤوليات بين الملفات، error handling،
logging احترافي) — ده اللي بيبين إنك فاهم مش بس بتكتب كود شغال.
