import json
import sys

import mysql.connector
from symphonyGPT.performers.api_extractor.api_extractor import APIExtractor
from symphonyGPT.performers.api_keys import APIKeys
from symphonyGPT.symphony.db_util import parse_mysql_connection_string, get_database_name
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony
from symphonyGPT.symphony.symphony_cache import SymphonyCache


class MySQLSchemaExtractor(APIExtractor):
    def __init__(self, database="use_connection_string", table_name="all", example_records=0, connection_string=None):
        super().__init__()
        # mysql://root:password123@localhost:3306/mydatabase
        if connection_string is not None:
            self.conn_str = connection_string
        else:
            self.conn_str = APIKeys().get_api_key("mysql_connection_string")

        # Parse the connection string
        self.mysql_params = parse_mysql_connection_string(self.conn_str)
        self.database = database
        self.table_name = table_name
        self.example_records = example_records
        self.cache = SymphonyCache("/tmp/symphonyGPT_cache")

    def _quote_ident(self, name):
        return '`' + str(name).replace('`', '``') + '`'

    def _table_status_map(self, cursor, table_name="all"):
        if table_name == "all":
            cursor.execute("SHOW TABLE STATUS")
        else:
            cursor.execute("SHOW TABLE STATUS WHERE Name = %s", (table_name,))

        status = {}
        for row in cursor.fetchall():
            status[row[0]] = {
                "name": row[0],
                "engine": row[1],
                "row_count": int(row[4]) if row[4] is not None else 0,
                "data_length": int(row[6]) if row[6] is not None else 0,
                "collation": row[14] if len(row) > 14 else "",
                "comment": row[17] if len(row) > 17 and row[17] else "",
            }
        return status

    def _get_columns(self, cursor, table_name):
        cursor.execute(f"SHOW FULL COLUMNS FROM {self._quote_ident(table_name)}")
        columns = []
        for col in cursor.fetchall():
            columns.append({
                "name": col[0],
                "type": col[1],
                "collation": col[2],
                "nullable": col[3] == "YES",
                "key": col[4] or "",
                "default": None if col[5] is None else str(col[5]),
                "extra": col[6] or "",
                "comment": col[8] if len(col) > 8 and col[8] else "",
            })
        return columns

    def _collect_table(self, cursor, table_name, status_map):
        quoted = self._quote_ident(table_name)
        cursor.execute(f"SHOW CREATE TABLE {quoted}")
        create_table_rows = cursor.fetchall()
        create_sql = create_table_rows[0][1] if create_table_rows else ""

        status = status_map.get(table_name, {})
        table_meta = {
            "name": table_name,
            "engine": status.get("engine"),
            "row_count": status.get("row_count", 0),
            "data_length": status.get("data_length", 0),
            "collation": status.get("collation", ""),
            "comment": status.get("comment", ""),
            "create_sql": create_sql,
            "columns": self._get_columns(cursor, table_name),
        }

        sample_text = ""
        if self.example_records > 0:
            cursor.execute(f"SELECT * FROM {quoted} LIMIT {int(self.example_records)}")
            example_rows = cursor.fetchall()
            field_names = [i[0] for i in cursor.description] if cursor.description else []
            sample_text += f"\n\nSample records for table {table_name} and its fields:\n"
            for example_row in example_rows:
                example_dict = dict(zip(field_names, example_row))
                sample_text += str(example_dict) + "\n"

        return table_meta, create_sql, sample_text

    def perform(self, prompt):
        # ignore prompt, not used

        answer = ""
        tables_meta = []

        # Connect to the MySQL Database
        conn = None
        try:
            # reset the cache for errors
            self.cache.delete("SQLSchemaExtractor.error")
            self.cache.delete("SQLSchemaExtractor.tables")
            database_name = get_database_name(self.mysql_params, self.database)

            try:
                conn = mysql.connector.connect(
                    host=self.mysql_params['host'],
                    user=self.mysql_params['user'],
                    password=self.mysql_params['password'],
                    database=database_name,
                    port=self.mysql_params['port']
                )
            except Exception as e:
                error_str = f"Failed to connect to the database: {database_name}, error: {e}"
                print(error_str, file=sys.stderr)
                self.cache.set("SQLSchemaExtractor.error", error_str)
                return

            self.cache.set("SQLSchemaExtractor.database", database_name)
            self.cache.set("SQLSchemaExtractor.host", self.mysql_params['host'])
            self.cache.set("SQLSchemaExtractor.port", self.mysql_params['port'])
            self.cache.set("SQLSchemaExtractor.user", self.mysql_params['user'])

            self.util.debug_print(
                f"Connected to the database '{database_name}' on {self.mysql_params['host']} as {self.mysql_params['user']}")
            # Create a cursor object
            cursor = conn.cursor()
            status_map = self._table_status_map(cursor, self.table_name)

            # Executing the DESCRIBE command
            if self.table_name == "all":
                cursor.execute("SHOW TABLES")
                rows = cursor.fetchall()
                for row in rows:
                    table_meta, create_sql, sample_text = self._collect_table(cursor, row[0], status_map)
                    tables_meta.append(table_meta)
                    answer += create_sql
                    answer += sample_text
                    answer += "\n\n"
            else:
                table_meta, create_sql, sample_text = self._collect_table(cursor, self.table_name, status_map)
                tables_meta.append(table_meta)
                answer += create_sql
                answer += sample_text

            self.cache.set("SQLSchemaExtractor.schema", answer)
            self.cache.set("SQLSchemaExtractor.tables", json.dumps({
                "database": database_name,
                "tables": tables_meta,
            }, default=str))
        finally:
            if conn is not None and conn.is_connected():
                conn.close()
                self.util.debug_print("Connection closed")

        self.set_raw_response(answer)


# test main
if __name__ == "__main__":
    m_test = Movement(
        # prompt_classifier=[KeyphraseExtractionTokenClassifier()],
        performers=[MySQLSchemaExtractor(table_name="all")]
    )
    symphony = Symphony(movements=[m_test], null_answer_break=True)
    res = symphony.perform("blah blah blah")

    print(res[0]["answer"])
