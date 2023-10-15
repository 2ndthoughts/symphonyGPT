import openai

from symphonyGPT.performers.api_keys import APIKeys
from symphonyGPT.performers.language_model.language_model_performer import LanguageModelPerformer


class OpenAIPerformer(LanguageModelPerformer):
    openai.api_key = APIKeys().get_api_key("openai")

    def __init__(self):
        super().__init__()
        self.response_raw_text = None

    def who_am_i(self):
        return f"{self.__class__.__name__} {self.get_model_attributes()}"