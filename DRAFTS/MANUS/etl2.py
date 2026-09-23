import requests
import pandas as pd
import sqlite3
from datetime import datetime
import time

def extract_api(base_url,endpoint,params=None,page_param="_page", limit_param="_limit", page_size=10):
    """
        Extracts data from a paginated REST API.
        Args:
            base_url (str): The base URL of the API.
            endpoint (str): The specific API endpoint (e.g., "/posts").
            params (dict, optional): Initial query parameters. Defaults to None.
            page_param (str): The name of the query parameter for the page number.
            limit_param (str): The name of the query parameter for the page size.
            page_size (int): The number of items per page.
        Returns:
            list: A list of dictionaries, each representing a record from the API.
    """
    all_data=[]
    page=1
    while True:
            current_params = params.copy() if params else {}
            current_params[page_param] = page
            current_params[limit_param] = page_size
            full_url = f"{base_url}{endpoint}"
    
            print(f"[Extract] Fetching from: {full_url} with params: {current_params}")
            try:
                response = requests.get(full_url, params=current_params)
                response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
                page_data = response.json()
    
                if not page_data:
                    print(f"[Extract] No more data found on page {page}. Stopping pagination.")
                    break
    
                all_data.extend(page_data)
                print(f"[Extract] Successfully fetched {len(page_data)} records from page {page}.")
                page += 1
                time.sleep(0.1) # Small delay to be polite to the API
    
            except requests.exceptions.RequestException as e:
                print(f"[Extract Error] Failed to fetch data from {full_url}: {e}")
                break # Stop if there's an error
            except Exception as e:
                print(f"[Extract Error] An unexpected error occurred during extraction: {e}")
                break
    print(f"[Extract] Total records extracted: {len(all_data)} from {endpoint}.")
    return all_data
    
def transform_posts_data(posts_data, users_data):
    """
    Transforms and cleans the extracted posts and users data.
    Args:
        posts_data (list): A list of dictionaries with raw post data.
        users_data (list): A list of dictionaries with raw user data.
    Returns:
        tuple: A tuple containing two pandas.DataFrame objects (transformed_posts_df, transformed_users_df).
    """
    print("[Transform] Starting data transformation for posts and users.")

    # Transform Users Data
    users_df = pd.DataFrame(users_data)
    if not users_df.empty:
        users_df = users_df.rename(columns={
            'id': 'user_id',
            'name': 'user_name',
            'email': 'user_email'
        })
        users_df = users_df[['user_id', 'user_name', 'user_email']]
        users_df.drop_duplicates(subset=['user_id'], inplace=True)
        print(f"[Transform] Transformed {len(users_df)} unique users.")
    else:
        print("[Transform] No user data to transform.")
        users_df = pd.DataFrame(columns=['user_id', 'user_name', 'user_email'])

    # Transform Posts Data
    posts_df = pd.DataFrame(posts_data)
    if not posts_df.empty:
        # Handle Missing Values: Fill empty body/title
        posts_df['title'] = posts_df['title'].fillna('No Title')
        posts_df['body'] = posts_df['body'].fillna('No Content')
        print("[Transform] Handled missing post titles and bodies.")

        # Deduplication: Remove duplicate posts based on id (assuming id is unique for posts)
        initial_posts_rows = len(posts_df)
        posts_df.drop_duplicates(subset=['id'], inplace=True)
        if len(posts_df) < initial_posts_rows:
            print(f"[Transform] Removed {initial_posts_rows - len(posts_df)} duplicate posts.")
        else:
            print("[Transform] No duplicate posts found.")

        # Rename 'id' to 'post_id' for clarity and 'userId' to 'user_id' for consistency
        posts_df = posts_df.rename(columns={'id': 'post_id', 'userId': 'user_id'})

        # Ensure user_id is numeric
        posts_df['user_id'] = pd.to_numeric(posts_df['user_id'], errors='coerce').fillna(-1).astype(int)

        # Add extraction date
        posts_df['extraction_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("[Transform] Added extraction date to posts.")

        # Select and reorder columns for posts
        posts_df = posts_df[['post_id', 'user_id', 'title', 'body', 'extraction_date']]

    else:
        print("[Transform] No post data to transform.")
        posts_df = pd.DataFrame(columns=['post_id', 'user_id', 'title', 'body', 'extraction_date'])

    print("[Transform] Data transformation complete.")
    return posts_df, users_df
def load_data_to_sqlite(posts_df, users_df, db_name='blog_data.db'):
    """
    Loads the transformed posts and users data into an SQLite database.
    Args:
        posts_df (pandas.DataFrame): DataFrame containing transformed post data.
        users_df (pandas.DataFrame): DataFrame containing transformed user data.
        db_name (str): The name of the SQLite database file.
    """
    print(f"[Load] Connecting to SQLite database: {db_name}")
    conn = None # Initialize conn to None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                user_name TEXT NOT NULL,
                user_email TEXT
            )
        """)
        conn.commit()
        print("[Load] Table 'users' ensured to exist.")

        # Create posts table with foreign key to users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                post_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                body TEXT,
                extraction_date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        conn.commit()
        print("[Load] Table 'posts' ensured to exist.")

        # Load users data (using replace to handle updates/deduplication on user_id)
        if not users_df.empty:
            users_df.to_sql('users', conn, if_exists='replace', index=False)
            print(f"[Load] Successfully loaded {len(users_df)} rows into 'users'.")
        else:
            print("[Load] No user data to load.")

        # Load posts data (using append for new posts, assuming post_id is unique and new posts are added)
        # For a more robust solution, consider upsert logic for posts as well.
        if not posts_df.empty:
            posts_df.to_sql('posts', conn, if_exists='append', index=False)
            print(f"[Load] Successfully loaded {len(posts_df)} rows into 'posts'.")
        else:
            print("[Load] No post data to load.")

    except sqlite3.Error as e:
        print(f"[Load Error] SQLite error: {e}")
    except Exception as e:
        print(f"[Load Error] An unexpected error occurred during loading: {e}")
    finally:
        if conn:
            conn.close()
            print("[Load] SQLite connection closed.")

# --- Main ETL Process ---
if __name__ == "__main__":
    API_BASE_URL = "https://jsonplaceholder.typicode.com"
    POSTS_ENDPOINT = "/posts"
    USERS_ENDPOINT = "/users"

    print("\n--- Starting ETL Process for Project 2 ---")

    # 1. Extract
    raw_posts = extract_data_from_api(API_BASE_URL, POSTS_ENDPOINT, page_size=10)
    raw_users = extract_data_from_api(API_BASE_URL, USERS_ENDPOINT, page_size=10)

    # 2. Transform
    transformed_posts_df, transformed_users_df = transform_posts_data(raw_posts, raw_users)

    # 3. Load
    load_data_to_sqlite(transformed_posts_df, transformed_users_df, db_name='blog_data.db')

    print("\n--- ETL Process Completed for Project 2 ---")

    # Optional: Verify data in SQLite
    print("\n[Verification] Fetching data from blog_data.db:")
    try:
        conn = sqlite3.connect('blog_data.db')
        print("\nUsers Table:")
        verification_users_df = pd.read_sql_query("SELECT * FROM users", conn)
        print(verification_users_df)

        print("\nPosts Table:")
        verification_posts_df = pd.read_sql_query("SELECT * FROM posts", conn)
        print(verification_posts_df)

        print("\nJoined Data (first 5 rows):")
        joined_df = pd.read_sql_query("""
            SELECT
                p.post_id, p.title, p.body, p.extraction_date,
                u.user_name, u.user_email
            FROM posts p
            JOIN users u ON p.user_id = u.user_id
            LIMIT 5
        """, conn)
        print(joined_df)

    except Exception as e:
        print(f"[Verification Error] Could not read from DB: {e}")
    finally:
        if conn:
            conn.close()
