from symphonyGPT.performers.language_model.configurable_model_performer import ConfigurableModelPerformer
from symphonyGPT.performers.language_model.openai_performers.gpt_35_turbo_0301 import Gpt35Turbo0301
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.outcome_strategy.huggingface.sentiment_all_positive import SentimentAllPositive
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
    prompt = "Which is a species of fish? Tope or Rope. Give only the answer in a word"

    movement_1 = Movement(
        performers=[
            config_performer,
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
