# نقطة التشغيل: سحب ثم تحويل ثم تحميل ثم تقرير
from datetime import datetime, timezone
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.config import load_settings, resolve_path, PROJECT_ROOT
from src.logging_setup import setup_logging
from src.extract.sources import extract_csv, extract_weather
from src.transform.clean import clean_hubs, clean_shipments, add_weather_and_risk
from src.load.warehouse import (
    connect,
    init_schema,
    seed_dates,
    upsert_hubs,
    get_watermark,
    set_watermark,
    load_facts,
)
from src.serve.reports import write_html
import pandas as pd


def main() -> None:
    settings = load_settings()
    logger = setup_logging(resolve_path(settings["paths"]["logs"]))
    raw_dir = resolve_path(settings["paths"]["raw"])
    staging = resolve_path(settings["paths"]["staging"])
    rejected = resolve_path(settings["paths"]["rejected"])
    staging.mkdir(parents=True, exist_ok=True)
    rejected.mkdir(parents=True, exist_ok=True)

    logger.info("بدأ بايبلاين التوصيل")
    hubs_raw = extract_csv(raw_dir, "hubs.csv")
    ships_raw = extract_csv(raw_dir, "shipments.csv")
    hubs = clean_hubs(hubs_raw)

    try:
        weather = extract_weather(
            settings["extract"]["weather_url"],
            hubs,
            settings["extract"]["request_timeout_seconds"],
        )
        logger.info("تم سحب الطقس لـ %s مدن", len(weather))
    except Exception as exc:
        logger.warning("الطقس فشل (%s). نكمل بصفر مطر", exc)
        weather = pd.DataFrame(
            {"city": hubs["city"], "temperature_c": None, "precipitation_mm": 0.0}
        )

    weather.to_csv(staging / "weather.csv", index=False)
    q = settings["quality"]
    ships = clean_shipments(ships_raw, rejected, q["min_weight_kg"], q["max_weight_kg"])
    logger.info("شحنات صالحة: %s", len(ships))
    if ships.empty:
        raise ValueError("لا توجد شحنات صالحة بعد التنظيف")

    enriched = add_weather_and_risk(ships, hubs, weather)
    conn = connect(resolve_path(settings["database"]["path"]))
    init_schema(conn, PROJECT_ROOT / "sql" / "schema.sql")
    seed_dates(conn, enriched["ship_date"].min(), enriched["ship_date"].max())
    upsert_hubs(conn, hubs)

    watermark = get_watermark(conn)
    batch = enriched
    if watermark:
        batch = enriched[enriched["ship_date"] > watermark]
        logger.info("تحميل تدريجي. العلامة=%s الصفوف=%s", watermark, len(batch))

    inserted = load_facts(conn, batch)
    set_watermark(conn, str(enriched["ship_date"].max()))
    write_html(conn, resolve_path(settings["paths"]["reports"]))
    conn.close()
    logger.info("انتهى. صفوف جديدة=%s", inserted)
    logger.info("التقرير reports/dashboard.html — الواجهة python run_api.py")


if __name__ == "__main__":
    main()
