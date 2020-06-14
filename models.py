from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string


db = SQLAlchemy()


class OrderedMeal(db.Model):
    __tablename__ = "ordered_meals"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"))
    meal_id = db.Column(db.Integer, db.ForeignKey("meals.id"))
    meal_amount = db.Column(db.Integer, nullable=False)

    order = db.relationship("Order", back_populates="meal")
    meal = db.relationship("Meal", back_populates="order")


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    column_exclude_list = ('password_hash')  # убрать из списка в admin

    order = db.relationship("Order", back_populates="customer")

    def password(self):
        # Запретим прямое обращение к паролю
        raise AttributeError("Вам не нужно знать пароль!")

    def generate_password(self):
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(20))
        return password

    def password(self, password):
        # Устанавливаем пароль через этот метод
        self.password_hash = generate_password_hash(password)

    def password_valid(self, password):
        # Проверяем пароль через этот метод
        # Функция check_password_hash превращает password в хеш и сравнивает с хранимым
        return check_password_hash(self.password_hash, password)


class Meal(db.Model):
    __tablename__ = "meals"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    picture = db.Column(db.String(100))
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    category = db.relationship("Category", back_populates="meal")
    order = db.relationship("OrderedMeal", back_populates="meal")


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    meal = db.relationship("Meal", back_populates="category")


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    total_payment = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"))
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(100), nullable=False)

    customer = db.relationship("Customer", back_populates="order")
    meal = db.relationship("OrderedMeal", back_populates="order")