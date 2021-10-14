import os
from WorkWithDB import WWDB
import telebot
from telebot import types
from prettytable import PrettyTable
from math import ceil
from telegram_bot_pagination import InlineKeyboardPaginator
from datetime import datetime


def main():
    TOKEN = os.environ.get('KursTGBot')
    bot = telebot.TeleBot(TOKEN)
    DBWork = WWDB()

    users_data = dict()
    tables = ('Publishers', 'Developers', 'Games', 'Keys', 'Orders', 'Users')
    page_size = 5

    tables_output_data_for_admins = {
        'Publishers': ('publishers', 'id, name, country', 'id', {}),
        'Developers': ('developers', 'id, name, country', 'id', {}),
        'Games': ('games', 'id, name, publisher, developer, genre', 'id',
                  {'publisher': ('publishers', 'id', 'name'), 'developer': ('developers', 'id', 'name')}),
        'Keys': ('keys', 'key, game, platform, price', 'true', {'game': ('games', 'id', 'name')}),
        'Orders': ('orders', 'date, key, id, user_id', 'id', {'user_id': ('users', 'id', 'name')}),
        'Users': ('users', 'id, name, is_admin', 'id', {})
    }

    tables_output_data_for_users = {
        'Publishers': ('publishers', 'name, country', 'id', {}),
        'Developers': ('developers', 'name, country', 'id', {}),
        'Games': ('games', 'name, publisher, genre', 'id',
                  {'publisher': ('publishers', 'id', 'name')}),
        'Orders': ('orders', 'date, key', 'id', {})
    }

    ##########################
    # -------Keyboards-------#
    ##########################

    start_KB = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    start_btn = types.KeyboardButton('/start')
    start_KB.add(start_btn)

    register_sign_in_inline_KB = types.InlineKeyboardMarkup()
    registe_inline_btn = types.InlineKeyboardButton('Регистрация', callback_data="register")
    gign_in_inline_btn = types.InlineKeyboardButton('Вход', callback_data="signin")
    register_sign_in_inline_KB.add(registe_inline_btn, gign_in_inline_btn)

    exit_KB = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    exit_btn = types.KeyboardButton('/exit')
    exit_KB.add(exit_btn)

    admin_tables_KB = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    admin_btn_pub = types.KeyboardButton('Publishers')
    admin_btn_dev = types.KeyboardButton('Developers')
    admin_btn_games = types.KeyboardButton('Games')
    admin_btn_keys = types.KeyboardButton('Keys')
    admin_btn_orders = types.KeyboardButton('Orders')
    admin_btn_users = types.KeyboardButton('Users')
    admin_tables_KB.add(admin_btn_pub, admin_btn_dev, admin_btn_games, admin_btn_keys, admin_btn_orders,
                        admin_btn_users)

    user_tables_KB = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    user_btn_pub = types.KeyboardButton('Publishers')
    user_btn_dev = types.KeyboardButton('Developers')
    user_btn_games = types.KeyboardButton('Games')
    user_btn_orders = types.KeyboardButton('Orders')
    user_tables_KB.add(user_btn_pub, user_btn_dev, user_btn_games, user_btn_orders)

    def tables_paginator(pages, page, table):
        table = table.capitalize()
        paginator = InlineKeyboardPaginator(
            pages,
            current_page=page,
            data_pattern=f'table#{table}#' + '{page}'
        )
        return paginator

    ##########################
    # ------Helps Funks------#
    ##########################

    def exit_check(funk):
        def wrapped(message):
            if (message.text == '/exit'):
                bot.send_message(message.chat.id, "Операция прервана", reply_markup=start_KB)
                raise Exception('Quit from function, all is OK')
            funk(message)

        return wrapped

    def is_admin(message):
        try:
            admin_check = users_data[message.from_user.id]['is_admin']
        except KeyError:
            bot.send_message(message.chat.id, "Пожалуйста зарагестрируйсесть или войдите",
                             reply_markup=register_sign_in_inline_KB)
            raise Exception("This user didn't signed in")
        else:
            return admin_check

    def for_admin(funk):
        def wrapped(message):
            if (users_data[message.from_user.id]['is_admin']):
                funk(message)
            else:
                bot.send_message(message.chat.id, "У вас нет доступа для такого:(\nПопробуйте другой аккаунт")
                raise Exception('This command not for common users')
        return wrapped

    ##########################
    # -------Commands--------#
    ##########################

    @bot.message_handler(commands=['start'])
    def start(message):
        bot.send_message(message.chat.id, "Привет, для регистрации или входа нажмите на кнопку",
                         reply_markup=register_sign_in_inline_KB)

    @bot.message_handler(commands=['help'])
    def help_message(message):
        bot.send_message(message.chat.id, "Для начала работы нажмите на /start и следуйте указаниям")

    # ветка регистрации
    @bot.callback_query_handler(func=lambda call: call.data == 'register')
    def start_register(call):
        register(call.message)

    @exit_check
    def register(message):
        bot.send_message(message.chat.id, "Введите лоигн", reply_markup=exit_KB)
        bot.register_next_step_handler(message, get_register_login)

    @exit_check
    def get_register_login(message):
        global login
        login = str(message.text)
        try:
            DBWork.select_value("users", 'id', key="name", key_value=login)
        except:
            bot.send_message(message.chat.id, "Придумайте пароль")
            bot.register_next_step_handler(message, get_register_password)
        else:
            bot.send_message(message.chat.id, "Такой логин уже существует, выберете другой")
            bot.register_next_step_handler(message, get_register_login)

    @exit_check
    def get_register_password(message):
        global password
        password = str(message.text)
        try:
            register_data = (login, password)
            DBWork.insert("users", 'name, password', register_data)
        except:
            bot.send_message(message.chat.id, "Что-то пошло не так. Приносим извинения за неполадки")
        else:
            users_data[message.from_user.id] = {'is_admin': DBWork.select_value('users', 'is_admin', 'name', login),
                                                'id': DBWork.select_value('users', 'id', 'name', login)}
            bot.send_message(message.chat.id, "Вы успешно зарегестрированы")
            output_table_KB(message)

    # ветка входа
    @bot.callback_query_handler(func=lambda call: call.data == 'signin')
    def start_signin(call):
        signin(call.message)

    @exit_check
    def signin(message):
        bot.send_message(message.chat.id, "Введите лоигн", reply_markup=exit_KB)
        bot.register_next_step_handler(message, get_signin_login)

    @exit_check
    def get_signin_login(message):
        global login
        login = str(message.text)
        try:
            DBWork.select_value("users", 'id', key="name", key_value=login)
        except:
            bot.send_message(message.chat.id,
                             "Такого лоигна не существует, попробуйте ввести другой или зарегестрироваться")
            bot.register_next_step_handler(message, get_signin_login)
        else:
            bot.send_message(message.chat.id, "Введите пароль")
            bot.register_next_step_handler(message, get_signin_password)

    @exit_check
    def get_signin_password(message):
        global password
        password = str(message.text)
        if (DBWork.select_value('users', 'password', 'name', login) == password):
            users_data[message.from_user.id] = {'is_admin': DBWork.select_value('users', 'is_admin', 'name', login),
                                                'id': DBWork.select_value('users', 'id', 'name', login)}
            bot.send_message(message.chat.id, 'Вход прошёл успешно')
            output_table_KB(message)
        else:
            bot.send_message(message.chat.id, "Пароль неверный, попробуйте снова")
            bot.register_next_step_handler(message, get_signin_password)

    # Вывод доступных таблиц
    @bot.message_handler(commands=['tables'])
    def output_table_KB(message):
        if is_admin(message):
            bot.send_message(message.chat.id, 'Выберете таблицу', reply_markup=admin_tables_KB)
        else:
            bot.send_message(message.chat.id, 'Выберете таблицу', reply_markup=user_tables_KB)

    @bot.message_handler(func=lambda message: message.text in tables)
    def send_table_to_user(message, page=1):
        # Получение необходимых данных для обращения  БД
        if is_admin(message):
            table, columns, order_by, forgein_keys = tables_output_data_for_admins[message.text]
        else:
            table, columns, order_by, forgein_keys = tables_output_data_for_users[message.text]

        # Заголовок таблицы
        head = columns.split(', ')
        if table == 'orders':
            head += ['game', 'platform']

        # Получение всех данных данных из бд для тела таблицы
        if ~is_admin(message) and table == 'orders':
            body = DBWork.select_many_rows(table, columns, key='user_id',
                                           key_value=users_data[message.from_user.id]['id'],
                                           order_by=order_by)
            empty_body_message = 'У вас нет заказов, нужно это исправить'
        else:
            body = DBWork.select_many_rows(table, columns, order_by=order_by)
            empty_body_message = 'Данных нет на сервере просим вас подождать до обновления сервера'

        # Проверка на существование данных
        if len(body) == 0:
            bot.send_message(message.chat.id, empty_body_message)
            raise Exception('Table "' + table + '" is empty or dont have needed entries')

        # Обработка данных из тела таблицы
        for row in body:
            if table == 'orders':
                date = row[0]
                date_string = datetime(date.year, date.month, date.day, date.hour, date.minute)
                row[0] = date_string.strftime('%d.%m.%Y')
                platform = DBWork.select_value('keys', 'platform', 'key', row[1])
                game = DBWork.select_value('games', 'name', 'id',
                                           DBWork.select_value('keys', 'game', 'key', row[1]))
                row += [game, platform]
            for col in forgein_keys:
                colNum = head.index(col)
                new_value = DBWork.select_value(forgein_keys[col][0], forgein_keys[col][2], forgein_keys[col][1],
                                                row[colNum])
                row[colNum] = new_value

        # Рассчёт страниц для пагинатора
        pages = ceil(len(body) / page_size)
        if page > pages:
            page = pages

        # Добавление данних из нужного промежутка на страницу
        tab = PrettyTable(head)
        tab.add_rows(body[page_size * (page - 1):page_size * page])
        res = '<pre>' + tab.get_string() + '</pre>'

        # Отправка сообщения
        bot.send_message(message.chat.id, res,
                         reply_markup=tables_paginator(pages, page, table).markup, parse_mode='HTML')

        # Обработчик обратных вызовов от пагинатора
        @bot.callback_query_handler(func=lambda call: call.data.split('#')[0] == 'table')
        def tables_page_callback(call):
            call.message.from_user = call.from_user
            call.message.text = call.data.split('#')[1]
            page = int(call.data.split('#')[2])
            bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )
            send_table_to_user(call.message, page)

    # ---Raw text handler----#
    @bot.message_handler(content_types='text')
    def raw_text_message(message):
        bot.send_message(message.chat.id, "Я не знаю такого, простите")


    bot.infinity_polling()


if __name__ == '__main__':
    main()
