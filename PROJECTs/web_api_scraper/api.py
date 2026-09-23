"""
Flask REST API
==============
A simple REST API for managing scraped product data.
Supports full CRUD operations with SQLite backend.

Endpoints:
  GET    /products          -> List all products
  GET    /products/<id>     -> Get single product
  POST   /products          -> Create new product
  PUT    /products/<id>     -> Update product
  DELETE /products/<id>     -> Delete product
  GET    /products/search   -> Search products by name/category
  GET    /stats             -> Get statistics
"""

from flask import Flask, request, jsonify
import sqlite3
import json
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
DB_PATH = os.path.join(DATA_DIR, 'api_database.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL CHECK (price >= 0),
            rating REAL CHECK (rating >= 0 AND rating <= 5),
            in_stock BOOLEAN DEFAULT 1,
            source TEXT DEFAULT 'api',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("[DB] Database initialized.")


def load_mock_data():
    products_file = os.path.join(DATA_DIR, 'products.json')
    if not os.path.exists(products_file):
        print("[DB] No products.json found. Run scraper.py first.")
        return

    with open(products_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    conn = get_db_connection()
    count = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    if count > 0:
        print(f"[DB] Database already has {count} products. Skipping load.")
        conn.close()
        return

    for p in products:
        conn.execute("""
            INSERT INTO products (id, name, category, price, rating, in_stock, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (p['id'], p['name'], p['category'], p['price'], 
              p.get('rating', 4.0), p.get('in_stock', True), p.get('source', 'scraper')))

    conn.commit()
    conn.close()
    print(f"[DB] Loaded {len(products)} products into database.")


@app.route('/')
def home():
    return jsonify({
        "message": "Product API - Welcome!",
        "version": "1.0",
        "endpoints": {
            "GET /products": "List all products (supports ?category= & ?in_stock=)",
            "GET /products/<id>": "Get a specific product",
            "POST /products": "Create a new product (JSON body)",
            "PUT /products/<id>": "Update a product (JSON body)",
            "DELETE /products/<id>": "Delete a product",
            "GET /products/search?q=term": "Search products by name",
            "GET /stats": "Get product statistics"
        }
    })


@app.route('/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    query = "SELECT * FROM products WHERE 1=1"
    params = []

    category = request.args.get('category')
    if category:
        query += " AND category = ?"
        params.append(category)

    in_stock = request.args.get('in_stock')
    if in_stock is not None:
        query += " AND in_stock = ?"
        params.append(1 if in_stock.lower() == 'true' else 0)

    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'ASC')
    if sort_by in ['id', 'name', 'price', 'rating', 'category']:
        query += f" ORDER BY {sort_by} {order}"

    products = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify({
        "count": len(products),
        "products": [dict(row) for row in products]
    })


@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()

    if product is None:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(dict(product))


@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()

    if not data or 'name' not in data or 'category' not in data or 'price' not in data:
        return jsonify({"error": "Required fields: name, category, price"}), 400

    conn = get_db_connection()
    cursor = conn.execute("""
        INSERT INTO products (name, category, price, rating, in_stock, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data['name'], data['category'], data['price'],
        data.get('rating', 4.0), data.get('in_stock', True), data.get('source', 'api')
    ))
    conn.commit()

    new_id = cursor.lastrowid
    product = conn.execute('SELECT * FROM products WHERE id = ?', (new_id,)).fetchone()
    conn.close()

    return jsonify({
        "message": "Product created successfully",
        "product": dict(product)
    }), 201


@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Product not found"}), 404

    fields = []
    values = []

    if 'name' in data:
        fields.append("name = ?")
        values.append(data['name'])
    if 'category' in data:
        fields.append("category = ?")
        values.append(data['category'])
    if 'price' in data:
        fields.append("price = ?")
        values.append(data['price'])
    if 'rating' in data:
        fields.append("rating = ?")
        values.append(data['rating'])
    if 'in_stock' in data:
        fields.append("in_stock = ?")
        values.append(1 if data['in_stock'] else 0)

    if not fields:
        return jsonify({"error": "No valid fields to update"}), 400

    values.append(product_id)
    query = f"UPDATE products SET {', '.join(fields)} WHERE id = ?"

    conn.execute(query, values)
    conn.commit()

    updated = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()

    return jsonify({
        "message": "Product updated successfully",
        "product": dict(updated)
    })


@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Product not found"}), 404

    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Product {product_id} deleted successfully"})


@app.route('/products/search', methods=['GET'])
def search_products():
    query_term = request.args.get('q', '')
    if not query_term:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    conn = get_db_connection()
    products = conn.execute("""
        SELECT * FROM products 
        WHERE name LIKE ? OR category LIKE ?
        ORDER BY name
    """, (f'%{query_term}%', f'%{query_term}%')).fetchall()
    conn.close()

    return jsonify({
        "query": query_term,
        "count": len(products),
        "products": [dict(row) for row in products]
    })


@app.route('/stats', methods=['GET'])
def get_stats():
    conn = get_db_connection()

    total = conn.execute('SELECT COUNT(*) as count FROM products').fetchone()['count']
    in_stock = conn.execute('SELECT COUNT(*) as count FROM products WHERE in_stock = 1').fetchone()['count']
    avg_price = conn.execute('SELECT ROUND(AVG(price), 2) as avg FROM products').fetchone()['avg']
    avg_rating = conn.execute('SELECT ROUND(AVG(rating), 2) as avg FROM products').fetchone()['avg']

    categories = conn.execute("""
        SELECT category, COUNT(*) as count, ROUND(AVG(price), 2) as avg_price
        FROM products
        GROUP BY category
    """).fetchall()

    conn.close()

    return jsonify({
        "total_products": total,
        "in_stock": in_stock,
        "out_of_stock": total - in_stock,
        "average_price": avg_price,
        "average_rating": avg_rating,
        "categories": [dict(row) for row in categories]
    })


if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    init_db()
    load_mock_data()

    print("\n" + "=" * 50)
    print("FLASK API STARTED")
    print("=" * 50)
    print("Visit: http://127.0.0.1:5000/")
    print("Try:  http://127.0.0.1:5000/products")
    print("=" * 50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
