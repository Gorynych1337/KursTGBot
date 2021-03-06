import psycopg2


class WWDB:
    def __init__(self, user, password, host, port, database):  # метод чтения БД и создания курсора
        self.conn = psycopg2.connect(user=user,
                                     password=password,
                                     host=host,
                                     port=port,
                                     database=database)
        self.curs = self.conn.cursor()  # курсор

    def select_many_rows(self, table, columns='*', **kwargs):
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
            select_many_rows_command = f"select {columns} from {table} where {kwargs['key']} = " \
                                       f"'{kwargs['key_value']}' order by {kwargs['order_by']}"
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

    def select_many_values(self, table, column, key, key_value):
        select_value_command = f"select {column} from {table} where {key} = '{key_value}'"
        self.curs.execute(select_value_command)
        raw_rows = self.curs.fetchall()
        values = []
        for row in raw_rows:
            values.append(row[0])
        return values

    def select_one_value(self, table, column, key, key_value):
        select_value_command = f"select {column} from {table} where {key} = '{key_value}'"
        self.curs.execute(select_value_command)
        value = self.curs.fetchone()[0]
        return value

    def insert(self, table, columns, values, **kwargs):
        insert_command_string = f"insert into {table} ({columns}) values (%s{', %s' * (len(values) - 1)})"
        if 'returning' in kwargs:
            insert_command_string += 'RETURNING ' + kwargs['returning']
        insert_command = self.curs.mogrify(insert_command_string, values)
        try:
            self.curs.execute(insert_command)
            self.conn.commit()
            if 'returning' in kwargs:
                result = self.curs.fetchone()[0]
                return result
        except:
            self.conn.rollback()
            raise Exception('Insert was non successful')

    def update(self, table, columns, values, key, key_value, crypt_columns=[None]):
        column_value_ratio_string = ''
        for i in range(len(columns)):
            values[i] = f"'{values[i]}'"
            if columns[i] in crypt_columns:
                values[i] = f"md5({values[i]})"
            column_value_ratio_string += f"{columns[i]} = {values[i]},"

        update_command_string = f"update {table} set {column_value_ratio_string[:-1]} where {key} = '{key_value}'"
        update_command = self.curs.mogrify(update_command_string)
        try:
            self.curs.execute(update_command)
            self.conn.commit()
        except:
            self.conn.rollback()
            raise Exception('Update was non successful')

    def delete(self, table, key, key_value):
        delete_command_string = f"delete from {table} where {key} = {key_value}"
        delete_command = self.curs.mogrify(delete_command_string)
        try:
            self.curs.execute(delete_command)
            self.conn.commit()
        except:
            self.conn.rollback()
            raise Exception('Delete was non successful')

    def get_crypt_value(self, data):
        command_string = f"select md5('{data}')"
        command = self.curs.mogrify(command_string)
        self.curs.execute(command)
        return self.curs.fetchone()[0]
