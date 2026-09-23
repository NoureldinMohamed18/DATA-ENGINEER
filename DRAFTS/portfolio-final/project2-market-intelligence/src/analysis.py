"""
analysis.py
-----------
تحليل تاريخ الأسعار باستخدام Pandas عشان نستخرج insights:

  1) rolling average (متوسط متحرك) لكل منتج — بيساعد نشوف الاتجاه العام من غير ضوضاء اليوم الواحد
  2) day-over-day % change — نسبة التغيير من يوم للتاني
  3) Alert detection: أي تغيير سعر أكبر من threshold معين (مثلاً 10%) بيتسجل كـ "تنبيه"

المفاهيم المستخدمة هنا مبنية على Window Functions اللي اتشرحت في سلايدز Advanced SQL
(concept الـ "حساب عبر صفوف مرتبطة بالصف الحالي")، لكن بنطبقها هنا بـ Pandas
باستخدام .rolling() و .pct_change() بدل SQL مباشرة — وده مفيد تتعلمه لأن نفس المنطق
بيتطبق بطريقتين مختلفتين حسب الأداة المتاحة.
"""

import pandas as pd
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "output", "market_watch.db")

ALERT_THRESHOLD_PCT = 10.0  # أي تغيير سعر أكبر من كده (موجب أو سالب) بيتسجل كتنبيه


def load_price_history() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT product_id, product_name, category, price, stock_status, scraped_at
        FROM price_history
        ORDER BY product_id, scraped_at
    """, conn)
    conn.close()

    df["scraped_at"] = pd.to_datetime(df["scraped_at"])
    return df


def compute_trends(df: pd.DataFrame) -> pd.DataFrame:
    """
    يحسب لكل منتج على حدة (groupby):
      - rolling_avg_3: متوسط متحرك لآخر 3 قراءات (يقلل تأثير التقلبات اليومية العشوائية)
      - pct_change: نسبة التغيير عن القراءة اللي قبلها مباشرة
    """
    df = df.sort_values(["product_id", "scraped_at"]).copy()

    df["rolling_avg_3"] = (
        df.groupby("product_id")["price"]
        .transform(lambda x: x.rolling(window=3, min_periods=1).mean())
        .round(2)
    )

    df["pct_change"] = (
        df.groupby("product_id")["price"]
        .transform(lambda x: x.pct_change() * 100)
        .round(2)
    )

    return df


def detect_alerts(df_with_trends: pd.DataFrame) -> pd.DataFrame:
    """
    يفلتر أي صف فيه تغيير سعر أكبر من الـ threshold (موجب أو سالب) ويرجعه كجدول تنبيهات.
    """
    alerts = df_with_trends[df_with_trends["pct_change"].abs() >= ALERT_THRESHOLD_PCT].copy()
    alerts["direction"] = alerts["pct_change"].apply(lambda x: "ارتفاع" if x > 0 else "انخفاض")
    alerts["alert_message"] = alerts.apply(
        lambda row: f"{row['product_name']}: {row['direction']} سعر بنسبة {abs(row['pct_change'])}% "
                    f"(من ${row['price'] / (1 + row['pct_change']/100):.2f} إلى ${row['price']:.2f})",
        axis=1
    )
    return alerts[["scraped_at", "product_id", "product_name", "category", "price", "pct_change", "direction", "alert_message"]]


def category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """ملخص لآخر الأسعار مجمعة حسب الفئة — متوسط السعر الحالي لكل فئة."""
    latest = df.sort_values("scraped_at").groupby("product_id").tail(1)
    summary = latest.groupby("category").agg(
        avg_price=("price", "mean"),
        num_products=("product_id", "nunique")
    ).round(2).reset_index()
    return summary


def run_analysis():
    print("=" * 60)
    print("بدء التحليل")
    print("=" * 60)

    df = load_price_history()
    if df.empty:
        print("[WARNING] مفيش بيانات في price_history. شغّل scraper.py أو backfill_history.py الأول.")
        return None

    trends = compute_trends(df)
    alerts = detect_alerts(trends)
    cat_summary = category_summary(df)

    print(f"[ANALYSIS] عدد السجلات المحللة: {len(df)}")
    print(f"[ANALYSIS] عدد التنبيهات المكتشفة (تغيير >= {ALERT_THRESHOLD_PCT}%): {len(alerts)}")

    os.makedirs(os.path.join(BASE_DIR, "output"), exist_ok=True)
    alerts.to_csv(os.path.join(BASE_DIR, "output", "price_alerts.csv"), index=False, encoding="utf-8-sig")
    trends.to_csv(os.path.join(BASE_DIR, "output", "price_trends.csv"), index=False, encoding="utf-8-sig")

    if not alerts.empty:
        print("\n--- التنبيهات المكتشفة ---")
        for msg in alerts["alert_message"]:
            print(f"  ⚠ {msg}")

    return {
        "raw": df,
        "trends": trends,
        "alerts": alerts,
        "category_summary": cat_summary
    }


if __name__ == "__main__":
    run_analysis()
