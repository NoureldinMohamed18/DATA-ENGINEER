"""
╔══════════════════════════════════════════════════════╗
║       Healthcare Data Pipeline — مستشفى النور        ║
║       Extract → Transform → Load                     ║
╚══════════════════════════════════════════════════════╝
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime 

# ══════════════════════════════════════════════════════
# الخطوة 1: EXTRACT — جلب البيانات
# ══════════════════════════════════════════════════════

def extract(filepath):
    """
    تقوم بقراءة ملف الـ CSV الخام وإرجاع DataFrame.
    """
    print("\n" + "="*55)
    print("📥 EXTRACT: جاري جلب البيانات...")
    print("="*55)
    
    try:
        df = pd.read_csv(filepath)
        print(f"  ✅ تم قراءة الملف: {filepath}")
        print(f"  📊 إجمالي السجلات : {len(df)} مريض")
        print(f"  📋 عدد الأعمدة    : {len(df.columns)}")
        print(f"  🏷️  الأعمدة         : {list(df.columns)}")
        return df
    except FileNotFoundError:
        print("❌ الملف غير موجود! يرجى التحقق من المسار.")
        raise

# ══════════════════════════════════════════════════════
# الخطوة 2: TRANSFORM — الفلترة والتحقق الصارم
# ══════════════════════════════════════════════════════

def transform(df):
    """
    تتحقق من صحة البيانات وتفصل السجلات النظيفة عن المرفوضة مع تحديد الأسباب.
    """
    print("\n" + "="*55)
    print("⚙️  TRANSFORM: جاري الفحص والفلترة الصارمة...")
    print("="*55)
    
    df = df.copy()
    
    # 0. حذف الأعمدة المحسوبة القديمة لو كانت موجودة مسبقاً في الملف المدمج
    cols_to_drop = ["age_group", "bp_category", "admission_year", "invalid_reason"]
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

    # 1. تحويل الأعمدة لأرقام وتواريخ للتحقق بشكل صحيح
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df["blood_pressure_systolic"] = pd.to_numeric(df["blood_pressure_systolic"], errors="coerce")
    df["heart_rate"] = pd.to_numeric(df["heart_rate"], errors="coerce")
    df["length_of_stay_days"] = pd.to_numeric(df["length_of_stay_days"], errors="coerce")
    parsed_dates = pd.to_datetime(df["admission_date"], errors="coerce")

    # 2. تحديد شروط الرفض (True = قيمة غير صحيحة)
    cond_age   = ~df["age"].between(0, 120) | df["age"].isna()
    cond_bp    = ~df["blood_pressure_systolic"].between(60, 250) | df["blood_pressure_systolic"].isna()
    cond_hr    = ~df["heart_rate"].between(40, 200) | df["heart_rate"].isna()
    cond_stay  = ~df["length_of_stay_days"].between(1, 60) | df["length_of_stay_days"].isna()
    cond_date  = parsed_dates.isna()

    # السجل يعتبر مرفوض إذا تحقق فيه أي شرط أخطاء
    invalid_mask = cond_age | cond_bp | cond_hr | cond_stay | cond_date

    # 3. بناء نص أسباب الرفض لكل سجل مرفوض
    reasons = pd.Series([""] * len(df), index=df.index)
    reasons[cond_age]  += "عمر غير منطقي | "
    reasons[cond_bp]   += "ضغط دم غير منطقي | "
    reasons[cond_hr]   += "ضربات قلب غير منطقية | "
    reasons[cond_stay] += "مدة إقامة غير منطقية | "
    reasons[cond_date] += "تاريخ دخول غير صحيح | "

    # 4. فصل السجلات المرفوضة
    df_invalid = df[invalid_mask].copy()
    df_invalid["invalid_reason"] = reasons[invalid_mask]

    # 5. معالجة وتجهيز السجلات النظيفة
    df_clean = df[~invalid_mask].copy()
    
    # توحيد صيغة التاريخ والتأكد من ضبط أنواع البيانات للأعداد الصحيحة
    df_clean["admission_date"] = parsed_dates[~invalid_mask].dt.strftime('%Y-%m-%d')
    int_cols = ["age", "blood_pressure_systolic", "heart_rate", "length_of_stay_days"]
    for c in int_cols:
        df_clean[c] = df_clean[c].astype(int)

    # معالجة القيم الناقصة في التشخيص بالسجلات النظيفة
    df_clean["diagnosis"] = df_clean["diagnosis"].fillna("Unknown")

    # 6. إضافة الأعمدة المحسوبة للبيانات النظيفة
    print("\n  ✨ إضافة الأعمدة المحسوبة (age_group, bp_category, admission_year)...")
    
    def classify_age(age):
        if age < 18:   return "Child"
        elif age < 40: return "Young Adult"
        elif age < 60: return "Middle Aged"
        else:          return "Senior"

    def classify_bp(bp):
        if bp < 90:    return "Low"
        elif bp < 120: return "Normal"
        elif bp < 140: return "Elevated"
        else:          return "High"

    df_clean["age_group"]      = df_clean["age"].apply(classify_age)
    df_clean["bp_category"]    = df_clean["blood_pressure_systolic"].apply(classify_bp)
    df_clean["admission_year"] = pd.to_datetime(df_clean["admission_date"]).dt.year

    # 📊 طباعة الملخص
    print("\n" + "-"*55)
    print("  📊 ملخص الـ Transform:")
    print(f"     إجمالي السجلات     : {len(df)}")
    print(f"     ✅ سجلات صحيحة    : {len(df_clean)}")
    print(f"     ❌ سجلات مرفوضة   : {len(df_invalid)}")
    if len(df) > 0:
        print(f"     📉 نسبة الرفض      : {len(df_invalid)/len(df)*100:.1f}%")
    print("-"*55)

    return df_clean, df_invalid

# ══════════════════════════════════════════════════════
# الخطوة 3: LOAD — حفظ المخرجات والتقرير
# ══════════════════════════════════════════════════════

def load(df_clean, df_invalid, output_dir):
    """
    تحفظ الملفات المفلترة وتكتب تقرير التشغيل المكتمل.
    """
    print("\n" + "="*55)
    print("💾 LOAD: جاري حفظ البيانات والتصنيفات...")
    print("="*55)

    os.makedirs(output_dir, exist_ok=True)

    clean_path   = os.path.join(output_dir, "patients_clean.csv")
    invalid_path = os.path.join(output_dir, "invalid_records.csv")
    summary_path = os.path.join(output_dir, "pipeline_summary.txt")

    # حفظ الملفات
    df_clean.to_csv(clean_path, index=False)
    print(f"  ✅ البيانات النظيفة   → {clean_path}")

    df_invalid.to_csv(invalid_path, index=False)
    print(f"  ⚠️  السجلات المرفوضة  → {invalid_path}")

    # كتابة ملف الملخص
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("=======================================================\n")
        f.write("  Healthcare Pipeline — تقرير التشغيل\n")
        f.write("=======================================================\n")
        f.write(f"  وقت التشغيل    : {datetime.now().strftime('%H:%M:%S %Y-%m-%d')}\n")
        f.write(f"  إجمالي السجلات : {len(df_clean) + len(df_invalid)}\n")
        f.write(f"  سجلات نظيفة    : {len(df_clean)}\n")
        f.write(f"  سجلات مرفوضة   : {len(df_invalid)}\n\n")

        f.write("  توزيع الفئات العمرية:\n")
        if not df_clean.empty:
            for group, count in df_clean["age_group"].value_counts().items():
                f.write(f"    {group}: {count}\n")
        else:
            f.write("    لا توجد سجلات نظيفة\n")

        f.write("\n  توزيع ضغط الدم:\n")
        if not df_clean.empty:
            for cat, count in df_clean["bp_category"].value_counts().items():
                f.write(f"    {cat}: {count}\n")
        else:
            f.write("    لا توجد سجلات نظيفة\n")

        f.write("\n  أكثر التشخيصات شيوعاً:\n")
        if not df_clean.empty:
            for diag, count in df_clean["diagnosis"].value_counts().head(5).items():
                f.write(f"    {diag}: {count}\n")
        else:
            f.write("    لا توجد سجلات نظيفة\n")

    print(f"  📄 ملف الملخص     → {summary_path}")

# ══════════════════════════════════════════════════════
# الـ Main — تشغيل الـ Pipeline
# ══════════════════════════════════════════════════════

def run_pipeline():
    print("\n" + "🏥 " * 18)
    print("  Healthcare Data Pipeline — مستشفى النور")
    print("🏥 " * 18)

    # مسارات الملفات
    BASE_DIR   = r"C:\Users\NOUR\OneDrive\Desktop\data-engineering-journey\SIMPLE ETL"
    INPUT_FILE = os.path.join(BASE_DIR, "patients_raw.csv")
    OUTPUT_DIR = BASE_DIR

    start_time = datetime.now()

    # 1. EXTRACT
    df_raw = extract(INPUT_FILE)

    # 2. TRANSFORM
    df_clean, df_invalid = transform(df_raw)

    # 3. LOAD
    load(df_clean, df_invalid, OUTPUT_DIR)

    duration = (datetime.now() - start_time).total_seconds()

    print("\n" + "="*55)
    print(f"  🎉 Pipeline اتشغل بنجاح في {duration:.2f} ثانية!")
    print("="*55 + "\n")

if __name__ == "__main__":
    run_pipeline()