import openai
from symphonyGPT.performers.language_model.language_model_performer import LanguageModelPerformer


class OpenAIPerformer(LanguageModelPerformer):

    openai.api_key = "<enter your openai api key here>" # do not check in your api key !!

    def __init__(self):
        super().__init__()
        if openai.api_key == "<enter your openai api key here>":
            raise Exception("You must enter your openai api key in ../performers/openai/openai_performer.py")
        self.response_raw_text = None

    def who_am_i(self):
        return f"{self.__class__.__name__} {self.get_model_attributes()}"