from symphonyGPT.performers.language_model.openai_performers.chat_completion_performer import ChatCompletionPerformer


class Gpt4(ChatCompletionPerformer):

    def __init__(self):
        super().__init__()
        self.set_model_attribute("model", "gpt-4-turbo-preview")

    def perform(self, prompt):
        return super().perform(prompt)
