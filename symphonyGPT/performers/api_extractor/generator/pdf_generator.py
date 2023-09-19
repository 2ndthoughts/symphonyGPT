from gpt_4 import Gpt4
from performers.api_extractor.generator.generator import Generator
from symphony.movement import Movement
from symphony.symphony import Symphony
from fpdf import FPDF


class PDFGenerator(Generator):
    def __init__(self, output_file_name=None, output_font=None, output_font_size=None):
        super().__init__()
        self.set_type("pdf_generator")

        if output_font is None:
            output_font = "Arial"
        self.font = output_font

        if output_font_size is None:
            output_font_size = 12
        self.font_size = output_font_size

        if output_file_name is None:
            output_file_name = "output.pdf"
        self.output_file_name = output_file_name

    def perform(self, prompt):
        self.util.debug_print("PDFGenerator.perform() called")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font(self.font, size=self.font_size)

        answer_text = self.util.extract_answer(prompt.get_prompt())

        text = answer_text.encode('utf-8').decode('latin-1')
        pdf.multi_cell(0, 10, text)

        pdf.output(self.output_file_name)
        self.set_raw_response(f"{self.output_file_name}")


# test main
if __name__ == "__main__":
    prompt = "Tell me a short story about a dog"

    m_generate_story = Movement(
        performers=[Gpt4()]
    )

    m_create_pdf = Movement(
        prompt_str = "{}",
        performers=[PDFGenerator("story.pdf")]
    )

    symphony = Symphony(movements=[m_generate_story, m_create_pdf], null_answer_break=True)
    res = symphony.perform(prompt)
