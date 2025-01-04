from symphonyGPT.performers.language_model.xai_performers.grok_beta import GrokBeta
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.outcome_strategy.outcome_strategy import OutcomeStrategy
from symphonyGPT.symphony.symphony import Symphony


# in this example, make sure to get an openai api key according to this page
# https://platform.openai.com/account/api-keys and update the api_key in the file
# symphonyGPT/performers/api_keys.py


def main() -> None:
    prompt = "Translate to Chinese 'How are you'"

    movement_chinese = Movement(
        performers=[GrokBeta()],
        outcome_strategy=OutcomeStrategy(format="answer_only")
    )
    movement_german = Movement(
        prompt_str="translate to German: {}",  # pass the result of the previous movement to the next movement using {}
        performers=[GrokBeta()],
        outcome_strategy=OutcomeStrategy(format="answer_only")
    )

    movement_french = Movement(
        prompt_str="translate to French: {}",
        performers=[GrokBeta()],
        outcome_strategy=OutcomeStrategy(format="answer_only")
    )

    movement_english = Movement(
        prompt_str="translate to English: {}",
        performers=[GrokBeta()]
        # the last one is not an array
    )

    symphony = Symphony(movements=[movement_chinese, movement_german, movement_french, movement_english])
    res = symphony.perform(prompt)
    answer = res[0]["answer"]
    print(f"\n\n{answer}")


if __name__ == "__main__":
    main()
