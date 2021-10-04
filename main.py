import os
import psycopg2
import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException
from prettytable import PrettyTable
from math import ceil
from telegram_bot_pagination import InlineKeyboardPaginator
from datetime import datetime


class WWDB():
    def __init__(self):  # метод чтения БД и создания курсора
        self.conn = psycopg2.connect(user='postgres',
                                     password='admin123',
                                     host='localhost',
                                     port='5432',
                                     database='GameShop')
        self.curs = self.conn.cursor()  # курсор

    def select_many_rows(self, table, columns='*', key='true', key_value='true'):
        select_many_rows_command = f"select {columns} from {table} where {key} = '{key_value}'"
        self.curs.execute(select_many_rows_command)
        raw_rows = self.curs.fetchall()
        rows = []
        for row in raw_rows:
            rows.append(list(row))
        return rows

    def select_one_row(self, table, columns='*', key='true', key_value='true'):
        select_one_row_command = f"select {columns} from {table} where {key} = '{key_value}'"
        self.curs.execute(select_one_row_command)
        row = list(self.curs.fetchone())
        return row

    def select_value(self, table, column='id', key='true', key_value='true'):
        select_value_command = f"select {column} from {table} where {key} = '{key_value}'"
        self.curs.execute(select_value_command)
        value = self.curs.fetchone()[0]
        return value

    def insert(self, table, columns, values):
        insert_command_string = f"insert into {table} ({columns}) values (%s{', %s' * (len(values) - 1)})"
        insert_command = self.curs.mogrify(insert_command_string, values)
        try:
            self.curs.execute(insert_command)
            self.conn.commit()
        except:
            self.conn.rollback()


def main():
    TOKEN = os.environ.get('KursTGBot')
    DBWork = WWDB()
    bot = telebot.TeleBot(TOKEN)
    users_data = dict()
    page_size = 9

    ##########################
    # -------Keyboards-------#
    ##########################

    admin_tables_KB = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=3)
    admin_btn_pub = types.KeyboardButton('Publishers')
    admin_btn_dev = types.KeyboardButton('Developers')
    admin_btn_games = types.KeyboardButton('Games')
    admin_btn_keys = types.KeyboardButton('Keys')
    admin_btn_orders = types.KeyboardButton('Orders')
    admin_btn_users = types.KeyboardButton('Users')
    admin_tables_KB.add(admin_btn_pub, admin_btn_dev, admin_btn_games, admin_btn_keys, admin_btn_orders,
                        admin_btn_users)

    user_tables_KB = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2)
    user_btn_pub = types.KeyboardButton('Publishers')
    user_btn_dev = types.KeyboardButton('Developers')
    user_btn_games = types.KeyboardButton('Games')
    user_btn_orders = types.KeyboardButton('Orders')
    user_tables_KB.add(user_btn_pub, user_btn_dev, user_btn_games, user_btn_orders)

    register_sign_in_inline_KB = types.InlineKeyboardMarkup()
    registe_inline_btn = types.InlineKeyboardButton('Регистрация', callback_data="register")
    gign_in_inline_btn = types.InlineKeyboardButton('Вход', callback_data="signin")
    register_sign_in_inline_KB.add(registe_inline_btn, gign_in_inline_btn)

    def tables_paginator(pages, page, table):
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
                bot.send_message(message.chat.id, "Операция прервана")
                raise Exception('Quit from function, all is OK')
            funk(message)

        return wrapped

    def for_admin(funk):
        def wrapped(message):
            if (users_data[message.from_user.id]['is_admin']):
                funk(message)
            else:
                bot.send_message(message.chat.id, "У вас нет доступа для такого:(\nПопробуйте другой аккаунт")
                raise Exception('This command not for common users')

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

    ##########################
    # --Commands For Users---#
    ##########################

    @bot.message_handler(commands=['help'])
    def help_message(message):
        bot.send_message(message.chat.id, "Для начала работы нажмите на /start и следуйте указаниям")

    @bot.message_handler(commands=['start'])
    def start(message):
        bot.send_message(message.chat.id, "Привет, для регистрации или входа нажмите на кнопку",
                         reply_markup=register_sign_in_inline_KB)

    @bot.callback_query_handler(func=lambda call: call.data.split('#')[0] == 'table')
    def tables_page_callback(call):
        table = call.data.split('#')[1]
        page = int(call.data.split('#')[2])
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
        send_table_to_user(call.message, table, page)

    # Цепочка регистрации/входа
    @bot.callback_query_handler(func=lambda call: True)
    def start_callback(call):
        if call.data == 'register':
            register(call.message)
        elif call.data == 'signin':
            signin(call.message)

    # ветка регистрации
    @bot.message_handler(commands=['register'])
    @exit_check
    def register(message):
        bot.send_message(message.chat.id, "Введите лоигн")
        bot.register_next_step_handler(message, get_register_login)

    @exit_check
    def get_register_login(message):
        global login
        login = str(message.text)
        try:
            DBWork.select_value("users", key="name", key_value=login)
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
            users_data[message.from_user.id] = {'is_admin': DBWork.select_value('users', 'admin', 'name', login),
                                                'id': DBWork.select_value('users', 'id', 'name', login)}
            bot.send_message(message.chat.id, "Вы успешно зарегестрированы, выберете таблицу")
            output_table_KB(message)

    # ветка входа
    @bot.message_handler(commands=['signin'])
    @exit_check
    def signin(message):
        bot.send_message(message.chat.id, "Введите лоигн")
        bot.register_next_step_handler(message, get_signin_login)

    @exit_check
    def get_signin_login(message):
        global login
        login = str(message.text)
        try:
            DBWork.select_value("users", key="name", key_value=login)
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
            users_data[message.from_user.id] = {'is_admin': DBWork.select_value('users', 'admin', 'name', login),
                                                'id': DBWork.select_value('users', 'id', 'name', login)}
            bot.send_message(message.chat.id, 'Вход прошёл успешно, выберете таблицу')
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

    def send_table_to_user(message, table_name, page):
        tables_output_templates_for_admins = {
            'publishers': ('publishers', 'id, name, country', {}),
            'developers': ('developers', 'id, name, country', {}),
            'games': ('games', 'id, name, publisher, developer, genre',
                      {'publisher': ('publishers', 'name'), 'developer': ('developers', 'name')}),
            'keys': ('keys', 'key, game, platform, price', {'game': ('games', 'name')}),
            'orders': ('orders', 'date, key, id, user_id', {'user_id': ('users', 'name')}),
            'users': ('users', 'id, name, admin', {})
        }

        tables_output_templates_for_users = {
            'publishers': ('publishers', 'name, country', {}),
            'developers': ('developers', 'name, country', {}),
            'games': ('games', 'name, publisher, genre',
                      {'publisher': ('publishers', 'name')}),
            'orders': ('orders', 'date, key', {})
        }

        if is_admin(message):
            table, columns, forgein_keys = tables_output_templates_for_admins[table_name]
        else:
            table, columns, forgein_keys = tables_output_templates_for_users[table_name]

        head = columns.split(', ')

        if table == 'orders':
            head += ['game', 'platform']
            if is_admin(message):
                body = DBWork.select_many_rows(table, columns)
            else:
                body = DBWork.select_many_rows(table, columns, 'user_id', users_data[message.from_user.id]['id'])
            for row in body:
                date = row[0]
                date_string = datetime(date.year, date.month, date.day, date.hour, date.minute)
                row[0] = date_string.strftime('%d.%m.%Y')
                platform = DBWork.select_value('keys', 'platform', 'key', row[1])
                game = DBWork.select_value('games', 'name', 'id', DBWork.select_value('keys', 'game', 'key', row[1]))
                row += [game, platform]

        else:
            body = DBWork.select_many_rows(table, columns)
        for row in body:
            for col in forgein_keys:
                colNum = head.index(col)
                new_value = DBWork.select_value(forgein_keys[col][0], forgein_keys[col][1])
                row[colNum] = new_value

        if len(body) == 0:
            bot.send_message(message.chat.id,
                             "Данных данных нет на сервере, просим вас подождать несколько дней и повторить запрос")
            raise Exception('Table "' + table + '" is empty')

        pages = ceil(len(body) / page_size)
        if page > pages:
            page = pages

        tab = PrettyTable(head)
        tab.add_rows(body[page_size * (page - 1):page_size * page])
        res = '<pre>' + tab.get_string() + '</pre>'

        bot.send_message(message.chat.id, res,
                             reply_markup=tables_paginator(pages, page, table).markup, parse_mode='HTML')


    ##########################
    # --Commands For Admins--#
    ##########################

    ##########################
    # ---Default commands----#
    ##########################

    character_pages = ['sada', 'dasdasd', 'dsasdsdaasddwadsd']

    @bot.message_handler(commands='test')
    def test(message, page=1):
        bot.send_message(message.chat.id, 'test')

    @bot.message_handler(content_types='text')
    def raw_text_message(message):
        if message.text in ('Publishers', 'Developers', 'Games', 'Keys', 'Orders', 'Users'):
            send_table_to_user(message, message.text.lower(), page=1)
        else:
            bot.send_message(message.chat.id, "Я не знаю такого, простите")

    bot.infinity_polling()


if __name__ == '__main__':
    main()
