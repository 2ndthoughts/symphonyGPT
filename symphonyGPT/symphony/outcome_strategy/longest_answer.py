from symphonyGPT.symphony.outcome_strategy.shortest_answer import ShortestAnswer


class LongestAnswerAI(ShortestAnswer):

    def __init__(self, format=None):
        super().__init__(format)

    def update_meta_data(self, response_raw_text):
        return super().update_meta_data(response_raw_text)

    def get_outcome_prompt(self):
        return "Parse the following array of JSON objects and select the one with the biggest 'length' attribute"

    def process_outcome(self, conductor, prompt, response_array=None):
        return super().process_stat_outcome('max', 'length', response_array)