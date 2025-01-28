
class APIKeys():
    def __init__(self):
        self.api_keys = {

        }

    def get_api_key(self, keyname):
        if keyname not in self.api_keys or self.api_keys[keyname] is None:
            raise Exception(f"API key '{keyname}' not found, please update the file performers/api_keys.py")

        return self.api_keys[keyname]
