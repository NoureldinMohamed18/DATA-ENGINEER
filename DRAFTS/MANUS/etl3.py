
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from pymongo import MongoClient
from datetime import datetime

def setup_selenium_driver():
    """
    Sets up a headless Chrome WebDriver.
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver.
    """
    print("[Setup] Setting up Selenium WebDriver.")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run Chrome in headless mode (without GUI)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--incognito")
    # Path to chromedriver executable (assuming it's in PATH or specified here)
    # For this sandbox environment, we assume chromedriver is available.
    try:
        driver = webdriver.Chrome(options=options)
        print("[Setup] WebDriver initialized successfully.")
        return driver
    except Exception as e:
        print(f"[Setup Error] Failed to initialize WebDriver: {e}")
        return None

def extract_dynamic_data(driver, url, max_scrolls=3):
    """
    Extracts product data from a dynamic webpage using Selenium and BeautifulSoup.
    Handles infinite scrolling or 'Load More' buttons.
    Args:
        driver (webdriver.Chrome): The Selenium WebDriver instance.
        url (str): The URL of the webpage to scrape.
        max_scrolls (int): Maximum number of times to scroll down or click 'Load More'.
    Returns:
        list: A list of dictionaries, each representing a product.
    """
    print(f"[Extract] Navigating to: {url}")
    products_data = []
    try:
        driver.get(url)
        # Wait for the initial page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".product-item"))
        )
        print("[Extract] Initial page loaded.")

        # Simulate scrolling or clicking 'Load More' button
        for i in range(max_scrolls):
            print(f"[Extract] Scrolling/Loading more (attempt {i+1}/{max_scrolls})...")
            # Example for 'Load More' button
            try:
                load_more_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".load-more-button"))
                )
                load_more_button.click()
                time.sleep(2) # Wait for new content to load
            except:
                # If no 'Load More' button, try scrolling down
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2) # Wait for new content to load
                # Check if page height changed, if not, no more content
                new_height = driver.execute_script("return document.body.scrollHeight")
                if i > 0 and new_height == driver.execute_script("return arguments[0]", driver.execute_script("return document.body.scrollHeight")):
                    print("[Extract] No new content loaded after scroll. Stopping.")
                    break

        # After all dynamic content is loaded, use BeautifulSoup for parsing
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        product_elements = soup.find_all('div', class_='product-item')

        if not product_elements:
            print("[Extract] No product items found. Check selectors or URL.")

        for product in product_elements:
            name_element = product.find('h2', class_='product-name')
            price_element = product.find('span', class_='product-price')
            desc_element = product.find('p', class_='product-description')

            name = name_element.text.strip() if name_element else 'N/A'
            price = price_element.text.strip() if price_element else '0.0'
            description = desc_element.text.strip() if desc_element else ''

            products_data.append({
                'name': name,
                'price': price,
                'description': description
            })
        print(f"[Extract] Successfully extracted {len(products_data)} products.")
        return products_data
    except Exception as e:
        print(f"[Extract Error] An error occurred during dynamic extraction: {e}")
        return []
    finally:
        if driver:
            driver.quit()
            print("[Extract] WebDriver closed.")

def transform_data(data):
    """
    Transforms and cleans the extracted product data.
    Args:
        data (list): A list of dictionaries with raw product data.
    Returns:
        pandas.DataFrame: A cleaned DataFrame of product data.
    """
    print("[Transform] Starting data transformation.")
    if not data:
        print("[Transform] No data to transform.")
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # 1. Handle Missing Values: Fill empty descriptions
    df['description'] = df['description'].fillna('No description available')
    print("[Transform] Handled missing descriptions.")

    # 2. Clean and Convert Price:
    df['price'] = df['price'].astype(str).str.replace('[^\d.]', '', regex=True)
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0.0)
    print("[Transform] Cleaned and converted prices to numeric.")

    # 3. Deduplication: Remove duplicate products based on name and price
    initial_rows = len(df)
    df.drop_duplicates(subset=['name', 'price'], inplace=True)
    if len(df) < initial_rows:
        print(f"[Transform] Removed {initial_rows - len(df)} duplicate rows.")
    else:
        print("[Transform] No duplicate rows found.")

    # Add extraction date
    df['extraction_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("[Transform] Added extraction date.")

    print("[Transform] Data transformation complete.")
    return df

def load_data_to_mongodb(df, db_name='product_db', collection_name='products'):
    """
    Loads the transformed data into a MongoDB collection.
    Args:
        df (pandas.DataFrame): The DataFrame containing cleaned product data.
        db_name (str): The name of the MongoDB database.
        collection_name (str): The name of the collection to load data into.
    """
    if df.empty:
        print("[Load] No data to load.")
        return

    print(f"[Load] Connecting to MongoDB database: {db_name}, collection: {collection_name}")
    try:
        # Assuming MongoDB is running locally on default port 27017
        client = MongoClient('mongodb://localhost:27017/')
        db = client[db_name]
        collection = db[collection_name]

        # Convert DataFrame to a list of dictionaries (JSON-like documents)
        records = df.to_dict(orient='records')

        # For simplicity, we'll insert new records. For more advanced scenarios,
        # consider upsert operations based on a unique identifier.
        insert_result = collection.insert_many(records)
        print(f"[Load] Successfully loaded {len(insert_result.inserted_ids)} documents into '{collection_name}'.")

    except Exception as e:
        print(f"[Load Error] An error occurred during MongoDB loading: {e}")
    finally:
        if 'client' in locals() and client:
            client.close()
            print("[Load] MongoDB connection closed.")

# --- Main ETL Process ---
if __name__ == "__main__":
    # For demonstration, we'll create a dummy HTML file to simulate a dynamic webpage
    # This HTML will have a 'Load More' button and some initial products.
    # Note: Selenium needs a real browser environment. For local testing, ensure chromedriver is installed
    # and accessible in your PATH, or specify its path.
    dummy_html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Dynamic Product Catalog</title></head>
    <body>
        <h1>Our Dynamic Products</h1>
        <div class="product-list">
            <div class="product-item">
                <h2 class="product-name">Dynamic Laptop X</h2>
                <span class="product-price">$1500.00</span>
                <p class="product-description">High-performance dynamic laptop.</p>
            </div>
            <div class="product-item">
                <h2 class="product-name">Dynamic Monitor Y</h2>
                <span class="product-price">$300.00</span>
                <p class="product-description">Crisp display for dynamic visuals.</p>
            </div>
        </div>
        <button class="load-more-button" onclick="loadMoreProducts()">Load More</button>

        <script>
            let productCount = 2;
            function loadMoreProducts() {
                if (productCount >= 6) {
                    document.querySelector('.load-more-button').style.display = 'none';
                    return;
                }
                const productList = document.querySelector('.product-list');
                for (let i = 0; i < 2; i++) {
                    productCount++;
                    const newProduct = document.createElement('div');
                    newProduct.className = 'product-item';
                    newProduct.innerHTML = `
                        <h2 class="product-name">Dynamic Product ${productCount}</h2>
                        <span class="product-price">$${(100 + productCount * 10).toFixed(2)}</span>
                        <p class="product-description">Description for dynamic product ${productCount}.</p>
                    `;
                    productList.appendChild(newProduct);
                }
            }
        </script>
    </body>
    </html>
    """

    dummy_html_path = "/home/ubuntu/projects/codding-6564b468/dummy_dynamic_products.html"
    with open(dummy_html_path, "w", encoding="utf-8") as f:
        f.write(dummy_html_content)
    print(f"[Setup] Created dummy dynamic HTML file at {dummy_html_path}")

    source_url = f"file://{dummy_html_path}"

    print("\n--- Starting ETL Process for Project 3 ---")

    driver = None
    try:
        # 1. Setup Selenium Driver
        driver = setup_selenium_driver()
        if driver is None:
            print("[Main] Failed to setup WebDriver. Exiting.")
        else:
            # 2. Extract
            raw_data = extract_dynamic_data(driver, source_url, max_scrolls=2) # Click 'Load More' twice

            # 3. Transform
            transformed_df = transform_data(raw_data)

            # 4. Load
            load_data_to_mongodb(transformed_df, db_name='dynamic_product_catalog', collection_name='products')

    except Exception as e:
        print(f"[Main Error] An error occurred in the main ETL process: {e}")
    finally:
        if driver:
            driver.quit()

    print("\n--- ETL Process Completed for Project 3 ---")

    # Optional: Verify data in MongoDB
    print("\n[Verification] Fetching data from MongoDB:")
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['dynamic_product_catalog']
        collection = db['products']
        mongo_data = list(collection.find({}))
        for doc in mongo_data:
            doc['_id'] = str(doc['_id']) # Convert ObjectId to string for display
        verification_df = pd.DataFrame(mongo_data)
        print(verification_df)
    except Exception as e:
        print(f"[Verification Error] Could not read from MongoDB: {e}")
    finally:
        if 'client' in locals() and client:
            client.close()

