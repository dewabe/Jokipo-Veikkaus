import urllib2
import json

class GameLoader(object):
	''' Class for loading the games and such things '''
	def _load_data(self):
		''' Load data from the webpage '''
		req = urllib2.Request(self.url)
		return urllib2.urlopen(req).read()

	def _json_to_dict(self, json_string):
		''' Parse JSON string to dictionary	'''
		return json.loads(json_string)

	def _validate_data(self, data):
		''' If data is not ready to execute right away, modify it first '''
		return data

	def _picker(self, data, mode):
		''' Pick selected data from dictionary
		
		Keyword arguments:
		data	-- data in dictionary format
		mode	-- selected mode or type you want to take
		'''
		result = dict()
		for record in self._validate_data(data):
			if mode == 'teams':
				result[record[self.team_name]] = record[self.team_id]
			elif mode == 'matches':
				result[record[self.match_id]] = {
					item: record[item] for item in record
				}
		return result

	def getData(self):
		''' Combines _load_data and _json_to_dict functions '''
		return self._json_to_dict(self._load_data())

	def getTeams(self):
		''' Get team as dictionary '''
		return self._picker(self.getData(), 'teams')
	
	def getMatches(self):
		''' Get all games as dictionary '''
		return self._picker(self.getData(), 'matches')


class Mestis(GameLoader):
	def __init__(self, groupid, team_id='', rink=''):
		''' For Mestis
		
		Keyword arguments:
		groupid	-- Identification number for season
		team_id -- Every team has an unique ID number
		rink	-- Rink ID of the rink where the match takes place
		'''
		super(Mestis, self).__init__()
		self._url(groupid, team_id, rink)
		self._data()
		
	def _url(self, groupid, team_id, rink):
		''' Generating URL '''
		url = 'http://www.tilastopalvelu.fi'
		url += '/ih/modules/mod_schedule/helper'
		url += '/games.php'
		url += '?statgroupid='+str(groupid)
		url += '&select='
		url += '&id='
		url += '&teamid='+str(team_id)
		url += '&rinkid='+str(rink)
		url += '&rmd='
		self.url = url
	
	def _validate_data(self, data):
		'''
		We know the data from Mestis service is
		not directly accessed as default
		'''
		return data['games']
	
	def _data(self):
		''' Some identifications for data '''
		self.team_id = 'HomeTeamID'
		self.team_name = 'HomeTeamName'
		self.match_id = 'UniqueID'
		'''
		NOTE
		FinishedType
		 1	Game finished in 60 minutes
		 2	Overtime
		 3	Shootout
		GameStatus
		 0	Not played??
		 1	Running??
		 2	Played
		 3	Cancelled??
		'''

if __name__ == '__main__':
	gameloader = Mestis(168)
	matches = gameloader.getMatches()
	for match_id in matches:
		dt = '{} {}'.format(matches[match_id]['GameDate'], matches[match_id]['GameTime'])
		print dt
