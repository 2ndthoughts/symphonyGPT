import logging
import sys

import mysql.connector
import snowflake
from snowflake.connector.compat import urlparse, parse_qs

from symphonyGPT.performers.api_extractor.api_extractor import APIExtractor
from symphonyGPT.performers.api_keys import APIKeys
from symphonyGPT.symphony.db_util import parse_mysql_connection_string, get_database_name
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony
from symphonyGPT.symphony.symphony_cache import SymphonyCache


def create_create_table_query(table_name, columns):
    # Start constructing the CREATE TABLE statement
    create_table_statement = f"CREATE TABLE {table_name} (\n"

    # Loop through the columns to append column definitions
    for column in columns:
        column_name = column[0]  # Column name
        column_type = column[1]  # Data type
        is_nullable = "NULL" if column[3] == "Y" else "NOT NULL"  # Nullability

        # Add the column definition to the CREATE TABLE statement
        create_table_statement += f"    {column_name} {column_type} {is_nullable},\n"

    # Remove the last comma and newline, and close the statement
    create_table_statement = create_table_statement.rstrip(",\n") + "\n);"

    return create_table_statement

def is_connected(conn):
    try:
        # Execute a lightweight query
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()  # Fetch the result to ensure query completion
        cur.close()
        return True  # If no error, connection is active
    except snowflake.connector.errors.Error as e:
        logging.error(f"Connection error: {e}")
        return False  # If there's an error, the connection is inactive


class SnowflakeSchemaExtractor(APIExtractor):
    def __init__(self, database="use_connection_string", table_name="all", connection_string=None):
        super().__init__()
        self.cache = SymphonyCache("/tmp/symphonyGPT_cache")

        self.table_name = table_name
        
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


    def perform(self, prompt):
        # ignore prompt, not used

        answer = ""

        # Connect to the MySQL Database
        conn = None
        try:
            # reset the cache for errors
            self.cache.delete("SQLSchemaExtractor.error")
            database_name = self.database

            try:
                conn = snowflake.connector.connect(
                    user=self.user,
                    password=self.password,
                    account=self.account,
                    warehouse=self.warehouse,
                    database=self.database,
                    schema=self.schema,
                    role=self.role
                )
            except Exception as e:
                error_str = f"Failed to connect to the database: {database_name}, error: {e}"
                print(error_str, file=sys.stderr)
                self.cache.set("SQLSchemaExtractor.error", error_str)
                return

            self.cache.set("SQLSchemaExtractor.user", self.user)
            self.cache.set("SQLSchemaExtractor.account", self.account)
            self.cache.set("SQLSchemaExtractor.warehouse", self.warehouse)
            self.cache.set("SQLSchemaExtractor.database", database_name)
            self.cache.set("SQLSchemaExtractor.schema", self.schema)
            self.cache.set("SQLSchemaExtractor.role", self.role)


            self.util.debug_print(
                f"Connected to the database '{database_name}' on {self.account} as {self.user}")
            # Create a cursor object
            cursor = conn.cursor()

            # Executing the DESCRIBE command
            if self.table_name == "all":
                cursor.execute(f"SHOW TABLES")
                rows = cursor.fetchall()
                for row in rows:
                    table_name = row[1]
                    cursor.execute(f"DESCRIBE TABLE {table_name}") # table name in index 1
                    columns = cursor.fetchall()

                    create_table_query = create_create_table_query(row[1], columns)
                    answer += create_table_query + "\n"

                    # get table stats
                    # table_stats_query = (f"SELECT COUNT(*) AS record_count, AVG(LENGTH(TO_JSON(OBJECT_CONSTRUCT(*)))) AS "
                    #                      f"average_record_size, MIN(LENGTH(TO_JSON(OBJECT_CONSTRUCT(*)))) AS min_record_size, "
                    #                      f"MAX(LENGTH(TO_JSON(OBJECT_CONSTRUCT(*)))) AS max_record_size FROM {table_name};")
                    #
                    # try:
                    #     cursor.execute(table_stats_query)
                    #     table_stats = cursor.fetchall()
                    #     answer += f"\nRecord Count: {table_stats[0][0]}\n"
                    #     answer += f"Average Record Size: {table_stats[0][1]}\n"
                    #     answer += f"Min Record Size: {table_stats[0][2]}\n"
                    #     answer += f"Max Record Size: {table_stats[0][3]}\n\n"
                    # except Exception as e:
                    #     self.util.debug_print(f"Error fetching table stats: {e}")

                cursor.close()
            else:
                cursor.execute(f"DESCRIBE TABLE {self.table_name}")
                columns = cursor.fetchall()
                create_table_query = create_create_table_query(self.table_name, columns)
                answer += create_table_query
                cursor.close()

            self.cache.set("SQLSchemaExtractor.schema", answer)
        finally:
            # check if conn is connected, then close it
            if conn is not None and is_connected(conn):
                conn.close()
                self.util.debug_print("Connection closed")

        self.set_raw_response(answer)


# test main
if __name__ == "__main__":
    m_test = Movement(
        performers=[SnowflakeSchemaExtractor(connection_string='snowflake://my_user:my_password@hwb17013.us-east-1/?warehouse=COMPUTE_WH&db=SNOWFLAKE_SAMPLE_DATA&schema=TPCDS_SF100TCL', table_name="all")]
    )
    symphony = Symphony(movements=[m_test], null_answer_break=True)
    res = symphony.perform("blah blah blah")

    print(res[0]["answer"])
