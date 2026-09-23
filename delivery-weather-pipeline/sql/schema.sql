CREATE TABLE IF NOT EXISTS dim_date (
    date_key   INTEGER PRIMARY KEY,
    full_date  TEXT NOT NULL UNIQUE,
    year       INTEGER NOT NULL,
    month      INTEGER NOT NULL,
    weekday    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_hub (
    hub_key   INTEGER PRIMARY KEY AUTOINCREMENT,
    hub_id    TEXT NOT NULL UNIQUE,
    hub_name  TEXT,
    city      TEXT NOT NULL,
    latitude  REAL NOT NULL,
    longitude REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_service (
    service_key INTEGER PRIMARY KEY AUTOINCREMENT,
    service_type TEXT NOT NULL UNIQUE
);

-- سطر واحد = شحنة واحدة
CREATE TABLE IF NOT EXISTS fact_shipment (
    shipment_key      INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id       TEXT NOT NULL UNIQUE,
    date_key          INTEGER NOT NULL REFERENCES dim_date(date_key),
    hub_key           INTEGER NOT NULL REFERENCES dim_hub(hub_key),
    service_key       INTEGER NOT NULL REFERENCES dim_service(service_key),
    weight_kg         REAL NOT NULL,
    temperature_c     REAL,
    precipitation_mm  REAL,
    delay_risk        INTEGER NOT NULL,
    loaded_at         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS etl_watermark (
    pipeline_name TEXT PRIMARY KEY,
    last_ship_date TEXT,
    updated_at TEXT NOT NULL
);

DROP VIEW IF EXISTS vw_delay_by_city;
CREATE VIEW vw_delay_by_city AS
SELECT
    h.city,
    COUNT(*) AS shipments,
    SUM(f.delay_risk) AS delay_flags,
    ROUND(100.0 * SUM(f.delay_risk) / COUNT(*), 1) AS delay_pct,
    RANK() OVER (ORDER BY SUM(f.delay_risk) * 1.0 / COUNT(*) DESC) AS risk_rank
FROM fact_shipment f
JOIN dim_hub h ON h.hub_key = f.hub_key
GROUP BY h.city;
