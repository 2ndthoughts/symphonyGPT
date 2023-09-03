import json
from symphonyGPT.symphony.outcome_strategy.outcome_strategy import OutcomeStrategy


class ShortestAnswer(OutcomeStrategy):

    def __init__(self, format=None):
        super().__init__(format)
        self.answer_length = 0

    def update_meta_data(self, response_raw_text):
        self.answer_length = len(response_raw_text)
        json_obj = json.loads("{}")
        json_obj["length"] = self.answer_length
        return json_obj

    def get_outcome_prompt(self):
        return "Parse the following array of JSON objects and select the one with the smallest 'length' attribute"

    def process_outcome(self, conductor, prompt, response_array=None):
        return super().process_stat_outcome('min', 'length', response_array)