import os
import logging
import json
import pdb
from typing import Union
import util

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
# season_id = 4208
# db = Database()
# db.read_calendar(season_id)
# print(db.content)
# print(type(db.content))

