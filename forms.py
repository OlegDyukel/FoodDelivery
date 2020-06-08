import email_validator

from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, HiddenField, FormField
from wtforms.validators import InputRequired, Email


class ClientContact(FlaskForm):
    client_name = StringField("Ваше имя",
                             [InputRequired(message="Как к вам обращаться?")])
    client_address = StringField("Адрес доставки",
                             [InputRequired(message="Куда нам привезти заказ?")])
    client_email = StringField("Электропочта",
                    [InputRequired(message="Куда отправить информацию о заказе?")])
    client_phone = StringField("Телефон",
                               [InputRequired(message="Как курьеру связаться с вами?")])