import numpy as np
from colorama import Fore
import xml.etree.ElementTree as ET

class Util:
    def __init__(self):
        self.debug = True

    def _message_print(self, message, color):
        print(color + message + Fore.RESET)

    def serialize_float32(obj):
        if isinstance(obj, np.float32):
            return float(obj)
        raise TypeError("Type not serializable")

    def debug_print(self, message):
        if self.debug:
            self._message_print(message, Fore.GREEN)

    def debug_print_line(self):
        if self.debug:
            self._message_print("--------------------------------------------------", Fore.GREEN)

    def error_print(self, message):
        self._message_print(message, Fore.RED)

    def error_print_line(self):
        self._message_print("--------------------------------------------------", Fore.RED)

    def print(self, message):
        self._message_print(message, Fore.WHITE)

    def print_line(self):
        self._message_print("--------------------------------------------------", Fore.WHITE)

    def extract_answer(self, answer):
        if isinstance(answer, list):  # if its an array
            if len(answer) > 1:
                return [item['answer'] for item in answer if 'answer' in item]
            elif len(answer) == 1:
                return answer[0]['answer']
            else:
                return "No answer found"
        else:  # not an array
            if isinstance(answer, dict):
                return answer['answer']
            else:
                return answer

    def xml_to_text(self, xml_string):
        root = ET.fromstring(xml_string)
        return ''.join(root.itertext())