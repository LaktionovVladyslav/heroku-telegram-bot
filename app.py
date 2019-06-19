import os
import re
import math

from flask import Flask, request

import telebot

from connector import User, session
from utils import send_game

TOKEN = "794766889:AAFvOD3zOdXi-OIYCN0cEq2fm06iZFm13jo"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

regex = re.compile(
    r'^https://www\.hltv\.org/matches(?:/?|[/?]\S+)$', re.IGNORECASE)


def sign_up(user_id):
    user = User(user_id=user_id)
    session.add(user)
    session.commit()


def log_in(user_id):
    user = session.query(User).get(user_id)
    if not user:
        sign_up(user_id)
    return user


def get_user_info(user_id):
    user = session.query(User).get(user_id)
    user_id = user.user_id
    counts = user.counts
    max_count = user.max_count
    daily_limit = max_count - counts
    return dict(user_id=user_id, counts=counts, max_count=max_count, daily_limit=daily_limit)


def add_count(user_id):
    user = session.query(User).get(user_id)
    user.counts += 1
    session.commit()


@bot.message_handler(regexp=r'^https://www\.hltv\.org/matches(?:/?|[/?]\S+)$')
def echo_message(message):
    text = message.text
    text, score = send_game(link_to_match=text)
    user = log_in(user_id=message.chat.id)
    user_info = get_user_info(user_id=user.id)
    text += f"За сегодня осталось {user_info.get('daily_limit')} попыток\nИспользованно {user_info.get('counts')}\n " \
        f"Лимит на день {user_info.get('max_count')} "
    bot.reply_to(message, text)


@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    user = log_in(user_id=message.chat.id)
    bot.reply_to(message=message, text='Здраствуйте!Весь анализ делает бот и выдает оценку каждой команды по 20-ти '
                                       'балльной шкале. Чем больше разница, тем больше шанс захода прогноза. У бота '
                                       'есть два исхода:\n1) В проходе уверен на 90%\n2) Возможны трудности с '
                                       'проходом.\nВ первом случае можно ставить до 20-25% банка.\nВо втором случае, '
                                       'лучше поставить сумму для округления своего баланса. Например если у вас 270 '
                                       'грн на балансе, то ставьте 20.')


@bot.message_handler(content_types=['text'])
def handle_docs_audio(message):
    bot.reply_to(message, "Введите ссылку на матч !\nhttps://www.hltv.org/matches")


@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "Hello from Heroku!", 200


@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://robobetsbot.herokuapp.com/' + TOKEN)
    return "Hello from Heroku!", 200


if __name__ == "__main__":
    bot.polling()
    # app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

