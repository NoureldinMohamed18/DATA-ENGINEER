"""
run_queries.py
---------------
Executes each analytical query in sql/queries.sql against sales.db
and prints the results in a readable format.

This separates "building the database" (build_database.py) from
"querying the database" (this file) — a clean separation of concerns.
"""
import sqlite3
from pathlib import Path
DB_PATH = Path("sales.db")
QUERIES_PATH = Path("sql/queries.sql")

def split_queries(sql_text:str):
    separator = "-- " + "=" * 60
    blocks = [b.strip() for b in sql_text.split(separator) if b.strip()]
    queries=[]
    i=0
    while i < len(blocks):
        block=blocks[i]
        lines=[l for l in block.splitlines() if l.strip()]
        if lines and lines[0].lstrip("-").strip().startswith("Q") and all(l.strip().startswith("--") for l in lines):
            title = lines[0].lstrip("-").strip()
            # The actual query is in the next block
            if i + 1 < len(blocks):
                query = blocks[i + 1].strip()
                queries.append((title, query))
            i += 2
        else:
            i += 1
    return queries

def main():
    conn=sqlite3.connect(DB_PATH)
    cur=conn.cursor()
    sql_text=QUERIES_PATH.read_text(encoding='utf-8')
    queries=split_queries(sql_text)
    
    for title, query in queries:
        print("\n" + "=" * 70)
        print(title)
        print("=" * 70)
        cur.execute(query)
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        print(" | ".join(cols))
        for row in rows[:15]:  # cap output for readability
            print(" | ".join(str(v) for v in row))
        if len(rows) > 15:
            print(f"... ({len(rows) - 15} more rows)")
        if not rows:
            print("(no rows returned)")

    conn.close()
    
if __name__=="__main__":
    main()