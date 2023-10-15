import json
import requests

from symphonyGPT.performers.api_keys import APIKeys
from symphonyGPT.performers.api_extractor.api_extractor import APIExtractor
from symphonyGPT.symphony.classifier.huggingface.keyphrase_extraction_token_classifier import \
    KeyphraseExtractionTokenClassifier
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony
from bs4 import BeautifulSoup


# :copyright: Copyright 2023 by 2ndthoughts.ai david@2ndthoughts.ai.
# :license: Licensed under the Non-Profit Open Software License version 3.0 see LICENSE for details.

class CourtListenerExtractor(APIExtractor):
    def __init__(self, fields=None, max_rnk=3, query_term_joiner="AND"):
        super().__init__()
        self.max_rnk = max_rnk
        self.fields = fields
        self.joiner = query_term_joiner
        self.api_token = APIKeys().get_api_key("courtlistener")

    def perform(self, prompt):
        classifications = prompt.get_classifications()
        query_str = self.create_query_str_from_classifier(classifications)

        if query_str == "":
            query_str = prompt.get_prompt()

        # URL for CourtListener search API endpoint
        search_url = "https://www.courtlistener.com/api/rest/v3/search"

        # Parameters for the API request
        # p_str = "breach of professional duty of care and tortious interference with
        # contract and prospective economic advantage"
        p_str = prompt.get_prompt()

        words = query_str.split("+")
        q_arg = ""
        for word in words:
            word = word.strip()
            if word != "":
                q_arg += f'{word} {self.joiner} '

        params = {'q': q_arg[:-5], 'order_by': 'citeCount desc', 'stat_Precedential': 'on'}
        self.util.debug_print(f"CourtListenerExtractor.perform() params: {params}")

        # The headers for the request
        headers = {'Authorization': 'Token ' + self.api_token}

        # Send the GET request to the API
        response = requests.get(search_url, params=params, headers=headers)

        json_answer = json.loads("[{}]")

        result_count = 0
        # Check if the request was successful
        if response.status_code == 200:
            # Get the JSON data from the response
            data = response.json()
            response_count = data['count']
            self.util.debug_print(f"CourtListenerExtractor.perform() response count: {response_count}")

            if response_count == 0:
                return json_answer

            # Print the details of each case
            for case in data['results']:
                json_answer_set = json.loads("{}")
                json_answer_set["cluster_id"] = case['cluster_id']
                json_answer_set["absolute_url"] = f"https://www.courtlistener.com{case['absolute_url']}"
                json_answer_set["caseName"] = case['caseName']
                json_answer_set["court"] = case['court']
                json_answer_set['docketNumber'] = case['docketNumber']
                json_answer_set["judge"] = case['judge']
                json_answer_set["dateFiled"] = case['dateFiled']
                json_answer_set["status"] = case['status']
                json_answer_set['citeCount'] = case['citeCount']

                opinion_url = f"https://www.courtlistener.com/api/rest/v3/opinions/{case['id']}/?format=json"
                # need try catch here
                opinion_response = requests.get(opinion_url, headers=headers)
                if opinion_response.status_code == 200:
                    opinion_data = opinion_response.json()
                    str_to_summarize = ""
                    case_html = opinion_data['html_lawbox']

                    if case_html == "":
                        case_html = opinion_data['html']

                    if case_html == "":
                        case_html = opinion_data['html_columbia']

                    if case_html == "":
                        case_html = opinion_data['html_anon_2020']

                    if case_html != "":
                        str_to_summarize = BeautifulSoup(case_html, 'html.parser').text
                    else:
                        if case_html == "" and opinion_data['xml_harvard'] != "":
                            str_to_summarize = self.util.xml_to_text(opinion_data['xml_harvard'])
                        else:
                            str_to_summarize = opinion_data['plain_text']

                    prompt_str = f"According to the allegation '{p_str}', summarize the following court case '{str_to_summarize[:7000]}'"  # make sure we dont overwhelm max tokens
                    summarize_this_str = self.summarize_result(str_to_summarize, p_str, prompt_str)

                    json_answer_set["caseSummary"] = summarize_this_str

                    self.util.debug_print(json.dumps(json_answer_set, indent=4, sort_keys=True))
                    self.util.debug_print_line()
                else:
                    print('Failed to retrieve opinion data. Status code:', opinion_response.status_code,
                          opinion_response.text)

                json_answer.append(json_answer_set)
                result_count += 1
                if result_count >= self.max_rnk:
                    break

                # time.sleep(1)  # sleep for 1 second to avoid rate limit
        else:
            print('Failed to retrieve case data. Status code:', response.status_code, response.text)

        self.set_raw_response(json.dumps(json_answer, indent=4, sort_keys=True))


# test main
if __name__ == "__main__":
    m_test = Movement(
        prompt_classifier=[KeyphraseExtractionTokenClassifier()],
        performers=[CourtListenerExtractor(max_rnk=10)]
    )
    symphony = Symphony(movements=[m_test], null_answer_break=True)
    res = symphony.perform("is Ivermectin allowed to treat COVID")
    # res = symphony.perform("breach of professional duty of care and tortious interference with contract and "
    #                        "prospective economic advantage")
