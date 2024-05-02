import mysql.connector
import pandas as pd
from sqlalchemy import create_engine, text
import sqlparse

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
        self.max_allowed_packet = 1073741824

    def load_excel(self, excel_file, dataset_name):
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
            sql = text(f"SET GLOBAL max_allowed_packet={self.max_allowed_packet};")
            connection.execute(sql)
        engine.dispose()

        # SQLAlchemy engine for MySQL connection
        engine = create_engine(f'mysql+mysqlconnector://{username}:{password}@{host}/{dataset_name}')

        # Read the Excel file
        xls = pd.ExcelFile(excel_file)

        # Process each sheet
        for sheet_name in xls.sheet_names:
            # Load sheet into DataFrame without headers to evaluate all rows
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)

            print(f"\nProcessing sheet: {sheet_name} ...")

            # Detect the header row: the first row that spans the most columns that contain a value
            max_count = df.apply(lambda x: x.last_valid_index(), axis=1).max()
            header_candidates = df.apply(lambda x: x.last_valid_index(), axis=1)
            header_row = header_candidates[header_candidates == max_count].index[0]

            # Re-load the sheet using the detected header row
            try:
                df = pd.read_excel(xls, sheet_name=sheet_name, header=header_row)

                # Filter columns to include only those that have at least some data
                non_empty_columns = df.columns[df.notna().any()].tolist()
                df = df[non_empty_columns]

                # print(df.head())

                # Write to MySQL, using sheet name as table name
                df.to_sql(name=sheet_name, con=engine, if_exists='replace', index=False)
            except Exception as e:
                print(f"Error processing sheet '{sheet_name}': {e}")

    def load_mysql_dump(self, dump_file, dataset_name):
        # Replace these with your connection details
        username = self.mysql_params['user']
        password = self.mysql_params['password']
        host = self.mysql_params['host']

        db = mysql.connector.connect(
            host=host,
            user=username,
            password=password
        )

        # Creating a cursor object using the cursor() method
        cursor = db.cursor()

        # Executing an SQL command
        cursor.execute(f"SET GLOBAL max_allowed_packet={self.max_allowed_packet};")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{dataset_name}`")
        cursor.execute(f"USE `{dataset_name}`")
        db.commit()

        # Open the dump file
        with open(dump_file, 'r', encoding='utf-8') as file:
            # Read the entire file in one go
            sql_file = file.read()

            # Split the file into separate statements
            sql_commands = sqlparse.split(sql_file)

            # Cursor to execute all SQL commands
            cursor = db.cursor()

            try:
                for command in sql_commands:
                    print(f"Executing command: {command}")
                    # Check if the command is not just whitespace
                    if command.strip():
                        cursor.execute(command)

                db.commit()  # Commit the transaction
                #print("MySQL Dump file has been loaded successfully.")
            except mysql.connector.Error as err:
                db.rollback()  # Rollback in case of error
                print(f"Failed executing command: {err}")
            finally:
                cursor.close()

        # Close the database connection
        db.close()

    def load_csv(self, csv_file, dataset_name):
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
            sql = text(f"SET GLOBAL max_allowed_packet={self.max_allowed_packet};")
            connection.execute(sql)
        engine.dispose()

        # if the CSV file is not UTF-8 encoded, specify the encoding, else loop back and try 'latin1'
        for encoding in ['utf-8', 'latin1']:
            try:
                # Specify the sheet name or its index as sheet_name parameter
                df = pd.read_csv(csv_file, header=0, index_col=False, encoding=encoding, low_memory=False)

                # SQLAlchemy engine for MySQL connection
                engine = create_engine(f'mysql+mysqlconnector://{username}:{password}@{host}/{dataset_name}')

                # Load data into MySQL - replace 'your_table_name' with your actual table name
                # The 'if_exists' parameter defines what to do if the table already exists:
                # 'replace', 'append', or 'fail'
                df.to_sql(dataset_name, con=engine, index=False, if_exists='append')

                break # no errors, so break out of the loop
            except Exception as e:
                print(f"Error loading CSV file: {e}")
                # if the Exception contains the words "'utf-8' codec" then try 'latin1' encoding
                if 'utf-8' in str(e):
                    print("Trying 'latin1' encoding ...")
                    continue

    def drop_database(self, database_name):
        # Replace these with your connection details
        username = self.mysql_params['user']
        password = self.mysql_params['password']
        host = self.mysql_params['host']

        # use dataset_name as database name, if it doesnt exist, create the database using the dataset name
        # print(f"Dropping dataset '{dataset_name}'")
        engine = create_engine(f'mysql+mysqlconnector://{username}:{password}@{host}/')
        with engine.connect() as connection:
            sql = text(f"DROP DATABASE IF EXISTS `{database_name}`")
            connection.execute(sql)
        engine.dispose()

    def perform(self, prompt):
        self.util.debug_print("MySQLQueryRunner.perform() called")

        sql_text = self.util.extract_answer(prompt.get_prompt())
        sql = self.util.extract_between(sql_text, "```sql", "```")
        if sql is None:
            sql = sql_text

        self.util.debug_print(f"extracted sql:\n{sql}")

        self.cache.set("MySQLQueryRunner.sql", sql)
        self.cache.set("MySQLQueryRunner.error", "None")  # clear any previous error

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
            # remove ONLY_FULL_GROUP_BY from sql_mode for this session
            cursor.execute("SET SESSION sql_mode = REPLACE(@@sql_mode, 'ONLY_FULL_GROUP_BY', '');")
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
