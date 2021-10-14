import psycopg2

class WWDB():
    def __init__(self):  # метод чтения БД и создания курсора
        self.conn = psycopg2.connect(user='postgres',
                                     password='admin123',
                                     host='localhost',
                                     port='5432',
                                     database='GameShop')
        self.curs = self.conn.cursor()  # курсор

    def select_many_rows(self, table, columns=('*'), **kwargs):
        """
        This function get many rows from needed table
        key='true', key_value='true', order_by = 'true'
        :param table: name of table in DB
        :param columns: needed columns in the table in array
        :param kwargs:
        :return: list with lists
        """
        if 'key' and 'key_value' in kwargs:
            select_many_rows_command = f"select {columns} from {table} where {kwargs['key']} = '{kwargs['key_value']}'"
        elif 'order_by' in kwargs:
            select_many_rows_command = f"select {columns} from {table} order by {kwargs['order_by']}"
        elif 'key' and 'key_value' and 'order_by' in kwargs:
            select_many_rows_command = f"select {columns} from {table} where {kwargs['key']} = '{kwargs['key_value']}' order by {kwargs['order_by']}"
        else:
            select_many_rows_command = f"select {columns} from {table}"

        self.curs.execute(select_many_rows_command)
        raw_rows = self.curs.fetchall()
        rows = []
        for row in raw_rows:
            rows.append(list(row))
        return rows

    def select_one_row(self, table, key, key_value, columns='*'):
        select_one_row_command = f"select {columns} from {table} where {key} = '{key_value}'"
        self.curs.execute(select_one_row_command)
        row = list(self.curs.fetchone())
        return row

    def select_value(self, table, column, key, key_value):
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