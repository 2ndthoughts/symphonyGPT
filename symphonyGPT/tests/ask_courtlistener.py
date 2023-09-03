from performers.api_extractor.secondthoughts.court_listener_extractor import CourtListenerExtractor
from symphonyGPT.performers.language_model.openai_performers.gpt_4 import Gpt4
from symphonyGPT.symphony.classifier.huggingface.keyphrase_extraction_token_classifier import \
    KeyphraseExtractionTokenClassifier
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
    # prompt = "breach of professional duty of care and tortious interference with contract and prospective economic advantage"
    # prompt = "company director did not recuse himself from merger negotiations resulting in a breach of fiduciary duty" # did not produce results
    # prompt = "breach of fiduciary duty by a director of a company due to withholding of information and failure to recuse himself from merger negotiations"
    # prompt = "valuation company collaborated with buyer company during a merger in order to produce a high value merger in order to flip the company for a profit"
    # prompt = "is Ivermectin allowed to treat COVID"
    prompt = "is it legal to withhold information after signing but before closing of merger"

    # The symphony is composed of two movements
    #  * The first movement is to extract the drug and effect from the prompt then list all
    #  * the studies from courtlistener.com (A Free Law company) based on the extracted terms in an allegation
    #
    #  * The second movement is to generate a summary based on the allegation
    #  * and the list of cases from courtlistener.com
    
    m_extract = Movement(
        # prompt_classifier=[KeyphraseExtractionTokenClassifier()],
        performers=[CourtListenerExtractor(max_rnk=10)]
    )

    m_list_and_conclude = Movement(
        prompt_str="First list all the cases by caseName, absolute_url, court, docketNumber, dateFiled and the caseSummary. " +
                   "Then from all the listed cases, select the best case to cite for the allegation '" + prompt + "' : {} ",
        performers=[Gpt4()]
    )

    print(prompt)
    symphony = Symphony(movements=[m_extract, m_list_and_conclude], null_answer_break=True)
    res = symphony.perform(prompt)
    answer = res[0]["answer"]
    print(f"\n\n{answer}")


if __name__ == "__main__":
    main()
