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
grocerylists = DATABASE.grocerylists

# flask config
app = Flask(__name__)


# meal routes
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
    return dumps(meals.find_one({"_id": meal_id})), 200


@app.route('/meals', methods=["GET"])
def get_meals():
    all_meals = meals.find()
    if all_meals.count() > 0:
        return dumps(meals.find()), 200
    else:
        return "Error: No meals found", 404


@app.route('/meals/<meal_id>/', methods=["GET"])
def get_meal_by_id(meal_id):
    meal = meals.find_one({"_id": ObjectId(meal_id)})
    if meal != None:
        return dumps(meal), 200
    else:
        return "Meal not found", 404


@app.route('/meals/<meal_id>/', methods=["PUT"])
def add_ingredient_to_meal(meal_id):
    filter = {"_id": ObjectId(meal_id)}
    meal = meals.find_one(filter)
    ingredient = {
        "id": ObjectId(),
        "ingredient": request.form.get("ingredient"),
        "totalcalories": request.form.get("totalcalories"),
        "measureunit": request.form.get("measureunit"),
        "measureunitquantity": request.form.get("measureunitquantity")
    }
    meal["ingredients"].append(ingredient)
    meal["totalcalories"] += float(ingredient["totalcalories"])

    result = meals.replace_one(filter, meal)
    if result.matched_count == 0:
        return "no ingredients deleted", 404
    else:
        return dumps(meal), 200


@app.route('/meals/<meal_id>/remove/<ing_id>', methods=["PUT"])
def remove_ingredient_from_meal(meal_id, ing_id):
    meal_filter = {"_id": ObjectId(meal_id)}
    ing_filter = {"id": ObjectId(ing_id)}
    meal = meals.find_one(meal_filter)

    cals = 0
    for i in meal["ingredients"]:
        if i["id"] == ObjectId(ing_id):
            cals = i["totalcalories"]
            meal["ingredients"].remove(i)
            break
    meal["totalcalories"] -= float(cals)

    result = meals.replace_one(meal_filter, meal)
    if result.matched_count == 0:
        return "non ingredients deleted", 404
    else:
        return dumps(meal), 200


@app.route('/meals/<meal_id>', methods=["DELETE"])
def delete_meal_by_id(meal_id):
    meal_filter = {"_id": ObjectId(meal_id)}

    delete_result = meals.delete_one(meal_filter)
    if delete_result.deleted_count == 0:
        return "deletion failed", 404
    else:
        return "deletion successful", 200

# meaplan routes


@app.route('/mealplans', methods=["POST"])
def create_mealplan():
    new_mealplan = {
        "userid": ObjectId(request.form.get("userid")),
        "planname": request.form.get('planname'),
        "totalcalories": float(0),
        "meals": list(),
        "dateadded": datetime.datetime.now()
    }
    mealplan_id = mealplans.insert_one(new_mealplan).inserted_id
    return dumps(mealplans.find_one({"_id": mealplan_id})), 200


@app.route('/mealplans', methods=["GET"])
def get_mealplans():
    all_mealplans = mealplans.find()
    if all_mealplans.count() > 0:
        return dumps(mealplans.find()), 200
    else:
        return "Error: No mealplans found", 404


@app.route('/mealplans/<mealplan_id>/', methods=["GET"])
def get_mealplan_by_id(mealplan_id):
    mealplan = mealplans.find_one({"_id": ObjectId(mealplan_id)})
    if mealplan != None:
        return dumps(mealplan), 200
    else:
        return "Mealplan not found", 404


@app.route('/mealplans/<mealplan_id>/<meal_id>', methods=["PUT"])
def add_meal_to_mealplan(mealplan_id, meal_id):
    mealplan_filter = {"_id": ObjectId(mealplan_id)}
    meal_filter = {"_id": ObjectId(meal_id)}
    mealplan = mealplans.find_one(mealplan_filter)
    if mealplan != None:
        meal = meals.find_one(meal_filter)
        if meal != None:
            mealplan["meals"].append(meal)
            mealplan["totalcalories"] += float(meal["totalcalories"])

            result = mealplans.replace_one(mealplan_filter, mealplan)
            if result.matched_count == 0:
                return "no meal added", 404
            else:
                return dumps(mealplan), 200


@app.route('/mealplans/<mealplan_id>/remove/<meal_id>', methods=["PUT"])
def remove_meal_from_mealplan(mealplan_id, meal_id):
    mealplan_filter = {"_id": ObjectId(mealplan_id)}
    meal_filter = {"_id": ObjectId(meal_id)}

    mealplan = mealplans.find_one(mealplan_filter)
    if mealplan != None:
        meal = meals.find_one(meal_filter)
        if meal != None:
            mealplan["totalcalories"] -= float(meal["totalcalories"])
            mealplan["meals"].remove(meal)
        else:
            return "couldnt find meal to delete", 404
    else:
        return "couldnt find mealplan in database", 404

    result = mealplans.replace_one(mealplan_filter, mealplan)
    if result.matched_count == 0:
        return "no meals deleted", 404
    else:
        return dumps(mealplan), 200


@app.route('/mealplans/<mealplan_id>', methods=["DELETE"])
def delete_mealplan_by_id(mealplan_id):
    mealplan_filter = {"_id": ObjectId(mealplan_id)}

    delete_result = mealplans.delete_one(mealplan_filter)
    if delete_result.deleted_count == 0:
        return "deletion failed", 404
    else:
        return "deletion successful", 200

# grocery list routes
@app.route('/grocerylist/<mealplan_id>', methods=["GET"])
def create_grocery_list(mealplan_id):
    mealplan_filter = {"_id": ObjectId(mealplan_id)}
    mealplan = mealplans.find_one(mealplan_filter)
    if mealplan != None:
        grocerylist = list()
        for meal in mealplan["meals"]:
            for ingredient in meal["ingredients"]:
                inserted = False
                if len(grocerylist) > 0:
                    for item in grocerylist:
                        if item["ingredient"].lower() == ingredient["ingredient"].lower():
                            item["measureunitquantity"] += float(
                                ingredient["measureunitquantity"])
                            inserted = True
                            break
                    if inserted == False:
                        temp_item = {
                            "ingredient": ingredient["ingredient"],
                            "measureunitquantity": float(ingredient["measureunitquantity"])
                        }
                        grocerylist.append(temp_item)
                else:
                    print("grocery list empty creating first item")
                    temp_item = {
                        "ingredient": ingredient["ingredient"],
                        "measureunitquantity": float(ingredient["measureunitquantity"])
                    }
                    grocerylist.append(temp_item)

        index = 0
        grocerydict = dict()
        for item in grocerylist:
            grocerydict[str(index)] = item
            index += 1

        grocery_id = grocerylists.insert_one(grocerydict).inserted_id
        return dumps(grocerylists.find_one({"_id": grocery_id})), 200
    else:
        return "Mealplan not found, cant make grocery list", 404
