import logging

import openai
from openai import APIError, OpenAI

from symphonyGPT.performers.api_keys import APIKeys
from symphonyGPT.performers.language_model.openai_performers.openai_performer import OpenAIPerformer

class ConfigurableChatCompletionPerformer(OpenAIPerformer):
    conversation_array = []

    def __init__(self):
        super().__init__()
        self.api_name = None
        self.max_conversation_length = 10

    def set_max_conversation_length(self, length):
        self.max_conversation_length = length

    def set_api_name(self, api_name):
        self.api_name = api_name

    def perform(self, prompt):
        user_prompt = prompt.get_prompt()

        # if the conversation_array is empty, add the system prompt
        if len(ConfigurableChatCompletionPerformer.conversation_array) == 0:
            if prompt.system_prompt is None:
                ConfigurableChatCompletionPerformer.conversation_array.append({"role": "system", "content": "You are a helpful assistant."})
            else:
                ConfigurableChatCompletionPerformer.conversation_array.append({"role": "system", "content": prompt.system_prompt})

        # if previous_prompt and previous_response are set, add them to the message array
        if prompt.previous_prompt is not None and prompt.previous_response is not None:
            ConfigurableChatCompletionPerformer.conversation_array.append({"role": "user", "content": prompt.previous_prompt})
            ConfigurableChatCompletionPerformer.conversation_array.append({"role": "assistant", "content": prompt.previous_response})

        api_key = APIKeys().get_api_key(self.api_name)
        if api_key is None:
            self.set_raw_response("Error: No API key found for xai")
            return None

        api_base_url = APIKeys().get_api_base_url(self.api_name)
        if api_base_url is None:
            self.set_raw_response("Error: No API base URL found for xai")
            return None

        tries = 0

        while tries < 3:
            tries += 1
            # now add the user prompt
            ConfigurableChatCompletionPerformer.conversation_array.append({"role": "user", "content": user_prompt})
            try:
                client = OpenAI(
                    api_key=api_key,
                    base_url=api_base_url
                )

                completion = client.chat.completions.create(
                    **self.get_model_attributes(),
                    messages=ConfigurableChatCompletionPerformer.conversation_array
                )
            except Exception as e:
                error_str = str(e)
                error_str = error_str.replace("\r", " ")
                error_str = error_str.replace("\n", " ")
                self.set_raw_response("Error: '" + error_str + "'")

                logging.debug(f"{error_str} retrying {tries}/3")

                # pop until conversation array is empty
                while len(ConfigurableChatCompletionPerformer.conversation_array) > 0:
                    ConfigurableChatCompletionPerformer.conversation_array.pop()

                # pop 2 items from the conversation array (the user prompt and the assistant response)
                #ConfigurableChatCompletionPerformer.conversation_array.pop()
                #ConfigurableChatCompletionPerformer.conversation_array.pop()

                #return None

        self.set_raw_response(completion.choices[0].message.content)

        if prompt.is_append_conversation():
            # add the response to the conversation array
            ConfigurableChatCompletionPerformer.conversation_array.append({"role": "assistant", "content": completion.choices[0].message.content})
        else:
            # pop the user prompt
            ConfigurableChatCompletionPerformer.conversation_array.pop()

        # if conversation_array is more than 10, keep the first item and remove the next
        if len(ConfigurableChatCompletionPerformer.conversation_array) > self.max_conversation_length:
            ConfigurableChatCompletionPerformer.conversation_array = [ConfigurableChatCompletionPerformer.conversation_array[0]] + ConfigurableChatCompletionPerformer.conversation_array[-9:]

        # get the maximum model context tokens for the model
        model_name = self.get_model_attribute("model")
        max_tokens = APIKeys().get_model_context_max_tokens(model_name)

        # if the total number of tokens in the conversation array exceeds 1,047,576, remove the first item
        total_tokens = sum(len(msg['content'].split()) for msg in ConfigurableChatCompletionPerformer.conversation_array)
        while total_tokens > max_tokens:
            ConfigurableChatCompletionPerformer.conversation_array = [ConfigurableChatCompletionPerformer.conversation_array[0]] + ConfigurableChatCompletionPerformer.conversation_array[-9:]
            total_tokens = sum(
                len(msg['content'].split()) for msg in ConfigurableChatCompletionPerformer.conversation_array)

        return None
