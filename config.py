import os

class Config:
    SECRET_KEY = "best_of_the_best_food"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
