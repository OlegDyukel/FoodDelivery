from flask import Flask, render_template, request, session, redirect, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import os

from config import Config
from models import db, Customer, Order, Meal, Category, ordered_meals
from forms import ClientContact, ClientAuth


def group_by_list(lst):
    d = {}
    for element in lst:
        if element in d.keys():
            d[element] += 1
        else:
            d[element] = 1
    return d


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)


@app.route("/")
def index():
    session["total_cheque"] = session.get("total_cheque", 0)
    session["n_meals"] = session.get("n_meals", 0)
    session["meals"] = session.get("meals", {})
    categories = db.session.query(Category).all()
    meals = db.session.query(Meal).all()
    return render_template("main.html", categories=categories, meals=meals,
                           total_cheque=session["total_cheque"], n_meals=session["n_meals"])


@app.route("/updatecart/<action>/<int:meal_id>/")
def updatecart(action, meal_id):
    # Получаем либо значение из сессии, либо пустой список
    cart = session.get("cart", [])
    if action == "add":
        # Добавлям элемент в список
        cart.append(meal_id)
    elif action == "remove":
        # удаляем элемент из списка
        cart = [element for element in cart if element != meal_id]
    # Записываем измененный список обратно в сессию
    session["cart"] = cart

    cart_meals = db.session.query(Meal).filter(Meal.id.in_(session["cart"])).all()

    dict_meal_amount = group_by_list(session["cart"])

    session["total_cheque"] = 0
    session["n_meals"] = 0
    session["meals"] = {}
    for meal in cart_meals:
        session["meals"][meal.id] = {"title": meal.title, "price": meal.price,
                                     "amount": dict_meal_amount[meal.id]}
        session["total_cheque"] += meal.price*dict_meal_amount[meal.id]
        session["n_meals"] += dict_meal_amount[meal.id]

    if action == "add":
        return redirect(url_for("index"))
    elif action == "remove":
        return redirect(url_for("cart", action="deleted"))


@app.route("/cart/")
@app.route("/cart/<action>/")
def cart(action=""):

    form = ClientContact()
    return render_template("cart.html", form=form, action=action, cart_meals=session["meals"],
                           total_cheque=session["total_cheque"], n_meals=session["n_meals"],
                           customer=session.get("customer", False))


@app.route("/account/")
def account():

    return render_template("account.html")


@app.route("/login/", methods=["GET", "POST"])
def login():
    form = ClientAuth()
    error_msg = ""

    if request.method == 'POST':
        email_input = form.client_email.data
        password_input = form.client_password.data

        customer = db.session.query(Customer).filter(Customer.email == email_input).first()

        if customer and customer.password_valid(password_input):
            session["customer"] = {"id": customer.id, "email": customer.email, "is_auth": True}
            return redirect(url_for("account"))
        else:
            error_msg = "Не удаётся войти. Пожалуйста, проверьте правильность написания логина и пароля."
            return render_template("login.html", form=form, error_msg=error_msg)

    return render_template("login.html", form=form, error_msg=error_msg)


@app.route("/register/", methods=["GET", "POST"])
def register():
    form = ClientAuth()
    error_msg = ""

    if request.method == "POST":
        email_input = form.client_email.data
        password_input = form.client_password.data

        customer = db.session.query(Customer).filter(Customer.email == email_input).first()

        if "@" not in email_input:
            error_msg = "Некорректная почта"
            return render_template("register.html", error_msg=error_msg, form=form)
        elif customer:
            error_msg = "Такой пользователь уже существует"
            return render_template("register.html", error_msg=error_msg, form=form)
        elif len(password_input) < 8:
            error_msg = "Пароль слишком простой"
            return render_template("register.html", error_msg=error_msg, form=form)
        else:
            customer = Customer()
            customer.email = email_input
            customer.password(password_input)
            db.session.add(customer)
            db.session.commit()

            session["customer"] = {"id": customer.id, "email": customer.email, "is_auth": True}
            return redirect(url_for("account"))

    return render_template("register.html", error_msg=error_msg, form=form)


@app.route("/logout/")
def logout():
    return "logout_page"


@app.route("/ordered/")
def ordered():
    return render_template("ordered.html")


if __name__ == '__main__':
    app.run()  # запустим сервер