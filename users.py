from pymongo import MongoClient
from flask import Flask
from flask import Blueprint
from flask import request
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask_jwt_extended import create_access_token
from flask_bcrypt import generate_password_hash, check_password_hash


DATABASE = MongoClient('localhost', 27017)["go_meals"]

users = DATABASE["users"]
users_api = Blueprint('users_api', __name__)


# from flask_bcrypt import Bcrypt
#user routes

@users_api.route('/users/register', methods=["POST"])
def register():
    nonhashed_password = request.form.get('password')
    hashed = generate_password_hash(request.form.get('password')).decode("utf-8")
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

@users_api.route('/users/login', methods=["POST"])
def login():
    user_email = request.form.get("email")
    user_password = request.form.get("password")
    db_user = users.find_one({"email": user_email})
    if db_user != None:
        db_user_id = str(db_user["_id"])
        if check_password_hash(db_user["password"], user_password) == True:
            jot = create_access_token(identity=db_user_id)
            response_item = {
            "success": True,
            "token": "Bearer " + jot
            }
            return dumps(response_item), 200
    else:
        return "invalid password email combination", 400
