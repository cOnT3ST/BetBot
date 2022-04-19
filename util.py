import os

def insure_dir_exists(dir):
	if not os.path.exists(dir):
		os.mkdir(dir)

def insure_file_exists(dir, file):
	insure_dir_exists(dir)
	if not os.path.isfile(os.path.join(dir, file)):
		with open(os.path.join(dir, file), 'w', encoding='utf-8'):
			pass

		# date_time_str = self.matches[-1]['date']
		# date_time_obj = datetime.datetime.strptime(date_time_str, PREFERRED_TIME_FORMAT)
		# return date_time_obj