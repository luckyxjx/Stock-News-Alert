import requests
from twilio.rest import Client
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from dotenv import load_dotenv
from datetime import datetime
import csv

#load environment variables 
load_dotenv()

#constanst 
STOCK_NAME = "TSLA" 
COMPANY_NAME = "Tesla Inc" 

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

News_api = os.getenv('NEWS_API_KEY')
Stock_api = os.getenv('STOCK_API_KEY')
twilio_SID = os.getenv('TWILIO_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')

#key parameters 
Stock_params = {
    "function": "Time_Series_Daily",
    "symbol": STOCK_NAME,
    "apikey": Stock_api,
}

NEWS_params = {
    "apikey": News_api,
    "qInTitle": COMPANY_NAME,
}

try:
    response = requests.get(STOCK_ENDPOINT, params=Stock_params)
    response.raise_for_status()
    data = response.json()

    print("api response",data)

    data_list=[value for(key,value)in sorted(data.get("Time Series (Daily)", {}).items(), reverse=True)]

 # Write stock data to CSV
    with open('stock_data.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        
        for date, entry in sorted(data.get("Time Series (Daily)", {}).items()):
            writer.writerow([
                date,
                entry.get("1. open"),
                entry.get("2. high"),
                entry.get("3. low"),
                entry.get("4. close"),
                entry.get("5. volume"),
            ])
    
    if len(data_list) < 2:
        raise ValueError("Not enough data to compare stock prices.")

    yesterdaydata = data_list[0]
    day_before_yesterday = data_list[1]

    yesterdaydataprice = float(yesterdaydata["4. close"])
    day_before_yesterday_price = float(day_before_yesterday["4. close"])

    positive_difference = yesterdaydataprice - day_before_yesterday_price
    up_down = "⬆️" if positive_difference > 0 else "⬇️"
    diff_percent = round((positive_difference / day_before_yesterday_price) * 100)

    if abs(diff_percent) > 1:
        # Fetch news articles
        news = requests.get(NEWS_ENDPOINT, params=NEWS_params)
        news.raise_for_status()
        articles = news.json().get("articles", [])[:3]

        new_news = [f"{STOCK_NAME}: {up_down}{diff_percent}%\nHeadline: {article['title']}. \n Brief: {article['description']}" for article in articles]

        # Send messages
        client = Client(twilio_SID, AUTH_TOKEN)
        for article in new_news:
            message = client.messages.create(
                from_='+16623732831',
                body=article,
                to='+917814866533'
            )

    # Read data from CSV and plot
    dates = []
    closes = []
    
    with open('stock_data.csv', mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            dates.append(datetime.strptime(row['Date'], '%Y-%m-%d'))
            closes.append(float(row['Close']))

    plt.figure(figsize=(12, 6))
    plt.plot(dates, closes, marker='o', linestyle='-', color='b')
    plt.xlabel('Date')
    plt.ylabel('Closing Price')
    plt.title(f'{STOCK_NAME} Stock Prices')
    
    # Formatting the x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gca().xaxis.set_minor_locator(mdates.WeekdayLocator())
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.grid(True)
    plt.show()

except requests.RequestException as e:
    print(f"API request error: {e}")
except ValueError as e:
    print(e)
except Exception as e:
    print(f"An error occurred: {e}")
