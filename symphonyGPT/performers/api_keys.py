
class APIKeys():
    def __init__(self):
        self.api_keys = {
            'openai': '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', # get it from https://platform.openai.com/account/api-keys after creating account
            'xai': 'xai-7WAFR0muXcRisHgA29hB3RCNOAx1DM3v0cQ5TN94NynAGYKbvWg8f2QTfTTDX7FENwKUQaHv782Yoq1y',

            'courtlistener': '357291dc2928178a4ca37933a71c00a0327a2d0a', # get it from https://www.courtlistener.com/help/api/rest/#permissions after creating account
            # DL75032 Blastah99!!
            'wikimedia': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJmMzA5MTViMzllNmRjY2U0NTljMDA5MWUyNDQ0ZjY0NCIsImp0aSI6ImExMTg2N2YzN2E5MjYyYjYxNDYxZmNkN2RiM2RkNmZhNTJlZDdhOGQwMDQxOTgwNmEwZDVmNjVhOTIwMmU4MzBhMjc2YTZiYjAwYTJkYzdiIiwiaWF0IjoxNzA0Njk1MzQwLjU4NzIyMSwibmJmIjoxNzA0Njk1MzQwLjU4NzIyNSwiZXhwIjoxNzA0NzA5NzQwLjU4Mzk2OCwic3ViIjoiNzQ2NzUwMDIiLCJpc3MiOiJodHRwczovL21ldGEud2lraW1lZGlhLm9yZyIsInJhdGVsaW1pdCI6eyJyZXF1ZXN0c19wZXJfdW5pdCI6NTAwMCwidW5pdCI6IkhPVVIifSwic2NvcGVzIjpbImJhc2ljIl19.YWk5h83dOc20C09eHRNjC7gn2PlkN_eQnwAyI9lujW2ha4dgM5iqaNmEj-y4POXEUEmrUucQALxQ96KRVWcEd_eNfKHTr720QuyDhYowRcRsaexVbqqRMELrxXeocvoGENZRH6E7ck-oVQbbOAFn7kd6HKF5P_N8qthQ3KOcWoH7YMk3UEr0Y0pSdQciqNtNdIOWkRU18J0f0aS7z8jXfEPJiOTRUdR3ky41CGbGrnCkacObw0W1-ZMooOl8XuE82BTdhYbZTCTaAGpR6IGRJVajJQ6RIS6O-317NEdvRUuhxg6MDMJ-mLeumT-Tqw0uqs7k8CWzcH9fidk-jjGRXyg7_SY7XjV0qZv8FeEnW1HH-IgwNL4MczeQNtzixpeOIhD4dgy0D1QH-5uk8hp7GkBvD3WCCPlp6lNgJTDRbt61aA--z-9hCMjlAyUtiH5sEubpH1t7VXgZUz0fkD2SioMY1R5vKlJkUYEE_sBoWYUc-_dbda3nmvHL802GnuGzHDOlxX-ejrxCQSOsEvlhH2ESz0RNSv0MHepvOpxowv2QQRwkJkQlP9U6NmlBMfb_Vxa7vSbiN9YZQhSMD51Y5oXlHpT-ekDprHcBSROjxtBJykJFtB1cQ-whyrV6vsvW2YgeTZaXYnodI9vrtqBv-E6aYjXk284Pl5BUYQDvYxM',
            'gemini': 'AIzaSyC46H22MjmK9Sv5dmlUJPz_LRIkheCM6NQ',

            # mysql
            'mysql_connection_string': 'mysql://root:Lucky*888@localhost:3306/',

            # snowflake
            'snowflake_connection_string': 'snowflake://2ndthoughts:Lucky*888@hwb17013.us-east-1/?warehouse=COMPUTE_WH&db=SNOWFLAKE_SAMPLE_DATA&schema=TPCDS_SF100TCL',

            'huggingface': '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',
            'orchestra_admin': 'seq888',
            'sequitur': 'uezg vbbq hrfc csst' # seq4me!!
        }

    def get_api_key(self, keyname):
        if keyname not in self.api_keys or self.api_keys[keyname] is None:
            raise Exception(f"API key '{keyname}' not found, please update the file performers/api_keys.py")

        return self.api_keys[keyname]
