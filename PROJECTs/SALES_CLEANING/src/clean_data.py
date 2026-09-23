"""
Sales Data Cleaning Script
============================
This script cleans raw sales data using Pandas and stores it in SQLite.
"""

import pandas as pd 
import sqlite3
import os
from datetime import datetime

"""بتعمل الملفات اللي هتخرن فيها الداتا 
    """
DATA_DIR=os.path.join(os.path.dirname(__file__),'..','data') 
RAW_PATH = os.path.join(DATA_DIR, 'sales_raw.csv')
CLEAN_PATH = os.path.join(DATA_DIR, 'sales_clean.csv')
DB_PATH = os.path.join(DATA_DIR, 'sales.db')

print("=== بداية تشغيل السكريبت ===")
print(f"مسار مجلد البيانات: {os.path.abspath(DATA_DIR)}")

# تأكد هل ملف البيانات خام موجود فعلاً؟
if os.path.exists(RAW_PATH):
    print("تم العثور على ملف البيانات الخام!")
else:
    print("تحذير: ملف البيانات الخام غير موجود في المسار المحدد!")

def load_raw_data(path:str)->pd.DataFrame:
    df=pd.read_csv(path)
    print(f"[LOAD] Loaded {len(df)} rows from {path}")
    return df

def clean_data(df:pd.DataFrame)->pd.DataFrame:
    """
    Clean sales data
    1.Remove duplictaes
    2.Handle missing data
    3.convert data type
    4.create derived columns
    5.standasdize text columns
    """
    
    print("[CLEAN] Starting data cleaning...")
    before=len(df)
    df=df.drop_duplicates()
    print(f"[CLEAN] Removed {before - len(df)} duplicate rows")
    
    df['Discount']=df['Discount'].fillna(0)
    df['Payment_Method']=df['Payment_Method'].fillna('Unknown')
    df['Order_Date']=pd.to_datetime(df['Order_Date'],errors='coerce')
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    df['Discount'] = pd.to_numeric(df['Discount'], errors='coerce')
    df['Year']=df['Order_Date'].dt.year
    df['Month'] = df['Order_Date'].dt.month
    df['Month_Name'] = df['Order_Date'].dt.strftime('%B')
    df['Total'] = df['Price'] * df['Quantity']
    df['Net_Amount'] = df['Total'] * (1 - df['Discount'])
    df['Product'] = df['Product'].str.strip().str.title()
    df['Category'] = df['Category'].str.strip().str.title()
    df['City'] = df['City'].str.strip().str.title()
    df['Customer_Name'] = df['Customer_Name'].str.strip().str.title()
    print(f"[CLEAN] Cleaning complete. {len(df)} rows remain.")
    return df

def save_to_csv(df:pd.DataFrame,path:str):
    df.to_csv(path,index=False,encoding='utf-8')
    print(f"[SAVE] Saved cleaned data to {path}")
    
def save_to_sqlite3(df:pd.DataFrame,db_path:str):
    conn=sqlite3.connect(db_path)
    df.to_sql('sales',conn,if_exists='replace',index=False)
    conn.close()
    print(f"[SAVE] Saved to SQLite: {db_path}")
    
def main():
    print("=" * 50)
    print("SALES DATA CLEANING PIPELINE")
    print("=" * 50)
    df=load_raw_data(RAW_PATH)
    df_clean=clean_data(df)
    save_to_csv(df_clean,CLEAN_PATH)
    save_to_sqlite3(df_clean,DB_PATH)
    print("\n[DONE] Pipeline completed successfully!")
    return df_clean
if __name__=="__main__":
    main()
    