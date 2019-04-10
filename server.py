from pymongo import MongoClient
from flask import request
from flask import Flask
from bson.json_util import dumps
from bson.objectid import ObjectId
import datetime
import pprint

DATABASE = MongoClient('localhost', 27017)["go_meals"]

meals = DATABASE.meals
mealplans = DATABASE.mealplans

# flask config
app = Flask(__name__)


@app.route('/meals', methods=["POST"])
def create_meal():
    new_meal = {
        "ID": ObjectId(),
        "username": request.form.get("username"),
        "mealname": request.form.get('mealname'),
        "totalcalories": float(0),
        "ingredients": list(),
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


@app.route('/meals/<meal_id>/', methods=["POST"])
def add_ingredient_to_meal(meal_id):
    print(meal_id)
    filter = {"_id": ObjectId(meal_id)}
    meal = meals.find_one(filter)
    ingredient = {
        "id": ObjectId(),
        "ingredient": request.form.get("ingredient"),
        "totalcalories": request.form.get("calories"),
        "measureunit": request.form.get("measureunit"),
        "measureunitquantity": request.form.get("measureunitquantity")
    }
    print(meal["ingredients"])
    print(meal["totalcalories"])
    print(ingredient["totalcalories"])
    print(type(meal["ingredients"]))
    meal["ingredients"].append(ingredient)
    meal["totalcalories"] += float(ingredient["totalcalories"])

    meals.replace_one(filter, meal)
    return dumps(meal)
