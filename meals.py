from flask import Blueprint
from pymongo import MongoClient
from flask import request
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask_jwt_extended import (
    jwt_required, get_raw_jwt
)
import datetime

DATABASE = MongoClient('localhost', 27017)["go_meals"]
meals = DATABASE["meals"]
meals_api = Blueprint("meals_api", __name__)

#POST create a meals
@meals_api.route('/meals', methods=["POST"])
@jwt_required
def create_meal():
    jot = get_raw_jwt()
    identity = ObjectId(jot["identity"])
    errors = dict()
    meal_filter = {"user": identity}
    if len(request.form.get('mealname')) == 0:
        errors["mealname"] = "mealname is required"
    if len(errors) > 0:
        return dumps(errors)
    users_meals = meals.find(meal_filter)
    for meal in users_meals:
        if (meal["mealname"]).lower() == (request.form.get('mealname')).lower():
            return "this mealname already exists"
    else:
        new_meal = {
            "user": identity,
            "mealname": request.form.get('mealname'),
            "totalcalories": float(0),
            "ingredients": list(),
            "dateadded": datetime.datetime.now()
        }
        meal_id = meals.insert_one(new_meal).inserted_id
        return dumps(meals.find_one({"_id": meal_id})), 200


# GET all meals
@meals_api.route('/meals', methods=["GET"])
@jwt_required
def get_current_users_meals():
    jot = get_raw_jwt()
    identity = jot["identity"]
    meal_filter = {"user": ObjectId(identity)}
    all_meals = meals.find(meal_filter)
    if all_meals.count() > 0:
        return dumps(all_meals), 200
    else:
        return "Error: No meals found", 404

#GET a meal by its id
@meals_api.route('/meals/<meal_id>/', methods=["GET"])
@jwt_required
def get_meal_by_id(meal_id):
    jot = get_raw_jwt()
    identity = ObjectId(jot["identity"])
    meal = meals.find_one({"_id": ObjectId(meal_id)})
    if meal != None:
        if meal["user"] == identity:
            return dumps(meal), 200
        else:
            return "thats not your meal", 403
    else:
        return "Meal not found", 404

# PUT adds ingredient to meal by meal id
# finds meal by meal id. makes an ingredient and appends that to the meals ingredient list. then replaces the meal in the db with the updated meal.

@meals_api.route('/meals/<meal_id>/', methods=["PUT"])
@jwt_required
def add_ingredient_to_meal(meal_id):
    #validate ingredient inputs
    errors = dict()
    if len(request.form.get("ingredient")) == 0:
        errors["ingredient"] = "Ingredient field is required"
    if len(request.form.get('calories')) == 0:
        errors["calories"] = "Calories field is required"
    if len(request.form.get('measureunit')) == 0:
        errors["measureunit"] = "measureunit field is required"
    if len(request.form.get('measureunitquantity')) == 0:
            errors["measureunitquantity"] = "measureunitquantity field is required"
    if len(errors) > 0:
        return dumps(errors)
    else:
        jot = get_raw_jwt()
        identity = ObjectId(jot["identity"])
        meal_filter = {"_id": ObjectId(meal_id)}
        meal = meals.find_one(meal_filter)

        if meal["user"] == identity:
            ingredient = {
                "_id": ObjectId(),
                "ingredient": request.form.get("ingredient"),
                "calories": float(request.form.get("calories")),
                "measureunit": request.form.get("measureunit"),
                "measureunitquantity": float(request.form.get("measureunitquantity"))
            }
            meal["ingredients"].append(ingredient)
            meal["totalcalories"] += float(ingredient["calories"])

            result = meals.replace_one(meal_filter, meal)
            if result.matched_count == 0:
                return "no ingredients added", 404
            else:
                return dumps(meal), 200
        else:
            return "thats not your meal", 403

#PUT removes an ingredient from the meal
# finds the meal by its id, then it cycles through each ingredient in the meals ingredient list. if the ingredients id is the same as the id in the url, it removes the calories and removes the ingredient from the list. then it replaces the meal  in the db


@meals_api.route('/meals/<meal_id>/remove/<ing_id>', methods=["PUT"])
@jwt_required
def remove_ingredient_from_meal(meal_id, ing_id):
    meal_filter = {"_id": ObjectId(meal_id)}
    ing_filter = {"_id": ObjectId(ing_id)}
    meal = meals.find_one(meal_filter)
    jot = get_raw_jwt()
    identity = ObjectId(jot["identity"])
    if meal != None:
        if meal["user"] == identity:
            cals = 0
            inserted = False
            for i in meal["ingredients"]:
                if i["_id"] == ObjectId(ing_id):
                    cals = i["calories"]
                    meal["ingredients"].remove(i)
                    inserted = True
                    break
            if inserted == True:
                meal["totalcalories"] -= float(cals)
                result = meals.replace_one(meal_filter, meal)
                if result.matched_count == 0:
                    return "non ingredients deleted", 404
                else:
                    return dumps(meal), 200
            else:
                errors = dict()
                errors["ingredient"] = "this ingredient wasnt in the meal"
        else:
            return "thats not your meal", 403
    else:
        errors = dict()
        errors["meal"] = "No meal was found"
        return dumps(errors)

# DELETE s meal by its id
@meals_api.route('/meals/<meal_id>', methods=["DELETE"])
@jwt_required
def delete_meal_by_id(meal_id):
    meal_filter = {"_id": ObjectId(meal_id)}
    meal_to_delete = meals.find_one(meal_filter)
    if meal_to_delete["user"] == identity:
        delete_result = meals.delete_one(meal_filter)
        if delete_result.deleted_count == 0:
            return "deletion failed", 404
        else:
            return "deletion successful", 200
    else:
        return "this is not your meal to delete", 403
