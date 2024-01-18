from symphonyGPT.performers.language_model.openai_performers.gpt_4 import Gpt4
from symphonyGPT.performers.api_extractor.secondthoughts.nlm_extractor import NLMExtractor
from symphonyGPT.symphony.classifier.huggingface.biomedical_ner_all_token_classifier import \
    BiomedicalNerAllTokenClassifier
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony

# in this example, make sure to get an openai api key according to this page
# https://platform.openai.com/account/api-keys and update the api_key in the file
# symphonyGPT/performers/api_keys.py


def main() -> None:

    prompt = "does childbirth reduce chance of breast cancer"

    # The symphony is composed of two movements
    #  * The first movement is to extract the drug and effect from the prompt then list all
    #  * the studies from eutils.ncbi.nlm.nih.gov (National Library of Medicine) based on the extracted drug and effect
    #
    #  * The second movement is to generate a conclusion based on the extracted drug and effect
    #  * and the list of studies from eutils.ncbi.nlm.nih.gov (National Library of Medicine)
    
    m_extract = Movement(
        prompt_classifier=[BiomedicalNerAllTokenClassifier()],
        performers=[NLMExtractor(max_rnk=10)]
    )

    m_list_and_conclude = Movement(
        prompt_str="Generate an article with a title based on '" +
                    prompt + "', citing all the publications by PMID and a summary. " +
                   "Then generate a conclusion for the publications: {} ",
        performers=[Gpt4()]
    )

    print(prompt)
    symphony = Symphony(movements=[m_extract, m_list_and_conclude], null_answer_break=True)
    res = symphony.perform(prompt)
    answer = res[0]["answer"]
    print(f"\n\n{answer}")


if __name__ == "__main__":
    main()
