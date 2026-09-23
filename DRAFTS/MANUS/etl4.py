
import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
from datetime import datetime
import time
import logging
import re
from fuzzywuzzy import fuzz # For fuzzy matching

# Setup logging
logging.basicConfig(filename='etl_project_4.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def extract_from_web(url):
    """
    Extracts product data from a static webpage.
    Args:
        url (str): The URL of the webpage to scrape.
    Returns:
        list: A list of dictionaries, each representing a product.
    """
    logging.info(f"[Extract Web] Attempting to fetch data from: {url}")
    products_data = []
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')

        product_elements = soup.find_all('div', class_='product-item')

        if not product_elements:
            logging.warning("[Extract Web] No product items found. Check selectors or URL.")

        for product in product_elements:
            name_element = product.find('h2', class_='product-name')
            price_element = product.find('span', class_='product-price')
            desc_element = product.find('p', class_='product-description')
            category_element = product.find('span', class_='product-category') # New: category

            name = name_element.text.strip() if name_element else 'N/A'
            price = price_element.text.strip() if price_element else '0.0'
            description = desc_element.text.strip() if desc_element else ''
            category = category_element.text.strip() if category_element else 'Uncategorized'

            products_data.append({
                'name': name,
                'price': price,
                'description': description,
                'category': category,
                'source': 'web_scrape'
            })
        logging.info(f"[Extract Web] Successfully extracted {len(products_data)} products.")
        return products_data
    except requests.exceptions.RequestException as e:
        logging.error(f"[Extract Web Error] Failed to fetch URL {url}: {e}")
        return []
    except Exception as e:
        logging.error(f"[Extract Web Error] An unexpected error occurred during web extraction: {e}")
        return []

def extract_from_api(base_url, endpoint, params=None, page_param="_page", limit_param="_limit", page_size=10):
    """
    Extracts data from a paginated REST API.
    Args:
        base_url (str): The base URL of the API.
        endpoint (str): The specific API endpoint.
        params (dict, optional): Initial query parameters. Defaults to None.
        page_param (str): The name of the query parameter for the page number.
        limit_param (str): The name of the query parameter for the page size.
        page_size (int): The number of items per page.
    Returns:
        list: A list of dictionaries, each representing a record from the API.
    """
    all_data = []
    page = 1
    while True:
        current_params = params.copy() if params else {}
        current_params[page_param] = page
        current_params[limit_param] = page_size
        full_url = f"{base_url}{endpoint}"

        logging.info(f"[Extract API] Fetching from: {full_url} with params: {current_params}")
        try:
            response = requests.get(full_url, params=current_params, timeout=10)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            page_data = response.json()

            if not page_data:
                logging.info(f"[Extract API] No more data found on page {page}. Stopping pagination.")
                break

            for item in page_data:
                item['source'] = 'api'
                all_data.append(item)

            logging.info(f"[Extract API] Successfully fetched {len(page_data)} records from page {page}.")
            page += 1
            time.sleep(0.1) # Small delay to be polite to the API

        except requests.exceptions.RequestException as e:
            logging.error(f"[Extract API Error] Failed to fetch data from {full_url}: {e}")
            break # Stop if there's an error
        except Exception as e:
            logging.error(f"[Extract API Error] An unexpected error occurred during API extraction: {e}")
            break
    logging.info(f"[Extract API] Total records extracted: {len(all_data)} from {endpoint}.")
    return all_data

def transform_data(web_data, api_data):
    """
    Transforms and cleans the extracted product data from web and API sources.
    Args:
        web_data (list): Raw product data from web scraping.
        api_data (list): Raw product data from API.
    Returns:
        pandas.DataFrame: A cleaned and consolidated DataFrame of product data.
    """
    logging.info("[Transform] Starting data transformation and consolidation.")

    # Convert to DataFrames
    web_df = pd.DataFrame(web_data)
    api_df = pd.DataFrame(api_data)

    # --- Web Data Transformations ---
    if not web_df.empty:
        web_df['description'] = web_df['description'].fillna('No description available')
        web_df['price'] = web_df['price'].astype(str).str.replace(r'[^\d.]', '', regex=True)
        web_df['price'] = pd.to_numeric(web_df['price'], errors='coerce').fillna(0.0)
        web_df['name'] = web_df['name'].apply(lambda x: re.sub(r'\s+', ' ', x).strip().lower())
        logging.info("[Transform] Cleaned web scraped data.")
    else:
        logging.warning("[Transform] No web data to transform.")

    # --- API Data Transformations ---
    if not api_df.empty:
        api_df = api_df.rename(columns={'id': 'api_product_id', 'userId': 'supplier_id', 'product_name': 'name', 'product_description': 'description', 'current_price': 'price', 'available_stock': 'stock_quantity'})
        api_df['description'] = api_df['description'].fillna('No description available')
        api_df['price'] = pd.to_numeric(api_df['price'], errors='coerce').fillna(0.0)
        api_df['stock_quantity'] = pd.to_numeric(api_df['stock_quantity'], errors='coerce').fillna(0).astype(int)
        api_df['category'] = api_df['category'].fillna('Uncategorized') # Assuming API provides category
        api_df['name'] = api_df['name'].apply(lambda x: re.sub(r'\s+', ' ', x).strip().lower())
        # Select relevant columns for API data before merging
        api_df = api_df[['api_product_id', 'name', 'description', 'category', 'price', 'stock_quantity', 'supplier_id', 'source']]
        logging.info("[Transform] Cleaned API data.")
    else:
        logging.warning("[Transform] No API data to transform.")

    # --- Consolidate DataFrames ---
    # Align columns for concatenation
    common_cols = ['name', 'description', 'category', 'price', 'source']
    web_df_aligned = web_df[common_cols].copy() if not web_df.empty else pd.DataFrame(columns=common_cols)
    api_df_aligned = api_df[common_cols + ['stock_quantity', 'supplier_id']].copy() if not api_df.empty else pd.DataFrame(columns=common_cols + ['stock_quantity', 'supplier_id'])

    # Fill missing columns in web_df_aligned that are present in api_df_aligned
    for col in ['stock_quantity', 'supplier_id']:
        if col not in web_df_aligned.columns:
            web_df_aligned[col] = None # Or a default value

    # Fill missing columns in api_df_aligned that are present in web_df_aligned
    for col in common_cols:
        if col not in api_df_aligned.columns:
            api_df_aligned[col] = None # Or a default value

    # Ensure column order is consistent for concatenation
    all_cols = list(set(web_df_aligned.columns) | set(api_df_aligned.columns))
    web_df_aligned = web_df_aligned.reindex(columns=all_cols)
    api_df_aligned = api_df_aligned.reindex(columns=all_cols)

    combined_df = pd.concat([web_df_aligned, api_df_aligned], ignore_index=True)
    logging.info(f"[Transform] Combined dataframes. Total records: {len(combined_df)}.")

    if combined_df.empty:
        logging.warning("[Transform] Combined DataFrame is empty. Skipping further transformations.")
        return pd.DataFrame()

    # --- Advanced Deduplication (Fuzzy Matching) ---
    # This is a simplified example. For large datasets, this can be computationally expensive.
    # A more scalable approach would involve blocking/indexing.
    deduplicated_products = []
    processed_indices = set()

    # Sort by name to bring similar items closer
    combined_df = combined_df.sort_values(by='name').reset_index(drop=True)

    for i in range(len(combined_df)):
        if i in processed_indices:
            continue

        current_product = combined_df.iloc[i]
        potential_duplicates = [current_product]
        processed_indices.add(i)

        for j in range(i + 1, len(combined_df)):
            if j in processed_indices:
                continue

            other_product = combined_df.iloc[j]
            # Fuzzy match on name and check price proximity
            if fuzz.ratio(current_product['name'], other_product['name']) > 80 and \
               abs(current_product['price'] - other_product['price']) < 5:
                potential_duplicates.append(other_product)
                processed_indices.add(j)

        # Merge duplicates: prioritize API data for stock/supplier, otherwise take first
        if len(potential_duplicates) > 1:
            # Find the API source if available, otherwise take the first one
            merged_product = potential_duplicates[0].copy()
            for dup in potential_duplicates:
                if dup['source'] == 'api':
                    merged_product = dup.copy()
                    break
            # If no API source, just take the first one and try to merge non-nulls
            for dup in potential_duplicates:
                for col in merged_product.index:
                    if pd.isna(merged_product[col]) and not pd.isna(dup[col]):
                        merged_product[col] = dup[col]
            deduplicated_products.append(merged_product)
            logging.info(f"[Transform] Merged duplicates for: {current_product['name']}")
        else:
            deduplicated_products.append(current_product)

    final_df = pd.DataFrame(deduplicated_products)
    logging.info(f"[Transform] Deduplication complete. Final records: {len(final_df)}.")

    # --- Standardize Categories ---
    category_mapping = {
        'laptops': 'Electronics',
        'notebooks': 'Electronics',
        'computers': 'Electronics',
        'mouse': 'Peripherals',
        'keyboard': 'Peripherals',
        'ssd': 'Storage',
        'hard drive': 'Storage',
        'monitors': 'Displays',
        'display': 'Displays',
        'uncategorized': 'Other'
    }
    final_df['category'] = final_df['category'].str.lower().map(category_mapping).fillna('Other')
    logging.info("[Transform] Standardized categories.")

    # --- Derived Metrics / Enrichment ---
    final_df['is_in_stock'] = final_df['stock_quantity'] > 0
    final_df['extraction_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info("[Transform] Added derived metrics and extraction date.")

    # Ensure supplier_id is int or None
    final_df['supplier_id'] = pd.to_numeric(final_df['supplier_id'], errors='coerce').astype('Int64') # Use Int64 for nullable integer

    logging.info("[Transform] Data transformation complete.")
    return final_df

def load_data_to_sqlite(df, db_name='ecommerce.db'):
    """
    Loads the transformed data into an SQLite database with products and suppliers tables.
    Args:
        df (pandas.DataFrame): The DataFrame containing cleaned and consolidated product data.
        db_name (str): The name of the SQLite database file.
    """
    if df.empty:
        logging.warning("[Load] No data to load.")
        return

    logging.info(f"[Load] Connecting to SQLite database: {db_name}")
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Create suppliers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                supplier_id INTEGER PRIMARY KEY,
                supplier_name TEXT NOT NULL,
                contact_email TEXT
            )
        """)
        conn.commit()
        logging.info("[Load] Table 'suppliers' ensured to exist.")

        # Create products table with foreign key to suppliers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                price REAL NOT NULL,
                stock_quantity INTEGER,
                supplier_id INTEGER,
                source TEXT NOT NULL,
                extraction_date TEXT NOT NULL,
                is_in_stock BOOLEAN,
                FOREIGN KEY (supplier_id) REFERENCES suppliers (supplier_id)
            )
        """)
        conn.commit()
        logging.info("[Load] Table 'products' ensured to exist.")

        # --- Load Suppliers Data ---
        # Extract unique suppliers from the product DataFrame
        suppliers_df = df[df['supplier_id'].notna()][['supplier_id']].drop_duplicates().copy()
        # For this example, we'll assign dummy names/emails. In a real scenario, this would come from a source.
        suppliers_df['supplier_name'] = 'Supplier ' + suppliers_df['supplier_id'].astype(str)
        suppliers_df['contact_email'] = 'contact@supplier' + suppliers_df['supplier_id'].astype(str) + '.com'

        if not suppliers_df.empty:
            # Upsert logic for suppliers: insert if not exists, update if exists
            for index, row in suppliers_df.iterrows():
                cursor.execute("""
                    INSERT INTO suppliers (supplier_id, supplier_name, contact_email)
                    VALUES (?, ?, ?)
                    ON CONFLICT(supplier_id) DO UPDATE SET
                        supplier_name=excluded.supplier_name,
                        contact_email=excluded.contact_email
                """, (row['supplier_id'], row['supplier_name'], row['contact_email']))
            conn.commit()
            logging.info(f"[Load] Upserted {len(suppliers_df)} suppliers.")
        else:
            logging.info("[Load] No supplier data to load.")

        # --- Load Products Data (Upsert) ---
        # Use a temporary table or custom logic for upserting products
        # For simplicity and to avoid complex SQL, we'll delete existing and insert new based on name/price for web_scrape
        # and based on api_product_id for api source. This is a simplified upsert.

        # First, handle web_scrape products (deduplicate by name/price)
        web_products_to_load = df[df['source'] == 'web_scrape'].copy()
        if not web_products_to_load.empty:
            # Delete existing web_scrape products that match name/price
            for index, row in web_products_to_load.iterrows():
                cursor.execute("DELETE FROM products WHERE name = ? AND price = ? AND source = ?",
                               (row['name'], row['price'], 'web_scrape'))
            conn.commit()
            web_products_to_load.to_sql('products', conn, if_exists='append', index=False, method='multi')
            conn.commit()
            logging.info(f"[Load] Upserted {len(web_products_to_load)} web scraped products.")

        # Then, handle API products (deduplicate by a unique API ID if available, or name/price)
        api_products_to_load = df[df['source'] == 'api'].copy()
        if not api_products_to_load.empty:
            # Assuming 'api_product_id' is a unique identifier from the API source
            # If not, a combination of name/supplier_id might be used.
            # For this example, we'll use name and supplier_id for API products as well for simplicity
            # and because 'api_product_id' might not be directly in the final_df after consolidation.
            for index, row in api_products_to_load.iterrows():
                cursor.execute("DELETE FROM products WHERE name = ? AND supplier_id = ? AND source = ?",
                               (row['name'], row['supplier_id'], 'api'))
            conn.commit()
            api_products_to_load.to_sql('products', conn, if_exists='append', index=False, method='multi')
            conn.commit()
            logging.info(f"[Load] Upserted {len(api_products_to_load)} API products.")

    except sqlite3.Error as e:
        logging.error(f"[Load Error] SQLite error: {e}")
    except Exception as e:
        logging.error(f"[Load Error] An unexpected error occurred during loading: {e}")
    finally:
        if conn:
            conn.close()
            logging.info("[Load] SQLite connection closed.")

# --- Main ETL Process ---
if __name__ == "__main__":
    # Install fuzzywuzzy and python-Levenshtein if not already installed
    # sudo pip3 install fuzzywuzzy python-Levenshtein

    # Dummy HTML content for web scraping
    dummy_web_html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Web Product Catalog</title></head>
    <body>
        <h1>Web Products</h1>
        <div class="product-item">
            <h2 class="product-name">Laptop Pro</h2>
            <span class="product-price">$1200.50</span>
            <p class="product-description">Powerful laptop for professionals.</p>
            <span class="product-category">Laptops</span>
        </div>
        <div class="product-item">
            <h2 class="product-name">Wireless Mouse</h2>
            <span class="product-price">$25.99</span>
            <p class="product-description">Ergonomic design, long battery life.</p>
            <span class="product-category">Peripherals</span>
        </div>
        <div class="product-item">
            <h2 class="product-name">External SSD</h2>
            <span class="product-price">$150.00</span>
            <p class="product-description">Fast and portable storage.</p>
            <span class="product-category">Storage</span>
        </div>
        <div class="product-item">
            <h2 class="product-name">Laptop Pro</h2>
            <span class="product-price">$1200.50</span>
            <p class="product-description">Powerful laptop for professionals.</p>
            <span class="product-category">Notebooks</span>
        </div>
        <div class="product-item">
            <h2 class="product-name">Gaming Keyboard</h2>
            <span class="product-price">$75.00</span>
            <!-- Missing description for demonstration -->
            <span class="product-category">Peripherals</span>
        </div>
    </body>
    </html>
    """

    # Dummy API data (simulating a JSONPlaceholder-like API with product details)
    # Note: In a real scenario, this would be fetched from a live API.
    dummy_api_data = [
        {"id": 101, "userId": 1, "product_name": "Laptop Pro", "product_description": "High-end laptop for demanding tasks.", "current_price": 1202.00, "available_stock": 50, "category": "Computers"},
        {"id": 102, "userId": 1, "product_name": "Gaming Mouse", "product_description": "Precision gaming mouse.", "current_price": 30.00, "available_stock": 120, "category": "Peripherals"},
        {"id": 103, "userId": 2, "product_name": "Portable SSD 1TB", "product_description": "Ultra-fast external storage.", "current_price": 149.99, "available_stock": 80, "category": "Hard Drive"},
        {"id": 104, "userId": 3, "product_name": "4K Monitor", "product_description": "Stunning 4K display.", "current_price": 350.00, "available_stock": 30, "category": "Displays"},
        {"id": 105, "userId": 1, "product_name": "Wireless Mouse", "product_description": "Ergonomic wireless mouse.", "current_price": 26.50, "available_stock": 200, "category": "Peripherals"}
    ]

    # Save dummy HTML to a local file
    dummy_web_html_path = "/home/ubuntu/projects/codding-6564b468/dummy_web_products.html"
    with open(dummy_web_html_path, "w", encoding="utf-8") as f:
        f.write(dummy_web_html_content)
    logging.info(f"[Setup] Created dummy web HTML file at {dummy_web_html_path}")

    # Simulate API endpoint (for demonstration, we'll pass dummy_api_data directly)
    # In a real scenario, this would be a URL like: API_BASE_URL = "http://localhost:8000", API_ENDPOINT = "/products"

    print("\n--- Starting ETL Process for Project 4 ---")

    # 1. Extract
    # For web scraping, use the local file URL
    web_products = extract_from_web(f"file://{dummy_web_html_path}")
    # For API, we'll use the dummy_api_data directly for simplicity in this sandbox.
    # In a real scenario, you'd call extract_from_api with a real API endpoint.
    api_products = dummy_api_data # Simulate API extraction
    logging.info("[Main] Finished extraction from web and API (simulated).")

    # 2. Transform
    transformed_products_df = transform_data(web_products, api_products)
    logging.info("[Main] Finished data transformation.")

    # 3. Load
    load_data_to_sqlite(transformed_products_df, db_name='ecommerce_advanced.db')
    logging.info("[Main] Finished data loading.")

    print("\n--- ETL Process Completed for Project 4 ---")

    # Optional: Verify data in SQLite
    print("\n[Verification] Fetching data from ecommerce_advanced.db:")
    try:
        conn = sqlite3.connect('ecommerce_advanced.db')
        print("\nSuppliers Table:")
        verification_suppliers_df = pd.read_sql_query("SELECT * FROM suppliers", conn)
        print(verification_suppliers_df)

        print("\nProducts Table:")
        verification_products_df = pd.read_sql_query("SELECT * FROM products", conn)
        print(verification_products_df)

        print("\nJoined Data (first 5 rows):")
        joined_df = pd.read_sql_query("""
            SELECT
                p.product_id, p.name, p.price, p.stock_quantity, p.category, p.source,
                s.supplier_name
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
            LIMIT 5
        """, conn)
        print(joined_df)

    except Exception as e:
        print(f"[Verification Error] Could not read from DB: {e}")
    finally:
        if conn:
            conn.close()

