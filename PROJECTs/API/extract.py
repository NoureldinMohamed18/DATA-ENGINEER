"""
extract.py
-----------
Project 4 - Extract step.

Fetches public repository data from the GitHub REST API for a given user or
organization. GitHub's API is free, well-documented, and needs no API key
for this kind of read-only public request — a good real API to practice on.

Each run appends a timestamped snapshot, which is what makes the later
"incremental load" step in load.py meaningful: we only load records that are
newer than what's already in the database.

Usage:
    python extract.py --user torvalds          # fetch live from GitHub API
    python extract.py --offline                # use local sample_response.json instead
"""

import argparse
import json
import requests
from datetime import datetime,timezone
from pathlib import Path
RAW_OUTPUT = Path("data/raw_repos.json")
API_URL_TEMPLATE = "https://api.github.com/users/{user}/repos?per_page=20&sort=updated"

def fetch_live(user:str)->list[dict]:
    """Call the real GitHub API for a given username."""
    url=API_URL_TEMPLATE
    print(f"[EXTRACT] GET {url}")
    headers={"Accept": "application/vnd.github+json"}
    response=requests.get(url,headers=headers,timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_offline() -> list[dict]:
    """Load a saved sample GitHub API response — for offline development/testing."""
    data = json.loads(Path("sample_response.json").read_text(encoding="utf-8"))
    print(f"[EXTRACT] Loaded {len(data)} records from local sample_response.json")
    return data

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--user", default="torvalds", help="GitHub username to fetch repos for")
    parser.add_argument("--offline", action="store_true", help="Use local sample_response.json instead of the live API")
    args = parser.parse_args()
    
    repos=fetch_offline() if args.offline else fetch_live(args.user)
    snapshot = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source_user": args.user,
        "repos": repos,
    }

    Path("data").mkdir(exist_ok=True)
    RAW_OUTPUT.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[EXTRACT] Saved {len(repos)} repo records -> {RAW_OUTPUT}")
    
if __name__=="__main__":
    main()
    