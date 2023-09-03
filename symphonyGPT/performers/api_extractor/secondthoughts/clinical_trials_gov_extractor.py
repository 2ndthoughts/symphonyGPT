import json
import requests
from symphonyGPT.performers.api_extractor.api_extractor import APIExtractor

# :copyright: Copyright 2023 by 2ndthoughts.ai david@2ndthoughts.ai.
# :license: Licensed under the Non-Profit Open Software License version 3.0 see LICENSE for details.


class CTGExtractor(APIExtractor):

    def __init__(self, fields=None, max_trials_returned=3):
        super().__init__()
        if fields is None:
            self.fields = ("NCTId,LeadSponsorName,CompletionDate,BriefTitle,DetailedDescription,"
                           "PrimaryOutcomeDescription")
            # additional fields include "ArmGroupLabel,ArmGroupDescription,EnrollmentCount"
        else:
            self.fields = fields
        self.max_trials_returned = max_trials_returned
        self.result_index = 1

    def perform(self, prompt):
        classifications = prompt.get_classifications()
        query_str = self.create_query_str_from_classifier(classifications)

        if query_str == "":
            query_str = prompt.get_prompt()

        if self.fields is None:
            self.fields = "NCTId,LeadSponsorName,CompletionDate,BriefTitle,DetailedDescription"

        json_answer = json.loads("{}")

        # loop through the results and for each result, summarize the DetailedDescription
        for self.result_index in range(1, self.max_trials_returned + 1):
            url = f"https://clinicaltrials.gov/api/query/study_fields?expr={query_str}&fields={self.fields}&min_rnk={self.result_index}&max_rnk={self.result_index}&fmt=JSON"
            self.util.debug_print(f"CTGExtractor.perform() url: {url}")
            self.util.debug_print_line()
            data = None
            try:
                response = requests.get(url)
                response.raise_for_status()  # Raise exception if the request was unsuccessful
            except requests.exceptions.RequestException as e:
                self.util.error_print(f"Error occurred: {e}")
            else:
                try:
                    data = response.json()
                    # summarize the DetailedDescription based on prompt if needed

                    if data["StudyFieldsResponse"]["NStudiesFound"] == 0:
                        self.util.debug_print(f"CTGExtractor.perform() No results found for: {query_str}")
                        break

                    # self.util.debug_print(f"CTGExtractor.perform() number of studies found: {data['StudyFieldsResponse']['NStudiesFound']}")

                    detailed_description = ""
                    if ("StudyFields" in data["StudyFieldsResponse"] and
                            "DetailedDescription" in data["StudyFieldsResponse"]["StudyFields"][0]):
                        self.util.debug_print(f"CTGExtractor.perform() Summarizing DetailedDescription: {self.result_index}")
                        detailed_description = data["StudyFieldsResponse"]["StudyFields"][0]["DetailedDescription"]
                        if detailed_description is not None:
                            # use Gpt4 to summarize the DetailedDescription
                            detailed_description = self.summarize_result(detailed_description, prompt.get_prompt())

                    # put the summarized DetailedDescription back into the data
                    if detailed_description != "":
                        data["StudyFieldsResponse"]["StudyFields"][0]["DetailedDescription"] = detailed_description
                except ValueError:  # includes simplejson.decoder.JSONDecodeError
                    print('Decoding JSON has failed')

            json_answer[f"result_set_{self.result_index}"] = data

        self.set_raw_response(json.dumps(json_answer, indent=4, sort_keys=True))
