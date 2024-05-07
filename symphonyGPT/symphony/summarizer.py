import chromadb
from chromadb.utils import embedding_functions
from symphonyGPT.performers.language_model.openai_performers.gpt_4 import Gpt4
from symphonyGPT.symphony.prompt import Prompt
import os
from symphonyGPT.symphony.util import Util

os.environ["TOKENIZERS_PARALLELISM"] = "true"  # to avoid dead lock warning

maximum_embedded_summarized_text = 100000
maximum_embedded_docs = 100
chunk_size = 25000

def summarize_result_in_chunks(summarize_this_str, summarizing_prompt, prompt_str=None):
    util = Util()
    db_client = chromadb.Client()
    summarizer_name = f"summarizer_{util.random_string(5)}"
    collection = db_client.get_or_create_collection(name=f"{summarizer_name}")
    default_embedding_function = embedding_functions.DefaultEmbeddingFunction()


    # summarize {chunk_size} characters at a time and concatenate the results
    summerized_text = ""
    for i in range(0, len(summarize_this_str), chunk_size):
        util.debug_print(
            f"summarize_result_in_chunks() summarizing and embedding chunk: {i + chunk_size} of {len(summarize_this_str)}")
        summerized_text += summarize_result(summarize_this_str[i:i + chunk_size],
                                            summarizing_prompt, prompt_str) + " "
        util.debug_print(f"summarize_result_in_chunks() summerized_text len: {len(summerized_text)}")
        # add the chunk to the embedding collection
        collection.add(
            documents=[summerized_text],
            ids=[f"{summarize_this_str[:10]}{i + chunk_size}"]
        )

    ef_val = default_embedding_function([summarizing_prompt])
    embedded_answers = collection.query(
        query_embeddings=ef_val,
        n_results=maximum_embedded_docs,
        include=["documents"]
    )

    embedded_summarized_text = ""
    number_of_documents = 0
    for documents in embedded_answers["documents"]:
        if len(embedded_summarized_text) <= maximum_embedded_summarized_text:
            for document in documents:
                embedded_summarized_text += document
                number_of_documents += 1
                if len(embedded_summarized_text) > maximum_embedded_summarized_text:
                    break

    db_client.delete_collection(name=f"{summarizer_name}")
    util.debug_print(
        f"summarize_result_in_chunks() embedded_summarized_text num/len: {number_of_documents}/{len(embedded_summarized_text)}")
    return embedded_summarized_text


def summarize_result(summarize_this_str, summarizing_prompt, prompt_str=None):
    # summarize 8000 characters at a time and concatenate the results
    # to avoid the 8000 character limit of the GPT-4 API
    if len(summarize_this_str) > maximum_embedded_summarized_text:
        summarize_this_str = summarize_this_str[:maximum_embedded_summarized_text]

    model = Gpt4()
    if prompt_str is None:
        prompt_str = (f"According to the question '{summarizing_prompt}', summarize the following "
                      f"'{summarize_this_str}'")

    sum_prompt = Prompt()
    sum_prompt.set_prompt(prompt_str)
    model.perform(sum_prompt)
    summarize_this_str = model.get_raw_response()
    # remove the prompt_str from the summarized DetailedDescription
    summarize_this_str = summarize_this_str.replace(prompt_str, "")
    return summarize_this_str
