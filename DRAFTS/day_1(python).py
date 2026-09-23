"""START AGAIN WITH BASICS AND FUNDAMENTALS ON PYTHON"""
##FIRST : VARIABLES , STRINGS , DATA STRUCTURE ,CONTROL FLOW 
name ="Noureldin"  #STRING
age=21  #INTEGAR 
salary=500.25 ##FLOAT
is_active=True ##BOOLEN
print(f"name : {name}, type : {type(name)}") 
print(f"name : {age}, type : {type(age)}")
age_str=str(age)
salary_int=int(salary)
print(f"age : {age_str}, type : {type(age_str)}")
print(f"salary : {salary_int}, type : {type(salary_int)}")
total = salary * 1.1
is_senior=age >30 and salary >6000
print("\n===============================\n")

"""Now string and string methods"""
raw_data=" noureldeenisco22@gamil.com"
cleaned=raw_data.strip().lower()
print(f"Before: '{raw_data}'")
print(f"After:  '{cleaned}'")

#split == parsing csv او بمعني اصح الفهم النحوي
email_parts=cleaned.split("@")
print(f"Username: {email_parts[0]}")
print(f"Domain: {email_parts[1]}")

##REPLACE FOR CLEANING 
phone="+20-106-260-8431"
clean_phone=phone.replace("-","").replace("+","")
print(f"Clean phone: {clean_phone}")

# f-strings - بناء queries
table = "users"
query = f"SELECT * FROM {table} WHERE active = True"
print(query)
print("\n===============================\n")

"""NOW DATA STRUCTURES"""
##LIST ,DICTONIRES
employees= ["Ahmed", "Sara", "Mohamed", "Ahmed"]
# Methods - اكتب كل واحدة وشوف النتيجة
employees.append("Laila")
employees.insert(1, "Omar")
print(f"After add: {employees}")

##remove duplicates
unique_employees=list(set(employees))
print(f"unique:{unique_employees}")

# List comprehension - أسرع وأنظف
names_upper = [name.upper() for name in employees]
print(names_upper)

# Filter
long_names = [name for name in employees if len(name) > 4]
print(long_names)
print("\n===============================\n")

##DICT
# Dict = JSON = API Response = اليومي في DE
user = {
    "id": 101,
    "name": "Ahmed",
    "email": "ahmed@test.com",
    "department": "Engineering",
    "salary": 5000,
    "skills": ["Python", "SQL", "Spark"]
}

# Access
print(user["name"])
print(user.get("phone", "Not found"))  # آمن

##add/update
user["level"]="senior"
user["salary"]+=1000

# Loop
for key, value in user.items():
    print(f"{key}: {value}")
    
# Nested dict - زي API response
api_response = {
    "status": "success",
    "data": {
        "users": [
            {"id": 1, "name": "A"},
            {"id": 2, "name": "B"}
        ]
    }
}

# Extract nested data
users = api_response["data"]["users"]
names = [u["name"] for u in users]
print(names)
print("\n===============================\n")

"""NOW CONTROOL FLOW AND LOOPS"""
##CONTROL FLOW
def validate_age(age):
    """Data Validation - اليومي في ETL"""
    if age < 0:
        return "invalid_negative"
    elif age > 120:
        return "invalid_too_old"
    elif age < 18:
        return "minor"
    else:
        return "valid"
  
# Test
print(validate_age(25))   
print(validate_age(-5))   
print(validate_age(150))  

##LOOPS For loop - Processing batches
data = [
    {"name": "A", "salary": 5000},
    {"name": "B", "salary": -100},  # invalid!
    {"name": "C", "salary": 7000},
]

valid_record=[]
for record in data :
    if record["salary"] > 0:
        valid_record.append(record)
    else :
        print(f"Invalid record: {record}")
print(f"Valid: {len(valid_record)}")   

# While loop - Retry logic (مهم جداً!)
import time
def fetch_data_with_retry(url,max_retries=3):
    attempt=0
    while attempt < max_retries:
        try:
            if attempt < 2 :
                raise ConnectionError("Network error")
            return {"data":"success"}
        except ConnectionError :
            attempt +=1
            wait_time=2** attempt
            print(f"Retry {attempt}, waiting {wait_time}s...")
            time.sleep(wait_time)
        return None
print("\n===============================\n")   

"""Now functions and error handling """
##MOST IMPORTANT
import logging
#setup logging no print
logging.basicConfig(
    level=logging.INFO,
    format ="%(asctime)s - %(levelname)s - %(message)s"
    )
def clean_email(email:str)->str:
    """
    Clean and validate email address.
    Args:
        email: Raw email string
    Returns:
        Cleaned email or None if invalid
    """
    if not email or not isinstance(email,str):
        logging.warning(f"Invalid email type: {type(email)}")
        return None
    cleaned=email.strip().lower()
    if "@" not in cleaned:
        logging.warning(f"Invalid email format: {email}")
        return None
    logging.info(f"Email cleaned: {email} -> {cleaned}")
    return cleaned
# Test
print(clean_email("  Ahmed@Email.COM  "))
print(clean_email("invalid"))
print(clean_email(None))
print("\n===============================\n")  
"""Now error handling"""
def read_csv_safe(filepath : str):
    """Read CSV with proper error handling"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.readlines()
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        return []
    except PermissionError:
        logging.error(f"Permission denied: {filepath}")
        return []
    except UnicodeDecodeError:
        logging.error(f"Encoding issue: {filepath}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise
print("\n===============================\n")  
"""NOW FILE HANDLING """
import csv
def process_large_csv(input_file,output_file):
    """
    Process large CSV without loading all in memory.
    Generator pattern - مهم جداً في DE!
    """
    with open(input_file, 'r', encoding='utf-8') as infile, \
        open(output_file, 'w', newline='', encoding='utf-8') as outfile:  
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ['is_valid']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        valid_count = 0
        invalid_count = 0
        for row in reader:
            # Validation logic
            is_valid = all([
                row.get('email'),
                row.get('salary'),
                float(row.get('salary', 0)) > 0
            ])
            
            row['is_valid'] = is_valid
            writer.writerow(row)
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
        
        print(f"Valid: {valid_count}, Invalid: {invalid_count}")
        
print("\n===============================\n")          
import json 
# Read JSON
with open('api_response.json', 'r') as f:
    data = json.load(f)
# Flatten nested JSON (مهم في ETL!)
def flatten_json(nested_json, prefix=''):
    """Flatten nested JSON to flat dict"""
    flat = {}
    for key, value in nested_json.items():
        new_key = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            flat.update(flatten_json(value, new_key))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    flat.update(flatten_json(item, f"{new_key}[{i}]"))
                else:
                    flat[f"{new_key}[{i}]"] = item
        else:
            flat[new_key] = value
    
    return flat
print("\n===============================\n")  
import csv
import json
import logging
from datetime import datetime
class DataPipeline:
    """Base ETL Pipeline"""
    def __init__(self, source: str, destination: str):
        self.source = source
        self.destination = destination
        self.log = []
        self.stats = {
            'processed': 0,
            'valid': 0,
            'invalid': 0,
            'errors': 0
        }
    
    def extract(self):
        """Override in subclass"""
        raise NotImplementedError
    
    def transform(self, data):
        """Default: clean and validate"""
        cleaned = []
        for record in data:
            self.stats['processed'] += 1
            try:
                clean_record = self._clean_record(record)
                if self._validate(clean_record):
                    cleaned.append(clean_record)
                    self.stats['valid'] += 1
                else:
                    self.stats['invalid'] += 1
            except Exception as e:
                self.stats['errors'] += 1
                logging.error(f"Error processing record: {e}")
        
        return cleaned
    
    def _clean_record(self, record):
        """Clean a single record"""
        return {
            k: v.strip().lower() if isinstance(v, str) else v
            for k, v in record.items()
        }
    
    def _validate(self, record):
        """Validate a single record"""
        return True
    
    def load(self, data):
        """Save to destination"""
        with open(self.destination, 'w') as f:
            json.dump(data, f, indent=2)
    
    def run(self):
        """Execute full pipeline"""
        start_time = datetime.now()
        logging.info(f"Pipeline started: {start_time}")
        
        raw_data = self.extract()
        clean_data = self.transform(raw_data)
        self.load(clean_data)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logging.info(f"Pipeline completed in {duration}s")
        logging.info(f"Stats: {self.stats}")
        
        return self.stats


class CSVPipeline(DataPipeline):
    """Pipeline for CSV files"""
    
    def extract(self):
        with open(self.source, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
