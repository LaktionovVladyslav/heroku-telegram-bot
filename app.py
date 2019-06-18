import os
import re
import math

from flask import Flask, request

import telebot

from connector import User, session
from utils import send_game

TOKEN = "844180371:AAGzN2Ls-3tuseaN9h_R22l6FAL8ZqPav2I"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

regex = re.compile(
    r'^https://www\.hltv\.org/matches(?:/?|[/?]\S+)$', re.IGNORECASE)


@bot.message_handler(regexp=r'^https://www\.hltv\.org/matches(?:/?|[/?]\S+)$')
def echo_message(message):
    text = message.text
    text, score = send_game(link_to_match=text)
    user_id = message.chat.id
    user = session.query(User).filter_by(user_id=user_id).all()
    if score > 1.7 and bool(len(user)):
        user[0].counts += 1
    elif not bool(len(user)):
        user = User(user_id=user_id)
        session.add(user)
    session.commit()
    bot.reply_to(message, text)
    # if re.match(regex, text):
    #
    # else:
    #     bot.reply_to(message, "Введите ссылку на матч !\nhttps://www.hltv.org/matches")


@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    user = session.query(User).filter_by(user_id=message.chat.id).all()
    if not bool(len(user)):
        user = User(user_id=message.chat.id)
        session.add(user)
        session.commit()
    bot.reply_to(message=message, text='Весь анализ делает бот и выдает оценку каждой команды по 20-ти балльной '
                                       'шкале. Чем больше разница, тем больше шанс захода прогноза. У бота есть два '
                                       'исхода:\n1) В проходе уверен на 90%\n2) Возможны трудности с проходом.\nВ '
                                       'первом случае можно ставить до 20-25% банка.\nВо втором случае, '
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
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
