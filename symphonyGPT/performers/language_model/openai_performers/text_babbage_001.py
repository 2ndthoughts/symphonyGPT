from symphonyGPT.performers.language_model.openai_performers.completion_performer import CompletionPerformer


class TextBabbage001(CompletionPerformer):

    def __init__(self):
        super().__init__()
        self.set_model_attribute("model", "text-babbage-001")
        self.set_model_attribute("temperature", 0)
        self.set_model_attribute("top_p", 1)
        self.set_model_attribute("n", 1)

    def perform(self, prompt):
        return super().perform(prompt)
