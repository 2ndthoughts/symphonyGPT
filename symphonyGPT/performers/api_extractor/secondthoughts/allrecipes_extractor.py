import json

from allrecipes import AllRecipes
from bs4 import BeautifulSoup
import requests

from symphonyGPT.performers.api_extractor.api_extractor import APIExtractor
from symphonyGPT.performers.api_extractor.secondthoughts.arxiv_extractor import ArxivExtractor
from symphonyGPT.symphony.classifier.huggingface.foodbase_distillbert_token_classifier import FoodBaseDistilBert
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.symphony import Symphony


class AllRecipesExtractor(APIExtractor):
    def __init__(self, max_results=5, max_embeddings_results=5):
        super().__init__(max_results, max_embeddings_results)

    def get_recipe(self, query):

        query_result = AllRecipes.search(query)
        if len(query_result) == 0:
            return json.loads("{}")

        answers = json.loads("{}")
        answers['search'] = query
        answers['recipes'] = []
        for k in range(len(query_result)):
            if k >= self.max_results:
                break

            main_recipe_url = query_result[k]['url']
            detailed_recipe = AllRecipes.get(
                main_recipe_url)  # Get the details of the first returned recipe (most relevant in our case)

            answer = json.loads("{}")
            answer['name'] = query_result[k]['name']  # Name of the recipe
            k += 1

            answer['url'] = main_recipe_url

            answer['nb_servings'] = detailed_recipe['nb_servings']
            i = 0
            ingredients = {}
            for ingredient in detailed_recipe['ingredients']:  # List of ingredients
                ingredients[i] = ingredient
                i += 1

            answer['ingredients'] = ingredients

            i = 0
            steps = {}
            for step in detailed_recipe['steps']:  # List of cooking steps
                steps[i] = step
                i += 1

            answer['steps'] = steps
            answers['recipes'].append(answer)

        return answers

    def perform(self, prompt):
        classifications = prompt.get_classifications()

        query_array = self.create_query_array_from_classifier(classifications)
        answers = []
        for query in query_array:
            answer = self.get_recipe(query)
            if answer:
                answers.append(answer)

        self.set_raw_response(answers)


# test main
if __name__ == "__main__":
    # prompt = "Tartufo Pasta with garlic flavoured butter and olive oil, egg yolk, parmigiano and pasta water."
    #prompt = "Today's meal: Fresh olive poké bowl topped with chia seeds. Very delicious!"
    #prompt = "chicken"
    prompt = "chia seeds"
    m_test = Movement(
        prompt_classifier=[FoodBaseDistilBert()],
        performers=[AllRecipesExtractor(max_results=5)]
    )

    symphony = Symphony(movements=[m_test], null_answer_break=True)
    res = symphony.perform(prompt)
    pretty_json = json.dumps(res, indent=4)
    print(pretty_json)
