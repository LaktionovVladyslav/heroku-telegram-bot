import os
import re

from telegram.ext import Updater
from utils import ChanelAdmin

TOKEN = "TOKEN"
PORT = int(os.environ.get('PORT', '8443'))
updater = Updater(TOKEN)
dispatcher = updater.dispatcher
regex = re.compile(
    r'^https://'
    r'www\.hltv\.org/matches'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)
admin = ChanelAdmin()


def gender(update, context):
    text = update.message.text
    if re.match(regex, text):
        text = admin.send_game(link_to_match=text)
        update.message.reply_text(text=text)
    else:
        pass


dispatcher.add_handler(gender)
updater.start_webhook(listen="0.0.0.0",
                      port=PORT,
                      url_path=TOKEN)
updater.bot.set_webhook("https://robobetsbot.herokuapp.com/" + TOKEN)
updater.idle()
