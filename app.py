import os

from flask import Flask, render_template, request, session, redirect, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime
from flask_wtf.csrf import CsrfProtect

from config import Config
from models import db, Customer, Order, Meal, Category, OrderedMeal
from forms import ClientContact, ClientAuth, ChangePasswordForm


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
admin = Admin(app)

csrf = CsrfProtect()
csrf.init_app(app)

class MyUserView(ModelView):
    # Настройка общего списка
    column_exclude_list = ['password_hash']  # убрать из списка одно или несколько полей


admin.add_view(MyUserView(Customer, db.session))
admin.add_view(MyUserView(Order, db.session))
admin.add_view(MyUserView(Meal, db.session))
admin.add_view(MyUserView(Category, db.session))
admin.add_view(MyUserView(OrderedMeal, db.session))


@app.route("/")
def index():
    session["total_cheque"] = session.get("total_cheque", 0)
    session["n_meals"] = session.get("n_meals", 0)
    session["cart"] = session.get("cart", [])
    session["meals"] = session.get("meals", {0: {"title": "", "price": 0, "amount": 0}})
    session["customer"] = session.get("customer", {"id": 0, "email": "", "is_auth": False})
    session["generated_password"] = session.get("generated_password", "")
    session["contacts"] = session.get("contacts", {})
    categories = db.session.query(Category).all()
    meals = db.session.query(Meal).all()
    return render_template("main.html", categories=categories, meals=meals,
                           total_cheque=session["total_cheque"], n_meals=session["n_meals"],
                           customer=session["customer"])


@app.route("/updatecart/<action>/<int:meal_id>/")
def updatecart(action, meal_id):
    # Получаем либо значение из сессии, либо пустой список
    session["cart"] = session.get("cart", [])
    if action == "add":
        # Добавлям элемент в список
        session["cart"].append(meal_id)
    elif action == "remove":
        # удаляем элемент из списка
        session["cart"] = [element for element in session["cart"] if element != meal_id]

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


@app.route("/cart/", methods=["GET", "POST"])
@app.route("/cart/<action>/", methods=["GET", "POST"])
def cart(action=""):
    session["total_cheque"] = session.get("total_cheque", 0)
    session["n_meals"] = session.get("n_meals", 0)
    session["meals"] = session.get("meals", {0: {"title": "", "price": 0, "amount": 0}})
    session["cart"] = session.get("cart", [])
    session["customer"] = session.get("customer", {"id": 0, "email": "", "is_auth": False})
    session["generated_password"] = session.get("generated_password", "")

    form = ClientContact()

    error_msg = ""
    if request.method == "POST":
        input_name = form.client_name.data
        input_address = form.client_address.data
        input_email = form.client_email.data
        input_phone = form.client_phone.data
        session["contacts"] = {"name": input_name, "address": input_address, "phone": input_phone}

        if "@" not in input_email:
            error_msg = "Некорректная почта"
            return render_template("cart.html", form=form, action=action, cart_meals=session["meals"],
                                   total_cheque=session["total_cheque"], n_meals=session["n_meals"],
                                   customer=session["customer"], contacts=session["contacts"],
                                   error_msg=error_msg)

        # Если покупателя нет в БД, то создаем его и генерим ему пароль
        customer = db.session.query(Customer).filter(Customer.email == input_email).first()
        if not customer:
            # генерим пароль
            customer = Customer()
            customer.email = input_email
            session["generated_password"] = customer.generate_password()
            customer.password(session["generated_password"])
            db.session.add(customer)
            db.session.commit()
            session["customer"]["is_auth"] = True

        session["customer"]["id"] = customer.id
        session["customer"]["email"] = customer.email

        if session["cart"] == []:
            error_msg = "Ваша корзина пуста. Выберите что-нибудь поесть."
            return render_template("cart.html", form=form, action=action, cart_meals=session["meals"],
                                   total_cheque=session["total_cheque"], n_meals=session["n_meals"],
                                   customer=session["customer"], contacts=session["contacts"],
                                   error_msg=error_msg)

        ### создается экземпляр заказа и записывается в таблицу
        order = Order(total_payment=session["total_cheque"],
                      status="order is accepted",
                      customer_id=customer.id,
                      address=input_address,
                      phone=input_phone)
        db.session.add(order)
        db.session.commit()



        ### в экземпляр заказа добавляются блюда из корзины
        for meal_key, meal_value in session["meals"].items():
            ordered_meal = OrderedMeal(order_id=order.id, meal_id=meal_key,
                                       meal_amount=meal_value["amount"])
            db.session.add(ordered_meal)

        db.session.commit()

        return redirect(url_for("ordered"))


    return render_template("cart.html", form=form, action=action, cart_meals=session["meals"],
                           total_cheque=session["total_cheque"], n_meals=session["n_meals"],
                           customer=session["customer"], contacts=session["contacts"],
                           error_msg=error_msg)


@app.route("/account/")
def account():
    session["total_cheque"] = session.get("total_cheque", 0)
    session["n_meals"] = session.get("n_meals", 0)
    session["cart"] = session.get("cart", [])
    session["meals"] = session.get("meals", {0: {"title": "", "price": 0, "amount": 0}})
    session["customer"] = session.get("customer", {"id": 0, "email": "", "is_auth": False})
    session["generated_password"] = session.get("generated_password", "")
    session["contacts"] = session.get("contacts", {})
    session["customer"] = session.get("customer", {"id": 0, "email": "", "is_auth": False})
    if not session["customer"]["is_auth"]:
        return redirect(url_for("login"))

    orders = db.session.query(Order).filter(Order.customer_id == session["customer"]["id"]).all()
    lst_order_id = [order.id for order in orders]

    # query = db.session.query(OrderedMeal).filter(OrderedMeal.order_id.in_(lst_order_id))
    # query = query.join(Meal, OrderedMeal.meal_id == Meal.id)
    # order_details = query.all()
    details = db.session.query(OrderedMeal).filter(OrderedMeal.order_id.in_(lst_order_id)).all()
    order_details = []
    for detail in details:
        meal = db.session.query(Meal).filter(Meal.id == detail.meal_id).first()
        order_details.append({"order_id": detail.order_id, "title": meal.title,
                              "price": meal.price, "amount": detail.meal_amount})

    session["meals"] = {0: {"title": "", "price": 0, "amount": 0}}
    session["total_cheque"] = 0
    session["n_meals"] = 0
    session["cart"] = []
    session["customer"] = session.get("customer", {"id": 0, "email": "", "is_auth": False})
    session["generated_password"] = session.get("generated_password", "")
    session["contacts"] = session.get("contacts", {})

    return render_template("account.html", customer=session["customer"],
                           orders=orders, order_details=order_details,
                           total_cheque=session["total_cheque"], n_meals=session["n_meals"],
                           generated_password=session["generated_password"])


@app.route("/login/", methods=["GET", "POST"])
def login():
    session["total_cheque"] = session.get("total_cheque", 0)
    session["n_meals"] = session.get("n_meals", 0)
    session["cart"] = session.get("cart", [])
    session["meals"] = session.get("meals", {0: {"title": "", "price": 0, "amount": 0}})
    session["customer"] = session.get("customer", {"id": 0, "email": "", "is_auth": False})
    session["generated_password"] = session.get("generated_password", "")
    session["contacts"] = session.get("contacts", {})
    session["customer"] = session.get("customer", {"id": 0, "email": "", "is_auth": False})

    if session["customer"]["is_auth"]:
        return redirect(url_for("account"))

    form = ClientAuth()
    error_msg = ""

    if request.method == 'POST':
        input_email = form.client_email.data
        input_password = form.client_password.data

        customer = db.session.query(Customer).filter(Customer.email == input_email).first()

        if customer and customer.password_valid(input_password):
            session["customer"] = {"id": customer.id, "email": customer.email, "is_auth": True}
            return redirect(url_for("account"))
        else:
            error_msg = "Не удаётся войти. Пожалуйста, проверьте правильность написания логина и пароля."
            return render_template("login.html", form=form, error_msg=error_msg, customer=session["customer"],
                                   total_cheque=session["total_cheque"], n_meals=session["n_meals"])

    return render_template("login.html", form=form, error_msg=error_msg, customer=session["customer"],
                           total_cheque=session["total_cheque"], n_meals=session["n_meals"])


@app.route("/register/", methods=["GET", "POST"])
def register():
    session["total_cheque"] = session.get("total_cheque", 0)
    session["n_meals"] = session.get("n_meals", 0)
    session["cart"] = session.get("cart", [])
    session["meals"] = session.get("meals", {0: {"title": "", "price": 0, "amount": 0}})
    session["customer"] = session.get("customer", {"id": 0, "email": "", "is_auth": False})
    session["generated_password"] = session.get("generated_password", "")
    session["contacts"] = session.get("contacts", {})
    session["customer"] = session.get("customer", {"id": 0, "email": "", "is_auth": False})
    session["customer"] = session.get("customer", {"id": 0, "email": "", "is_auth": False})
    if session["customer"]["is_auth"]:
        return redirect(url_for("account"))

    form = ClientAuth()
    error_msg = ""

    if request.method == "POST":
        input_email = form.client_email.data
        input_password = form.client_password.data

        customer = db.session.query(Customer).filter(Customer.email == input_email).first()

        if "@" not in input_email:
            error_msg = "Некорректная почта"
            return render_template("register.html", error_msg=error_msg, form=form,
                                   total_cheque=session["total_cheque"], n_meals=session["n_meals"])
        elif customer:
            error_msg = "Такой пользователь уже существует"
            return render_template("register.html", error_msg=error_msg, form=form,
                                   total_cheque=session["total_cheque"], n_meals=session["n_meals"])
        elif len(input_password) < 8:
            error_msg = "Пароль слишком простой"
            return render_template("register.html", error_msg=error_msg, form=form,
                                   total_cheque=session["total_cheque"], n_meals=session["n_meals"])
        else:
            customer = Customer()
            customer.email = input_email
            customer.password(input_password)
            db.session.add(customer)
            db.session.commit()
            session["customer"] = {"id": customer.id, "email": customer.email, "is_auth": True}
            return redirect(url_for("account"))

    return render_template("register.html", error_msg=error_msg, form=form,
                           total_cheque=session["total_cheque"], n_meals=session["n_meals"])


@app.route("/logout/")
def logout():
    session["total_cheque"] = 0
    session["n_meals"] = 0
    session["meals"] = {}
    session["cart"] = []
    session["customer"] = {"id": 0, "email": "", "is_auth": False}
    session["generated_password"] = ""

    return redirect(url_for("index"))


@app.route("/ordered/")
def ordered():
    session["total_cheque"] = session.get("total_cheque", 0)
    session["n_meals"] = session.get("n_meals", 0)
    session["cart"] = session.get("cart", [])
    session["meals"] = session.get("meals", {0: {"title": "", "price": 0, "amount": 0}})
    session["customer"] = session.get("customer", {"id": 0, "email": "", "is_auth": False})
    session["generated_password"] = session.get("generated_password", "")
    session["contacts"] = session.get("contacts", {})
    session["customer"] = session.get("customer", {"id": 0, "email": "", "is_auth": False})

    return render_template("ordered.html",
                           total_cheque=session["total_cheque"], n_meals=session["n_meals"])


@app.route("/change-password/", methods=["GET", "POST"])
def change_password():
    session["total_cheque"] = session.get("total_cheque", 0)
    session["n_meals"] = session.get("n_meals", 0)
    session["cart"] = session.get("cart", [])
    session["meals"] = session.get("meals", {0: {"title": "", "price": 0, "amount": 0}})
    session["customer"] = session.get("customer", {"id": 0, "email": "", "is_auth": False})
    session["generated_password"] = session.get("generated_password", "")
    session["contacts"] = session.get("contacts", {})
    session["customer"] = session.get("customer", {"id": 0, "email": "", "is_auth": False})

    form = ChangePasswordForm()

    if request.method == "POST" and form.validate_on_submit():
        old_password = form.old_password.data
        new_password = form.new_password.data
        customer = db.session.query(Customer).filter(Customer.id == session["customer"]["id"]).first()
        if customer and customer.password_valid(old_password):
            # Обновляем пароль у текущего пользователя
            customer.password(new_password)
            db.session.add(customer)
            db.session.commit()
            session["generated_password"] = ""
            return redirect(url_for("account"))

    return render_template("change_password.html", form=form,
                           total_cheque=session["total_cheque"], n_meals=session["n_meals"])

if __name__ == '__main__':
    app.run()  # запустим сервер