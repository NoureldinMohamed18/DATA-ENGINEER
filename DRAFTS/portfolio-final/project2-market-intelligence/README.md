# Automated Market Intelligence Dashboard

نظام آلي بيراقب أسعار السوق بشكل دوري، بيخزن تاريخ كامل للأسعار، بيكتشف التغيرات الكبيرة
تلقائيًا، وبيعرض كل ده في Dashboard تفاعلي.

## المشكلة اللي المشروع بيحلها

أي حد عايز يراقب أسعار منافسين أو منتجات في السوق محتاج نظام بيسحب البيانات دوريًا،
يحتفظ بالتاريخ (مش بس آخر قراءة)، ويقدر يكتشف التغيرات المهمة (زيادة/نقصان كبير) من غير
ما يحتاج يراجع البيانات يدويًا كل مرة.

## البنية المعمارية

```
[Market Page/HTML] → Scraper (BeautifulSoup) → SQLite (price_history) → Analysis (Pandas)
                                                                              │
                                                        ┌─────────────────────┴────────────────────┐
                                                        ▼                                            ▼
                                                 Alert Notifier                              Streamlit Dashboard
                                                 (logs/alerts.log)                           (رسوم بيانية تفاعلية)
```

## المكونات

| الملف | الوظيفة |
|---|---|
| `mock_market_site.py` | يحاكي موقع سوق حقيقي بأسعار متغيرة (بديل مؤقت عن موقع حقيقي) |
| `scraper.py` | يستخرج البيانات بـ BeautifulSoup ويخزنها كـ snapshot في SQL |
| `backfill_history.py` | يولّد 30 يوم بيانات تاريخية واقعية لأول تشغيل |
| `analysis.py` | يحسب Rolling Average و % Change ويكتشف التنبيهات (Pandas) |
| `alert_notifier.py` | يسجل التنبيهات في ملف log (بديل بسيط لإيميل/Slack حقيقي) |
| `dashboard.py` | Dashboard تفاعلي بـ Streamlit + Plotly |
| `scheduler.py` | يشغل دورة السحب والتحليل تلقائيًا كل فترة زمنية |
| `main.py` | نقطة تشغيل واحدة لكل حاجة |

## منطق كشف التنبيهات

أي تغيير سعر (زيادة أو نقصان) أكبر من **10%** بين قراءتين متتاليتين لنفس المنتج
بيتسجل كتنبيه تلقائيًا. الـ threshold ده قابل للتعديل من `analysis.py`
(متغير `ALERT_THRESHOLD_PCT`).

## طريقة التشغيل

```bash
# 1. تثبيت المكتبات
pip install pandas beautifulsoup4 streamlit plotly schedule

# 2. تشغيل أول مرة (بيولّد بيانات تاريخية + يحلل)
python src/main.py

# 3. فتح الداشبورد التفاعلي
streamlit run src/dashboard.py

# 4. (اختياري) تشغيل المراقبة التلقائية المستمرة
python src/scheduler.py
```

## التقنيات المستخدمة

Python, Pandas (rolling/pct_change), SQLite, BeautifulSoup, Streamlit, Plotly,
`schedule` library, Logging

## كيف تعرضه

المشروع ده مثالي تعرضه كـ **فيديو قصير أو GIF للداشبورد شغال** بدل ما تشرحه بالكلام بس —
شركة أو عميل هيقتنع أسرع لما يشوف الرسم البياني بيتحرك ويوريه التنبيهات مباشرة.
