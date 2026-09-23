"""
scheduler.py
------------
مسؤول عن تشغيل دورة السحب والتحليل بشكل دوري تلقائي، من غير الحاجة لتشغيل السكريبت يدويًا
كل مرة. ده بديل بسيط لـ Apache Airflow (اللي هتتعلمه لاحقًا في خطتك للـ cloud/orchestration)،
لكنه بيوضح نفس الفكرة الأساسية: "شغّل المهمة دي كل فترة زمنية معينة بشكل تلقائي".

طريقة التشغيل:
    python scheduler.py
    (هيفضل شغال في الخلفية ويعمل دورة سحب + تحليل + تنبيهات كل ساعة، أو المدة اللي تحددها)

للإيقاف: Ctrl+C
"""

import schedule
import time
import logging
import os
from scraper import run_scrape_cycle
from analysis import run_analysis
from alert_notifier import notify_alerts

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "scheduler.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("scheduler")


def job():
    """دورة كاملة: سحب بيانات جديدة -> تحليل -> إرسال تنبيهات لو فيه."""
    logger.info("بدء دورة مجدولة جديدة")
    try:
        run_scrape_cycle()
        result = run_analysis()
        if result:
            notify_alerts(result["alerts"])
        logger.info("اكتملت الدورة بنجاح")
    except Exception as e:
        logger.error(f"فشلت الدورة: {str(e)}", exc_info=True)


def start_scheduler(interval_minutes: int = 60):
    """
    يجدول تشغيل job() كل interval_minutes دقيقة.
    القيمة الافتراضية ساعة، لكن تقدر تقللها لو عايز تختبر بسرعة (مثلاً كل دقيقة).
    """
    schedule.every(interval_minutes).minutes.do(job)
    logger.info(f"تم بدء الـ Scheduler — هيشتغل كل {interval_minutes} دقيقة. اضغط Ctrl+C للإيقاف.")

    # نشغل أول دورة فورًا عشان مانستناش دقيقة كاملة عشان نشوف نتيجة
    job()

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    start_scheduler(interval_minutes=60)
