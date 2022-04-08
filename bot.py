import telebot
from config import TELEGRAM_TOKEN

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Howdy, how are you doing?")

@bot.message_handler(func=lambda m: m.text in ('Привет!', 'Как дела?'))
def echo_special(message):
	reply_text = 'Даров!' if message.text == 'Привет!' else 'Да норм. Сам как?'
	bot.reply_to(message, reply_text)

@bot.message_handler(func=lambda m: True)
def echo_all(message):
	bot.reply_to(message, message.text)

bot.polling(none_stop=True, interval=0)