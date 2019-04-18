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
mealplans = DATABASE["mealplans"]
meals = DATABASE["meals"]
mealplans_api = Blueprint("mealplans_api", __name__)

#POST creates a mealplan
@mealplans_api.route('/mealplans', methods=["POST"])
@jwt_required
def create_mealplan():
    jot = get_raw_jwt()
    identity = ObjectId(jot["identity"])
    mealplan_filter = {"user": identity}
    errors = dict()
    if len(request.form.get("planname")) == 0:
        errors["planname"] = "planname field must be filled"

    users_mealplans = mealplans.find(mealplan_filter)
    for mealplan in users_mealplans:
        if mealplan["planname"].lower() == request.form.get('planname').lower():
            errors["planname"] = "this planname already exists"
    if len(errors) > 0:
        return dumps(errors)

    else:
        new_mealplan = {
            "user": identity,
            "planname": request.form.get('planname'),
            "totalcalories": float(0),
            "meals": list(),
            "dateadded": datetime.datetime.now()
        }
        mealplan_id = mealplans.insert_one(new_mealplan).inserted_id
        return dumps(mealplans.find_one({"_id": mealplan_id})), 200

#GET s all mealplans
@mealplans_api.route('/mealplans', methods=["GET"])
@jwt_required
def get_current_users_mealplans():
    jot = get_raw_jwt()
    identity = ObjectId(jot["identity"])
    mealplan_filter = {"user": identity}
    all_mealplans = mealplans.find(mealplan_filter)
    if all_mealplans.count() > 0:
        return dumps(all_mealplans), 200
    else:
        return "Error: No mealplans found", 404

#GET s a mealplan by its id
@mealplans_api.route('/mealplans/<mealplan_id>', methods=["GET"])
@jwt_required
def get_mealplan_by_id(mealplan_id):
    jot = get_raw_jwt()
    identity = ObjectId(jot["identity"])
    mealplan = mealplans.find_one({"_id": ObjectId(mealplan_id)})
    if mealplan != None:
        if mealplan["user"] == identity:
            return dumps(mealplan), 200
        else:
            return "thats not your mealplan!", 403
    else:
        return "Mealplan not found", 404

#PUT adds a meal to the mealplan
# finds mealplan by id, if it exists, check to see if meal exists, if it does, add it to the mealplans list of meals and add the meals calories to the total calories
@mealplans_api.route('/mealplans/<mealplan_id>/<meal_id>', methods=["PUT"])
@jwt_required
def add_meal_to_mealplan(mealplan_id, meal_id):
    jot = get_raw_jwt()
    identity = ObjectId(jot["identity"])
    mealplan_filter = {"_id": ObjectId(mealplan_id)}
    meal_filter = {"_id": ObjectId(meal_id)}
    mealplan = mealplans.find_one(mealplan_filter)
    if mealplan != None:
        meal = meals.find_one(meal_filter)
        if meal != None:
            if meal["user"] == identity and mealplan["user"] == identity:
                mealplan["meals"].append(meal)
                mealplan["totalcalories"] += float(meal["totalcalories"])

                result = mealplans.replace_one(mealplan_filter, mealplan)
                if result.matched_count == 0:
                    return "no meal added", 404
                else:
                    return dumps(mealplan), 200
            else:
                return "You dont have access to a meal or a mealplan"
        else:
            return "meal doesnt exist", 404
    else:
        return "no mealplan found with that id", 404

#PUT removes a meal from mealplan from its mealplan_id
#checks to see if there is a mealplan by the ide in the url. if there is, it finds the meal. if the meal exists with the id, it removes the meal from the list of meals in the mealplan and removes the calories from the calories value.

@mealplans_api.route('/mealplans/<mealplan_id>/remove/<meal_id>', methods=["PUT"])
@jwt_required
def remove_meal_from_mealplan(mealplan_id, meal_id):
    mealplan_filter = {"_id": ObjectId(mealplan_id)}
    meal_filter = {"_id": ObjectId(meal_id)}

    mealplan = mealplans.find_one(mealplan_filter)
    if mealplan != None:
        meal = meals.find_one(meal_filter)
        if meal != None:
            if meal in mealplan["meals"]:
                mealplan["totalcalories"] -= float(meal["totalcalories"])
                mealplan["meals"].remove(meal)
            else:
                return "that meal wasnt in the mealplan", 404
        else:
            return "couldnt find meal to delete", 404
    else:
        return "couldnt find mealplan in database", 404

    result = mealplans.replace_one(mealplan_filter, mealplan)
    if result.matched_count == 0:
        return "no meals deleted", 404
    else:
        return dumps(mealplan), 200

#DELETE s a mealplan by its id
@mealplans_api.route('/mealplans/<mealplan_id>', methods=["DELETE"])
@jwt_required
def delete_mealplan_by_id(mealplan_id):
    mealplan_filter = {"_id": ObjectId(mealplan_id)}

    delete_result = mealplans.delete_one(mealplan_filter)
    if delete_result.deleted_count == 0:
        return "deletion failed", 404
    else:
        return "deletion successful", 200
