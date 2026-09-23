"""
main.py
-------
نقطة تشغيل واحدة للمشروع كامل (بدون الـ scheduler المستمر):
  1. توليد بيانات تاريخية (لو أول مرة)
  2. تشغيل دورة سحب واحدة
  3. تحليل وإرسال تنبيهات
  4. طباعة ملخص نهائي

بعد كده تقدر تفتح الداشبورد بـ: streamlit run dashboard.py
"""

import os
from scraper import init_database, run_scrape_cycle
from backfill_history import backfill
from analysis import run_analysis
from alert_notifier import notify_alerts

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "output", "market_watch.db")


def run_pipeline():
    print("=" * 60)
    print("MARKET INTELLIGENCE PIPELINE")
    print("=" * 60)

    # لو أول مرة تشتغل، نعمل بيانات تاريخية عشان التحليل يبقى له معنى فورًا
    if not os.path.exists(DB_PATH):
        print("[INFO] أول تشغيل — بنعمل بيانات تاريخية (30 يوم)...")
        backfill(days=30)
    else:
        print("[INFO] قاعدة البيانات موجودة بالفعل — هنضيف عليها دورة سحب جديدة")
        run_scrape_cycle()

    result = run_analysis()
    if result:
        notify_alerts(result["alerts"])

    print("\n" + "=" * 60)
    print("اكتمل الـ Pipeline. لعرض الداشبورد التفاعلي شغّل:")
    print("   streamlit run dashboard.py")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
