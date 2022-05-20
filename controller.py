import datetime
import logging
import os
import json
import time

import config
import util
from typing import Union
from bot import Bet_bot
import threading
from stat_api_handler import StatAPIHandler
from database import Database


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

# TODO all methods in this file must have type hints -> check for it


class Controller:
	# TODO docstring
	# seasons_db_dir = os.path.join('Database','Seasons')
	# seasons_db_filename = 'seasons.txt'
	# seasons_db_path = os.path.join(seasons_db_dir, seasons_db_filename)

	# TODO when create new season / condition / how

	def __init__(self):
		self.sah = StatAPIHandler()
		with open(Controller.seasons_db_path, 'r', encoding='utf-8') as f:
			season_id = json.load(f)[-1]['season_id'] # Read season_id of a season last written into db
		self.db = Database(season_id = season_id)
		self.bot = Bet_bot(token = config.TELEGRAM_TOKEN, parse_mode=None)
		self.seasons = []
		self.season = Season()

	def read_seasons_db(self):
		'''Reads data stored in database
		'''

		if not os.path.exists(self.seasons_db_path):
			logger.error('No file found to read from')
			return

		with open(Controller.seasons_db_path, 'r', encoding='utf-8') as file:
			self.seasons = json.load(file)
			self.season = self.seasons[-1]
			self.db.read_calendar()
		logger.info('Seasons file read succesfully')

	def backup_seasons_db(self):
		'''Dumps self.seasons into a text file as a database
		'''

		if self.seasons == []:
			logger.error('Nothing to dump')
			return

		util.insure_file_exists(Controller.seasons_db_dir, Controller.seasons_db_filename)

		with open(Controller.seasons_db_path, 'w', encoding='utf-8') as file:
			json.dump(self.seasons, file, indent=4, ensure_ascii=False)
			logger.info('Seasons db file dumped')

	def create_new_season(self):
		# TODO docstring
		# TODO must not have given args. Season id must be gotten from stat api
		self.season = {}
		self.season['id'] = len(self.seasons) if not self.seasons == [] else 0
		self.season['country'] = config.COUNTRY_NAME
		self.season['league'] = config.TOURNAMENT_NAME
		# TODO uncomment and delete debug line
		#self.season['country_id'] = self.sah.get_country_id_by_name()
		self.season['country_id'] = 71
		# TODO uncomment and delete debug line
		#self.season['league_id'] = self.sah.get_league_id_by_country_id(self.season['country_id'])
		self.season['league_id'] = 422
		# TODO uncomment and delete debug line
		#self.season['season_id'] = self.sah.get_current_season_id_by_league_id(self.season['league_id'])
		self.season['season_id'] = 4208
		self.db.read_calendar()
		self.season['calendar'] = self.db.calendar_name
		self.season['max_rounds'] = self.db.count_max_rounds()
		self.season['current_round'] = 1
		self.season['start_date'] = self.db.read_season_start_date()
		self.season['finish_date'] = self.db.read_season_finish_date()
		self.season['round_dates'] = self.db.read_round_dates()
		#self.season['db'] = self.db.content
		self.seasons.append(self.season)

		self.backup_seasons_db()
		self.read_seasons_db()

		logger.info(f'Season id {self.season["season_id"]} successfully created')

	def get_match_data(self, match_id: int) -> Union[dict, None]:
		'''Makes sah download data by given match id
		'''

		if not isinstance(match_id, int):
			logger.error(f'Match id must be integer. Given match id: {match_id}')
			return

		match_data = self.sah.get_match_data_by_id(match_id)
		if match_data:
			logger.info(f'Data on match (id {match_id}) downloaded')
		else:
			logger.error(f'Failed to download data on match (id {match_id})')
		return match_data

	def update_match_data_in_db(self, match_data: dict):
		'''Makes db dump data on a match by given match data
		'''

		if match_data:
			self.db.update_match_data(match_data)
			logger.info(f'Match {match_data["id"]} updated')

	def update_match_data(self, match_id: int):
		'''Downloads data on a match by given match id and updates it in db
		'''

		updated_match_data = self.get_match_data(match_id)
		if not updated_match_data:
			logger.error(f'Failed to update match as None was given')
			return

		self.update_match_data_in_db(updated_match_data)
		logger.info(f'Data on match {match_id} downloaded')

	def update_round_data(self, round: int):
		# TODO is this methods used anywhere???
		# TODO docstring
		match_ids = self.db.read_match_ids_by_round(round)
		for mi in match_ids:
			self.update_match_data(mi)
		logger.info(f'Round data {round} updated successfully')

	def track_match(self, match_id: int):
		''' Keeps track of a match at match day
		This func serves as a target for a thread so that we can track simultaneous matches
		'''

		print(f'Tracking match id {match_id} ...')
		# Updating match time since API only provides start time at the very last moment
		self.update_match_data(match_id)
		match_data = self.db.read_match_data(match_id)
		match_name = f'{match_data["homeName"]} - {match_data["awayName"]}'
		match_start_time_str = match_data["date"].split()[1]
		self.bot.notify_admin(f'Match {match_name} is scheduled for today at {match_start_time_str}')

		match_start_datetime_obj = match_data["date"].strptime(config.PREFERRED_TIME_FORMAT)
		util.wait_until(match_start_datetime_obj)
		self.bot.notify_admin(f'Матч {match_name} начался!')

		match_finish_datetime_obj = match_start_datetime_obj + datetime.timedelta(minutes=config.MATCH_DURATION)
		util.wait_until(match_finish_datetime_obj)

		# getting match results
		self.update_match_data(match_id)
		match_data = self.db.read_match_data(match_id)
		match_score = match_data['score']
		self.bot.notify_users(f'Матч {match_name} завершился!\n'
							  f'Счёт {match_score}')

	def track_schedule(self):
		# TODO docstring

		#self.bot.notify_admin(f'{datetime.datetime.now().strftime(config.PREFERRED_TIME_FORMAT)}: exec_schedule in process ...')
		while True:
			print(f'Start time: {datetime.datetime.now().strftime("%H:%M:%S")}')
			# TODO update schedule daily so that we dont miss postponed matches
			if self.db.today_is_match_day():
				print(f'It\'s match day! Today\'s matches: {self.db.next_day_matches}')
				#util.wait_until(config.MATCHDAY_STATUS_UPDATE_TIME) # Uncomment once this method is gebugged
				now = datetime.datetime.now() # test purpose. Delete
				match_update_time = now + datetime.timedelta(seconds=3) # test purpose. Delete
				print(f'Update start time: {match_update_time.strftime("%H:%M:%S")}')
				print(f'Time to wait until: {match_update_time.strftime("%H:%M")}')
				util.wait_until(match_update_time)
				print(f'Day update time: {datetime.datetime.now().strftime("%H:%M:%S")}')

				for match in self.db.next_day_matches:
					print(self.db.next_day_matches)
					match_id = list(match.keys())[0]
					print(f'Match id: {match_id}')
					threading.Thread(target=self.track_match, args=[match_id]).start()

				# Updating property so that it knows about match_data updates we did in a previous for loop
				self.next_day_matches = self.db.read_next_day_matches()

				self.db.read_season_status()
				if self.db.season_status == 'finished': # Check for condition to break while loop
					break


				# TODO count bets results
				# TODO send users notifications about bet results
				# TODO update leaderboard
				# TODO send users notifications about leaderboard changes
				# TODO If its last match of the round we must also notify all users about round results
				# TODO add postponed matches
				# TODO backup seasons db

			else:
				print('NOT MATCH DAY')
				next_match_datetime_obj = list(self.db.next_day_matches[0].values())[0]
				match_datetime = next_match_datetime_obj.strftime(config.PREFERRED_TIME_FORMAT)
				self.bot.notify_admin(f'Today is {datetime.datetime.today().strftime(config.PREFERRED_TIME_FORMAT)}'
									  f' and it\'s not a match day. Next match day is scheduled for {match_datetime}')

			util.wait_until(config.MATCHDAY_STATUS_UPDATE_TIME) # Wait till next day

		#TODO what to do when championship is over

class Season:
	''' Contains all the info about current season
	'''

	seasons_db_dir = os.path.join('Database','Seasons')
	seasons_db_filename = 'seasons.txt'
	seasons_db_path = os.path.join(seasons_db_dir, seasons_db_filename)


	def __init__(self):


		self.id = len(self.seasons) if not self.seasons == [] else 0
		self.season['id'] = len(self.seasons) if not self.seasons == [] else 0
		self.season['country'] = config.COUNTRY_NAME
		self.season['league'] = config.TOURNAMENT_NAME
		# TODO uncomment and delete debug line
		#self.season['country_id'] = self.sah.get_country_id_by_name()
		self.season['country_id'] = 71
		# TODO uncomment and delete debug line
		#self.season['league_id'] = self.sah.get_league_id_by_country_id(self.season['country_id'])
		self.season['league_id'] = 422
		# TODO uncomment and delete debug line
		#self.season['season_id'] = self.sah.get_current_season_id_by_league_id(self.season['league_id'])
		self.season['season_id'] = 4208
		self.db.read_calendar()
		self.season['calendar'] = self.db.calendar_name
		self.season['max_rounds'] = self.db.count_max_rounds()
		self.season['current_round'] = 1
		self.season['start_date'] = self.db.read_season_start_date()
		self.season['finish_date'] = self.db.read_season_finish_date()
		self.season['round_dates'] = self.db.read_round_dates()
		#self.season['db'] = self.db.content
		self.seasons.append(self.season)

		self.backup_seasons_db()
		self.read_seasons_db()

		logger.info(f'Season id {self.season["season_id"]} successfully created')
