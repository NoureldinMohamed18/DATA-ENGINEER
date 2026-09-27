"""
generate_weather_data.py
--------------------------
Simulates a second, independent data source: daily weather data per region,
as if pulled from a weather API. This mirrors the "umbrella sales vs weather"
example from the Data Pipeline material — combining sales data with an
unrelated external data source to find a business insight.

Run once to create data/weather.csv.
"""

import csv
import random
from datetime import date, timedelta

random.seed(7)

regions = ["Cairo", "Alexandria", "Giza", "Mansoura", "Aswan"]
start_date = date(2026, 1, 1)

rows = []
for day_offset in range(28):
    current_date = start_date + timedelta(days=day_offset)
    for region in regions:
        # Aswan is hotter/drier; Alexandria is cooler/rainier -- gives the data some real signal
        base_temp = {"Cairo": 20, "Alexandria": 16, "Giza": 20, "Mansoura": 18, "Aswan": 26}[region]
        temp = round(base_temp + random.uniform(-3, 3), 1)
        rained = random.random() < (0.35 if region == "Alexandria" else 0.1)

        rows.append({
            "date": current_date.isoformat(),
            "region": region,
            "temperature_c": temp,
            "rained": int(rained),
        })

with open("data/weather.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} weather records -> data/weather.csv")
