from symphonyGPT.performers.language_model.xai_performers.chat_completion_performer import ChatCompletionPerformer

class GrokBeta(ChatCompletionPerformer):

    def __init__(self):
        super().__init__()
        self.set_model_attribute("model", "grok-3-mini-fast-beta")

    def perform(self, prompt):
        return super().perform(prompt)
