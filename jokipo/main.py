# -*- coding: utf-8 -*-
import os
from flask import Flask, Blueprint
from flask.ext.login import LoginManager
from flask.ext.mail import Mail, Message

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'user_login'
app = Flask(__name__)
mail = Mail()
auth = Blueprint('auth', __name__)

import configuration, forms, database, views

login_manager.init_app(app)
mail.init_app(app)
