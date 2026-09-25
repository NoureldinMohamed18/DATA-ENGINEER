"""
clean_and_analyze.py
---------------------
Project 1: Sales Data Cleaner & Analyzer

Takes a messy sales CSV export and produces a clean dataset plus a
summary analytical report (sales by product, by month, by region).

Pipeline steps:
    1. Load          -> read the raw CSV
    2. Inspect        -> report data quality issues found
    3. Clean          -> fix types, handle missing values, remove duplicates
    4. Analyze        -> aggregate sales by product / month / region
    5. Export         -> save the clean dataset + a summary report
"""
import pandas as pd
import re
from pathlib import Path
RAW_PATH=Path("data/raw_sales.csv")
CLEAN_PATH=Path("output/clean_sales.csv")
REPORT_PATH=Path("output/report.txt")

def load_data(path:Path)->pd.DataFrame:
    df=pd.read_csv(path,dtype=str)
    print(f"[LOAD] Loaded {len(df)} rows from {path}")
    return df

def inspect_data(df:pd.DataFrame)->None:
    print("\n[INSPECT] Data quality report (before cleaning):")
    print(f"- Duplicate rows:{df.duplicated().sum()}")
    print("  - Missing values per column:")
    missing=df.isna().sum() + (df == "").sum()
    for col,count in missing.items():
        if count >0:
            print(f"      {col}: {count}")
            
def clean_unit_price(value:str)->float:
    if pd.isna(value) or value == "":
        return None
    cleaned=re.sub(r"[^\d.]", "", str(value))
    return float(cleaned) if cleaned else None

def clean_date(value:str):
    if pd.isna(value) or value=="":
        return pd.NaT
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return pd.to_datetime(value,format=fmt)
        except ValueError:
            continue
    return pd.NaT

def clean_data(df:pd.DataFrame)->pd.DataFrame:
    df=df.copy()
    df['region']=df["region"].str.strip().str.title()
    df['product']=df['product'].str.strip().str.title()
    df['quantity']=pd.to_numeric(df['quantity'],errors='coerce')
    df['unit_price']=df["unit_price"].apply(clean_unit_price)
    df['order_date']=df['order_date'].apply(clean_date)
    
    before=len(df)
    df=df.drop_duplicates()
    print(f"[CLEAN] Removed {before - len(df)} duplicate rows")
    df['region']=df['region'].fillna('Unknown')
    before = len(df)
    df=df.dropna(subset=['quantity','unit_price','order_date'])
    print(f"[CLEAN] Dropped {before - len(df)} rows with missing quantity/price/date")
    df['total_amount']=df['quantity'] * df['unit_price']
    df['order_month']=df['order_date'].dt.to_period("M").astype(str)
    print(f"[CLEAN] Final clean dataset: {len(df)} rows")
    return df

def analyze_data(df:pd.DataFrame)->str:
    by_product = df.groupby("product")["total_amount"].sum().sort_values(ascending=False)
    by_month = df.groupby("order_month")["total_amount"].sum().sort_index()
    by_region = df.groupby("region")["total_amount"].sum().sort_values(ascending=False)
    
    lines=[]
    lines = []
    lines.append("SALES SUMMARY REPORT")
    lines.append("=" * 40)
    lines.append(f"Total revenue: {df['total_amount'].sum():,.2f}")
    lines.append(f"Total orders: {len(df)}")
    lines.append("")
    lines.append("Revenue by Product:")
    for product, amount in by_product.items():
        lines.append(f"  {product:<15} {amount:>12,.2f}")
    lines.append("")
    lines.append("Revenue by Month:")
    for month, amount in by_month.items():
        lines.append(f"  {month:<15} {amount:>12,.2f}")
    lines.append("")
    lines.append("Revenue by Region:")
    for region, amount in by_region.items():
        lines.append(f"  {region:<15} {amount:>12,.2f}")

    report = "\n".join(lines)
    print("\n[ANALYZE]\n" + report)
    return report

def export(df:pd.DataFrame,report:str)->None:
    Path("output").mkdir(exist_ok=True)
    df.to_csv(CLEAN_PATH,index=False)
    REPORT_PATH.write_text(report,encoding="utf-8")
    print(f"\n[EXPORT] Clean data  -> {CLEAN_PATH}")
    print(f"[EXPORT] Report      -> {REPORT_PATH}")
    
def main():
    df_raw=load_data(RAW_PATH)
    inspect_data(df_raw)
    df_clean=clean_data(df_raw)
    report=analyze_data(df_clean)
    export(df_clean,report)
    
if __name__=="__main__":
    main()