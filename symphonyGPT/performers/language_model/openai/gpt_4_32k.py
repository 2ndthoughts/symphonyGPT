from symphonyGPT.performers.language_model.openai.chat_completion_performer import ChatCompletionPerformer

# you must have the license to access this model
class Gpt4_32k(ChatCompletionPerformer):

    def __init__(self):
        super().__init__()
        self.set_model_attribute("model", "gpt-4-32k")

    def perform(self, prompt):
        return super().perform(prompt)
