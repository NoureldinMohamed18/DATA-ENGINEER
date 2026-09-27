# Mini Data Warehouse with Orchestrated Pipeline

The final project: combines **two independent data sources** (sales +
weather), models them as a **Star Schema**, and runs the whole pipeline
through a small **DAG execution engine** built from scratch — mirroring
the exact "umbrella sales vs weather" example and DAG algorithm from the
Data Pipeline course material.

## The business question

Does weather affect sales? To answer that, we need data from two unrelated
sources joined together:

- **Sales data** (from Project 1's cleaned output): orders by region and product
- **Weather data** (simulated, as if pulled from a weather API): daily temperature
  and rainfall by region

Neither source depends on the other to be extracted — they're independent,
which is exactly the scenario the course material uses to justify DAG-based
pipelines over plain sequential scripts.

## Pipeline as a DAG

```
extract_sales -----\
                     >---  join_data  --->  load_warehouse
extract_weather ---/
```

`extract_sales` and `extract_weather` have no dependency on each other, so a
real orchestrator (like Airflow) could run them in parallel. `join_data` can
only start once **both** extracts finish. `load_warehouse` can only start
once the join is done.

This dependency graph isn't just described in the README — it's **enforced
in code** by [`dag_engine.py`](dag_engine.py), a small DAG execution engine
implementing the loop-based algorithm from the course material:

1. Find every task whose dependencies are all completed → add it to the "ready" queue
2. Run every ready task, mark it completed
3. Repeat until every task is completed
4. Fail loudly if no task is ever ready (a cycle/deadlock)

This is a simplified, single-process stand-in for what Apache Airflow does
at scale. Running `run_pipeline.py` prints each loop of the algorithm so you
can see the dependency resolution happen live:

```
[DAG] Loop 1: ready tasks -> ['extract_sales', 'extract_weather']
[DAG] Loop 2: ready tasks -> ['join_data']
[DAG] Loop 3: ready tasks -> ['load_warehouse']
```

## Star Schema design

```
              dim_date            dim_region           dim_product
           --------------        -------------        --------------
           date_key (PK)         region_id (PK)        product_id (PK)
           day, month, year      region_name           product_name
                 \                    |                     /
                  \                   |                    /
                   \                  v                   /
                    ------------ fact_sales ---------------
                                 --------------
                                 sale_id (PK)
                                 date_key    (FK)
                                 region_id   (FK)
                                 product_id  (FK)
                                 quantity
                                 total_amount
                                 temperature_c   <- enriched from weather source
                                 rained          <- enriched from weather source
```

**Why a Star Schema and not just one big joined table?**
- Dimension tables (`dim_date`, `dim_region`, `dim_product`) store descriptive
  attributes once, instead of repeating region/product names on every fact row.
- The fact table (`fact_sales`) stores only measurable numbers and foreign keys.
- This shape is what BI tools and analysts expect when querying a warehouse —
  it's the same pattern used in real company data warehouses, just at small scale.

See [`sql/star_schema.sql`](sql/star_schema.sql) for the full DDL.

## How to run it

```bash
pip install -r requirements.txt

# 1. Generate the weather data source (a sales.csv is already included, copied
#    from Project 1's cleaned output)
python generate_weather_data.py

# 2. Run the full DAG-orchestrated pipeline
python run_pipeline.py
```

This produces `warehouse.db`, a SQLite database with the star schema
populated and ready to query.

## Answering the business question

Run the queries in [`sql/analysis_queries.sql`](sql/analysis_queries.sql):

```bash
sqlite3 warehouse.db < sql/analysis_queries.sql
```

Included queries:
1. **Revenue vs. average temperature vs. rainy days, per region** — the core question
2. **Average order value on rainy days vs. dry days**
3. **Revenue by product, broken down by month**
4. **Average sale value on hot days (≥22°C) vs. cooler days, per region**

## Skills demonstrated

- Designing and building a Star Schema (fact + dimension tables) from scratch
- Combining two independent data sources with a `merge`/`join` step
- Building a DAG-based pipeline orchestrator from first principles (not just using Airflow as a black box)
- Detecting and failing on circular dependencies (cycle detection)
- Writing analytical SQL queries against a warehouse to answer a real business question
- Structuring a multi-source ETL project cleanly: extract, join, load as distinct, testable functions

## Project structure

```
project5_mini_data_warehouse/
├── generate_weather_data.py   # creates the second (weather) data source
├── dag_engine.py               # small reusable DAG execution engine
├── run_pipeline.py             # defines the pipeline's tasks & dependencies, runs the DAG
├── data/
│   ├── sales.csv                # from Project 1's cleaned output
│   ├── weather.csv               # generated weather data
│   └── joined.csv                 # intermediate joined dataset
├── sql/
│   ├── star_schema.sql            # fact + dimension table definitions
│   └── analysis_queries.sql       # business-question queries
├── warehouse.db                  # generated SQLite data warehouse
└── requirements.txt
```

## What's next (beyond this project)

This DAG engine is intentionally simplified — it runs everything in one
process with in-memory state. A real next step would be running the same
task graph in **actual Apache Airflow**: each function here becomes an
Airflow `PythonOperator`, `depends_on` becomes `>>` between tasks, and
Airflow's scheduler + web UI replace the manual loop in `dag_engine.py`.
