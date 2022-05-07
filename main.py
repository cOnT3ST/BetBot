import threading
from controller import Controller

c = Controller()

if "__name__" == '__main__':
	threading.Thread(target=c.exec_schedule()).start()
	threading.Thread(target=c.bot.polling(none_stop=True, interval=0)).start()
