import json
import timeit
from symphonyGPT.symphony.util import Util


class Symphony:

    def __init__(self, prompt_str=None, movements=None, null_answer_break=False):

        self.util = Util()
        self.start_time = None
        self.end_time = None
        self.prompt_str = prompt_str
        if prompt_str is None:
            self.prompt_str = "Do something randomly"  # at the level of Symphony, prompt is a string

        if movements is None:
            movements = []

        self.movements = movements
        self.null_answer_break = null_answer_break
        self.enumerated_responses = ""

    def perform(self, prompt_str=None):
        self.start_time = timeit.default_timer()

        if prompt_str is None:
            prompt_str = self.prompt_str  # still a string here

        movement_output = None
        for movement in self.movements:
            self.util.debug_print(f"Symphony.perform() movement: {self.movements.index(movement)}")
            # if the movement has a prompt_str, override the symphony one
            if movement.prompt.get_prompt() is not None:
                prompt_str = movement.prompt.get_prompt()

            if "{}" in prompt_str and movement_output is not None:
                prompt_str = prompt_str.format(movement_output)

            movement_output = movement.perform(prompt_str, movement_output)
            self.enumerated_responses = f"{self.enumerated_responses}{movement_output}\n"
            movement_output_formatted = json.dumps(movement_output, indent=4)
            self.util.debug_print_line()
            self.util.debug_print(f"Symphony.perform() movement_output: {movement_output_formatted}\n")
            self.util.debug_print_line()

            # if the movement returns a null answer, break
            if self.null_answer_break and (len(movement_output) == 0 or movement_output is None or
                                           movement_output[0] == "null" or
                                           movement_output[0]["answer"] == "null" or
                                           movement_output[0]["answer"] == "" or
                                           movement_output[0]["answer"] == "{}" or
                                           movement_output[0]["answer"] is None):
                self.util.debug_print("Symphony.perform() null answer break, there is no answer")
                movement_output[0]["answer"] = "There is no answer"
                break

        self.end_time = timeit.default_timer()
        execution_time = self.end_time - self.start_time

        self.util.debug_print(f"The code executed in {execution_time: .2f} seconds")
        return movement_output
