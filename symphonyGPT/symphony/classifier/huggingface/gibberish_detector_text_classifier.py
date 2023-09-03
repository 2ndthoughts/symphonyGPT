from symphonyGPT.symphony.classifier.classifier import Classifier


class GibberishDetectorTextClassifier(Classifier):

    def __init__(self):
        super().__init__()
        self.model = "madhurjindal/autonlp-Gibberish-Detector-492513457"

    def classify(self, prompt):
        return super()._classify(self.model, prompt)
