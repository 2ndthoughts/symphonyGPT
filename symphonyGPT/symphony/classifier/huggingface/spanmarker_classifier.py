from symphonyGPT.symphony.classifier.classifier import Classifier
from span_marker import SpanMarkerModel


class SpanMarkerClassifier(Classifier):

        def __init__(self):
            super().__init__("token-classification")

        def _classify(self, classifier_model, prompt):
            if self.model is None:
                raise Exception("Model not set")

            # Download from the 🤗 Hub
            model = SpanMarkerModel.from_pretrained(classifier_model)
            # Run inference
            return model.predict(prompt.get_prompt())