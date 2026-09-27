# REST API Data Pipeline

Pulls repository data from the **GitHub REST API**, cleans it, loads it
**incrementally** into SQLite, and serves it through a small **Flask API**
of its own. This project has two sides: consuming an external API, and
building one.

## Architecture

```
GitHub REST API  --(extract.py)-->  raw_repos.json
                                          |
                                   (transform.py)
                                          v
                                  clean_repos.json
                                          |
                                     (load.py, incremental upsert)
                                          v
                                      repos.db  <----- (api.py, Flask) <----- your requests
```

- **Left side**: an external system (GitHub) is the data source.
- **Right side**: your own Flask API exposes the pipeline's output to anyone else.

## Why incremental loading?

Project 3's pipeline rebuilds its database from scratch every run — fine for
a one-off scrape. This pipeline is meant to run **repeatedly over time**
(e.g. daily) to track how a GitHub user's repos change. Re-fetching and
re-processing everything from zero every time is wasteful, so `load.py`
instead:

- **Inserts** a repo it has never seen (`repo_id` is new)
- **Updates** a repo only if GitHub's `updated_at` is newer than what's stored
- **Skips** a repo if nothing changed since the last run

Run the pipeline twice in a row and you'll see this directly:
```
First run:   Inserted: 4 | Updated: 0 | Skipped: 0
Second run:  Inserted: 0 | Updated: 0 | Skipped: 4   <- nothing changed, nothing rewritten
```

## How to run it

```bash
pip install -r requirements.txt

# Option A: pull live data from GitHub for any public username
python run_pipeline.py --user torvalds

# Option B: run fully offline using the included sample_response.json
python run_pipeline.py --offline

# Then start your own API on top of the stored data
python api.py
```

## Your own API endpoints

| Endpoint | Description |
|---|---|
| `GET /repos` | All stored repos, most recently fetched first |
| `GET /repos/top?limit=5` | Top N repos by star count |
| `GET /repos/<repo_id>` | A single repo by GitHub's numeric id (404 if not found) |

Example:
```bash
curl http://127.0.0.1:5000/repos/top?limit=3
```

## Skills demonstrated

- Consuming a real REST API with `requests` (headers, error handling via `raise_for_status`)
- Building a REST API with Flask (routes, JSON responses, 404 error handling)
- Incremental data loading (upsert pattern) instead of full reloads
- Structuring a pipeline as separate extract/transform/load stages
- Working with timestamps to detect what has actually changed

## Project structure

```
project4_api_pipeline/
├── extract.py             # pulls data from GitHub API (or local fixture)
├── transform.py           # cleans and flattens the raw API response
├── load.py                # incremental upsert into repos.db
├── api.py                 # Flask API serving the stored data
├── run_pipeline.py        # runs extract -> transform -> load in order
├── sample_response.json   # local fixture for offline testing
├── data/
│   ├── raw_repos.json
│   └── clean_repos.json
├── repos.db                # generated SQLite database
└── requirements.txt
```
