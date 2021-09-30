from main import WWDB
from math import ceil
from tablib import *

DBWork = WWDB()

tables_output_templates = {
            'publishers': ('publishers', 'id, name, country', {}),
            'developers': ('developers', 'id, name, country', {}),
            'games': ('games', 'id, name, publisher, developer, genre',
                      {'publisher': ('publishers', 'name'), 'developer': ('developers', 'name')}),
            'keys': ('keys', 'key, game, platform, price', {'game': ('games', 'name')}),
            'orders': ('orders', 'id, user_id, data, key', {'user_id': ('users', 'name')}),
            'users': ('users', 'id, name, admin', {})
        }

table, columns, forgein_keys = tables_output_templates['users']

head = columns.split(', ')
body = DBWork.select_many_rows(table, columns)
for col in forgein_keys:
    colNum = head.index(col)
    for row in body:
        new_value = DBWork.select_value(forgein_keys[col][0], forgein_keys[col][1])
        row[colNum] = new_value

tab = Dataset(head)
for i in body:
    tab.append(i)

print(tab)
print(type(tab.export('json')))