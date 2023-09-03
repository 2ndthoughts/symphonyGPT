from symphonyGPT.performers.language_model.openai.gpt_4 import Gpt4
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.outcome_strategy.outcome_strategy import OutcomeStrategy
from symphonyGPT.symphony.symphony import Symphony


# in this example, make sure to get an openai api key according to this page
# https://platform.openai.com/account/api-keys and update the api_key in the file
# symphonyGPT/performers/language_model/openai/openai_performer.py
#
# also make sure to get a huggingface api key according to this page https://huggingface.co/settings/tokens
# and update the api_key in the file symphonyGPT/symphony/classifier/huggingface/huggingface_performer.py


def main() -> None:
    prompt = "Translate to Chinese 'How are you'"

    movement_chinese = Movement(
        performers=[Gpt4()],
        outcome_strategy=OutcomeStrategy(format="answer_only")
    )
    movement_german = Movement(
        prompt_str="translate to German: {}",  # pass the result of the previous movement to the next movement using {}
        performers=[Gpt4()],
        outcome_strategy=OutcomeStrategy(format="answer_only")
    )

    movement_french = Movement(
        prompt_str="translate to French: {}",
        performers=[Gpt4()],
        outcome_strategy=OutcomeStrategy(format="answer_only")
    )

    movement_english = Movement(
        prompt_str="translate to English: {}",
        performers=[Gpt4()]
        # the last one is not an array
    )

    symphony = Symphony(movements=[movement_chinese, movement_german, movement_french, movement_english])
    res = symphony.perform(prompt)
    answer = res[0]["answer"]
    print(f"\n\n{answer}")


if __name__ == "__main__":
    main()
