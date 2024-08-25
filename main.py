import requests
from twilio.rest import Client
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from dotenv import load_dotenv
from datetime import datetime
import csv

load_dotenv()

STOCK_NAME = "TSLA" # Write the Name of the stock you want to search
COMPANY_NAME = "Tesla Inc" # Write the Name of the Company

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

News_api = os.getenv('NEWS_API_KEY')
Stock_api = os.getenv('STOCK_API_KEY')
twilio_SID = os.getenv('TWILIO_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')


Stock_params = {
    "function": "Time_Series_Daily",
    "symbol": STOCK_NAME,
    "apikey": Stock_api,
}

NEWS_params = {
    "apikey": News_api,
    "qInTitle": COMPANY_NAME,
}

response = requests.get(STOCK_ENDPOINT, params=Stock_params)
data = response.json()["Time Series (Daily)"]

data_list = [value for (key, value) in data.items()]

yesterdaydata = data_list[0]

yesterdaydataprice = yesterdaydata["4. close"]

day_before_yesterday = data_list[1]
day_before_yesterday_price = day_before_yesterday["4. close"]

positive_difference = float(yesterdaydataprice) - float(day_before_yesterday_price)
up_down = None
if positive_difference > 0:
    up_down = "⬆️"
else:
    up_down = "⬇️"

diff_percent = round((positive_difference/float(yesterdaydataprice)) * 100)

if abs(diff_percent) > 1:
    news = requests.get(NEWS_ENDPOINT, params=NEWS_params)
    articles = news.json()["articles"]

    three_articles = articles[:3]
    print(three_articles)

    new_news = [f"{STOCK_NAME}: {up_down}{diff_percent}%\nHeadline: {article['title']}. \n Brief: {article['description']}"  for article in three_articles]


    client = Client(twilio_SID, AUTH_TOKEN)

    for article in new_news:
        message = client.messages.create(
            from_='',
            body=article,
            to=''
        )
