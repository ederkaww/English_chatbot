import requests
import random
from newsapi import NewsApiClient
from typing import Any, Text, Dict, List
from rasa_sdk.events import SlotSet
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import language_tool_python

import os
from dotenv import load_dotenv

load_dotenv()

weather_api_key = os.getenv('WEATHER_API_KEY')
news_api_key = os.getenv('NEWS_API_KEY')
words_api_key = os.getenv('WORDS_API_KEY')


def ask_question(data):
    current_data = data.pop()
    question = current_data['question']
    correct_answer = current_data['correct_answer']
    options = current_data['incorrect_answers']
    options.append(correct_answer)
    random.shuffle(options)
    index = options.index(correct_answer)
    letter_options = ['A', 'B', 'C', 'D']
    correct_letter = letter_options[index]

    current_data = [question, options, correct_letter]

    return current_data


class ActionTellWeather(Action):

    def name(self) -> Text:
        return "action_tell_weather"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        city = next(tracker.get_latest_entity_values("place"), None)

        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': weather_api_key,
            'units': 'metric'
        }
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            weather_data = response.json()
            msg = f"Temperature now in {city}: {weather_data['main']['temp']}°C"
        else:
            msg = "I don't have any information about the weather there. Please give me some other city."

        dispatcher.utter_message(text=msg)

        return []


class ActionTellNews(Action):

    def name(self) -> Text:
        return "action_tell_news"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        newsapi = NewsApiClient(api_key=news_api_key)
        category = tracker.get_slot('category')

        if not category:
            news = newsapi.get_top_headlines(country='us',
                                             language='en',
                                          )
        else:
            news = newsapi.get_top_headlines(country='us',
                                             language='en',
                                             category=category
                                             )

        if news:
            i = random.randint(1, 10)
            msg = f""" <a href = "{news['articles'][i]['url']}"> {news['articles'][i]['title']} </a > """
        else:
            msg = "I don't have any information about this. Try something different."

        dispatcher.utter_message(text=msg)

        return []


class ActionTellCountryInfo(Action):

    def name(self) -> Text:
        return "action_tell_country_info"

    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        country = next(tracker.get_latest_entity_values("country"), None)
        response = requests.get(f"https://restcountries.com/v3.1/name/{country}")

        if response:
            data = response.json()
            currency = data[0]['currencies']['PLN']['name']
            cur_symbol = data[0]['currencies']['PLN']['symbol']
            capital = data[0]['capital'][0]
            subregion = data[0]["subregion"]
            languages = ', '.join(data[0]["languages"].values())
            borders = ', '.join(data[0]["borders"])
            population = data[0]['population']
            timezones = ', '.join(data[0]['timezones'])
            flag = data[0]['flags']['png']
            map_url = data[0]['maps']['googleMaps']

            msg = f"""
                                            <b>BASIC INFO ABOUT:</b> {country}<br>
                                            <b>CAPITAL:</b> {capital}<br>
                                            <b>CURRENCY:</b> {currency} [{cur_symbol}]<br>
                                            <b>REGION:</b> {subregion}<br>
                                            <b>BORDERS:</b> {borders}<br>
                                            <b>LANGUAGES:</b> {languages}<br>
                                            <b>POPULATION:</b> {population}<br>
                                            <b>TIMEZONES:</b> {timezones}<br>
                                            <b>FLAG:</b> <a href="{flag}">Link to flag</a><br>
                                            <b>MAP:</b> <a href="{map_url}">Link to map</a>
                                            """

            dispatcher.utter_message(text=msg)

        else:
            msg = "I don't have any information about this. Try something different."
            dispatcher.utter_message(text=msg)

        return []


class ActionStartTrivia(Action):
    def name(self) -> Text:
        return "action_start_trivia"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        response = requests.get('https://opentdb.com/api.php?amount=10&difficulty=medium&type=multiple')
        data = response.json()

        trivia_data = data['results']

        return [SlotSet("trivia_data", trivia_data)]


class ActionAskQuestion(Action):
    def name(self) -> Text:
        return "action_ask_question"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[
        Dict[Text, Any]]:

        trivia_data = tracker.get_slot('trivia_data')

        if trivia_data:
            question, options, correct_letter = ask_question(trivia_data)

            msg = f"""
            Question: {question}
            A: {options[0]}
            B: {options[1]}
            C: {options[2]}
            D: {options[3]}
            """

            dispatcher.utter_message(text=msg)

            return [SlotSet("question", question), SlotSet("correct_answer", correct_letter)]
        else:
            dispatcher.utter_message(text="That's the end of the game!")


class ActionCheckAnswer(Action):
    def name(self) -> Text:
        return "action_check_answer"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_answer = tracker.get_slot('answer')
        correct_answer = tracker.get_slot("correct_answer")

        score = tracker.get_slot('score') or 0  # Ensure score is initialized to 0 if None

        if user_answer is None or correct_answer is None:
            dispatcher.utter_message(template="utter_missing_information")
            return []

        if user_answer.lower() == correct_answer.lower():
            score = score + 1
            dispatcher.utter_message(template="utter_correct_answer", score=score)
            return [SlotSet("score", score)]
        else:
            dispatcher.utter_message(template="utter_wrong_answer", correct_answer=correct_answer, score=score)

        return []


class ActionRetrieveLastUserMessage(Action):

    def name(self) -> Text:
        return "action_retrieve_last_user_message"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        tool = language_tool_python.LanguageTool('en-US')
        last_user_message = tracker.latest_message.get('text')
        matches = tool.check(last_user_message)

        for match in matches:
            dispatcher.utter_message(text=match.message)

        return []


###
class ActionExplainWord(Action):

    def name(self) -> Text:
        return "action_explain_word"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        word_to_explain = next(tracker.get_latest_entity_values("word_to_explain"), None)

        url = f"https://wordsapiv1.p.rapidapi.com/words/{word_to_explain}"
        headers = {
            'x-rapidapi-key': words_api_key,
            'x-rapidapi-host': 'wordsapiv1.p.rapidapi.com'
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            word = response.json()['word']
            definition = response.json()['results'][0]['definition']
            part_of_speech = response.json()['results'][0]['partOfSpeech']
            synonyms = response.json()['results'][0]['synonyms']
            synonyms_str = ', '.join(synonyms)

            text = f"""
                    The definition of a word '{word}': {definition} 
                    Part of speech: {part_of_speech}
                    Synonyms: {synonyms_str}
                    """
        else:
            text = "I don't have any information about this word. Please give me some other one."

        dispatcher.utter_message(text=text)

        return []
