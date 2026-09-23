"""
transform.py
------------
مرحلة الـ T في ETL: هنا بيحصل التنظيف والدمج والتجهيز لبناء الـ Star Schema.

الفلسفة المتبعة في التعامل مع البيانات الغلط (زي ما اتفقنا):
  - مبنمسحهاش نهائيًا من غير ما نشوفها.
  - بنفصلها لملف منفصل (rejected_records.csv) عشان لو حد احتاج يراجعها لاحقًا يقدر.
  - الـ pipeline الرئيسي بيكمل بالبيانات النضيفة بس.

خطوات التنظيف:
  1. توحيد تنسيق التاريخ (كان فيه 3 فورمات مختلفة عمدًا في sales_export.csv)
  2. حذف الصفوف المكررة بالكامل
  3. فصل الصفوف اللي فيها قيم غلط (quantity فاضية، سعر سالب، customer_id فاضي) في ملف مرفوض
  4. دمج بيانات المنتجات (من الـ API) مع بيانات المبيعات
  5. دمج سعر المنافس لعمل مقارنة أسعار (تُستخدم لاحقًا في تقارير المشروع الثاني كمان كفكرة)
  6. حساب أعمدة مشتقة: total_amount = quantity * unit_price
"""

import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOG_DIR = os.path.join(BASE_DIR, "logs")


def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    يوحّد كل التواريخ لصيغة واحدة (YYYY-MM-DD) بغض النظر عن الفورمات الأصلي.
    pandas.to_datetime مع errors='coerce' بيحول أي تاريخ مش قادر يفهمه لـ NaT
    بدل ما يوقف البرنامج بالكامل — وده أسلوب دفاعي مهم مع بيانات حقيقية.
    """
    df = df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce", format="mixed")
    return df


def separate_invalid_records(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    يفصل الصفوف اللي فيها مشاكل عن الصفوف النضيفة.
    يرجع (clean_df, rejected_df) — الـ rejected فيها عمود إضافي 'rejection_reason'
    يوضح السبب بالظبط، عشان تكون قابلة للمراجعة بسهولة.
    """
    df = df.copy()
    reasons = []

    invalid_mask = pd.Series(False, index=df.index)

    # 1) quantity فاضية أو NaN
    qty_invalid = df["quantity"].isna()
    reasons.append(("quantity فارغة", qty_invalid))

    # 2) unit_price سالب (سعر مش منطقي)
    price_invalid = df["unit_price"] < 0
    reasons.append(("unit_price سالب", price_invalid))

    # 3) customer_id فاضي
    customer_invalid = df["customer_id"].isna() | (df["customer_id"] == "")
    reasons.append(("customer_id فارغ", customer_invalid))

    # 4) order_date فشل تحويله (NaT)
    date_invalid = df["order_date"].isna()
    reasons.append(("order_date غير صالح", date_invalid))

    # نجمع كل الأسباب في عمود واحد نصي لكل صف (ممكن يبقى فيه أكتر من سبب في نفس الوقت)
    reason_col = pd.Series([""] * len(df), index=df.index)
    for reason_text, mask in reasons:
        invalid_mask |= mask
        reason_col.loc[mask] = reason_col.loc[mask].apply(
            lambda x, r=reason_text: f"{x}; {r}" if x else r
        )

    rejected_df = df[invalid_mask].copy()
    rejected_df["rejection_reason"] = reason_col[invalid_mask]

    clean_df = df[~invalid_mask].copy()

    return clean_df, rejected_df


def run_transformation(raw_data: dict) -> dict:
    print("=" * 60)
    print("بدء مرحلة الـ TRANSFORM")
    print("=" * 60)

    sales_df = raw_data["sales"]
    products_df = raw_data["products"]
    competitor_df = raw_data["competitor"]

    # --- خطوة 1: توحيد التواريخ ---
    sales_df = normalize_dates(sales_df)

    # --- خطوة 2: حذف الصفوف المكررة بالكامل ---
    before = len(sales_df)
    sales_df = sales_df.drop_duplicates()
    duplicates_removed = before - len(sales_df)
    print(f"[TRANSFORM] تم حذف {duplicates_removed} صف مكرر بالكامل")

    # --- خطوة 3: فصل الصفوف الغلط ---
    clean_sales, rejected_sales = separate_invalid_records(sales_df)
    print(f"[TRANSFORM] صفوف نضيفة: {len(clean_sales)} | صفوف مرفوضة: {len(rejected_sales)}")

    # حفظ الصفوف المرفوضة في ملف منفصل للمراجعة (النهج اللي بنستخدمه دايمًا)
    os.makedirs(LOG_DIR, exist_ok=True)
    rejected_path = os.path.join(LOG_DIR, "rejected_records.csv")
    rejected_sales.to_csv(rejected_path, index=False, encoding="utf-8-sig")
    print(f"[TRANSFORM] الصفوف المرفوضة اتحفظت في: {rejected_path}")

    # --- خطوة 4: تصحيح الأنواع ---
    clean_sales["quantity"] = clean_sales["quantity"].astype(int)
    clean_sales["unit_price"] = clean_sales["unit_price"].astype(float)

    # --- خطوة 5: حساب total_amount ---
    clean_sales["total_amount"] = clean_sales["quantity"] * clean_sales["unit_price"]

    # --- خطوة 6: دمج بيانات المنتج (من API) ---
    # بنستخدم فقط الأعمدة المفيدة من products_df عشان نتجنب تكرار أعمدة زي product_name
    products_slim = products_df[["product_id", "category", "supplier", "cost_price"]]
    merged = clean_sales.merge(products_slim, on="product_id", how="left")

    # --- خطوة 7: دمج سعر المنافس لعمل مقارنة ---
    competitor_slim = competitor_df[["product_id", "competitor_price"]]
    merged = merged.merge(competitor_slim, on="product_id", how="left")

    # حساب هامش الربح وفرق السعر عن المنافس (أعمدة تحليلية مفيدة للتقارير لاحقًا)
    merged["profit_margin"] = merged["unit_price"] - merged["cost_price"]
    merged["price_diff_vs_competitor"] = merged["unit_price"] - merged["competitor_price"]

    print(f"\n[SUCCESS] الجدول النهائي بعد الدمج: {len(merged)} صف, {len(merged.columns)} عمود")

    return {
        "clean_sales_full": merged,
        "rejected": rejected_sales
    }


if __name__ == "__main__":
    from extract import run_extraction
    raw = run_extraction()
    result = run_transformation(raw)
    print("\n--- عينة من الجدول النهائي ---")
    print(result["clean_sales_full"].head())
