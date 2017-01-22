# -*- coding: utf-8 -*-
import os
from main import app

basedir = os.path.abspath(os.path.dirname(__file__))

print os.path.join(basedir, 'data.sqlite')

app.config.update(
	SECRET_KEY = 'Monthy Python and the Super Rabbit',
	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite'),
	SQLALCHEMY_COMMIT_ON_TEARDOWN = False,
	SQLALCHEMY_TRACK_MODIFICATIONS = True,
	MAIL_SERVER = 'smtp.gmail.com',
	MAIL_PORT = 465,
	MAIL_USE_SSL = True,
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME'),
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD'),
	FLASKY_MAIL_SUBJECT_PREFIX = 'JOKIPO VEIKKAUS: ',
	FLASKY_MAIL_SENDER = 'Jokipoveikkaus <jokikoveikkaus@gmail.com>',
	FLASKY_ADMIN = 'flask@admin.user'
)
