# -*- coding: utf-8 -*-
import datetime
import bcrypt
import common
import gameloader
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask.ext.login import UserMixin
from main import app, login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app

db = SQLAlchemy(app)

# Database models and tables

class Role(db.Model):
	''' User roles table '''
	__tablename__ = 'roles'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), unique=True)
	users = db.relationship('User', backref='role')
	
	def __repr__(self):
		return '<Role {}>'.format(self.name)
		
class User(UserMixin, db.Model):
	''' Users table '''
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), unique=True, nullable=False, index=True)
	password = db.Column(db.String(128), nullable=False)
	email = db.Column(db.String(64), nullable=False)
	date_registered = db.Column(db.DateTime)
	date_login = db.Column(db.DateTime)
	role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
	disabled = db.Column(db.Boolean, default=False)
	confirmed = db.Column(db.Boolean, default=False)
	
	def generate_confirmation_token(self, expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'confirm':self.id})
	
	def confirm(self, token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('confirm') != self.id:
			return False
		self.confirmed = True
		db.session.add(self)
		db.session.commit()
		return True
	
	def set_password(self, pw):
		pwhash = bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
		self.password = pwhash

	def check_password(self, pw):
		if self.password is not None:
			expected_hash = self.password
			actual_hash = bcrypt.hashpw(pw.encode('utf8'), expected_hash.encode('utf8'))
			return expected_hash == actual_hash
		return False
	
	def __repr__(self):
		return '<User {}>'.format(self.username)

class Team(db.Model):
	''' Teams table '''
	__tablename__ = 'teams'
	id = db.Column(db.Integer, primary_key=True)
	team_id = db.Column(db.Integer, unique=True)
	official = db.Column(db.String(64))
	name = db.Column(db.String(64), unique=True, nullable=False, index=True)
	logo = db.Column(db.String(64))

class Match(db.Model):
	''' Table for matches '''
	__tablename__ = 'matches'
	id = db.Column(db.Integer, primary_key=True)
	match_id = db.Column(db.Integer, unique=True)
	match_time = db.Column(db.DateTime)
	home_team_id = db.Column(db.Integer, db.ForeignKey('teams.team_id'))
	away_team_id = db.Column(db.Integer, db.ForeignKey('teams.team_id'))
	home_goals = db.Column(db.Integer, default=0)
	away_goals = db.Column(db.Integer, default=0)
	overtime = db.Column(db.Integer, default=0)
	played = db.Column(db.Boolean, default=False)
	points_shared = db.Column(db.Boolean, default=False)
	
	home_team = db.relationship("Team", foreign_keys=home_team_id)
	away_team = db.relationship("Team", foreign_keys=away_team_id)

class Bet(db.Model):
	''' Bet table '''
	__tablename__ = 'bets'
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	match_id = db.Column(db.Integer, db.ForeignKey('matches.match_id'))
	home_goals = db.Column(db.Integer)
	away_goals = db.Column(db.Integer)
	
	user = db.relationship("User", foreign_keys=user_id)
	match = db.relationship("Match", foreign_keys=match_id)

class Points(db.Model):
	''' Table for storing all the points users has got '''
	__tablename__ = 'points'
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	match_id = db.Column(db.Integer, db.ForeignKey('matches.match_id'))
	goals = db.Column(db.Integer)
	wins = db.Column(db.Integer)
	ties = db.Column(db.Integer)
	corrects = db.Column(db.Integer)
	total = db.Column(db.Integer)

# Functions to retrieve or add data

@login_manager.user_loader
def load_user(user_id):
	''' Get User from database '''
	return User.query.get(int(user_id))

def get_role(role):
	'''
	Find role from SQL
	'''
	return Role.query.filter_by(name=role).first()
	
def get_user_by_name(username):
	'''
	Find user from SQL using username
	'''
	return User.query.filter_by(username=username).first()
	
def get_user_by_email(email):
	'''
	Find user from SQL using email
	'''
	return User.query.filter_by(email=email).first()

def get_users():
	'''
	Return all users
	'''
	return User.query.all()

def add_user(username, password, email):
	'''
	Add new user if username or password won't be found
	'''
	if get_user_by_name(username) is None and get_user_by_email(email) is None:
		user = User(
			username=username,
			role=get_role('basic'),
			email=email,
			date_registered=common.timestamp()
		)
		user.set_password(password)
		db.session.add(user)
		db.session.commit()
		return user
	else:
		return False

def validate_user(email, password):
	'''
	Check does email exists and is the password correct
	'''
	user = get_user_by_email(email)
	print user
	if user and user.check_password(password):
		# Update the last login timestamp
		user.date_login = common.timestamp()
		db.session.add(user)
		db.session.commit()
		return user
	return False

def get_teams():
	''' Return list of teams '''
	return Team.query.all()

def get_team(team_id):
	'''
	Get team by team id
	'''
	return Team.query.filter_by(team_id=team_id).first()
	
def get_matches(played=None):
	''' Get played, not played or all matches '''
	if played is 1:
		return Match.query.order_by('match_time').filter_by(played=1).all()
	elif played is 0:
		return Match.query.order_by('match_time').filter_by(played=0).all()
	else:
		return Match.query.order_by('match_time').all()

def get_matches_by_team(team_id):
	''' Return all team matches as list '''
	return db.session.query(Match).order_by('match_time').filter(or_(
		Match.home_team_id == team_id,
		Match.away_team_id == team_id
	)).all()
		
def get_matches_by_month(dt):
	'''
	Get all the matches from the selected month
	'''
	start = str(dt)
	end = str(common.add_one_month(dt))
	return db.session.query(Match).filter(Match.match_time.between(start, end)).all()
	
def get_match(match_id):
	''' Get Match details '''
	return Match.query.filter_by(match_id=match_id).first()

def get_bet(match_id, user_id):
	''' Get users bet for single match '''
	return Bet.query.filter_by(match_id=match_id, user_id=user_id).first()
	
def get_all_bets(match_id):
	''' Get all bets according to the match id '''
	return Bet.query.filter_by(match_id=match_id).all()

def get_user_bets_all(user_id):
	''' Get all bets that user has been done so far '''
	return db.session.query(Bet, Match).filter_by(user_id=user_id).join(Match).order_by(Match.match_time).all()
	
def get_user_bets_with_points(user_id):
	''' Get all bets of user, including points '''
	all = get_user_bets_all(user_id)
	_return = list()
	for single in all:
		points = db.session.query(Points.total).filter_by(user_id=user_id, match_id=single.Match.id).first()
		if points:
			_s = [single[0], single[1], points[0]]
		else:
			_s = [single[0], single[1], 0]
		_return.append(_s)
	return _return
	
def add_bet(match_id, user_id, home_goals, away_goals):
	''' Adding new bet '''
	old_bet = get_bet(match_id, user_id)
	if old_bet:
		old_bet.home_goals = home_goals
		old_bet.away_goals = away_goals
		new_bet = old_bet
	else:
		new_bet = Bet(
			match_id = match_id,
			user_id = user_id,
			home_goals = home_goals,
			away_goals = away_goals
		)
	db.session.add(new_bet)
	db.session.commit()

def get_points(match_id, user_id):
	''' Get points that user has got in single match '''
	return Points.query.filter_by(match_id=match_id, user_id=user_id).first()

def check_points():
	'''
	Check what user has bet and what was the result of the game
	Write points to SQL
	'''
	matches = Match.query.order_by('match_time').filter_by(played=1, points_shared=0).all()
	print matches
	for match in matches:
		print match
		for bet in get_all_bets(match.match_id):
			if get_points(match.match_id, bet.user_id):
				continue
			if match.overtime:
				match_home_goals = match.home_goals
				match_away_goals = match.away_goals
			else:
				match_home_goals = min(match.home_goals, match.away_goals)
				match_away_goals = min(match.home_goals, match.away_goals)
				
			# Bet home goals is the same as match home goals
			goal_home = bet.home_goals == match_home_goals
			# Bet away goals is the same as match away goals
			goal_away = bet.away_goals == match_away_goals
			# Bet is tie
			tie_bet = (bet.home_goals - bet.away_goals) == 0
			# Match is tie
			tie_match = (match_home_goals - match_away_goals) == 0
			# Which team won the game, positive = home, negative = away, 0 = tie
			win_bet = (bet.home_goals - bet.away_goals)
			win_match = (match_home_goals - match_away_goals)
			
			goal = 0
			win = 0
			tie = 0
			correct = 0
			if goal_home:
				goal += common.Points.GOAL
			if goal_away:
				goal += common.Points.GOAL
			if tie_bet and tie_match:
				tie += common.Points.TIE
			elif (win_bet > 0 and win_match > 0) or (win_bet < 0 and win_match < 0):
				win += common.Points.WIN
			if goal_home and goal_away:
				correct += common.Points.CORRECT
			total = goal + tie + win + correct
			
			db.session.add(Points(
				match_id=match_id,
				user_id=bet.user_id,
				goals=goal,
				wins=win,
				ties=tie,
				corrects=correct,
				total=total
			))
			match.points_shared = 1
			db.session.add(match)
			db.session.commit()

def get_ranking():
	''' Generate ranking list '''
	points = db.session.query(
		Points.user_id,
		db.func.sum(Points.goals).label('total_goals'),
		db.func.sum(Points.wins).label('total_wins'),
		db.func.sum(Points.ties).label('total_ties'),
		db.func.sum(Points.corrects).label('total_corrects'),
		db.func.sum(Points.total).label('total_total'),
		db.func.count(Points.user_id).label('bets')
	).order_by(
		db.desc('total_total'),
		db.desc('total_corrects'),
		db.desc('total_ties'),
		db.desc('total_wins'),
		db.desc('total_goals')
	).group_by('user_id').all()
	ranking = dict()
	nro = 1
	for p in points:
		user = User.query.filter_by(id=p[0]).first()
		ranking[nro] = {
			'user': user,
			'goals': p[1],
			'wins': p[2],
			'ties': int(p[3]) / 2,
			'corrects': p[4],
			'total': p[5],
			'bets': p[6]
		}
		nro += 1
	return ranking
			
def add_result(match_id, user_id, home_goals, away_goals, played):
	''' Adding new bet '''
	match = get_match(match_id)
	match.home_goals = home_goals
	match.away_goals = away_goals
	match.played = played
	db.session.add(match)
	db.session.commit()
	
def add_results_auto():
	loader = gameloader.Mestis(168, 425114685)
	matches = loader.getMatches()
	for match_id in matches:
		if Match.query.filter_by(match_id=match_id).first():
			result = matches[match_id]['Result'].split()[0].split('-')
			played = 1 if matches[match_id]['GameStatus'] == '2' else 0
			overtime = 1 if matches[match_id]['FinishedType'] != '1' else 0
			thisMatch = get_match(match_id)
			thisMatch.home_goals=result[0]
			thisMatch.away_goals=result[1]
			thisMatch.played=played
			thisMatch.overtime=overtime
			db.session.add(thisMatch)
			db.session.commit()
	check_points()

def init():
	''' Initialize the database '''
	db.create_all()
	if not get_role('basic'):
		# User roles
		db.session.add(Role(name='basic'))
		db.session.add(Role(name='admin'))
		db.session.commit()
		
		user_master = User(
			username="master",
			role=get_role('admin'),
			email="email@to.master.user",
			date_registered=common.timestamp()
		)
		user_master.set_password("1234")
		db.session.add(user_master)
		db.session.commit()
		
	loader = gameloader.Mestis(168, 425114685)
	for team, team_id in loader.getTeams().iteritems():
		if Team.query.filter_by(name=team).first() is None:
			thisTeam = Team(name=team, team_id=team_id)
			db.session.add(thisTeam)
			db.session.commit()
	matches = loader.getMatches()
	for match_id in matches:
		if Match.query.filter_by(match_id=match_id).first() is None:
			dt = '{} {}'.format(matches[match_id]['GameDate'], matches[match_id]['GameTime'])
			result = matches[match_id]['Result'].split()[0].split('-')
			thisMatch = Match(
				match_id=match_id,
				home_team_id=matches[match_id]['HomeTeamID'],
				away_team_id=matches[match_id]['AwayTeamID'],
				match_time=common.set_timestamp(dt)
			)
			db.session.add(thisMatch)
			db.session.commit()

