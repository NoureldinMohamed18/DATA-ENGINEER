"""
engine.py
---------
المحرك الرئيسي للإطار: بياخد أي ملف (CSV أو Excel) كمدخل، يشغل عليه كل قواعد الفحص،
ويطلع تقرير شامل + يفصل السجلات المشكوك فيها في ملف منفصل للمراجعة
(بنفس النهج اللي استخدمناه في المشروع الأول: منمسحش البيانات، بنعزلها بس).

طريقة الاستخدام:
    python engine.py path/to/your_file.csv
    أو
    python engine.py path/to/your_file.xlsx

الناتج:
    output/quality_report.json   -> تقرير شامل بكل القواعد والمشاكل المكتشفة
    output/flagged_records.csv   -> الصفوف اللي فيها مشكلة واحدة على الأقل (للمراجعة)
"""

import pandas as pd
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validation_rules import ALL_RULES

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def load_file(file_path: str) -> pd.DataFrame:
    """يحمل أي ملف CSV أو Excel في DataFrame واحد — نقطة دخول موحدة بغض النظر عن الصيغة."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".csv":
        return pd.read_csv(file_path)
    elif ext in (".xlsx", ".xls"):
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"صيغة الملف غير مدعومة: {ext}. الصيغ المدعومة: .csv, .xlsx, .xls")


def run_all_checks(df: pd.DataFrame) -> list:
    """يشغل كل القواعد المسجلة في ALL_RULES ويرجع قائمة بنتائج كل واحدة منهم."""
    results = []
    for rule_func in ALL_RULES:
        result = rule_func(df)
        results.append(result)
        status_icon = "✅" if result["severity"] == "ok" else "⚠️"
        print(f"  {status_icon} {result['rule_name']}: {result['issues_found']} مشكلة")
    return results


def flag_problematic_rows(df: pd.DataFrame, check_results: list) -> pd.DataFrame:
    """
    يحدد أي صف فيه مشكلة واحدة على الأقل (nulls, negative values, duplicates)
    ويرجعه في DataFrame منفصل مع عمود flag_reasons يوضح السبب.

    ملاحظة: قواعد الـ outliers والـ email format والـ data types بتديك insight عن الأعمدة
    عمومًا، لكن الصفوف اللي بنعلّمها هنا (flag) هي أوضح حالات: nulls, negatives, duplicates.
    """
    df = df.copy()
    flags = pd.Series([""] * len(df), index=df.index)

    # nulls في أي عمود
    null_mask = df.isnull().any(axis=1)
    flags.loc[null_mask] = flags.loc[null_mask].apply(
        lambda x: f"{x}; قيمة فارغة" if x else "قيمة فارغة"
    )

    # صفوف مكررة
    dup_mask = df.duplicated(keep=False)
    flags.loc[dup_mask] = flags.loc[dup_mask].apply(
        lambda x: f"{x}; صف مكرر" if x else "صف مكرر"
    )

    # قيم سالبة في أي عمود رقمي يحتمل يكون مؤشر خطأ (نفس منطق check_negative_values)
    keywords = ["price", "salary", "amount", "quantity", "age", "cost", "revenue"]
    candidate_cols = [c for c in df.columns if any(k in c.lower() for k in keywords)]
    for col in candidate_cols:
        if pd.api.types.is_numeric_dtype(df[col]):
            neg_mask = df[col] < 0
            flags.loc[neg_mask] = flags.loc[neg_mask].apply(
                lambda x, c=col: f"{x}; قيمة سالبة في {c}" if x else f"قيمة سالبة في {c}"
            )

    df["flag_reasons"] = flags
    flagged = df[df["flag_reasons"] != ""].copy()
    return flagged


def generate_report(df: pd.DataFrame, check_results: list, file_path: str) -> dict:
    total_issues = sum(r["issues_found"] for r in check_results)
    severity_levels = [r["severity"] for r in check_results if r["severity"] != "ok"]

    if "high" in severity_levels:
        overall_status = "يحتاج مراجعة عاجلة"
    elif "medium" in severity_levels:
        overall_status = "يحتاج تحسين"
    elif "low" in severity_levels:
        overall_status = "جيد مع ملاحظات بسيطة"
    else:
        overall_status = "ممتاز"

    report = {
        "file_analyzed": os.path.basename(file_path),
        "analyzed_at": datetime.now().isoformat(timespec="seconds"),
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "overall_status": overall_status,
        "total_issues_found": total_issues,
        "checks": check_results
    }
    return report


def run_quality_check(file_path: str):
    print("=" * 60)
    print(f"فحص جودة البيانات: {os.path.basename(file_path)}")
    print("=" * 60)

    df = load_file(file_path)
    print(f"\n[INFO] تم تحميل {len(df)} صف, {len(df.columns)} عمود\n")

    print("[جاري تشغيل قواعد الفحص]")
    check_results = run_all_checks(df)

    report = generate_report(df, check_results, file_path)
    flagged = flag_problematic_rows(df, check_results)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    report_path = os.path.join(OUTPUT_DIR, "quality_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    flagged_path = os.path.join(OUTPUT_DIR, "flagged_records.csv")
    flagged.to_csv(flagged_path, index=False, encoding="utf-8-sig")

    print(f"\n[النتيجة العامة]: {report['overall_status']}")
    print(f"[إجمالي المشاكل المكتشفة]: {report['total_issues_found']}")
    print(f"[صفوف تحتاج مراجعة]: {len(flagged)} من أصل {len(df)}")
    print(f"\n[OK] التقرير الكامل: {report_path}")
    print(f"[OK] الصفوف المعلّمة: {flagged_path}")

    return report, flagged


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # لو مفيش مسار متحدد، نستخدم ملف العينة الافتراضي للاختبار والعرض
        default_path = os.path.join(BASE_DIR, "data", "sample_employees.csv")
        print(f"[INFO] مفيش ملف محدد، هنستخدم ملف العينة: {default_path}\n")
        run_quality_check(default_path)
    else:
        run_quality_check(sys.argv[1])
