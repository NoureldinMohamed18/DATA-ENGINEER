"""
load.py
--------
Project 3 - Load step.

Loads the clean book data into a SQLite database (books.db),
ready for querying. This is the final step of the E-T-L pipeline:
extract.py -> transform.py -> load.py
"""
import json 
import sqlite3
from pathlib import Path

CLEAN_INPUT = Path("data/clean_books.json")
DB_PATH = Path("books.db")

SCHEMA="""
DROP TABLE IF EXIXTS books;
CREATE TABLE books(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    price REAL NOT NULL,
    rating INTEGER NOT NULL,
    in_stock INTEGER NOT NULL,
    product_url TEXT
);
"""

def main():
    clean_books = json.loads(CLEAN_INPUT.read_text(encoding="utf-8"))
    print(f"[LOAD] Loaded {len(clean_books)} clean records from {CLEAN_INPUT}")

    if DB_PATH.exists():
        DB_PATH.unlink()  # rebuild fresh each run

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    conn.executemany(
        "INSERT INTO books (title, price, rating, in_stock, product_url) VALUES (?, ?, ?, ?, ?)",
        [
            (b["title"], b["price"], b["rating"], int(b["in_stock"]), b["product_url"])
            for b in clean_books
        ],
    )
    conn.commit()

    # quick sanity check query
    cur = conn.execute("SELECT COUNT(*), AVG(price), AVG(rating) FROM books")
    count, avg_price, avg_rating = cur.fetchone()
    print(f"[LOAD] Inserted {count} books into {DB_PATH}")
    print(f"[LOAD] Average price: £{avg_price:.2f} | Average rating: {avg_rating:.1f} / 5")

    conn.close()

if __name__=="__main__":
    main()
