from transformers import pipeline
from symphonyGPT.symphony.outcome_strategy.outcome_strategy import OutcomeStrategy


class SentimentAllPositive(OutcomeStrategy):

    def __init__(self, format=None):
        super().__init__(format)
        self.sentiment_analyzer = 'distilbert-base-uncased-finetuned-sst-2-english'

    def update_meta_data(self, response_raw_text):
        sentiment = pipeline('sentiment-analysis',
                             model=f"{self.sentiment_analyzer}")(response_raw_text)[0]

        return sentiment

    def get_outcome_prompt(self):
        return "Parse the following array of JSON objects and select the one where the 'label' attribute value is 'POSITIVE'"

    def process_outcome(self, conductor, prompt, response_array=None):
        return super().process_stat_outcome('filter', 'label', response_array, 'POSITIVE')