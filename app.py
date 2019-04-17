from pymongo import MongoClient
from flask import request
from flask import Flask
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, get_raw_jwt
)
from flask_bcrypt import Bcrypt
import datetime
import pprint

DATABASE = MongoClient('localhost', 27017)["go_meals"]

meals = DATABASE.meals
mealplans = DATABASE.mealplans
grocerylists = DATABASE.grocerylists
users = DATABASE.users

# flask config
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['JWT_SECRET_KEY'] = 'This-secret-will-be-secret-later'
jwt = JWTManager(app)
# meal routes

#POST create a meals
@app.route('/meals', methods=["POST"])
@jwt_required
def create_meal():
    jot = get_raw_jwt()
    identity = jot["identity"]
    errors = dict()
    if len(request.form.get('mealname')) == 0:
        errors["mealname"] = "mealname is required"

    if len(errors) > 0:
        return dumps(errors)
    else:
        new_meal = {
            "user": ObjectId(identity),
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

#PUT removes an ingredient from the meal
# finds the meal by its id, then it cycles through each ingredient in the meals ingredient list. if the ingredients id is the same as the id in the url, it removes the calories and removes the ingredient from the list. then it replaces the meal  in the db

######## bug I updated the creation route so the models wont line up this needs to be fixed next

@app.route('/meals/<meal_id>/remove/<ing_id>', methods=["PUT"])
def remove_ingredient_from_meal(meal_id, ing_id):
    meal_filter = {"_id": ObjectId(meal_id)}
    ing_filter = {"_id": ObjectId(ing_id)}
    meal = meals.find_one(meal_filter)
    if meal != None:
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
@app.route('/mealplans', methods=["POST"])
def create_mealplan():
    errors = dict()
    if len(request.form.get("user")) < 24:
        errors["user"] = "User id must be 24 characters"
    if len(request.form.get("planname")) == 0:
        errors["planname"] = "planname field must be filled"
    if len(errors) > 0:
        return dumps(errors)
    else:
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
@app.route('/mealplans/<mealplan_id>', methods=["GET"])
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
    else:
        return "no mealplan found with that id", 404

#PUT removes a meal from mealplan from its mealplan_id
#checks to see if there is a mealplan by the ide in the url. if there is, it finds the meal. if the meal exists with the id, it removes the meal from the list of meals in the mealplan and removes the calories from the calories value.

@app.route('/mealplans/<mealplan_id>/remove/<meal_id>', methods=["PUT"])
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

# it checks for a mealplan, if it exists, it makes an empty list. it looks through each meal in the mealplan. For each meal, it loops through the ingredients,  then checks if the list is empty, if its empty it creates an object with the grocery item info for the first ingredient. Otherwise, it loops through the ingredients in the grocerylist ands if the ingredient is already in there, if it is, it increments the quantity, otherwise it makes a new object and adds it to the list. after iterating through them all, it makes a dictionary. it checks to see if a grocery ilst exists for associated mealplan. if it does, it replces it, otherwise it creates a new list

@app.route('/grocerylists/<mealplan_id>', methods=["POST"])
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
@app.route('/grocerylists', methods=["GET"])
def get_grocerylists():
    grocerylist = grocerylists.find()
    if grocerylist != None:
        return dumps(grocerylist), 200
    else:
        return "Grocery list not found", 404

#GET s specific grocery list using the mealplan id
@app.route('/grocerylists/<mealplan_id>', methods=["GET"])
def get_grocerylist_by_mealplan_id(mealplan_id):
    grocerylist = grocerylists.find_one({"associatedmealplanid": ObjectId(mealplan_id)})
    if grocerylist != None:
        return dumps(grocerylist), 200
    else:
        return "Grocery list not found", 404

#PUT s deletes an item from a grocery list
# it finds the grocery list with the mealplan id, then if the grocery list exists, it iterates over the groceries in the list. if the id matches the id in the url, it pops that item from the list and replaces the grocery list with the updated list, otherwise if none of the items in the list match the url id, it lets you know the item wasnt in the list. if the grocery list didnt exist to begin with, it lets you know the grocery list wasnt found.
@app.route('/grocerylists/<mealplan_id>/<grocery_id>', methods=["PUT"])
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
@app.route('/grocerylists/<grocerylist_id>', methods=["DELETE"])
def delete_grocerylist_by_id(grocerylist_id):
    grocerylist_filter = {"_id": ObjectId(grocerylist_id)}

    delete_result = grocerylists.delete_one(grocerylist_filter)
    if delete_result.deleted_count == 0:
        return "deletion failed", 404
    else:
        return "deletion successful", 200

#user routes

@app.route('/users/register', methods=["POST"])
def register():
    nonhashed_password = request.form.get('password')
    hashed = bcrypt.generate_password_hash(nonhashed_password)
    email = request.form.get('email')
    new_user = {
        "name": request.form.get("name"),
        "password": hashed,
        "email": email
    }
    returned_user = users.find_one({"email": email})
    if returned_user != None:
        return "email already in use", 500
    else:
        user_id = users.insert_one(new_user).inserted_id
        return dumps(users.find_one({"_id": user_id})), 200

@app.route('/users/login', methods=["POST"])
def login():
    user_email = request.form.get("email")
    user_password = request.form.get("password")
    db_user = users.find_one({"email": user_email})
    db_user_id = str(db_user["_id"])
    if db_user != None:
        if bcrypt.check_password_hash(db_user["password"], user_password) == True:
            jot = create_access_token(identity=db_user_id)
            response_item = {
            "success": True,
            "token": "Bearer " + jot
            }
            return dumps(response_item), 200
        else:
            return "invalid password email combination", 500
