from symphonyGPT.performers.language_model.openai.completion_performer import CompletionPerformer


class TextDavinci002(CompletionPerformer):

    def __init__(self):
        super().__init__()
        self.set_model_attribute("model", "text-davinci-002")
        self.set_model_attribute("temperature", 0)
        self.set_model_attribute("top_p", 1)
        self.set_model_attribute("n", 1)

    def perform(self, prompt):
        return super().perform(prompt)
