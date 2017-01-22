# -*- coding: utf-8 -*-
from flask import render_template, session, redirect, url_for, flash, request
from main import app, login_manager, mail, auth
import forms, database, common
from flask.ext.bootstrap import Bootstrap
from flask.ext.login import login_required, login_user, logout_user, current_user
from flask.ext.mail import Message
from threading import Thread

bootstrap = Bootstrap(app)

# Main menu items and settings
main_menu = [
	{
		'id'	: common.MainMenuID.MAIN,
		'text'	: u'Etusivu',
		'link'	: '/'
	},
	{
		'id'	: common.MainMenuID.MATCHES,
		'text'	: u'Ottelut',
		'link'	: '/matches'
	},
	{
		'id'	: common.MainMenuID.RANKING,
		'text'	: u'Ranking',
		'link'	: '/ranking'
	},
	{
		'id'	: common.MainMenuID.MYPAGE,
		'text'	: u'Omasivu',
		'link'	: '/mypage'
	}
]

# Submenu items and settings
subpages = {
	common.MainMenuID.MYPAGE : {
		'default' : {
			'id'	: None,
			'text'	: u'Tiedot',
			'link'	: '/mypage'
		}
	},
	common.MainMenuID.MATCHES : {
		'default' : {
			'id'	: None,
			'text'	: u'Kalenteri',
			'link'	: '/matches'
		},
		'list' : {
			'id'	: 'list',
			'text'	: u'Kaikki ottelut',
			'link'	: '/matches/list'
		}
	}
}

def send_async_email(app, msg):
	with app.app_context():
		mail.send(msg)

def send_email(to, subject, template, **kwargs):
	msg = Message(
		app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
		sender=app.config['FLASKY_MAIL_SENDER'],
		recipients=[to])
	msg.body = render_template(template + '.txt', **kwargs)
	msg.html = render_template(template + '.html', **kwargs)
	thr = Thread(target=send_async_email, args=[app, msg])
	thr.start()
	return thr


@app.route('/')
def index():
	return render_template(
		'index.html',
		main_menu_id=common.MainMenuID.MAIN,
		main_menu=main_menu,
		sub_menu=False,
		form=forms.Login(),
		rules=common.Points()
	)

@app.route('/user_login')
def user_login():
	return render_template(
		'login.html',
		main_menu_id=common.MainMenuID.MAIN,
		main_menu=main_menu,
		sub_menu=False,
		form=forms.Login(),
		token=request.args.get('next')
	)

@app.route('/register', methods=['GET', 'POST'])
def register():
	form = forms.Register()
	if form.validate_on_submit():
		username = form.name.data
		password = form.password.data
		email = form.email.data
		new_user = database.add_user(username, password, email)
		if new_user:
			flash(u'Käyttäjä lisätty! Vahvista vielä saamasi sähköpostin mukaisesti.')	
			token = new_user.generate_confirmation_token()
			send_email(
				new_user.email, 'Vahvista rekisteröinti',
				'mail/confirm', user=new_user, token=token)
		else:
			flash(u'Käyttäjätunnus ja/tai sähköposti on jo käytössä!')
		form.name.data = form.password.data = form.email.data = None
	elif request.method == 'POST':
		flash(u'Täytä kaikki tiedot!')
	return render_template(
		'register.html',
		main_menu_id=common.MainMenuID.REGISTER,
		main_menu=main_menu,
		sub_menu=False,
		form=form
	)

@app.route('/confirm/<token>')
@login_required
def confirm(token):
	_confirm(token)
	
def _confirm(token, user=None):
	if user:
		this_user = user
	else:
		this_user = current_user
	this_user.confirm(token)

@app.route('/login', methods=['GET', 'POST'])
def login():
	form = forms.Login()
	if form.validate_on_submit():
		token = form.token.data
		email = form.email.data
		password = form.password.data
		user = database.validate_user(email, password)
		if user:
			if token:
				_confirm(token.split('/')[2], user=user)
			if not user.confirmed:
				flash(u'Ei aktivoitu. Tarkista sähköposti.')
			else:
				login_user(user, form.remember_me.data)
		else:
			flash(u'Käyttäjätunnus tai salasana väärin')
	return redirect(url_for('index'))

@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))
	
@app.route('/mypage', methods=['GET', 'POST'])
@app.route('/mypage/<subpage_id>')
@login_required
def my_page(subpage_id='default'):
	sub_menu = subpages[common.MainMenuID.MYPAGE]
	template = sub_menu[subpage_id]['link']
	form = forms.ChangePassword()
	if form.validate_on_submit():
		current_pw = form.current_pw.data
		new_pw = form.new_pw.data
		new_pw_confirm = form.new_pw_confirm.data
		if new_pw != new_pw_confirm:
			flash(u'Salasanan vaihto ei onnistunut.')
		elif current_user.check_password(current_pw):
			current_user.set_password(new_pw)
			database.db.session.add(current_user)
			database.db.session.commit()
			flash(u'Salasana muutettu')
		else:
			flash(u'Salasanan vaihto ei onnistunut.')
		
	return render_template(
		'auth'+template+'.html',
		main_menu_id=common.MainMenuID.MYPAGE,
		main_menu=main_menu,
		sub_menu_id=subpage_id,
		sub_menu=sub_menu,
		form=form
	)

@app.route('/ranking')
@login_required
def ranking():
	return render_template(
		'auth/ranking.html',
		main_menu_id=common.MainMenuID.RANKING,
		main_menu=main_menu,
		ranking=database.get_ranking()
	)	

@app.route('/matches')
@app.route('/matches/<int:year>/<int:month>')
@login_required
def matches(year=None, month=None, subpage_id='default', filter=None):
	sub_menu = subpages[common.MainMenuID.MATCHES]
	template = sub_menu[subpage_id]['link']

	if not year:
		year = common.timestamp().year
	if not month:
		month = common.timestamp().month
			
	return render_template(
		'auth'+template+'.html',
		main_menu_id=common.MainMenuID.MATCHES,
		main_menu=main_menu,
		sub_menu_id=subpage_id,
		sub_menu=sub_menu,
		special=common.generate_calendar(year, month),
		form=None
	)

@app.route('/matches/list')
@app.route('/matches/list/<int:team_id>')
@login_required
def matches_list(team_id=None):
	sub_menu = subpages[common.MainMenuID.MATCHES]
	if team_id:
		special = (database.get_teams(), database.get_matches_by_team(team_id))
	else:
		special = (database.get_teams(), database.get_matches(0))

	return render_template(
		'auth/matches/list.html',
		main_menu_id=common.MainMenuID.MATCHES,
		main_menu=main_menu,
		sub_menu_id='list',
		sub_menu=sub_menu,
		special=special,
		form=None
	)
	
@app.route('/matches/match/<int:match_id>', methods=['POST', 'GET'])
@login_required
def single_match(match_id):
	sub_menu = subpages[common.MainMenuID.MATCHES]
	match = database.get_match(match_id)
	
	form = forms.Bet(
		match.match_id,
		match.home_team.team_id,
		match.away_team.team_id
	)

	if form.validate_on_submit():
		match_id = form.match_id.data
		home_goals = form.home_goals.data
		away_goals = form.away_goals.data
		if (common.timestamp() < match.match_time):
			database.add_bet(match_id, current_user.id, home_goals, away_goals)
		else:
			flash(u'Et voi enää veikata tätä ottelua!')
			
	return render_template(
		'auth/match.html',
		main_menu_id=common.MainMenuID.MATCHES,
		main_menu=main_menu,
		sub_menu_id='default',
		sub_menu=sub_menu,
		match=match,
		allbets=database.get_all_bets(match_id),
		mybet=database.get_bet(match_id, current_user.id),
		form=form
	)
	
@app.route('/teams')
def teams():
	user = database.get_user(session.get("logged_username"))
	return render_template(
		'teams.html',
		title='Joukkueet',
		teams=database.get_teams(),
		user=user
	)


@app.route('/write_my_bet', methods=['GET', 'POST'])
def write_by_bet():
	form = forms.Bet()
	user = database.get_user(session.get('logged_username'))
	if form.validate_on_submit():
		match_id = form.match_id.data
		if (common.timestamp() > database.get_match(match_id).match_time):
			pass
		else:
			home_goals = form.home_goals.data
			away_goals = form.away_goals.data
			database.add_bet(match_id, user.id, home_goals, away_goals)
	return redirect(url_for('matches'))
	
@app.route('/bet/<int:id>', methods=['GET', 'POST'])
def bet(id):
	user = database.get_user(session.get('logged_username'))
	match=database.get_match(id)
	form = forms.Bet(id, match.home_team_id, match.away_team_id)
	
	match_id = None
	home_goals = None
	away_goals = None
	error = None
	if form.validate_on_submit():
		if (common.timestamp() > match.match_time):
			error = 'Tapahtui virhe'
		else:
			match_id = form.match_id.data
			home_goals = form.home_goals.data
			away_goals = form.away_goals.data
			database.add_bet(match_id, user.id, home_goals, away_goals)
			return redirect(url_for('mybets'))
	return render_template(
		'bet.html',
		title='Veikkaa',
		user=user,
		match=match,
		form=form,
		error=error
	)
	
@app.route('/result/<int:id>', methods=['GET', 'POST'])
def result(id):
	user = database.get_user(session.get('logged_username'))
	if user.role.name != 'admin':
		return redirect(url_for('matches'))
	match=database.get_match(id)
	form = forms.Result(id, match.home_team_id, match.away_team_id)
	
	match_id = None
	home_goals = None
	away_goals = None
	error = None
	if form.validate_on_submit():
		match_id = form.match_id.data
		home_goals = form.home_goals.data
		away_goals = form.away_goals.data
		played = form.played.data
		database.add_result(match_id, user.id, home_goals, away_goals, played)
		database.check_points()
		return redirect(url_for('matches'))
	return render_template(
		'result.html',
		title='Tulos',
		user=user,
		match=match,
		form=form,
		error=error
	)
	
@app.route('/mybets')
def mybets():
	user = database.get_user(session.get("logged_username"))
	user_bets = database.get_user_bets(user.id)
	return render_template(
		'mybets.html',
		title='Veikkaukseni',
		user=user,
		mybets=user_bets
	)

@app.route('/multibet', methods=['POST', 'GET'])
@login_required
def multibet():
	for val in request.values.items():
		print val[0].split(":")[0], val[1]
	return redirect(url_for('index'))

@app.route('/check_points')
@login_required
def check_points():
	if current_user.role.name == 'admin':
		database.check_points()
	return redirect(url_for('my_page'))

@app.route('/autocheck')
def autocheck():
	if current_user.role.name == 'admin':
		database.add_results_auto()
	return redirect(url_for('matches'))


@app.route('/autoinit')
def autoinit():
	if current_user.role.name == 'admin':
		database.init()
	return redirect(url_for('matches'))
