from symphonyGPT.performers.api_extractor.secondthoughts.arxiv_extractor import ArxivExtractor
from symphonyGPT.performers.api_extractor.secondthoughts.clinical_trials_gov_extractor import CTGExtractor
from symphonyGPT.performers.api_extractor.secondthoughts.court_listener_extractor import CourtListenerExtractor
from symphonyGPT.performers.api_extractor.secondthoughts.wikipedia_extractor import WikipediaExtractor
from symphonyGPT.performers.generator.pdf_generator import PDFGenerator
from symphonyGPT.performers.generator.secondthoughts.prompt_context_generator import PromptContextGenerator
from symphonyGPT.symphony.classifier.huggingface.keyphrase_extraction_token_classifier import KeyphraseExtractionTokenClassifier
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

    prompt = input("What is your question: ")

    m_generate_context = Movement(
        performers=[PromptContextGenerator(number_of_questions=3)]
    )

    m_extract = Movement(
        prompt_str="{}",
        prompt_classifier=[KeyphraseExtractionTokenClassifier()],
        performers=[ArxivExtractor(max_results=10),
                    WikipediaExtractor(max_results=10),
                    NLMExtractor(max_rnk=10),
                    CTGExtractor(max_trials_returned=10),
                    CourtListenerExtractor(max_rnk=10)]
    )

    m_list_and_conclude = Movement(
        prompt_str="First, list all the documents by source, id, title, authors, date, and summary, " +
                   "then based on all the documents, generate a conclusion for '" + prompt + "' : {} ",
        performers=[Gpt4()]
    )

    m_create_pdf = Movement(
        prompt_str="{}",
        performers=[PDFGenerator("wiki_query_summary.pdf")]
    )

    print(prompt)
    symphony = Symphony(movements=[m_generate_context, m_extract, m_list_and_conclude, m_create_pdf], null_answer_break=False)
    res = symphony.perform(prompt)
    answer = res[0]["answer"]
    print(f"\n\n{answer}")


if __name__ == "__main__":
    main()
