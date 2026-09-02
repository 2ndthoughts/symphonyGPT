import logging
import math
import time
from openai import OpenAI

from symphonyGPT.performers.api_keys import APIKeys
from symphonyGPT.performers.language_model.openai_performers.openai_performer import OpenAIPerformer

INFERENCE_FLASH_INTERVAL_SEC = 0.25


class ConfigurableChatCompletionPerformer(OpenAIPerformer):
    conversation_array = []

    def __init__(self):
        super().__init__()
        self.api_name = None
        self.max_conversation_length = 1 # default
        self.max_tokens = 256000 # default
        self.api_key = None
        self.api_base_url = None
        self.flash_message_func = None
        self.flash_message_title = None

    def set_max_tokens(self, max_tokens):
        self.max_tokens = max_tokens

    def set_max_conversation_length(self, length):
        self.max_conversation_length = length

    def set_api_name(self, api_name):
        self.api_name = api_name

    def set_api_key(self, api_key):
        self.api_key = api_key

    def set_api_base_url(self, api_base_url):
        self.api_base_url = api_base_url

    def perform(self, prompt):
        user_prompt = prompt.get_prompt()
        flash_cb = getattr(self, "flash_message_func", None)
        title = getattr(self, "flash_message_title", None) or "Generating"

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

        if self.api_key is None:
            self.api_key = APIKeys().get_api_key(self.api_name)
            if self.api_key is None:
                self.set_raw_response("Error: No API key found for xai")
                return None

        if self.api_base_url is None:
            self.api_base_url = APIKeys().get_api_base_url(self.api_name)
            if self.api_base_url is None:
                self.set_raw_response("Error: No API base URL found for xai")
                return None

        tries = 0
        completion_content = None
        while tries < 3:
            tries += 1
            # now add the user prompt
            ConfigurableChatCompletionPerformer.conversation_array.append({"role": "user", "content": user_prompt})
            try:
                client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base_url
                )

                if flash_cb is not None:
                    completion_content = self._complete_chat_with_flash(
                        client, ConfigurableChatCompletionPerformer.conversation_array, title, flash_cb)
                else:
                    completion = client.chat.completions.create(
                        **self.get_model_attributes(),
                        messages=ConfigurableChatCompletionPerformer.conversation_array
                    )
                    reasoning, content = self._message_parts(completion.choices[0].message)
                    completion_content = content or reasoning
                break
            except Exception as e:
                error_str = str(e)
                error_str = error_str.replace("\r", " ")
                error_str = error_str.replace("\n", " ")
                self.set_raw_response("Error: '" + error_str + "'")

                logging.debug(f"{error_str} retrying {tries}/3")

                # pop until conversation array is empty
                while len(ConfigurableChatCompletionPerformer.conversation_array) > 0:
                    ConfigurableChatCompletionPerformer.conversation_array.pop()

        if completion_content is None:
            self.set_raw_response("Error: Unable to get response from API")
        else:
            self.set_raw_response(completion_content)

        if completion_content is not None:
            if prompt.is_append_conversation():
                ConfigurableChatCompletionPerformer.conversation_array.append(
                    {"role": "assistant", "content": completion_content})
            elif ConfigurableChatCompletionPerformer.conversation_array:
                ConfigurableChatCompletionPerformer.conversation_array.pop()

        # if conversation_array is more than 10, keep the first item and remove the next
        if len(ConfigurableChatCompletionPerformer.conversation_array) > self.max_conversation_length:
            ConfigurableChatCompletionPerformer.conversation_array = [ConfigurableChatCompletionPerformer.conversation_array[0]] + ConfigurableChatCompletionPerformer.conversation_array[-9:]

        # get the maximum model context tokens for the model
        model_name = self.get_model_attribute("model")
        max_tokens = APIKeys().get_model_context_max_tokens(model_name)
        if self.max_tokens is not None and max_tokens is not None and max_tokens < self.max_tokens:
            max_tokens = self.max_tokens

        # if the total number of tokens in the conversation array exceeds 1,047,576, remove the first item
        total_tokens = sum(len(msg['content'].split()) for msg in ConfigurableChatCompletionPerformer.conversation_array)
        while total_tokens > max_tokens:
            ConfigurableChatCompletionPerformer.conversation_array = [ConfigurableChatCompletionPerformer.conversation_array[0]] + ConfigurableChatCompletionPerformer.conversation_array[-9:]
            total_tokens = sum(
                len(msg['content'].split()) for msg in ConfigurableChatCompletionPerformer.conversation_array)

        return None

    def _complete_chat_with_flash(self, client, messages, title, flash_cb):
        self._inference_flash_started = time.monotonic()
        self._emit_inference_flash(flash_cb, title, "", "", waiting=True)
        try:
            return self._complete_chat_stream(client, messages, title, flash_cb)
        except Exception as stream_exc:
            logging.debug(f"streaming completion failed, falling back: {stream_exc}")
            completion = client.chat.completions.create(
                **self.get_model_attributes(),
                messages=messages
            )
            message = completion.choices[0].message
            reasoning, content = self._message_parts(message)
            self._emit_inference_flash(flash_cb, title, reasoning, content or "", done=True)
            return content or reasoning or ""

    def _complete_chat_stream(self, client, messages, title, flash_cb):
        kwargs = dict(self.get_model_attributes())
        kwargs["stream"] = True
        stream = client.chat.completions.create(messages=messages, **kwargs)

        reasoning_parts = []
        content_parts = []
        last_emit = 0.0

        for chunk in stream:
            if not getattr(chunk, "choices", None):
                continue
            delta = chunk.choices[0].delta
            reasoning_delta, content_delta = self._delta_parts(delta)
            if reasoning_delta:
                reasoning_parts.append(reasoning_delta)
            if content_delta:
                content_parts.append(content_delta)
            if not reasoning_delta and not content_delta:
                continue

            now = time.monotonic()
            if last_emit and (now - last_emit) < INFERENCE_FLASH_INTERVAL_SEC:
                continue
            last_emit = now
            self._emit_inference_flash(
                flash_cb, title, "".join(reasoning_parts), "".join(content_parts))

        reasoning = "".join(reasoning_parts)
        content = "".join(content_parts)
        self._emit_inference_flash(flash_cb, title, reasoning, content, done=True)
        return content or reasoning or ""

    def _guess_completion_pct(self, reasoning, content, waiting=False, done=False):
        if done:
            return 100

        elapsed = 0.0
        started = getattr(self, "_inference_flash_started", None)
        if started:
            elapsed = max(0.0, time.monotonic() - started)

        reasoning_len = len(reasoning or "")
        content_len = len(content or "")

        if waiting and not reasoning and not content:
            return max(1, min(8, 1 + int(elapsed)))

        # Unknown total length: climb toward 90% from tokens and time, never hard-stop at 50%.
        from_text = 90 * (1 - math.exp(-reasoning_len / 8000.0))
        from_time = 90 * (1 - math.exp(-elapsed / 60.0))
        thinking_pct = max(3, min(90, max(from_text, from_time)))

        if content_len == 0:
            return int(round(thinking_pct))

        draft_pct = thinking_pct + (95 - thinking_pct) * (1 - math.exp(-content_len / 800.0))
        return max(int(round(thinking_pct)) + 1, min(95, int(round(draft_pct))))

    def _emit_inference_flash(self, flash_cb, title, reasoning, content, waiting=False, done=False):
        if flash_cb is None:
            return
        pct = self._guess_completion_pct(reasoning, content, waiting=waiting, done=done)
        if done:
            status = f"Done {pct}%"
        elif content:
            status = f"Draft... {pct}%"
        elif reasoning:
            status = f"Thinking... {pct}%"
        else:
            status = f"Waiting for Agent... {pct}%"
        flash_cb(f"**{title}**\n{status}|in_process")

    def _coerce_text(self, value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return "".join(self._coerce_text(item) for item in value)
        if isinstance(value, dict):
            text = value.get("content") or value.get("text") or value.get("reasoning")
            return text if isinstance(text, str) else self._coerce_text(text) if text else ""
        text = getattr(value, "content", None) or getattr(value, "text", None)
        return text if isinstance(text, str) else ""

    def _as_dict(self, obj):
        if obj is None:
            return {}
        if isinstance(obj, dict):
            return obj
        data = {}
        if hasattr(obj, "model_dump"):
            try:
                data = obj.model_dump(exclude_none=True) or {}
            except TypeError:
                data = obj.model_dump() or {}
        extra = getattr(obj, "model_extra", None)
        if isinstance(extra, dict):
            data = {**data, **extra}
        return data

    def _first_text(self, *values):
        for value in values:
            piece = self._coerce_text(value)
            if piece:
                return piece
        return ""

    def _delta_parts(self, delta):
        if delta is None:
            return "", ""

        data = self._as_dict(delta)
        reasoning = ""
        for key in ("reasoning_content", "reasoning", "thinking"):
            piece = self._first_text(data.get(key), getattr(delta, key, None))
            if piece:
                reasoning += piece
        content = self._first_text(data.get("content"), getattr(delta, "content", None))
        return reasoning, content

    def _message_parts(self, message):
        if message is None:
            return "", ""
        reasoning, content = self._delta_parts(message)
        if not content:
            content = self._coerce_text(getattr(message, "content", None))
        return reasoning, content
