import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import requests
from twilio.rest import Client
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from dotenv import load_dotenv
from datetime import datetime
import csv

# Load environment variables
load_dotenv()

# Constants
STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

News_api = os.getenv('NEWS_API_KEY')
Stock_api = os.getenv('STOCK_API_KEY')
twilio_SID = os.getenv('TWILIO_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')

def fetch_stock_data(stock_name):
    params = {
        "function": "Time_Series_Daily",
        "symbol": stock_name,
        "apikey": Stock_api,
    }
    response = requests.get(STOCK_ENDPOINT, params=params)
    response.raise_for_status()
    data = response.json()
    return data

def fetch_news(company_name):
    params = {
        "apikey": News_api,
        "qInTitle": company_name,
    }
    response = requests.get(NEWS_ENDPOINT, params=params)
    response.raise_for_status()
    return response.json().get("articles", [])[:3]

def send_notifications(messages, phone_number):
    client = Client(twilio_SID, AUTH_TOKEN)
    for message in messages:
        client.messages.create(
            from_='TWILIO_ACC_NUMBER',
            body=message,
            to=phone_number
        )

def plot_stock_data(filename):
    dates, closes = [], []
    with open(filename, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            dates.append(datetime.strptime(row['Date'], '%Y-%m-%d'))
            closes.append(float(row['Close']))

    plt.figure(figsize=(12, 6))
    plt.plot(dates, closes, marker='o', linestyle='-', color='b')
    plt.xlabel('Date')
    plt.ylabel('Closing Price')
    plt.title(f'Stock Prices')
    
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.grid(True)
    plt.show()

def process_request():
    stock_name = stock_entry.get().upper()
    company_name = company_entry.get()
    phone_number = phone_entry.get()
    action = action_var.get()

    try:
        stock_data = fetch_stock_data(stock_name)
        data_list = [value for (key, value) in sorted(stock_data.get("Time Series (Daily)", {}).items(), reverse=True)]

        with open('stock_data.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
            for date, entry in sorted(stock_data.get("Time Series (Daily)", {}).items()):
                writer.writerow([
                    date,
                    entry.get("1. open"),
                    entry.get("2. high"),
                    entry.get("3. low"),
                    entry.get("4. close"),
                    entry.get("5. volume"),
                ])

        yesterday_price = float(data_list[0]["4. close"])
        day_before_yesterday_price = float(data_list[1]["4. close"])
        positive_difference = yesterday_price - day_before_yesterday_price
        up_down = "⬆️" if positive_difference > 0 else "⬇️"
        diff_percent = round((positive_difference / day_before_yesterday_price) * 100)

        if abs(diff_percent) > 1:
            articles = fetch_news(company_name)
            messages = [f"{stock_name}: {up_down}{diff_percent}%\nHeadline: {article['title']}\nBrief: {article['description']}" for article in articles]

            if action == "SMS/WhatsApp":
                send_notifications(messages, phone_number)
                messagebox.showinfo("Notification", "Messages sent successfully!")
            elif action == "Show Data":
                plot_stock_data('stock_data.csv')
    except requests.RequestException as e:
        messagebox.showerror("API Error", f"API request failed: {e}")
    except ValueError as e:
        messagebox.showerror("Data Error", str(e))
    except Exception as e:
        messagebox.showerror("Error", str(e))

#tkinter
root = tk.Tk()
root.title("Stock Data Viewer")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

ttk.Label(frame, text="Stock Symbol:").grid(row=0, column=0, sticky=tk.W)
stock_entry = ttk.Entry(frame)
stock_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))

ttk.Label(frame, text="Company Name:").grid(row=1, column=0, sticky=tk.W)
company_entry = ttk.Entry(frame)
company_entry.grid(row=1, column=1, sticky=(tk.W, tk.E))

ttk.Label(frame, text="Phone Number:").grid(row=2, column=0, sticky=tk.W)
phone_entry = ttk.Entry(frame)
phone_entry.grid(row=2, column=1, sticky=(tk.W, tk.E))

ttk.Label(frame, text="Action:").grid(row=3, column=0, sticky=tk.W)
action_var = tk.StringVar(value="Show Data")
ttk.Radiobutton(frame, text="Show Data", variable=action_var, value="Show Data").grid(row=3, column=1, sticky=tk.W)
ttk.Radiobutton(frame, text="SMS/WhatsApp", variable=action_var, value="SMS/WhatsApp").grid(row=3, column=2, sticky=tk.W)

ttk.Button(frame, text="Submit", command=process_request).grid(row=4, column=1, sticky=(tk.W, tk.E))

root.mainloop()
