import openai

from symphonyGPT.performers.api_keys import APIKeys
from symphonyGPT.performers.language_model.language_model_performer import LanguageModelPerformer


class XAIPerformer(LanguageModelPerformer):
    openai.api_key = APIKeys().get_api_key("xai")
    openai.base_url = "https://api.x.ai/v1"

    def __init__(self):
        super().__init__()

    def who_am_i(self):
        return f"{self.__class__.__name__} {self.get_model_attributes()}"