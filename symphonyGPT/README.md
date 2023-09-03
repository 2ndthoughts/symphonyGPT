# SymphonyGPT
##### Copyright (c) 2023 <a href=https://2ndthoughts.ai/>2ndthoughts.ai</a>
Contact: <a href=mailto:dev@2ndthoughts.ai>dev@2ndthoughts.ai</a>

<p>A platform developed from an open framework to help AI researchers and developers to rapidly prototype, test and
deploy workflows that include machine learning models as a component. The workflow can be invoked on command line or web service,
as well as integrated into UX/UI as part of a larger intelligent solution.</p>

<p>The architecture is inspired by the structures of a classical music symphony, its movements, and performers. Hence the
source code is comprised of class hierarchies that reflect these concepts. Ultimately, the hierarchy of Python classes can 
be overriden by a developer to create their own custom workflow. The framework is designed to be extensible and flexible.</p>

<p>Unless otherwise specified in the source file, all source code in this project is licensed under the open-source 
MIT License (see SymphonyGPT/LICENSE file)</p>

<p>The API Extractor sub-classes in the <b>secondthoughts</b> folder are licensed under the Non-Profit Open Software License 
version 3.0 see performers/api_extractor/secondthoughts/LICENSE for details.</p>

### Architecture
<p><i>After all, a Symphony is a complex workflow of musical notes flowing in harmony</i></p>
<p>As a high level overview, a <b>Symphony</b> is comprised of <b>Movements</b> which in turn contains any numbers of 
<b>Performers</b>, <b>Classifiers</b>, and <b>OutcomeStrategies</b>. A <b>Prompt</b> is an input to the <b>Symphony</b>
or <b>Movement</b> that drives the workflow. The <b>Performers</b> are the main components that
does the work in the workflow and can be an LLM (remote API or local) or any executable code that builds the content along 
the path of the <b>Symphony</b> (workflow).  <b>Classifiers</b> extract attributes from the <b>Prompt</b> to be used by
<b>Performers</b> as kind of a hint or suggestion on how to customize the work. There currently is a special <b>Performer</b>
called an <b>APIExtractor</b> that can be part of a <b>Movement</b> to gather input or more context for subsequent
<b>Movement</b>s</p>

![SymphonyGPT.png](images%2FSymphonyGPT.png)

### Project files
<p>The project is organized into the following directories:</p>

- <b>symphonyGPT</b> - the root directory
  - <b>symphony</b>
    - <b>classifier</b> - the classifiers that extract attributes from the <b>Prompt</b>
      - <b>huggingface</b> - the <b>HuggingFaceClassifier</b> class and its subclasses 
    - <b>outcome_strategy</b> - the <b>OutcomeStrategy</b> class and its subclasses
      - <b>huggingface</b> - the <b>HuggingFaceOutcomeStrategy</b> class and its subclasses
  - <b>performers</b> - the <b>Performer</b> class and its subclasses
    - <b>language_model</b> - the <b>LanguageModel</b> class and its subclasses
      - <b>openai</b> - the <b>Gpt4</b> class and its subclasses
      - <b>huggingface</b> - the <b>HuggingFace</b> class and its subclasses
    - <b>api_extractor</b> - the <b>APIExtractor</b> class and its subclasses
  - <b>tests</b> - the example tests, these all have main() and are directly executable examples

### Running the test examples
<p>The best way to learn about the framework, its components and class hierarchy is to run the examples in the 
../tests folder. You will need the following instructions on how to get api keys for the models and web services
we will be calling.</p>

#### OpenAI API key
<p>After getting an OpenAI account from https://platform.openai.com, login and navigate this page 
https://platform.openai.com/account/api-keys, copy the API key and update the api_key in the file 
symphonyGPT/performers/language_model/openai_performers/openai_performer.py</p>

#### CourtListener API key
<p>After getting an account from https://www.courtlistener.com/sign-in/, login and navigate to this page
https://www.courtlistener.com/help/api/rest/#permissions to copy your authorization token and update the api_key in
the file symphonyGPT/performers/api_extractor/secondthoughts/court_listener_extractor.py</p>

<p>Here is a list of the examples from the ../tests folder, a short description of what they do and the requirements to 
run them:</p>

1. <b>answers_with_positive_sentiments.py</b>
    - <b>Requirements:</b> OpenAI API key
    - <b>Test:</b> Asks multiple GPT models to answer a question and then uses a HuggingFace model to classify the answer, next select the answers with positive sentiment
2. <b>ask_arxiv.py</b>
    - <b>Requirements:</b> OpenAI API key
    - <b>Test:</b> Asks the ArXiv API to find articles for a given technical finding and then asks GPT to summarize the answers
2. <b>ask_clinical_trials_gov.py</b>
    - <b>Requirements:</b> OpenAI API key
    - <b>Test:</b> Asks the ClinicalTrials.gov API to find clinical trials for a given disease and then asks GPT to summarize the answers
3. <b>ask_courtlistener.py</b>
    - <b>Requirements:</b> CourtListener API key, OpenAI API key
    - <b>Test:</b> Asks the CourtListener API to find court cases relating to a given allegation and then asks GPT to summarize the answers
4. <b>ask_nlm</b>
    - <b>Requirements:</b> OpenAI API key
    - <b>Test:</b> Asks the National Library of Medicine API to find articles for a given disease and then asks GPT to summarize the answers
5. <b>ask_nlm_ctg_courtlistener.py</b>
    - <b>Requirements:</b> CourtListener API key, OpenAI API key
    - <b>Test:</b> Asks the National Library of Medicine, ClinicalTrials.gov and CourtListener APIs to find articles, clinical trials and court cases for a given situation and then asks GPT to summarize the answers
6. <b>generate_text_and_merge.py</b>
    - <b>Requirements:</b> OpenAI API key
    - <b>Test:</b> Asks GPT to generate text and then merge the results into a single answer
7. <b>multi_movement_translation.py</b>
    - <b>Requirements:</b> OpenAI API key
    - <b>Test:</b> Asks GPT to translate a sentence into multiple languages and back
8. <b>question_answer_with_context.py</b>
    - <b>Requirements:</b> OpenAI API key
    - <b>Test:</b> Asks GPT to answer a question with context
9. <b>shortest_math_answer_translated.py</b>
    - <b>Requirements:</b> OpenAI API key
    - <b>Test:</b> Asks GPT to answer a math question, select the shortest answer and then translate the answer

### Configuring a Symphony
<p>The workflow (Symphony) is defined by the <b>Movements</b> of a <b>Symphony</b> and the arrangement of <b>Performers</b> in them.
A <b>Symphony</b> can have any number of <b>Movements</b> and each <b>Movement</b> can have any number of <b>Performers</b>
defined in it.</p>

<p>The output of a <b>Movement</b> is passed along as text into an empty variable '{}' accessible from the next 
<b>Movements</b> <b>Prompt</b> in the "prompt_str" attribute of the <b>Movement</b></p>

<p>A <b>Symphony</b> object is re-usable but but the <b>Movements</b> that are defined cannot be re-used.</p>

<p>Here is an example of a multi-<b>Movement</b> <b>Symphony</b> showing how to translate a sentence into multiple 
languages and back. You can explore other executable tests in the ../test folder</p>

```python
from symphonyGPT.performers.language_model.openai_performers.gpt_4 import Gpt4
from symphonyGPT.symphony.movement import Movement
from symphonyGPT.symphony.outcome_strategy.outcome_strategy import OutcomeStrategy
from symphonyGPT.symphony.symphony import Symphony

prompt = "Translate to Chinese 'How are you'"  # why or question


def main() -> None:
    movement_chinese = Movement(
        performers=[Gpt4()],
        outcome_strategy=OutcomeStrategy(format="answer_only")
    )
    movement_german = Movement(
        prompt_str="translate to German: {}", # pass the result of the previous movement to the next movement using {}
        performers=[Gpt4()],
        outcome_strategy=OutcomeStrategy(format="answer_only")
    )

    movement_french = Movement(
        prompt_str="translate to French: {}",
        performers=[Gpt4()],
        outcome_strategy=OutcomeStrategy(format="answer_only")
    )

    movement_english = Movement(
        prompt_str="translate to English: {}",
        performers=[Gpt4()]
        # the last one is not an array
    )

    symphony = Symphony(movements=[movement_chinese, movement_german, movement_french, movement_english])
    res = symphony.perform(prompt)
    answer = res[0]["answer"]
    print(f"\n\n{answer}")


if __name__ == "__main__":
    main()
```