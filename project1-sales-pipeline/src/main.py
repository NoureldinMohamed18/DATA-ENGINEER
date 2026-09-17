"""
main.py
-------
نقطة الدخول الوحيدة لتشغيل الـ Pipeline بالكامل: Extract -> Transform -> Load

طريقة التشغيل:
    python main.py

بعد ما يخلص، تقدر تشغل الـ API بـ:
    python api.py
"""

import time
import logging
import os
from extract import run_extraction
from transform import run_transformation
from load import run_load

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "pipeline.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("sales_pipeline")


def run_pipeline():
    start = time.time()
    logger.info("بدء تشغيل الـ Pipeline الكامل")

    try:
        raw_data = run_extraction()
        clean_data = run_transformation(raw_data)
        db_path = run_load(clean_data)

        elapsed = round(time.time() - start, 2)
        logger.info(f"اكتمل الـ Pipeline بنجاح في {elapsed} ثانية")
        logger.info(f"قاعدة البيانات النهائية: {db_path}")
        return True

    except Exception as e:
        logger.error(f"فشل الـ Pipeline: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    success = run_pipeline()
    if success:
        print("\n" + "=" * 60)
        print("الـ Pipeline اكتمل بنجاح! شغّل الأمر التالي عشان تفتح الـ API:")
        print("   python src/api.py")
        print("=" * 60)
