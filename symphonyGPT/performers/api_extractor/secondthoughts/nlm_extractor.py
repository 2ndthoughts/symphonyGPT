import json
import xml.etree.ElementTree as ElementTree
import requests
from symphonyGPT.performers.api_extractor.api_extractor import APIExtractor
from symphonyGPT.symphony.classifier.huggingface.ade_drug_effect_token_classifier import AdeDrugEffectTokenClassifier
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony


# :copyright: Copyright 2023 by 2ndthoughts.ai david@2ndthoughts.ai.
# :license: Licensed under the Non-Profit Open Software License version 3.0 see LICENSE for details.

class NLMExtractor(APIExtractor):

    def __init__(self, fields=None, max_rnk=5):
        super().__init__()
        self.max_rnk = max_rnk

    def perform(self, prompt):
        classifications = prompt.get_classifications()
        query_str = self.create_query_str_from_classifier(classifications)

        if query_str == "":
            query_str = prompt.get_prompt()

        # step 1, search
        # https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=metformin+lifespan
        # step 2, get the list of ids
        # step 3, for each id, get detail from the id
        # https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=37421961&retmode=text&rettype=abstract

        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query_str}&retmax={self.max_rnk}"
        self.util.debug_print(f"NLMExtractor.perform() get list url: {url}")
        self.util.debug_print_line()
        xml = None
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise exception if the request was unsuccessful
        except requests.exceptions.RequestException as e:
            print(f"Error occurred: {e}")
        else:
            try:
                xml = ElementTree.fromstring(response.content)
            except ValueError:  # includes xml.etree.ElementTree.ParseError
                print('Decoding XML has failed')

        response_count = xml.find('Count').text
        self.util.debug_print(f"NLMExtractor.perform() get list response_count: {response_count}")

        # self.util.debug_print(f"NLMExtractor.perform() get list xml: {ElementTree.tostring(xml, encoding='utf8').decode('utf8')}")
        # print all the ids
        ids = []
        for id in xml.iter('Id'):
            ids.append(id.text)

        self.util.debug_print(f"NLMExtractor.perform() get list ids: {ids}")
        # step 2
        # iterate all ids and fetch the abstract
        # https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=37421961&retmode=text&rettype=abstract

        kount = 0
        answer = json.loads("{}")
        for id in ids:
            kount = kount + 1
            if kount > self.max_rnk:
                break

            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={id}&retmode=text&rettype=abstract"
            self.util.debug_print(f"NLMExtractor.perform() get detail url: {url}")
            self.util.debug_print_line()

            try:
                response = requests.get(url)
                response.raise_for_status()  # Raise exception if the request was unsuccessful
            except requests.exceptions.RequestException as e:
                print(f"Error occurred: {e}")
            else:
                try:
                    text = response.content
                    summarized_text = self.summarize_result(text.decode("utf-8"), prompt.get_prompt())
                    # optional to add code to summarize answer to fit in LLM context
                    answer[f"PMID {id}"] = summarized_text
                except ValueError:
                    print('Decoding output has failed')

        self.set_raw_response(answer)


# test main
if __name__ == "__main__":
    m_test = Movement(
        prompt_classifier=[AdeDrugEffectTokenClassifier()],
        performers=[NLMExtractor()]
    )
    symphony = Symphony(movements=[m_test], null_answer_break=True)
    res = symphony.perform("does metformin increase lifespan")
