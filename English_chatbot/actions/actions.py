import requests
from newsapi import NewsApiClient
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

import os
from dotenv import load_dotenv

load_dotenv()

weather_api_key = os.getenv('WEATHER_API_KEY')
news_api_key = os.getenv('NEWS_API_KEY')


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

        keyword = next(tracker.get_latest_entity_values("keyword"), None)
        newsapi = NewsApiClient(api_key=news_api_key)

        news = newsapi.get_everything(q=keyword,
                                              sources='bbc-news,the-verge',
                                              domains='bbc.co.uk,techcrunch.com',
                                              from_param='2024-07-13',
                                              language='en',
                                              sort_by='relevancy',
                                              page=2)

        if news:
            msg = f"You can read the article '{news['articles'][0]['title']}' here: \n{news['articles'][0]['url']}"
        else:
            msg = "I don't have any information about this. Try something different."

        dispatcher.utter_message(text=msg)

        return []

