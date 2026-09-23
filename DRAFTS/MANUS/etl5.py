
import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
from pymongo import MongoClient
from datetime import datetime
import time
import logging
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup logging
logging.basicConfig(filename=\'etl_project_5.log\', level=logging.INFO,
                    format=\'%(asctime)s - %(levelname)s - %(message)s\')

def setup_selenium_driver():
    """
    Sets up a headless Chrome WebDriver.
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver.
    """
    logging.info("[Setup] Setting up Selenium WebDriver.")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--incognito")
    try:
        driver = webdriver.Chrome(options=options)
        logging.info("[Setup] WebDriver initialized successfully.")
        return driver
    except Exception as e:
        logging.error(f"[Setup Error] Failed to initialize WebDriver: {e}")
        return None

def extract_products_from_api(base_url, endpoint, page_param="_page", limit_param="_limit", page_size=10):
    """
    Extracts product data from a paginated REST API.
    Returns:
        list: A list of dictionaries, each representing a product.
    """
    all_products = []
    page = 1
    while True:
        params = {page_param: page, limit_param: page_size}
        full_url = f"{base_url}{endpoint}"

        logging.info(f"[Extract API] Fetching products from: {full_url} with params: {params}")
        try:
            response = requests.get(full_url, params=params, timeout=10)
            response.raise_for_status()
            page_data = response.json()

            if not page_data:
                logging.info(f"[Extract API] No more product data found on page {page}. Stopping pagination.")
                break

            for item in page_data:
                # Simulate adding a category if not present, and a supplier_id
                item["category"] = item.get("category", "Electronics") # Default category
                item["supplier_id"] = item.get("userId", 1) # Use userId from API as supplier_id
                all_products.append(item)

            logging.info(f"[Extract API] Successfully fetched {len(page_data)} products from page {page}.")
            page += 1
            time.sleep(0.1) # Be polite

        except requests.exceptions.RequestException as e:
            logging.error(f"[Extract API Error] Failed to fetch products from {full_url}: {e}")
            break
        except Exception as e:
            logging.error(f"[Extract API Error] An unexpected error occurred during API product extraction: {e}")
            break
    logging.info(f"[Extract API] Total products extracted: {len(all_products)}.")
    return all_products

def extract_reviews_from_web(driver, product_ids, base_review_url_template, max_scrolls=1):
    """
    Extracts product reviews from dynamic webpages using Selenium and BeautifulSoup.
    Args:
        driver (webdriver.Chrome): The Selenium WebDriver instance.
        product_ids (list): List of product IDs to scrape reviews for.
        base_review_url_template (str): Template for review URLs, e.g., "file:///path/to/reviews_{}.html"
        max_scrolls (int): Maximum number of times to scroll down or click \'Load More\'.
    Returns:
        list: A list of dictionaries, each representing a product review.
    """
    all_reviews = []
    for product_id in product_ids:
        review_url = base_review_url_template.format(product_id)
        logging.info(f"[Extract Web] Navigating to reviews for product {product_id} at: {review_url}")
        try:
            driver.get(review_url)
            # Wait for reviews to load
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".review-item"))
            )

            # Simulate scrolling or clicking \'Load More\' button
            for i in range(max_scrolls):
                try:
                    load_more_button = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".load-more-reviews"))
                    )
                    load_more_button.click()
                    time.sleep(1) # Wait for new content to load
                except:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    # Check if page height changed, if not, no more content
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if i > 0 and new_height == driver.execute_script("return arguments[0]", driver.execute_script("return document.body.scrollHeight")):
                        logging.info("[Extract Web] No new content loaded after scroll. Stopping.")
                        break

            soup = BeautifulSoup(driver.page_source, \'html.parser\')
            review_elements = soup.find_all(\'div\', class_=\'review-item\')

            if not review_elements:
                logging.warning(f"[Extract Web] No review items found for product {product_id}. Check selectors or URL.")

            for review in review_elements:
                review_text_element = review.find(\'p\', class_=\'review-text\')
                review_score_element = review.find(\'span\', class_=\'review-score\')
                reviewer_name_element = review.find(\'span\', class_=\'reviewer-name\')
                review_date_element = review.find(\'span\', class_=\'review-date\')

                review_text = review_text_element.text.strip() if review_text_element else \'\'
                review_score = review_score_element.text.strip() if review_score_element else \'0\'
                reviewer_name = reviewer_name_element.text.strip() if reviewer_name_element else \'Anonymous\'
                review_date = review_date_element.text.strip() if review_date_element else datetime.now().strftime(\'%Y-%m-%d\')

                all_reviews.append({
                    \"product_id\": product_id,
                    \"review_text\": review_text,
                    \"review_score\": review_score,
                    \"reviewer_name\": reviewer_name,
                    \"review_date\": review_date
                })
            logging.info(f"[Extract Web] Successfully extracted {len(review_elements)} reviews for product {product_id}.")

        except Exception as e:
            logging.error(f"[Extract Web Error] An error occurred during review extraction for product {product_id}: {e}")
            continue # Continue to next product even if one fails
    return all_reviews

def analyze_sentiment(text):
    """
    Performs a very basic sentiment analysis on text.
    (No external NLP libraries allowed, so this is a simplified example).
    """
    positive_keywords = ["great", "excellent", "love", "good", "happy", "satisfied", "amazing", "best"]
    negative_keywords = ["bad", "poor", "disappointing", "hate", "terrible", "unhappy", "worst"]

    text_lower = text.lower()
    positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
    negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)

    if positive_count > negative_count:
        return "Positive"
    elif negative_count > positive_count:
        return "Negative"
    else:
        return "Neutral"

def transform_data(raw_products, raw_reviews):
    """
    Transforms and cleans the extracted product and review data.
    Args:
        raw_products (list): Raw product data from API.
        raw_reviews (list): Raw review data from web scraping.
    Returns:
        tuple: (transformed_products_df, transformed_reviews_df)
    """
    logging.info("[Transform] Starting data transformation and consolidation.")

    # --- Products Data Transformation ---
    products_df = pd.DataFrame(raw_products)
    if not products_df.empty:
        products_df = products_df.rename(columns={
            \"id\": \"product_id\",
            \"title\": \"name\", # Assuming API title is product name
            \"body\": \"description\", # Assuming API body is product description
            \"price\": \"price\"
        })
        products_df = products_df[["product_id", "name", "description", "category", "price", "supplier_id"]]
        products_df["price"] = pd.to_numeric(products_df["price"], errors=\'coerce\').fillna(0.0)
        products_df["description"] = products_df["description"].fillna(\'No description available\')
        products_df["category"] = products_df["category"].fillna(\'Uncategorized\')
        products_df.drop_duplicates(subset=["product_id"], inplace=True)
        logging.info(f"[Transform] Transformed {len(products_df)} unique products.")
    else:
        logging.warning("[Transform] No product data to transform.")
        products_df = pd.DataFrame(columns=["product_id", "name", "description", "category", "price", "supplier_id"])

    # --- Reviews Data Transformation ---
    reviews_df = pd.DataFrame(raw_reviews)
    if not reviews_df.empty:
        reviews_df["review_score"] = pd.to_numeric(reviews_df["review_score"], errors=\'coerce\').fillna(0).astype(int)
        reviews_df["review_text"] = reviews_df["review_text"].fillna(\'\')
        reviews_df["review_date"] = pd.to_datetime(reviews_df["review_date"], errors=\'coerce\').dt.strftime(\'%Y-%m-%d\').fillna(datetime.now().strftime(\'%Y-%m-%d\'))

        # Sentiment Analysis
        reviews_df["sentiment"] = reviews_df["review_text"].apply(analyze_sentiment)
        logging.info("[Transform] Performed sentiment analysis on reviews.")

        reviews_df.drop_duplicates(subset=["product_id", "review_text", "reviewer_name"], inplace=True)
        logging.info(f"[Transform] Transformed {len(reviews_df)} unique reviews.")
    else:
        logging.warning("[Transform] No review data to transform.")
        reviews_df = pd.DataFrame(columns=["product_id", "review_text", "review_score", "reviewer_name", "review_date", "sentiment"])

    # --- Aggregate Review Data for Products (for SQLite) ---
    if not reviews_df.empty:
        # Calculate average review score and total reviews per product
        aggregated_reviews = reviews_df.groupby("product_id").agg(
            avg_review_score=("review_score", \'mean\'),
            total_reviews=("product_id", \'count\')
        ).reset_index()
        # Merge aggregated review data back into products_df
        products_df = pd.merge(products_df, aggregated_reviews, on="product_id", how="left")
        products_df[["avg_review_score", "total_reviews"]] = products_df[["avg_review_score", "total_reviews"]].fillna(0)
        products_df["avg_review_score"] = products_df["avg_review_score"].round(2)
        logging.info("[Transform] Aggregated review data for products.")
    else:
        products_df[\"avg_review_score\"] = 0.0
        products_df[\"total_reviews\"] = 0

    # Add last_updated timestamp to products
    products_df["last_updated"] = datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')

    logging.info("[Transform] Data transformation complete.")
    return products_df, reviews_df

def load_data_to_sqlite_and_mongodb(products_df, reviews_df, sqlite_db_name=\'ecommerce_final.db\', mongo_db_name=\'product_analytics\', mongo_collection_name=\'reviews\'):
    """
    Loads transformed product data into SQLite and review data into MongoDB.
    """
    logging.info("[Load] Starting data loading to SQLite and MongoDB.")

    # --- Load to SQLite (Products and Suppliers) ---
    sqlite_conn = None
    try:
        sqlite_conn = sqlite3.connect(sqlite_db_name)
        sqlite_cursor = sqlite_conn.cursor()

        # Create suppliers table
        sqlite_cursor.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                supplier_id INTEGER PRIMARY KEY,
                supplier_name TEXT NOT NULL,
                contact_email TEXT
            )
        """)
        sqlite_conn.commit()
        logging.info("[Load SQLite] Table \'suppliers\' ensured to exist.")

        # Create products table
        sqlite_cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                price REAL NOT NULL,
                stock_quantity INTEGER,
                supplier_id INTEGER,
                avg_review_score REAL,
                total_reviews INTEGER,
                last_updated TEXT NOT NULL,
                FOREIGN KEY (supplier_id) REFERENCES suppliers (supplier_id)
            )
        """)
        sqlite_conn.commit()
        logging.info("[Load SQLite] Table \'products\' ensured to exist.")

        # Upsert Suppliers
        suppliers_to_load = products_df[products_df["supplier_id"].notna()][["supplier_id"]].drop_duplicates().copy()
        suppliers_to_load["supplier_name"] = \'Supplier \' + suppliers_to_load["supplier_id"].astype(str)
        suppliers_to_load["contact_email"] = \'contact@supplier\' + suppliers_to_load["supplier_id"].astype(str) + \'.com\'

        if not suppliers_to_load.empty:
            for index, row in suppliers_to_load.iterrows():
                sqlite_cursor.execute("""
                    INSERT INTO suppliers (supplier_id, supplier_name, contact_email)
                    VALUES (?, ?, ?)
                    ON CONFLICT(supplier_id) DO UPDATE SET
                        supplier_name=excluded.supplier_name,
                        contact_email=excluded.contact_email
                """, (row["supplier_id"], row["supplier_name"], row["contact_email"]))
            sqlite_conn.commit()
            logging.info(f"[Load SQLite] Upserted {len(suppliers_to_load)} suppliers.")
        else:
            logging.info("[Load SQLite] No supplier data to upsert.")

        # Upsert Products
        if not products_df.empty:
            for index, row in products_df.iterrows():
                sqlite_cursor.execute("""
                    INSERT INTO products (product_id, name, description, category, price, stock_quantity, supplier_id, avg_review_score, total_reviews, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(product_id) DO UPDATE SET
                        name=excluded.name,
                        description=excluded.description,
                        category=excluded.category,
                        price=excluded.price,
                        stock_quantity=excluded.stock_quantity,
                        supplier_id=excluded.supplier_id,
                        avg_review_score=excluded.avg_review_score,
                        total_reviews=excluded.total_reviews,
                        last_updated=excluded.last_updated
                """, (
                    row["product_id"],
                    row["name"],
                    row["description"],
                    row["category"],
                    row["price"],
                    row["stock_quantity"],
                    row["supplier_id"],
                    row["avg_review_score"],
                    row["total_reviews"],
                    row["last_updated"]
                ))
            sqlite_conn.commit()
            logging.info(f"[Load SQLite] Upserted {len(products_df)} products.")
        else:
            logging.info("[Load SQLite] No product data to upsert.")

    except sqlite3.Error as e:
        logging.error(f"[Load SQLite Error] SQLite error: {e}")
    except Exception as e:
        logging.error(f"[Load SQLite Error] An unexpected error occurred during SQLite loading: {e}")
    finally:
        if sqlite_conn:
            sqlite_conn.close()
            logging.info("[Load SQLite] SQLite connection closed.")

    # --- Load to MongoDB (Reviews) ---
    mongo_client = None
    try:
        if not reviews_df.empty:
            mongo_client = MongoClient(\'mongodb://localhost:27017/\')
            mongo_db = mongo_client[mongo_db_name]
            mongo_collection = mongo_db[mongo_collection_name]

            # Add extraction_date to reviews before loading to MongoDB
            reviews_df["extraction_date"] = datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')

            # Convert DataFrame to list of dictionaries for MongoDB
            reviews_records = reviews_df.to_dict(orient=\'records\')

            # For reviews, we can insert new ones. For updates, we'd need a unique review ID.
            # For simplicity, we'll just insert new reviews.
            # To prevent duplicates on subsequent runs, one might clear the collection or implement upsert logic
            # based on a composite key (product_id, review_text, reviewer_name).
            # Here, we'll clear the collection for demonstration of fresh load.
            mongo_collection.delete_many({})
            insert_result = mongo_collection.insert_many(reviews_records)
            logging.info(f"[Load MongoDB] Successfully loaded {len(insert_result.inserted_ids)} reviews into \'{mongo_collection_name}\'.")
        else:
            logging.info("[Load MongoDB] No review data to load.")

    except Exception as e:
        logging.error(f"[Load MongoDB Error] An error occurred during MongoDB loading: {e}")
    finally:
        if mongo_client:
            mongo_client.close()
            logging.info("[Load MongoDB] MongoDB connection closed.")

# --- Main ETL Process ---
if __name__ == "__main__":
    # Ensure fuzzywuzzy and python-Levenshtein are installed for Project 4 if running all projects sequentially.
    # For Project 5, we don't use fuzzywuzzy directly, but it's good practice to have it if needed.
    # sudo pip3 install fuzzywuzzy python-Levenshtein

    # Dummy API data (simulating a JSONPlaceholder-like API with product details)
    # Note: In a real scenario, this would be fetched from a live API.
    dummy_api_products = [
        {"id": 1, "title": "Laptop Pro", "body": "High-end laptop for demanding tasks.", "price": 1200.50, "stock_quantity": 50, "category": "Laptops", "userId": 1},
        {"id": 2, "title": "Wireless Mouse", "body": "Ergonomic wireless mouse.", "price": 25.99, "stock_quantity": 200, "category": "Peripherals", "userId": 1},
        {"id": 3, "title": "External SSD 1TB", "body": "Ultra-fast external storage.", "price": 150.00, "stock_quantity": 80, "category": "Storage", "userId": 2},
        {"id": 4, "title": "4K Monitor", "body": "Stunning 4K display.", "price": 350.00, "stock_quantity": 30, "category": "Displays", "userId": 3},
        {"id": 5, "title": "Gaming Keyboard", "body": "Mechanical keyboard for gamers.", "price": 75.00, "stock_quantity": 100, "category": "Peripherals", "userId": 1}
    ]

    # Dummy HTML content for product reviews (simulating dynamic pages for each product_id)
    # We'll create separate files for each product_id for demonstration.
    dummy_review_html_template = """
    <!DOCTYPE html>
    <html>
    <head><title>Reviews for Product {product_id}</title></head>
    <body>
        <h1>Reviews for Product {product_id}</h1>
        <div class="review-list">
            <div class="review-item">
                <span class="reviewer-name">Alice</span>
                <span class="review-date">2023-01-15</span>
                <span class="review-score">5</span>
                <p class="review-text">This product is great! I love it.</p>
            </div>
            <div class="review-item">
                <span class="reviewer-name">Bob</span>
                <span class="review-date">2023-02-20</span>
                <span class="review-score">4</span>
                <p class="review-text">Good value for money, very satisfied.</p>
            </div>
            <div class="review-item">
                <span class="reviewer-name">Charlie</span>
                <span class="review-date">2023-03-10</span>
                <span class="review-score">2</span>
                <p class="review-text">Disappointing performance, not happy.</p>
            </div>
        </div>
        <button class="load-more-reviews" onclick="loadMoreReviews()">Load More Reviews</button>

        <script>
            let reviewCount = 3;
            function loadMoreReviews() {
                if (reviewCount >= 5) {
                    document.querySelector(\".load-more-reviews\").style.display = \'none\';
                    return;
                }
                const reviewList = document.querySelector(\".review-list\");
                reviewCount++;
                const newReview = document.createElement(\'div\');
                newReview.className = \'review-item\';
                newReview.innerHTML = `
                    <span class=\"reviewer-name\">Reviewer ${reviewCount}</span>
                    <span class=\"review-date\">2023-04-${reviewCount}</span>
                    <span class=\"review-score\">${reviewCount % 5 + 1}</span>
                    <p class=\"review-text\">Another review for product {product_id}. This is ${reviewCount % 2 == 0 ? \'good\' : \'bad\'}.</p>
                `;
                reviewList.appendChild(newReview);
            }
        </script>
    </body>
    </html>
    """

    # Create dummy review HTML files for each product
    product_ids_for_reviews = [p["id"] for p in dummy_api_products]
    review_file_paths = {}
    for p_id in product_ids_for_reviews:
        path = f"/home/ubuntu/projects/codding-6564b468/dummy_reviews_{p_id}.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(dummy_review_html_template.format(product_id=p_id))
        review_file_paths[p_id] = f"file://{path}"
        logging.info(f"[Setup] Created dummy review HTML file for product {p_id} at {path}")

    print("\n--- Starting ETL Process for Project 5 ---")

    selenium_driver = None
    try:
        # 1. Extract Products from API
        raw_products = dummy_api_products # Simulate API extraction
        logging.info("[Main] Finished product extraction from API (simulated).")

        # 2. Extract Reviews from Web (using Selenium)
        selenium_driver = setup_selenium_driver()
        if selenium_driver is None:
            logging.error("[Main] Failed to setup WebDriver. Cannot extract reviews. Exiting.")
            raw_reviews = []
        else:
            # Pass the template for review URLs, not individual URLs
            raw_reviews = extract_reviews_from_web(selenium_driver, product_ids_for_reviews, "file:///home/ubuntu/projects/codding-6564b468/dummy_reviews_{}.html", max_scrolls=1)
            logging.info("[Main] Finished review extraction from web.")

        # 3. Transform
        transformed_products_df, transformed_reviews_df = transform_data(raw_products, raw_reviews)
        logging.info("[Main] Finished data transformation.")

        # 4. Load
        load_data_to_sqlite_and_mongodb(transformed_products_df, transformed_reviews_df,
                                        sqlite_db_name=\'ecommerce_final.db\',
                                        mongo_db_name=\'product_analytics\',
                                        mongo_collection_name=\'reviews\')
        logging.info("[Main] Finished data loading to SQLite and MongoDB.")

    except Exception as e:
        logging.error(f"[Main Error] An error occurred in the main ETL process: {e}")
    finally:
        if selenium_driver:
            selenium_driver.quit()

    print("\n--- ETL Process Completed for Project 5 ---")

    # Optional: Verify data in SQLite and MongoDB
    print("\n[Verification] Fetching data from ecommerce_final.db (SQLite):")
    sqlite_conn = None
    try:
        sqlite_conn = sqlite3.connect(\'ecommerce_final.db\')
        print("\nProducts Table:")
        verification_products_df = pd.read_sql_query("SELECT * FROM products", sqlite_conn)
        print(verification_products_df)

        print("\nSuppliers Table:")
        verification_suppliers_df = pd.read_sql_query("SELECT * FROM suppliers", sqlite_conn)
        print(verification_suppliers_df)

    except Exception as e:
        print(f"[Verification Error] Could not read from SQLite DB: {e}")
    finally:
        if sqlite_conn:
            sqlite_conn.close()

    print("\n[Verification] Fetching data from product_analytics.reviews (MongoDB):")
    mongo_client = None
    try:
        mongo_client = MongoClient(\'mongodb://localhost:27017/\')
        mongo_db = mongo_client[\'product_analytics\']
        mongo_collection = mongo_db[\'reviews\']
        mongo_data = list(mongo_collection.find({}))
        for doc in mongo_data:
            doc[\'_id\'] = str(doc[\'_id\']) # Convert ObjectId to string for display
        verification_reviews_df = pd.DataFrame(mongo_data)
        print(verification_reviews_df)
    except Exception as e:
        print(f"[Verification Error] Could not read from MongoDB: {e}")
    finally:
        if mongo_client:
            mongo_client.close()

