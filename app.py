import re
from flask import Flask, request

import telebot

from connector import User, session
from utils import send_game

TOKEN = "794766889:AAFvOD3zOdXi-OIYCN0cEq2fm06iZFm13jo"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

regex = re.compile(
    r'^https://www\.hltv\.org/matches(?:/?|[/?]\S+)$', re.IGNORECASE)

pattern_chat_id = r'\d{9}'


def sign_up(user_id):
    user = User(user_id=user_id)
    session.add(user)
    session.commit()
    return user


def log_in(user_id):
    user = session.query(User).get(user_id)
    if not user:
        return sign_up(user_id)
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


def add_max_count(user_id):
    user = session.query(User).get(user_id)
    user.max_count += 1
    session.commit()


def check(user_id):
    user = session.query(User).get(user_id)
    return bool(user.max_count - user.counts)


def add_ref(user_id, ref_user_id):
    if not session.query(User).get(user_id):
        add_max_count(user_id=ref_user_id)
        bot.send_message(chat_id=ref_user_id, text='Пользователь перешел по вашей ссылке')
    else:
        bot.send_message(chat_id=ref_user_id, text='Пользователь уже использует')


@bot.message_handler(regexp=r'^https://www\.hltv\.org/matches(?:/?|[/?]\S+)$')
def echo_message(message):
    if check(message.chat.id):
        user = log_in(user_id=message.chat.id)
        text = message.text
        text, score = send_game(link_to_match=text)
        add_count(user.user_id)
        user_info = get_user_info(user.user_id)
        text += "\nНа сегодня осталось {daily_limit} попыток\nИспользованно {counts}\n" \
                "Лимит на день {max_count}".format(
            **user_info
        )
        bot.reply_to(message, text)
    else:
        text = 'Чтобы увеличить количество ' \
               'попыток, пригласите друзей'
        text += 'https://t.me/devrobbot?start=%s' % message.chat.id
        bot.reply_to(message, text=text)


@bot.message_handler(commands=['start'])
def handle_start_help(message):
    ref_user_id = message.text[7:]
    if re.match(pattern=pattern_chat_id, string=ref_user_id):
        add_ref(user_id=message.chat.id, ref_user_id=ref_user_id)
    user = log_in(user_id=message.chat.id)
    user_info = get_user_info(user.user_id)
    text = 'Здраствуйте!Весь анализ делает бот и выдает оценку каждой команды по 20-ти балльной шкале. Чем больше разница, тем больше шанс захода прогноза. У бота есть два исхода:\n1) В проходе уверен на 90%\n2) Возможны трудности с проходом.\nВ первом случае можно ставить до 20-25% банка.\nВо втором случае, лучше поставить сумму для округления своего баланса. Например если у вас 270 грн на балансе, то ставьте 20.'
    text += "\nВведите ссылку на матч !\nhttps://www.hltv.org/matches"
    text += f"\nНа сегодня осталось {user_info.get('daily_limit')} попыток\nИспользованно {user_info.get('counts')}\n" \
        f"Лимит на день {user_info.get('max_count')}"
    bot.reply_to(message=message, text=text)


@bot.message_handler(content_types=['text'])
def handle_docs_audio(message):
    bot.reply_to(message, "Введите ссылку на матч !\nhttps://www.hltv.org/matches")


@app.route('/' + TOKEN, methods=['POST'])
def get_message():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "Hello from Heroku!", 200


@app.route("/")
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://robobetsbot.herokuapp.com/' + TOKEN)
    return "Hello from Heroku!", 200


if __name__ == "__main__":
    bot.polling()
