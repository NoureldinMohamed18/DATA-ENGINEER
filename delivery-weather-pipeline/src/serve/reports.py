from datetime import datetime, timezone
from pathlib import Path
import pandas as pd


def write_html(conn, reports_dir: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    table = pd.read_sql_query("SELECT * FROM vw_delay_by_city ORDER BY delay_pct DESC", conn)
    when = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="utf-8"/><title>توصيل وطقس</title>
<style>
body {{ font-family: Tahoma, sans-serif; margin: 24px; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 8px; }}
th {{ background: #1f4e79; color: white; }}
</style></head>
<body>
<h1>خطر التأخير حسب المدينة</h1>
<p>{when}</p>
{table.to_html(index=False)}
</body></html>"""
    (reports_dir / "dashboard.html").write_text(html, encoding="utf-8")
