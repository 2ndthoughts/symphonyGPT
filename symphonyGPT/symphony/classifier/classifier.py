import os
from transformers import pipeline
from symphonyGPT.symphony.util import Util


class Classifier:

    def __init__(self, classification_type_str=None):
        os.environ["TOKENIZERS_PARALLELISM"] = "true" # to avoid dead lock warning
        self.model = None
        self.tokenizer = None
        self.device = None
        self.util = Util()
        self.classification_type_str = "text-classification" # default to text classifier
        if classification_type_str is not None:
            self.classification_type_str = classification_type_str

    def _classify(self, classifier_model, prompt):
        pipe = pipeline(self.classification_type_str, classifier_model)
        topics = pipe(prompt.get_prompt())
        prompt.set_classification(f"{self.__class__.__name__}",  topics)
        return topics