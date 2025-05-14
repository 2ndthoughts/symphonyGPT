from openai import OpenAI

from symphonyGPT.performers.api_keys import APIKeys
from symphonyGPT.performers.language_model.xai_performers.xai_performer import XAIPerformer


class ChatCompletionPerformer(XAIPerformer):
    conversation_array = []

    def __init__(self):
        super().__init__()
        # don't restrict the output number of tokens
        # self.set_model_attribute("max_tokens", 500) # maximium number of tokens to generate

    def perform(self, prompt):
        user_prompt = prompt.get_prompt()

        # if the conversation_array is empty, add the system prompt
        if len(ChatCompletionPerformer.conversation_array) == 0:
            if prompt.system_prompt is None:
                ChatCompletionPerformer.conversation_array.append({"role": "system", "content": "You are a helpful assistant."})
            else:
                ChatCompletionPerformer.conversation_array.append({"role": "system", "content": prompt.system_prompt})

        # if previous_prompt and previous_response are set, add them to the message array
        if prompt.previous_prompt is not None and prompt.previous_response is not None:
            ChatCompletionPerformer.conversation_array.append({"role": "user", "content": prompt.previous_prompt})
            ChatCompletionPerformer.conversation_array.append({"role": "assistant", "content": prompt.previous_response})

        # now add the user prompt
        ChatCompletionPerformer.conversation_array.append({"role": "user", "content": user_prompt})
        try:
            client = OpenAI(
                api_key=APIKeys().get_api_key("xai"),
                base_url="https://api.x.ai/v1",
            )

            completion = client.chat.completions.create(
                **self.get_model_attributes(),
                messages=ChatCompletionPerformer.conversation_array
            )
        except Exception as e:
            error_str = str(e)
            error_str = error_str.replace("\r", " ")
            error_str = error_str.replace("\n", " ")
            self.set_raw_response("Error: '" + error_str + "'")
            return None

        self.set_raw_response(completion.choices[0].message.content)

        # add the response to the conversation array
        ChatCompletionPerformer.conversation_array.append({"role": "assistant", "content": completion.choices[0].message.content})
        # if conversation_array is more than 10, keep the first item and remove the next
        if len(ChatCompletionPerformer.conversation_array) > 10:
            ChatCompletionPerformer.conversation_array = [ChatCompletionPerformer.conversation_array[0]] + ChatCompletionPerformer.conversation_array[-9:]

        return None

    def set_model_attribute(self, key, value):
        super().set_model_attribute(key, value)

    def get_model_attribute(self, key):
        return super().get_model_attribute(key)
