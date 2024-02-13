import chromadb

from symphonyGPT.performers.api_extractor.secondthoughts.allrecipes_extractor import AllRecipesExtractor
from symphonyGPT.performers.api_extractor.secondthoughts.arxiv_extractor import ArxivExtractor
from symphonyGPT.performers.generator.pdf_generator import PDFGenerator
from symphonyGPT.performers.language_model.openai_performers.gpt_4 import Gpt4
from symphonyGPT.symphony.classifier.huggingface.foodbase_distillbert_token_classifier import FoodBaseDistilBert
from symphonyGPT.symphony.classifier.huggingface.keyphrase_extraction_token_classifier import \
    KeyphraseExtractionTokenClassifier
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony


# in this example, make sure to get an openai api key according to this page
# https://platform.openai.com/account/api-keys and update the api_key in the file
# symphonyGPT/performers/api_keys.py

def main() -> None:
    prompt = "what are some recipes that contain mushrooms"

    # The symphony is composed of two movements
    #  * list all the studies from arxiv based on a search of the prompt
    #
    #  * The second movement is to generate a conclusion based on the extracted statements
    #  * and the list of studies from eutils.ncbi.nlm.nih.gov (National Library of Medicine)

    m_extract = Movement(
        prompt_classifier=[FoodBaseDistilBert()],
        performers=[AllRecipesExtractor(max_results=5)]
    )

    m_list_and_conclude = Movement(
        prompt_str="Summarize the following recipes by the following question'" + prompt + "' : {} ",
        performers=[Gpt4()]
    )

    m_generate_article = Movement(
        prompt_str="Generate an article and its title based on '" + prompt + "using and citing the following "
                                                                             "publications with title, authors, and "
                                                                             "link as a list': '{}' ",
        performers=[Gpt4()]
    )

    m_create_pdf = Movement(
        prompt_str="{}",
        performers=[PDFGenerator("research_paper.pdf")]
    )

    print(prompt)
    symphony = Symphony(movements=[m_extract, m_list_and_conclude],
                        null_answer_break=True)
    res = symphony.perform(prompt)

    # Util().print_collection_counts()

    answer = res[0]["answer"]
    print(f"\n\n{answer}")

    db_client = chromadb.Client()
    collections = db_client.list_collections()
    for collection in collections:
        print(collection.name)
        #print(collection.peek())
        print(collection.count())

    for collection in collections:
        db_client.delete_collection(name=collection.name)


if __name__ == "__main__":
    main()
