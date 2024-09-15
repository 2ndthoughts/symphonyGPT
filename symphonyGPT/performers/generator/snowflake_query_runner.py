import mysql.connector
import pandas as pd
import snowflake
from snowflake.connector.compat import urlparse, parse_qs
from sqlalchemy import create_engine, text
import sqlparse

from symphonyGPT.performers.api_extractor.secondthoughts import snowflake_schema_extractor
from symphonyGPT.performers.api_extractor.secondthoughts.snowflake_schema_extractor import SnowflakeSchemaExtractor
from symphonyGPT.performers.api_keys import APIKeys
from symphonyGPT.performers.generator.generator import Generator
from symphonyGPT.symphony.db_util import parse_mysql_connection_string, get_database_name
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony
from symphonyGPT.symphony.symphony_cache import SymphonyCache


class SnowflakeQueryRunner(Generator):
    def __init__(self, database="use_connection_string", connection_string=None):
        super().__init__()
        self.cache = SymphonyCache("/tmp/symphonyGPT_cache")

        # snowflake://my_user:my_password@xy12345.us-east-1.aws/?warehouse=my_warehouse&db=my_database&schema=my_schema&role=my_role
        if connection_string is not None:
            self.conn_str = connection_string
        else:
            self.conn_str = APIKeys().get_api_key("snowflake_connection_string")

        # Parse the connection string
        parsed_url = urlparse(self.conn_str)

        assert parsed_url.username is not None, "Username is required for Snowflake connection"
        assert parsed_url.password is not None, "Password is required for Snowflake connection"

        # Extract user and password
        self.user = parsed_url.username
        self.password = parsed_url.password

        assert parsed_url.hostname is not None, "Account is required for Snowflake connection"

        # Extract account from the netloc
        self.account = parsed_url.hostname

        # Extract query parameters (warehouse, database, schema, role)
        query_params = parse_qs(parsed_url.query)

        self.warehouse = query_params.get('warehouse', [None])[0]

        if database == "use_connection_string":
            self.database = query_params.get('db', [None])[0]
        else:
            self.database = database

        self.schema = query_params.get('schema', [None])[0]
        self.role = query_params.get('role', [None])[0]

    def get_connection(self):
        return snowflake.connector.connect(
            user=self.user,
            password=self.password,
            account=self.account,
            warehouse=self.warehouse,
            database=self.database,
            schema=self.schema,
            role=self.role,
            login_timeout=60,  # Timeout for login (seconds)
            network_timeout=600  # Timeout for queries (seconds)
        )

    def is_database_exists(self, database_name):
        # Replace these with your connection details

        # Connect to the MySQL Database
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            for db in databases:
                if db[1] == database_name:
                    print(f"Database {database_name} exists")
                    return True

            print(f"Database {database_name} does not exist")
            cursor.close()
            return False
        except mysql.connector.Error as e:
            print(f"Error: {e}")
        finally:
            if snowflake_schema_extractor.is_connected(conn):
                conn.close()


    def perform(self, prompt):
        cursor = None
        self.util.debug_print("SQLQueryRunner.perform() called")

        sql_text = self.util.extract_answer(prompt.get_prompt())
        sql = self.util.extract_between(sql_text, "```sql", "```")
        if sql is None:
            sql = sql_text

        self.util.debug_print(f"extracted sql:\n{sql}")

        self.cache.set("SQLQueryRunner.sql", sql)
        self.cache.set("SQLQueryRunner.error", "None")  # clear any previous error

        # Connect to the MySQL Database
        conn = None
        try:
            database_name = self.database
            conn = self.get_connection()
            self.util.debug_print(
                f"Connected to the database '{database_name}' on {self.account} as {self.user}")
            # Create a cursor object
            cursor = conn.cursor()
            cursor.execute("ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = 600") # set query timeout to 10 minutes for testing

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

            if answer == "":
                answer = "No results returned"

            self.cache.set("SQLQueryRunner.result", answer)
        except snowflake.connector.errors.ProgrammingError as e:
            # Handle specific SQL errors
            answer = f"SQL ProgrammingError: {e}"
            self.cache.set("SQLQueryRunner.error", f"Error: {e}")
        except snowflake.connector.errors.Error as e:
            # Handle other Snowflake connector errors
            answer = f"Error: {e}"
            self.cache.set("SQLQueryRunner.error", f"Error: {e}")
        except Exception as e:
            # Handle any other errors (network issues, etc.)
            answer = f"An unexpected error occurred: {e}"
            self.cache.set("SQLQueryRunner.error", f"Error: {e}")
        finally:
            cursor.close()
            conn.close()
            self.util.debug_print("Connection closed")

        self.set_raw_response(answer)


# test main
if __name__ == "__main__":
    with open(
            "../../../../../Library/Application "
            "Support/JetBrains/PyCharmCE2024.2/scratches/sandbox/test_snowflake_query_runner.txt", 'r') as file:
        content = file.read()

    prompt = content

    m_test = Movement(
        performers=[SnowflakeQueryRunner(connection_string='snowflake://my_user:my_password@hwb17013.us-east-1/?warehouse=COMPUTE_WH&db=SNOWFLAKE_SAMPLE_DATA&schema=TPCDS_SF100TCL')]
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
