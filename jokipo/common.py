# -*- coding: utf-8 -*-
import datetime
import calendar
import xml.etree.ElementTree as etree
import database

calendar.month_name = [
	'',
	'Tammikuu',
	'Helmikuu',
	'Maaliskuu',
	'Huhtikuu',
	'Toukokuu', 
	u'Kesäkuu'.encode('utf8'),
	u'Heinäkuu'.encode('utf8'),
	'Elokuu',
	'Syyskuu',
	'Lokakuu',
	'Marraskuu',
	'Joulukuu'
]

calendar.day_name = [
	'Maanantai',
	'Tiistai',
	'Keskiviikko',
	'Torstai',
	'Perjantai',
	'Lauantai',
	'Sunnuntai'
]

calendar.day_abbr = [
	'Ma',
	'Ti',
	'Ke',
	'To',
	'Pe',
	'La',
	'Su'
]

def timestamp():
	''' Return current timestamp in local server time '''
	return datetime.datetime.now()

def set_timestamp(string_date):
	'''
	Return string as datetime
	'''
	return datetime.datetime.strptime(string_date, "%d.%m.%Y %H:%M:%S")

class Points():
	''' For calculating the points '''
	GOAL = 1
	WIN = 1
	TIE = 2
	CORRECT = 1

class MainMenuID():
	''' Identify every main menu item '''
	MAIN = 'MAIN'
	REGISTER = 'REGISTER'
	MATCHES = 'MATCHES'
	RANKING = 'RANKING'
	MYPAGE = 'MYPAGE'

def subtract_one_month(dt):
	''' Substract one month to datetime '''
	return dt - datetime.timedelta(days=1)
	
def add_one_month(dt):
	''' Add one month to datetime '''
	return dt + datetime.timedelta(days=31)

def calendar_header(root, year, month):
	'''
	Generate header for the calendar
	includes "next" and "previous" buttons for months
	'''
	this_date = datetime.datetime.strptime(str(year) + '-' + str(month), '%Y-%m')
	
	prev_date = subtract_one_month(this_date)
	prev_date_str = '{}/{}'.format(prev_date.year, prev_date.month)
	
	next_date = add_one_month(this_date)
	next_date_str = '{}/{}'.format(next_date.year, next_date.month)
	
	for elem in root.findall("*//th"):
		a = etree.SubElement(elem, "a")
		a.set('href', '/matches/' + prev_date_str)
		a.text = "Edellinen "

		t = etree.SubElement(elem, 'span')
		t.text = ' | ' + elem.text + ' | '
		elem.text = ''
		
		b = etree.SubElement(elem, "a")
		b.set('href', '/matches/' + next_date_str)
		b.text = " Seuraava"
		break
	return root

def calendar_days(root, year, month):
	'''
	Generate days for calendar
	marks "today"
	'''
	this_date = datetime.datetime.strptime(str(year) + '-' + str(month), '%Y-%m')
	matches = database.get_matches_by_month(this_date)
	matches_by_date = dict()
	for match in matches:
		try:
			matches_by_date[match.match_time.day].append(match)
		except:
			matches_by_date[match.match_time.day] = list()
			matches_by_date[match.match_time.day].append(match)
	day_passed = True
	cur_dt = timestamp()
	for elem in root.findall("*//td"):
		_day = elem.text
		elem.text = ''
		try:
			for day_match in matches_by_date[int(_day)]:
				home_team = database.get_team(day_match.home_team_id).name[:3]
				away_team = database.get_team(day_match.away_team_id).name[:3]
				link = etree.SubElement(elem, "a")
				link.tail = home_team + '-' + away_team
				if day_match.played:
					overtime = ' '
					if day_match.overtime:
						overtime += "JA" if day_match.overtime == 1 else "VL"
					link.tail += ' ' + str(day_match.home_goals) + '-' + str(day_match.away_goals) + overtime
				link.set('href', '/matches/match/' + str(day_match.match_id))
				br = etree.SubElement(elem, 'br')
				elem.set('class', elem.get('class') + ' match_day')
		except:
			pass
		if _day != " ":
			td_day_a = etree.SubElement(elem, 'a')
			td_day_a.set('href', '#')#'/match_day/{}-{}-{}'.format(year, month, _day))
			td_day = etree.SubElement(td_day_a, 'span')
			td_day.tail = _day
			td_day.set('class', 'day_number')
		if year > cur_dt.year:
			continue
		if year == cur_dt.year and month > cur_dt.month:
			continue
		if _day == str(timestamp().day):
			elem.set('class', elem.get('class') + ' today')
			day_passed = False
		if (month < cur_dt.month or day_passed or year < cur_dt.year) and elem.get('class') != 'noday':
			elem.set('class', 'day_passed')
	return root

def generate_calendar(year, month):
	''' Generate calendar '''
	myCal = calendar.HTMLCalendar(calendar.MONDAY)
	htmlStr = myCal.formatmonth(year, month)
	htmlStr = htmlStr.replace("&nbsp;"," ")
	root = etree.fromstring(htmlStr)
	# Generate header
	root = calendar_header(root, year, month)
	# Generate days
	root = calendar_days(root, year, month)
	return etree.tostring(root)
