import telebot

bot = None

def send_message(enable, key, id, message):
    global bot
    if enable:
        if bot is None:
            bot = telebot.TeleBot(key)
        bot.send_message(id, message)
