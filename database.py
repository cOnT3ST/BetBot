import os
import logging
import json
import time
from typing import Union
import util
import datetime
from config import PREFERRED_TIME_FORMAT
from stat_api_handler import StatAPIHandler

util.insure_dir_exists('Logs')
log_file = os.path.join('Logs', f'{os.path.basename(__file__)}.log')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter(fmt='%(levelname)s: %(asctime)s: %(funcName)s: %(message)s',
								  datefmt='%d.%m.%Y %H:%M:%S %p'
								  )
log_file_handler = logging.FileHandler(log_file)
logger.addHandler(log_file_handler)
log_file_handler.setFormatter(log_formatter)

class Database:
	calendar_db_dir = os.path.join('Database','Calendars')
	def __init__(self):
		self.content = {}
		self.matches = []
		self.calendar_name = ''

	def read_calendar(self, season_id: int) -> Union[dict, None]:
		'''Reads file and puts it into self.content'''

		db_filename = f'calendar season id_{season_id}.txt'
		db_path = os.path.join(Database.calendar_db_dir, db_filename)
		self.calendar_name = db_path

		if db_filename not in db_path:
			logger.error('Database doesn\'t exist in provided path')
			return None

		with open(db_path, 'r', encoding='utf-8') as f:
			self.content = json.load(f)
			self.matches = self.content['data']

	def count_max_rounds(self) -> int:
		'''Returns max rounds in a competition'''
		return max([m['round'] for m in self.matches])

	def read_season_start_date(self) -> str:
		'''Returns season start date read from a calendar'''
		return self.matches[0]['date']

	def read_season_finish_date(self) -> str:
		'''Returns season finish date read from a calendar'''
		return self.matches[-1]['date']

	def read_round_dates(self) -> dict:
		'''Returns all rounds first and last match dates'''
		#TODO need to collect all starts as well not only finish dates
		first_match = self.matches[0]
		round_dates = {first_match['round']: [first_match['date'], first_match['date']]}

		for m in self.matches:
			if m['round'] > max(round_dates):
				round_dates[m['round']] = [m['date'],m['date']]
				continue
			curr_match_date = StatAPIHandler.format_time(m['date'])
			curr_round_date = StatAPIHandler.format_time(round_dates[max(round_dates)][0])
			if curr_match_date > curr_round_date:
				round_dates[m['round']][1] = m['date']

		return round_dates

	def update_match_data(self, match_data: dict):
		'''Updates calendar file by given match data'''
		if not match_data:
			logger.error('None as an argument')
			return

		for m in self.matches:
			if m['id'] == match_data['id']:
				match_index = self.matches.index(m)
				self.matches[match_index] = match_data

				with open(self.calendar_name, 'r', encoding='utf-8') as file:
					data_read = json.load(file)
				data_read['data'] = self.matches

				with open(self.calendar_name, 'w', encoding='utf-8') as file:
					json.dump(data_read, file, indent=4, ensure_ascii=False)

				logger.info(f'Match data updated! Match id: {match_data["id"]}')
				return

		logger.error('Failed to found given match in db')
		return

	def read_next_round_data(self, round: int) -> list:
		'''Returns a list of matches in a given round'''
		#TODO make controller know which round it is now
		#TODO how to count tournament's max round in controller?

		res =  [m for m in self.matches if m['round'] == round]
		logger.info('Round {round} data successfully read')
		return res

	def read_team_previous_matches(self, team_id:int, n:int, current_round:int) -> list:
		'''Returns a list of n previous matches of a team_id'''
		#TODO can return empty list in case current round 1
		if current_round - n > 0:
			rounds_needed = [r for r in range(current_round - n, current_round)]
		else:
			rounds_needed = [r for r in range(1, current_round)]

		res = []
		for m in self.matches:
			if m['round'] in rounds_needed:
				if team_id in (m['idHome'], m['idAway']):
					res.append(m)
			elif m['round'] > current_round:
				break

		logger.info(f'Team {team_id} previous matches read successfully')
		return res

	def read_team_previous_results(self, prev_matches: list) -> list:
		'''Returns a list of results from given previous matches'''
		res = []
		for m in prev_matches:
			round = m['round']
			teams = f'{m["homeName"]} - {m["awayName"]}'
			score = m['score']
			res.append({'round': round, 'teams': teams, 'score': score})
		return res

	def read_match_data(self, match_id: int) -> Union[dict, None]:
		'''Returns data on match_id'''
		for m in self.matches:
			if m['id'] == match_id:
				logger.info(f'Data on {match_id} successfully read')
				return m
		return

	def read_match_scorers(self, match_data:dict) -> Union[list, None]:
		'''Returns a list of scores from a given match data'''
		events = match_data['events']
		scorers = []
		for e in events:
			if e['type'] in ('goal', 'pen_scored', 'own_goal'):
				time = e['elapsed'] + e['elapsedPlus'] if e['elapsedPlus'] else e['elapsed']
				player = e['player1Name']
				if e['type'] == 'pen_scored':
					comm = 'pen'
				elif e['type'] == 'own_goal':
					comm = 'og'
				scorers.append((time, player) if e['type'] == 'goal' else (time, player, comm))
				scorers = sorted(scorers, key = lambda score: score[0])
		return scorers

	def find_corrupt_goal_data(self):
		round = 1
		print(f'{round} тур')
		for i, m in enumerate(db.matches[:60]):
			if m['round'] > round:
				round = m['round']
				print(f'{round} тур')
			md = db.read_match_data(m['id'])
			gs = db.read_match_scorers(md)

			score = m['score']

			total_goals = sum([int(i) for i in score.split('-')])
			if total_goals != len(gs):
				print(f"{m['id']}>>>>>>>{i+1}. {m['homeName']}-{m['awayName']}, {score}, {total_goals}, {gs}")
			else:
				print(f"{i+1}. {m['homeName']}-{m['awayName']}, {score}, {total_goals}, {gs}")

# db = Database()
# db.read_calendar(4208)


# sd = db.read_season_start_date()
# fd = db.read_season_finish_date()
# print(sd)
# print(fd)

# ss = db.read_season_start_date()

# pm = db.read_team_previous_matches(1768, 3, 3)
# pr = db.read_team_previous_results(pm)

# db.read_calendar(season_id)
# print(db.content)
# print(type(db.content))

