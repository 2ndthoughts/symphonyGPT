import openai
from symphonyGPT.performers.language_model.openai.openai_performer import OpenAIPerformer


class CompletionPerformer(OpenAIPerformer):

    def __init__(self):
        super().__init__()
        # dont set the maximum output tokens
        # self.set_model_attribute("max_tokens", 500)
        self.set_model_attribute("temperature", 0.9)
        self.set_model_attribute("top_p", 1)
        self.set_model_attribute("n", 1)
        self.set_model_attribute("stream", False)

    def perform(self, prompt):
        self.set_model_attribute("prompt", prompt.get_prompt())
        response = openai.Completion.create(
            **self.get_model_attributes()
        )
        self.set_raw_response(response.choices[0].text.strip())

    def set_model_attribute(self, key, value):
        super().set_model_attribute(key, value)

    def get_model_attribute(self, key):
        return super().get_model_attribute(key)