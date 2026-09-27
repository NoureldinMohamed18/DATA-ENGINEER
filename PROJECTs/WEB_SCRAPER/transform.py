"""
transform.py
-------------
Project 3 - Transform step.

Takes the raw scraped JSON from extract.py and cleans it:
    - price_text "£51.77"    -> price (float) 51.77
    - rating_word "Three"    -> rating (int) 3
    - availability_text      -> in_stock (bool)
    - remove duplicate titles (in case a book appears on multiple pages)
"""

import json
import re
from pathlib import Path

RAW_INPUT = Path("data/raw_books.json")
CLEAN_OUTPUT = Path("data/clean_books.json")
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def clean_price(price_text:str)->float:
    """'£51.77' -> 51.77"""
    numeric=re.sub(r"[^\d.]", "", price_text)
    return float(numeric) if numeric else 0.0

def clean_rating(rating_word:str)->int:
    """'Three' -> 3. Defaults to 0 if the word isn't recognized (data-quality safeguard)."""
    return RATING_MAP.GET(rating_word,0)

def clean_availability(availability_text: str) -> bool:
    """'In stock' -> True, anything else -> False."""
    return "in stock" in availability_text.lower()

def transform_books(raw_books: list[dict]) -> list[dict]:
    seen_titles = set()
    clean_books = []

    for book in raw_books:
        title = book["title"].strip()

        # Skip duplicates (e.g. if the same book showed up across scraped pages)
        if title in seen_titles:
            continue
        seen_titles.add(title)

        clean_books.append({
            "title": title,
            "price": clean_price(book["price_text"]),
            "rating": clean_rating(book["rating_word"]),
            "in_stock": clean_availability(book["availability_text"]),
            "product_url": book["product_url"],
        })

    return clean_books

def main():
    raw_books = json.loads(RAW_INPUT.read_text(encoding="utf-8"))
    print(f"[TRANSFORM] Loaded {len(raw_books)} raw records")

    clean_books = transform_books(raw_books)
    print(f"[TRANSFORM] Produced {len(clean_books)} clean records "
          f"(removed {len(raw_books) - len(clean_books)} duplicates)")

    CLEAN_OUTPUT.write_text(json.dumps(clean_books, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[TRANSFORM] Saved -> {CLEAN_OUTPUT}")


if __name__ == "__main__":
    main()
    