import openai
from symphonyGPT.performers.language_model.openai_performers.openai_performer import OpenAIPerformer


class ChatCompletionPerformer(OpenAIPerformer):

    def __init__(self):
        super().__init__()
        # dont restrict the output number of tokens
        # self.set_model_attribute("max_tokens", 500) # maximium number of tokens to generate

    def perform(self, prompt):
        response = openai.ChatCompletion.create(
            **self.get_model_attributes(),
            messages=[
                {"role": "user", "content": prompt.get_prompt()}
            ]
        )
        self.set_raw_response(response.choices[0].message.content)

    def set_model_attribute(self, key, value):
        super().set_model_attribute(key, value)

    def get_model_attribute(self, key):
        return super().get_model_attribute(key)
