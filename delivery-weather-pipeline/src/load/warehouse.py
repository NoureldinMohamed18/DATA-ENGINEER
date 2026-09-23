from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import sqlite3
import pandas as pd


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    # سكليت لا يفحص المفاتيح الأجنبية إلا بعد هذا الأمر
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection, sql_path: Path) -> None:
    conn.executescript(sql_path.read_text(encoding="utf-8"))
    conn.commit()


def date_key(value) -> int:
    # 2024-06-01 يصبح 20240601
    return int(pd.Timestamp(value).strftime("%Y%m%d"))


def seed_dates(conn: sqlite3.Connection, start, end) -> None:
    start = pd.Timestamp(start).date()
    end = pd.Timestamp(end).date()
    rows = []
    day = start
    while day <= end:
        rows.append(
            (
                int(day.strftime("%Y%m%d")),
                day.isoformat(),
                day.year,
                day.month,
                day.strftime("%A"),
            )
        )
        day += timedelta(days=1)
    conn.executemany(
        """
        INSERT OR IGNORE INTO dim_date (date_key, full_date, year, month, weekday)
        VALUES (?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()


def upsert_hubs(conn: sqlite3.Connection, hubs: pd.DataFrame) -> None:
    for row in hubs.itertuples(index=False):
        conn.execute(
            """
            INSERT INTO dim_hub (hub_id, hub_name, city, latitude, longitude)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(hub_id) DO UPDATE SET
                hub_name = excluded.hub_name,
                city = excluded.city,
                latitude = excluded.latitude,
                longitude = excluded.longitude
            """,
            (row.hub_id, row.hub_name, row.city, float(row.latitude), float(row.longitude)),
        )
    conn.commit()


def upsert_service(conn: sqlite3.Connection, service_type: str) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO dim_service (service_type) VALUES (?)",
        (service_type,),
    )
    row = conn.execute(
        "SELECT service_key FROM dim_service WHERE service_type = ?",
        (service_type,),
    ).fetchone()
    return row["service_key"]


def get_watermark(conn: sqlite3.Connection) -> Optional[str]:
    row = conn.execute(
        "SELECT last_ship_date FROM etl_watermark WHERE pipeline_name = 'shipments'"
    ).fetchone()
    return row["last_ship_date"] if row else None


def set_watermark(conn: sqlite3.Connection, last_date: str) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute(
        """
        INSERT INTO etl_watermark (pipeline_name, last_ship_date, updated_at)
        VALUES ('shipments', ?, ?)
        ON CONFLICT(pipeline_name) DO UPDATE SET
            last_ship_date = excluded.last_ship_date,
            updated_at = excluded.updated_at
        """,
        (last_date, now),
    )
    conn.commit()


def load_facts(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    inserted = 0
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for row in df.itertuples(index=False):
        hub = conn.execute(
            "SELECT hub_key FROM dim_hub WHERE hub_id = ?",
            (row.hub_id,),
        ).fetchone()
        if hub is None:
            continue
        service_key = upsert_service(conn, row.service_type)
        conn.execute(
            """
            INSERT OR IGNORE INTO fact_shipment
            (shipment_id, date_key, hub_key, service_key, weight_kg,
             temperature_c, precipitation_mm, delay_risk, loaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.shipment_id,
                date_key(row.ship_date),
                hub["hub_key"],
                service_key,
                float(row.weight_kg),
                None if pd.isna(row.temperature_c) else float(row.temperature_c),
                None if pd.isna(row.precipitation_mm) else float(row.precipitation_mm),
                int(row.delay_risk),
                now,
            ),
        )
        inserted += conn.execute("SELECT changes()").fetchone()[0]
    conn.commit()
    return inserted
