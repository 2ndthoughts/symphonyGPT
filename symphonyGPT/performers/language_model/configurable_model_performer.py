from symphonyGPT.performers.language_model.configurable_chat_completion_performer import ConfigurableChatCompletionPerformer

class ConfigurableModelPerformer(ConfigurableChatCompletionPerformer):

    def __init__(self, api_name="openai", model_name="gpt-4.1-mini", max_conversation_length=10):
        super().__init__()
        # if model name contains / the first part is api_name
        if model_name.find("/") != -1:
            api_name = model_name.split("/")[0]
            model_name = model_name.split("/")[1]

        self.set_api_name(api_name)
        self.set_model_attribute("model", model_name)
        self.set_max_conversation_length(max_conversation_length)

    def perform(self, prompt):
        return super().perform(prompt)
