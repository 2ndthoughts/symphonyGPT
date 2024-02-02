import mysql.connector
from symphonyGPT.performers.api_extractor.api_extractor import APIExtractor
from symphonyGPT.performers.api_keys import APIKeys
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony
from symphonyGPT.symphony.util import parse_mysql_connection_string


class MySQLSchemaExtractor(APIExtractor):
    def __init__(self, table_name="all"):
        super().__init__()
        # mysql://root:password123@localhost:3306/mydatabase
        self.conn_str = APIKeys().get_api_key("mysql_connection_string")
        # Parse the connection string
        self.mysql_params = parse_mysql_connection_string(self.conn_str)
        self.table_name = table_name

    def perform(self, prompt):
        # ignore prompt, not used

        answer = ""

        # Connect to the MySQL Database
        conn = None
        try:
            conn = mysql.connector.connect(
                host=self.mysql_params['host'],
                user=self.mysql_params['user'],
                password=self.mysql_params['password'],
                database=self.mysql_params['database'],
                port=self.mysql_params['port']
            )
            self.util.debug_print(
                f"Connected to the database {self.mysql_params['database']} on {self.mysql_params['host']} as {self.mysql_params['user']}")
            # Create a cursor object
            cursor = conn.cursor()

            # Executing the DESCRIBE command
            if self.table_name == "all":
                cursor.execute(f"SHOW TABLES")
                rows = cursor.fetchall()
                for row in rows:
                    cursor.execute(f"SHOW CREATE TABLE {row[0]}")
                    create_table_rows = cursor.fetchall()
                    for create_table_row in create_table_rows:
                        answer += create_table_row[1]

                    answer += "\n\n"
            else:
                cursor.execute(f"SHOW CREATE TABLE {self.table_name}")

            # Fetch all the rows
            rows = cursor.fetchall()

            for row in rows:
                answer += row[1]
        finally:
            if conn.is_connected():
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
