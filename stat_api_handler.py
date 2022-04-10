'''This module handles requests to football statistic API called ElenaSport.io.
URL: https://rapidapi.com/mararrdeveloper/api/elenasport-io1/.'''

import requests
from urllib.parse import urljoin
from config import STAT_API_URL, STAT_API_KEY, TEAMNAME_TRANSLATION, TOURNAMENT_NAME
import json

HEADERS = {'x-rapidapi-key': STAT_API_KEY,
		   'x-rapidapi-host': "elenasport-io1.p.rapidapi.com"
		   }
LEAGUE_ID = '422' # as per https://elenasport.io/doc/coverage


class StatAPIHandler():
	def __init__(self):
		pass

	def get_russia_id(self):
		#based on API's allCountries method. Gets Russia's id in API. Returns string
		endpoint = '/v2/countries'
		querystring = {"name":"Russia"}
		url = urljoin(STAT_API_URL, endpoint)
		r = requests.get(url, headers = HEADERS, params=querystring).json()
		return (r['data'][0]['id'])

	def get_league_by_country_id(self, country_id):
		#based on API's leaguesByCountryId method. Gets config.TOURNAMENT_NAME's id in API. Returns string
		endpoint = '/v2/countries/:id/leagues'
		url = urljoin(STAT_API_URL, endpoint.replace(':id',country_id))
		r = requests.get(url, headers = HEADERS).json()

		for league in r['data']:
			if league['name'] == TOURNAMENT_NAME:
				return league['id']
		return None

	def get_current_season_id(self, league_id):
		# gets current season id based on a league id. returns string
		endpoint = '/v2/leagues/:id/seasons'
		url = urljoin(STAT_API_URL, endpoint.replace(':id', league_id))
		r = requests.get(url, headers = HEADERS).json()
		return (r['data'][0]['id'])

	def get_season_calendar(self, season_id):
		'''Downloads all the info on a season by given season_id and dumps all the data into a calendar_filename txt
		file to be used as a database'''

		#based on API's fixturesBySeasonId method

		calendar_filename = f'calendar season id_{season_id}.txt'
		endpoint = '/v2/seasons/:id/fixtures'
		url = urljoin(STAT_API_URL, endpoint.replace(':id', season_id))
		querystring = {"page":"1"}
		r = requests.get(url, headers = HEADERS, params=querystring).json()

		while r['pagination']['hasNextPage']:
			del(r['pagination']) # we dont need that info in our calendar_filename anymore
			matches = r['data']
			for match in matches:
				translated_home_name = StatAPIHandler.translate_team_name(match['homeName'])
				translated_away_name = StatAPIHandler.translate_team_name(match['awayName'])
				match['homeName'], match['awayName'] = translated_home_name, translated_away_name

				# adding match score which is not included visibly in response data
				home_score = match["team_home_90min_goals"] + match["team_home_ET_goals"]
				away_score = match["team_away_90min_goals"] + match["team_away_ET_goals"]
				match['score'] = f'{home_score}-{away_score}'

			if querystring['page'] == '1':
				with open(calendar_filename, 'w', encoding = 'utf-8') as file:
					json.dump(r, file, indent=4, ensure_ascii=False)
			else:
				with open(calendar_filename, 'r', encoding = 'utf-8') as file:
					data_to_dump = json.load(file)
				for match in r['data']:
					data_to_dump['data'].append(match)
				with open(calendar_filename, 'w', encoding = 'utf-8') as file:
					json.dump(data_to_dump, file, indent = 4, ensure_ascii = False)

			querystring['page'] = str(int(querystring['page']) + 1)
			r = requests.get(url, headers = HEADERS, params=querystring).json()


	def get_match_by_id(self, id):
		#TODO написать метод
		#based on API's fixtureById method
		pass

	@staticmethod
	def read_db():
		#TODO считывание id
		current_season_id = '4208'
		db_filename = f'calendar season id_{current_season_id}.txt'

		try:
			with open (db_filename, 'r', encoding='utf-8') as f:
				return f.read()
		except FileNotFoundError:
			return

	@staticmethod
	def translate_team_name(eng_name):
		return TEAMNAME_TRANSLATION[eng_name] if eng_name in TEAMNAME_TRANSLATION else eng_name

	@staticmethod
	def write_data_into_file(data, filename):
		with open (filename, 'w', encoding='utf-8') as f:
			json.dump(data, f, indent = 4, ensure_ascii = False)

	@staticmethod
	def read_data_from_file(filename):
		with open (filename, 'r', encoding='utf-8') as f:
			return json.load(f)



sah = StatAPIHandler()

#db = sah.read_db()
#print(db)