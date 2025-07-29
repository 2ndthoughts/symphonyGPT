from symphonyGPT.performers.language_model.configurable_model_performer import ConfigurableModelPerformer
from symphonyGPT.performers.language_model.openai_performers.gpt_4o_mini import Gpt4oMini
from symphonyGPT.performers.language_model.xai_performers.grok_beta import GrokBeta
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.outcome_strategy.outcome_strategy import OutcomeStrategy
from symphonyGPT.symphony.symphony import Symphony


# in this example, make sure to get an openai api key according to this page
# https://platform.openai.com/account/api-keys and update the api_key in the file
# symphonyGPT/performers/api_keys.py

api_name = "openai"
api_model_name = "gpt-4.1-mini"

#api_name = "xai"
#api_model_name = "grok-4-0709"
#api_model_name = "grok-3-mini"

config_performer = ConfigurableModelPerformer(api_name, api_model_name)

def main() -> None:
    prompt = "Translate to Chinese 'How are you'"

    movement_chinese = Movement(
        performers=[config_performer],
        #outcome_strategy=OutcomeStrategy(format="answer_only")
    )
    movement_german = Movement(
        prompt_str="translate to German: {}",  # pass the result of the previous movement to the next movement using {}
        performers=[config_performer],
        #outcome_strategy=OutcomeStrategy(format="answer_only")
    )

    movement_french = Movement(
        prompt_str="translate to French: {}",
        performers=[config_performer],
        #outcome_strategy=OutcomeStrategy(format="answer_only")
    )

    movement_english = Movement(
        prompt_str="translate to English: {}",
        performers=[config_performer]
        # the last one is not an array
    )

    symphony = Symphony(movements=[movement_chinese, movement_german, movement_french, movement_english])
    res = symphony.perform(prompt)
    answer = res[0]["answer"]
    print(f"\n\n{answer}")


if __name__ == "__main__":
    main()
