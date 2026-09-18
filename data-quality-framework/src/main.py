"""
main.py
-------
نقطة تشغيل واحدة: فحص أي ملف بيانات + توليد تقرير JSON و HTML.

طريقة الاستخدام:
    python main.py path/to/your_file.csv
    python main.py path/to/your_file.xlsx

لو مفيش مسار، بيشتغل على ملف العينة الافتراضي للعرض.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import run_quality_check, BASE_DIR
from html_report import generate_html_report


def main():
    if len(sys.argv) < 2:
        file_path = os.path.join(BASE_DIR, "data", "sample_employees.csv")
        print(f"[INFO] مفيش ملف محدد، هنستخدم ملف العينة: {file_path}\n")
    else:
        file_path = sys.argv[1]
        if not os.path.exists(file_path):
            print(f"[ERROR] الملف مش موجود: {file_path}")
            return

    report, flagged = run_quality_check(file_path)
    html_path = generate_html_report(report)

    print("\n" + "=" * 60)
    print("افتح التقرير المرئي في المتصفح:")
    print(f"   {html_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
