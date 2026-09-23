import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
from datetime import datetime

def extract_data(url):
    """
        Extracts product data from a static webpage.
        Args:
            url (str): The URL of the webpage to scrape.
        Returns:
            list: A list of dictionaries, each representing a product.
        """    
    print(f"[Extract] Attempting to fetch data from: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup=BeautifulSoup(response.text, 'html.parser')
        products_data = []
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
    except requests.exceptions.RequestException as e:
        print(f"[Extract Error] Failed to fetch URL {url}: {e}")
        return []
    except Exception as e:
        print(f"[Extract Error] An unexpected error occurred during extraction: {e}")
        return []
    
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
    # Remove currency symbols, commas, and convert to float
    df['price'] = df['price'].astype(str).str.replace('[^\d.]', '', regex=True)
    # Handle cases where price might be empty after cleaning (e.g., 'N/A' becomes '')
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

def load_data(df, db_name='products.db', table_name='products'):
    """
    Loads the transformed data into an SQLite database.
    Args:
        df (pandas.DataFrame): The DataFrame containing cleaned product data.
        db_name (str): The name of the SQLite database file.
        table_name (str): The name of the table to load data into.
    """
    if df.empty:
        print("[Load] No data to load.")
        return

    print(f"[Load] Connecting to SQLite database: {db_name}")
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                extraction_date TEXT NOT NULL
            )
        """)
        conn.commit()
        print(f"[Load] Table '{table_name}' ensured to exist.")

        # Load data into the table
        # Using 'append' if table exists, which adds new rows. This is simple for beginner.
        # For more advanced scenarios, consider 'replace' or custom upsert logic.
        df.to_sql(table_name, conn, if_exists='append', index=False)
        conn.commit()
        print(f"[Load] Successfully loaded {len(df)} rows into '{table_name}'.")

    except sqlite3.Error as e:
        print(f"[Load Error] SQLite error: {e}")
    except Exception as e:
        print(f"[Load Error] An unexpected error occurred during loading: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("[Load] SQLite connection closed.")
            
# --- Main ETL Process ---
if __name__ == "__main__":
    # For demonstration, we'll create a dummy HTML file to simulate a static webpage
    # In a real scenario, this URL would point to an actual website.
    dummy_html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Product Catalog</title></head>
    <body>
        <h1>Our Products</h1>
        <div class="product-item">
            <h2 class="product-name">Laptop Pro</h2>
            <span class="product-price">$1200.50</span>
            <p class="product-description">Powerful laptop for professionals.</p>
        </div>
        <div class="product-item">
            <h2 class="product-name">Wireless Mouse</h2>
            <span class="product-price">$25.99</span>
            <p class="product-description">Ergonomic design, long battery life.</p>
        </div>
        <div class="product-item">
            <h2 class="product-name">External SSD</h2>
            <span class="product-price">$150.00</span>
            <p class="product-description">Fast and portable storage.</p>
        </div>
        <div class="product-item">
            <h2 class="product-name">Laptop Pro</h2>
            <span class="product-price">$1200.50</span>
            <p class="product-description">Powerful laptop for professionals.</p>
        </div>
        <div class="product-item">
            <h2 class="product-name">Gaming Keyboard</h2>
            <span class="product-price">$75.00</span>
            <!-- Missing description for demonstration -->
        </div>
    </body>
    </html>
    """

    # Save dummy HTML to a local file
    dummy_html_path = "/home/ubuntu/projects/codding-6564b468/dummy_products.html"
    with open(dummy_html_path, "w", encoding="utf-8") as f:
        f.write(dummy_html_content)
    print(f"[Setup] Created dummy HTML file at {dummy_html_path}")

    # Use the local file URL for extraction
    source_url = f"file://{dummy_html_path}"

    # 1. Extract
    raw_data = extract_data(source_url)

    # 2. Transform
    transformed_df = transform_data(raw_data)

    # 3. Load
    load_data(transformed_df, db_name='product_catalog.db')

    print("\n--- ETL Process Completed for Project 1 ---")

    # Optional: Verify data in SQLite
    print("\n[Verification] Fetching data from product_catalog.db:")
    try:
        conn = sqlite3.connect('product_catalog.db')
        verification_df = pd.read_sql_query("SELECT * FROM products", conn)
        print(verification_df)
    except Exception as e:
        print(f"[Verification Error] Could not read from DB: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()           