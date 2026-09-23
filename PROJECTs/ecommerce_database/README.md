# 🛒 Project 2: E-Commerce Database System

> **Level:** Beginner-Intermediate | **Skills:** SQL, Database Design, ER Modeling, Views, CTEs, Window Functions

## 🎯 Overview

A complete relational database design and implementation for an online store. This project covers everything from schema creation to advanced analytical queries.

## 📁 Project Structure

```
02_ecommerce_database/
├── schema/
│   └── create_tables.sql    # Full DDL + sample data
├── src/
│   └── queries.sql          # 20+ analytical queries
└── README.md
```

## 🚀 Quick Start

### 1. Setup Database
```bash
# Using SQLite (no installation needed!)
sqlite3 ecommerce.db < schema/create_tables.sql
```

### 2. Run Queries
```bash
sqlite3 ecommerce.db < src/queries.sql
```

Or use **DB Browser for SQLite** (GUI) to explore interactively.

## 🗃️ Database Schema (ER Diagram)

```
    ┌─────────────┐       ┌─────────────┐
    │  customers  │       │  categories │
    ├─────────────┤       ├─────────────┤
    │ customer_id │       │ category_id │
    │ first_name  │       │category_name│
    │ last_name   │       │ description │
    │ email       │       └──────┬──────┘
    │ phone       │              │
    │ city        │              │
    └──────┬──────┘              │
           │                     │
           │ 1:N                 │ 1:N
           ▼                     ▼
    ┌─────────────┐       ┌─────────────┐
    │   orders    │       │   products  │
    ├─────────────┤       ├─────────────┤
    │  order_id   │       │ product_id  │
    │ customer_id │       │ product_name│
    │ order_date  │       │ category_id │
    │   status    │       │    price    │
    │total_amount │       │stock_quantity
    └──────┬──────┘       └──────┬──────┘
           │                     │
           │ 1:N                 │ 1:N
           ▼                     ▼
    ┌─────────────┐       ┌─────────────┐
    │  payments   │       │ order_items │
    ├─────────────┤       ├─────────────┤
    │ payment_id  │       │  item_id    │
    │  order_id   │       │  order_id   │
    │   amount    │       │ product_id  │
    │payment_method│      │  quantity   │
    │   status    │       │ unit_price  │
    └─────────────┘       │  discount   │
                          │ line_total  │
                          └─────────────┘
```

## 🔍 Query Categories

### 1️⃣ JOINs
| Query | Type | Description |
|-------|------|-------------|
| 1.1 | INNER JOIN | Orders with customer names |
| 1.2 | Multi-table JOIN | Full order details with products & categories |
| 1.3 | LEFT JOIN | All customers (even with 0 orders) |

### 2️⃣ Subqueries
| Query | Type | Description |
|-------|------|-------------|
| 2.1 | Correlated | Customers above average spending |
| 2.2 | Non-correlated | Products above category average price |
| 2.3 | Scalar | Most popular product by quantity |

### 3️⃣ CTEs (Common Table Expressions)
| Query | Description |
|-------|-------------|
| 3.1 | Monthly revenue with 3-month moving average |
| 3.2 | Customer segmentation (VIP, Loyal, Regular, Inactive) |

### 4️⃣ Window Functions
| Query | Function | Description |
|-------|----------|-------------|
| 4.1 | RANK() | Product price ranking within category |
| 4.2 | SUM() OVER | Running total per customer |
| 4.3 | AVG() OVER | Compare order to customer average |

### 5️⃣ Views
| View | Purpose |
|------|---------|
| `vw_order_details` | Complete order information in one query |
| `vw_daily_sales` | Daily aggregated sales metrics |

## 📊 Sample Results

**Customer Segmentation:**
| customer_name | total_spent | segment |
|---------------|-------------|---------|
| Layla Youssef | 200.00 | VIP |
| Omar Khaled | 245.00 | VIP |
| Mohamed Adel | 120.00 | Loyal |

**Monthly Revenue:**
| month | order_count | revenue | moving_avg_3m |
|-------|-------------|---------|---------------|
| 2024-01 | 5 | 470.00 | 470.00 |
| 2024-02 | 4 | 350.00 | 410.00 |
| 2024-03 | 1 | 90.00 | 303.33 |

## 🎓 Key Learnings
- Designing normalized relational schemas (3NF)
- Choosing appropriate data types and constraints
- Using FOREIGN KEY with ON DELETE/UPDATE actions
- Writing complex multi-table JOINs
- Leveraging CTEs for readable complex queries
- Applying Window Functions for advanced analytics
- Creating Views to simplify reporting

## 🛠️ Tech Stack
- SQLite 3
- SQL (DDL, DML, DQL)
