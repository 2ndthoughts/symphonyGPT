from symphonyGPT.performers.api_extractor.secondthoughts.court_listener_extractor import CourtListenerExtractor
from symphonyGPT.performers.generator.pdf_generator import PDFGenerator
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

    prompt = "climate change and global warming are caused by human activity"

    # The symphony is composed of two movements
    #  * The first movement is to extract the drug and effect from the prompt then list all
    #  * the studies from courtlistener.com (A Free Law company) based on the extracted terms in an allegation
    #
    #  * The second movement is to generate a summary based on the allegation
    #  * and the list of cases from courtlistener.com
    
    m_extract = Movement(
        # prompt_classifier=[KeyphraseExtractionTokenClassifier()],
        performers=[CourtListenerExtractor(max_rnk=8)]
    )

    m_list_and_conclude = Movement(
        prompt_str="Summarize the findings and list only the related cases by caseName, absolute_url, court, "
                   "docketNumber, dateFiled and the caseSummary. " +
                   "Then from the related cases, select the best case to cite for the allegation '" + prompt + "' : {} ",
        performers=[Gpt4()]
    )

    m_create_pdf = Movement(
        prompt_str="{}",
        performers=[PDFGenerator("court_research.pdf")]
    )

    print(prompt)
    symphony = Symphony(movements=[m_extract, m_list_and_conclude, m_create_pdf], null_answer_break=True)
    res = symphony.perform(prompt)
    answer = res[0]["answer"]
    print(f"\n\n{answer}")


if __name__ == "__main__":
    main()
