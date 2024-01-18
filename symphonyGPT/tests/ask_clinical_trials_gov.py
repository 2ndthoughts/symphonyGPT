import chromadb

from symphonyGPT.performers.api_extractor.secondthoughts.clinical_trials_gov_extractor import CTGExtractor
from symphonyGPT.performers.language_model.openai_performers.gpt_4 import Gpt4
from symphonyGPT.symphony.classifier.huggingface.ade_drug_effect_token_classifier import \
    AdeDrugEffectTokenClassifier
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony


# in this example, make sure to get an openai api key according to this page
# https://platform.openai.com/account/api-keys and update the api_key in the file
# symphonyGPT/performers/api_keys.py

def main() -> None:

    prompt = "does taking magnesium reduce high blood pressure"

    # The symphony is composed of two movements
    #  * The first movement is to extract the drug and effect from the prompt then list all
    #  * the studies from clinicaltrials.gov based on the extracted drug and effect
    #
    #  * The second movement is to generate a conclusion based on the extracted drug and effect
    #  * and the list of studies from clinicaltrials.gov

    m_extract = Movement(
        prompt_classifier=[AdeDrugEffectTokenClassifier()],
        # use classifier to extract drug and effect as api search terms
        performers=[CTGExtractor(max_trials_returned=10)]
    )

    m_list_and_conclude = Movement(
        prompt_str="Generate an article with title and a conclusion related to '" + prompt +
                   "' and list all the studies by NCTId, BriefTitle, LeadSponsorName, CompletionDate and a summary of"
                   "DetailedDescription from this list of studies : {} ",
        performers=[Gpt4()]
    )

    print(prompt)
    symphony = Symphony(movements=[m_extract, m_list_and_conclude], null_answer_break=True)
    res = symphony.perform(prompt)
    answer = res[0]["answer"]
    print(f"\n\n{answer}")


if __name__ == "__main__":
    main()
