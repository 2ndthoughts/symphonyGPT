import json
from symphonyGPT.symphony.classifier.autotoken_classifier import AutoTokenClassifier
from symphonyGPT.symphony.prompt import Prompt
from symphonyGPT.symphony.util import Util


class KeyphraseExtractionTokenClassifier(AutoTokenClassifier):

    def __init__(self):
        super().__init__("token-classification")
        self.model = "ml6team/keyphrase-extraction-kbir-kpcrowd"

    def classify(self, prompt):
        return super()._classify(self.model, prompt)


# test main
if __name__ == "__main__":
    test_str = ("breach of professional duty of care and tortious interference with contract and prospective economic advantage")
    # test_str = "list cases related to a company director breaching fiduciary duty during company merger"
    classifier = KeyphraseExtractionTokenClassifier()
    prompt = Prompt()
    prompt.set_prompt(test_str)
    res = classifier.classify(prompt)
    print(json.dumps(res, indent=4, sort_keys=True, default=Util.serialize_float32))
