import os

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from chromadb.utils import embedding_functions
from symphonyGPT.performers.performer import Performer
from symphonyGPT.symphony.chroma_client import chroma_client


class APIExtractor(Performer):
    def __init__(self, max_results=5, max_embeddings_results=5, use_embeddings=True):
        super().__init__()
        self.max_results = max_results
        self.set_type("api_extractor")
        self.max_embeddings_results = max_embeddings_results
        self.db_client = None
        self.collection = None
        self.default_embedding_function = None
        if not use_embeddings:
            return
        self.db_client = chroma_client()
        self.collection = self.db_client.get_or_create_collection(name=f"s_{self.__class__.__name__}")
        self.default_embedding_function = embedding_functions.DefaultEmbeddingFunction()

    def create_query_array_from_classifier(self, classifications):
        query_array = []
        if classifications is not None:
            # use classification words to search for drug and effect
            for classification_name, classification in classifications.items():
                for entity in classification:
                    query_array.append(entity["word"].strip())

        return query_array

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
