import mysql.connector
from symphonyGPT.performers.api_keys import APIKeys
from symphonyGPT.performers.generator.generator import Generator
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony
from symphonyGPT.symphony.symphony_cache import SymphonyCache
from symphonyGPT.symphony.util import parse_mysql_connection_string


class MySQLQueryRunner(Generator):
    def __init__(self, database="use_connection_string"):
        super().__init__()
        self.cache = SymphonyCache("/tmp/symphonyGPT_cache")
        self.set_type("mysql_query_runner")
        self.conn_str = APIKeys().get_api_key("mysql_connection_string")
        # Parse the connection string
        self.mysql_params = parse_mysql_connection_string(self.conn_str)
        self.database = database


    def get_database_name(self):
        database_name = self.mysql_params['database']
        if self.database != "use_connection_string":
            database_name = self.database

        return database_name

    def perform(self, prompt):
        self.util.debug_print("MySQLQueryRunner.perform() called")

        text = self.util.extract_answer(prompt.get_prompt())
        sql = self.util.extract_between(text, "```sql", "```")

        self.util.debug_print(f"extracted sql:\n{sql}")

        self.cache.set("MySQLQueryRunner.sql", sql)
        self.cache.set("MySQLQueryRunner.error", "None") # clear any previous error

        # Connect to the MySQL Database
        conn = None
        try:
            database_name = self.get_database_name()

            conn = mysql.connector.connect(
                host=self.mysql_params['host'],
                user=self.mysql_params['user'],
                password=self.mysql_params['password'],
                database=database_name,
                port=self.mysql_params['port']
            )
            self.util.debug_print(
                f"Connected to the database {database_name} on {self.mysql_params['host']} as {self.mysql_params['user']}")
            # Create a cursor object
            cursor = conn.cursor()

            cursor.execute(sql)

            # Retrieve column headers
            column_headers = [i[0] for i in cursor.description]

            # Fetch all the rows
            rows = cursor.fetchall()

            results = []
            for row in rows:
                row_dict = dict(zip(column_headers, row))
                results.append(row_dict)

            answer = '\n'.join([str(row) for row in results])
            self.cache.set("MySQLQueryRunner.result", answer)
        except mysql.connector.Error as e:
            answer = f"Error: {e}"
            self.cache.set("MySQLQueryRunner.error", f"Error: {e}")
        finally:
            if conn.is_connected():
                conn.close()
                self.util.debug_print("Connection closed")

        self.set_raw_response(answer)


# test main
if __name__ == "__main__":
    with open(
            "../../../../../Library/Application "
            "Support/JetBrains/PyCharmCE2023.3/scratches/sandbox/test_mysql_query_runner.txt", 'r') as file:
        content = file.read()

    prompt = content

    m_test = Movement(
        performers=[MySQLQueryRunner()]
    )

    if "```sql" in prompt:
        run = input("Code detected, would you like to run the code? (y/n): ")
        if run == "y":
            symphony = Symphony(movements=[m_test], null_answer_break=True)
            res = symphony.perform(prompt)
            answer = res[0]["answer"]
            print(f"\n\n{answer}")
        else:
            print("Code not run")
