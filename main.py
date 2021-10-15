import os
from WorkWithDB import WWDB
from keyboards import *
import telebot
from prettytable import PrettyTable
from math import ceil
from datetime import datetime


def main():
    token = os.environ.get('CourseTGBot')
    bot = telebot.TeleBot(token)
    dbwork = WWDB()

    users_data = dict()
    tables = ('Publishers', 'Developers', 'Games', 'Keys', 'Orders', 'Users')
    page_size = 5

    tables_output_data_for_admins = {
        'Publishers': ('publishers', 'id, name, country', 'id', {}),
        'Developers': ('developers', 'id, name, country', 'id', {}),
        'Games': ('games', 'id, name, publisher, developer, genre', 'id',
                  {'publisher': ('publishers', 'id', 'name'), 'developer': ('developers', 'id', 'name')}),
        'Keys': ('keys', 'id, key, game, platform, price', 'id', {'game': ('games', 'id', 'name')}),
        'Orders': ('orders', 'id, date, buyer', 'id', {'buyer': ('users', 'id', 'name')}),
        'Users': ('users', 'id, name, is_admin', 'id', {})
    }

    tables_output_data_for_users = {
        'Publishers': ('publishers', 'name, country', 'id', {}),
        'Developers': ('developers', 'name, country', 'id', {}),
        'Games': ('games', 'name, genre, year', 'id', {}),
        'Orders': ('orders', 'id', 'id', {})
    }

    ##########################
    # ------Helps Funks------#
    ##########################

    def exit_check(funk):
        def wrapped(message):
            if (message.text == '/exit'):
                bot.send_message(message.chat.id, 'Операция прервана', reply_markup=start_kb)
                raise Exception('Quit from function, all is OK')
            funk(message)

        return wrapped

    def is_admin(user_id, chat_id):
        try:
            admin_check = users_data[user_id]['is_admin']
        except KeyError:
            bot.send_message(chat_id, 'Пожалуйста зарагестрируйсесть или войдите',
                             reply_markup=register_sign_in_inline_kb)
            raise Exception("This user didn't signed in")
        else:
            return admin_check

    def output_tables_kb(user_id, chat_id):
        if is_admin(user_id, chat_id):
            bot.send_message(chat_id, 'Выберете таблицу', reply_markup=admin_tables_kb)
        else:
            bot.send_message(chat_id, 'Выберете таблицу', reply_markup=user_tables_kb)

    def timestampz_to_string(timestamp_date_time, date_or_datetime):
        date_string = datetime(timestamp_date_time.year, timestamp_date_time.month, timestamp_date_time.day,
                               timestamp_date_time.hour, timestamp_date_time.minute)
        if date_or_datetime == 'date':
            res_string = date_string.strftime('%d.%m.%Y')
        elif date_or_datetime == 'datetime':
            res_string = date_string.strftime('%d.%m.%Y %H:%M')
        else:
            raise Exception('Bad info for timestampz_to_string func')
        return res_string

    def pay_the_game():
        return 'Подключить оплату в этого бота я не могу, потому что это будет мошенничество, но заказ на ваш аккаунт' \
               'добавить можно'

    def for_admin(funk):
        def wrapped(message):
            if (users_data[message.from_user.id]['is_admin']):
                funk(message)
            else:
                bot.send_message(message.chat.id, 'У вас нет доступа для такого:(\nПопробуйте другой аккаунт')
                raise Exception('This command not for common users')

        return wrapped

    ##########################
    # -------Commands--------#
    ##########################

    @bot.message_handler(commands=['start'])
    def start(message):
        bot.send_message(message.chat.id, 'Привет, для регистрации или входа нажмите на кнопку',
                         reply_markup=register_sign_in_inline_kb)

    @bot.message_handler(commands=['help'])
    def help_message(message):
        bot.send_message(message.chat.id, 'Для начала работы нажмите на /start и следуйте указаниям')

    # ветка регистрации
    @bot.callback_query_handler(func=lambda call: call.data == 'register')
    def start_register(call):
        bot.send_message(call.message.chat.id, 'Введите лоигн', reply_markup=exit_kb)
        bot.register_next_step_handler(call.message, get_register_login)

    @exit_check
    def get_register_login(message):
        global login
        login = str(message.text)
        try:
            dbwork.select_one_value('users', 'id', key='name', key_value=login)
        except:
            bot.send_message(message.chat.id, 'Придумайте пароль')
            bot.register_next_step_handler(message, get_register_password)
        else:
            bot.send_message(message.chat.id, 'Такой логин уже существует, выберете другой')
            bot.register_next_step_handler(message, get_register_login)

    @exit_check
    def get_register_password(message):
        global password
        password = str(message.text)
        try:
            register_data = (login, password)
            dbwork.insert('users', 'name, password', register_data)
        except:
            bot.send_message(message.chat.id, 'Что-то пошло не так. Приносим извинения за неполадки')
        else:
            users_data[message.from_user.id] = {'is_admin': dbwork.select_one_value('users', 'is_admin', 'name', login),
                                                'id': dbwork.select_one_value('users', 'id', 'name', login)}
            bot.send_message(message.chat.id, 'Вы успешно зарегестрированы')
            output_tables_kb(message.from_user.id, message.chat.id)

    # ветка входа
    @bot.callback_query_handler(func=lambda call: call.data == 'sign_in')
    def start_sign_in(call):
        bot.send_message(call.message.chat.id, 'Введите лоигн', reply_markup=exit_kb)
        bot.register_next_step_handler(call.message, get_sign_in_login)

    @exit_check
    def get_sign_in_login(message):
        global login
        login = str(message.text)
        try:
            dbwork.select_one_value('users', 'id', key='name', key_value=login)
        except:
            bot.send_message(message.chat.id,
                             'Такого лоигна не существует, попробуйте ввести другой или зарегестрироваться')
            bot.register_next_step_handler(message, get_sign_in_login)
        else:
            bot.send_message(message.chat.id, 'Введите пароль')
            bot.register_next_step_handler(message, get_sign_in_password)

    @exit_check
    def get_sign_in_password(message):
        global password
        password = str(message.text)
        if (dbwork.select_one_value('users', 'password', 'name', login) == password):
            users_data[message.from_user.id] = {'is_admin': dbwork.select_one_value('users', 'is_admin', 'name', login),
                                                'id': dbwork.select_one_value('users', 'id', 'name', login)}
            bot.send_message(message.chat.id, 'Вход прошёл успешно')
            output_tables_kb(message.from_user.id, message.chat.id)
        else:
            bot.send_message(message.chat.id, 'Пароль неверный, попробуйте снова')
            bot.register_next_step_handler(message, get_sign_in_password)

    # Вывод доступных таблиц
    @bot.message_handler(commands=['tables'])
    def output_tables_kb_by_message(message):
        output_tables_kb(message.from_user.id, message.chat.id)

    @bot.message_handler(func=lambda message: message.text in tables)
    def send_table_to_user(message, page=1):
        # Получение необходимых данных для обращения  БД
        if is_admin(message.from_user.id, message.chat.id):
            table, columns, order_by, foreign_keys = tables_output_data_for_admins[message.text]
        else:
            table, columns, order_by, foreign_keys = tables_output_data_for_users[message.text]

        # Заголовок таблицы
        head = columns.split(', ')
        if table == 'orders':
            head += ['game', 'platform']

        # Получение всех данных данных из бд для тела таблицы
        if table == 'orders' and not is_admin(message.from_user.id, message.chat.id):
            body = dbwork.select_many_rows(table, columns, key='buyer',
                                           key_value=users_data[message.from_user.id]['id'],
                                           order_by=order_by)
            # Проверка на существование данных
            if len(body) == 0:
                bot.send_message(message.chat.id, 'У вас нет заказов, нужно это исправить',
                                 reply_markup=make_order_inline_kb)
                return
        else:
            body = dbwork.select_many_rows(table, columns, order_by=order_by)
            empty_body_message = 'Данных нет на сервере просим вас подождать до обновления сервера'
            # Проверка на существование данных
            if len(body) == 0:
                bot.send_message(message.chat.id, empty_body_message)
                raise Exception("Table '' + table + ' is empty or dont have needed entries")

        # Обработка данных из тела таблицы
        for row in body:
            if table == 'orders':
                if is_admin(message.from_user.id, message.chat.id):
                    row[1] = timestampz_to_string(row[1], 'date')
                key_id = dbwork.select_one_value('orders', 'key', 'id', row[0])

                platform = dbwork.select_one_value('keys', 'platform', 'id', key_id)

                game_id = dbwork.select_one_value('keys', 'game', 'id', key_id)
                game = dbwork.select_one_value('games', 'name', 'id', game_id)

                row += [game, platform]
            for col in foreign_keys:
                colNum = head.index(col)
                new_value = dbwork.select_one_value(foreign_keys[col][0], foreign_keys[col][2], foreign_keys[col][1],
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

        paginator = tables_paginator(pages, page, table)
        if table == 'orders':
            paginator.add_after(make_order_inline_btn)
        elif table == 'games':
            paginator.add_after(make_order_inline_btn)

        # Отправка сообщения
        bot.send_message(message.chat.id, res,
                         reply_markup=paginator.markup, parse_mode='HTML')

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

    @bot.callback_query_handler(func=lambda call: call.data == 'make_order')
    def start_make_order_by_callback(call):
        is_admin(call.from_user.id, call.message.chat.id)
        bot.send_message(call.message.chat.id, 'Введите название игры для покупки', reply_markup=exit_kb)
        bot.register_next_step_handler(call.message, get_game_name)

    @bot.message_handler(commands=['make_order'])
    def start_make_order_by_command(message):
        is_admin(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id, 'Введите название игры для покупки', reply_markup=exit_kb)
        bot.register_next_step_handler(message, get_game_name)

    @exit_check
    def get_game_name(message):
        global user_id
        user_id = message.from_user.id
        try:
            game_id = dbwork.select_one_value('games', 'id', key='name', key_value=message.text)
        except:
            bot.send_message(message.chat.id,
                             'Такой игры не существует, перепроверьте правильность написания')
            bot.register_next_step_handler(message, get_game_name)
        else:
            try:
                keys = dbwork.select_many_rows('keys', key='game', key_value=game_id)
                global not_purchased_keys
                not_purchased_keys = {}
                for key in keys:
                    if not key[5]:
                        not_purchased_keys[key[0]] = key[3]
                if len(not_purchased_keys) == 0:
                    raise Exception('There is no needed game-keys')
            except:
                bot.send_message(message.chat.id, 'К сожалению, ключи закончились, а новые ещё не куплены.'
                                                  'Попробуйте совершить покупку позже')
            else:
                platforms_inline_kb = make_inline_kb('platform', list(set(not_purchased_keys.values())))
                bot.send_message(message.chat.id, 'Выберете одну из следующих платформ',
                                 reply_markup=platforms_inline_kb)

    @bot.callback_query_handler(func=lambda call: call.data.split('-')[0] == 'platform')
    def get_game_platform(call):
        try:
            platform = call.data.split('-')[1]
            key_id = list(not_purchased_keys.keys())[list(not_purchased_keys.values()).index(platform)]
            dbwork.update('keys', ['purchased'], ['true'], 'id', key_id)
            dbwork.insert('orders', 'buyer, key', [users_data[user_id]['id'], key_id])
        except:
            bot.send_message(call.message.chat.id,
                             'При оформлении заказа произошла ошибка, попробуйте сделать запрос позже')
            output_tables_kb(call.from_user.id, call.message.chat.id)
        else:
            text = pay_the_game()
            bot.send_message(call.message.chat.id, text)
            output_tables_kb(call.from_user.id, call.message.chat.id)

    # ---Raw text handler----#
    @bot.message_handler(content_types='text')
    def raw_text_message(message):
        bot.send_message(message.chat.id, 'Я не знаю такого, простите')

    bot.infinity_polling()


if __name__ == '__main__':
    main()
