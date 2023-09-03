import torch
from transformers import pipeline
from symphonyGPT.performers.language_model.language_model_performer import LanguageModelPerformer


# example of a performer that uses a huggingface model locally trained on databricks
class DollyV23B(LanguageModelPerformer):

    def __init__(self):
        super().__init__()
        self.set_model_attribute("model", "dolly-v2-3b")

    def perform(self, prompt):
        generate_text = pipeline(model="databricks/dolly-v2-3b",
                                 torch_dtype=torch.bfloat16,
                                 trust_remote_code=True, device_map="auto")
        res = generate_text(prompt)
        self.set_raw_response(res[0]["generated_text"])
