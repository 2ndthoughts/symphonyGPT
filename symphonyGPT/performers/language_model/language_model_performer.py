import json
from symphonyGPT.performers.performer import Performer


class LanguageModelPerformer(Performer):

    def __init__(self):
        super().__init__()
        self.set_type("language_model")
        self.model_attributes = json.loads("{}")
        self.response_raw_text = None

    def format_response(self, response):
        return self.get_model_attribute("model") + ":\n" + response + "\n"

    def set_model_attribute(self, key, value):
        self.model_attributes[key] = value

    def get_model_attribute(self, key):
        return self.model_attributes[key]

    def get_model_attributes(self):
        return self.model_attributes
