from symphonyGPT.performers.language_model.configurable_chat_completion_performer import ConfigurableChatCompletionPerformer

class ConfigurableModelPerformer(ConfigurableChatCompletionPerformer):

    def __init__(self, api_name="openai", model_name="gpt-4.1-mini"):
        super().__init__()
        self.set_api_name(api_name)
        self.set_model_attribute("model", model_name)

    def perform(self, prompt):
        return super().perform(prompt)
