from symphonyGPT.symphony.classifier.classifier import Classifier


class RobertaBaseGoEmotionsTextClassifier(Classifier):

    def __init__(self):
        super().__init__()
        self.model = "SamLowe/roberta-base-go_emotions"

    def classify(self, prompt):
        return super()._classify(self.model, prompt)

