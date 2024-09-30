import sys

import openai
from symphonyGPT.performers.language_model.openai_performers.openai_performer import OpenAIPerformer


class ChatCompletionPerformer(OpenAIPerformer):

    def __init__(self):
        super().__init__()
        # dont restrict the output number of tokens
        # self.set_model_attribute("max_tokens", 500) # maximium number of tokens to generate

    def perform(self, prompt):
        user_prompt = prompt.get_prompt()

        message_array =[{"role": "system", "content": prompt.system_prompt}]

        # if previous_prompt and previous_response are set, add them to the message array
        if prompt.previous_prompt is not None and prompt.previous_response is not None:
            message_array.append({"role": "user", "content": prompt.previous_prompt})
            message_array.append({"role": "assistant", "content": prompt.previous_response})

        # now add the user prompt
        message_array.append({"role": "user", "content": user_prompt})
        try:
            response = openai.ChatCompletion.create(
                **self.get_model_attributes(),
                messages=message_array
            )
        except Exception as e:
            print("\n\nChatCompletionPerformer: " + str(e) + "\n", flush=True, file=sys.stderr)
            return None

        self.set_raw_response(response.choices[0].message.content)

    def set_model_attribute(self, key, value):
        super().set_model_attribute(key, value)

    def get_model_attribute(self, key):
        return super().get_model_attribute(key)
