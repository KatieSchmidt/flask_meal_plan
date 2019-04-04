from pymongo import MongoClient
from flask import request
from flask import Flask
from bson.json_util import dumps
import datetime
import pprint

DATABASE = MongoClient('localhost', 27017)["meal_plan"]

meals = DATABASE.meals

# flask config
app = Flask(__name__)


@app.route('/meals', methods=["POST"])
def create_meal():
    new_meal = {
        "meal_name": request.form.get('meal_name'),
        "user": request.form.get("user")
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
