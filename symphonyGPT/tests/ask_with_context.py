from gpt_4 import Gpt4
from performers.generator.pdf_generator import PDFGenerator
from performers.generator.secondthoughts.prompt_context_generator import PromptContextGenerator
from performers.generator.python_code_runner import PythonCodeRunner
from symphony.movement import Movement
from symphony.symphony import Symphony


def main() -> None:
    prompt = input("How can I help you: ")
    # prompt = "Tell me a short story about a dog"
    # prompt = "write a client web service code to query arxiv for information regarding superconductors"
    # prompt = "write code that can calculate pi to the 20th decimal place"
    # prompt = "write code that sorts a list of numbers"

    m_generate_context = Movement(
        performers=[PromptContextGenerator(number_of_questions=3)]
    )

    m_respond = Movement(
        prompt_str="{}",
        performers=[Gpt4()]
    )

    m_generate_pdf = Movement(
        performers=[PDFGenerator("contextual_response.pdf")]
    )

    m_run_python = Movement(
        performers=[PythonCodeRunner()]
    )

    symphony = Symphony(movements=[m_generate_context, m_respond],
                        null_answer_break=False)
    res = symphony.perform(prompt)

    # detect code in answer and offer to run it
    if "```python" in res[0]["answer"] or "```Python" in res[0]["answer"]:
        run = input("Code detected, would you like to run the code? (y/n): ")
        if run == "y":
            symphony = Symphony(movements=[m_run_python], null_answer_break=True)
            res = symphony.perform(res[0]["answer"])
        else:
            print("Code not run")

    pdf = input("Would you like a PDF of the response? (y/n): ")
    if pdf == "y":
        symphony = Symphony(movements=[m_generate_pdf],
                            null_answer_break=False)
        res = symphony.perform(res[0]["answer"])

    answer = res[0]["answer"]
    print(f"\n\n{answer}")


if __name__ == "__main__":
    main()
