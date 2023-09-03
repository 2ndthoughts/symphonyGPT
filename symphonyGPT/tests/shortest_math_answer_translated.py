from symphonyGPT.performers.language_model.openai_performers.gpt_35_turbo_0301 import Gpt35Turbo0301
from symphonyGPT.performers.language_model.openai_performers.gpt_4 import Gpt4
from symphonyGPT.performers.language_model.openai_performers.text_ada_001 import TextAda001
from symphonyGPT.performers.language_model.openai_performers.text_babbage_001 import TextBabbage001
from symphonyGPT.performers.language_model.openai_performers.text_curie_001 import TextCurie001
from symphonyGPT.performers.language_model.openai_performers.text_davinci_002 import TextDavinci002
from symphonyGPT.performers.language_model.openai_performers.text_davinci_003 import TextDavinci003
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.outcome_strategy.outcome_strategy import OutcomeStrategy
from symphonyGPT.symphony.outcome_strategy.shortest_answer import ShortestAnswer
from symphonyGPT.symphony.symphony import Symphony


# in this example, make sure to get an openai api key according to this page
# https://platform.openai.com/account/api-keys and update the api_key in the file
# symphonyGPT/performers/language_model/openai/openai_performer.py


def main() -> None:
    question = "What is the square root of 256?"

    m_do_math = Movement(
        performers=[
            TextCurie001(),
            TextBabbage001(),
            TextAda001(),
            TextDavinci002(),
            TextDavinci003(),
            Gpt35Turbo0301()
        ],
        outcome_strategy=ShortestAnswer(format="answer_only")
    )

    m_translate = Movement(
        prompt_str="translate to Chinese: {}",
        performers=[Gpt4()],
        outcome_strategy=OutcomeStrategy(format="answer_only")
    )

    print(question)
    symphony = Symphony(movements=[m_do_math, m_translate])

    res = symphony.perform(question)
    print(f"\n\n{res}")


if __name__ == "__main__":
    main()
