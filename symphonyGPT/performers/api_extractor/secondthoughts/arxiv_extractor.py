import json
import xml.etree.ElementTree as ElementTree
import requests
from symphonyGPT.performers.api_extractor.api_extractor import APIExtractor
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony


# :copyright: Copyright 2023 by 2ndthoughts.ai david@2ndthoughts.ai.
# :license: Licensed under the Non-Profit Open Software License version 3.0 see LICENSE for details.

class ArxivExtractor(APIExtractor):

    def __init__(self, max_results=5, max_embeddings_results=3):
        super().__init__(max_results, max_embeddings_results)

    def perform(self, prompt):
        classifications = prompt.get_classifications()
        query_str = self.create_query_str_from_classifier(classifications)

        if query_str == "":
            query_str = prompt.get_prompt()

        answer = []
        for start_count in range(0, self.max_results):
            url = f"https://export.arxiv.org/api/query?search_query=all:{query_str}&start={start_count}&max_results=1"
            self.util.debug_print(f"ArxivExtractor.perform() get detail url: {url}")
            self.util.debug_print_line()

            try:
                response = requests.get(url)
                response.raise_for_status()  # Raise exception if the request was unsuccessful
            except requests.exceptions.RequestException as e:
                self.util.error_print(f"Error occurred: {e}")
            else:
                if response.status_code != 200:
                    self.util.debug_print(f"ArxivExtractor.perform() get detail response: {response.content}")
                    break
                try:
                    xml = None
                    r_text = response.text
                    try:
                        xml = ElementTree.fromstring(r_text)
                    except ValueError:  # includes xml.etree.ElementTree.ParseError
                        self.util.error_print('Decoding XML has failed')

                    ns = {'ns':'http://www.w3.org/2005/Atom'}
                    #sub_answer = json.loads("{}")
                    if xml.find('ns:entry', namespaces=ns) is None:
                        self.util.debug_print(f"ArxivExtractor.perform() no content found")
                        break

                    id = xml.find('ns:entry', namespaces=ns).find('ns:id', namespaces=ns).text
                    published = xml.find('ns:entry', namespaces=ns).find('ns:published', namespaces=ns).text
                    title = xml.find('ns:entry', namespaces=ns).find('ns:title', namespaces=ns).text
                    summary = xml.find('ns:entry', namespaces=ns).find('ns:summary', namespaces=ns).text
                    link = xml.find('ns:entry', namespaces=ns).find('ns:link', namespaces=ns).attrib['href']
                    authors = xml.find('ns:entry', namespaces=ns).findall('ns:author/ns:name', namespaces=ns)
                    author_names = ""
                    for author in authors:
                        author_names += author.text + ", "

                    if len(authors) > 0:
                        author_names = author_names[:-2]

                    # add to embeddings array
                    self.collection.add(
                        documents=[summary],
                        metadatas=[{"id": id,
                                    "published": published,
                                    "title": title,
                                    "authors": author_names,
                                    "link": link,
                                    "summary": summary}],
                        ids=[id]
                    )

                except ValueError:
                    print('Decoding output has failed')

        ef_val = self.default_embedding_function([prompt.get_prompt()])
        embedded_answers = self.collection.query(
            query_embeddings=ef_val,
            n_results=self.max_embeddings_results
        )

        for metadatas in embedded_answers["metadatas"]:
            for metadata in metadatas:
                answer.append(metadata)

        self.set_raw_response(answer)


# test main
if __name__ == "__main__":
    prompt = "Spatiotemporal applications in predicting outcomes"
    m_test = Movement(
        performers=[ArxivExtractor(max_results=5)]
    )

    symphony = Symphony(movements=[m_test], null_answer_break=True)
    res = symphony.perform(prompt)