import json
import xml.etree.ElementTree as ElementTree
import requests
from symphonyGPT.performers.api_extractor.api_extractor import APIExtractor
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony


# :copyright: Copyright 2023 by 2ndthoughts.ai david@2ndthoughts.ai.
# :license: Licensed under the Non-Profit Open Software License version 3.0 see LICENSE for details.

class ArxivExtractor(APIExtractor):

    def __init__(self, fields=None, max_results=5):
        super().__init__()
        self.max_results = max_results

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
                    sub_answer = json.loads("{}")
                    if xml.find('ns:entry', namespaces=ns) is None:
                        self.util.debug_print(f"ArxivExtractor.perform() no content found")
                        break

                    id = xml.find('ns:entry', namespaces=ns).find('ns:id', namespaces=ns).text
                    published = xml.find('ns:entry', namespaces=ns).find('ns:published', namespaces=ns).text
                    title = xml.find('ns:entry', namespaces=ns).find('ns:title', namespaces=ns).text
                    summary = xml.find('ns:entry', namespaces=ns).find('ns:summary', namespaces=ns).text

                    sub_answer["id"] = id
                    sub_answer["published"] = published
                    sub_answer["title"] = title
                    sub_answer["summary"] = summary

                    answer.append(sub_answer)
                except ValueError:
                    print('Decoding output has failed')

        self.set_raw_response(answer)


# test main
if __name__ == "__main__":
    prompt = "Spatiotemporal applications in predicting outcomes"
    m_test = Movement(
        performers=[ArxivExtractor(max_results=5)]
    )

    symphony = Symphony(movements=[m_test], null_answer_break=True)
    res = symphony.perform(prompt)