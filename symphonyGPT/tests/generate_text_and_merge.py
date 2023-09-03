from symphonyGPT.performers.language_model.openai_performers.gpt_35_turbo_0301 import Gpt35Turbo0301
from symphonyGPT.performers.language_model.openai_performers.gpt_4 import Gpt4
from symphonyGPT.performers.language_model.openai_performers.text_ada_001 import TextAda001
from symphonyGPT.performers.language_model.openai_performers.text_babbage_001 import TextBabbage001
from symphonyGPT.performers.language_model.openai_performers.text_curie_001 import TextCurie001
from symphonyGPT.performers.language_model.openai_performers.text_davinci_002 import TextDavinci002
from symphonyGPT.performers.language_model.openai_performers.text_davinci_003 import TextDavinci003
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony


# in this example, make sure to get an openai api key according to this page
# https://platform.openai.com/account/api-keys and update the api_key in the file
# symphonyGPT/performers/language_model/openai/openai_performer.py


def main() -> None:
    prompt = "complete the sentence: To be or not to be"

    movement_1 = Movement(
        performers=[
            TextCurie001(),
            TextBabbage001(),
            TextAda001(),
            TextDavinci002(),
            TextDavinci003(),
            Gpt35Turbo0301()
        ]
    )
    movement_combine_answers = Movement(
        prompt_str="Merge the text in the answer attributes elegantly: {}",
        performers=[Gpt4()]
    )

    symphony = Symphony(movements=[movement_1, movement_combine_answers])
    res = symphony.perform(prompt)
    answer = res[0]["answer"]
    print(f"\n\n{answer}")


if __name__ == "__main__":
    main()
