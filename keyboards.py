from telebot import types
from telegram_bot_pagination import InlineKeyboardPaginator


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

make_order_inline_KB = types.InlineKeyboardMarkup()
make_order_inline_btn = types.InlineKeyboardButton('Сделать заказ!', callback_data="make_order")
make_order_inline_KB.add(make_order_inline_btn)

def tables_paginator(pages, page, table):
    table = table.capitalize()
    paginator = InlineKeyboardPaginator(
        pages,
        current_page=page,
        data_pattern=f'table#{table}#' + '{page}'
    )
    return paginator

def make_inline_KB(KB_name, btns_names_array):
    inline_KB = types.InlineKeyboardMarkup()
    for i in range(len(btns_names_array)):
        btn_text = btns_names_array[i]
        btn_callback = f'{KB_name}-{btns_names_array[i]}'
        btn = (types.InlineKeyboardButton(btn_text, callback_data=btn_callback))
        inline_KB.add(btn)
    return inline_KB