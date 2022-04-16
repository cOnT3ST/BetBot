import logging
import os
import json
import config
from stat_api_handler import StatAPIHandler
from database import Database
import util
from typing import Union

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

class Controller:
	seasons_db_dir = os.path.join('Database','Seasons')
	seasons_db_filename = 'seasons.txt'
	seasons_db_path = os.path.join(seasons_db_dir, seasons_db_filename)

	def __init__(self):
		self.sah = StatAPIHandler()
		self.db = Database()
		self.seasons = []

	def backup_seasons_db(self):
		if self.seasons == []:
			logger.error('Nothing to dump')
			return

		util.insure_file_exists(Controller.seasons_db_dir, Controller.seasons_db_filename)

		with open(Controller.seasons_db_path, 'w', encoding='utf-8') as file:
			json.dump(self.seasons, file, indent=4, ensure_ascii=False)
			logger.info('Seasons db file dumped')

	def read_seasons_db(self):
		if not os.path.exists(self.seasons_db_path):
			logger.error('No file found to read from')
			return

		with open(Controller.seasons_db_path, 'r', encoding='utf-8') as file:
			self.seasons = json.load(file)
			self.season = self.seasons[-1]
		logger.info('Seasons file read succesfully')

	def create_new_season(self, season_id):
		self.season = {}
		self.season['id'] = len(self.seasons) if not self.seasons == [] else 0
		self.season['country'] = config.COUNTRY_NAME
		self.season['league'] = config.TOURNAMENT_NAME
		#self.season['country_id'] = self.sah.get_country_id_by_name()
		self.season['country_id'] = 71
		#self.season['league_id'] = self.sah.get_league_id_by_country_id(self.season['country_id'])
		self.season['league_id'] = 422
		#self.season['season_id'] = self.sah.get_current_season_id_by_league_id(self.season['league_id'])
		#self.season['season_id'] = 4208
		self.season['season_id'] = season_id
		self.db.read_calendar(self.season['season_id'])
		self.season['calendar'] = self.db.calendar_name
		#self.season['db'] = self.db.content
		self.seasons.append(self.season)

	def get_match_data(self, match_id: int) -> Union[dict, None]:
		'''Makes sah download data by given match id'''
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
		'''Makes db dump data on a match by given match data'''
		if match_data:
			self.db.update_match_data(match_data)
			logger.info(f'Match {match_data["id"]} updated')

	def update_match_data(self, match_id: int):
		updated_match_data = self.get_match_data(match_id)
		if not updated_match_data:
			logger.error(f'Failed to update match as None was given')
			return

		self.update_match_data_in_db(updated_match_data)
		logger.info(f'Data on match {match_id} downloaded')

c = Controller()
c.create_new_season(4208)
#res = c.get_match_data(207048)
c.update_match_data(207048)

