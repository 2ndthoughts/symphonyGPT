from symphonyGPT.performers.language_model.openai_performers.gpt_35_turbo_0301 import Gpt35Turbo0301
from symphonyGPT.performers.language_model.openai_performers.gpt_4 import Gpt4
from symphonyGPT.performers.language_model.openai_performers.text_babbage_001 import TextBabbage001
from symphonyGPT.performers.language_model.openai_performers.text_curie_001 import TextCurie001
from symphonyGPT.performers.language_model.openai_performers.text_davinci_003 import TextDavinci003
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.outcome_strategy.huggingface.sentiment_hi_score import SentimentHiScore
from symphonyGPT.symphony.symphony import Symphony


# in this example, make sure to get an openai api key according to this page
# https://platform.openai.com/account/api-keys and update the api_key in the file
# symphonyGPT/performers/api_keys.py


def main() -> None:
    context = (
        "Tomoaki Komorida was born in Kumamoto Prefecture on July 10, 1981. After graduating from high school, he joined "
        "the J1 League club Avispa Fukuoka in 2000. Although he debuted as a midfielder in 2001, he did not play "
        "much and the club was relegated to the J2 League at the end of the 2001 season. In 2002, he moved to the "
        "J2 club Oita Trinita. He became a regular player as a defensive midfielder and the club won the "
        "championship in 2002 and was promoted in 2003. He played many matches until 2005. In September 2005, "
        "he moved to the J2 club Montedio Yamagata. In 2006, he moved to the J2 club Vissel Kobe. Although he "
        "became a regular player as a defensive midfielder, his gradually was played less during the summer. In "
        "2007, he moved to the Japan Football League club Rosso Kumamoto (later Roasso Kumamoto) based in his "
        "local region. He played as a regular player and the club was promoted to J2 in 2008. Although he did not "
        "play as much, he still played in many matches. In 2010, he moved to Indonesia and joined Persela "
        "Lamongan. In July 2010, he returned to Japan and joined the J2 club Giravanz Kitakyushu. He played often "
        "as a defensive midfielder and center back until 2012 when he retired.")

    question = "When was Tomoaki Komorida born?"

    question2 = f"When was Tomoaki Komorida born Based on the following context: '{context}'"  # question with contex

    m_without_context = Movement(
        performers=[
            TextCurie001(),
            TextBabbage001(),
            TextDavinci003(),
            Gpt4(),
            Gpt35Turbo0301()
        ],
        outcome_strategy=SentimentHiScore(format="answer_only")
    )

    m_with_context = Movement(
        performers=[
            TextCurie001(),
            TextBabbage001(),
            TextDavinci003(),
            Gpt4(),
            Gpt35Turbo0301()
        ],
        outcome_strategy=SentimentHiScore(format="answer_only")
    )

    # Movements are not re-usable, Symphonies are
    symphony = Symphony(movements=[m_without_context])
    res1 = symphony.perform(question)

    symphony = Symphony(movements=[m_with_context])
    res2 = symphony.perform(question2)

    print(f"Question: {question}")
    print(f"\nAnswer without context: {res1}\n")

    print(f"Question: {question2}")
    print(f"\n\nAnswer with context: {res2}")


if __name__ == "__main__":
    main()
