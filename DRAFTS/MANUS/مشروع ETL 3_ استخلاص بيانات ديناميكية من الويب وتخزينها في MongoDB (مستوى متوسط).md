# مشروع ETL 3: استخلاص بيانات ديناميكية من الويب وتخزينها في MongoDB (مستوى متوسط)

## 1. عنوان وفكرة المشروع

**العنوان:** بناء خط أنابيب ETL لاستخلاص بيانات المنتجات من صفحات ويب ديناميكية (تتطلب تفاعلاً مثل التمرير أو النقر على زر "تحميل المزيد") باستخدام Selenium و BeautifulSoup، وتخزينها في قاعدة بيانات NoSQL (MongoDB).

**الفكرة:** في هذا المشروع، سنتعامل مع تحدٍ شائع في استخلاص البيانات: صفحات الويب الديناميكية التي يتم تحميل محتواها باستخدام JavaScript (مثل التمرير اللانهائي أو أزرار "تحميل المزيد"). سنستخدم Selenium لمحاكاة تفاعل المستخدم مع المتصفح وجلب المحتوى الديناميكي، ثم BeautifulSoup لتحليل HTML المستخلص. بعد ذلك، سنقوم بتنظيف البيانات باستخدام Pandas وتخزينها في قاعدة بيانات MongoDB، وهي قاعدة بيانات NoSQL مناسبة للبيانات غير المهيكلة أو شبه المهيكلة. هذا المشروع يركز على تقنيات Web Scraping المتقدمة، والتعامل مع البيانات الديناميكية، والتخزين في بيئة NoSQL.

## 2. تصميم نمط البيانات (Data Model)

سنستخدم قاعدة بيانات NoSQL (MongoDB) لتخزين بيانات المنتجات. في MongoDB، يتم تخزين البيانات في **مجموعات (Collections)**، وكل سجل يسمى **مستند (Document)**. المستندات هي هياكل JSON-like مرنة.

**المجموعة:** `products`

**مثال على مستند المنتج:**

```json
{
  "_id": ObjectId("65d4e1f8a1b2c3d4e5f6a7b8"),
  "name": "Dynamic Laptop X",
  "price": 1500.00,
  "description": "High-performance dynamic laptop.",
  "extraction_date": "2023-10-27 10:30:00"
}
```

| الحقل            | نوع البيانات (MongoDB) | الوصف                                        |
| :--------------- | :-------------------- | :------------------------------------------- |
| `_id`            | `ObjectId`            | معرف فريد للمستند (يتم إنشاؤه تلقائياً بواسطة MongoDB). |
| `name`           | `String`              | اسم المنتج.                                  |
| `price`          | `Double`              | سعر المنتج.                                  |
| `description`    | `String`              | وصف المنتج.                                  |
| `extraction_date`| `String`              | تاريخ ووقت استخلاص البيانات (بصيغة YYYY-MM-DD HH:MM:SS). |

## 3. مراحل الـ Pipeline

يتكون خط أنابيب ETL من ثلاث مراحل رئيسية:

### أ. مرحلة الاستخلاص (Extract)

*   **المصدر:** صفحة ويب ديناميكية (HTML) تتطلب تفاعلاً (مثل التمرير أو النقر على زر "تحميل المزيد").
*   **الأداة:** مكتبة `Selenium` لمحاكاة المتصفح، ومكتبة `BeautifulSoup` لتحليل HTML.
*   **الخطوات:**
    1.  إعداد متصفح Chrome في وضع headless (بدون واجهة رسومية) باستخدام `selenium.webdriver`.
    2.  الانتقال إلى عنوان URL للصفحة المستهدفة باستخدام `driver.get(url)`.
    3.  الانتظار حتى يتم تحميل المحتوى الأولي للصفحة باستخدام `WebDriverWait` و `expected_conditions`.
    4.  محاكاة التفاعل الديناميكي: إما التمرير لأسفل الصفحة (`driver.execute_script("window.scrollTo...")`) أو النقر على زر "تحميل المزيد" (`load_more_button.click()`) لعدة مرات محددة أو حتى لا يظهر المزيد من المحتوى.
    5.  بعد تحميل كل المحتوى الديناميكي، يتم الحصول على مصدر الصفحة الكامل (`driver.page_source`).
    6.  تحليل محتوى HTML باستخدام `BeautifulSoup` لاستخلاص بيانات المنتج (الاسم، السعر، الوصف) بنفس الطريقة المستخدمة في المشروع الأول.
    7.  تجميع البيانات المستخلصة في قائمة من القواميس.
    8.  معالجة الأخطاء المحتملة أثناء إعداد WebDriver أو التفاعل مع الصفحة.
    9.  إغلاق WebDriver بعد الانتهاء.

### ب. مرحلة التحويل (Transform)

*   **المصدر:** قائمة البيانات الخام المستخلصة من مرحلة الاستخلاص.
*   **الأداة:** مكتبة `Pandas` لمعالجة وتنظيف البيانات.
*   **الخطوات:**
    1.  تحويل قائمة القواميس إلى DataFrame من Pandas.
    2.  **معالجة القيم المفقودة (Missing Values):** ملء أي وصف مفقود بقيمة افتراضية.
    3.  **تنظيف وتحويل السعر:** إزالة أي رموز عملة أو فواصل من حقل السعر وتحويله إلى نوع بيانات رقمي (float). معالجة الحالات التي قد يكون فيها السعر فارغاً بعد التنظيف.
    4.  **إزالة التكرار (Deduplication):** إزالة المنتجات المكررة بناءً على مزيج من الاسم والسعر لضمان فرادة البيانات.
    5.  إضافة عمود جديد لتسجيل تاريخ ووقت الاستخلاص (`extraction_date`).

### ج. مرحلة التحميل (Load)

*   **المصدر:** DataFrame النظيف والمحول من مرحلة التحويل.
*   **الأداة:** مكتبة `PyMongo` (عميل Python لـ MongoDB).
*   **الخطوات:**
    1.  الاتصال بخادم MongoDB (افتراضياً على `localhost:27017`).
    2.  تحديد قاعدة البيانات والمجموعة المستهدفة.
    3.  تحويل DataFrame إلى قائمة من المستندات (قواميس Python) لتكون جاهزة للإدراج في MongoDB.
    4.  إدراج المستندات في المجموعة باستخدام `insert_many()`. في هذا المستوى، سنقوم بإدراج المستندات الجديدة فقط.
    5.  معالجة الأخطاء المحتملة أثناء الاتصال بـ MongoDB أو تحميل البيانات.
    6.  إغلاق الاتصال بـ MongoDB بعد الانتهاء.

## 4. الكود البرمجي الكامل

تم توفير الكود البرمجي الكامل في الملف `etl_project_3_intermediate_dynamic_web_mongodb.py`.

## 5. الشرح التفصيلي والكتابي للكود (Line-by-Line Breakdown)

سيتم شرح كل دالة وجزء رئيسي من الكود أدناه، مع التركيز على المفاهيم المطلوبة.

### دالة `setup_selenium_driver()`

```python
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# ... (باقي الاستيرادات)

def setup_selenium_driver():
    print("[Setup] Setting up Selenium WebDriver.")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run Chrome in headless mode (without GUI)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--incognito")
    try:
        driver = webdriver.Chrome(options=options)
        print("[Setup] WebDriver initialized successfully.")
        return driver
    except Exception as e:
        print(f"[Setup Error] Failed to initialize WebDriver: {e}")
        return None
```

*   **`from selenium import webdriver`**: استيراد وحدة WebDriver من Selenium.
*   **`options = webdriver.ChromeOptions()`**: إنشاء كائن `ChromeOptions` لتخصيص سلوك المتصفح.
*   **`options.add_argument("--headless")`**: تشغيل Chrome في وضع headless، مما يعني أنه سيعمل في الخلفية بدون فتح نافذة متصفح مرئية. هذا ضروري لبيئات الخادم أو الأتمتة.
*   **`options.add_argument("--no-sandbox")`, `--disable-dev-shm-usage`, `--disable-gpu`**: هذه الخيارات ضرورية لتشغيل Chrome بشكل مستقر في بيئات مثل Docker أو بيئات السحابة التي قد تفتقر إلى موارد رسومية أو بيئات sandbox معينة.
*   **`options.add_argument("--window-size=1920,1080")`**: تحديد حجم نافذة المتصفح، مما يساعد في ضمان عرض الصفحة بشكل صحيح.
*   **`options.add_argument("--incognito")`**: تشغيل المتصفح في وضع التصفح المتخفي.
*   **`try...except Exception as e`**: **معالجة الأخطاء (Exception Handling)**: يلتقط أي أخطاء قد تحدث أثناء تهيئة WebDriver (مثل عدم العثور على ChromeDriver) ويطبع رسالة خطأ.
*   **`driver = webdriver.Chrome(options=options)`**: إنشاء مثيل لمتصفح Chrome WebDriver مع الخيارات المحددة.

### دالة `extract_dynamic_data(driver, url, max_scrolls=3)`

```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
# ... (باقي الاستيرادات)

def extract_dynamic_data(driver, url, max_scrolls=3):
    print(f"[Extract] Navigating to: {url}")
    products_data = []
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".product-item"))
        )
        print("[Extract] Initial page loaded.")

        for i in range(max_scrolls):
            print(f"[Extract] Scrolling/Loading more (attempt {i+1}/{max_scrolls})...")
            try:
                load_more_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".load-more-button"))
                )
                load_more_button.click()
                time.sleep(2) # Wait for new content to load
            except:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2) # Wait for new content to load
                new_height = driver.execute_script("return document.body.scrollHeight")
                if i > 0 and new_height == driver.execute_script("return arguments[0]", driver.execute_script("return document.body.scrollHeight")):
                    print("[Extract] No new content loaded after scroll. Stopping.")
                    break

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
```

*   **`driver.get(url)`**: يوجه المتصفح إلى عنوان URL المحدد.
*   **`WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product-item")))`**: ينتظر حتى يظهر عنصر `product-item` على الصفحة، مما يضمن تحميل المحتوى الأولي قبل محاولة استخلاصه. هذا مهم للصفحات التي تعتمد على JavaScript.
*   **`for i in range(max_scrolls):`**: حلقة لمحاكاة التمرير أو النقر على زر "تحميل المزيد" لعدة مرات.
*   **`try...except` داخل الحلقة**: يحاول العثور على زر "تحميل المزيد" والنقر عليه. إذا لم يتم العثور على الزر، فإنه يحاول التمرير لأسفل الصفحة. هذا يجعل الكود مرناً للتعامل مع آليات التحميل الديناميكية المختلفة.
*   **`load_more_button.click()`**: ينقر على زر "تحميل المزيد" إذا وجد.
*   **`driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")`**: يقوم بتمرير الصفحة إلى الأسفل. `document.body.scrollHeight` يمثل الارتفاع الكلي للصفحة.
*   **`time.sleep(2)`**: انتظار لمدة ثانيتين للسماح للمحتوى الجديد بالتحميل بعد التمرير أو النقر.
*   **`soup = BeautifulSoup(driver.page_source, 'html.parser')`**: بعد تحميل كل المحتوى الديناميكي، يتم الحصول على مصدر HTML الكامل للصفحة باستخدام `driver.page_source`، ثم يتم تحليله بواسطة BeautifulSoup.
*   **`product_elements = soup.find_all(...)`**: نفس منطق الاستخلاص من المشروع الأول باستخدام BeautifulSoup.
*   **`try...except Exception as e`**: **معالجة الأخطاء (Exception Handling)**: يلتقط أي أخطاء قد تحدث أثناء التفاعل مع الصفحة أو تحليلها.
*   **`finally: if driver: driver.quit()`**: يضمن إغلاق WebDriver في جميع الأحوال، حتى لو حدث خطأ، لتحرير الموارد.

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
    df["description"] = df["description"].fillna("No description available")
    print("[Transform] Handled missing descriptions.")

    # 2. Clean and Convert Price:
    df["price"] = df["price"].astype(str).str.replace("[^\\d.]", "", regex=True)
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    print("[Transform] Cleaned and converted prices to numeric.")

    # 3. Deduplication: Remove duplicate products based on name and price
    initial_rows = len(df)
    df.drop_duplicates(subset=["name", "price"], inplace=True)
    if len(df) < initial_rows:
        print(f"[Transform] Removed {initial_rows - len(df)} duplicate rows.")
    else:
        print("[Transform] No duplicate rows found.")

    # Add extraction date
    df["extraction_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("[Transform] Added extraction date.")

    print("[Transform] Data transformation complete.")
    return df
```

*   هذه الدالة مطابقة تقريباً لدالة التحويل في المشروع الأول. تقوم بتحويل البيانات إلى DataFrame، ومعالجة القيم المفقودة في الوصف، وتنظيف وتحويل حقل السعر إلى رقم، وإزالة المنتجات المكررة بناءً على الاسم والسعر، وإضافة تاريخ الاستخلاص. المفاهيم هي نفسها: **معالجة القيم المفقودة (Missing Values)** و **إزالة التكرار (Deduplication)**.

### دالة `load_data_to_mongodb(df, db_name=\'product_db\', collection_name=\'products\')`

```python
from pymongo import MongoClient
# ... (باقي الاستيرادات)

def load_data_to_mongodb(df, db_name=\'product_db\', collection_name=\'products\'):
    if df.empty:
        print("[Load] No data to load.")
        return

    print(f"[Load] Connecting to MongoDB database: {db_name}, collection: {collection_name}")
    try:
        client = MongoClient(\'mongodb://localhost:27017/\')
        db = client[db_name]
        collection = db[collection_name]

        records = df.to_dict(orient=\'records\')

        insert_result = collection.insert_many(records)
        print(f"[Load] Successfully loaded {len(insert_result.inserted_ids)} documents into \'{collection_name}\'.")

    except Exception as e:
        print(f"[Load Error] An error occurred during MongoDB loading: {e}")
    finally:
        if \'client\' in locals() and client:
            client.close()
            print("[Load] MongoDB connection closed.")
```

*   **`from pymongo import MongoClient`**: استيراد عميل MongoDB لـ Python.
*   **`client = MongoClient(\'mongodb://localhost:27017/\')`**: ينشئ اتصالاً بخادم MongoDB. يفترض أن MongoDB يعمل على المنفذ الافتراضي 27017 على الجهاز المحلي.
*   **`db = client[db_name]`**: الوصول إلى قاعدة بيانات معينة (سيتم إنشاؤها إذا لم تكن موجودة).
*   **`collection = db[collection_name]`**: الوصول إلى مجموعة معينة داخل قاعدة البيانات (سيتم إنشاؤها إذا لم تكن موجودة).
*   **`records = df.to_dict(orient=\'records\')`**: يحول Pandas DataFrame إلى قائمة من القواميس، حيث يمثل كل قاموس مستنداً واحداً في MongoDB. `orient=\'records\'` هو التنسيق المثالي لهذا الغرض.
*   **`insert_result = collection.insert_many(records)`**: يقوم بإدراج جميع المستندات في المجموعة. هذه عملية تحميل بسيطة. في سيناريوهات أكثر تعقيداً، قد تحتاج إلى استخدام `update_one` أو `bulk_write` مع خيار `upsert=True` لتحديث المستندات الموجودة بدلاً من إدراجها فقط.
*   **`except Exception as e`**: **معالجة الأخطاء (Exception Handling)**: يلتقط أي أخطاء قد تحدث أثناء الاتصال بـ MongoDB أو الإدراج.
*   **`finally: if \'client\' in locals() and client: client.close()`**: يضمن إغلاق الاتصال بـ MongoDB في جميع الأحوال.

### الجزء الرئيسي (`if __name__ == "__main__":`)

```python
# --- Main ETL Process ---
if __name__ == "__main__":
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
                    document.querySelector(\".load-more-button\").style.display = \'none\';
                    return;
                }
                const productList = document.querySelector(\".product-list\");
                for (let i = 0; i < 2; i++) {
                    productCount++;
                    const newProduct = document.createElement(\'div\');
                    newProduct.className = \'product-item\';
                    newProduct.innerHTML = `
                        <h2 class=\"product-name\">Dynamic Product ${productCount}</h2>
                        <span class=\"product-price\">$${(100 + productCount * 10).toFixed(2)}</span>
                        <p class=\"product-description\">Description for dynamic product ${productCount}.</p>
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
        driver = setup_selenium_driver()
        if driver is None:
            print("[Main] Failed to setup WebDriver. Exiting.")
        else:
            raw_data = extract_dynamic_data(driver, source_url, max_scrolls=2)
            transformed_df = transform_data(raw_data)
            load_data_to_mongodb(transformed_df, db_name=\'dynamic_product_catalog\', collection_name=\'products\')

    except Exception as e:
        print(f"[Main Error] An error occurred in the main ETL process: {e}")
    finally:
        if driver:
            driver.quit()

    print("\n--- ETL Process Completed for Project 3 ---")

    # Optional: Verify data in MongoDB
    print("\n[Verification] Fetching data from MongoDB:")
    try:
        client = MongoClient(\'mongodb://localhost:27017/\')
        db = client[\'dynamic_product_catalog\']
        collection = db[\'products\']
        mongo_data = list(collection.find({}))
        for doc in mongo_data:
            doc[\'_id\'] = str(doc[\'_id\']) # Convert ObjectId to string for display
        verification_df = pd.DataFrame(mongo_data)
        print(verification_df)
    except Exception as e:
        print(f"[Verification Error] Could not read from MongoDB: {e}")
    finally:
        if \'client\' in locals() and client:
            client.close()
```

*   **`dummy_html_content`**: يتم إنشاء محتوى HTML وهمي يتضمن JavaScript لمحاكاة تحميل المنتجات ديناميكياً عند النقر على زر "Load More". هذا يسمح باختبار Selenium دون الحاجة إلى موقع ويب حقيقي.
*   **`dummy_html_path` و `source_url`**: يتم حفظ المحتوى الوهمي في ملف HTML محلي واستخدامه كعنوان URL للمتصفح.
*   **`driver = setup_selenium_driver()`**: تهيئة WebDriver.
*   **`raw_data = extract_dynamic_data(driver, source_url, max_scrolls=2)`**: استدعاء دالة الاستخلاص، مع تحديد عدد مرات النقر على زر "Load More" (مرتين في هذا المثال).
*   **`transformed_df = transform_data(raw_data)`**: استدعاء دالة التحويل.
*   **`load_data_to_mongodb(...)`**: استدعاء دالة التحميل.
*   **جزء التحقق الاختياري**: بعد اكتمال عملية ETL، يتم الاتصال بـ MongoDB وقراءة جميع المستندات من مجموعة `products` وعرضها باستخدام Pandas DataFrame للتحقق من أن البيانات تم تحميلها بشكل صحيح. يتم تحويل `_id` من `ObjectId` إلى `str` لسهولة العرض.

## 6. تطوير ذاتي للمشروع

لزيادة تعقيد المشروع وتعميق فهمك، يمكنك محاولة تطبيق المهام الإضافية التالية باستخدام الأدوات المتاحة لديك فقط:

1.  **تنفيذ Upsert في MongoDB:** بدلاً من مجرد إدراج المستندات الجديدة (`insert_many()`)، قم بتعديل دالة `load_data_to_mongodb` لتنفيذ عملية Upsert. هذا يعني أنه إذا كان المنتج موجوداً بالفعل في المجموعة (يمكن تحديده بواسطة `name` و `price` مثلاً)، فيجب تحديث معلوماته (مثل `description` أو `extraction_date`). وإذا لم يكن موجوداً، فيجب إدراجه كمستند جديد. يتطلب هذا استخدام `update_one` مع `upsert=True` أو `bulk_write`.
2.  **استخلاص سمات إضافية للمنتج:** قم بتعديل محتوى HTML الوهمي ليشمل سمات إضافية للمنتج (مثل `rating` أو `category` أو `availability`). ثم قم بتعديل دالة `extract_dynamic_data` لاستخلاص هذه السمات، ودالة `transform_data` لتنظيفها (معالجة القيم المفقودة، تحويل الأنواع)، وتأكد من أن نمط البيانات في MongoDB يمكنه استيعاب هذه الحقول الجديدة.
3.  **التعامل مع صفحات متعددة أو روابط تفصيلية:** بدلاً من مجرد التمرير أو النقر على "تحميل المزيد" في صفحة واحدة، قم بتعديل دالة `extract_dynamic_data` لتتبع الروابط إلى صفحات تفصيلية للمنتجات (مثلاً، النقر على كل منتج للانتقال إلى صفحته الخاصة واستخلاص المزيد من التفاصيل). هذا سيتطلب إدارة متصفح Selenium للتنقل بين الصفحات والعودة، مما يزيد من تعقيد عملية الاستخلاص بشكل كبير.
