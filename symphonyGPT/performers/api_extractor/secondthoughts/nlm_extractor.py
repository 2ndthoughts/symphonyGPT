import json
import xml.etree.ElementTree as ElementTree
import requests
from symphonyGPT.performers.api_extractor.api_extractor import APIExtractor
from symphonyGPT.symphony.classifier.huggingface.ade_drug_effect_token_classifier import AdeDrugEffectTokenClassifier
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony
from symphonyGPT.symphony import summarizer


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
        for id in ids:
            kount = kount + 1
            if kount > self.max_rnk:
                break

            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={id}&retmode=xml&rettype=abstract"
            self.util.debug_print(f"NLMExtractor.perform() get detail url: {url}")
            self.util.debug_print_line()

            try:
                response = requests.get(url)
                response.raise_for_status()  # Raise exception if the request was unsuccessful
            except requests.exceptions.RequestException as e:
                print(f"Error occurred: {e}")
            else:
                try:
                    xml = ElementTree.fromstring(response.text)
                except ValueError:  # includes xml.etree.ElementTree.ParseError
                    self.util.error_print('Decoding XML has failed')

                try:
                    text = response.content

                    pmid = ""
                    if xml.find('PubmedArticle/MedlineCitation/PMID') is not None:
                        pmid = xml.find('PubmedArticle/MedlineCitation/PMID').text

                    issn = ""
                    if xml.find('PubmedArticle/MedlineCitation/Article/Journal/ISSN') is not None:
                        issn = xml.find('PubmedArticle/MedlineCitation/Article/Journal/ISSN').text

                    article_title = ""
                    if xml.find('PubmedArticle/MedlineCitation/Article/ArticleTitle') is not None:
                        article_title = xml.find('PubmedArticle/MedlineCitation/Article/ArticleTitle').text

                    abstract_text = ""
                    if xml.find('PubmedArticle/MedlineCitation/Article/Abstract/AbstractText') is not None:
                        abstract_text = xml.find('PubmedArticle/MedlineCitation/Article/Abstract/AbstractText').text

                    summarized_text = summarizer.summarize_result(abstract_text, prompt.get_prompt())

                    authors = ""
                    for author in xml.findall('PubmedArticle/MedlineCitation/Article/AuthorList/Author'):
                        last_name = author.find('LastName').text

                        first_name = ""
                        if author.find('ForeName') is not None:
                            first_name = author.find('ForeName').text

                        authors += f"{last_name}, {first_name}; "

                    if authors != "":
                        authors = authors[:-2]

                    article_date = ""
                    for date in xml.findall('PubmedArticle/MedlineCitation/Article/Journal/JournalIssue/PubDate'):
                        if date.find('Year') is None:
                            continue
                        year = date.find('Year').text

                        month = ""
                        if date.find('Month') is not None:
                            month = date.find('Month').text

                        day = ""
                        if date.find('Day') is not None:
                            day = date.find('Day').text

                        article_date += article_date + f"{year}-{month}-{day}"

                    sub_answer = json.loads("{}")
                    sub_answer["PMID"] = pmid
                    sub_answer["ISSN"] = issn
                    sub_answer["ArticleDate"] = article_date
                    sub_answer["ArticleTitle"] = article_title
                    sub_answer["AbstractText"] = summarized_text
                    sub_answer["Authors"] = authors
                    sub_answer["Link"] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

                    self.collection.add(
                        documents=[summarized_text],
                        metadatas=[sub_answer],
                        ids=[f"{pmid}"]
                    )
                except ValueError:
                    print('Decoding output has failed')

        ef_val = self.default_embedding_function([prompt.get_prompt()])
        embedded_answers = self.collection.query(
            query_embeddings=ef_val,
            n_results=self.max_embeddings_results
        )

        answer = []
        for metadatas in embedded_answers["metadatas"]:
            for metadata in metadatas:
                answer.append(metadata)

        self.set_raw_response(answer)


# test main
if __name__ == "__main__":
    m_test = Movement(
        prompt_classifier=[AdeDrugEffectTokenClassifier()],
        performers=[NLMExtractor(max_rnk=5)]
    )
    symphony = Symphony(movements=[m_test], null_answer_break=True)
    res = symphony.perform("does metformin increase lifespan")
