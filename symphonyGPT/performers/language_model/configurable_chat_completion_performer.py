import io
import logging
import math
import os
import re
import sys
import threading
import time
from contextlib import contextmanager
from openai import OpenAI

from symphonyGPT.performers.api_keys import APIKeys
from symphonyGPT.performers.language_model.openai_performers.openai_performer import OpenAIPerformer

INFERENCE_FLASH_INTERVAL_SEC = 0.25
_THINK_BLOCK_RE = re.compile(
    r"(?is)"
    r"<think\b[^>]*>.*?</think>"
    r"|<thinking\b[^>]*>.*?</thinking>"
    r"|◁think▷.*?◁/?think▷"
    r"|<\|begin_of_thought\|>.*?<\|end_of_thought\|>"
)
_STDIO_GATE = threading.RLock()
_STDIO_DEPTH = 0
_ORIG_STDOUT = None
_ORIG_STDERR = None
_SAVED_STDERR_FD = None
_DEVNULL_FD = None
_SAVED_STDOUT_FD = None


class _ProtocolStdio:
    """Drop model traces; keep only Orchestra protocol lines (live_log / flash_message)."""

    _PASS_PREFIXES = ("live_log: ", "flash_message: ")

    def __init__(self, out_fd):
        self._out_fd = out_fd
        self._buf = ""

    def write(self, data):
        if not data:
            return 0
        if isinstance(data, bytes):
            data = data.decode("utf-8", errors="replace")
        self._buf += data
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            self._forward(line + "\n")
        return len(data)

    def _forward(self, line):
        if line.lstrip("\ufeff").startswith(self._PASS_PREFIXES):
            os.write(self._out_fd, line.encode("utf-8"))

    def flush(self):
        if self._buf:
            self._forward(self._buf if self._buf.endswith("\n") else self._buf + "\n")
            self._buf = ""

    def isatty(self):
        return False

    def fileno(self):
        # Do not expose the real fd; writers would bypass this filter.
        raise io.UnsupportedOperation("fileno")

    def __getattr__(self, name):
        if name in ("fileno", "buffer"):
            raise AttributeError(name)
        raise AttributeError(name)


@contextmanager
def _quiet_inference_stdio():
    """Hide thinking/SSE on both Python streams and the real stdout/stderr fds."""
    global _STDIO_DEPTH, _ORIG_STDOUT, _ORIG_STDERR, _SAVED_STDERR_FD, _DEVNULL_FD
    global _SAVED_STDOUT_FD
    with _STDIO_GATE:
        if _STDIO_DEPTH == 0:
            _ORIG_STDOUT, _ORIG_STDERR = sys.stdout, sys.stderr
            try:
                _SAVED_STDOUT_FD = os.dup(1)
                _SAVED_STDERR_FD = os.dup(2)
                _DEVNULL_FD = os.open(os.devnull, os.O_WRONLY)
                quiet = _ProtocolStdio(_SAVED_STDOUT_FD)
                sys.stdout = quiet
                sys.stderr = quiet
                os.dup2(_DEVNULL_FD, 1)
                os.dup2(_DEVNULL_FD, 2)
            except Exception:
                sys.stdout = _ORIG_STDOUT
                sys.stderr = _ORIG_STDERR
                _SAVED_STDOUT_FD = None
                _SAVED_STDERR_FD = None
                _DEVNULL_FD = None
        _STDIO_DEPTH += 1
    try:
        yield
    finally:
        with _STDIO_GATE:
            _STDIO_DEPTH -= 1
            if _STDIO_DEPTH == 0:
                try:
                    sys.stdout.flush()
                except Exception:
                    pass
                if _SAVED_STDOUT_FD is not None:
                    try:
                        os.dup2(_SAVED_STDOUT_FD, 1)
                        os.close(_SAVED_STDOUT_FD)
                    except Exception:
                        pass
                    _SAVED_STDOUT_FD = None
                if _SAVED_STDERR_FD is not None:
                    try:
                        os.dup2(_SAVED_STDERR_FD, 2)
                        os.close(_SAVED_STDERR_FD)
                    except Exception:
                        pass
                    _SAVED_STDERR_FD = None
                if _DEVNULL_FD is not None:
                    try:
                        os.close(_DEVNULL_FD)
                    except Exception:
                        pass
                    _DEVNULL_FD = None
                sys.stdout = _ORIG_STDOUT
                sys.stderr = _ORIG_STDERR


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

                # Always stream so reasoning/thinking stays off the visible answer
                # (and off stdout) even when no flash callback is wired, e.g. insights.
                completion_content = self._complete_chat_with_flash(
                    client, ConfigurableChatCompletionPerformer.conversation_array, title, flash_cb)
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
        with _quiet_inference_stdio():
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
                return self._visible_completion(reasoning, content)

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
            delta = getattr(chunk.choices[0], "delta", None)
            reasoning_delta, content_delta = self._delta_parts(delta)
            if not reasoning_delta and not content_delta:
                reasoning_delta, content_delta = self._delta_parts(
                    getattr(chunk.choices[0], "message", None))
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
        return self._visible_completion(reasoning, content)

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

    def _strip_thinking_markup(self, text):
        if not text:
            return ""
        return _THINK_BLOCK_RE.sub("", text).strip()

    def _visible_completion(self, reasoning, content):
        visible = self._strip_thinking_markup(content or "")
        if visible:
            return visible
        # Some models only fill reasoning_content; use it only after stripping traces.
        return self._strip_thinking_markup(reasoning or "")

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
        # Use <br> so a callback that prints to stdout cannot split this across
        # lines and leak "Thinking..." into the browser echo.
        flash_cb(f"**{title}**<br>{status}|in_process")

    def _coerce_text(self, value, allow_thinking=False):
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return "".join(self._coerce_text(item, allow_thinking=allow_thinking) for item in value)
        if isinstance(value, dict):
            part_type = str(value.get("type") or "").lower()
            if part_type in ("thinking", "reasoning") and not allow_thinking:
                return ""
            text = (
                value.get("thinking") if part_type in ("thinking", "reasoning") else None
            ) or value.get("content") or value.get("text") or value.get("reasoning")
            return text if isinstance(text, str) else self._coerce_text(text, allow_thinking=allow_thinking) if text else ""
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

    def _first_text(self, *values, allow_thinking=False):
        for value in values:
            piece = self._coerce_text(value, allow_thinking=allow_thinking)
            if piece:
                return piece
        return ""

    def _delta_parts(self, delta):
        if delta is None:
            return "", ""

        data = self._as_dict(delta)
        reasoning = ""
        for key in ("reasoning_content", "reasoning", "thinking", "reasoning_text"):
            piece = self._first_text(data.get(key), getattr(delta, key, None), allow_thinking=True)
            if piece:
                reasoning += piece
        content_value = data.get("content")
        if isinstance(content_value, list):
            for item in content_value:
                if isinstance(item, dict) and str(item.get("type") or "").lower() in ("thinking", "reasoning"):
                    reasoning += self._coerce_text(item, allow_thinking=True)
        content = self._first_text(content_value, getattr(delta, "content", None))
        return reasoning, content

    def _message_parts(self, message):
        if message is None:
            return "", ""
        reasoning, content = self._delta_parts(message)
        if not content:
            content = self._coerce_text(getattr(message, "content", None))
        return reasoning, content
