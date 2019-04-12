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

#POST create a meals
@app.route('/meals', methods=["POST"])
def create_meal():
    errors = dict()
    if len(request.form.get("user")) < 24:
        errors["user"] = "user id is required to be 24 characters"
    if len(request.form.get('mealname')) == 0:
        errors["mealname"] = "mealname is required"

    if len(errors) > 0:
        return dumps(errors)
    else:
        new_meal = {
            "user": ObjectId(request.form.get("user")),
            "mealname": request.form.get('mealname'),
            "totalcalories": float(0),
            "ingredients": list(),
            "dateadded": datetime.datetime.now()
        }
        meal_id = meals.insert_one(new_meal).inserted_id
        return dumps(meals.find_one({"_id": meal_id})), 200


# GET all meals
@app.route('/meals', methods=["GET"])
def get_meals():
    all_meals = meals.find()
    if all_meals.count() > 0:
        return dumps(meals.find()), 200
    else:
        return "Error: No meals found", 404

#GET a meal by its id
@app.route('/meals/<meal_id>/', methods=["GET"])
def get_meal_by_id(meal_id):
    meal = meals.find_one({"_id": ObjectId(meal_id)})
    if meal != None:
        return dumps(meal), 200
    else:
        return "Meal not found", 404

# PUT adds ingredient to meal by meal id
# finds meal by meal id. makes an ingredient and appends that to the meals ingredient list. then replaces the meal in the db with the updated meal.

@app.route('/meals/<meal_id>/', methods=["PUT"])
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
        meal_filter = {"_id": ObjectId(meal_id)}
        meal = meals.find_one(meal_filter)
        ingredient = {
            "id": ObjectId(),
            "ingredient": request.form.get("ingredient"),
            "calories": request.form.get("calories"),
            "measureunit": request.form.get("measureunit"),
            "measureunitquantity": request.form.get("measureunitquantity")
        }
        meal["ingredients"].append(ingredient)
        meal["totalcalories"] += float(ingredient["calories"])

        result = meals.replace_one(meal_filter, meal)
        if result.matched_count == 0:
            return "no ingredients added", 404
        else:
            return dumps(meal), 200

#PUT removes an ingredient from the meal
# finds the meal by its id, then it cycles through each ingredient in the meals ingredient list. if the ingredients id is the same as the id in the url, it removes the calories and removes the ingredient from the list. then it replaces the meal  in the db

@app.route('/meals/<meal_id>/remove/<ing_id>', methods=["PUT"])
def remove_ingredient_from_meal(meal_id, ing_id):
    meal_filter = {"_id": ObjectId(meal_id)}
    ing_filter = {"id": ObjectId(ing_id)}
    meal = meals.find_one(meal_filter)
    if meal != None:
        cals = 0
        inserted = False
        for i in meal["ingredients"]:
            if i["id"] == ObjectId(ing_id):
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
        errors = dict()
        errors["meal"] = "No meal was found"
        return dumps(errors)

# DELETE s meal by its id
@app.route('/meals/<meal_id>', methods=["DELETE"])
def delete_meal_by_id(meal_id):
    meal_filter = {"_id": ObjectId(meal_id)}

    delete_result = meals.delete_one(meal_filter)
    if delete_result.deleted_count == 0:
        return "deletion failed", 404
    else:
        return "deletion successful", 200

# meaplan routes

#POST creates a mealplan
####### bug needs to check and make sure the user id and the planname arent empty
@app.route('/mealplans', methods=["POST"])
def create_mealplan():
    new_mealplan = {
        "user": ObjectId(request.form.get("user")),
        "planname": request.form.get('planname'),
        "totalcalories": float(0),
        "meals": list(),
        "dateadded": datetime.datetime.now()
    }
    mealplan_id = mealplans.insert_one(new_mealplan).inserted_id
    return dumps(mealplans.find_one({"_id": mealplan_id})), 200

#GET s all mealplans
@app.route('/mealplans', methods=["GET"])
def get_mealplans():
    all_mealplans = mealplans.find()
    if all_mealplans.count() > 0:
        return dumps(mealplans.find()), 200
    else:
        return "Error: No mealplans found", 404

#GET s a mealplan by its id
@app.route('/mealplans/<mealplan_id>/', methods=["GET"])
def get_mealplan_by_id(mealplan_id):
    mealplan = mealplans.find_one({"_id": ObjectId(mealplan_id)})
    if mealplan != None:
        return dumps(mealplan), 200
    else:
        return "Mealplan not found", 404

#PUT adds a meal to the mealplan
# finds mealplan by id, if it exists, check to see if meal exists, if it does, add it to the mealplans list of meals and add the meals calories to the total calories
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

#PUT removes a meal from its mealplan_id
#checks to see if there is a mealplan by the ide in the url. if there is, it finds the meal. if the meal exists with the id, it removes the meal from the list of meals in the mealplan and removes the calories from the calories value.

####### bug need to check to make sure the meal is actually in the mealplan before trying to remove the calories and the meal
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

#DELETE s a mealplan by its id
@app.route('/mealplans/<mealplan_id>', methods=["DELETE"])
def delete_mealplan_by_id(mealplan_id):
    mealplan_filter = {"_id": ObjectId(mealplan_id)}

    delete_result = mealplans.delete_one(mealplan_filter)
    if delete_result.deleted_count == 0:
        return "deletion failed", 404
    else:
        return "deletion successful", 200

# grocery list routes

#POST Creates a grocery list from a mealplan using the mealplan id.

# it checks for a mealplan, if it exists, it makes an empty list. it looks through each meal in the mealplan. For each meal, it loops through the ingredients,  then checks if the list is empty, if its empty it creates an object with the grocery item info for the first ingredient. Otherwise, it loops through the ingredients in the grocerylist ands if the ingredient is already in there, if it is, it increments the quantity, otherwise it makes a new object and adds it to the list. after iterating through them all, it makes a dictionary and uses that to insert it into the db. then it returns the new grocery list.
@app.route('/grocerylists/<mealplan_id>', methods=["POST"])
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

        grocerydict = dict()
        for item in grocerylist:
            grocerydict[item["ingredient"]] = item["measureunitquantity"]

        grocery_id = grocerylists.insert_one(grocerydict).inserted_id
        return dumps(grocerylists.find_one({"_id": grocery_id})), 200
    else:
        return "Mealplan not found, cant make grocery list", 404



#gets all grocery lists
@app.route('/grocerylists', methods=["GET"])
def get_grocerylists():
    grocerylist = grocerylists.find()
    if grocerylist != None:
        return dumps(grocerylist), 200
    else:
        return "Grocery list not found", 404

#GET s specific grocery list using the grocery list id
@app.route('/grocerylists/<grocerylist_id>', methods=["GET"])
def get_grocerylist_by_id(grocerylist_id):
    grocerylist = grocerylists.find_one({"_id": ObjectId(grocerylist_id)})
    if grocerylist != None:
        return dumps(grocerylist), 200
    else:
        return "Grocery list not found", 404

#PUT s deletes an item from a grocery list
# it finds the grocery list with the id, then if the grocery list exists, it pops the item from the grocerylist. then it uses replace_one to replace the grocery list in the db. returns the new grocery list.
@app.route('/grocerylists/<grocerylist_id>/<itemname>', methods=["PUT"])
def remove_grocery_item_from_list(grocerylist_id, itemname):
    list_filter = {"_id": ObjectId(grocerylist_id)}
    grocerylist = grocerylists.find_one(list_filter)
    if grocerylist != None:
        removed_value = grocerylist.pop(itemname, None)
        result = grocerylists.replace_one(list_filter, grocerylist)
        if result.matched_count == 0:
            return "no items deleted", 404
        else:
            return dumps(grocerylist), 200
    else:
        return "Grocery list not found", 404

# DELETES a grocery list by its id
@app.route('/grocerylists/<grocerylist_id>', methods=["DELETE"])
def delete_grocerylist_by_id(grocerylist_id):
    grocerylist_filter = {"_id": ObjectId(grocerylist_id)}

    delete_result = grocerylists.delete_one(grocerylist_filter)
    if delete_result.deleted_count == 0:
        return "deletion failed", 404
    else:
        return "deletion successful", 200
