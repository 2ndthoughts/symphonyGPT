from transformers import pipeline
from symphonyGPT.symphony.outcome_strategy.outcome_strategy import OutcomeStrategy


class SentimentMostStars(OutcomeStrategy):

    def __init__(self,format=None):
        super().__init__(format)
        self.sentiment_analyzer = 'nlptown/bert-base-multilingual-uncased-sentiment'

    def update_meta_data(self, response_raw_text):
        json_array = pipeline('sentiment-analysis',
                             model=f"{self.sentiment_analyzer}")(response_raw_text)

        sentiment = max(json_array, key=lambda json_array: json_array['score'])
        return sentiment

    def get_outcome_prompt(self):
        return "Parse the following array of JSON objects and select the one with the most 'stars' attribute"

    def process_outcome(self, conductor, prompt, response_array=None):
        # get the maximum stars and filter on it
        return super().process_stat_outcome('max_filter', 'label', response_array)