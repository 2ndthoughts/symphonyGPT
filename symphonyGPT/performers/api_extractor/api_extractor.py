import chromadb
from chromadb.utils import embedding_functions
from symphonyGPT.performers.performer import Performer


class APIExtractor(Performer):
    def __init__(self, max_results=5, max_embeddings_results=5):
        super().__init__()
        self.max_results = max_results
        self.set_type("api_extractor")
        self.db_client = chromadb.Client()
        self.collection = self.db_client.get_or_create_collection(name=f"s_{self.__class__.__name__}")
        self.default_embedding_function = embedding_functions.DefaultEmbeddingFunction()
        self.max_embeddings_results = max_embeddings_results

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
