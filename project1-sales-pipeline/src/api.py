"""
api.py
------
طبقة الـ "Serve": Flask API بيقدم بيانات الـ Data Warehouse لأي حد يحتاجها
(ممكن تتربط بـ Dashboard، أو Power BI، أو حتى تديها لعميل يستخدمها مباشرة).

نستخدم هنا نفس الأسلوب اللي اتشرح في سلايدز "Python for Databases & APIs":
  - sqlite3.connect() للاتصال
  - GET endpoints لقراءة البيانات
  - كل endpoint بيرجع JSON

Endpoints المتاحة:
  GET /                                -> صفحة توضيحية بكل الـ endpoints
  GET /api/sales/summary               -> إجمالي المبيعات والربح
  GET /api/sales/by-category           -> المبيعات مجمعة حسب فئة المنتج
  GET /api/sales/by-region             -> المبيعات مجمعة حسب المنطقة
  GET /api/sales/monthly                -> المبيعات شهريًا (لعمل trend chart)
  GET /api/products/top?limit=5        -> أعلى المنتجات مبيعًا
  GET /api/products/price-comparison   -> مقارنة أسعارنا بأسعار المنافس
"""

from flask import Flask, jsonify, request
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "output", "sales_warehouse.db")

app = Flask(__name__)


def get_connection():
    """
    بنفتح اتصال جديد بكل request بدل ما نستخدم اتصال واحد مشترك.
    ده أفضل مع Flask لأن كل request ممكن يجي على thread مختلف،
    وSQLite مش بيحب مشاركة نفس الاتصال بين threads.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # يخلينا نقدر نحول النتائج لـ dict بسهولة
    return conn


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


@app.route("/")
def home():
    return jsonify({
        "message": "Sales Data Warehouse API",
        "endpoints": [
            "/api/sales/summary",
            "/api/sales/by-category",
            "/api/sales/by-region",
            "/api/sales/monthly",
            "/api/products/top?limit=5",
            "/api/products/price-comparison"
        ]
    })


@app.route("/api/sales/summary")
def sales_summary():
    conn = get_connection()
    row = conn.execute("""
        SELECT
            COUNT(*) AS total_orders,
            SUM(total_amount) AS total_revenue,
            SUM(profit_margin * quantity) AS total_profit,
            ROUND(AVG(total_amount), 2) AS avg_order_value
        FROM fact_sales
    """).fetchone()
    conn.close()
    return jsonify(dict(row))


@app.route("/api/sales/by-category")
def sales_by_category():
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            p.category,
            COUNT(*) AS num_orders,
            SUM(f.total_amount) AS total_revenue
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        GROUP BY p.category
        ORDER BY total_revenue DESC
    """).fetchall()
    conn.close()
    return jsonify(rows_to_dicts(rows))


@app.route("/api/sales/by-region")
def sales_by_region():
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            r.region,
            COUNT(*) AS num_orders,
            SUM(f.total_amount) AS total_revenue
        FROM fact_sales f
        JOIN dim_region r ON f.region_key = r.region_key
        GROUP BY r.region
        ORDER BY total_revenue DESC
    """).fetchall()
    conn.close()
    return jsonify(rows_to_dicts(rows))


@app.route("/api/sales/monthly")
def sales_monthly():
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            d.year,
            d.month,
            SUM(f.total_amount) AS total_revenue,
            COUNT(*) AS num_orders
        FROM fact_sales f
        JOIN dim_date d ON f.date_key = d.date_key
        GROUP BY d.year, d.month
        ORDER BY d.year, d.month
    """).fetchall()
    conn.close()
    return jsonify(rows_to_dicts(rows))


@app.route("/api/products/top")
def top_products():
    limit = request.args.get("limit", default=5, type=int)
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            p.product_name,
            p.category,
            SUM(f.quantity) AS total_units_sold,
            SUM(f.total_amount) AS total_revenue
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        GROUP BY p.product_name, p.category
        ORDER BY total_revenue DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return jsonify(rows_to_dicts(rows))


@app.route("/api/products/price-comparison")
def price_comparison():
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            p.product_name,
            p.category,
            AVG(f.unit_price) AS our_avg_price,
            AVG(f.competitor_price) AS competitor_price,
            AVG(f.price_diff_vs_competitor) AS avg_price_diff
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        GROUP BY p.product_name, p.category
        ORDER BY avg_price_diff DESC
    """).fetchall()
    conn.close()
    return jsonify(rows_to_dicts(rows))


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("[ERROR] قاعدة البيانات مش موجودة. شغّل main.py الأول عشان تبني الـ pipeline كامل.")
    else:
        print(f"[INFO] بيشتغل على قاعدة البيانات: {DB_PATH}")
        app.run(debug=True, port=5000)
