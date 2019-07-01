import os
import re
import connector
import config
import telebot

from flask import Flask, request
from telebot.apihelper import ApiException
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

from utils import send_game

if os.environ.get('env') == "prod":
    config = config.ProductionConfig
    TOKEN = config.TOKEN
    bot = telebot.TeleBot(TOKEN)
else:  # os.environ.get('env') == "dev"
    config = config.DevelopmentConfig
    TOKEN = config.TOKEN
    bot = telebot.TeleBot(TOKEN)

if os.environ.get('env') == "prod":
    app = Flask(__name__)


    @app.route('/' + TOKEN, methods=['POST'])
    def get_message():
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "Hello from Heroku!", 200

inline_key_board = InlineKeyboardMarkup()
get_ref_link_button = InlineKeyboardButton("Получить ссылку для приглашения друзей", callback_data='get_link')
inline_key_board.row(get_ref_link_button)


def sign_up(user):
    user = connector.User(user)
    return user


def log_in(user):
    print(user.__dict__)
    new_user = connector.session.query(connector.User).get(user.id)
    if not user:
        return sign_up(user)
    return new_user


def get_user_info(user_id):
    user = connector.session.query(connector.User).get(user_id)
    return user


@bot.message_handler(regexp=r'^https://www\.hltv\.org/matches(?:/?|[/?]\S+)$')
def echo_message(message):
    user = log_in(user=message.from_user)
    if user.check():
        text = message.text
        text, score = send_game(link_to_match=text)
        counts = user.add_count()
        text += "\nНа сегодня осталось {daily_limit} попыток\nИспользованно {counts}\nЛимит на день {max_count}".format(
            daily_limit=user.limit - counts,
            counts=counts,
            max_count=user.limit
        )
        user.rem_count()
        bot.reply_to(message, text)
    elif user.check() is None:
        text = 'Чтобы увеличить количество попыток, пригласите друзей'
        bot.reply_to(message, text=text, reply_markup=inline_key_board)


@bot.message_handler(commands=['start'])
def handle_start_help(message):
    user = log_in(user=message.from_user)
    menu_items = ['Инструкция', 'Баланс', 'Реф. система', 'Получить прогноз']
    ref_user_id = message.text[7:]
    if not user:
        user = connector.User(message.from_user)
        if re.match(pattern=r'\d{9}', string=ref_user_id):
            ref_user = get_user_info(user_id=ref_user_id)
            bot.send_message(chat_id=ref_user_id, text='Ваш друг перешел по вашей ссылке')
            ref_user.add_ref_count()
            ref_user = get_user_info(user_id=ref_user_id)
            text = "Ваш баланс: {daily_limit} прогноз(ов)".format(
                daily_limit=ref_user.limit - ref_user.counts,
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
    user = log_in(user=message.from_user)
    text = "Ваш баланс: {daily_limit} прогноз(ов)".format(
        daily_limit=user.limit - user.counts,
    )
    bot.reply_to(message, text=text, reply_markup=inline_key_board)


@bot.callback_query_handler(func=lambda call: call.data == 'get_link')
def command_click_inline(call):
    text = config.LINK_TO_BOT % call.from_user.id
    bot.send_message(call.from_user.id, text=text)


@bot.message_handler(func=lambda message: message.text == 'Получить прогноз')
def button_handler(message):
    user = log_in(user=message.from_user)
    text = "Введите ссылку на матч !\nhttps://www.hltv.org/matches"
    bot.reply_to(message, text=text)


@bot.message_handler(func=lambda message: message.text == 'Реф. система')
def button_handler(message):
    user = log_in(user=message.from_user)
    text = 'Каждый день вы получаете 1 бесплатный прогноз, которым можете воспользоваться в течений одного ' \
           'дня.\nЗа каждого приглашенного пользователя вы получаете 1 прогноз. '
    text += "\nВаш баланс: {daily_limit} прогноз(ов)".format(
        daily_limit=user.limit - user.counts,
    )
    bot.reply_to(message, text=text, reply_markup=inline_key_board)


@bot.callback_query_handler(func=lambda call: call.data.startswith('get_game_'))
def command_click_inline(call):
    game_id = call.data[9:]
    link_to_match = connector.session.query(connector.Maths).filter_by(math_id=game_id).first().link
    user = log_in(user=call.from_user)
    if user.check():
        text, score = send_game(link_to_match=link_to_match)
        counts = user.add_count()
        text += "\nНа сегодня осталось {daily_limit} попыток\nИспользованно {counts}\nЛимит на день {max_count}".format(
            daily_limit=user.limit - counts,
            counts=counts,
            max_count=user.limit
        )
        user.rem_count()
        bot.send_message(call.from_user.id, text)
    elif user.check() is None:
        text = 'Чтобы увеличить количество попыток, пригласите друзей'
        bot.reply_to(call.from_user.id, text=text, reply_markup=inline_key_board)


if __name__ == "__main__":
    if os.environ.get('env') == "prod":
        app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
        bot.set_webhook(url='https://robobetsbot.herokuapp.com/' + TOKEN)
    else:
        bot.remove_webhook()
        bot.polling()
