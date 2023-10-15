import chromadb
from symphonyGPT.symphony.prompt import Prompt
from symphonyGPT.symphony.util import Util


class Performer:
    def __init__(self):
        self.type = "performer"
        self.__response_raw_text = None
        self.util = Util()
        self.db_client = chromadb.Client()
        self.collection = self.db_client.get_or_create_collection(name=f"p_{self.__class__.__name__}")

    def perform(self, prompt: Prompt):
        raise NotImplementedError("Subclass must implement abstract method")

    def set_type(self, type):
        self.type = type

    def get_type(self):
        return self.type

    def set_raw_response(self, response_raw_text):
        self.__response_raw_text = response_raw_text

    def get_raw_response(self):
        return self.__response_raw_text

    def add_raw_response_text(self, response_raw_text):
        if self.__response_raw_text is None:
            self.__response_raw_text = response_raw_text
        else:
            self.__response_raw_text = f"{self.__response_raw_text}\n{response_raw_text}"

    def who_am_i(self):
        return self.__class__.__name__
