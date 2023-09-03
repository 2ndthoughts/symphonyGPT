import json

from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from symphonyGPT.symphony.classifier.autotoken_classifier import AutoTokenClassifier
from symphonyGPT.symphony.prompt import Prompt
from symphonyGPT.symphony.util import Util


class BiomedicalNerAllTokenClassifier(AutoTokenClassifier):

    def __init__(self):
        super().__init__("token-classification")
        self.model = "d4data/biomedical-ner-all"

    def classify(self, prompt):
        return super()._classify(self.model, prompt)


# test main
if __name__ == "__main__":
    classifier = BiomedicalNerAllTokenClassifier()
    prompt = Prompt()
    prompt.set_prompt("does Ivermectin reduce covid-19 symptoms")
    # prompt.set_prompt("does Rapamycin reduce Alzheimer's disease")
    res = classifier.classify(prompt)
    print(json.dumps(res, indent=4, sort_keys=True, default=Util.serialize_float32))
