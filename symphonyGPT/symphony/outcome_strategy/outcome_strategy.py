import json
from symphonyGPT.symphony.util import Util


# directly use this base class in movement config if you just want to pass through the response
# and strip out the answer from json
class OutcomeStrategy:
    def __init__(self, format=None):
        self.format = format
        self.util = Util()

    def update_meta_data(self, response_raw_text):
        return json.loads("{}")

    def get_outcome_prompt(self):
        pass

    def get_format(self):
        return self.format

    def process_outcome(self, conductor, prompt, response_array=None):
        # pass through as default
        return self.format_answer(response_array)

    def process_stat_outcome(self, stat="max", stat_label=None, response_array=None, stat_value=None):
        json_str = json.dumps(response_array, indent=4)
        self.util.debug_print(json_str)

        answer = None
        if stat == "max":
            answer = max(response_array, key=lambda response_array: response_array[stat_label])
        elif stat == "min":
            answer = min(response_array, key=lambda response_array: response_array[stat_label])
        elif stat == "filter":
            answer = list(filter(lambda item: item[stat_label] == stat_value, response_array))
        elif stat == "max_filter":
            # get the max
            max_answer = max(response_array, key=lambda response_array: response_array[stat_label])
            max_value = max_answer[stat_label]
            answer = list(filter(lambda item: item[stat_label] == max_value, response_array))

        if answer is None:
            return "No answer found"

        return self.format_answer(answer)

    def format_answer(self, answer):
        # if the format is answer_only, then return the answer only
        if self.get_format() == "answer_only":
            return self.util.extract_answer(answer)
        else:
            if len(answer) == 0:
                return "No answer found"
            else:
                return answer
