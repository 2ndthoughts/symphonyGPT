from setuptools import setup

setup(
    name='symphonyGPT',
    version='0.1',
    packages=['symphonyGPT', 'symphonyGPT.tests', 'symphonyGPT.symphony', 'symphonyGPT.symphony.classifier',
              'symphonyGPT.symphony.classifier.huggingface', 'symphonyGPT.symphony.outcome_strategy',
              'symphonyGPT.symphony.outcome_strategy.huggingface', 'symphonyGPT.performers',
              'symphonyGPT.performers.generator', 'symphonyGPT.performers.generator.secondthoughts',
              'symphonyGPT.performers.api_extractor', 'symphonyGPT.performers.api_extractor.secondthoughts',
              'symphonyGPT.performers.language_model', 'symphonyGPT.performers.language_model.openai_performers',
              'symphonyGPT.performers.language_model.huggingface_performers'],
    url='https://github.com/2ndthoughts/symphonyGPT',
    license='MIT License',
    author='davidloo',
    author_email='david@secondthoughts.ai',
    description='Framework for AI workflows'
)
