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


@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    text = message.text
    if re.match(regex, text):
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
    else:
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
