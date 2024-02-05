from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from symphonyGPT.symphony.classifier.classifier import Classifier


class AutoTokenClassifier(Classifier):

    def __init__(self, classification_type_str=None, from_tf=False):
        super().__init__(classification_type_str)
        self.classification_type_str = "token-classification"  # default to text classifier
        self.from_tf = from_tf

    def _classify(self, classifier_model, prompt):
        tokenizer = AutoTokenizer.from_pretrained(self.model)
        model = AutoModelForTokenClassification.from_pretrained(self.model, from_tf=self.from_tf)

        pipe = pipeline("token-classification", model=model, tokenizer=tokenizer,
                        aggregation_strategy="simple")  # pass device=0 if using gpu
        topics = pipe(prompt.get_prompt())
        prompt.set_classification(f"{self.__class__.__name__}", topics)
        return topics
