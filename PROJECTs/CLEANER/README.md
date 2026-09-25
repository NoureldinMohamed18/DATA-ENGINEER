# Sales Data Cleaner & Analyzer

A small ETL-style script that takes a messy, real-world-style sales CSV export
and turns it into a clean dataset plus a summary analytical report.

## The problem

Real sales exports are rarely clean. The sample raw file used here
(`data/raw_sales.csv`) intentionally contains the kind of issues you'd find in
an actual business export:

- **Duplicate rows** (same order appearing twice)
- **Missing values** in `quantity`, `unit_price`, and `region`
- **Inconsistent date formats** (`2026-01-15`, `15/01/2026`, `2026/01/15` all appear)
- **Prices stored as text** with currency symbols (`$123.45` vs `123.45`)
- **Inconsistent casing** in categorical columns (`CAIRO`, `cairo`, `Cairo`)

## What the script does

`clean_and_analyze.py` runs a 5-step pipeline:

| Step | What happens |
|---|---|
| **Load** | Read the raw CSV as strings (avoid pandas guessing wrong types) |
| **Inspect** | Print a data-quality report — duplicates found, missing values per column |
| **Clean** | Normalize text casing, parse mixed date formats, strip currency symbols from prices, remove duplicates, handle missing values |
| **Analyze** | Aggregate total revenue by product, by month, and by region |
| **Export** | Save the clean dataset and a text summary report to `output/` |

### Missing value strategy

- Missing `region` → filled with `"Unknown"` (safe default for a categorical field)
- Missing `quantity`, `unit_price`, or `order_date` → row is **dropped**, since these
  are required to compute revenue and can't be safely guessed.

## How to run it

```bash
pip install -r requirements.txt

# 1. Generate a fresh sample of dirty data (optional — a sample is already included)
python generate_dirty_data.py

# 2. Run the cleaning + analysis pipeline
python clean_and_analyze.py
```

Output files are written to `output/`:
- `clean_sales.csv` — the cleaned dataset
- `sales_report.txt` — revenue summary by product / month / region

## Before → After

**Before (raw_sales.csv):**
```
order_id,customer_id,product,region,order_date,quantity,unit_price
ORD0001,C1023,Mouse,CAIRO,15/01/2026,,$45.99
ORD0002,C1010,Laptop,cairo,2026-01-15,3,899.5
ORD0002,C1010,Laptop,cairo,2026-01-15,3,899.5    <- duplicate
```

**After (clean_sales.csv):**
```
order_id,customer_id,product,region,order_date,quantity,unit_price,total_amount,order_month
ORD0002,C1010,Laptop,Cairo,2026-01-15,3,899.5,2698.5,2026-01
```
(The row with missing quantity was dropped; the duplicate was removed;
region casing was standardized to "Cairo".)

## Skills demonstrated

- Pandas fundamentals (reading/writing CSV, dtype handling)
- Data cleaning: missing values, duplicates, inconsistent formats
- `groupby` aggregation across multiple dimensions
- Writing a clear, reproducible, step-by-step data pipeline in plain Python

## Project structure

```
project1_sales_cleaner/
├── generate_dirty_data.py   # creates the sample messy dataset
├── clean_and_analyze.py     # main pipeline: load -> inspect -> clean -> analyze -> export
├── data/
│   └── raw_sales.csv        # sample raw input
├── output/
│   ├── clean_sales.csv      # cleaned output
│   └── sales_report.txt     # summary report
└── requirements.txt
```
