from fastapi import FastAPI
import sqlite3
from src.config import load_settings, resolve_path

settings = load_settings()
DB_PATH = resolve_path(settings["database"]["path"])
app = FastAPI(title="Delivery Weather API")


def query(sql: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/health")
def health():
    return {"status": "ok", "db_exists": DB_PATH.exists()}


@app.get("/metrics/delay-by-city")
def delay_by_city():
    return query("SELECT * FROM vw_delay_by_city ORDER BY delay_pct DESC")
