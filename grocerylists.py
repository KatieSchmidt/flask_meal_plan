from pymongo import MongoClient
from flask import Flask
from flask import Blueprint
from flask import request
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask_jwt_extended import ( jwt_required, get_jwt_identity )

DATABASE = MongoClient('localhost', 27017)["go_meals"]

mealplans = DATABASE["grocerylists"]

grocerylists_api = Blueprint('grocerylists_api', __name__)

#POST Creates a grocery list from a mealplan using the mealplan id.

# it checks for a mealplan, if it exists, it makes an empty list. it looks through each meal in the mealplan. For each meal, it loops through the ingredients,  then checks if the list is empty, if its empty it creates an object with the grocery item info for the first ingredient. Otherwise, it loops through the ingredients in the grocerylist ands if the ingredient is already in there, if it is, it increments the quantity, otherwise it makes a new object and adds it to the list. after iterating through them all, it makes a dictionary. it checks to see if a grocery ilst exists for associated mealplan. if it does, it replces it, otherwise it creates a new list

@grocerylists_api.route('/grocerylists/<mealplan_id>', methods=["POST"])
@jwt_required
def create_grocery_list(mealplan_id):
    mealplan_filter = {"_id": ObjectId(mealplan_id)}
    grocerylist_filter = {"associatedmealplanid": ObjectId(mealplan_id)}

    previous_grocerylist = grocerylists.find_one(grocerylist_filter)
    mealplan = mealplans.find_one(mealplan_filter)

    if mealplan != None:
        grocerylist = list()
        for meal in mealplan["meals"]:
            for ingredient in meal["ingredients"]:
                inserted = False
                if len(grocerylist) > 0:
                    for item in grocerylist:
                        if item["ingredient"].lower() == ingredient["ingredient"].lower():
                            item["quantity"] += float(
                                ingredient["measureunitquantity"])
                            inserted = True
                            break
                    if inserted == False:
                        temp_item = {
                            "_id": ObjectId(),
                            "ingredient": ingredient["ingredient"],
                            "quantity": float(ingredient["measureunitquantity"]),
                            "measureunit": ingredient["measureunit"]
                        }
                        grocerylist.append(temp_item)


                else:
                    print("grocery list empty creating first item")
                    temp_item = {
                        "_id": ObjectId(),
                        "ingredient": ingredient["ingredient"],
                        "quantity": float(ingredient["measureunitquantity"]),
                        "measureunit": ingredient["measureunit"]
                    }
                    grocerylist.append(temp_item)

        grocerydict = dict()
        grocerydict["associatedmealplanid"] = ObjectId(mealplan_id)
        grocerydict["groceries"] = grocerylist

        if previous_grocerylist != None:
            result = grocerylists.replace_one(grocerylist_filter, grocerydict)
            if result.matched_count == 0:
                return "no grocerylist replaced", 404
            else:
                return dumps(grocerydict), 200
        else:
            grocery_id = grocerylists.insert_one(grocerydict).inserted_id
            return dumps(grocerylists.find_one({"_id": grocery_id})), 200
    else:
        return "Mealplan not found, cant make grocery list", 404



#gets all grocery lists
@grocerylists_api.route('/grocerylists', methods=["GET"])
@jwt_required
def get_grocerylists():
    grocerylist = grocerylists.find()
    if grocerylist != None:
        return dumps(grocerylist), 200
    else:
        return "Grocery list not found", 404

#GET s specific grocery list using the mealplan id
@grocerylists_api.route('/grocerylists/<mealplan_id>', methods=["GET"])
@jwt_required
def get_grocerylist_by_mealplan_id(mealplan_id):
    grocerylist = grocerylists.find_one({"associatedmealplanid": ObjectId(mealplan_id)})
    if grocerylist != None:
        return dumps(grocerylist), 200
    else:
        return "Grocery list not found", 404

#PUT s deletes an item from a grocery list
# it finds the grocery list with the mealplan id, then if the grocery list exists, it iterates over the groceries in the list. if the id matches the id in the url, it pops that item from the list and replaces the grocery list with the updated list, otherwise if none of the items in the list match the url id, it lets you know the item wasnt in the list. if the grocery list didnt exist to begin with, it lets you know the grocery list wasnt found.
@grocerylists_api.route('/grocerylists/<mealplan_id>/<grocery_id>', methods=["PUT"])
@jwt_required
def remove_grocery_item_from_list(mealplan_id, grocery_id):
    list_filter = {"associatedmealplanid": ObjectId(mealplan_id)}
    grocerylist = grocerylists.find_one(list_filter)

    if grocerylist != None:
        inserted = False
        index = 0
        for item in grocerylist["groceries"]:
            if item["_id"] == ObjectId(grocery_id):
                removed_value = grocerylist["groceries"].pop(index)
                if removed_value != None:
                    result = grocerylists.replace_one(list_filter, grocerylist)
                    if result.matched_count == 0:
                        return "no items deleted", 404
                    else:
                        return dumps(grocerylist), 200
            else:
                index += 1
        if inserted == False:
            return "That item was not in the grocerylist", 404
    else:
        return "Grocery list not found", 404

# DELETES a grocery list by its id
@grocerylists_api.route('/grocerylists/<grocerylist_id>', methods=["DELETE"])
@jwt_required
def delete_grocerylist_by_id(grocerylist_id):
    grocerylist_filter = {"_id": ObjectId(grocerylist_id)}

    delete_result = grocerylists.delete_one(grocerylist_filter)
    if delete_result.deleted_count == 0:
        return "deletion failed", 404
    else:
        return "deletion successful", 200
