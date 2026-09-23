# 🏭 Project 4: Data Warehouse + ETL Pipeline

> **Level:** Intermediate | **Skills:** Star Schema, ETL, OLAP, Pandas, SQLite

## 🎯 Overview

Builds a mini Data Warehouse using the Star Schema model. Extracts data from CSV and JSON sources, transforms it with Pandas, and loads it into dimensional models for OLAP analysis.

## 📁 Structure

```
04_data_warehouse_etl/
├── data/
│   ├── source1.csv          # Transaction data (CSV)
│   ├── source2.json         # Transaction data (JSON)
│   └── warehouse.db         # SQLite Data Warehouse
└── src/
    └── etl_pipeline.py      # Full ETL script
```

## 🚀 Quick Start

```bash
cd src
python etl_pipeline.py
```

## ⭐ Star Schema Design

```
                    dim_date
                   ┌─────────┐
                   │ date_id │
                   │  year   │
                   │  month  │
                   │  day    │
                   └────┬────┘
                        │
    dim_product         │         dim_customer
   ┌───────────┐        │        ┌───────────┐
   │product_id │◄───────┼───────►│customer_id│
   │   name    │        │        │   name    │
   │ category  │        │        │   city    │
   └───────────┘        │        └───────────┘
                        │
                   ┌────┴────┐
                   │fact_sales│
                   │ sale_id  │
                   │ date_id  │
                   │product_id│
                   │customer_ │
                   │ quantity │
                   │net_amount│
                   └─────────┘
```

## 🔧 ETL Steps

| Phase | Action |
|-------|--------|
| **Extract** | Read CSV + JSON, combine with `pd.concat` |
| **Transform** | Parse dates, calculate measures, standardize text |
| **Load** | Populate dimensions first, then facts with surrogate keys |

## 📊 OLAP Operations Demonstrated

- **Roll-up:** Category-level aggregation
- **Drill-down:** Category + Month detail
- **Slice:** Filter Electronics category
- **Top-N:** Highest spending customers

## 🎓 Key Learnings

- Designing Star Schema vs Snowflake Schema
- Surrogate keys vs Natural keys
- ETL vs ELT trade-offs
- OLAP operations for business intelligence
