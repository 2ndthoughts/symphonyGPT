
class APIKeys():
    def __init__(self):
        self.api_keys = {
            'openai': None, # get it from https://platform.openai.com/account/api-keys after creating account
            'courtlistener': None # get it from https://www.courtlistener.com/help/api/rest/#permissions after
                                  # creating account
        }

    def get_api_key(self, keyname):
        if keyname not in self.api_keys or self.api_keys[keyname] is None:
            raise Exception(f"API key '{keyname}' not found, please update the file performers/api_keys.py")

        return self.api_keys[keyname]
