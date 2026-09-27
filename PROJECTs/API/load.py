"""
load.py
--------
Project 4 - Load step, with INCREMENTAL loading.

Unlike Project 3 (which rebuilds the database fresh every run), this pipeline
is meant to run repeatedly over time (e.g. once a day) to track a GitHub
user's repos as they change. So instead of wiping the table each run, we:

    - INSERT a repo if we haven't seen its repo_id before
    - UPDATE it if we have seen it before AND the source's updated_at is newer
    - SKIP it if nothing has changed since our last fetch

This mirrors the "incremental data integration" concept from the Data
Pipeline material: only process what actually changed, not the full dataset
every time.
"""

import json
import sqlite3
from pathlib import Path

CLEAN_INPUT = Path("data/clean_repos.json")
DB_PATH = Path("repos.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS repos (
    repo_id     INTEGER PRIMARY KEY,
    full_name   TEXT NOT NULL,
    description TEXT,
    language    TEXT,
    stars       INTEGER,
    forks       INTEGER,
    updated_at  TEXT,
    url         TEXT,
    fetched_at  TEXT
);
"""

def upsert_repo(conn: sqlite3.Connection, repo: dict) -> str:
    """Insert a new repo, update an existing one if it changed, or skip if unchanged.
    Returns one of 'inserted', 'updated', 'skipped' for reporting purposes."""
    cur = conn.execute(
        "SELECT updated_at FROM repos WHERE repo_id = ?", (repo["repo_id"],)
    )
    existing = cur.fetchone()

    if existing is None:
        conn.execute(
            """INSERT INTO repos (repo_id, full_name, description, language, stars, forks, updated_at, url, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (repo["repo_id"], repo["full_name"], repo["description"], repo["language"],
             repo["stars"], repo["forks"], repo["updated_at"], repo["url"], repo["fetched_at"]),
        )
        return "inserted"

    existing_updated_at = existing[0]
    if repo["updated_at"] > existing_updated_at:
        conn.execute(
            """UPDATE repos SET full_name=?, description=?, language=?, stars=?, forks=?,
               updated_at=?, url=?, fetched_at=? WHERE repo_id=?""",
            (repo["full_name"], repo["description"], repo["language"], repo["stars"], repo["forks"],
             repo["updated_at"], repo["url"], repo["fetched_at"], repo["repo_id"]),
        )
        return "updated"

    return "skipped"


def main():
    clean_rows = json.loads(CLEAN_INPUT.read_text(encoding="utf-8"))
    print(f"[LOAD] Loaded {len(clean_rows)} clean records from {CLEAN_INPUT}")

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    counts = {"inserted": 0, "updated": 0, "skipped": 0}
    for repo in clean_rows:
        result = upsert_repo(conn, repo)
        counts[result] += 1

    conn.commit()
    print(f"[LOAD] Inserted: {counts['inserted']} | Updated: {counts['updated']} | Unchanged (skipped): {counts['skipped']}")
    print(f"[LOAD] Database at {DB_PATH}")

    conn.close()


if __name__ == "__main__":
    main()