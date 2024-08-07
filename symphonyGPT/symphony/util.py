import io
import random
import re
import string
import sys
import chromadb
import demjson3
import numpy as np
from colorama import Fore
import xml.etree.ElementTree as ET


class Util:
    debug = False

    def __init__(self):
        pass

    def _message_print(self, message, color):
        print(color + message + Fore.RESET)

    def serialize_float32(obj):
        if isinstance(obj, np.float32):
            return float(obj)
        raise TypeError("Type not serializable")

    def debug_print(self, message):
        if Util.debug:
            self._message_print(message, Fore.GREEN)

    def debug_print_line(self):
        if Util.debug:
            self._message_print("--------------------------------------------------", Fore.GREEN)

    def error_print(self, message):
        self._message_print(message, Fore.RED)

    def error_print_line(self):
        self._message_print("--------------------------------------------------", Fore.RED)

    def print(self, message):
        self._message_print(message, Fore.WHITE)

    def print_line(self):
        self._message_print("--------------------------------------------------", Fore.WHITE)

    def print_collection_counts(self):
        self.print_line()
        self.print("Collection Counts")
        self.print_line()
        db_client = chromadb.Client()
        for collection in db_client.list_collections():
            self.print(f"{collection.name}: {collection.count()}")
        self.print_line()

    def print_boxed_text(self, text):
        # Determine the length of the longest line
        max_length = max(len(line) for line in text.split('\n'))

        # Create the top border
        top_border = '+' + '-' * (max_length + 2) + '+'

        # Print the top border
        print(top_border)

        # Print each line of text within borders
        for line in text.split('\n'):
            print('| ' + line.ljust(max_length) + ' |')

        # Print the bottom border
        print(top_border)

    def get_collection(self, name):
        db_client = chromadb.Client()
        return db_client.get_or_create_collection(name=name)

    def add_to_collection(self, name, data):
        collection = self.get_collection(name)
        collection.add(data)


    def extract_answer(self, answer):
        if isinstance(answer, str):
            try:
                answer = demjson3.decode(answer)  # convert to json
            except demjson3.JSONDecodeError:
                pass

        try:
            if isinstance(answer, list):  # if its an array
                if len(answer) > 1:
                    return [item['answer'] for item in answer if 'answer' in item]
                elif len(answer) == 1:
                    return answer[0]['answer']
                else:
                    return "No answer found"
            else:  # not an array
                if isinstance(answer, dict) and 'answer' in answer:
                    return answer['answer']
                else:
                    return answer
        except TypeError:
            return answer

    def xml_to_text(self, xml_string):
        root = ET.fromstring(xml_string)
        return ''.join(root.itertext())

    def extract_between(self, text, sub1, sub2):
        """
        Extracts a substring from 'text' that is between the first occurrences of 'sub1' and 'sub2'
        """
        pattern = re.escape(sub1) + '(.*?)' + re.escape(sub2)
        matches = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            self.debug_print(f"extract_between:\n{matches.group(1).strip()}")
            return matches.group(1).strip()
        return None

    def capture_exec_output(self, code):
        # Create an in-memory text stream
        buffer = io.StringIO()

        # Backup the current stdout
        original_stdout = sys.stdout

        # Redirect stdout to the buffer
        sys.stdout = buffer

        try:
            # Execute the code
            exec(code, globals())
        finally:
            # Restore the original stdout
            sys.stdout = original_stdout

        # Return the content of the buffer
        return buffer.getvalue()

    def random_string(self, length):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))
