# مشروع ETL 4: استخلاص بيانات من مصادر متعددة وتحويلها بشكل متقدم وتخزينها في SQLite (مستوى متقدم)

## 1. عنوان وفكرة المشروع

**العنوان:** بناء خط أنابيب ETL متقدم لدمج بيانات المنتجات من مصادر متعددة (Web Scraping و REST API)، وتطبيق تحويلات معقدة مثل إزالة التكرار الغامض (Fuzzy Deduplication) وتوحيد الفئات، ثم تخزينها في قاعدة بيانات SQLite علائقية مع جداول متعددة وعمليات Upsert.

**الفكرة:** في هذا المشروع، نرفع مستوى التعقيد من خلال التعامل مع بيانات المنتجات التي تأتي من مصدرين مختلفين: صفحة ويب ثابتة (باستخدام BeautifulSoup) وواجهة برمجة تطبيقات (API) (باستخدام requests). الهدف هو دمج هذه البيانات، وتطبيق تحويلات متقدمة مثل التعرف على المنتجات المتشابهة من مصادر مختلفة وإزالة التكرار بينها (حتى لو كانت أسماؤها مختلفة قليلاً)، وتوحيد تصنيفات المنتجات، وإضافة مقاييس مشتقة. أخيراً، سيتم تخزين البيانات في قاعدة بيانات SQLite تتضمن جداول للمنتجات والموردين، مع تطبيق منطق Upsert (تحديث أو إدراج) لضمان تحديث البيانات بكفاءة. هذا المشروع يركز على دمج البيانات من مصادر متباينة، تقنيات التحويل المتقدمة، وإدارة العلاقات في قواعد البيانات العلائقية.

## 2. تصميم نمط البيانات (Data Model)

سنستخدم قاعدة بيانات SQLite لتخزين بيانات المنتجات والموردين. سيتكون نمط البيانات من جدولين رئيسيين يمثلان **جدول أبعاد (Dimension Table)** للموردين و **جدول حقائق (Fact Table)** للمنتجات:

1.  **جدول الأبعاد: `suppliers`** (يمثل معلومات الموردين)

    | اسم العمود      | نوع البيانات (SQLite) | الوصف                                        |
    | :-------------- | :------------------- | :------------------------------------------- |
    | `supplier_id`   | `INTEGER PRIMARY KEY`| معرف فريد للمورد.                             |
    | `supplier_name` | `TEXT NOT NULL`      | اسم المورد.                                   |
    | `contact_email` | `TEXT`               | البريد الإلكتروني للمورد.                     |

2.  **جدول الحقائق: `products`** (يمثل معلومات المنتجات، ويرتبط بجدول `suppliers`)

    | اسم العمود        | نوع البيانات (SQLite) | الوصف                                        |
    | :---------------- | :------------------- | :------------------------------------------- |\n    | `product_id`      | `INTEGER PRIMARY KEY AUTOINCREMENT` | معرف فريد للمنتج.                            |
    | `name`            | `TEXT NOT NULL`      | اسم المنتج.                                  |
    | `description`     | `TEXT`               | وصف المنتج.                                  |
    | `category`        | `TEXT`               | فئة المنتج الموحدة.                           |
    | `price`           | `REAL NOT NULL`      | سعر المنتج.                                  |
    | `stock_quantity`  | `INTEGER`            | الكمية المتوفرة في المخزون (من API).          |
    | `supplier_id`     | `INTEGER`            | معرف المورد (مفتاح خارجي لجدول `suppliers`). |
    | `source`          | `TEXT NOT NULL`      | مصدر البيانات (مثل 'web_scrape' أو 'api').   |
    | `extraction_date` | `TEXT NOT NULL`      | تاريخ ووقت استخلاص البيانات.                 |
    | `is_in_stock`     | `BOOLEAN`            | هل المنتج متوفر في المخزون؟                   |

**العلاقة:** `products.supplier_id` يشير إلى `suppliers.supplier_id` (علاقة واحد إلى متعدد: مورد واحد يمكن أن يوفر عدة منتجات).

## 3. مراحل الـ Pipeline

يتكون خط أنابيب ETL من ثلاث مراحل رئيسية:

### أ. مرحلة الاستخلاص (Extract)

*   **المصادر:**
    *   صفحة ويب ثابتة (HTML) لبيانات المنتجات الأساسية.
    *   واجهة برمجة تطبيقات RESTful (API) لبيانات المنتجات الأكثر تفصيلاً (بما في ذلك المخزون والموردين).
*   **الأدوات:** مكتبة `requests` و `BeautifulSoup` لاستخلاص الويب، ومكتبة `requests` لاستخلاص API.
*   **الخطوات:**
    1.  استخلاص بيانات المنتجات من صفحة الويب باستخدام `requests` و `BeautifulSoup` (كما في المشروع الأول)، مع إضافة استخلاص الفئة إن وجدت.
    2.  استخلاص بيانات المنتجات من API باستخدام `requests`، مع التعامل مع Pagination (كما في المشروع الثاني). يتم إضافة حقل `source` لكل سجل لتحديد مصدره.
    3.  معالجة الأخطاء المحتملة أثناء جلب البيانات من كلا المصدرين.
    4.  تسجيل (logging) تفاصيل عملية الاستخلاص بدلاً من مجرد الطباعة.

### ب. مرحلة التحويل (Transform)

*   **المصدر:** البيانات الخام المستخلصة من الويب و API.
*   **الأداة:** مكتبة `Pandas` لمعالجة وتنظيف البيانات، ومكتبة `fuzzywuzzy` لإزالة التكرار الغامض.
*   **الخطوات:**
    1.  تحويل البيانات المستخلصة من الويب و API إلى Pandas DataFrames منفصلة.
    2.  **تنظيف البيانات الأولية:**
        *   معالجة القيم المفقودة (Missing Values) في الوصف والعنوان والفئات والمخزون.
        *   تنظيف وتحويل حقول السعر والمخزون إلى أنواع بيانات رقمية مناسبة.
        *   توحيد تنسيق أسماء المنتجات (مثل تحويلها إلى أحرف صغيرة وإزالة المسافات الزائدة) لتسهيل المقارنة.
    3.  **دمج البيانات (Consolidation):** دمج DataFrames من الويب و API في DataFrame واحد، مع التأكد من توافق الأعمدة.
    4.  **إزالة التكرار المتقدمة (Advanced Deduplication - Fuzzy Matching):**
        *   تحديد المنتجات المتشابهة (ولكن ليست متطابقة تماماً) بين المصدرين باستخدام `fuzzywuzzy` لمقارنة الأسماء، بالإضافة إلى مقارنة تقريبية للأسعار.
        *   دمج السجلات المكررة، مع إعطاء الأولوية للبيانات الأكثر اكتمالاً أو دقة (مثل تفضيل بيانات API التي تحتوي على معلومات المخزون والمورد).
    5.  **توحيد الفئات (Category Standardization):** تحويل الفئات المختلفة (مثل 'Laptops', 'Notebooks', 'Computers') إلى فئات موحدة (مثل 'Electronics').
    6.  **إثراء البيانات (Data Enrichment):** إضافة أعمدة مشتقة جديدة، مثل `is_in_stock` بناءً على `stock_quantity`.
    7.  إضافة عمود `extraction_date`.
    8.  تسجيل تفاصيل عملية التحويل.

### ج. مرحلة التحميل (Load)

*   **المصدر:** DataFrame النظيف والمحول والمدمج.
*   **الأداة:** مكتبة `sqlite3` المدمجة في Python.
*   **الخطوات:**
    1.  الاتصال بقاعدة بيانات SQLite.
    2.  إنشاء جدول `suppliers` وجدول `products` إذا لم يكونا موجودين، مع تحديد المفاتيح الأساسية والخارجية.
    3.  **تحميل بيانات الموردين (Upsert):** استخلاص الموردين الفريدين من بيانات المنتجات. تنفيذ عملية Upsert (تحديث أو إدراج) لجدول `suppliers` لضمان تحديث معلومات الموردين الموجودين وإضافة الجدد.
    4.  **تحميل بيانات المنتجات (Upsert):** تنفيذ عملية Upsert لجدول `products`. هذا يعني أنه إذا كان المنتج موجوداً بالفعل (بناءً على الاسم والسعر ومصدر البيانات)، يتم تحديث معلوماته؛ وإلا يتم إدراجه كصف جديد.
    5.  معالجة الأخطاء المحتملة أثناء الاتصال بقاعدة البيانات أو تحميل البيانات.
    6.  إغلاق الاتصال بقاعدة البيانات بعد الانتهاء.
    7.  تسجيل تفاصيل عملية التحميل.

## 4. الكود البرمجي الكامل

تم توفير الكود البرمجي الكامل في الملف `etl_project_4_advanced_multi_source_sqlite.py`.

## 5. الشرح التفصيلي والكتابي للكود (Line-by-Line Breakdown)

سيتم شرح كل دالة وجزء رئيسي من الكود أدناه، مع التركيز على المفاهيم المطلوبة.

### إعداد التسجيل (Logging Setup)

```python
import logging
# ... (باقي الاستيرادات)

# Setup logging
logging.basicConfig(filename=\'etl_project_4.log\', level=logging.INFO,
                    format=\'%(asctime)s - %(levelname)s - %(message)s\')
```

*   **`import logging`**: استيراد مكتبة التسجيل المدمجة في Python.
*   **`logging.basicConfig(...)`**: تهيئة نظام التسجيل. يتم توجيه جميع الرسائل ذات المستوى `INFO` أو أعلى إلى ملف `etl_project_4.log`. `format` يحدد تنسيق رسائل السجل، بما في ذلك الطابع الزمني، مستوى الرسالة، والرسالة نفسها. هذا يوفر طريقة أفضل لتتبع سير عمل خط الأنابيب واستكشاف الأخطاء وإصلاحها مقارنة بـ `print()`.

### دالة `extract_from_web(url)`

```python
import requests
from bs4 import BeautifulSoup
# ... (باقي الاستيرادات)

def extract_from_web(url):
    logging.info(f"[Extract Web] Attempting to fetch data from: {url}")
    products_data = []
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, \'html.parser\')

        product_elements = soup.find_all(\'div\', class_=\'product-item\')

        if not product_elements:
            logging.warning("[Extract Web] No product items found. Check selectors or URL.")

        for product in product_elements:
            name_element = product.find(\'h2\', class_=\'product-name\')
            price_element = product.find(\'span\', class_=\'product-price\')
            desc_element = product.find(\'p\', class_=\'product-description\')
            category_element = product.find(\'span\', class_=\'product-category\')

            name = name_element.text.strip() if name_element else \'N/A\'
            price = price_element.text.strip() if price_element else \'0.0\'
            description = desc_element.text.strip() if desc_element else \'\'
            category = category_element.text.strip() if category_element else \'Uncategorized\'

            products_data.append({
                \'name\': name,
                \'price\': price,
                \'description\': description,
                \'category\': category,
                \'source\': \'web_scrape\'
            })
        logging.info(f"[Extract Web] Successfully extracted {len(products_data)} products.")
        return products_data
    except requests.exceptions.RequestException as e:
        logging.error(f"[Extract Web Error] Failed to fetch URL {url}: {e}")
        return []
    except Exception as e:
        logging.error(f"[Extract Web Error] An unexpected error occurred during web extraction: {e}")
        return []
```

*   هذه الدالة مشابهة لدالة الاستخلاص في المشروع الأول، ولكنها تستخدم `logging.info` و `logging.error` بدلاً من `print` لتسجيل الرسائل. كما أنها تضيف استخلاص حقل `category` جديد وتعيين `source` كـ `web_scrape`.
*   **`timeout=10`**: يحدد مهلة زمنية لطلب HTTP، مما يمنع الطلب من التعليق إلى الأبد في حالة عدم استجابة الخادم. هذا جزء من **معالجة الأخطاء (Exception Handling)**.

### دالة `extract_from_api(base_url, endpoint, params=None, page_param="_page", limit_param="_limit", page_size=10)`

```python
import requests
import time
# ... (باقي الاستيرادات)

def extract_from_api(base_url, endpoint, params=None, page_param="_page", limit_param="_limit", page_size=10):
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
            response.raise_for_status()
            page_data = response.json()

            if not page_data:
                logging.info(f"[Extract API] No more data found on page {page}. Stopping pagination.")
                break

            for item in page_data:
                item[\'source\'] = \'api\'
                all_data.append(item)

            logging.info(f"[Extract API] Successfully fetched {len(page_data)} records from page {page}.")
            page += 1
            time.sleep(0.1)

        except requests.exceptions.RequestException as e:
            logging.error(f"[Extract API Error] Failed to fetch data from {full_url}: {e}")
            break
        except Exception as e:
            logging.error(f"[Extract API Error] An unexpected error occurred during API extraction: {e}")
            break
    logging.info(f"[Extract API] Total records extracted: {len(all_data)} from {endpoint}.")
    return all_data
```

*   هذه الدالة مشابهة لدالة الاستخلاص من API في المشروع الثاني، ولكنها تستخدم `logging` بدلاً من `print` وتضيف حقل `source` كـ `api` لكل سجل.

### دالة `transform_data(web_data, api_data)`

```python
import pandas as pd
from datetime import datetime
import re
from fuzzywuzzy import fuzz
# ... (باقي الاستيرادات)

def transform_data(web_data, api_data):
    logging.info("[Transform] Starting data transformation and consolidation.")

    web_df = pd.DataFrame(web_data)
    api_df = pd.DataFrame(api_data)

    # --- Web Data Transformations ---
    if not web_df.empty:
        web_df[\'description\'] = web_df[\'description\'].fillna(\'No description available\')
        web_df[\'price\'] = web_df[\'price\'].astype(str).str.replace(r\'[^\\d.]\', \'\', regex=True)
        web_df[\'price\'] = pd.to_numeric(web_df[\'price\'], errors=\'coerce\').fillna(0.0)
        web_df[\'name\'] = web_df[\'name\'].apply(lambda x: re.sub(r\'\\s+\', \' \', x).strip().lower())
        logging.info("[Transform] Cleaned web scraped data.")
    else:
        logging.warning("[Transform] No web data to transform.")

    # --- API Data Transformations ---
    if not api_df.empty:
        api_df = api_df.rename(columns={\'id\': \'api_product_id\', \'userId\': \'supplier_id\', \'product_name\': \'name\', \'product_description\': \'description\', \'current_price\': \'price\', \'available_stock\': \'stock_quantity\'}) # Renaming for consistency
        api_df[\'description\'] = api_df[\'description\'].fillna(\'No description available\')
        api_df[\'price\'] = pd.to_numeric(api_df[\'price\'], errors=\'coerce\').fillna(0.0)
        api_df[\'stock_quantity\'] = pd.to_numeric(api_df[\'stock_quantity\'], errors=\'coerce\').fillna(0).astype(int)
        api_df[\'category\'] = api_df[\'category\'].fillna(\'Uncategorized\')
        api_df[\'name\'] = api_df[\'name\'].apply(lambda x: re.sub(r\'\\s+\', \' \', x).strip().lower())
        api_df = api_df[[\'api_product_id\', \'name\', \'description\', \'category\', \'price\', \'stock_quantity\', \'supplier_id\', \'source\']]
        logging.info("[Transform] Cleaned API data.")
    else:
        logging.warning("[Transform] No API data to transform.")

    # --- Consolidate DataFrames ---
    common_cols = [\'name\', \'description\', \'category\', \'price\', \'source\']
    web_df_aligned = web_df[common_cols].copy() if not web_df.empty else pd.DataFrame(columns=common_cols)
    api_df_aligned = api_df[common_cols + [\'stock_quantity\', \'supplier_id\']].copy() if not api_df.empty else pd.DataFrame(columns=common_cols + [\'stock_quantity\', \'supplier_id\'])

    for col in [\'stock_quantity\', \'supplier_id\']:
        if col not in web_df_aligned.columns:
            web_df_aligned[col] = None

    for col in common_cols:
        if col not in api_df_aligned.columns:
            api_df_aligned[col] = None

    all_cols = list(set(web_df_aligned.columns) | set(api_df_aligned.columns))
    web_df_aligned = web_df_aligned.reindex(columns=all_cols)
    api_df_aligned = api_df_aligned.reindex(columns=all_cols)

    combined_df = pd.concat([web_df_aligned, api_df_aligned], ignore_index=True)
    logging.info(f"[Transform] Combined dataframes. Total records: {len(combined_df)}.")

    if combined_df.empty:
        logging.warning("[Transform] Combined DataFrame is empty. Skipping further transformations.")
        return pd.DataFrame()

    # --- Advanced Deduplication (Fuzzy Matching) ---
    deduplicated_products = []
    processed_indices = set()

    combined_df = combined_df.sort_values(by=\'name\').reset_index(drop=True)

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
            if fuzz.ratio(current_product[\'name\'], other_product[\'name\']) > 80 and \
               abs(current_product[\'price\'] - other_product[\'price\']) < 5:
                potential_duplicates.append(other_product)
                processed_indices.add(j)

        if len(potential_duplicates) > 1:
            merged_product = potential_duplicates[0].copy()
            for dup in potential_duplicates:
                if dup[\'source\'] == \'api\':
                    merged_product = dup.copy()
                    break
            for dup in potential_duplicates:
                for col in merged_product.index:
                    if pd.isna(merged_product[col]) and not pd.isna(dup[col]):
                        merged_product[col] = dup[col]
            deduplicated_products.append(merged_product)
            logging.info(f"[Transform] Merged duplicates for: {current_product[\'name\']}")
        else:
            deduplicated_products.append(current_product)

    final_df = pd.DataFrame(deduplicated_products)
    logging.info(f"[Transform] Deduplication complete. Final records: {len(final_df)}.")

    # --- Standardize Categories ---
    category_mapping = {
        \'laptops\': \'Electronics\',
        \'notebooks\': \'Electronics\',
        \'computers\': \'Electronics\',
        \'mouse\': \'Peripherals\',
        \'keyboard\': \'Peripherals\',
        \'ssd\': \'Storage\',
        \'hard drive\': \'Storage\',
        \'monitors\': \'Displays\',
        \'display\': \'Displays\',
        \'uncategorized\': \'Other\'
    }
    final_df[\'category\'] = final_df[\'category\'].str.lower().map(category_mapping).fillna(\'Other\')
    logging.info("[Transform] Standardized categories.")

    # --- Derived Metrics / Enrichment ---
    final_df[\'is_in_stock\'] = final_df[\'stock_quantity\'] > 0
    final_df[\'extraction_date\'] = datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')
    logging.info("[Transform] Added derived metrics and extraction date.")

    final_df[\'supplier_id\'] = pd.to_numeric(final_df[\'supplier_id\'], errors=\'coerce\').astype(\'Int64\')

    logging.info("[Transform] Data transformation complete.")
    return final_df
```

*   **`web_df = pd.DataFrame(web_data)`, `api_df = pd.DataFrame(api_data)`**: تحويل البيانات الخام من كلا المصدرين إلى DataFrames.
*   **تنظيف بيانات الويب و API**: يتم تطبيق عمليات تنظيف مماثلة للمشاريع السابقة (معالجة القيم المفقودة، تحويل الأنواع) على كلا DataFrame. لاحظ إعادة تسمية الأعمدة في `api_df` لتكون متسقة مع نمط البيانات المستهدف.
*   **`web_df[\'name\'] = web_df[\'name\'].apply(lambda x: re.sub(r\'\\s+\', \' \', x).strip().lower())`**: توحيد تنسيق أسماء المنتجات (إزالة المسافات الزائدة، تحويل إلى أحرف صغيرة) لتسهيل مقارنة التشابه لاحقاً. هذا جزء مهم من **إزالة التكرار (Deduplication)**.
*   **`combined_df = pd.concat([web_df_aligned, api_df_aligned], ignore_index=True)`**: دمج DataFrames من الويب و API بعد التأكد من توافق الأعمدة. هذا يجمع جميع المنتجات المحتملة في DataFrame واحد قبل إزالة التكرار.
*   **`from fuzzywuzzy import fuzz`**: استيراد مكتبة `fuzzywuzzy` التي توفر وظائف لمقارنة تشابه السلاسل النصية (Fuzzy String Matching).
*   **`for i in range(len(combined_df)): ...`**: حلقة تكرارية رئيسية لعملية إزالة التكرار الغامض.
*   **`fuzz.ratio(current_product[\'name\'], other_product[\'name\']) > 80`**: يستخدم `fuzz.ratio` لحساب نسبة التشابه بين اسمي منتجين. إذا كانت النسبة أعلى من 80 (قيمة قابلة للتعديل)، يتم اعتبار الاسمين متشابهين بشكل كافٍ.
*   **`abs(current_product[\'price\'] - other_product[\'price\']) < 5`**: يتحقق من أن الأسعار متقاربة (بفارق أقل من 5 وحدات عملة) كمعيار إضافي لتحديد التكرار. هذا يمنع دمج منتجات مختلفة تماماً ولكن لها أسماء متشابهة بالصدفة.
*   **دمج التكرارات**: إذا تم العثور على منتجات مكررة محتملة، يتم دمجها في سجل واحد. يتم إعطاء الأولوية للبيانات من مصدر API (إذا كانت موجودة) لأنها غالباً ما تكون أكثر اكتمالاً (تحتوي على المخزون والمورد). يتم أيضاً ملء القيم المفقودة في السجل المدمج بالقيم الموجودة في السجلات المكررة الأخرى.
*   **`category_mapping = {...}`**: قاموس لتوحيد الفئات المختلفة إلى مجموعة قياسية من الفئات. هذا جزء من **معالجة القيم المفقودة (Missing Values)** و **تنظيف البيانات (Data Cleaning)**.
*   **`final_df[\'category\'] = final_df[\'category\'].str.lower().map(category_mapping).fillna(\'Other\')`**: تطبيق خريطة الفئات على عمود `category` وتحويل أي فئات غير معروفة إلى 'Other'.
*   **`final_df[\'is_in_stock\'] = final_df[\'stock_quantity\'] > 0`**: إنشاء عمود مشتق جديد `is_in_stock` بناءً على قيمة `stock_quantity`. هذا مثال على **إثراء البيانات (Data Enrichment)**.
*   **`final_df[\'supplier_id\'] = ... .astype(\'Int64\')`**: التأكد من أن `supplier_id` هو نوع رقمي قابل للقيم الفارغة (`Int64` في Pandas يدعم `NaN` للأعداد الصحيحة).

### دالة `load_data_to_sqlite(df, db_name=\'ecommerce.db\')`

```python
import sqlite3
# ... (باقي الاستيرادات)

def load_data_to_sqlite(df, db_name=\'ecommerce.db\'):
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
        logging.info("[Load] Table \'suppliers\' ensured to exist.")

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
        logging.info("[Load] Table \'products\' ensured to exist.")

        # --- Load Suppliers Data (Upsert) ---
        suppliers_df = df[df[\'supplier_id\'].notna()][[\'supplier_id\']].drop_duplicates().copy()
        suppliers_df[\'supplier_name\'] = \'Supplier \' + suppliers_df[\'supplier_id\'].astype(str)
        suppliers_df[\'contact_email\'] = \'contact@supplier\' + suppliers_df[\'supplier_id\'].astype(str) + \'.com\'

        if not suppliers_df.empty:
            for index, row in suppliers_df.iterrows():
                cursor.execute("""
                    INSERT INTO suppliers (supplier_id, supplier_name, contact_email)
                    VALUES (?, ?, ?)
                    ON CONFLICT(supplier_id) DO UPDATE SET
                        supplier_name=excluded.supplier_name,
                        contact_email=excluded.contact_email
                """, (row[\'supplier_id\'], row[\'supplier_name\'], row[\'contact_email\']))
            conn.commit()
            logging.info(f"[Load] Upserted {len(suppliers_df)} suppliers.")
        else:
            logging.info("[Load] No supplier data to load.")

        # --- Load Products Data (Simplified Upsert) ---
        web_products_to_load = df[df[\'source\'] == \'web_scrape\'].copy()
        if not web_products_to_load.empty:
            for index, row in web_products_to_load.iterrows():
                cursor.execute("DELETE FROM products WHERE name = ? AND price = ? AND source = ?",
                               (row[\'name\'], row[\'price\'], \'web_scrape\'))
            conn.commit()
            web_products_to_load.to_sql(\'products\', conn, if_exists=\'append\', index=False, method=\'multi\')
            conn.commit()
            logging.info(f"[Load] Upserted {len(web_products_to_load)} web scraped products.")

        api_products_to_load = df[df[\'source\'] == \'api\'].copy()
        if not api_products_to_load.empty:
            for index, row in api_products_to_load.iterrows():
                cursor.execute("DELETE FROM products WHERE name = ? AND supplier_id = ? AND source = ?",
                               (row[\'name\'], row[\'supplier_id\'], \'api\'))
            conn.commit()
            api_products_to_load.to_sql(\'products\', conn, if_exists=\'append\', index=False, method=\'multi\')
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
```

*   **إنشاء الجداول**: يتم إنشاء جدول `suppliers` وجدول `products` مع تعريف المفتاح الخارجي `supplier_id` في جدول `products` الذي يشير إلى `suppliers.supplier_id`.
*   **تحميل بيانات الموردين (Upsert)**:
    *   يتم استخلاص الموردين الفريدين من DataFrame المنتجات.
    *   يتم استخدام حلقة `for` مع استعلام `INSERT ... ON CONFLICT DO UPDATE` لتنفيذ عملية Upsert. هذا الاستعلام يقوم بإدراج صف جديد إذا لم يكن `supplier_id` موجوداً بالفعل، أو يقوم بتحديث الصف الموجود إذا كان `supplier_id` موجوداً. هذا يضمن أن جدول الموردين يتم تحديثه باستمرار.
*   **تحميل بيانات المنتجات (Simplified Upsert)**:
    *   نظراً لعدم وجود معرف فريد عالمي للمنتجات عبر كلا المصدرين بعد الدمج الغامض، يتم تطبيق عملية Upsert مبسطة.
    *   بالنسبة للمنتجات المستخلصة من الويب (`web_scrape`): يتم حذف أي منتجات موجودة مسبقاً تتطابق في `name` و `price` و `source`، ثم يتم إدراج المنتجات الجديدة. هذا يضمن أن أحدث بيانات الويب هي التي يتم الاحتفاظ بها.
    *   بالنسبة للمنتجات المستخلصة من API (`api`): يتم حذف أي منتجات موجودة مسبقاً تتطابق في `name` و `supplier_id` و `source`، ثم يتم إدراج المنتجات الجديدة. هذا يضمن تحديث بيانات API.
    *   **`method=\'multi\'`**: عند استخدام `to_sql`، يمكن أن يحسن `method=\'multi\'` الأداء عند إدراج عدد كبير من الصفوف.
*   **`except sqlite3.Error as e`**: **معالجة الأخطاء (Exception Handling)**: يلتقط الأخطاء الخاصة بـ SQLite.
*   **`finally: ...`**: يضمن إغلاق الاتصال بقاعدة البيانات.

### الجزء الرئيسي (`if __name__ == "__main__":`)

```python
# --- Main ETL Process ---
if __name__ == "__main__":
    # Install fuzzywuzzy and python-Levenshtein if not already installed
    # sudo pip3 install fuzzywuzzy python-Levenshtein

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

    dummy_api_data = [
        {"id": 101, "userId": 1, "product_name": "Laptop Pro", "product_description": "High-end laptop for demanding tasks.", "current_price": 1202.00, "available_stock": 50, "category": "Computers"},
        {"id": 102, "userId": 1, "product_name": "Gaming Mouse", "product_description": "Precision gaming mouse.", "current_price": 30.00, "available_stock": 120, "category": "Peripherals"},
        {"id": 103, "userId": 2, "product_name": "Portable SSD 1TB", "product_description": "Ultra-fast external storage.", "current_price": 149.99, "available_stock": 80, "category": "Hard Drive"},
        {"id": 104, "userId": 3, "product_name": "4K Monitor", "product_description": "Stunning 4K display.", "current_price": 350.00, "available_stock": 30, "category": "Displays"},
        {"id": 105, "userId": 1, "product_name": "Wireless Mouse", "product_description": "Ergonomic wireless mouse.", "current_price": 26.50, "available_stock": 200, "category": "Peripherals"}
    ]

    dummy_web_html_path = "/home/ubuntu/projects/codding-6564b468/dummy_web_products.html"
    with open(dummy_web_html_path, "w", encoding="utf-8") as f:
        f.write(dummy_web_html_content)
    logging.info(f"[Setup] Created dummy web HTML file at {dummy_web_html_path}")

    web_products = extract_from_web(f"file://{dummy_web_html_path}")
    api_products = dummy_api_data
    logging.info("[Main] Finished extraction from web and API (simulated).")

    transformed_products_df = transform_data(web_products, api_products)
    logging.info("[Main] Finished data transformation.")

    load_data_to_sqlite(transformed_products_df, db_name=\'ecommerce_advanced.db\')
    logging.info("[Main] Finished data loading.")

    print("\n--- ETL Process Completed for Project 4 ---")

    # Optional: Verify data in SQLite
    print("\n[Verification] Fetching data from ecommerce_advanced.db:")
    try:
        conn = sqlite3.connect(\'ecommerce_advanced.db\')
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
```

*   **`dummy_web_html_content` و `dummy_api_data`**: يتم إنشاء بيانات وهمية لكل من الويب و API لمحاكاة المصادر الحقيقية. هذا يسمح بتشغيل الكود بشكل مستقل.
*   **`web_products = extract_from_web(...)`**: استدعاء دالة الاستخلاص من الويب.
*   **`api_products = dummy_api_data`**: في هذا المثال، يتم استخدام البيانات الوهمية مباشرة بدلاً من استدعاء `extract_from_api` مع URL حقيقي، لتبسيط التنفيذ في بيئة Sandbox. في سيناريو حقيقي، سيتم استدعاء `extract_from_api` مع `API_BASE_URL` و `API_ENDPOINT`.
*   **`transformed_products_df = transform_data(web_products, api_products)`**: استدعاء دالة التحويل لدمج ومعالجة البيانات من كلا المصدرين.
*   **`load_data_to_sqlite(...)`**: استدعاء دالة التحميل لتخزين البيانات في SQLite.
*   **جزء التحقق الاختياري**: يتم التحقق من البيانات في جداول `suppliers` و `products`، ويتم عرض استعلام `JOIN` لإظهار العلاقة بين المنتجات والموردين.

## 6. تطوير ذاتي للمشروع

لزيادة تعقيد المشروع وتعميق فهمك، يمكنك محاولة تطبيق المهام الإضافية التالية باستخدام الأدوات المتاحة لديك فقط:

1.  **تحسين إزالة التكرار الغامض (Fuzzy Deduplication):**
    *   استكشف استخدام تقنيات أكثر تقدماً في `fuzzywuzzy` مثل `fuzz.token_set_ratio` أو `fuzz.partial_ratio` التي قد تكون أكثر فعالية لبعض أنواع الأسماء. جرب دمج هذه المقاييس مع بعضها البعض.
    *   نفذ "كتلة" (blocking) للبيانات قبل تطبيق المقارنة الغامضة. بدلاً من مقارنة كل منتج بكل منتج آخر (مما يؤدي إلى تعقيد زمني كبير O(N^2))، قم أولاً بتجميع المنتجات في مجموعات أصغر بناءً على سمات متطابقة تماماً (مثل الحرف الأول من الاسم، أو الفئة). ثم طبق المقارنة الغامضة فقط داخل هذه الكتل. هذا سيحسن الأداء بشكل كبير على مجموعات البيانات الكبيرة.
2.  **إضافة مصدر بيانات ثالث (ملف CSV/JSON محلي):** قم بإنشاء ملف CSV أو JSON وهمي يحتوي على بيانات منتجات إضافية (مثل تقييمات العملاء أو تواريخ الإطلاق). قم بتعديل مرحلة الاستخلاص لقراءة هذا الملف باستخدام Pandas، ثم قم بدمج هذه البيانات مع البيانات الموجودة من الويب و API في مرحلة التحويل. سيتطلب هذا تحديث منطق إزالة التكرار والتحميل للتعامل مع مصدر البيانات الجديد.
3.  **تطبيق مفهوم "البيانات البطيئة التغير" (Slowly Changing Dimensions - SCD Type 2):**
    *   في جدول `products`، بدلاً من مجرد تحديث السجلات الموجودة، قم بتتبع التغييرات في سمات معينة (مثل `price` أو `description`). عندما يتغير سعر منتج ما، بدلاً من تحديث السجل الحالي، قم بإنشاء سجل جديد للمنتج مع السعر الجديد وتاريخ بدء الصلاحية، وقم بتعيين تاريخ انتهاء الصلاحية للسجل القديم. هذا يسمح بالاحتفاظ بسجل تاريخي للتغييرات. سيتطلب هذا تعديلات كبيرة في نمط البيانات (إضافة `start_date`, `end_date`, `is_current`) وفي منطق Upsert في مرحلة التحميل باستخدام استعلامات SQL معقدة.
