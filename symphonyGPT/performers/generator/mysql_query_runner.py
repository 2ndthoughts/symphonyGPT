import mysql.connector
import pandas as pd
from sqlalchemy import create_engine, text

from symphonyGPT.performers.api_keys import APIKeys
from symphonyGPT.performers.generator.generator import Generator
from symphonyGPT.symphony.db_util import parse_mysql_connection_string, get_database_name
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony
from symphonyGPT.symphony.symphony_cache import SymphonyCache


class MySQLQueryRunner(Generator):
    def __init__(self, database="use_connection_string"):
        super().__init__()
        self.cache = SymphonyCache("/tmp/symphonyGPT_cache")
        self.set_type("mysql_query_runner")
        self.conn_str = APIKeys().get_api_key("mysql_connection_string")
        # Parse the connection string
        self.mysql_params = parse_mysql_connection_string(self.conn_str)
        self.database = database

    def load_csv_to_db(self, csv_file, dataset_name):
        # Replace these with your connection details
        username = self.mysql_params['user']
        password = self.mysql_params['password']
        host = self.mysql_params['host']

        # use dataset_name as database name, if it doesnt exist, create the database using the dataset name
        # print(f"Creating dataset '{dataset_name}'")
        engine = create_engine(f'mysql+mysqlconnector://{username}:{password}@{host}/')
        with engine.connect() as connection:
            sql = text(f"CREATE DATABASE IF NOT EXISTS `{dataset_name}`")
            connection.execute(sql)
        engine.dispose()

        # Specify the sheet name or its index as sheet_name parameter
        df = pd.read_csv(csv_file, header=0, index_col=False, encoding='utf-8', low_memory=False)

        # SQLAlchemy engine for MySQL connection
        engine = create_engine(f'mysql+mysqlconnector://{username}:{password}@{host}/{dataset_name}')

        # Load data into MySQL - replace 'your_table_name' with your actual table name
        # The 'if_exists' parameter defines what to do if the table already exists:
        # 'replace', 'append', or 'fail'
        df.to_sql(dataset_name, con=engine, index=False, if_exists='append')

    def perform(self, prompt):
        self.util.debug_print("MySQLQueryRunner.perform() called")

        sql_text = self.util.extract_answer(prompt.get_prompt())
        sql = self.util.extract_between(sql_text, "```sql", "```")
        if sql is None:
            sql = sql_text

        self.util.debug_print(f"extracted sql:\n{sql}")

        self.cache.set("MySQLQueryRunner.sql", sql)
        self.cache.set("MySQLQueryRunner.error", "None") # clear any previous error

        # Connect to the MySQL Database
        conn = None
        try:
            database_name = get_database_name(self.mysql_params, self.database)

            conn = mysql.connector.connect(
                host=self.mysql_params['host'],
                user=self.mysql_params['user'],
                password=self.mysql_params['password'],
                database=database_name,
                port=self.mysql_params['port']
            )
            self.util.debug_print(
                f"Connected to the database '{database_name}' on {self.mysql_params['host']} as {self.mysql_params['user']}")
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
