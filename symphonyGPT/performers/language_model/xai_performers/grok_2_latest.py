from symphonyGPT.performers.language_model.xai_performers.chat_completion_performer import ChatCompletionPerformer

class Grok2Latest(ChatCompletionPerformer):

    def __init__(self):
        super().__init__()
        self.set_model_attribute("model", "grok-2-latest")

    def perform(self, prompt):
        return super().perform(prompt)
