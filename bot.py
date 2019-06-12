from flask import Flask
from flask import render_template, request
import logging
import telegram

HOST = "https://robobetsbot.herokuapp.com/"

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

global bot
bot = telegram.Bot(token='844180371:AAGzN2Ls-3tuseaN9h_R22l6FAL8ZqPav2I')
botName = "RobobetsBot"  # Without @


@app.route("/", methods=["POST", "GET"])
def setWebhook():
    if request.method == "GET":
        logging.info("Hello, Telegram!")
        return "OK, Telegram Bot!"


@app.route("/verify", methods=["POST"])
def verification():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        if update is None:
            return "Show me your TOKEN please!"
        logging.info("Calling {}".format(update.message))
        handle_message(update.message)
        return "ok"


def handle_message(msg):
    text = msg.text
    bot.sendMessage(chat_id=msg.chat.id, text=text)


if __name__ == "__main__":
    s = bot.setWebhook("{}/verify".format(HOST))
    if s:
        logging.info("{} WebHook Setup OK!".format(botName))
    else:
        logging.info("{} WebHook Setup Failed!".format(botName))
    app.run(host="0.0.0.0", debug=True)
