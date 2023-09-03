from performers.api_extractor.secondthoughts.clinical_trials_gov_extractor import CTGExtractor
from performers.api_extractor.secondthoughts.court_listener_extractor import CourtListenerExtractor
from symphony.classifier.huggingface.keyphrase_extraction_token_classifier import KeyphraseExtractionTokenClassifier
from symphonyGPT.performers.language_model.openai_performers.gpt_4 import Gpt4
from symphonyGPT.performers.api_extractor.secondthoughts.nlm_extractor import NLMExtractor
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony


# in this example, make sure to get a courtlistener api key according to this page
# https://www.courtlistener.com/help/api/rest/#permissions and update the api_key in the file
# symphonyGPT/performers/api_extractor/secondthoughts/court_listener_extractor.py
#
# additionally, make sure to get an openai api key according to this page
# https://platform.openai.com/account/api-keys and update the api_key in the file
# symphonyGPT/performers/api_keys.py


def main() -> None:
    prompt = "is Ivermectin allowed to treat COVID-19"
    # prompt = "Is it legal to treat depression with cannabis"
    # prompt = "can abortion be performed after 20 weeks of pregnancy"

    m_extract = Movement(
        #prompt_classifier=[KeyphraseExtractionTokenClassifier()],
        performers=[NLMExtractor(max_rnk=3), CTGExtractor(max_trials_returned=3), CourtListenerExtractor(max_rnk=3)]
    )

    m_list_and_conclude = Movement(
        prompt_str="First, list all the documents by source, id, title, and summary, " +
                   "then based on all the documents, generate a conclusion for '" + prompt + "' : {} ",
        performers=[Gpt4()]
    )

    print(prompt)
    symphony = Symphony(movements=[m_extract, m_list_and_conclude], null_answer_break=False)
    res = symphony.perform(prompt)
    answer = res[0]["answer"]
    print(f"\n\n{answer}")


if __name__ == "__main__":
    main()
