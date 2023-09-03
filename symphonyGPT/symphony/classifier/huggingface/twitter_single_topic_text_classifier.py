from symphonyGPT.symphony.classifier.classifier import Classifier


class TwitterSingleTopicTextClassifier(Classifier):

    def __init__(self):
        super().__init__()
        self.model = "cardiffnlp/twitter-roberta-base-dec2021-tweet-topic-single-all"

    def classify(self, prompt):
        return super()._classify(self.model, prompt)
