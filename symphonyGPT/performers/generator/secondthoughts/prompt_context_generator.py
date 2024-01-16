from symphonyGPT.performers.language_model.openai_performers.gpt_4 import Gpt4
from symphonyGPT.performers.generator.generator import Generator
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.prompt import Prompt
from symphonyGPT.symphony.symphony import Symphony


# :copyright: Copyright 2023 by 2ndthoughts.ai david@2ndthoughts.ai.
# :license: Licensed under the Non-Profit Open Software License version 3.0 see LICENSE for details.
class PromptContextGenerator(Generator):
    def __init__(self, number_of_questions=None):
        super().__init__()
        self.set_type("prompt_context_generator")
        if number_of_questions is None:
            number_of_questions = 3
        self.number_of_questions = number_of_questions

    def perform(self, prompt):
        self.util.debug_print("PromptContextGenerator.perform() called")

        prompt_str = prompt.get_prompt()

        # use Gpt4 to generate questions to ask human to get more context
        # for the prompt
        context_questions_prompt = (
            f"ask {self.number_of_questions} questions to clarify the user's intent regarding '{prompt_str}', respond "
            f"exactly with the questions only")
        q_prompt = Prompt()
        q_prompt.set_prompt(context_questions_prompt)
        gpt4 = Gpt4()
        gpt4.perform(q_prompt)

        questions = gpt4.get_raw_response()

        questions_array = questions.split("\n")

        q_count = 0
        for question in questions_array:
            question = question.strip()
            if len(question) > 0:
                user_input = input(f"{question}: ")
                context = f"{question}: {user_input}"
                # self.util.debug_print(f"question: {context}")
                questions_array[q_count] = context
                q_count = q_count + 1

        new_prompt_str = f"{prompt_str} using the following context\n" + "\n".join(questions_array)
        self.set_raw_response(new_prompt_str)


# test main
if __name__ == "__main__":
    prompt = "Tell me a short story about a dog"

    m_test = Movement(
        performers=[PromptContextGenerator()]
    )

    symphony = Symphony(movements=[m_test], null_answer_break=True)
    res = symphony.perform(prompt)
    answer = res[0]["answer"]
    print(f"\n\n{answer}")
