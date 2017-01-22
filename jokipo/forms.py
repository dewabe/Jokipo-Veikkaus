# -*- coding: utf-8 -*-
from main import app
import database
from flask.ext.wtf import Form
from wtforms import StringField, HiddenField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import Required, Email


class Register(Form):
	''' Registration form '''
	name = StringField(u'Nimimerkki', validators=[Required()])
	password = PasswordField(u'Salasana', validators=[Required()])
	email = StringField(u'Sähköposti', validators=[Email()])
	submit = SubmitField(u'Rekisteröidy')

class Login(Form):
	''' Login form '''
	email = StringField(u'Sähköposti', validators=[Required()])
	password = PasswordField(u'Salasana', validators=[Required()])
	remember_me = BooleanField(u'Muista minut')
	token = HiddenField(u'token')
	submit = SubmitField(u'Kirjaudu')

class Bet(Form):
	''' Betting form '''
	match_id = HiddenField(u'match_id')
	home_goals = IntegerField(u'Kotijoukkueen maalit')
	away_goals = IntegerField(u'Vierasjoukkueen maalit')
	submit = SubmitField(u'Veikkaa')

	def __init__(self, match_id, home_id, away_id):
		super(Bet, self).__init__()
		self.match_id.data = match_id
		self.home_goals.description = database.get_team(home_id).name
		self.away_goals.description = database.get_team(away_id).name

class Result(Form):
	''' Result form for admin user '''
	match_id = HiddenField(u'match_id')
	home_goals = StringField(u'Koti')
	away_goals = StringField(u'Vieras')
	overtime = BooleanField(u'Jatkoaika')
	played = BooleanField(u'Pelattu')
	submit = SubmitField(u'Lähetä')
	
	def __init__(self, match_id, home_id, away_id):
		super(Result, self).__init__()
		self.match_id.data = match_id
		self.home_goals.description = database.get_team(home_id).name
		self.away_goals.description = database.get_team(away_id).name

class ChangePassword(Form):
	''' Change user password '''
	current_pw = PasswordField(u'Nykyinen salasana')
	new_pw = PasswordField(u'Uusi salasana')
	new_pw_confirm = PasswordField(u'Uusi salasana uudestaan')
	submit = SubmitField(u'Muuta')
