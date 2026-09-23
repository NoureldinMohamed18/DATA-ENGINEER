"""
alert_notifier.py
------------------
نظام تنبيهات بسيط: بياخد التنبيهات المكتشفة من analysis.py ويسجلها في ملف log مخصص،
بنفس الشكل اللي هيبقى عليه أي نظام إشعارات حقيقي (email / Slack / SMS).

ليه log file بدل إرسال إيميل فعلي؟
  عشان المشروع يفضل شغال ومتكامل من غير الحاجة لإعداد SMTP server أو API keys حقيقية.
  الكود هنا مصمم بحيث لو حبيت تفعّل إرسال إيميل حقيقي، هتضيف بس دالة send_email()
  وتستدعيها بدل log_alert() — باقي المنطق (اكتشاف التنبيه، صياغة الرسالة) هيفضل زي ما هو.
"""

import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
ALERT_LOG_PATH = os.path.join(LOG_DIR, "alerts.log")


def log_alert(message: str):
    """
    يسجل تنبيه واحد في ملف alerts.log مع timestamp.
    نفس المكان اللي لو حبيت تربطه بـ email حقيقي، هتستبدل السطر ده بمكتبة smtplib
    أو webhook لـ Slack بدل الكتابة في ملف.
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="seconds")
    with open(ALERT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def notify_alerts(alerts_df):
    """ياخد DataFrame التنبيهات من analysis.py ويسجل كل واحد منهم."""
    if alerts_df is None or alerts_df.empty:
        print("[NOTIFIER] مفيش تنبيهات جديدة عشان نبعتها.")
        return 0

    count = 0
    for _, row in alerts_df.iterrows():
        log_alert(row["alert_message"])
        count += 1

    print(f"[NOTIFIER] تم تسجيل {count} تنبيه في {ALERT_LOG_PATH}")
    return count


if __name__ == "__main__":
    from analysis import run_analysis
    result = run_analysis()
    if result:
        notify_alerts(result["alerts"])
