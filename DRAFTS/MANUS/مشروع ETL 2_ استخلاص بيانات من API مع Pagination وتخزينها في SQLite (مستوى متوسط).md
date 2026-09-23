# مشروع ETL 2: استخلاص بيانات من API مع Pagination وتخزينها في SQLite (مستوى متوسط)

## 1. عنوان وفكرة المشروع

**العنوان:** بناء خط أنابيب ETL لاستخلاص بيانات المنشورات والمستخدمين من واجهة برمجة تطبيقات (API) مقسمة إلى صفحات (Paginated API)، وربطها وتخزينها في قاعدة بيانات SQLite علائقية.

**الفكرة:** في هذا المشروع، سنتعامل مع سيناريو أكثر تعقيداً حيث يتم جلب البيانات من واجهة برمجة تطبيقات RESTful تتطلب التعامل مع Pagination (تقسيم البيانات إلى صفحات). سنقوم باستخلاص بيانات المنشورات (Posts) والمستخدمين (Users) من API وهمية (JSONPlaceholder)، ثم نقوم بتحويلها وربطها منطقياً، وأخيراً تخزينها في قاعدة بيانات SQLite باستخدام جدولين مرتبطين (Users و Posts) لتمثيل العلاقة بينهما. هذا المشروع يركز على التعامل مع APIs، إدارة Pagination، ربط البيانات، والتخزين في قاعدة بيانات علائقية مع مفاتيح خارجية (Foreign Keys).

## 2. تصميم نمط البيانات (Data Model)

سنستخدم قاعدة بيانات SQLite لتخزين بيانات المستخدمين والمنشورات. سيتكون نمط البيانات من جدولين رئيسيين يمثلان **جداول الأبعاد (Dimension Tables)** و **جداول الحقائق (Fact Tables)** بشكل مبسط:

1.  **جدول الأبعاد: `users`** (يمثل معلومات المستخدمين)

    | اسم العمود  | نوع البيانات (SQLite) | الوصف                                        |
    | :---------- | :------------------- | :------------------------------------------- |
    | `user_id`   | `INTEGER PRIMARY KEY`| معرف فريد للمستخدم.                           |
    | `user_name` | `TEXT NOT NULL`      | اسم المستخدم.                                 |
    | `user_email`| `TEXT`               | البريد الإلكتروني للمستخدم.                   |

2.  **جدول الحقائق: `posts`** (يمثل معلومات المنشورات، ويرتبط بجدول `users`)

    | اسم العمود        | نوع البيانات (SQLite) | الوصف                                        |
    | :---------------- | :------------------- | :------------------------------------------- |
    | `post_id`         | `INTEGER PRIMARY KEY`| معرف فريد للمنشور.                            |
    | `user_id`         | `INTEGER NOT NULL`   | معرف المستخدم الذي كتب المنشور (مفتاح خارجي لجدول `users`). |
    | `title`           | `TEXT NOT NULL`      | عنوان المنشور.                                |
    | `body`            | `TEXT`               | محتوى المنشور.                                |
    | `extraction_date` | `TEXT NOT NULL`      | تاريخ ووقت استخلاص البيانات (بصيغة YYYY-MM-DD HH:MM:SS). |

**العلاقة:** `posts.user_id` يشير إلى `users.user_id` (علاقة واحد إلى متعدد: مستخدم واحد يمكن أن يكتب عدة منشورات).

## 3. مراحل الـ Pipeline

يتكون خط أنابيب ETL من ثلاث مراحل رئيسية:

### أ. مرحلة الاستخلاص (Extract)

*   **المصدر:** واجهة برمجة تطبيقات RESTful وهمية (JSONPlaceholder) توفر بيانات المنشورات والمستخدمين.
*   **الأداة:** مكتبة `requests` لجلب البيانات من API.
*   **الخطوات:**
    1.  تحديد عناوين URL الأساسية ونقاط النهاية (endpoints) لبيانات المنشورات والمستخدمين.
    2.  استخدام حلقة `while` لجلب البيانات صفحة تلو الأخرى (pagination) حتى لا تعود API بأي بيانات أخرى.
    3.  إرسال طلبات HTTP GET لكل صفحة، مع تضمين معلمات `_page` و `_limit` في الطلب.
    4.  التحقق من نجاح الاستجابة وتحويل JSON المستلم إلى قاموس/قائمة Python.
    5.  تجميع البيانات المستخلصة من جميع الصفحات في قائمة واحدة.
    6.  معالجة الأخطاء المحتملة أثناء جلب البيانات من API.
    7.  إضافة تأخير بسيط بين الطلبات لتجنب إثقال كاهل API (polite scraping).

### ب. مرحلة التحويل (Transform)

*   **المصدر:** قائمة البيانات الخام للمنشورات والمستخدمين المستخلصة من مرحلة الاستخلاص.
*   **الأداة:** مكتبة `Pandas` لمعالجة وتنظيف البيانات.
*   **الخطوات:**
    1.  تحويل بيانات المستخدمين الخام إلى Pandas DataFrame.
    2.  إعادة تسمية الأعمدة في DataFrame المستخدمين لتكون أكثر وضوحاً واتساقاً (مثل `id` إلى `user_id`).
    3.  **إزالة التكرار (Deduplication):** إزالة المستخدمين المكررين بناءً على `user_id`.
    4.  تحويل بيانات المنشورات الخام إلى Pandas DataFrame.
    5.  **معالجة القيم المفقودة (Missing Values):** ملء العناوين أو المحتوى المفقود في المنشورات بقيم افتراضية.
    6.  **إزالة التكرار (Deduplication):** إزالة المنشورات المكررة بناءً على `post_id`.
    7.  إعادة تسمية الأعمدة في DataFrame المنشورات (مثل `id` إلى `post_id` و `userId` إلى `user_id`).
    8.  ضمان أن `user_id` في جدول المنشورات هو نوع رقمي صحيح.
    9.  إضافة عمود `extraction_date` لكل من DataFrame المستخدمين والمنشورات.
    10. إعادة ترتيب الأعمدة في كلا DataFrame لضمان التناسق.

### ج. مرحلة التحميل (Load)

*   **المصدر:** DataFrame النظيف والمحول للمنشورات والمستخدمين.
*   **الأداة:** مكتبة `sqlite3` المدمجة في Python.
*   **الخطوات:**
    1.  الاتصال بقاعدة بيانات SQLite (إنشاء ملف قاعدة بيانات جديد إذا لم يكن موجوداً).
    2.  إنشاء جدول `users` إذا لم يكن موجوداً، مع تحديد الأعمدة والمفتاح الأساسي.
    3.  إنشاء جدول `posts` إذا لم يكن موجوداً، مع تحديد الأعمدة والمفتاح الأساسي والمفتاح الخارجي الذي يشير إلى جدول `users`.
    4.  تحميل بيانات المستخدمين إلى جدول `users`. في هذا المشروع، سنستخدم `if_exists=\'replace\'` لضمان تحديث بيانات المستخدمين في كل مرة يتم فيها تشغيل خط الأنابيب.
    5.  تحميل بيانات المنشورات إلى جدول `posts`. سنستخدم `if_exists=\'append\'` لإضافة المنشورات الجديدة.
    6.  معالجة الأخطاء المحتملة أثناء الاتصال بقاعدة البيانات أو تحميل البيانات.
    7.  إغلاق الاتصال بقاعدة البيانات بعد الانتهاء.

## 4. الكود البرمجي الكامل

تم توفير الكود البرمجي الكامل في الملف `etl_project_2_intermediate.py`.

## 5. الشرح التفصيلي والكتابي للكود (Line-by-Line Breakdown)

سيتم شرح كل دالة وجزء رئيسي من الكود أدناه، مع التركيز على المفاهيم المطلوبة.

### دالة `extract_data_from_api(base_url, endpoint, params=None, page_param="_page", limit_param="_limit", page_size=10)`

```python
import requests
import time
# ... (باقي الاستيرادات)

def extract_data_from_api(base_url, endpoint, params=None, page_param="_page", limit_param="_limit", page_size=10):
    all_data = []
    page = 1
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
            break # Stop if there\'s an error
        except Exception as e:
            print(f"[Extract Error] An unexpected error occurred during extraction: {e}")
            break
    print(f"[Extract] Total records extracted: {len(all_data)} from {endpoint}.")
    return all_data
```

*   **`import requests`, `import time`**: استيراد المكتبات اللازمة لجلب البيانات من API وإضافة تأخير.
*   **`all_data = []`, `page = 1`**: تهيئة قائمة لتخزين جميع البيانات المستخلصة ومتغير لتتبع رقم الصفحة الحالي.
*   **`while True:`**: حلقة لا نهائية للاستمرار في جلب الصفحات حتى لا تعود API بأي بيانات.
*   **`current_params = params.copy() if params else {}`**: إنشاء نسخة من المعلمات الأولية وإضافة معلمات `page_param` و `limit_param` إليها.
*   **`response = requests.get(full_url, params=current_params)`**: إرسال طلب GET إلى API مع المعلمات المحددة.
*   **`response.raise_for_status()`**: **معالجة الأخطاء (Exception Handling)**: يتحقق من نجاح الطلب. إذا كان هناك خطأ في HTTP (مثل 404 أو 500)، فإنه يثير استثناء.
*   **`page_data = response.json()`**: يحول استجابة JSON إلى كائن Python (عادةً قائمة من القواميس).
*   **`if not page_data: break`**: إذا كانت الصفحة المسترجعة فارغة، فهذا يعني أنه لا توجد المزيد من البيانات، لذا يتم إنهاء الحلقة.
*   **`all_data.extend(page_data)`**: إضافة البيانات المستخلصة من الصفحة الحالية إلى القائمة الكلية.
*   **`page += 1`**: زيادة رقم الصفحة للانتقال إلى الصفحة التالية.
*   **`time.sleep(0.1)`**: إضافة تأخير صغير (100 مللي ثانية) بين الطلبات. هذا يقلل من الضغط على الخادم ويساعد على تجنب حظر IP الخاص بك من قبل API (ممارسة جيدة لـ 
Polite Scraping).
*   **`except requests.exceptions.RequestException as e`**: يلتقط الأخطاء المتعلقة بطلبات `requests` (مثل مشاكل الشبكة أو أخطاء HTTP) ويوقف عملية الاستخلاص.
*   **`except Exception as e`**: يلتقط أي أخطاء أخرى غير متوقعة.

### دالة `transform_posts_data(posts_data, users_data)`

```python
import pandas as pd
from datetime import datetime
# ... (باقي الاستيرادات)

def transform_posts_data(posts_data, users_data):
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
```

*   **`users_df = pd.DataFrame(users_data)`**: تحويل قائمة قواميس المستخدمين إلى DataFrame.
*   **`users_df = users_df.rename(...)`**: إعادة تسمية الأعمدة لتكون أكثر وصفاً وتطابقاً مع نمط البيانات المستهدف.
*   **`users_df.drop_duplicates(subset=['user_id'], inplace=True)`**: **إزالة التكرار (Deduplication)**: إزالة أي صفوف مكررة في بيانات المستخدمين بناءً على `user_id`، مع افتراض أن `user_id` يجب أن يكون فريداً.
*   **`posts_df = pd.DataFrame(posts_data)`**: تحويل قائمة قواميس المنشورات إلى DataFrame.
*   **`posts_df['title'] = posts_df['title'].fillna('No Title')`**: **معالجة القيم المفقودة (Missing Values)**: ملء القيم المفقودة في عمود `title` بقيمة افتراضية.
*   **`posts_df['body'] = posts_df['body'].fillna('No Content')`**: **معالجة القيم المفقودة (Missing Values)**: ملء القيم المفقودة في عمود `body` بقيمة افتراضية.
*   **`posts_df.drop_duplicates(subset=['id'], inplace=True)`**: **إزالة التكرار (Deduplication)**: إزالة المنشورات المكررة بناءً على `id` الخاص بالمنشور.
*   **`posts_df = posts_df.rename(...)`**: إعادة تسمية الأعمدة في DataFrame المنشورات.
*   **`posts_df['user_id'] = pd.to_numeric(posts_df['user_id'], errors='coerce').fillna(-1).astype(int)`**: التأكد من أن `user_id` هو رقم صحيح. `errors='coerce'` يحول القيم غير الرقمية إلى `NaN`، ثم `fillna(-1)` يملأها بـ `-1` (يمكن أن يكون مؤشراً على مستخدم غير معروف أو غير صالح)، وأخيراً `astype(int)` يحول العمود إلى أعداد صحيحة.
*   **`posts_df['extraction_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')`**: إضافة عمود `extraction_date` لكل من المنشورات والمستخدمين.
*   **`posts_df = posts_df[['post_id', 'user_id', 'title', 'body', 'extraction_date']]`**: تحديد واعادة ترتيب الأعمدة في DataFrame المنشورات لضمان التناسق.

### دالة `load_data_to_sqlite(posts_df, users_df, db_name='blog_data.db')`

```python
import sqlite3
# ... (باقي الاستيرادات)

def load_data_to_sqlite(posts_df, users_df, db_name='blog_data.db'):
    print(f"[Load] Connecting to SQLite database: {db_name}")
    conn = None
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
```

*   **`conn = sqlite3.connect(db_name)`**: ينشئ اتصالاً بقاعدة بيانات SQLite.
*   **`cursor.execute(...)`**: ينفذ استعلامات SQL لإنشاء جدول `users` وجدول `posts` إذا لم يكونا موجودين. لاحظ تعريف `FOREIGN KEY (user_id) REFERENCES users (user_id)` في جدول `posts`، والذي ينشئ علاقة بين الجدولين.
*   **`users_df.to_sql('users', conn, if_exists='replace', index=False)`**: يحمل بيانات المستخدمين. `if_exists='replace'` يعني أنه إذا كان الجدول موجوداً، فسيتم حذفه وإعادة إنشائه بالبيانات الجديدة. هذا مفيد لضمان أن جدول المستخدمين يعكس دائماً أحدث حالة من API ويزيل أي مستخدمين قد لا يكونوا موجودين في الاستخلاص الحالي.
*   **`posts_df.to_sql('posts', conn, if_exists='append', index=False)`**: يحمل بيانات المنشورات. `if_exists='append'` يضيف المنشورات الجديدة إلى الجدول. في هذا السيناريو، نفترض أن `post_id` فريد وأننا نريد فقط إضافة منشورات جديدة، وليس تحديث المنشورات الموجودة (لأن المنشورات عادة لا تتغير بعد إنشائها).
*   **`except sqlite3.Error as e`**: **معالجة الأخطاء (Exception Handling)**: يلتقط الأخطاء الخاصة بـ SQLite.
*   **`finally: if conn: conn.close()`**: يضمن إغلاق الاتصال بقاعدة البيانات في جميع الأحوال.

### الجزء الرئيسي (`if __name__ == "__main__":`)

```python
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
```

*   **`API_BASE_URL`, `POSTS_ENDPOINT`, `USERS_ENDPOINT`**: تعريف الثوابت لعناوين URL ونقاط النهاية لـ API الوهمية.
*   **`raw_posts = extract_data_from_api(...)`**: استدعاء دالة الاستخلاص لجلب بيانات المنشورات.
*   **`raw_users = extract_data_from_api(...)`**: استدعاء دالة الاستخلاص لجلب بيانات المستخدمين.
*   **`transformed_posts_df, transformed_users_df = transform_posts_data(...)`**: استدعاء دالة التحويل لمعالجة كلا مجموعتي البيانات.
*   **`load_data_to_sqlite(...)`**: استدعاء دالة التحميل لتخزين البيانات في SQLite.
*   **جزء التحقق الاختياري**: بعد اكتمال عملية ETL، يتم الاتصال بقاعدة البيانات وقراءة البيانات من جدولي `users` و `posts` بشكل منفصل، ثم يتم تنفيذ استعلام `JOIN` بسيط لعرض كيفية ربط البيانات، مما يؤكد نجاح عملية التحميل والعلاقات بين الجداول.

## 6. تطوير ذاتي للمشروع

لزيادة تعقيد المشروع وتعميق فهمك، يمكنك محاولة تطبيق المهام الإضافية التالية باستخدام الأدوات المتاحة لديك فقط:

1.  **تنفيذ Upsert للمنشورات:** بدلاً من مجرد إلحاق المنشورات الجديدة (`if_exists='append'`)، قم بتعديل دالة `load_data_to_sqlite` لتنفيذ عملية Upsert لجدول `posts`. هذا يعني أنه إذا كان `post_id` موجوداً بالفعل، يتم تحديث المنشور (على سبيل المثال، تحديث `extraction_date` أو `body` إذا تغير)، وإلا يتم إدراج المنشور كصف جديد. يتطلب هذا استخدام استعلامات SQL مخصصة أو تقنيات متقدمة في `sqlite3`.
2.  **إضافة جدول للتعليقات (Comments):** قم بتوسيع خط الأنابيب ليشمل استخلاص بيانات التعليقات من API (نقطة النهاية `/comments` في JSONPlaceholder). قم بتصميم جدول `comments` جديد في نمط البيانات الخاص بك، مع مفتاح خارجي يشير إلى `posts.post_id`. ثم قم بتعديل دالتي `transform_data` و `load_data` لمعالجة هذه البيانات الجديدة وتخزينها بشكل صحيح.
3.  **معالجة الأخطاء بشكل أكثر تفصيلاً:** قم بتحسين معالجة الأخطاء في جميع المراحل لتسجيل الأخطاء في ملف سجل (log file) بدلاً من مجرد طباعتها على الشاشة. يمكنك استخدام مكتبة `logging` المدمجة في Python لهذا الغرض. هذا سيجعل خط الأنابيب أكثر قوة وسهولة في المراقبة في بيئة إنتاجية.
