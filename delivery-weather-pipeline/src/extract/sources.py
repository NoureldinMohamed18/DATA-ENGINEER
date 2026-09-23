from pathlib import Path
import pandas as pd
import requests


def extract_csv(raw_dir: Path, filename: str) -> pd.DataFrame:
    # السحب = قراءة فقط. أي تنظيف هنا يخلط عيب الملف بعيب الكود
    path = raw_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"الملف الخام ناقص: {path}")
    return pd.read_csv(path)


def extract_weather(url: str, hubs: pd.DataFrame, timeout: int) -> pd.DataFrame:
    # لكل مدينة إحداثيات. نطلب الطقس الحالي من أوبن ميتيو (من غير مفتاح)
    rows = []
    session = requests.Session()
    for hub in hubs.itertuples(index=False):
        params = {
            "latitude": hub.latitude,
            "longitude": hub.longitude,
            "current": "temperature_2m,precipitation",
        }
        response = session.get(url, params=params, timeout=timeout)
        # لو الموقع رجع خطأ نوقف هذه المدينة برفع الاستثناء للأعلى
        response.raise_for_status()
        payload = response.json()
        current = payload.get("current") or {}
        rows.append(
            {
                "city": hub.city,
                "temperature_c": current.get("temperature_2m"),
                "precipitation_mm": current.get("precipitation") or 0.0,
            }
        )
    return pd.DataFrame(rows)
