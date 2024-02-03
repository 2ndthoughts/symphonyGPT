from symphonyGPT.performers.api_extractor.secondthoughts.mysql_schema_extractor import MySQLSchemaExtractor
from symphonyGPT.performers.generator.mysql_query_runner import MySQLQueryRunner
from symphonyGPT.performers.generator.secondthoughts.prompt_context_generator import PromptContextGenerator
from symphonyGPT.performers.language_model.openai_performers.gpt_4 import Gpt4
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony


def main(prompt) -> None:
    # prompt = "how did the roman empire fall"

    # The symphony is composed of two movements
    #  * list all the studies from arxiv based on a search of the prompt
    #
    #  * The second movement is to generate a conclusion based on the extracted statements
    #  * and the list of studies from eutils.ncbi.nlm.nih.gov (National Library of Medicine)

    #prompt = "how many customers are from California"
    #prompt = "what is the address of the office in NYC"
    #prompt = "Which customer has the most orders and what is the total revenue from those orders?"
    #prompt = ("What is the most popular product by name, price, and MSRP being ordered and how many products were ordered and are there for it? "
    #          "What is the total revenue from those orders? How many customers paid MSRP for the product and who were they?")
    #prompt = ("In what city do we have the least number of orders, how many orders are there and what is the total revenue "
    #          "from those orders")
    #prompt = ("Do we get more revenue from customers in NYC compared to customers in San Francisco? Give me the "
    #          "total revenue for each city, and the difference between the two.")

    #prompt = input("What would you like to know: ")

    # request the schema, use connection string defined in APIKeys
    m_extract_schema = Movement(
        performers=[MySQLSchemaExtractor(table_name="all")]
    )

    # generate a SQL statement based on the question (prompt) using the following MySQL schema
    m_generate_sql = Movement(
        prompt_str="Generate only one SQL statement based on the question '"
                   + prompt + "' using the following MySQL schema: \n{} ",
        performers=[Gpt4()]
    )

    # detect the SQL statement and run it
    m_run_sql = Movement(
        prompt_str = "{}",
        performers=[MySQLQueryRunner()]
    )

    # generate a human readable response based on the SQL results
    m_compose_answer = Movement(
        # prompt_str="Generate a response for the following results: {} to the prompt '" + prompt + "'",
        prompt_str = f"Summarize the answer to the question '{prompt}'" +" based on this result: {}",
        performers=[Gpt4()]
    )

    print(prompt)
    symphony = Symphony(movements=[m_extract_schema,m_generate_sql,m_run_sql, m_compose_answer],
                        null_answer_break=True)

    res = symphony.perform(prompt)
    answer = res[0]["answer"]
    print(f"\n\n{answer}\n\n")


if __name__ == "__main__":
    prompt_history = []
    for i in range(999):
        mprompt = input("What would you like to know: ")
        if mprompt == "":
            break

        if mprompt == "clear":
            prompt_history = []
            print("Prompt history cleared\n")
            continue

        if mprompt == "show":
            print("".join(prompt_history) + "\n")
            continue

        if not mprompt.endswith("?"):
            mprompt = mprompt + "? "

        prompt_history.append(mprompt)
        main(" ".join(prompt_history))