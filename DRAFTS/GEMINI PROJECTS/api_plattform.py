from flask import Flask,request,jsonify
from pymongo import MongoClient , ASCENDING , DESCENDING
import datetime
app=Flask(__name__)
client=MongoClient("mongodb://localhost:27017/")
db=client["MRAKET_ANALYTICES.db"]
employees_col = db["employees"]
employees_col.create_index([("department", ASCENDING), ("salary", DESCENDING)])

@app.route("/api/emplyees",methods=["GET"])
def get_employees():
    dept = request.args.get("department")
    min_sal = request.args.get("min_salary", type=float)
    query = {}
    if dept: query["department"] = dept
    if min_sal is not None: query["salary"] = {"$gte": min_sal}
    results = list(employees_col.find(query, {"_id": 0}))
    return jsonify({"count": len(results), "data": results}), 200

@app.route("/api/employees", methods=["POST"])
def add_employee():
    data = request.json
    doc = {
    "name": data["name"],
    "department": data["department"],
        "salary": float(data["salary"]),
    "skills": list(data.get("skills", [])),"created_at": datetime.datetime.utcnow().isoformat()
}
    res = employees_col.insert_one(doc)
    return jsonify({"message": "Created", "id": str(res.inserted_id)}), 201
 
@app.route("/api/employees/<string:name>", methods=["PATCH"])
def update_employee(name):
    patch = request.json
    ops = {}
    if "salary" in patch: ops.setdefault("$set", {})["salary"] = float(patch["salary"])
    if "add_skill" in patch: ops.setdefault("$push", {})["skills"] = patch["add_skill"]
    if "increment_salary" in patch: ops.setdefault("$inc", {})["salary"] 
    float(patch["increment_salary"])
    res = employees_col.update_one({"name": name}, ops)
    if res.matched_count == 0: return jsonify({"error": "Not found"}), 404
    return jsonify({"message": "Updated successfully"}), 200


@app.route("/api/employees/<string:name>", methods=["DELETE"])
def delete_employee(name):
    res = employees_col.delete_one({"name": name})
    if res.deleted_count == 0: return jsonify({"error": "Not found"}), 404
    return jsonify({"message": "Deleted successfully"}), 200


@app.route("/api/analytics/department-summary", methods=["GET"])
def department_summary():
    pipeline = [
    {"$match": {"salary": {"$exists": True, "$gt": 0}}},
    {"$group": {
    "_id": "$department",
    "employee_count": {"$sum": 1},
    "avg_salary": {"$avg": "$salary"},
    "min_salary": {"$min": "$salary"},
    "max_salary": {"$max": "$salary"}
    }},
    {"$project": {
    "department": "$_id", "_id": 0, "employee_count": 1,
    "avg_salary": {"$round": ["$avg_salary", 2]},
    "min_salary": 1, "max_salary": 1
    }},
    {"$sort": {"avg_salary": -1}}]
    return jsonify({"analytics": list(employees_col.aggregate(pipeline))}), 200
if __name__ == "__main__":
    app.run(debug=True, port=5000)   