from symphonyGPT.performers.language_model.openai_performers.gpt_35_turbo_0301 import Gpt35Turbo0301
from symphonyGPT.performers.language_model.openai_performers.text_ada_001 import TextAda001
from symphonyGPT.performers.language_model.openai_performers.text_babbage_001 import TextBabbage001
from symphonyGPT.performers.language_model.openai_performers.text_curie_001 import TextCurie001
from symphonyGPT.performers.language_model.openai_performers.text_davinci_002 import TextDavinci002
from symphonyGPT.performers.language_model.openai_performers.text_davinci_003 import TextDavinci003
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.outcome_strategy.huggingface.sentiment_all_positive import SentimentAllPositive
from symphonyGPT.symphony.symphony import Symphony

# in this example, make sure to get an openai api key according to this page
# https://platform.openai.com/account/api-keys and update the api_key in the file
# symphonyGPT/performers/api_keys.py


def main() -> None:
    prompt = "Which is a species of fish? Tope or Rope. Give only the answer in a word"

    movement_1 = Movement(
        performers=[
            TextCurie001(),
            TextBabbage001(),
            TextAda001(),
            TextDavinci002(),
            TextDavinci003(),
            Gpt35Turbo0301()
        ],
        outcome_strategy=SentimentAllPositive(format="answer_only")
    )
    print(prompt)
    symphony = Symphony(movements=[movement_1])
    res = symphony.perform(prompt)
    print(f"\n\n{res}")


if __name__ == "__main__":
    main()
