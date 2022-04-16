'''This module handles requests to football statistic API called ElenaSport.io.
URL: https://rapidapi.com/mararrdeveloper/api/elenasport-io1/.'''

import requests
from urllib.parse import urljoin
from config import STAT_API_URL, STAT_API_KEY, TEAMNAME_TRANSLATION, TOURNAMENT_NAME, COUNTRY_NAME
import json
import os
import logging
from typing import Union
import util
import datetime

HEADERS = {'x-rapidapi-key': STAT_API_KEY,
		   'x-rapidapi-host': "elenasport-io1.p.rapidapi.com"
		   }

util.insure_dir_exists('Logs')
log_file = os.path.join('Logs', f'{os.path.basename(__file__)}.log')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter(fmt='%(levelname)s: %(asctime)s: %(funcName)s: %(message)s',
								  datefmt='%d/%m/%Y %H:%M:%S %p'
								  )
log_file_handler = logging.FileHandler(log_file)
logger.addHandler(log_file_handler)
log_file_handler.setFormatter(log_formatter)

class StatAPIHandler:
	def __init__(self):
		# TODO add country, league and other id's gathered with coressponding methods
		pass

	def get_country_id_by_name(self) -> Union[int, None]:
		# based on API's allCountries method. Gets country's id in API.
		endpoint = '/v2/countries'
		country_name = COUNTRY_NAME
		querystring = {"name": country_name}
		url = urljoin(STAT_API_URL, endpoint)
		r = requests.get(url, headers=HEADERS, params=querystring)

		if not r.status_code == requests.codes.ok:
			logger.error(f'Bad request:{r.json()["message"]} Arg passed: {country_name}')
			return None

		if r.json()['data'] == []:  # country doesn't exist
			logger.error(f'Country doesn\'t exist. Arg passed: {country_name}')
			return None

		return (r.json()['data'][0]['id'])

	def get_league_id_by_country_id(self, country_id: int) -> Union[int, None]:
		# based on API's leaguesByCountryId method. Gets config.TOURNAMENT_NAME's id in API.
		endpoint = '/v2/countries/:id/leagues'
		url = urljoin(STAT_API_URL, endpoint.replace(':id', str(country_id)))
		r = requests.get(url, headers=HEADERS)

		if not r.status_code == requests.codes.ok:
			logger.error(f'Bad request:{r.json()["message"]} Arg passed: {country_id}')
			return None

		leagues_in_country = r.json()['data']
		for league in leagues_in_country:
			if league['name'] == TOURNAMENT_NAME:
				return league['id']

		logger.error(f'No {TOURNAMENT_NAME} in country with given country_id ({country_id})')
		return None

	def get_current_season_id_by_league_id(self, league_id: int) -> Union[int, None]:
		# gets current season id based on a league id. Based on a seasonsByLeagueId method. Returns string
		endpoint = '/v2/leagues/:id/seasons'
		url = urljoin(STAT_API_URL, endpoint.replace(':id', str(league_id)))
		r = requests.get(url, headers=HEADERS)

		if not r.status_code == requests.codes.ok:
			logger.error(f'Bad request:{r.json()["message"]} Arg passed: {league_id}')
			return None

		return r.json()['data'][0]['id']

	def get_season_calendar(self, season_id):
		'''Downloads all the info on a season by given season_id and dumps all the data into a calendar_filename txt
		file to be used as a database'''

		# based on API's fixturesBySeasonId method

		calendar_filename = f'calendar season id_{season_id}.txt'
		endpoint = '/v2/seasons/:id/fixtures'
		url = urljoin(STAT_API_URL, endpoint.replace(':id', str(season_id)))
		querystring = {"page": "1"}

		response_has_next_page = True
		while response_has_next_page:
			r = requests.get(url, headers=HEADERS, params=querystring)

			if not r.status_code == requests.codes.ok:
				logger.error(f'Bad request:{r.json()["message"]} Arg passed: {season_id}')
				return

			r = r.json()
			page_data = r['pagination'] # we remember this part
			del (r['pagination']) #and right off the bat get rid of it because we don't need to store it

			matches = r['data']
			for match in matches:
				# translating team names from english
				translated_home_name = StatAPIHandler.translate_team_name(match['homeName'])
				translated_away_name = StatAPIHandler.translate_team_name(match['awayName'])
				match['homeName'], match['awayName'] = translated_home_name, translated_away_name

				#TODO format data to D:M:Y H:M:S

				# adding match score which is not included visibly in response data
				home_score = match["team_home_90min_goals"] + match["team_home_ET_goals"]
				away_score = match["team_away_90min_goals"] + match["team_away_ET_goals"]
				match['score'] = f'{home_score}-{away_score}'

			if querystring['page'] == '1':
				util.insure_dir_exists(os.path.join('Database', 'Calendars'))
				# if not os.path.isdir(os.path.join(os.getcwd(), 'Calendars')):
				# 	os.mkdir('Calendars')
				calendar_path = os.path.join('Database','Calendars', calendar_filename)
				r['season id'] = season_id # adding season id to dict to tell one calendar from another
				with open(calendar_path, 'w', encoding='utf-8') as file:
					json.dump(r, file, indent=4, ensure_ascii=False)
			else:
				with open(calendar_path, 'r', encoding='utf-8') as file:
					data_to_dump = json.load(file)
				for match in r['data']:
					data_to_dump['data'].append(match)
				with open(calendar_path, 'w', encoding='utf-8') as file:
					json.dump(data_to_dump, file, indent=4, ensure_ascii=False)

			if page_data['hasNextPage']:
				querystring['page'] = str(int(querystring['page']) + 1)
			else:
				response_has_next_page = False

			logger.info(f'Calendar {calendar_path} successfully created')

	def get_match_data_by_id(self, match_id:int) -> Union[dict, None]:
		'''Gets info on a match with match_id'''

		# based on API's fixtureById method
		if not isinstance(match_id, int):
			logger.error(f'Match id must be an integer. Arg passed: {match_id}')
			return None

		endpoint = '/v2/fixtures/:id'
		url = urljoin(STAT_API_URL, endpoint.replace(':id', str(match_id)))
		querystring = {'events': True}
		r = requests.get(url, headers=HEADERS, params=querystring)

		if not r.status_code == requests.codes.ok:
			logger.error(f'Bad request:{r.json()["message"]} Arg passed: {match_id}')
			return None

		r = r.json()['data'][0]

		date_time_str = r['date']
		date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
		formatted_time = date_time_obj.strftime('%d.%m.%Y %H:%M:%S')
		r['date'] = formatted_time

		translated_home_name = StatAPIHandler.translate_team_name(r['homeName'])
		translated_away_name = StatAPIHandler.translate_team_name(r['awayName'])
		r['homeName'], r['awayName'] = translated_home_name, translated_away_name

		for e in r['events']:
			translated_team_name = StatAPIHandler.translate_team_name(e['teamName'])
			e['teamName'] = translated_team_name

		return r

	@staticmethod
	def translate_team_name(eng_name):
		return TEAMNAME_TRANSLATION[eng_name] if eng_name in TEAMNAME_TRANSLATION else eng_name


# for debug purposes
#sah = StatAPIHandler()

#country_id = sah.get_country_id_by_name()
#print(country_id)
#country_id = 71

#league_id = sah.get_league_id_by_country_id(country_id)
#print(league_id)
#league_id = 422

#season_id = sah.get_current_season_id_by_league_id(league_id)
#print(season_id)
#season_id = 4208
#sah.get_season_calendar(season_id)

# desired_match_id = 206995
# m = sah.get_match_data_by_id(desired_match_id)
# print(m)
