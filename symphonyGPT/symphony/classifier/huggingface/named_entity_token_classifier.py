import json
from symphonyGPT.symphony.classifier.huggingface.spanmarker_classifier import SpanMarkerClassifier
from symphonyGPT.symphony.prompt import Prompt


class NamedEntityTokenClassifier(SpanMarkerClassifier):

    def __init__(self):
        super().__init__()
        self.model = "tomaarsen/span-marker-mbert-base-multinerd"

    def classify(self, prompt):
        return super()._classify(self.model, prompt)


# test main
if __name__ == "__main__":
    #test_str = "breach of professional duty of care and tortious interference with contract and prospective economic advantage"
    test_str = "Amelia Earhart flew her single engine Lockheed Vega 5B across the Atlantic to Paris."
    classifier = NamedEntityTokenClassifier()
    prompt = Prompt()
    prompt.set_prompt(test_str)
    res = classifier.classify(prompt)
    print(json.dumps(res, indent=4, sort_keys=True))