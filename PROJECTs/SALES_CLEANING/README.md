# 📊 Project 1: Sales Data Cleaning & Analysis

> **Level:** Beginner | **Skills:** Pandas, SQLite, SQL, Data Cleaning

## 🎯 Overview

This project demonstrates the complete data preprocessing workflow for a sales dataset. It covers loading raw CSV data, cleaning it with Pandas, storing it in SQLite, and running analytical SQL queries.

## 📁 Project Structure

```
01_sales_data_cleaning/
├── data/
│   ├── sales_raw.csv       # Raw input data
│   ├── sales_clean.csv     # Cleaned output data
│   └── sales.db            # SQLite database
├── src/
│   ├── clean_data.py       # Data cleaning pipeline
│   └── sql_analysis.py     # SQL analytical queries
└── README.md
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install pandas
```

### 2. Run the Cleaning Pipeline
```bash
cd src
python clean_data.py
```

**Output:**
```
==================================================
SALES DATA CLEANING PIPELINE
==================================================
[LOAD] Loaded 25 rows from ..\data\sales_raw.csv
[CLEAN] Starting data cleaning...
[CLEAN] Removed 0 duplicate rows
[CLEAN] Cleaning complete. 25 rows remain.
[SAVE] Saved cleaned data to ..\data\sales_clean.csv
[SAVE] Saved to SQLite: ..\data\sales.db

[DONE] Pipeline completed successfully!
```

### 3. Run SQL Analysis
```bash
python sql_analysis.py
```

## 🔧 What the Code Does

### `clean_data.py`
| Step | Action | Purpose |
|------|--------|---------|
| 1 | `drop_duplicates()` | Remove duplicate records |
| 2 | `fillna()` | Handle missing values |
| 3 | `pd.to_datetime()` | Convert dates to proper format |
| 4 | Create `Year`, `Month`, `Total`, `Net_Amount` | Derive new features |
| 5 | `str.strip().str.title()` | Standardize text formatting |
| 6 | Save to CSV + SQLite | Persist cleaned data |

### `sql_analysis.py`
Includes 6 analytical queries:
1. **Top Products by Revenue** — Identify best-selling items
2. **Sales by Category** — Compare Electronics, Furniture, Stationery
3. **Monthly Trend** — Track sales over time
4. **Top Customers** — Find VIP customers
5. **Payment Analysis** — Compare Cash vs Credit Card
6. **City Performance** — Geographic insights

## 📈 Sample Results

**Top Products:**
| Product | Total_Revenue |
|---------|---------------|
| Laptop | 2,160.90 |
| Sofa | 640.00 |
| Desk | 225.00 |

**Category Summary:**
| Category | Orders | Total_Revenue |
|----------|--------|---------------|
| Electronics | 14 | 5,893.37 |
| Furniture | 5 | 1,467.50 |
| Stationery | 6 | 376.50 |

## 🎓 Key Learnings
- Using `pd.to_datetime()` for date handling
- Creating derived columns for business metrics
- SQLite as a lightweight database for small projects
- Writing GROUP BY queries for aggregation

## 🛠️ Tech Stack
- Python 3.8+
- Pandas
- SQLite3 (built-in)
