import os   # PROD
import re

import telebot
from flask import Flask, request
from telebot.apihelper import ApiException
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

from connector import User, session
from utils import send_game

TOKEN = "844180371:AAGzN2Ls-3tuseaN9h_R22l6FAL8ZqPav2I"  # PROD
# TOKEN = "794766889:AAFvOD3zOdXi-OIYCN0cEq2fm06iZFm13jo"  # DEV
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

regex = re.compile(
    r'^https://www\.hltv\.org/matches(?:/?|[/?]\S+)$', re.IGNORECASE)

pattern_chat_id = r'\d{9}'
menu_items = ['Инструкция', 'Баланс', 'Реф. система', 'Получить прогноз']
# link_to_bot = 'https://t.me/devrobbot?start=%s'   # DEV
link_to_bot = 'https://t.me/RobobetsBot?start=%s'   # PROD
inline_key_board = InlineKeyboardMarkup()
get_ref_link_button = InlineKeyboardButton("Получить ссылку для приглашения друзей", callback_data='get_link')
inline_key_board.row(get_ref_link_button)


def sign_up(user):
    user = User(user)
    return user


def log_in(user_id):
    user = session.query(User).get(user_id)
    if not user:
        return sign_up(user_id)
    return user


def get_user_info(user_id):
    user = session.query(User).get(user_id)
    return user


@bot.message_handler(regexp=r'^https://www\.hltv\.org/matches(?:/?|[/?]\S+)$')
def echo_message(message):
    user = get_user_info(user_id=message.chat.id)
    if user.check():
        text = message.text
        text, score = send_game(link_to_match=text)
        counts = user.add_count()
        text += "\nНа сегодня осталось {daily_limit} попыток\nИспользованно {counts}\nЛимит на день {max_count}".format(
            daily_limit=user.daily_limit,
            counts=counts,
            max_count=user.ref_count + user.daily_limit + user.payed
        )
        bot.reply_to(message, text)
    else:
        text = 'Чтобы увеличить количество попыток, пригласите друзей'
        bot.reply_to(message, text=text, reply_markup=inline_key_board)


@bot.message_handler(commands=['start'])
def handle_start_help(message):
    user = get_user_info(user_id=message.chat.id)
    ref_user_id = message.text[7:]
    if not user:
        user = User(message.from_user)
        if re.match(pattern=pattern_chat_id, string=ref_user_id):
            ref_user = get_user_info(user_id=ref_user_id)
            bot.send_message(chat_id=ref_user_id, text='Ваш друг перешел по вашей ссылке')
            ref_user.add_ref_count()
            ref_user = get_user_info(user_id=ref_user_id)
            text = "\nНа сегодня осталось {daily_limit} попыток\nИспользованно {counts}\nЛимит на день {max_count}".format(
                daily_limit=ref_user.daily_limit,
                counts=ref_user.counts,
                max_count=ref_user.ref_count + ref_user.daily_limit + ref_user.payed
            )
            bot.send_message(chat_id=ref_user_id, text=text)
    else:
        try:
            bot.send_message(chat_id=ref_user_id, text='Пользователь уже использует')
        except ApiException:
            pass
    reply_markup = ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True, row_width=2)
    reply_markup.add(*menu_items)
    text = 'Здраствуйте ' + user.first_name
    bot.reply_to(message=message, text=text, reply_markup=reply_markup)


@app.route('/' + TOKEN, methods=['POST'])
def get_message():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "Hello from Heroku!", 200


@app.route("/")
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://robobetsbot.herokuapp.com/' + TOKEN)
    return "Hello from Heroku!", 200


@bot.message_handler(func=lambda message: message.text == 'Инструкция')
def button_handler(message):
    text = "Весь анализ делает бот и выдает оценку каждой команды по 20-ти балльной шкале. Чем больше " \
           "разница, тем больше шанс захода прогноза. У бота есть два исхода:\n1) В проходе уверен на 90%\n2) " \
           "Возможны трудности с проходом.\nВ первом случае можно ставить до 20-25% банка.\nВо втором случае, " \
           "лучше поставить сумму для округления своего баланса. Например если у вас 270 грн на балансе, то ставьте " \
           "20.\nСКИДЫВАТЬ ССЫЛКУ ТОЛЬКО КОГДА ИЗВЕСТНА КАРТА\nУдачи "
    bot.reply_to(message, text=text)


@bot.message_handler(func=lambda message: message.text == 'Баланс')
def button_handler(message):
    user = get_user_info(user_id=message.chat.id)
    text = "\nНа сегодня осталось {daily_limit} попыток\nИспользованно {counts}\nЛимит на день {max_count}".format(
        daily_limit=user.daily_limit,
        counts=user.counts,
        max_count=user.ref_count + user.daily_limit + user.payed
    )
    bot.reply_to(message, text=text, reply_markup=inline_key_board)


@bot.callback_query_handler(func=lambda call: call.data == 'get_link')
def command_click_inline(call):
    text = link_to_bot % call.from_user.id
    bot.send_message(call.from_user.id, text=text)


@bot.message_handler(func=lambda message: message.text == 'Получить прогноз')
def button_handler(message):
    text = "Введите ссылку на матч !\nhttps://www.hltv.org/matches"
    bot.reply_to(message, text=text)


@bot.message_handler(func=lambda message: message.text == 'Реф. система')
def button_handler(message):
    user = get_user_info(user_id=message.chat.id)
    text = 'Каждый день вы получаете 1 бесплатный прогноз, которым можете воспользоваться в течений одного ' \
           'дня.\nЗа каждого приглашенного пользователя вы получаете 1 прогноз. '
    text += "\nНа сегодня осталось {daily_limit} попыток\nИспользованно {counts}\nЛимит на день {max_count}".format(
        daily_limit=user.daily_limit,
        counts=user.counts,
        max_count=user.ref_count + user.daily_limit + user.payed
    )
    bot.reply_to(message, text=text, reply_markup=inline_key_board)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))  # PROD
    # bot.remove_webhook()
    # bot.polling()  # DEV
