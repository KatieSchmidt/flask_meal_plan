from pymongo import MongoClient
from flask import request, jsonify
from flask import Flask
from bson.json_util import dumps
from bson.objectid import ObjectId
import datetime
import pprint

DATABASE = MongoClient('localhost', 27017)["go_meals"]

meals = DATABASE.meals

# flask config
app = Flask(__name__)


@app.route('/meals', methods=["POST"])
def create_meal():
    new_meal = {
        "ID": ObjectId(),
        "username": request.form.get("username"),
        "mealname": request.form.get('mealname'),
        "totalcalories": 0,
        "ingredients": [],
        "dateadded": datetime.datetime.now()
    }
    meal_id = meals.insert_one(new_meal).inserted_id
    return dumps(meals.find_one({"_id": meal_id}))


@app.route('/meals', methods=["GET"])
def get_meals():
    all_meals = meals.find()
    if all_meals.count() > 0:
        return dumps(meals.find())
    else:
        return "Error: No meals found", 404


@app.route('/meals/<meal_id>/', methods=["GET"])
def get_meal_by_id(meal_id):
    print(meal_id)
    meal = meals.find_one({"_id": ObjectId(meal_id)})
    return dumps(meal)
