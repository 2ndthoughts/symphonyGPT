import json
import concurrent.futures

import chromadb

from symphonyGPT.performers.language_model.openai_performers.gpt_35_turbo_0301 import Gpt35Turbo0301
from symphonyGPT.symphony.prompt import Prompt
from symphonyGPT.symphony.util import Util


class Movement:

    def __init__(self, prompt_str=None, performers=None, outcome_strategy=None, conductor=None, prompt_classifier=None):
        self.concurrent = True  # 6 times faster but requires high throughput with API

        self.classifier = prompt_classifier
        self.util = Util()
        self.prompt = Prompt()
        if prompt_str is not None:
            self.prompt.set_prompt(prompt_str)

        if performers is None:
            performers = []

        if conductor is None:
            self.conductor = Gpt35Turbo0301()  # default to GPT-3 175B

        self.performers = performers
        self.response_array = []
        self.count = 1
        self.outcome_strategy = outcome_strategy
        self.conductor = conductor
        self.db_client = chromadb.Client()
        self.collection = self.db_client.get_or_create_collection(name=f"m_{self.__class__.__name__}")

    def worker(self, performer, current_response):
        self.util.debug_print(
            f"Movement.worker() performer who_am_i: {performer.who_am_i()}")
        return self.process_output(current_response, performer)

    def perform(self, prompt_str=None, current_response=None, conductor=None):
        if prompt_str is None:
            raise Exception("Movement.perform() requires a prompt string")  # cannot move forward if no prompt string

        # self.prompt is a Prompt class object
        # if self.prompt.get_prompt() is None:
        self.prompt.set_prompt(prompt_str)  # set the prompt_str into prompt object
        # if this is the first movement ==  None
        self.util.debug_print(f"Movement.perform() prompt: {self.prompt.get_prompt()}")

        if conductor is None:
            conductor = self.conductor

        # classify the prompt before running through performers
        if self.classifier is not None:
            for classifier in self.classifier:
                classifier.classify(self.prompt)  # pass the object to be classified
            # output the classification for the prompt
            self.util.debug_print(f"Movement.perform() prompt classified: {self.prompt.get_classifications()}")

        if self.concurrent is True:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(self.worker, performer, current_response): performer for performer in
                           self.performers}
                for future in concurrent.futures.as_completed(futures):
                    future.result()  # here result is the return value of update_meta_data_by_outcome_strategy
        else:
            for performer in self.performers:
                self.util.debug_print(
                    f"Movement.perform() performer who_am_i: {performer.who_am_i()}")
                self.process_output(current_response, performer)

        if self.outcome_strategy is not None:
            self.util.debug_print(
                f"Movement.perform() outcome_strategy: {self.outcome_strategy.__class__.__name__} {self.outcome_strategy.get_format()}")
            return self.outcome_strategy.process_outcome(conductor, self.prompt, self.response_array)
        else:
            return self.response_array

    def process_output(self, current_response, performer):
        # perform deposits results in performer.__response_raw_text
        performer.perform(self.prompt)

        outcome_meta = json.loads("{}")
        response_raw_text = performer.get_raw_response()
        if self.outcome_strategy is not None:
            outcome_meta = self.outcome_strategy.update_meta_data(response_raw_text)

        outcome_meta["model"] = performer.__class__.__name__
        outcome_meta["answer"] = response_raw_text
        self.response_array.append(outcome_meta)

        self.count += 1
