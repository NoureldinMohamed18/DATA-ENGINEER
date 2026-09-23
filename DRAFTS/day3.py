"""VARIABLES"""  ##DONE
"""DATA STRUCTURE""" #LIST ,TUPLE,DICT,SET
"""STRING METHODS"""
text = " data ENGINEER  "
print(text.strip()) #REMOVES SPACES
print(text.lower())   
print(text.upper())
print(text.find("ENG"))
print(text.replace("data","BIG DATA"))
print("=="*50)
##list
data=[10,20,30,40,50]
data.append(5)
data.insert(0,15)
data.remove(10)
data.pop()
data.sort()
print(data)
print(len(data))
print("=="*50)
# ========== DICTIONARIES ==========
config = {
    "host": "localhost",
    "port": 5432,
    "database": "production_db"
}
# الوصول للبيانات
print(config["host"])       # "localhost"
print(config.get("user", "default"))  # "default" (لو المفتاح مش موجود)
# Iteration
for key, value in config.items():
    print(f"{key}: {value}")
print("=="*50)