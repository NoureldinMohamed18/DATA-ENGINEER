# ⚙️ Project 5: Apache Airflow Pipeline

> **Level:** Advanced | **Skills:** Airflow, DAGs, Docker, Scheduling, XCom

## 🎯 Overview

A production-ready data pipeline using Apache Airflow. Fetches daily weather data from a free API, transforms it, loads it into SQLite, and sends a confirmation email.

## 📁 Structure

```
05_airflow_pipeline/
├── dags/
│   └── weather_pipeline.py    # DAG definition
├── data/                      # Shared data volume
├── docker-compose.yml         # Airflow + Postgres setup
└── README.md
```

## 🚀 Quick Start

### 1. Install Docker & Docker Compose

### 2. Start Airflow
```bash
docker-compose up -d
```

### 3. Access Airflow UI
Open: http://localhost:8080  
Login: `admin` / `admin`

### 4. Trigger the DAG
- Find `weather_data_pipeline` in the UI
- Click the "Play" button to trigger manually
- Or wait for the daily schedule (`@daily`)

## 🔧 DAG Tasks

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Extract   │───►│  Transform  │───►│    Load     │───►│   Validate  │───►│    Email    │
│   Weather   │    │    Data     │    │   to SQLite │    │    Data     │    │   Notify    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

| Task | Operator | Purpose |
|------|----------|---------|
| `extract_weather` | PythonOperator | Call Open-Meteo API |
| `transform_weather` | PythonOperator | Structure JSON into records |
| `load_weather` | PythonOperator | Insert into SQLite with UPSERT |
| `validate_data` | PythonOperator | Check counts and latest date |
| `send_success_email` | EmailOperator | Notify on success |

## 🎓 Key Learnings

- DAG = Directed Acyclic Graph (no cycles allowed)
- XCom = Cross-communication between tasks
- Idempotency = Same result whether run once or many times
- Retries & timeouts for fault tolerance
- Docker volumes for persistence between containers

## 🛠️ Tech Stack
- Apache Airflow 2.8
- PostgreSQL (metadata DB)
- Docker & Docker Compose
- SQLite (data warehouse)
- Open-Meteo API (free weather data)
