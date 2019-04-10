from pymongo import MongoClient
from flask import request
from flask import Flask
from bson.json_util import dumps
import bson
import datetime
import pprint

DATABASE = MongoClient('localhost', 27017)["meal_plan"]

meals = DATABASE.meals

# flask config
app = Flask(__name__)


@app.route('/meals', methods=["POST"])
def create_meal():
    new_meal = {
        "ID": bson.objectid.ObjectId(),
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
    errors = {}
    all_meals = meals.find()
    if all_meals.count() > 0:
        return dumps(meals.find())
    else:
        return "Error: No meals found", 404
