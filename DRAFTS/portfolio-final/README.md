# Data Engineering Portfolio — المشاريع النهائية

3 مشاريع End-to-End كاملة، الخطوة الأخيرة قبل التقديم على فريلانس أو وظيفة Data Engineering.

كل مشروع مش تمرين منفصل — كل واحد بيدمج مهارات متعددة (SQL, Pandas, APIs, Web Scraping,
Data Warehousing, Dashboards) في سيناريو واقعي متكامل، بالظبط زي شغل حقيقي.

## المشاريع

### 1. [End-to-End Sales Data Pipeline](./project1-sales-pipeline)
ETL كامل: يسحب من 3 مصادر (CSV, API, Web Scraping) → ينضف → يبني Star Schema
في SQLite → يقدم البيانات عبر Flask REST API.

**أقوى نقطة فيه:** تصميم Data Warehouse حقيقي (fact + dimension tables) — ده اللي
بيفرقك عن حد بيعرف Pandas بس.

### 2. [Automated Market Intelligence Dashboard](./project2-market-intelligence)
مراقبة أسعار دورية تلقائية: Scraping → تخزين تاريخي → تحليل اتجاهات (Rolling Average)
→ كشف تنبيهات تلقائي → Dashboard تفاعلي بـ Streamlit.

**أقوى نقطة فيه:** الجانب البصري (Dashboard شغال بيتحرك) — أسهل حاجة تقنع بيها
حد بسرعة في فيديو قصير.

### 3. [Data Quality & Validation Framework](./project3-data-quality-framework)
أداة عامة تفحص جودة أي ملف بيانات (CSV/Excel) تلقائيًا وتطلع تقرير HTML جاهز.

**أقوى نقطة فيه:** قابل لإعادة الاستخدام مع أي عميل بدون تعديل كود — أسهل حاجة
تحولها لـ "خدمة" ثابتة على Mostaql.

## طريقة تشغيل أي مشروع

كل مشروع فيه `README.md` خاص بيه فيه تفاصيل التشغيل، لكن الشكل العام:

```bash
cd project-name
pip install -r requirements.txt   # لو موجود، أو حسب المكتوب في الـ README
python src/main.py
```

## إزاي تعرض المشاريع دي

| الموقف | المشروع الأنسب |
|---|---|
| عميل فريلانس عايز تنظيف بيانات | المشروع 3 (سريع تعرضه، نتيجته واضحة) |
| عميل فريلانس عايز تقارير مبيعات | المشروع 1 |
| شركة عايزة تشوف تصميم Data Warehouse | المشروع 1 |
| شركة عايزة تشوف Dashboard وautomation | المشروع 2 |
| فيديو تعريفي قصير على LinkedIn/Mostaql | المشروع 2 (الأكثر بصريًا) |

## الخطوة الجاية بعد المشاريع دي

بناءً على خطتك: بعد ما تظبط المشاريع دي في بورتفوليو (GitHub + README لكل واحد)،
الخطوة الجاية هي البدء الفعلي في التقديم على Mostaql/Khamsat بأسعار رمزية لجمع
أول تقييمات، مع الاستمرار في التعلم بالتوازي (Airflow, Docker, ثم Cloud).
