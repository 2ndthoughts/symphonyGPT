from symphonyGPT.performers.generator.generator import Generator
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony


class PythonCodeRunner(Generator):
    def __init__(self):
        super().__init__()
        self.set_type("python_code_runner")

    def perform(self, prompt):
        self.util.debug_print("PythonCodeRunner.perform() called")

        text = self.util.extract_answer(prompt.get_prompt())
        code = self.util.extract_between(text, "```python", "```")

        result = self.util.capture_exec_output(code)
        self.set_raw_response(result)


# test main
if __name__ == "__main__":
    with open(
            "../../../../../Library/Application "
            "Support/JetBrains/PyCharmCE2023.2/scratches/sandbox/test_python_code_runner.txt", 'r') as file:
        content = file.read()

    prompt = content

    m_test = Movement(
        performers=[PythonCodeRunner()]
    )

    if "```python" in prompt:
        run = input("Code detected, would you like to run the code? (y/n): ")
        if run == "y":
            symphony = Symphony(movements=[m_test], null_answer_break=True)
            res = symphony.perform(prompt)
            answer = res[0]["answer"]
            print(f"\n\n{answer}")
        else:
            print("Code not run")
