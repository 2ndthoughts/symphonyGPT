from performers.api_extractor.secondthoughts.arxiv_extractor import ArxivExtractor
from symphony.classifier.huggingface.keyphrase_extraction_token_classifier import KeyphraseExtractionTokenClassifier
from symphonyGPT.performers.language_model.openai_performers.gpt_4 import Gpt4
from symphonyGPT.performers.api_extractor.secondthoughts.nlm_extractor import NLMExtractor
from symphonyGPT.symphony.classifier.huggingface.biomedical_ner_all_token_classifier import \
    BiomedicalNerAllTokenClassifier
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony


# in this example, make sure to get an openai api key according to this page
# https://platform.openai.com/account/api-keys and update the api_key in the file
# symphonyGPT/performers/language_model/openai_performers/openai_performer.py

def main() -> None:
    # prompt = "are spatiotemporal techniques preferred in predicting outcomes"
    # prompt = "what are popular frameworks for multi agent LLMs cooperatively solving problems"
    prompt = "what is the best technique for maximizing the context length of LLMs"
    # prompt = "have room temperature superconductors been shown to work"

    # The symphony is composed of two movements
    #  * list all the studies from arxiv based on a search of the prompt
    #
    #  * The second movement is to generate a conclusion based on the extracted statements
    #  * and the list of studies from eutils.ncbi.nlm.nih.gov (National Library of Medicine)

    m_extract = Movement(
        prompt_classifier=[KeyphraseExtractionTokenClassifier()],
        performers=[ArxivExtractor(max_results=5)]
    )

    m_list_and_conclude = Movement(
        prompt_str="First, list all publications by id, published, title, and summary. " +
                   "Next, based on all the publications, generate a conclusion for '" + prompt + "' : {} ",
        performers=[Gpt4()]
    )

    print(prompt)
    symphony = Symphony(movements=[m_extract, m_list_and_conclude], null_answer_break=True)
    res = symphony.perform(prompt)
    answer = res[0]["answer"]
    print(f"\n\n{answer}")


if __name__ == "__main__":
    main()
