from symphonyGPT.performers.language_model.openai_performers.chat_completion_performer import ChatCompletionPerformer


class Gpt41Mini(ChatCompletionPerformer):

    def __init__(self):
        super().__init__()
        self.set_model_attribute("model", "gpt-4.1-mini")

    def perform(self, prompt):
        return super().perform(prompt)
