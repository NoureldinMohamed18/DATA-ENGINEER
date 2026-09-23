"""
dashboard.py
------------
Dashboard تفاعلي بـ Streamlit لعرض بيانات مراقبة السوق.

طريقة التشغيل:
    streamlit run dashboard.py

المحتوى:
  - ملخص سريع (عدد المنتجات، متوسط الأسعار، عدد التنبيهات)
  - رسم بياني لتاريخ السعر لكل منتج (زمن مقابل سعر)
  - جدول بكل التنبيهات المكتشفة
  - فلترة حسب الفئة
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis import run_analysis

st.set_page_config(page_title="Market Intelligence Dashboard", layout="wide")

st.title("📊 Market Intelligence Dashboard")
st.caption("مراقبة أسعار السوق وتحليل الاتجاهات لحظيًا")

result = run_analysis()

if result is None:
    st.error("مفيش بيانات متاحة. شغّل backfill_history.py أو scraper.py الأول.")
    st.stop()

df = result["raw"]
trends = result["trends"]
alerts = result["alerts"]
cat_summary = result["category_summary"]

# --- فلترة حسب الفئة ---
categories = ["الكل"] + sorted(df["category"].unique().tolist())
selected_category = st.sidebar.selectbox("فلترة حسب الفئة", categories)

if selected_category != "الكل":
    df_filtered = df[df["category"] == selected_category]
    trends_filtered = trends[trends["category"] == selected_category]
else:
    df_filtered = df
    trends_filtered = trends

# --- ملخص سريع (KPIs) ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("عدد المنتجات المراقبة", df["product_id"].nunique())
col2.metric("متوسط السعر الحالي", f"${df_filtered.groupby('product_id').last()['price'].mean():.2f}")
col3.metric("عدد التنبيهات", len(alerts))
col4.metric("عدد القراءات المسجلة", len(df))

st.divider()

# --- رسم بياني لتاريخ الأسعار ---
st.subheader("📈 تاريخ الأسعار عبر الوقت")
fig = px.line(
    trends_filtered,
    x="scraped_at",
    y="price",
    color="product_name",
    title="سعر كل منتج عبر الوقت",
    labels={"scraped_at": "التاريخ", "price": "السعر ($)", "product_name": "المنتج"}
)
st.plotly_chart(fig, use_container_width=True)

# --- المتوسط المتحرك ---
st.subheader("📉 المتوسط المتحرك (Rolling Average) مقابل السعر الفعلي")
selected_product = st.selectbox(
    "اختر منتج لعرض تفاصيله",
    trends_filtered["product_name"].unique()
)
product_trend = trends_filtered[trends_filtered["product_name"] == selected_product]

fig2 = px.line(
    product_trend,
    x="scraped_at",
    y=["price", "rolling_avg_3"],
    title=f"{selected_product}: السعر الفعلي مقابل المتوسط المتحرك",
    labels={"scraped_at": "التاريخ", "value": "السعر ($)", "variable": "النوع"}
)
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --- جدول التنبيهات ---
st.subheader("⚠️ التنبيهات المكتشفة")
if alerts.empty:
    st.success("مفيش تغيرات سعر كبيرة حاليًا.")
else:
    st.dataframe(
        alerts[["scraped_at", "product_name", "category", "price", "pct_change", "direction"]],
        use_container_width=True
    )

st.divider()

# --- ملخص حسب الفئة ---
st.subheader("📦 ملخص حسب الفئة")
st.dataframe(cat_summary, use_container_width=True)
