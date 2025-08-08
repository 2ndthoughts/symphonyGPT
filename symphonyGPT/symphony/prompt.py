import json


class Prompt:
    def __init__(self):
        self.prompt = None
        self.system_prompt = "You are a helpful assistant."
        self.assistant_prompt = None
        self.previous_prompt = None
        self.previous_response = None
        self.preferences = None
        self.outcome_strategy = None
        self.append_conversation = True
        self.classifications = json.loads("{}")

    def set_append_conversation(self, append):
        self.append_conversation = append

    def is_append_conversation(self):
        return self.append_conversation

    def set_previous_prompt(self, prompt):
        self.previous_prompt = prompt

    def set_previous_response(self, response):
        self.previous_response = response

    # set system prompt
    def set_system_prompt(self, prompt):
        self.system_prompt = prompt

    # sets user prompt
    def set_prompt(self, prompt):
        self.prompt = prompt

    # sets assistant prompt
    def set_assistant_prompt(self, prompt):
        self.assistant_prompt = prompt

    def get_prompt(self):
        return self.prompt

    def set_classification(self, classifier, topics):
        self.classifications[classifier] = topics

    def get_classification(self, classifier):
        return self.classifications[classifier]

    def get_classifications(self):
        return self.classifications
