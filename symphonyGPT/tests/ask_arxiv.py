import chromadb

from symphonyGPT.performers.api_extractor.secondthoughts.arxiv_extractor import ArxivExtractor
from symphonyGPT.performers.generator.pdf_generator import PDFGenerator
from symphonyGPT.performers.language_model.xai_performers.grok_beta import GrokBeta
from symphonyGPT.symphony.classifier.huggingface.keyphrase_extraction_token_classifier import \
    KeyphraseExtractionTokenClassifier
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony


# in this example, make sure to get an openai api key according to this page
# https://platform.openai.com/account/api-keys and update the api_key in the file
# symphonyGPT/performers/api_keys.py

def main() -> None:
    # prompt = "are spatiotemporal techniques preferred in predicting outc f gomes"
    # prompt = "what are popular frameworks for multi-agent LLMs cooperatively solving problems"
    # prompt = "what is the best technique for maximizing the context length of LLMs"
    # prompt = "the techniques of prompt context generation and their effectiveness in LLMs"
    # prompt = "have room temperature superconductors been shown to work"
    # prompt = "spatiotemporal prediction using LLM context embeddings"
    prompt = "what are the advances in rocket propulsion including the argon hall thruster"

    # The symphony is composed of two movements
    #  * list all the studies from arxiv based on a search of the prompt
    #
    #  * The second movement is to generate a conclusion based on the extracted statements
    #  * and the list of studies from eutils.ncbi.nlm.nih.gov (National Library of Medicine)

    m_extract = Movement(
        prompt_classifier=[KeyphraseExtractionTokenClassifier()],
        performers=[ArxivExtractor(max_results=15)]
    )

    m_list_and_conclude = Movement(
        prompt_str="First, list all publications by id, authors, published, link, title, and summary. " +
                   "Next, based on all the publications, generate a conclusion for '" + prompt + "' : {} ",
        performers=[GrokBeta()]
    )

    m_generate_article = Movement(
        prompt_str="Generate an article and its title based on '" + prompt + "using and citing the following "
                                                                             "publications with title, authors, and "
                                                                             "link as a list': '{}' ",
        performers=[GrokBeta()]
    )

    m_create_pdf = Movement(
        prompt_str="{}",
        performers=[PDFGenerator("research_paper.pdf")]
    )

    print(prompt)
    symphony = Symphony(movements=[m_extract, m_list_and_conclude, m_generate_article, m_create_pdf],
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
