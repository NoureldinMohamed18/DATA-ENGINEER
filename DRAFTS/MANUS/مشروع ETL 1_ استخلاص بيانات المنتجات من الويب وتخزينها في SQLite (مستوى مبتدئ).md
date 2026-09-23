# مشروع ETL 1: استخلاص بيانات المنتجات من الويب وتخزينها في SQLite (مستوى مبتدئ)

## 1. عنوان وفكرة المشروع

**العنوان:** بناء خط أنابيب ETL بسيط لاستخلاص معلومات المنتجات من كتالوج ويب ثابت وتخزينها في قاعدة بيانات محلية.

**الفكرة:** في هذا المشروع، سنقوم بمحاكاة سيناريو شائع في التجارة الإلكترونية حيث نحتاج إلى جمع بيانات المنتجات (مثل الاسم، السعر، الوصف) من صفحة ويب عامة. الهدف هو بناء خط أنابيب ETL (Extract, Transform, Load) باستخدام أدوات Python الأساسية لمعالجة هذه البيانات وتخزينها بشكل منظم في قاعدة بيانات SQLite محلية. هذا المشروع يركز على أساسيات الـ Web Scraping، معالجة البيانات باستخدام Pandas، والتخزين في قاعدة بيانات علائقية بسيطة.

## 2. تصميم نمط البيانات (Data Model)

سنستخدم قاعدة بيانات علائقية (SQLite) لتخزين بيانات المنتجات. نمط البيانات سيكون بسيطاً ويتكون من جدول واحد يمثل **جدول حقائق (Fact Table)** للمنتجات، حيث كل صف يمثل منتجاً فريداً.

**الجدول:** `products`

| اسم العمود        | نوع البيانات (SQLite) | الوصف                                        |
| :---------------- | :------------------- | :------------------------------------------- |
| `id`              | `INTEGER PRIMARY KEY AUTOINCREMENT` | معرف فريد لكل منتج.                          |
| `name`            | `TEXT NOT NULL`      | اسم المنتج.                                  |
| `price`           | `REAL NOT NULL`      | سعر المنتج.                                  |
| `description`     | `TEXT`               | وصف المنتج.                                  |
| `extraction_date` | `TEXT NOT NULL`      | تاريخ ووقت استخلاص البيانات (بصيغة YYYY-MM-DD HH:MM:SS). |

## 3. مراحل الـ Pipeline

يتكون خط أنابيب ETL من ثلاث مراحل رئيسية:

### أ. مرحلة الاستخلاص (Extract)

*   **المصدر:** صفحة ويب ثابتة (HTML) تحتوي على قائمة المنتجات.
*   **الأداة:** مكتبة `requests` لجلب محتوى الصفحة، ومكتبة `BeautifulSoup` لتحليل HTML واستخلاص البيانات المطلوبة.
*   **الخطوات:**
    1.  إرسال طلب HTTP GET إلى عنوان URL للصفحة المستهدفة.
    2.  التحقق من نجاح الاستجابة (HTTP Status Code 200).
    3.  تحليل محتوى HTML باستخدام `BeautifulSoup`.
    4.  البحث عن عناصر HTML التي تحتوي على معلومات المنتج (مثل `div` لكل منتج، و `h2` للاسم، و `span` للسعر، و `p` للوصف).
    5.  استخلاص الاسم والسعر والوصف لكل منتج وتجميعها في قائمة من القواميس (List of Dictionaries).
    6.  معالجة الأخطاء المحتملة أثناء جلب الصفحة أو تحليلها.

### ب. مرحلة التحويل (Transform)

*   **المصدر:** قائمة البيانات الخام المستخلصة من مرحلة الاستخلاص.
*   **الأداة:** مكتبة `Pandas` لمعالجة وتنظيف البيانات.
*   **الخطوات:**
    1.  تحويل قائمة القواميس إلى DataFrame من Pandas.
    2.  **معالجة القيم المفقودة (Missing Values):** ملء أي وصف مفقود بقيمة افتراضية مثل 
'No description available'.
    3.  **تنظيف وتحويل السعر:** إزالة أي رموز عملة أو فواصل من حقل السعر وتحويله إلى نوع بيانات رقمي (float). معالجة الحالات التي قد يكون فيها السعر فارغاً بعد التنظيف.
    4.  **إزالة التكرار (Deduplication):** تحديد وإزالة المنتجات المكررة بناءً على مزيج من الاسم والسعر لضمان فرادة البيانات.
    5.  إضافة عمود جديد لتسجيل تاريخ ووقت الاستخلاص (`extraction_date`).

### ج. مرحلة التحميل (Load)

*   **المصدر:** DataFrame النظيف والمحول من مرحلة التحويل.
*   **الأداة:** مكتبة `sqlite3` المدمجة في Python.
*   **الخطوات:**
    1.  الاتصال بقاعدة بيانات SQLite (إنشاء ملف قاعدة بيانات جديد إذا لم يكن موجوداً).
    2.  إنشاء جدول `products` إذا لم يكن موجوداً، مع تحديد الأعمدة وأنواع البيانات المناسبة.
    3.  تحميل البيانات من DataFrame إلى جدول `products` في قاعدة البيانات. في هذا المستوى، سنستخدم طريقة الإلحاق (`append`) لإضافة سجلات جديدة.
    4.  معالجة الأخطاء المحتملة أثناء الاتصال بقاعدة البيانات أو تحميل البيانات.
    5.  إغلاق الاتصال بقاعدة البيانات بعد الانتهاء.

## 4. الكود البرمجي الكامل

تم توفير الكود البرمجي الكامل في الملف `etl_project_1_beginner.py`.

## 5. الشرح التفصيلي والكتابي للكود (Line-by-Line Breakdown)

سيتم شرح كل دالة وجزء رئيسي من الكود أدناه، مع التركيز على المفاهيم المطلوبة.

### دالة `extract_data(url)`

```python
import requests
from bs4 import BeautifulSoup
# ... (باقي الاستيرادات)

def extract_data(url):
    print(f"[Extract] Attempting to fetch data from: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')

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
```

*   **`import requests`, `from bs4 import BeautifulSoup`**: استيراد المكتبات اللازمة لجلب صفحات الويب وتحليلها.
*   **`print(f"[Extract]...")`**: رسائل توضيحية لتتبع سير العمل.
*   **`try...except requests.exceptions.RequestException as e`**: **معالجة الأخطاء (Exception Handling)**: يلتقط هذا الجزء الأخطاء المتعلقة بطلبات HTTP (مثل عدم وجود اتصال بالإنترنت، أو خطأ 404/500 من الخادم). في حالة حدوث خطأ، يتم طباعة رسالة الخطأ وإرجاع قائمة فارغة لمنع تعطل خط الأنابيب.
*   **`response = requests.get(url)`**: يرسل طلب HTTP GET إلى عنوان URL المحدد لجلب محتوى الصفحة.
*   **`response.raise_for_status()`**: يتحقق مما إذا كان الطلب ناجحاً (رمز الحالة 200). إذا كان رمز الحالة يشير إلى خطأ (4xx أو 5xx)، فإنه يثير استثناء `HTTPError`.
*   **`soup = BeautifulSoup(response.text, 'html.parser')`**: يقوم بإنشاء كائن `BeautifulSoup` من محتوى HTML للصفحة، مما يسهل البحث عن العناصر.
*   **`product_elements = soup.find_all('div', class_='product-item')`**: يبحث عن جميع عناصر `div` التي تحتوي على الفئة `product-item`. هذا هو الافتراض الذي بني عليه الكود لتحديد كل منتج على الصفحة.
*   **`if not product_elements: ...`**: يتحقق مما إذا تم العثور على أي عناصر منتج. إذا لم يتم العثور عليها، يطبع رسالة تحذير.
*   **`for product in product_elements:`**: يتكرر على كل عنصر منتج تم العثور عليه.
*   **`name_element = product.find('h2', class_='product-name')`**: يبحث داخل عنصر المنتج الحالي عن اسم المنتج (افتراضياً في `h2` بفئة `product-name`).
*   **`name = name_element.text.strip() if name_element else 'N/A'`**: يستخلص النص من العنصر. إذا لم يتم العثور على العنصر (`name_element` هو `None`)، يتم تعيين القيمة الافتراضية 'N/A'. `strip()` يزيل المسافات البيضاء الزائدة.
*   **`products_data.append({...})`**: يضيف قاموساً يمثل المنتج المستخلص إلى القائمة.
*   **`except Exception as e`**: يلتقط أي استثناءات أخرى غير متوقعة قد تحدث أثناء الاستخلاص.

### دالة `transform_data(data)`

```python
import pandas as pd
from datetime import datetime
# ... (باقي الاستيرادات)

def transform_data(data):
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
```

*   **`import pandas as pd`**: استيراد مكتبة Pandas لمعالجة البيانات.
*   **`if not data: ...`**: يتحقق مما إذا كانت هناك بيانات للتحويل. إذا كانت القائمة فارغة، يتم إرجاع DataFrame فارغ.
*   **`df = pd.DataFrame(data)`**: يحول قائمة القواميس إلى Pandas DataFrame، وهو التنسيق المفضل لمعالجة البيانات.
*   **`df['description'] = df['description'].fillna('No description available')`**: **معالجة القيم المفقودة (Missing Values)**: يستخدم `fillna()` لملء أي قيم `NaN` (التي تمثل القيم المفقودة) في عمود `description` بالنص الافتراضي.
*   **`df['price'] = df['price'].astype(str).str.replace('[^\d.]', '', regex=True)`**: ينظف عمود السعر. أولاً، يتأكد من أن القيم هي سلاسل نصية، ثم يستخدم التعبيرات العادية (`regex=True`) لإزالة أي أحرف ليست أرقاماً أو نقطة عشرية. هذا يزيل رموز العملة والفواصل.
*   **`df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0.0)`**: يحول عمود السعر إلى نوع رقمي (`float`). `errors='coerce'` يحول أي قيم لا يمكن تحويلها إلى أرقام إلى `NaN`، ثم يتم ملء هذه القيم `NaN` بـ `0.0` باستخدام `fillna()`.
*   **`df.drop_duplicates(subset=['name', 'price'], inplace=True)`**: **إزالة التكرار (Deduplication)**: يزيل الصفوف المكررة من DataFrame. `subset=['name', 'price']` يحدد أن التكرار يتم تحديده بناءً على تطابق كل من الاسم والسعر. `inplace=True` يطبق التغيير مباشرة على DataFrame.
*   **`df['extraction_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')`**: يضيف عموداً جديداً يحتوي على الطابع الزمني الحالي، مما يوثق متى تم استخلاص البيانات.

### دالة `load_data(df, db_name='products.db', table_name='products')`

```python
import sqlite3
# ... (باقي الاستيرادات)

def load_data(df, db_name='products.db', table_name='products'):
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
```

*   **`import sqlite3`**: استيراد مكتبة SQLite المدمجة في Python.
*   **`if df.empty: ...`**: يتحقق مما إذا كان DataFrame فارغاً. إذا كان كذلك، لا توجد بيانات للتحميل.
*   **`try...except sqlite3.Error as e`**: **معالجة الأخطاء (Exception Handling)**: يلتقط الأخطاء الخاصة بقاعدة بيانات SQLite (مثل مشكلات الاتصال، أو أخطاء في الاستعلامات). يتم طباعة رسالة الخطأ.
*   **`conn = sqlite3.connect(db_name)`**: ينشئ اتصالاً بقاعدة بيانات SQLite. إذا لم يكن الملف موجوداً، فسيتم إنشاؤه.
*   **`cursor = conn.cursor()`**: ينشئ كائن مؤشر لتنفيذ أوامر SQL.
*   **`cursor.execute(f""" CREATE TABLE IF NOT EXISTS {table_name} (...) """)`**: ينفذ استعلام SQL لإنشاء الجدول `products` إذا لم يكن موجوداً بالفعل. هذا يضمن أن الجدول جاهز لاستقبال البيانات.
*   **`conn.commit()`**: يحفظ التغييرات التي تم إجراؤها على قاعدة البيانات (مثل إنشاء الجدول).
*   **`df.to_sql(table_name, conn, if_exists='append', index=False)`**: هذه هي الطريقة الأكثر ملاءمة لتحميل DataFrame إلى جدول SQLite. `if_exists='append'` يحدد أنه إذا كان الجدول موجوداً، فسيتم إلحاق البيانات الجديدة به. `index=False` يمنع Pandas من كتابة فهرس DataFrame كعمود في الجدول.
*   **`finally: ...`**: يضمن إغلاق الاتصال بقاعدة البيانات (`conn.close()`) حتى إذا حدث خطأ، وذلك لتحرير الموارد.

### الجزء الرئيسي (`if __name__ == "__main__":`)

```python
# --- Main ETL Process ---
if __name__ == "__main__":
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

    dummy_html_path = "/home/ubuntu/projects/codding-6564b468/dummy_products.html"
    with open(dummy_html_path, "w", encoding="utf-8") as f:
        f.write(dummy_html_content)
    print(f"[Setup] Created dummy HTML file at {dummy_html_path}")

    source_url = f"file://{dummy_html_path}"

    raw_data = extract_data(source_url)
    transformed_df = transform_data(raw_data)
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
```

*   **`if __name__ == "__main__":`**: يضمن أن الكود داخل هذه الكتلة سيتم تنفيذه فقط عند تشغيل الملف مباشرة (وليس عند استيراده كوحدة).
*   **`dummy_html_content = """..."""`**: لغرض العرض والتجربة، يتم إنشاء محتوى HTML وهمي يمثل صفحة ويب للمنتجات. هذا يسمح بتشغيل الكود دون الحاجة إلى الاتصال بإنترنت أو موقع ويب حقيقي.
*   **`dummy_html_path = "..."` و `with open(...)`**: يتم حفظ المحتوى الوهمي في ملف HTML محلي.
*   **`source_url = f"file://{dummy_html_path}"`**: يتم استخدام مسار الملف المحلي كعنوان URL للاستخلاص، مما يحاكي جلب البيانات من صفحة ويب.
*   **`raw_data = extract_data(source_url)`**: استدعاء دالة الاستخلاص.
*   **`transformed_df = transform_data(raw_data)`**: استدعاء دالة التحويل.
*   **`load_data(transformed_df, db_name='product_catalog.db')`**: استدعاء دالة التحميل.
*   **جزء التحقق الاختياري**: بعد اكتمال عملية ETL، يتم الاتصال بقاعدة البيانات مرة أخرى وقراءة جميع البيانات من جدول `products` وعرضها باستخدام Pandas DataFrame للتحقق من أن البيانات تم تحميلها بشكل صحيح.

## 6. تطوير ذاتي للمشروع

لزيادة تعقيد المشروع وتعميق فهمك، يمكنك محاولة تطبيق المهام الإضافية التالية باستخدام الأدوات المتاحة لديك فقط:

1.  **تحسين معالجة القيم المفقودة للسعر:** بدلاً من ملء السعر المفقود بـ `0.0`، حاول استبداله بمتوسط أسعار المنتجات الأخرى في نفس الفئة (إذا كان لديك فئات) أو بـ `None` والتعامل معه لاحقاً في التحليل. هذا يتطلب إضافة منطق لتحديد الفئات أو التعامل مع `None` في SQLite.
2.  **إضافة عمود جديد لـ `category`:** قم بتعديل محتوى HTML الوهمي لإضافة فئة لكل منتج (مثلاً، `data-category="Electronics"` في `div` المنتج). ثم قم بتعديل دالة `extract_data` لاستخلاص هذه الفئة، ودالة `transform_data` لتنظيفها، ودالة `load_data` لإضافة عمود `category` إلى جدول `products` في SQLite.
3.  **تطبيق تحديث البيانات (Upsert):** بدلاً من مجرد إلحاق البيانات (`if_exists='append'`)، قم بتعديل دالة `load_data` لتنفيذ عملية 
Upsert (Update or Insert). هذا يعني أنه إذا كان المنتج موجوداً بالفعل في قاعدة البيانات (يمكن تحديده بواسطة `name` و `price` مثلاً)، فيجب تحديث معلوماته (مثل `description` أو `extraction_date`). وإذا لم يكن موجوداً، فيجب إدراجه كصف جديد. هذا يتطلب استخدام استعلامات SQL أكثر تعقيداً أو استخدام ميزات `sqlite3` المتقدمة.
