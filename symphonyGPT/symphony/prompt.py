import json


class Prompt:
    def __init__(self):
        self.prompt = None
        self.preferences = None
        self.outcome_strategy = None
        self.classifications = json.loads("{}")

    def set_prompt(self, prompt):
        self.prompt = prompt

    def get_prompt(self):
        return self.prompt

    def set_classification(self, classifier, topics):
        self.classifications[classifier] = topics

    def get_classification(self, classifier):
        return self.classifications[classifier]

    def get_classifications(self):
        return self.classifications
