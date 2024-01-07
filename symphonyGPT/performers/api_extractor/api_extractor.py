import chromadb
from chromadb.utils import embedding_functions

from symphonyGPT.performers.language_model.openai_performers.gpt_4 import Gpt4
from symphonyGPT.performers.performer import Performer
from symphonyGPT.symphony.prompt import Prompt


class APIExtractor(Performer):
    def __init__(self, max_results=5, max_embeddings_results=3):
        super().__init__()
        self.max_results = max_results
        self.set_type("api_extractor")
        self.db_client = chromadb.Client()
        self.collection = self.db_client.get_or_create_collection(name=f"s_{self.__class__.__name__}")
        self.default_embedding_function = embedding_functions.DefaultEmbeddingFunction()
        self.max_embeddings_results = max_embeddings_results

    def create_query_str_from_classifier(self, classifications):
        query_str = ""
        if classifications is not None:
            # use classification words to search for drug and effect
            for classification_name, classification in classifications.items():
                for entity in classification:
                    query_str += entity["word"].strip()
                    query_str += "+"

        # remove the last +
        if query_str.endswith("+"):
            query_str = query_str[:-1]

        return query_str

    def summarize_result(self, summarize_this_str, summarizing_prompt, prompt_str=None):
        gpt4 = Gpt4()
        if prompt_str is None:
            prompt_str = (f"According to the question '{summarizing_prompt}', summarize the following "
                          f"'{summarize_this_str}'")

        sum_prompt = Prompt()
        sum_prompt.set_prompt(prompt_str)
        gpt4.perform(sum_prompt)
        summarize_this_str = gpt4.get_raw_response()
        # remove the prompt_str from the summarized DetailedDescription
        summarize_this_str = summarize_this_str.replace(prompt_str, "")
        return summarize_this_str