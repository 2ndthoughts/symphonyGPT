import json
import requests
import wikipediaapi
from symphonyGPT.performers.api_extractor.api_extractor import APIExtractor
from symphonyGPT.symphony import summarizer
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony


# :copyright: Copyright 2023 by 2ndthoughts.ai david@2ndthoughts.ai.
# :license: Licensed under the Non-Profit Open Software License version 3.0 see LICENSE for details.

class WikipediaExtractor(APIExtractor):
    def __init__(self, fields=None, max_results=10):
        super().__init__()
        self.max_results = max_results
        # no keys required for public wikipedia api
        # self.api_token = APIKeys().get_api_key("wikimedia")

    def perform(self, prompt):
        classifications = prompt.get_classifications()
        query_str = self.create_query_str_from_classifier(classifications)

        if query_str == "":
            query_str = prompt.get_prompt()

        # replace + with spaces
        query_str = query_str.replace("+", " ")

        self.util.debug_print(f"WikipediaExtractor.perform() query_str: {query_str}")

        language_code = 'en'
        search_query = query_str
        headers = {
            # 'Authorization': 'Bearer ' + access_token,
            'User-Agent': 'SymphonyGPT (dev@2ndthoughts.ai)'
        }

        base_url = 'https://api.wikimedia.org/core/v1/wikipedia/'
        endpoint = '/search/page'
        url = base_url + language_code + endpoint

        self.util.debug_print(f"WikipediaExtractor.perform() url: {url}")

        parameters = {'q': search_query, 'limit': self.max_results}
        response = requests.get(url, headers=headers, params=parameters)

        wiki_wiki = wikipediaapi.Wikipedia(
            user_agent='SymphonyGPT (dev@2ndthoughts.ai)',
            language='en'
        )

        response_json = json.loads(response.text)

        self.util.debug_print(f"WikipediaExtractor.perform() response pages count: {len(response_json['pages'])}")

        for page in response_json['pages']:
            display_title = page['title']
            article_url = f"https://{language_code}.wikipedia.org/wiki/{page['key']}"
            page_py = wiki_wiki.page(page['key'])
            page_text = page_py.text
            try:
                article_description = f"{page['description']}"
            except:
                article_description = 'a Wikipedia article'
            try:
                thumbnail_url = f"https:{page['thumbnail']['url']}"
            except:
                thumbnail_url = ('https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Wikipedia-logo-v2.svg'
                                 '/200px-Wikipedia-logo-v2.svg.png')

            self.util.debug_print(display_title)
            self.util.debug_print(article_url)
            self.collection.add(
                documents=[page_text],
                metadatas=[{"id": f"{page['id']}",
                            "title": display_title,
                            "key": f"{page['key']}",
                            "excerpt": f"{page['excerpt']}",
                            "article_url": article_url,
                            "content": page_text,
                            "description": article_description,
                            "thumbnail_url": thumbnail_url
                            }],
                ids=[f"{page['id']}"]
            )

        ef_val = self.default_embedding_function([prompt.get_prompt()])
        embedded_answers = self.collection.query(
            query_embeddings=ef_val,
            n_results=self.max_embeddings_results
        )

        answer = []
        for metadatas in embedded_answers["metadatas"]:
            for metadata in metadatas:
                self.util.debug_print(f"WikipediaExtractor.perform() summarizing: {metadata['title']}")
                metadata["content"] = summarizer.summarize_result_in_chunks(metadata["content"],
                                                                            prompt.get_prompt())
                answer.append(metadata)

        self.set_raw_response(answer)


# test main
if __name__ == "__main__":
    m_test = Movement(
        # prompt_classifier=[KeyphraseExtractionTokenClassifier()],
        performers=[WikipediaExtractor(max_results=10)]
    )
    symphony = Symphony(movements=[m_test], null_answer_break=True)
    res = symphony.perform("what are some ancient indian foods")
    # res = symphony.perform("breach of professional duty of care and tortious interference with contract and "
    #                        "prospective economic advantage")
