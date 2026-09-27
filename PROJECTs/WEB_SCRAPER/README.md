# Web Scraping ETL Pipeline

Scrapes book listings from [books.toscrape.com](https://books.toscrape.com),
cleans the data, and loads it into a SQLite database — structured as a proper
three-stage ETL pipeline (`extract.py` → `transform.py` → `load.py`), not one
long script.

## Is this legal?

Yes. [books.toscrape.com](https://books.toscrape.com) is a website **built
specifically for practicing web scraping**. Its `robots.txt` allows full
crawling, and it exists precisely so learners have a legal, ethical target to
scrape without hitting real businesses' servers or violating anyone's Terms
of Service. This is the right habit to build: always check `robots.txt` and
a site's ToS before scraping a real target.

## Pipeline design

```
extract.py  ->  data/raw_books.json   ->  transform.py  ->  data/clean_books.json  ->  load.py  ->  books.db
(scrape HTML)    (raw scraped fields)      (clean types)      (typed, deduped)          (SQLite)
```

Each stage reads the previous stage's output file and writes its own — so
you can inspect the data at every step, and re-run any single stage without
re-running the whole pipeline.

| Stage | What it does |
|---|---|
| **extract.py** | Requests catalogue pages, parses book cards with BeautifulSoup, extracts title/price/rating/availability/URL as raw text |
| **transform.py** | Converts `"£51.77"` → `51.77` (float), `"Three"` → `3` (int), `"In stock"` → `True` (bool), removes duplicate titles |
| **load.py** | Creates a `books` table in SQLite and inserts the clean records |
| **run_pipeline.py** | Runs all three stages in order, stopping immediately if any stage fails |

## How to run it

```bash
pip install -r requirements.txt

# Option A: scrape the live site (requires internet access)
python run_pipeline.py --pages 5

# Option B: run entirely offline, using the included local HTML fixture
# (sample_page.html mirrors the real site's exact HTML structure/selectors)
python run_pipeline.py --offline
```

You can also run each stage individually for debugging:
```bash
python extract.py --offline
python transform.py
python load.py
```

## Why BeautifulSoup here (not Selenium)?

books.toscrape.com serves fully-rendered static HTML — no JavaScript needed
to see the book listings — so BeautifulSoup alone is enough and is faster
than spinning up a browser with Selenium. Selenium becomes necessary when a
site loads content dynamically via JavaScript after the initial page load
(e.g. infinite-scroll pages, or content behind a "Load More" button).

## Skills demonstrated

- Web scraping with `requests` + `BeautifulSoup` (CSS selectors, HTML parsing)
- Structuring a scraper as a proper ETL pipeline instead of one script
- Data cleaning: parsing currency strings, mapping categorical text to numbers, deduplication
- Respecting scraping ethics (robots.txt, rate limiting with `time.sleep`, custom User-Agent)
- Loading scraped data into SQLite

## Project structure

```
project3_web_scraping_etl/
├── extract.py           # Extract: scrape or parse local HTML -> raw_books.json
├── transform.py         # Transform: clean types, dedupe -> clean_books.json
├── load.py              # Load: insert clean data into books.db
├── run_pipeline.py       # Orchestrates all three stages in order
├── sample_page.html     # Local fixture for offline testing (same structure as the live site)
├── data/
│   ├── raw_books.json
│   └── clean_books.json
├── books.db             # Generated SQLite database
└── requirements.txt
```
