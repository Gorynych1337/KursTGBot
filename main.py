import os
import telebot
from WorkWithDB import WWDB
from keyboards import *
from prettytable import PrettyTable
from math import ceil
from datetime import datetime


def main():
    token = os.environ.get('CourseTGBot')
    bot = telebot.TeleBot(token)
    dbwork = WWDB(user='postgres',
                  password='admin123',
                  host='localhost',
                  port='5432',
                  database='GameShop')

    users_data = dict()
    tables = ('Publishers', 'Developers', 'Games', 'Keys', 'Orders', 'Users')
    page_size = 9
    change_types = ('Insert', 'Update', 'Delete')

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

    insert_data = {
        'publishers': ('Название, страна', {}, 'name, country'),
        'developers': ('Название, страна', {}, 'name, country'),
        'games': ('Название, издатель, разработчик, жанр, год выпуска',
                  {1: ('publishers', 'id', 'name'), 2: ('developers', 'id', 'name')},
                  'name, publisher, developer, genre, year, description'),
        'keys': ('Ключ, игра, платформа, цена', {1: ('games', 'id', 'name')},
                 'key, game, platform, price')
    }
    update_data = {
        'publishers': {'name': 'string', 'country': 'string'},
        'developers': {'name': 'string', 'country': 'string'},
        'games': {'name': 'string', 'publisher': 'id', 'developer': 'id', 'genre': 'string', 'year': 'int',
                  'description': 'big string'},
        'keys': {'key': 'string', 'game': 'id', 'platform': 'string', 'price': 'int'},
        'users': {'name': 'string', 'password': 'string', 'is_admin': 'bool'}
    }
    delete_data = {
        'publishers': ['id', 'Название', 'Страна'],
        'developers': ['id', 'Название', 'Страна'],
        'games': ['id', 'Название', 'Издатель', 'Разработчик', 'Жанр'],
        'keys': ['id', 'Ключ', 'Игра', 'Платформа', 'Цена'],
        'orders': ['id', 'Дата', 'Покупатель'],
        'users': ['id', 'Логин', 'is_admin']
    }
    rules = {
        'id': '\n•столбец {} является id записи в соответствующей таблице',
        'bool': '\n•столбец {} имеет только занечения true или false',
        'date': '\n•столбец {} имеет формат "год.месяц.день час:минута"',
        'big string': '\n•столбец {} вводится отдельно'
    }

    ##########################
    # ------Helps Funcs------#
    ##########################

    def exit_check(func):
        def wrapped(message):
            if message.text == '/exit':
                bot.send_message(message.chat.id, 'Операция прервана')
                output_tables_kb(message.from_user.id, message.chat.id)
                raise Exception('Quit from function, all is OK')
            func(message)

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

    def datetime_to_string(date_time, date_or_datetime):
        date_string = datetime(date_time.year, date_time.month, date_time.day,
                               date_time.hour, date_time.minute)
        if date_or_datetime == 'date':
            res_string = date_string.strftime('%d.%m.%Y')
        elif date_or_datetime == 'datetime':
            res_string = date_string.strftime('%d.%m.%Y %H:%M')
        else:
            raise Exception('Bad info for timestamptz_to_string func')
        return res_string

    def pay_the_game():
        return 'Подключить оплату в этого бота я не могу, потому что это будет мошенничество, но заказ на ваш аккаунт' \
               ' добавить можно'

    def for_admin(func):
        def wrapped(data):
            try:
                chat_id = data.chat.id
            except:
                chat_id = data.message.chat.id
            if is_admin(data.from_user.id, chat_id):
                func(data)
            else:
                bot.send_message(chat_id, 'У вас нет доступа для такого:(\nПопробуйте другой аккаунт')
                raise Exception('This command not for common users')

        return wrapped

    def get_data_for_output_table(table, columns, order_by, foreign_keys, admin_check, **kwargs):
        # Получение всех данных данных из бд для тела таблицы
        if 'key' and 'key_value' in kwargs:
            body = dbwork.select_many_rows(table, columns, key=kwargs['key'],
                                           key_value=kwargs['key_value'],
                                           order_by=order_by)
        else:
            body = dbwork.select_many_rows(table, columns, order_by=order_by)

        # Проверка на существование данных
        if len(body) == 0:
            raise ValueError("Table '' + table + ' is empty or dont have needed entries")

        # Обработка данных из тела таблицы
        for row in body:
            if table == 'orders':
                if admin_check:
                    row[1] = datetime_to_string(row[1], 'date')
                key_id = dbwork.select_one_value('orders', 'key', 'id', row[0])

                platform = dbwork.select_one_value('keys', 'platform', 'id', key_id)

                game_id = dbwork.select_one_value('keys', 'game', 'id', key_id)
                game = dbwork.select_one_value('games', 'name', 'id', game_id)

                row += [game, platform]

            columns_array = columns.split(', ')
            for col in foreign_keys:
                col_num = columns_array.index(col)
                new_value = dbwork.select_one_value(foreign_keys[col][0], foreign_keys[col][2],
                                                    foreign_keys[col][1], row[col_num])
                row[col_num] = new_value

        return body

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
        bot.send_message(call.message.chat.id, 'Введите логин', reply_markup=exit_kb)
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, get_register_login)

    @exit_check
    def get_register_login(message):
        try:
            password = dbwork.select_one_value('users', 'password', key='name', key_value=message.text)
            if password is None:
                raise Exception('user without password')
        except Exception as err:
            global reg_user_id
            if err.args[0] == "user without password":
                reg_user_id = dbwork.select_one_value('users', 'id', key='name', key_value=message.text)
            else:
                reg_user_id = dbwork.insert('users', 'name', [message.text], returning='id')
            bot.send_message(message.chat.id, 'Придумайте пароль')
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_register_password)
        else:
            bot.send_message(message.chat.id, 'Такой логин уже существует, выберете другой')
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_register_login)

    @exit_check
    def get_register_password(message):
        try:
            dbwork.update('users', ['password'], [str(message.text)], 'id', reg_user_id, ['password'])
        except:
            bot.send_message(message.chat.id, 'Что-то пошло не так. Приносим извинения за неполадки')
        else:
            users_data[message.from_user.id] = {'is_admin': dbwork.select_one_value('users', 'is_admin',
                                                                                    key='id',
                                                                                    key_value=reg_user_id),
                                                'id': reg_user_id}
            bot.send_message(message.chat.id, 'Вы успешно зарегестрированы')
            output_tables_kb(message.from_user.id, message.chat.id)

    # ветка входа
    @bot.callback_query_handler(func=lambda call: call.data == 'sign_in')
    def start_sign_in(call):
        bot.send_message(call.message.chat.id, 'Введите лоигн', reply_markup=exit_kb)
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, get_sign_in_login)

    @exit_check
    def get_sign_in_login(message):
        try:
            global sign_in_user_id
            sign_in_user_id = dbwork.select_one_value('users', 'id', key='name', key_value=message.text)
        except:
            bot.send_message(message.chat.id,
                             'Такого лоигна не существует, попробуйте ввести другой или зарегестрироваться')
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_sign_in_login)
        else:
            bot.send_message(message.chat.id, 'Введите пароль')
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_sign_in_password)

    @exit_check
    def get_sign_in_password(message):
        if dbwork.select_one_value('users', 'password', 'id', sign_in_user_id) == dbwork.get_crypt_value(message.text):
            users_data[message.from_user.id] = {'is_admin': dbwork.select_one_value('users', 'is_admin',
                                                                                    key='id',
                                                                                    key_value=sign_in_user_id),
                                                'id': sign_in_user_id}
            bot.send_message(message.chat.id, 'Вход прошёл успешно')
            output_tables_kb(message.from_user.id, message.chat.id)
        else:
            bot.send_message(message.chat.id, 'Пароль неверный, попробуйте снова')
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_sign_in_password)

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

        if table == 'orders' and not is_admin(message.from_user.id, message.chat.id):
            try:
                body = get_data_for_output_table(table, columns, order_by, foreign_keys,
                                                 is_admin(message.from_user.id, message.chat.id),
                                                 key='buyer', key_value=users_data[message.from_user.id]['id'])
            except ValueError:
                return bot.send_message(message.chat.id,
                                        'У вас нет заказов, нужно это исправить',
                                        reply_markup=make_order_inline_kb)

        else:
            try:
                body = get_data_for_output_table(table, columns, order_by, foreign_keys,
                                                 is_admin(message.from_user.id, message.chat.id))
            except ValueError:
                return bot.send_message(message.chat.id,
                                        'Данных нет на сервере просим вас подождать до обновления сервера',
                                        reply_markup=make_order_inline_kb)

        # Рассчёт страниц для пагинатора
        pages = ceil(len(body) / page_size)
        if page > pages:
            page = pages

        # Добавление данних из нужного промежутка на страницу
        tab = PrettyTable(head)
        tab.add_rows(body[page_size * (page - 1):page_size * page])
        tab.border = False
        res = '<pre>' + tab.get_string() + '</pre>'

        paginator = tables_paginator(pages, page, table)

        # Добавление клавиатур к пагинатору
        insert_btn, update_btn, delete_btn = make_change_db_inline_btns(table)
        if table == 'developers':
            if is_admin(message.from_user.id, message.chat.id):
                paginator.add_after(insert_btn, update_btn, delete_btn)

        elif table == 'publishers':
            if is_admin(message.from_user.id, message.chat.id):
                paginator.add_after(insert_btn, update_btn, delete_btn)

        elif table == 'games':
            paginator.add_before(make_order_inline_btn)
            if is_admin(message.from_user.id, message.chat.id):
                paginator.add_after(insert_btn, update_btn, delete_btn)

        elif table == 'keys':
            if is_admin(message.from_user.id, message.chat.id):
                paginator.add_after(insert_btn, update_btn, delete_btn)

        elif table == 'users':
            if is_admin(message.from_user.id, message.chat.id):
                paginator.add_after(update_btn, delete_btn)

        elif table == 'orders':
            if is_admin(message.from_user.id, message.chat.id):
                paginator.add_after(delete_btn)

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
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, get_game_name)

    @bot.message_handler(commands=['make_order'])
    def start_make_order_by_command(message):
        is_admin(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id, 'Введите название игры для покупки', reply_markup=exit_kb)
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_game_name)

    @exit_check
    def get_game_name(message):
        try:
            game_id = dbwork.select_one_value('games', 'id', key='name', key_value=message.text)
        except:
            bot.send_message(message.chat.id,
                             'Такой игры не существует, перепроверьте правильность написания')
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_game_name)
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
            dbwork.insert('orders', 'buyer, key', [users_data[call.from_user.id]['id'], key_id])
            dbwork.update('keys', ['purchased'], ['true'], 'id', key_id)
        except:
            bot.send_message(call.message.chat.id,
                             'При оформлении заказа произошла ошибка, попробуйте сделать запрос позже')
            output_tables_kb(call.from_user.id, call.message.chat.id)
        else:
            text = pay_the_game()
            bot.send_message(call.message.chat.id, text)
            output_tables_kb(call.from_user.id, call.message.chat.id)

    # Цепочка работы сданными в БД для администраторов
    @bot.message_handler(commands=['change'])
    @for_admin
    def start_change_db_by_message(message):
        bot.send_message(message.chat.id, 'Выберете таблицу для изменения', reply_markup=admin_tables_kb)

    @bot.callback_query_handler(func=lambda call: call.data.split('-')[0] in change_types)
    @for_admin
    def start_change_db_by_callback(call):
        global table
        table = call.data.split('-')[1]
        callback_change_type = call.data.split('-')[0]
        if callback_change_type == 'Insert':
            bot.send_message(call.message.chat.id,
                             'Введите через запятую значения следующих параметров для добавления:\n' +
                             insert_data[table][0], reply_markup=exit_kb)
            bot.register_next_step_handler_by_chat_id(call.message.chat.id, get_insert_values)

        elif callback_change_type == 'Update':
            bot.send_message(call.message.chat.id, 'Введите id записи, которую небходимо изменить',
                             reply_markup=exit_kb)
            bot.register_next_step_handler_by_chat_id(call.message.chat.id, get_update_entry_id)

        elif callback_change_type == 'Delete':
            bot.send_message(call.message.chat.id, 'Введите id записи, которую небходимо удалить',
                             reply_markup=exit_kb)
            bot.register_next_step_handler_by_chat_id(call.message.chat.id, get_delete_entry_id)

    # Ветка добавления новых данных в БД
    @exit_check
    def get_insert_values(message):
        global insert_input_data
        insert_input_data = message.text.split(', ')
        if len(insert_input_data) != len(insert_data[table][0].split(', ')):
            bot.send_message(message.chat.id, 'Введённые данные не соответсвуют количеству колонок')
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_insert_values)

        names_instead_ids = insert_data[table][1]
        for col in names_instead_ids.keys():
            try:
                insert_input_data[col] = dbwork.select_one_value(names_instead_ids[col][0], names_instead_ids[col][1],
                                                                 names_instead_ids[col][2], insert_input_data[col])
            except TypeError:
                bot.send_message(message.chat.id, 'Данные не соответсвуют данным из других таблиц, '
                                                  'перепроверьте данные')

        if table == 'games':
            bot.send_message(message.chat.id, 'Введите описание для игры')
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_insert_game_description)
        else:
            end_insert_db(message.chat.id, message.from_user.id)

    def get_insert_game_description(message):
        insert_input_data.append(message.text)
        end_insert_db(message.chat.id, message.from_user.id)

    def end_insert_db(chat_id, user_id):
        try:
            col = insert_data[table][2]
            dbwork.insert(table, col, insert_input_data)
        except:
            bot.send_message(chat_id, 'Что-то пошло не так, повторите запрос позже')
        else:
            bot.send_message(chat_id, 'Данные успешно добавлены')
        output_tables_kb(user_id, chat_id)

    # Ветка изменения данных в БД
    @exit_check
    def get_update_entry_id(message):
        try:
            dbwork.select_one_row(table, 'id', message.text)
        except:
            bot.send_message(message.chat.id, 'Такого id не существует, перепроверьте данные')
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_update_entry_id)
        else:
            global update_id
            update_id = message.text
            columns = update_data[table].keys()
            bot.send_message(message.chat.id, 'Введите через запятую колонки, которые необходимо изменить:\n' +
                             ', '.join(columns))
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_update_columns)

    @exit_check
    def get_update_columns(message):
        global update_columns
        update_columns = message.text.split(', ')
        additional_rules = ''
        for column in update_columns:
            try:
                update_data[table][column]
            except:
                bot.send_message(message.chat.id, 'Введённые данные не соответсвуют колонкам выбранной таблицы,'
                                                  'попробуйте ввести необходимые колонки вновь')
                bot.register_next_step_handler_by_chat_id(message.chat.id, get_update_columns)
            else:
                if update_data[table][column] != 'string' and update_data[table][column] != 'int':
                    additional_rules += rules[update_data[table][column]].format(column)
                    if update_data[table][column] == 'big string':
                        global description_exist
                        description_exist = True
                        update_columns.remove(column)
        if additional_rules != '':
            additional_rules = '\n\nТак же обратите внимание, что:' + additional_rules
        bot.send_message(message.chat.id, 'Введите новые данные для записи' + additional_rules)
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_new_update_data)

    @exit_check
    def get_new_update_data(message):
        global update_input_data
        update_input_data = message.text.split(', ')
        if len(update_input_data) != len(update_columns):
            bot.send_message(message.chat.id, 'Введённые данные не соответсвуют количеству колонок')
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_new_update_data)
        for i in range(len(update_input_data)):
            if update_data[table][update_columns[i]] == 'id':
                try:
                    dbwork.select_one_row(table, update_columns[i], update_input_data[i])
                except:
                    bot.send_message(message.chat.id, 'Введённые id не существуют, перепроверьте и повторите запрос')
                    bot.register_next_step_handler_by_chat_id(message.chat.id, get_new_update_data)
            elif update_data[table][update_columns[i]] == 'date':
                update_input_data[i] = datetime_to_string(update_input_data[i], 'datetime')
        if 'description_exist' in globals():
            bot.send_message(message.chat.id, 'Введите описание игры')
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_update_game_description)
        else:
            end_update_db(message.chat.id, message.from_user.id)

    def get_update_game_description(message):
        update_columns.append('description')
        update_input_data.append(message.text)
        end_update_db(message.chat.id, message.from_user.id)

    def end_update_db(chat_id, user_id):
        try:
            dbwork.update(table, update_columns, update_input_data, 'id', update_id)
        except:
            bot.send_message(chat_id, 'Что-то пошло не так, повторите запрос позже')
        else:
            bot.send_message(chat_id, 'Данные успешно добавлены')
        output_tables_kb(user_id, chat_id)

    # Ветка удаления данных из БД
    @exit_check
    def get_delete_entry_id(message):
        try:
            dbwork.select_one_row(table, 'id', message.text)
        except:
            bot.send_message(message.chat.id, 'Такого id не существует, перепроверьте данные')
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_update_entry_id)
        else:
            global delete_id
            delete_id = message.text
            ask_delete_entry(message.chat.id)

    def ask_delete_entry(chat_id):
        table_name, columns, order_by, foreign_keys = tables_output_data_for_admins[table.capitalize()]
        data = get_data_for_output_table(table_name, columns, order_by, foreign_keys, 'true', key='id',
                                         key_value=delete_id)[0]
        columns_names = delete_data[table]
        output_string = 'Вы точно хотите удалить следующую запись?\n'
        for i in range(len(data)):
            output_string += f"{columns_names[i]}: {data[i]}\n"
        bot.send_message(chat_id, output_string, reply_markup=yes_no_kb)
        bot.register_next_step_handler_by_chat_id(chat_id, delete_entry)

    def delete_entry(message):
        if message.text == 'Нет':
            output_tables_kb(message.from_user.id, message.chat.id)
            return
        try:
            dbwork.delete(table, 'id', delete_id)
        except:
            bot.send_message(message.chat.id, 'Что-то пошло не так, повторите запрос позже')
        else:
            bot.send_message(message.chat.id, 'Данные успешно удалены')
        output_tables_kb(message.from_user.id, message.chat.id)

    # Обработчик для неизвестных сообщений
    @bot.message_handler(func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document',
                                                                   'text', 'location', 'contact', 'sticker'])
    def raw_text_message(message):
        bot.send_message(message.chat.id, 'Я не знаю такого, простите')

    bot.infinity_polling()


if __name__ == '__main__':
    main()
