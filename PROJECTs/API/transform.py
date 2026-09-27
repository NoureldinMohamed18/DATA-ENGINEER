"""
transform.py
-------------
Project 4 - Transform step.

Takes the raw GitHub API snapshot from extract.py and reshapes it into a
flat, clean structure ready for loading:
    - keeps only the fields we actually need
    - fills missing descriptions
    - parses updated_at into a proper datetime string
    - keeps the fetched_at timestamp on every row (needed for incremental loading)
"""
import json
from pathlib import Path
from datetime import datetime

RAW_INPUT = Path("data/raw_repos.json")
CLEAN_OUTPUT = Path("data/clean_repos.json")


def transform_repos(snapshot:dict)-> list[dict]:
    fetched_at = snapshot["fetched_at"]
    clean_rows = []

    for repo in snapshot["repos"]:
        clean_rows.append({
            "repo_id": repo["id"],
            "full_name": repo["full_name"],
            "description": repo["description"] or "No description provided",
            "language": repo["language"] or "Unknown",
            "stars": repo["stargazers_count"],
            "forks": repo["forks_count"],
            "updated_at": repo["updated_at"],
            "url": repo["html_url"],
            "fetched_at": fetched_at,  # when OUR pipeline pulled this record
        })

    return clean_rows

def main():
    snapshot=json.loads(RAW_INPUT.read_text(encoding='utf-8'))
    print(f"[TRANSFORM] Loaded snapshot fetched at {snapshot['fetched_at']} "
          f"with {len(snapshot['repos'])} repos")
    clean_rows = transform_repos(snapshot)
    CLEAN_OUTPUT.write_text(json.dumps(clean_rows,indent=2,ensure_ascii=False))
    print(f"[TRANSFORM] Saved {len(clean_rows)} clean records -> {CLEAN_OUTPUT}")

if __name__=='__main__':
    main()