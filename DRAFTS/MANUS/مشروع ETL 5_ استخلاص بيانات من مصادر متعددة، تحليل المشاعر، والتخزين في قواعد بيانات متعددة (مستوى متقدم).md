# مشروع ETL 5: استخلاص بيانات من مصادر متعددة، تحليل المشاعر، والتخزين في قواعد بيانات متعددة (مستوى متقدم)

## 1. عنوان وفكرة المشروع

**العنوان:** بناء خط أنابيب ETL متكامل لاستخلاص بيانات المنتجات من API، واستخلاص مراجعات المنتجات الديناميكية من الويب، وإجراء تحليل المشاعر على المراجعات، ثم تخزين البيانات المنظمة في قاعدة بيانات علائقية (SQLite) والبيانات شبه المهيكلة (المراجعات) في قاعدة بيانات NoSQL (MongoDB).

**الفكرة:** يمثل هذا المشروع تتويجاً للمفاهيم المكتسبة، حيث يجمع بين الاستخلاص من مصادر متعددة (API لبيانات المنتجات الأساسية، و Selenium لصفحات مراجعات المنتجات الديناميكية)، وتطبيق تحويلات معقدة تتضمن **تحليل المشاعر (Sentiment Analysis)** على النصوص، ودمج البيانات، ثم التحميل إلى نظامي تخزين مختلفين: SQLite لبيانات المنتجات المنظمة مع ملخصات المراجعات، و MongoDB لتخزين المراجعات الخام مع نتائج تحليل المشاعر. هذا السيناريو شائع في أنظمة التجارة الإلكترونية التي تحتاج إلى جمع بيانات المنتجات والمراجعات لتحليلها واتخاذ القرارات. يركز المشروع على التعامل مع أنواع بيانات مختلفة، وتطبيق منطق عمل معقد، واستخدام قواعد بيانات متعددة بفعالية.

## 2. تصميم نمط البيانات (Data Model)

سنستخدم قاعدتي بيانات لتخزين البيانات، كل منهما مناسبة لنوع معين من البيانات:

1.  **SQLite (قاعدة بيانات علائقية):** لتخزين بيانات المنتجات والموردين، بالإضافة إلى ملخصات المراجعات المجمعة لكل منتج.

    *   **جدول الأبعاد: `suppliers`** (يمثل معلومات الموردين)

        | اسم العمود      | نوع البيانات (SQLite) | الوصف                                        |
        | :-------------- | :------------------- | :------------------------------------------- |
        | `supplier_id`   | `INTEGER PRIMARY KEY`| معرف فريد للمورد.                             |
        | `supplier_name` | `TEXT NOT NULL`      | اسم المورد.                                   |
        | `contact_email` | `TEXT`               | البريد الإلكتروني للمورد.                     |

    *   **جدول الحقائق: `products`** (يمثل معلومات المنتجات وملخصات المراجعات، ويرتبط بجدول `suppliers`)

        | اسم العمود        | نوع البيانات (SQLite) | الوصف                                        |
        | :---------------- | :------------------- | :------------------------------------------- |
        | `product_id`      | `INTEGER PRIMARY KEY`| معرف فريد للمنتج.                            |
        | `name`            | `TEXT NOT NULL`      | اسم المنتج.                                  |
        | `description`     | `TEXT`               | وصف المنتج.                                  |
        | `category`        | `TEXT`               | فئة المنتج.                                   |
        | `price`           | `REAL NOT NULL`      | سعر المنتج.                                  |
        | `stock_quantity`  | `INTEGER`            | الكمية المتوفرة في المخزون.                   |
        | `supplier_id`     | `INTEGER`            | معرف المورد (مفتاح خارجي لجدول `suppliers`). |
        | `avg_review_score`| `REAL`               | متوسط تقييمات المراجعات للمنتج.              |
        | `total_reviews`   | `INTEGER`            | العدد الإجمالي للمراجعات للمنتج.              |
        | `last_updated`    | `TEXT NOT NULL`      | تاريخ ووقت آخر تحديث لسجل المنتج.             |

    **العلاقة:** `products.supplier_id` يشير إلى `suppliers.supplier_id`.

2.  **MongoDB (قاعدة بيانات NoSQL):** لتخزين المراجعات الخام لكل منتج، بما في ذلك نص المراجعة، التقييم، اسم المراجع، وتاريخ المراجعة، بالإضافة إلى نتيجة تحليل المشاعر.

    *   **المجموعة: `reviews`**

    **مثال على مستند المراجعة:**

    ```json
    {
      "_id": ObjectId("65d4e1f8a1b2c3d4e5f6a7b8"),
      "product_id": 1,
      "review_text": "This product is great! I love it.",
      "review_score": 5,
      "reviewer_name": "Alice",
      "review_date": "2023-01-15",
      "sentiment": "Positive",
      "extraction_date": "2023-10-27 10:30:00"
    }
    ```

    | الحقل            | نوع البيانات (MongoDB) | الوصف                                        |
    | :--------------- | :-------------------- | :------------------------------------------- |
    | `_id`            | `ObjectId`            | معرف فريد للمستند.                           |
    | `product_id`     | `Int32`               | معرف المنتج الذي تنتمي إليه المراجعة.         |
    | `review_text`    | `String`              | نص المراجعة.                                 |
    | `review_score`   | `Int32`               | تقييم المراجعة (مثلاً من 1 إلى 5).            |
    | `reviewer_name`  | `String`              | اسم المراجع.                                 |
    | `review_date`    | `String`              | تاريخ المراجعة.                              |
    | `sentiment`      | `String`              | نتيجة تحليل المشاعر (Positive, Negative, Neutral). |
    | `extraction_date`| `String`              | تاريخ ووقت استخلاص المراجعة.                 |

## 3. مراحل الـ Pipeline

يتكون خط أنابيب ETL من ثلاث مراحل رئيسية:

### أ. مرحلة الاستخلاص (Extract)

*   **المصادر:**
    *   واجهة برمجة تطبيقات RESTful (API) لبيانات المنتجات الأساسية (مثل `JSONPlaceholder`).
    *   صفحات ويب ديناميكية تحتوي على مراجعات المنتجات (تتطلب تفاعلاً) لكل منتج على حدة.
*   **الأدوات:** مكتبة `requests` لاستخلاص API، ومكتبة `Selenium` و `BeautifulSoup` لاستخلاص مراجعات الويب.
*   **الخطوات:**
    1.  استخلاص بيانات المنتجات من API باستخدام `requests`، مع التعامل مع Pagination (كما في المشروع الثاني). يتم جلب `product_id`, `name`, `description`, `price`, `category`, `supplier_id`.
    2.  إعداد متصفح Chrome في وضع headless باستخدام `selenium.webdriver`.
    3.  لكل منتج تم استخلاصه، يتم الانتقال إلى صفحة المراجعات الخاصة به (التي يتم إنشاؤها ديناميكياً).
    4.  محاكاة التفاعل الديناميكي (التمرير أو النقر على زر "تحميل المزيد") لجلب جميع المراجعات المتاحة لكل منتج.
    5.  تحليل محتوى HTML للصفحة باستخدام `BeautifulSoup` لاستخلاص نص المراجعة، التقييم، اسم المراجع، وتاريخ المراجعة.
    6.  تجميع البيانات المستخلصة (المنتجات والمراجعات) في قوائم منفصلة من القواميس.
    7.  معالجة الأخطاء المحتملة أثناء جلب البيانات من كلا المصدرين.
    8.  تسجيل (logging) تفاصيل عملية الاستخلاص.

### ب. مرحلة التحويل (Transform)

*   **المصدر:** البيانات الخام للمنتجات والمراجعات المستخلصة.
*   **الأداة:** مكتبة `Pandas` لمعالجة وتنظيف البيانات.
*   **الخطوات:**
    1.  تحويل البيانات الخام للمنتجات والمراجعات إلى Pandas DataFrames منفصلة.
    2.  **تنظيف بيانات المنتجات:**
        *   إعادة تسمية الأعمدة لتكون متسقة مع نمط البيانات المستهدف.
        *   معالجة القيم المفقودة في الوصف والفئات.
        *   تحويل حقل السعر إلى نوع بيانات رقمي.
        *   إزالة المنتجات المكررة بناءً على `product_id`.
    3.  **تنظيف بيانات المراجعات:**
        *   تحويل `review_score` إلى نوع رقمي.
        *   معالجة القيم المفقودة في نص المراجعة وتاريخها.
        *   إزالة المراجعات المكررة بناءً على `product_id`, `review_text`, `reviewer_name`.
    4.  **تحليل المشاعر (Sentiment Analysis):** تطبيق دالة بسيطة لتحليل المشاعر على عمود `review_text` في DataFrame المراجعات، وتصنيف كل مراجعة على أنها "Positive", "Negative", أو "Neutral". (نظراً للقيود، سيتم استخدام تحليل مشاعر قائم على الكلمات المفتاحية).
    5.  **تجميع بيانات المراجعات للمنتجات:** حساب متوسط `review_score` والعدد الإجمالي للمراجعات (`total_reviews`) لكل `product_id`.
    6.  **إثراء بيانات المنتجات:** دمج بيانات المراجعات المجمعة (متوسط التقييم والعدد الإجمالي) مع DataFrame المنتجات.
    7.  إضافة عمود `last_updated` لـ DataFrame المنتجات وعمود `extraction_date` لـ DataFrame المراجعات.
    8.  تسجيل تفاصيل عملية التحويل.

### ج. مرحلة التحميل (Load)

*   **المصدر:** DataFrames المنتجات والمراجعات المحولة.
*   **الأدوات:** مكتبة `sqlite3` لـ SQLite، ومكتبة `PyMongo` لـ MongoDB.
*   **الخطوات:**
    1.  **التحميل إلى SQLite:**
        *   الاتصال بقاعدة بيانات SQLite.
        *   إنشاء جدول `suppliers` وجدول `products` إذا لم يكونا موجودين، مع تعريف المفاتيح الأساسية والخارجية.
        *   تنفيذ عملية Upsert لجدول `suppliers` (تحديث أو إدراج الموردين).
        *   تنفيذ عملية Upsert لجدول `products` (تحديث أو إدراج المنتجات، بما في ذلك بيانات المراجعات المجمعة).
        *   إغلاق الاتصال بـ SQLite.
    2.  **التحميل إلى MongoDB:**
        *   الاتصال بخادم MongoDB.
        *   تحديد قاعدة البيانات والمجموعة المستهدفة (مثلاً `product_analytics.reviews`).
        *   تحويل DataFrame المراجعات إلى قائمة من المستندات.
        *   إدراج المستندات في مجموعة `reviews`. (للتوضيح، سيتم مسح المجموعة قبل الإدراج لتجنب التكرار في كل مرة يتم فيها تشغيل خط الأنابيب، ولكن في سيناريو حقيقي قد يتم استخدام Upsert بناءً على معرف فريد للمراجعة).
        *   إغلاق الاتصال بـ MongoDB.
    3.  معالجة الأخطاء المحتملة أثناء التحميل إلى أي من قاعدتي البيانات.
    4.  تسجيل تفاصيل عملية التحميل.

## 4. الكود البرمجي الكامل

تم توفير الكود البرمجي الكامل في الملف `etl_project_5_advanced_multi_db_sentiment.py`.

## 5. الشرح التفصيلي والكتابي للكود (Line-by-Line Breakdown)

سيتم شرح كل دالة وجزء رئيسي من الكود أدناه، مع التركيز على المفاهيم المطلوبة.

### إعداد التسجيل (Logging Setup) و `setup_selenium_driver()`

```python
import logging
# ... (باقي الاستيرادات)

# Setup logging
logging.basicConfig(filename=\'etl_project_5.log\', level=logging.INFO,
                    format=\'%(asctime)s - %(levelname)s - %(message)s\')

def setup_selenium_driver():
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
```

*   هذه الأجزاء مطابقة لتلك الموجودة في المشروع الرابع والمشروع الثالث على التوالي، مع استخدام `logging` بدلاً من `print`.

### دالة `extract_products_from_api(base_url, endpoint, page_param="_page", limit_param="_limit", page_size=10)`

```python
import requests
import time
# ... (باقي الاستيرادات)

def extract_products_from_api(base_url, endpoint, page_param="_page", limit_param="_limit", page_size=10):
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
                item["category"] = item.get("category", "Electronics")
                item["supplier_id"] = item.get("userId", 1)
                all_products.append(item)

            logging.info(f"[Extract API] Successfully fetched {len(page_data)} products from page {page}.")
            page += 1
            time.sleep(0.1)

        except requests.exceptions.RequestException as e:
            logging.error(f"[Extract API Error] Failed to fetch products from {full_url}: {e}")
            break
        except Exception as e:
            logging.error(f"[Extract API Error] An unexpected error occurred during API product extraction: {e}")
            break
    logging.info(f"[Extract API] Total products extracted: {len(all_products)}.")
    return all_products
```

*   هذه الدالة مشابهة لدالة `extract_from_api` في المشروع الرابع، ولكنها تركز على استخلاص بيانات المنتجات وتضيف حقول `category` و `supplier_id` افتراضية إذا لم تكن موجودة في بيانات API الخام.

### دالة `extract_reviews_from_web(driver, product_ids, base_review_url_template, max_scrolls=1)`

```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
# ... (باقي الاستيرادات)

def extract_reviews_from_web(driver, product_ids, base_review_url_template, max_scrolls=1):
    all_reviews = []
    for product_id in product_ids:
        review_url = base_review_url_template.format(product_id)
        logging.info(f"[Extract Web] Navigating to reviews for product {product_id} at: {review_url}")
        try:
            driver.get(review_url)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".review-item"))
            )

            for i in range(max_scrolls):
                try:
                    load_more_button = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".load-more-reviews"))
                    )
                    load_more_button.click()
                    time.sleep(1)
                except:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
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
            continue
    return all_reviews
```

*   تستخدم هذه الدالة `Selenium` و `BeautifulSoup` لاستخلاص المراجعات من صفحات ويب ديناميكية، وهي امتداد لدالة `extract_dynamic_data` من المشروع الثالث.
*   تتلقى قائمة بـ `product_ids` وتكرر عليها، وتنتقل إلى صفحة المراجعات لكل منتج.
*   تتعامل مع التمرير أو أزرار "تحميل المزيد" لجلب جميع المراجعات.
*   تستخلص `review_text`, `review_score`, `reviewer_name`, `review_date` لكل مراجعة.
*   **`continue` في `except`**: يسمح هذا بالاستمرار في استخلاص المراجعات للمنتجات الأخرى حتى لو فشل استخلاص مراجعات منتج واحد، مما يعزز مرونة خط الأنابيب.

### دالة `analyze_sentiment(text)`

```python
def analyze_sentiment(text):
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
```

*   هذه دالة بسيطة لـ **تحليل المشاعر (Sentiment Analysis)** تعتمد على الكلمات المفتاحية. نظراً للقيود بعدم استخدام مكتبات NLP خارجية، فإنها تقوم بحساب عدد الكلمات الإيجابية والسلبية الموجودة في النص وتصنف المشاعر بناءً على ذلك.
*   **`positive_keywords`, `negative_keywords`**: قوائم بالكلمات التي تشير إلى مشاعر إيجابية أو سلبية.
*   **`sum(1 for keyword in ... if keyword in text_lower)`**: يحسب عدد مرات ظهور الكلمات المفتاحية في النص.

### دالة `transform_data(raw_products, raw_reviews)`

```python
import pandas as pd
from datetime import datetime
# ... (باقي الاستيرادات)

def transform_data(raw_products, raw_reviews):
    logging.info("[Transform] Starting data transformation and consolidation.")

    # --- Products Data Transformation ---
    products_df = pd.DataFrame(raw_products)
    if not products_df.empty:
        products_df = products_df.rename(columns={
            "id": "product_id",
            "title": "name",
            "body": "description",
            "price": "price"
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
        aggregated_reviews = reviews_df.groupby("product_id").agg(
            avg_review_score=("review_score", \'mean\'),
            total_reviews=("product_id", \'count\')
        ).reset_index()
        products_df = pd.merge(products_df, aggregated_reviews, on="product_id", how="left")
        products_df[["avg_review_score", "total_reviews"]] = products_df[["avg_review_score", "total_reviews"]].fillna(0)
        products_df["avg_review_score"] = products_df["avg_review_score"].round(2)
        logging.info("[Transform] Aggregated review data for products.")
    else:
        products_df["avg_review_score"] = 0.0
        products_df["total_reviews"] = 0

    products_df["last_updated"] = datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')

    logging.info("[Transform] Data transformation complete.")
    return products_df, reviews_df
```

*   **تحويل بيانات المنتجات**: مشابه للمشاريع السابقة، مع إعادة تسمية الأعمدة لتتناسب مع نمط البيانات الجديد.
*   **تحويل بيانات المراجعات**: تنظيف `review_score` و `review_date`، ومعالجة القيم المفقودة في `review_text`.
*   **`reviews_df["sentiment"] = reviews_df["review_text"].apply(analyze_sentiment)`**: تطبيق دالة `analyze_sentiment` على كل نص مراجعة لإنشاء عمود `sentiment` جديد. هذا هو جوهر **تحليل المشاعر (Sentiment Analysis)**.
*   **`reviews_df.drop_duplicates(subset=["product_id", "review_text", "reviewer_name"], inplace=True)`**: **إزالة التكرار (Deduplication)** للمراجعات بناءً على مجموعة من الأعمدة لضمان فرادة المراجعة.
*   **`aggregated_reviews = reviews_df.groupby("product_id").agg(...)`**: تجميع المراجعات لحساب `avg_review_score` و `total_reviews` لكل منتج. هذا مثال على **إثراء البيانات (Data Enrichment)**.
*   **`products_df = pd.merge(products_df, aggregated_reviews, on="product_id", how="left")`**: دمج البيانات المجمعة للمراجعات مع DataFrame المنتجات.
*   **`products_df["last_updated"] = datetime.now().strftime(...)`**: إضافة طابع زمني لآخر تحديث للمنتجات.

### دالة `load_data_to_sqlite_and_mongodb(products_df, reviews_df, sqlite_db_name=\'ecommerce_final.db\', mongo_db_name=\'product_analytics\', mongo_collection_name=\'reviews\')`

```python
import sqlite3
from pymongo import MongoClient
# ... (باقي الاستيرادات)

def load_data_to_sqlite_and_mongodb(products_df, reviews_df, sqlite_db_name=\'ecommerce_final.db\', mongo_db_name=\'product_analytics\', mongo_collection_name=\'reviews\'):
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

            reviews_df["extraction_date"] = datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')

            reviews_records = reviews_df.to_dict(orient=\'records\')

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
```

*   **التحميل إلى SQLite**: يتم إنشاء جداول `suppliers` و `products` (مع المفتاح الخارجي). يتم استخدام منطق Upsert (باستخدام `ON CONFLICT DO UPDATE`) لكل من الموردين والمنتجات لضمان تحديث السجلات الموجودة وإدراج السجلات الجديدة. هذا يضمن أن جدول المنتجات في SQLite يحتوي دائماً على أحدث معلومات المنتجات وملخصات المراجعات.
*   **التحميل إلى MongoDB**: يتم الاتصال بـ MongoDB. قبل إدراج المراجعات، يتم مسح المجموعة (`mongo_collection.delete_many({})`) لضمان تحميل جديد في كل مرة. ثم يتم تحويل DataFrame المراجعات إلى قائمة من القواميس وإدراجها في المجموعة باستخدام `insert_many()`. هذا يحافظ على المراجعات الخام مع تحليل المشاعر في MongoDB، مما يوفر مرونة أكبر للتحليلات المستقبلية التي قد تتطلب الوصول إلى البيانات الأصلية.
*   **معالجة الأخطاء (Exception Handling)**: يتم استخدام كتل `try...except...finally` لكل عملية تحميل لضمان إغلاق الاتصالات بقواعد البيانات بشكل صحيح وتسجيل أي أخطاء.

### الجزء الرئيسي (`if __name__ == "__main__":`)

```python
# --- Main ETL Process ---
if __name__ == "__main__":
    dummy_api_products = [
        {"id": 1, "title": "Laptop Pro", "body": "High-end laptop for demanding tasks.", "price": 1200.50, "stock_quantity": 50, "category": "Laptops", "userId": 1},
        {"id": 2, "title": "Wireless Mouse", "body": "Ergonomic wireless mouse.", "price": 25.99, "stock_quantity": 200, "category": "Peripherals", "userId": 1},
        {"id": 3, "title": "External SSD 1TB", "body": "Ultra-fast external storage.", "price": 150.00, "stock_quantity": 80, "category": "Storage", "userId": 2},
        {"id": 4, "title": "4K Monitor", "body": "Stunning 4K display.", "price": 350.00, "stock_quantity": 30, "category": "Displays", "userId": 3},
        {"id": 5, "title": "Gaming Keyboard", "body": "Mechanical keyboard for gamers.", "price": 75.00, "stock_quantity": 100, "category": "Peripherals", "userId": 1}
    ]

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
        raw_products = dummy_api_products
        logging.info("[Main] Finished product extraction from API (simulated).")

        selenium_driver = setup_selenium_driver()
        if selenium_driver is None:
            logging.error("[Main] Failed to setup WebDriver. Cannot extract reviews. Exiting.")
            raw_reviews = []
        else:
            raw_reviews = extract_reviews_from_web(selenium_driver, product_ids_for_reviews, "file:///home/ubuntu/projects/codding-6564b468/dummy_reviews_{}.html", max_scrolls=1)
            logging.info("[Main] Finished review extraction from web.")

        transformed_products_df, transformed_reviews_df = transform_data(raw_products, raw_reviews)
        logging.info("[Main] Finished data transformation.")

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
```

*   **`dummy_api_products`**: بيانات منتجات وهمية تحاكي الاستجابة من API.
*   **`dummy_review_html_template`**: قالب HTML وهمي لصفحات مراجعات المنتجات، يتضمن JavaScript لمحاكاة تحميل المراجعات ديناميكياً.
*   **إنشاء ملفات HTML وهمية للمراجعات**: يتم إنشاء ملف HTML منفصل لكل منتج بناءً على `product_id`، مما يسمح لـ Selenium بزيارة كل صفحة مراجعة بشكل فردي.
*   **سير عمل ETL الرئيسي**: يتم استدعاء دوال الاستخلاص والتحويل والتحميل بالتسلسل.
*   **جزء التحقق الاختياري**: يتم التحقق من البيانات في كل من SQLite (جداول `products` و `suppliers`) و MongoDB (مجموعة `reviews`) للتأكد من أن البيانات تم تحميلها بشكل صحيح في كلا النظامين.

## 6. تطوير ذاتي للمشروع

لزيادة تعقيد المشروع وتعميق فهمك، يمكنك محاولة تطبيق المهام الإضافية التالية باستخدام الأدوات المتاحة لديك فقط:

1.  **تحسين تحليل المشاعر:**
    *   قم بتوسيع قوائم الكلمات المفتاحية الإيجابية والسلبية في دالة `analyze_sentiment` لتشمل المزيد من المرادفات والعبارات الشائعة في سياق مراجعات المنتجات.
    *   أضف منطقاً للتعامل مع النفي (مثل "ليس جيداً") أو الكلمات التي تغير معنى الكلمة المفتاحية. على سبيل المثال، يمكن أن تكون كلمة "good" إيجابية، ولكن "not good" سلبية.
    *   حاول تطبيق نظام نقاط بسيط حيث يتم إعطاء نقاط مختلفة للكلمات المفتاحية بناءً على قوتها، ثم يتم جمع هذه النقاط لتحديد المشاعر بشكل أكثر دقة.
2.  **تنفيذ Upsert للمراجعات في MongoDB:** بدلاً من مسح مجموعة المراجعات وإعادة إدراجها في كل مرة، قم بتعديل دالة `load_data_to_mongodb` لتنفيذ عملية Upsert للمراجعات. سيتطلب ذلك تحديد مفتاح فريد لكل مراجعة (مثلاً، مزيج من `product_id`, `review_text`, `reviewer_name`) واستخدام `update_one` مع `upsert=True` أو `bulk_write`.
3.  **إضافة جدول للتحليلات المجمعة في SQLite:** قم بإنشاء جدول جديد في SQLite (مثلاً `product_analytics`) لتخزين تحليلات مجمعة إضافية للمنتجات، مثل عدد المراجعات الإيجابية والسلبية والمتوسطة لكل منتج، أو المنتج الأعلى تقييماً في كل فئة. سيتطلب هذا تعديل مرحلة التحويل لإجراء هذه التجميعات الإضافية وتعديل مرحلة التحميل لإدراجها في الجدول الجديد. هذا يفصل بين البيانات الخام والمراجعات المجمعة، مما يجعل الاستعلامات التحليلية أسرع.))

## References

[1] JSONPlaceholder. *Free fake API for testing and prototyping.* [https://jsonplaceholder.typicode.com/](https://jsonplaceholder.typicode.com/)
[2] SQLite. *SQLite Home Page.* [https://www.sqlite.org/index.html](https://www.sqlite.org/index.html)
[3] MongoDB. *MongoDB Developer Hub.* [https://www.mongodb.com/docs/](https://www.mongodb.com/docs/)
[4] Pandas. *pandas documentation.* [https://pandas.pydata.org/docs/](https://pandas.pydata.org/docs/)
[5] Requests. *Requests: HTTP for Humans™.* [https://requests.readthedocs.io/en/latest/](https://requests.readthedocs.io/en/latest/)
[6] BeautifulSoup. *Beautiful Soup Documentation.* [https://www.crummy.com/software/BeautifulSoup/bs4/doc/](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
[7] Selenium. *Selenium Documentation.* [https://www.selenium.dev/documentation/](https://www.selenium.dev/documentation/)
[8] PyMongo. *PyMongo Documentation.* [https://pymongo.readthedocs.io/en/stable/](https://pymongo.readthedocs.io/en/stable/)
[9] FuzzyWuzzy. *FuzzyWuzzy documentation.* [https://chairnerd.github.io/fuzzywuzzy/](https://chairnerd.github.io/fuzzywuzzy/)
