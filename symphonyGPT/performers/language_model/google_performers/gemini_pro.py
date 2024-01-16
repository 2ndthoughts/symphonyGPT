import google.generativeai as genai
from symphonyGPT.performers.language_model.language_model_performer import LanguageModelPerformer
from symphonyGPT.performers.api_keys import APIKeys


class GeminiPro(LanguageModelPerformer):
    def __init__(self):
        super().__init__()
        self.set_model_attribute("model", "gemini-pro")
        api_keys = APIKeys()
        GOOGLE_API_KEY = api_keys.get_api_key("gemini")
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    def perform(self, prompt):
        response = self.model.generate_content(prompt.get_prompt())
        self.set_raw_response(response.candidates[0].content.parts)
