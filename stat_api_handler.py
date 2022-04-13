'''This module handles requests to football statistic API called ElenaSport.io.
URL: https://rapidapi.com/mararrdeveloper/api/elenasport-io1/.'''

import requests
from urllib.parse import urljoin
from config import STAT_API_URL, STAT_API_KEY, TEAMNAME_TRANSLATION, TOURNAMENT_NAME, COUNTRY_NAME
import json
import os
import logging
from typing import Union

HEADERS = {'x-rapidapi-key': STAT_API_KEY,
		   'x-rapidapi-host': "elenasport-io1.p.rapidapi.com"
		   }

if not os.path.isdir('Logs'):
	os.mkdir('Logs')
log_file = os.path.join('Logs', f'{os.path.basename(__file__)}.log')
logging.basicConfig(filename=log_file,
					format='%(asctime)s: %(levelname)s: %(funcName)s: %(message)s',
					datefmt='%d/%m/%Y %H:%M:%S %p',
					level=logging.DEBUG
					)

class StatAPIHandler():
	def __init__(self):
		#TODO add country, league and other id's gathered with coressponding methods
		pass

	def get_country_id_by_name(self) -> Union[int, None]:
		#based on API's allCountries method. Gets country's id in API.
		endpoint = '/v2/countries'
		country_name = COUNTRY_NAME
		querystring = {"name":country_name}
		url = urljoin(STAT_API_URL, endpoint)
		r = requests.get(url, headers = HEADERS, params=querystring)

		if not r.status_code == requests.codes.ok:
			logging.debug(f'Bad request:{r.json()["message"]} Arg passed: {country_name}')
			return None

		if r.json()['data'] == []: # country doesn't exist
			logging.debug(f'Country doesn\'t exist. Arg passed: {country_name}')
			return None

		return (r.json()['data'][0]['id'])

	def get_league_id_by_country_id(self, country_id: int) -> Union[int, None]:
		#based on API's leaguesByCountryId method. Gets config.TOURNAMENT_NAME's id in API.
		endpoint = '/v2/countries/:id/leagues'
		url = urljoin(STAT_API_URL, endpoint.replace(':id',str(country_id)))
		r = requests.get(url, headers = HEADERS)

		if not r.status_code == requests.codes.ok:
			logging.debug(f'Bad request:{r.json()["message"]} Arg passed: {country_id}')
			return None

		leagues_in_country = r.json()['data']
		for league in leagues_in_country:
			if league['name'] == TOURNAMENT_NAME:
				return league['id']

		logging.debug(f'No {TOURNAMENT_NAME} in country with given country_id ({country_id})')
		return None

	def get_current_season_id_by_league_id(self, league_id: int) -> Union[int, None]:
		# gets current season id based on a league id. Based on a seasonsByLeagueId method. Returns string
		endpoint = '/v2/leagues/:id/seasons'
		url = urljoin(STAT_API_URL, endpoint.replace(':id', str(league_id)))
		r = requests.get(url, headers = HEADERS)

		if not r.status_code == requests.codes.ok:
			logging.debug(f'Bad request:{r.json()["message"]} Arg passed: {league_id}')
			return None

		return r.json()['data'][0]['id']

	def get_season_calendar(self, season_id):
		'''Downloads all the info on a season by given season_id and dumps all the data into a calendar_filename txt
		file to be used as a database'''

		#based on API's fixturesBySeasonId method

		calendar_filename = f'calendar season id_{season_id}.txt'
		endpoint = '/v2/seasons/:id/fixtures'
		url = urljoin(STAT_API_URL, endpoint.replace(':id', str(season_id)))
		querystring = {"page":"1"}
		r = requests.get(url, headers = HEADERS, params=querystring)

		if not r.status_code == requests.codes.ok:
			logging.debug(f'Bad request:{r.json()["message"]} Arg passed: {season_id}')
			return None

		r = r.json()
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

			calendar_path = ''
			if querystring['page'] == '1':
				if not os.path.isdir(os.path.join(os.getcwd(), 'Calendars')):
					os.mkdir('Calendars')
				calendar_path = os.path.join('Calendars', calendar_filename)
				with open(calendar_path, 'w', encoding='utf-8') as file:
					json.dump(r, file, indent=4, ensure_ascii=False)
			else:
				with open(calendar_path, 'r', encoding = 'utf-8') as file:
					data_to_dump = json.load(file)
				for match in r['data']:
					data_to_dump['data'].append(match)
				with open(calendar_path, 'w', encoding = 'utf-8') as file:
					json.dump(data_to_dump, file, indent = 4, ensure_ascii = False)

			querystring['page'] = str(int(querystring['page']) + 1)
			r = requests.get(url, headers = HEADERS, params=querystring).json()

	def get_match_by_id(self, match_id):
		#based on API's fixtureById method
		if not isinstance(match_id, int):
			logging.debug(f'Match id must be an integer. Arg passed: {match_id}')
			return None

		endpoint = '/v2/fixtures/:id'
		url = urljoin(STAT_API_URL, endpoint.replace(':id', str(match_id)))
		querystring = {'events': True}
		r = requests.get(url, headers= HEADERS, params=querystring)

		if not r.status_code == requests.codes.ok:
			logging.debug(f'Bad request:{r.json()["message"]} Arg passed: {match_id}')
			return None

		return r.json()

	@staticmethod
	def read_db():
		#TODO считывание id
		current_season_id = '4208'

		if not os.path.isdir('Calendars'):
			logging.debug('Nothing to read. "Calendars" folder doesn\'t exist')
			return None

		db_filename = f'calendar season id_{current_season_id}.txt'
		db_path = os.path.join('Calendars', db_filename)

		if db_filename not in db_path:
			logging.debug('Database doesn\'t exist in provided path')
			return None

		with open (db_filename, 'r', encoding='utf-8') as f:
			return json.load(f)

	@staticmethod
	def translate_team_name(eng_name):
		return TEAMNAME_TRANSLATION[eng_name] if eng_name in TEAMNAME_TRANSLATION else eng_name

#for debug purposes
sah = StatAPIHandler()

#country_id = sah.get_country_id()
#print(country_id)
country_id = 71

#league_id = sah.get_league_id_by_country_id(country_id)
#print(league_id)
league_id = 422

#season_id = sah.get_current_season_id_by_league_id(league_id)
#print(season_id)
season_id = 4208

#desired_match_id = 12312312312
#m = sah.get_match_by_id(desired_match_id)
#print(m)