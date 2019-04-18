from pymongo import MongoClient
from flask import Flask
from flask_jwt_extended import (
    JWTManager
)
from flask_bcrypt import Bcrypt
from meals import meals_api
from mealplans import mealplans_api
from grocerylists import grocerylists_api
from users import users_api

# flask config
app = Flask(__name__)
flask_bcrypt = Bcrypt(app)
app.config['JWT_SECRET_KEY'] = 'This-secret-will-be-secret-later'
jwt = JWTManager(app)

#routes blueprints
app.register_blueprint(meals_api)
app.register_blueprint(mealplans_api)
app.register_blueprint(grocerylists_api)
app.register_blueprint(users_api)
