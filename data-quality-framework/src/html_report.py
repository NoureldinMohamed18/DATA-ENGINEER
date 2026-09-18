"""
html_report.py
--------------
يحوّل تقرير الـ JSON اللي طلع من engine.py لتقرير HTML جميل بصريًا،
عشان تقدر تبعته للعميل مباشرة أو تفتحه في المتصفح — ده اللي بيفرق بين
"سكريبت بيطبع في الترمينال" و"منتج جاهز تبيعه".
"""

import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

SEVERITY_COLORS = {
    "high": "#e74c3c",
    "medium": "#f39c12",
    "low": "#3498db",
    "ok": "#27ae60"
}

SEVERITY_LABELS_AR = {
    "high": "عالي",
    "medium": "متوسط",
    "low": "منخفض",
    "ok": "سليم"
}


def render_check_card(check: dict) -> str:
    color = SEVERITY_COLORS.get(check["severity"], "#95a5a6")
    label = SEVERITY_LABELS_AR.get(check["severity"], check["severity"])

    details_html = ""
    details = check["details"]

    if isinstance(details, list) and details:
        for item in details:
            if isinstance(item, dict):
                rows = "".join(f"<li><b>{k}:</b> {v}</li>" for k, v in item.items())
                details_html += f"<ul class='detail-block'>{rows}</ul>"
    elif isinstance(details, dict) and details:
        rows = "".join(f"<li><b>{k}:</b> {v}</li>" for k, v in details.items())
        details_html = f"<ul class='detail-block'>{rows}</ul>"

    if not details_html:
        details_html = "<p class='no-issues'>لا توجد مشاكل ✓</p>"

    return f"""
    <div class="check-card" style="border-right: 5px solid {color};">
        <div class="check-header">
            <h3>{check['rule_name']}</h3>
            <span class="badge" style="background:{color};">{label} ({check['issues_found']})</span>
        </div>
        {details_html}
    </div>
    """


def generate_html_report(report: dict, output_path: str = None) -> str:
    checks_html = "".join(render_check_card(c) for c in report["checks"])

    status_color = "#27ae60" if report["overall_status"] == "ممتاز" else \
                   "#3498db" if report["overall_status"] == "جيد مع ملاحظات بسيطة" else \
                   "#f39c12" if report["overall_status"] == "يحتاج تحسين" else "#e74c3c"

    html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<title>تقرير جودة البيانات - {report['file_analyzed']}</title>
<style>
    body {{
        font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
        background: #f4f6f8;
        margin: 0;
        padding: 40px 20px;
        color: #2c3e50;
    }}
    .container {{ max-width: 900px; margin: 0 auto; }}
    .header {{
        background: white;
        border-radius: 12px;
        padding: 30px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 25px;
    }}
    .header h1 {{ margin: 0 0 10px 0; font-size: 24px; }}
    .meta {{ color: #7f8c8d; font-size: 14px; }}
    .status-badge {{
        display: inline-block;
        padding: 8px 20px;
        border-radius: 20px;
        color: white;
        font-weight: bold;
        margin-top: 15px;
        background: {status_color};
    }}
    .stats-row {{ display: flex; gap: 15px; margin-top: 20px; }}
    .stat-box {{
        flex: 1;
        background: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }}
    .stat-box .num {{ font-size: 28px; font-weight: bold; color: #2c3e50; }}
    .stat-box .label {{ font-size: 13px; color: #7f8c8d; margin-top: 5px; }}
    .check-card {{
        background: white;
        border-radius: 10px;
        padding: 20px 25px;
        margin-bottom: 15px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }}
    .check-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }}
    .check-header h3 {{ margin: 0; font-size: 17px; }}
    .badge {{
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: bold;
    }}
    .detail-block {{
        background: #fafafa;
        border-radius: 6px;
        padding: 12px 20px;
        margin: 8px 0 0 0;
        font-size: 14px;
        list-style: none;
    }}
    .detail-block li {{ margin: 4px 0; }}
    .no-issues {{ color: #27ae60; font-weight: bold; margin: 0; }}
    .footer {{ text-align: center; color: #95a5a6; font-size: 13px; margin-top: 30px; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📋 تقرير جودة البيانات</h1>
        <div class="meta">
            الملف: <b>{report['file_analyzed']}</b> &nbsp;|&nbsp;
            تاريخ الفحص: {report['analyzed_at']}
        </div>
        <div class="status-badge">الحالة العامة: {report['overall_status']}</div>
        <div class="stats-row">
            <div class="stat-box"><div class="num">{report['total_rows']}</div><div class="label">إجمالي الصفوف</div></div>
            <div class="stat-box"><div class="num">{report['total_columns']}</div><div class="label">الأعمدة</div></div>
            <div class="stat-box"><div class="num">{report['total_issues_found']}</div><div class="label">إجمالي المشاكل</div></div>
        </div>
    </div>

    {checks_html}

    <div class="footer">تم إنشاء هذا التقرير تلقائيًا بواسطة Data Quality Framework</div>
</div>
</body>
</html>"""

    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, "quality_report.html")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[OK] تقرير HTML اتولد في: {output_path}")
    return output_path


if __name__ == "__main__":
    report_json_path = os.path.join(OUTPUT_DIR, "quality_report.json")
    if not os.path.exists(report_json_path):
        print("[ERROR] مفيش quality_report.json. شغّل engine.py الأول.")
    else:
        with open(report_json_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        generate_html_report(report)
