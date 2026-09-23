"""
SQL Analysis Script
===================
Run analytical SQL queries on the cleaned sales database.
"""
import sqlite3
import pandas as pd
import os
DB_PATH=os.path.join(os.path.dirname(__file__), '..', 'data', 'sales.db')

def run_query(query:str,description:str)->pd.DataFrame:
    conn=sqlite3.connect(DB_PATH)
    print(f"\n{'='*60}")
    print(f"QUERY: {description}")
    print(f"{'='*60}")
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))
    conn.close()
    return df

def main():
    print("SALES DATA ANALYSIS - SQL QUERIES")
    
    run_query("""
        SELECT Product,SUM(Net_amount) as Revenue
        From sales
        GROUP BY Product
        ORDER BY Revenue DESC
        limit 10""","TOP 10 PRODUCTS BY Revenue")
    
    run_query("""SELECT
            category,COUNT(*) AS Order_count,
            SUM(QUANTITY) as Total_Quantity,
            ROUND(SUM(Net_Amount), 2) as Total_Revenue,
            ROUND(AVG(Net_Amount), 2) as Avg_Order_Value
        FROM sales
        GROUP BY category
        ORDER BY Total_Revenue DESC
        ""","Sales Summary by Category")
    
    run_query("""
        SELECT 
            Year,
            Month,
            Month_Name,
            COUNT(*) as Orders,
            ROUND(SUM(Net_Amount), 2) as Revenue
        FROM sales
        GROUP BY Year, Month
        ORDER BY Year, Month
    """, "Monthly Sales Trend")
    
    run_query("""
        SELECT 
            Customer_Name,
            City,
            COUNT(*) as Orders,
            ROUND(SUM(Net_Amount), 2) as Total_Spent
        FROM sales
        GROUP BY Customer_Name
        ORDER BY Total_Spent DESC
        LIMIT 5
    """, "Top 5 Customers by Spending")

    run_query("""
        SELECT 
            Payment_Method,
            COUNT(*) as Count,
            ROUND(SUM(Net_Amount), 2) as Revenue,
            ROUND(AVG(Discount), 2) as Avg_Discount
        FROM sales
        GROUP BY Payment_Method
    """, "Payment Method Analysis")

    run_query("""
        SELECT 
            City,
            COUNT(DISTINCT Customer_Name) as Unique_Customers,
            COUNT(*) as Orders,
            ROUND(SUM(Net_Amount), 2) as Revenue
        FROM sales
        GROUP BY City
        ORDER BY Revenue DESC
    """, "Performance by City")
    
    
if __name__ == "__main__":
    main()