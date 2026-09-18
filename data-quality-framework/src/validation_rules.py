"""
validation_rules.py
--------------------
ده قلب الإطار (framework): مجموعة قواعد فحص جودة بيانات، كل قاعدة عبارة عن دالة مستقلة
بتاخد DataFrame وترجع تقرير عن المشاكل اللي لقتها.

فلسفة التصميم:
  - كل قاعدة (rule) مستقلة تمامًا عن الباقي — تقدر تشغل واحدة بس أو كلهم مع بعض.
  - كل قاعدة بترجع نفس الشكل الموحد (نفس structure) عشان يسهل تجميعهم في تقرير واحد.
  - القواعد "عامة" (generic) — تشتغل على أي DataFrame مش مربوطة بعمود معين،
    كده الأداة تصلح لأي بيانات يجيبها أي عميل، مش بس البيانات اللي احنا مولدينها.

القواعد المتاحة:
  1. check_missing_values      -> نسبة القيم الفاضية في كل عمود
  2. check_duplicates          -> الصفوف المكررة بالكامل
  3. check_outliers            -> القيم الشاذة إحصائيًا (IQR method) في الأعمدة الرقمية
  4. check_data_types          -> تناسق نوع البيانات في كل عمود
  5. check_negative_values     -> قيم سالبة في أعمدة يفترض تكون موجبة (زي salary, price, age)
  6. check_email_format        -> صحة صيغة الإيميل في أي عمود اسمه فيه "email"
  7. check_date_format         -> صحة صيغة وتواريخ الأعمدة الزمنية واكتشاف التواريخ المعطوبة
  8. check_string_whitespace   -> اكتشاف المسافات الزائدة (leading/trailing) والنصوص الفارغة
"""

import pandas as pd
import numpy as np
import re


def check_missing_values(df: pd.DataFrame) -> dict:
    """يحسب عدد ونسبة القيم الفاضية (null/NaN) في كل عمود."""
    missing_counts = df.isnull().sum()
    missing_pct = (missing_counts / len(df) * 100).round(2)

    issues = []
    for col in df.columns:
        if missing_counts[col] > 0:
            issues.append({
                "column": col,
                "missing_count": int(missing_counts[col]),
                "missing_pct": float(missing_pct[col])
            })

    return {
        "rule_name": "Missing Values Check",
        "severity": "high" if any(i["missing_pct"] > 20 for i in issues) else "medium" if issues else "ok",
        "issues_found": len(issues),
        "details": issues
    }


def check_duplicates(df: pd.DataFrame) -> dict:
    """يكتشف الصفوف المكررة بالكامل."""
    duplicate_mask = df.duplicated()
    duplicate_count = int(duplicate_mask.sum())

    return {
        "rule_name": "Duplicate Rows Check",
        "severity": "medium" if duplicate_count > 0 else "ok",
        "issues_found": duplicate_count,
        "details": {
            "duplicate_row_count": duplicate_count,
            "duplicate_pct": round(duplicate_count / len(df) * 100, 2) if len(df) > 0 else 0
        }
    }


def check_outliers(df: pd.DataFrame, columns: list = None) -> dict:
    """
    يكتشف القيم الشاذة (outliers) في الأعمدة الرقمية باستخدام IQR method:
    أي قيمة أصغر من (Q1 - 1.5*IQR) أو أكبر من (Q3 + 1.5*IQR) بتتحسب شاذة.
    ده معيار إحصائي معروف ومستخدم على نطاق واسع في تحليل جودة البيانات.
    """
    numeric_cols = columns or df.select_dtypes(include=[np.number]).columns.tolist()
    issues = []

    for col in numeric_cols:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if len(series) < 4:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_mask = (series < lower_bound) | (series > upper_bound)
        outlier_count = int(outlier_mask.sum())

        if outlier_count > 0:
            issues.append({
                "column": col,
                "outlier_count": outlier_count,
                "valid_range": f"[{round(lower_bound, 2)}, {round(upper_bound, 2)}]",
                "outlier_examples": series[outlier_mask].head(5).tolist()
            })

    return {
        "rule_name": "Outlier Detection (IQR Method)",
        "severity": "medium" if issues else "ok",
        "issues_found": len(issues),
        "details": issues
    }


def check_data_types(df: pd.DataFrame) -> dict:
    """
    يفحص كل عمود "نصي" (object dtype) لو فيه خليط من أنواع بيانات مختلفة
    (مثلاً عمود فيه أرقام وnصوص مع بعض)، وده مؤشر شائع لمشاكل في جودة البيانات.
    """
    issues = []
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna()
            types_found = sample.apply(lambda x: type(x).__name__).unique().tolist()
            if len(types_found) > 1:
                issues.append({
                    "column": col,
                    "types_found": types_found
                })

    return {
        "rule_name": "Data Type Consistency Check",
        "severity": "low" if issues else "ok",
        "issues_found": len(issues),
        "details": issues
    }


def check_negative_values(df: pd.DataFrame, columns: list = None) -> dict:
    """
    يفحص أعمدة يفترض منطقيًا إنها تكون موجبة دايمًا (زي salary, price, age, quantity)
    عن وجود قيم سالبة، اللي غالبًا بتبقى خطأ إدخال بيانات.

    لو مفيش columns محددة، الدالة بتحاول تخمن الأعمدة المرشحة تلقائيًا بناءً على اسمها.
    """
    if columns is None:
        keywords = ["price", "salary", "amount", "quantity", "age", "cost", "revenue"]
        columns = [c for c in df.columns if any(k in c.lower() for k in keywords)]

    issues = []
    for col in columns:
        if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
            continue
        negative_mask = df[col] < 0
        negative_count = int(negative_mask.sum())
        if negative_count > 0:
            issues.append({
                "column": col,
                "negative_count": negative_count,
                "examples": df.loc[negative_mask, col].head(5).tolist()
            })

    return {
        "rule_name": "Negative Values Check",
        "severity": "high" if issues else "ok",
        "issues_found": len(issues),
        "details": issues
    }


def check_email_format(df: pd.DataFrame) -> dict:
    """يفحص أي عمود فيه كلمة 'email' في اسمه للتأكد من صحة صيغة الإيميلات."""
    email_pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    email_cols = [c for c in df.columns if "email" in c.lower()]

    issues = []
    for col in email_cols:
        series = df[col].dropna().astype(str)
        invalid_mask = ~series.apply(lambda x: bool(email_pattern.match(x)))
        invalid_count = int(invalid_mask.sum())
        if invalid_count > 0:
            issues.append({
                "column": col,
                "invalid_count": invalid_count,
                "examples": series[invalid_mask].head(5).tolist()
            })

    return {
        "rule_name": "Email Format Check",
        "severity": "medium" if issues else "ok",
        "issues_found": len(issues),
        "details": issues
    }
    
def check_date_format(df: pd.DataFrame, columns: list = None) -> dict:
    """
    يفحص الأعمدة التي يُفترض أنها تواريخ (تحتوي على 'date' أو 'time' أو 'created' في اسمها أو محددة يدويًا)
    للتأكد من إمكانية تحويلها لصيغة تاريخ صالحة واكتشاف القيم المعطوبة.
    """
    if columns is None:
        keywords = ["date", "time", "created", "updated", "dob", "deadline"]
        columns = [c for c in df.columns if any(k in c.lower() for k in keywords)]

    issues = []
    for col in columns:
        if col not in df.columns:
            continue
            
        # لو العمود بالفعل datetime يتم تخطيه
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            continue

        series = df[col].dropna().astype(str)
        if series.empty:
            continue

        # محاولة تحويل النصوص إلى تواريخ وتحويل ما يفشل إلى NaT
        parsed = pd.to_datetime(series, errors="coerce")
        invalid_mask = parsed.isna()
        invalid_count = int(invalid_mask.sum())

        if invalid_count > 0:
            issues.append({
                "column": col,
                "invalid_count": invalid_count,
                "invalid_pct": round(invalid_count / len(series) * 100, 2),
                "examples": series[invalid_mask].head(5).tolist()
            })

    return {
        "rule_name": "Date Validity Check",
        "severity": "high" if any(i["invalid_pct"] > 10 for i in issues) else "medium" if issues else "ok",
        "issues_found": len(issues),
        "details": issues
    }


def check_string_whitespace(df: pd.DataFrame) -> dict:
    """
    يفحص الأعمدة النصية (string/object) لاكتشاف وجود مسافات زائدة في البداية أو النهاية (leading/trailing whitespace)
    أو وجود نصوص فارغة مكونة من مسافات فقط، والتي تسبب مشاكل أثناء الـ joins والفلترة.
    """
    issues = []
    text_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()

    for col in text_cols:
        series = df[col].dropna().astype(str)
        if series.empty:
            continue

        # كشف المسافات في الأطراف
        has_whitespace = series.str.strip() != series
        whitespace_count = int(has_whitespace.sum())

        if whitespace_count > 0:
            issues.append({
                "column": col,
                "whitespace_issues_count": whitespace_count,
                "examples": series[has_whitespace].head(5).tolist()
            })

    return {
        "rule_name": "String Whitespace Check",
        "severity": "low" if issues else "ok",
        "issues_found": len(issues),
        "details": issues
    }


# قائمة كل القواعد المتاحة — إضافة قاعدة جديدة تحتاج بس تضيفها هنا
ALL_RULES = [
    check_missing_values,
    check_duplicates,
    check_outliers,
    check_data_types,
    check_negative_values,
    check_email_format,
    check_date_format,         # الإضافة الأولى
    check_string_whitespace,    # الإضافة الثانية
]
