from symphonyGPT.performers.api_extractor.secondthoughts.wikipedia_extractor import WikipediaExtractor
from symphonyGPT.performers.generator.pdf_generator import PDFGenerator
from symphonyGPT.performers.generator.secondthoughts.prompt_context_generator import PromptContextGenerator
from symphonyGPT.performers.language_model.openai_performers.gpt_4 import Gpt4
from symphonyGPT.performers.language_model.xai_performers.grok_beta import GrokBeta
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony


# in this example, make sure to get an openai api key according to this page
# https://platform.openai.com/account/api-keys and update the api_key in the file
# symphonyGPT/performers/api_keys.py

def main() -> None:
    prompt = "how did the roman empire fall"

    # The symphony is composed of two movements
    #  * list all the studies from arxiv based on a search of the prompt
    #
    #  * The second movement is to generate a conclusion based on the extracted statements
    #  * and the list of studies from eutils.ncbi.nlm.nih.gov (National Library of Medicine)

    #prompt = input("What would you like to know: ")

    m_generate_context = Movement(
        performers=[PromptContextGenerator(number_of_questions=3)]
    )

    m_summarize_generated_prompt = Movement(
        prompt_str="create a concise prompt from the following questions: '{}'",
        performers=[GrokBeta()]
    )

    m_extract = Movement(
        performers=[WikipediaExtractor(max_results=10)]
    )

    m_generate_article = Movement(
        prompt_str="Generate an article with a title based on '"
                   + prompt + " using content from the following list of articles and citing the "
                              "title, description, and article_url as a list in the end ': '{}' ",
        performers=[GrokBeta()]
    )

    m_create_pdf = Movement(
        prompt_str="{}",
        performers=[PDFGenerator("wiki_query_summary.pdf")]
    )

    print(prompt)
    symphony = Symphony(movements=[m_extract,m_generate_article, m_create_pdf],
                        null_answer_break=True)
    res = symphony.perform(prompt)

    answer = res[0]["answer"]
    print(f"\n\n{answer}")


if __name__ == "__main__":
    main()
