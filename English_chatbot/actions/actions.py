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
            msg = f"Temperature in {city}: {weather_data['main']['temp']}°C"
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
            currency = data[0]['currencies']
            currency_key = list(currency.keys())[0]
            cur_name = data[0]['currencies'][currency_key]['name']
            cur_symbol = data[0]['currencies'][currency_key]['symbol']
            capital = data[0]['capital'][0]
            subregion = data[0]["subregion"]
            languages = ', '.join(data[0]["languages"].values())
            borders = ', '.join(data[0]["borders"])
            population = data[0]['population']
            timezones = ', '.join(data[0]['timezones'])
            flag = data[0]['flags']['png']
            map_url = data[0]['maps']['googleMaps']
            print(currency)

            msg = f"""
                                            <b>COUNTRY:</b> {country}<br>
                                            <b>CAPITAL:</b> {capital}<br>
                                            <b>CURRENCY:</b> {cur_name} [{cur_symbol}, {currency_key}]<br>
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

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[
        Dict[Text, Any]]:

        if tracker.get_slot('trivia_data'):
            # Trivia data already set, no need to fetch again
            return []

        response = requests.get('https://opentdb.com/api.php?amount=5&difficulty=easy&type=multiple')
        if response:
            data = response.json()
            trivia_data = data.get('results', [])
            questions = []
            all_answers = []

            for i in range(5):
                question = trivia_data[i]['question']
                questions.append(question)
                correct_answer = trivia_data[i]['correct_answer']
                answers = trivia_data[i]['incorrect_answers']
                answers.append(correct_answer)
                all_answers.append(answers)

            trivia_data = [[questions[i], all_answers[i]] for i in range(5)]

            return [SlotSet("trivia_data", trivia_data)]

        else:
            dispatcher.utter_message(text="Failed to retrieve trivia questions.")
            return []


class ActionAskQuestion(Action):
    def name(self) -> Text:
        return "action_ask_question"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        trivia_data = tracker.get_slot('trivia_data')

        if trivia_data:
            print(trivia_data)
            [question, options] = trivia_data.pop(0)
            correct_answer = options[-1]
            random.shuffle(options)
            index = options.index(correct_answer)
            letter_options = ['A', 'B', 'C', 'D']
            correct_letter = letter_options[index]

            msg = f"""
            Question: {question}
            A: {options[0]}
            B: {options[1]}
            C: {options[2]}
            D: {options[3]}
            """

            dispatcher.utter_message(text=msg)

            return [
                SlotSet("trivia_data", trivia_data),  # Update the trivia data
                SlotSet("correct_letter", correct_letter)
            ]
        else:
            score = tracker.get_slot('score')
            dispatcher.utter_message(text=f"That's the end of the game! Your final score is {score}")
            dispatcher.utter_message(template="utter_what_to_do")
            return [SlotSet("trivia_data", None), SlotSet("score", 0)]


class ActionCheckAnswer(Action):
    def name(self) -> Text:
        return "action_check_answer"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_answer = tracker.get_slot('answer')
        correct_letter = tracker.get_slot("correct_letter")

        score = tracker.get_slot('score') or 0  # Ensure score is initialized to 0 if None

        if user_answer is None or correct_letter is None:
            dispatcher.utter_message(template="utter_missing_information")
            return []

        if user_answer.lower() == correct_letter.lower():
            score = score + 1
            dispatcher.utter_message(text=f"Good! {correct_letter} is correct!")
            return [SlotSet("score", score)]
        else:
            dispatcher.utter_message(text=f"No, {correct_letter} is correct")

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


class ActionGreetUser(Action):

    def name(self) -> str:
        return "action_greet_user"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain: dict) -> list:

        dispatcher.utter_message(text="Hi! I'm Enbot. I'd love to help you improving your English. What's your name?")
        return []


class ActionSaveName(Action):

    def name(self) -> str:
        return "action_save_name"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain: dict) -> list:

        name = tracker.get_slot("user_name")
        dispatcher.utter_message(response="utter_nice_to_meet", name=name)
        dispatcher.utter_message(response="utter_what_to_do")
        return []


