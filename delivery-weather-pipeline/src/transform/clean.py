from pathlib import Path
import pandas as pd


def _reject(df: pd.DataFrame, folder: Path, reason: str) -> None:
    # جدول فاضي يعني مفيش حاجة تتكتب
    if df.empty:
        return
    folder.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    out["reject_reason"] = reason
    path = folder / "rejected_rows.csv"
    # الرأس مرة واحدة فقط لو الملف جديد
    out.to_csv(path, mode="a", index=False, header=not path.exists())


def parse_dates(series: pd.Series) -> pd.Series:
    # نبدأ بكل القيم غير صالحة ثم نملأ اللي تنجح صيغته
    result = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    # الترتيب مهم: السنة-شهر-يوم أولاً حتى لا يتكسر 2024-06-18
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        still_empty = series.notna() & result.isna()
        parsed = pd.to_datetime(series[still_empty], format=fmt, errors="coerce")
        good = parsed.notna()
        result.loc[parsed.index[good]] = parsed[good]
    return result


def clean_hubs(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    df["hub_id"] = df["hub_id"].astype(str).str.strip()
    df["city"] = df["city"].astype(str).str.strip().str.title()
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    return df


def clean_shipments(raw: pd.DataFrame, rejected_dir: Path, min_w: float, max_w: float) -> pd.DataFrame:
    df = raw.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    df["shipment_id"] = df["shipment_id"].astype(str).str.strip()
    df["hub_id"] = df["hub_id"].astype(str).str.strip()
    df["service_type"] = df["service_type"].astype(str).str.strip().str.lower()
    df["ship_date"] = parse_dates(df["ship_date"])
    df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce")

    bad_date = df[df["ship_date"].isna()]
    _reject(bad_date, rejected_dir, "invalid_date")
    df = df[df["ship_date"].notna()]

    bad_w = df[(df["weight_kg"].isna()) | (df["weight_kg"] < min_w) | (df["weight_kg"] > max_w)]
    _reject(bad_w, rejected_dir, "invalid_weight")
    df = df.drop(bad_w.index)

    dups = df.duplicated(subset=["shipment_id"], keep="last")
    _reject(df[dups], rejected_dir, "duplicate_id")
    df = df[~dups]
    return df.reset_index(drop=True)


def add_weather_and_risk(shipments: pd.DataFrame, hubs: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    # نربط الشحنة بالمدينة عن طريق المحور ثم بالطقس
    df = shipments.merge(hubs[["hub_id", "city"]], on="hub_id", how="left")
    df = df.merge(weather, on="city", how="left")
    # مطر مع خدمة سريعة = خطر تأخير 1 وإلا 0
    rain = df["precipitation_mm"].fillna(0) > 0.2
    express = df["service_type"] == "express"
    df["delay_risk"] = (rain & express).astype(int)
    return df
