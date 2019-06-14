import os
import re

from flask import Flask, request

import telebot

from connector import User, session
from utils import ChanelAdmin

TOKEN = "844180371:AAGzN2Ls-3tuseaN9h_R22l6FAL8ZqPav2I"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

regex = re.compile(
    r'^https://www\.hltv\.org/matches(?:/?|[/?]\S+)$', re.IGNORECASE)
admin = ChanelAdmin()


@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    text = message.text
    if re.match(regex, text):
        text = admin.send_game(link_to_match=text)
        user_id = message.chat.id
        user = session.query(User).filter_by(user_id=user_id).all()
        session.commit()
        if bool(len(user)):
            user[0].counts += 1
        else:
            user = User(user_id=user_id)
            session.add(user)
        session.commit()
        bot.reply_to(message, text)
    else:
        pass


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
