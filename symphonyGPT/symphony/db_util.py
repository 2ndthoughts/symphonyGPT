import re


class DBUtil:
    def __init__(self):
        pass

def get_database_name(mysql_params, database):
    database_name = "mysql"

    if database != "use_connection_string":
        database_name = database
    # if database is not set, use the one in the connection string, if there is none in the connection string, use 'mysql'
    elif 'database' not in mysql_params or mysql_params['database'] is None:
        return "mysql"
    elif 'database' in mysql_params:
        database_name = mysql_params['database']

    return database_name

def parse_mysql_connection_string(conn_str):
    pattern = re.compile(
        r'mysql://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>[^/]+)/(?P<database>.+)'
    )
    match = pattern.match(conn_str)
    if match:
        return match.groupdict()
    else:
        # if partial match, return partial dict, database name is optional
        pattern = re.compile(
            r'mysql://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>[^/]+)'
        )
        match = pattern.match(conn_str)
        if match:
            return match.groupdict()
        else:
            raise ValueError("Invalid MySQL connection string")