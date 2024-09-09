import sys

import mysql.connector
from symphonyGPT.performers.api_extractor.api_extractor import APIExtractor
from symphonyGPT.performers.api_keys import APIKeys
from symphonyGPT.symphony.db_util import parse_mysql_connection_string, get_database_name
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony
from symphonyGPT.symphony.symphony_cache import SymphonyCache


class MySQLSchemaExtractor(APIExtractor):
    def __init__(self, database="use_connection_string", table_name="all"):
        super().__init__()
        # mysql://root:password123@localhost:3306/mydatabase
        self.conn_str = APIKeys().get_api_key("mysql_connection_string")
        # Parse the connection string
        self.mysql_params = parse_mysql_connection_string(self.conn_str)
        self.database = database
        self.table_name = table_name
        self.cache = SymphonyCache("/tmp/symphonyGPT_cache")


    def perform(self, prompt):
        # ignore prompt, not used

        answer = ""

        # Connect to the MySQL Database
        conn = None
        try:
            # reset the cache for errors
            self.cache.delete("SQLSchemaExtractor.error")
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

            # Executing the DESCRIBE command
            if self.table_name == "all":
                cursor.execute(f"SHOW TABLES")
                rows = cursor.fetchall()
                for row in rows:
                    cursor.execute(f"SHOW CREATE TABLE `{row[0]}`")
                    create_table_rows = cursor.fetchall()
                    for create_table_row in create_table_rows:
                        answer += create_table_row[1]

                    answer += "\n\n"
            else:
                cursor.execute(f"SHOW CREATE TABLE `{self.table_name}`")

            # Fetch all the rows
            rows = cursor.fetchall()

            for row in rows:
                answer += row[1]

            self.cache.set("SQLSchemaExtractor.schema", answer)
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
