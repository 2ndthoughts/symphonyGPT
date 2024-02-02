from symphonyGPT.performers.api_extractor.secondthoughts.mysql_schema_extractor import MySQLSchemaExtractor
from symphonyGPT.performers.generator.mysql_query_runner import MySQLQueryRunner
from symphonyGPT.performers.language_model.openai_performers.gpt_4 import Gpt4
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony


def main() -> None:
    # prompt = "how did the roman empire fall"

    # The symphony is composed of two movements
    #  * list all the studies from arxiv based on a search of the prompt
    #
    #  * The second movement is to generate a conclusion based on the extracted statements
    #  * and the list of studies from eutils.ncbi.nlm.nih.gov (National Library of Medicine)

    #prompt = "how many customers are from California"
    #prompt = "what is the address of the office in NYC"
    #prompt = "Which customer has the most orders and what is the total revenue from those orders?"
    prompt = ("What is the most popular product by name, price, and MSRP being ordered and how many products were ordered and are there for it? "
              "What is the total revenue from those orders? How many customers paid MSRP for the product and who were they?")
    #prompt = ("In what city do we have the least number of orders, how many orders are there and what is the total revenue "
    #          "from those orders")
    #prompt = ("Do we get more revenue from customers in NYC compared to customers in San Francisco? Give me the "
    #          "total revenue for each city, and the difference between the two.")

    m_extract_schema = Movement(
        performers=[MySQLSchemaExtractor(table_name="all")]
    )

    m_generate_sql = Movement(
        prompt_str="Generate a SQL statement based on the question '"
                   + prompt + "' using the following MySQL schema: \n{} ",
        performers=[Gpt4()]
    )

    m_run_sql = Movement(
        prompt_str = "{}",
        performers=[MySQLQueryRunner()]
    )

    m_compose_answer = Movement(
        prompt_str="Generate a response based on the following SQL results: {} to the prompt '" + prompt + "'",
        performers=[Gpt4()]
    )

    print(prompt)
    symphony = Symphony(movements=[m_extract_schema,m_generate_sql,m_run_sql, m_compose_answer],
                        null_answer_break=True)
    res = symphony.perform(prompt)

    answer = res[0]["answer"]
    print(f"\n\n{answer}")


if __name__ == "__main__":
    main()