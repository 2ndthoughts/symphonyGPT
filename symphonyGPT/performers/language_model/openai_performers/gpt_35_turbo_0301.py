from symphonyGPT.performers.language_model.openai_performers.chat_completion_performer import ChatCompletionPerformer


class Gpt35Turbo0301(ChatCompletionPerformer):

    def __init__(self):
        super().__init__()
        self.set_model_attribute("model", "gpt-3.5-turbo-0301")

    def perform(self, prompt):
        return super().perform(prompt)
