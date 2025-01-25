import requests
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import numpy as np

BASE_URL = "https://api.simcotools.com/v1/realms/"

def get_market_price(realm, resource, quality, interval):
    url = f"{BASE_URL}{realm}/market/prices/{resource}/{quality}?interval={interval}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.status_code}

def get_vwap(realm, resource):
    url = f"{BASE_URL}{realm}/market/vwaps/{resource}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.status_code}

def get_market_summary(realm, resource, quality):
    url = f"{BASE_URL}{realm}/market/resources/{resource}/{quality}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.status_code}

def fetch_data():
    try:
        realm = int(realm_entry.get())
        resource = int(resource_entry.get())
        quality = int(quality_entry.get())
        interval = interval_var.get()

        market_data = get_market_price(realm, resource, quality, interval)
        vwap_data = get_vwap(realm, resource)
        summary_data = get_market_summary(realm, resource, quality)

        if "error" in market_data or "error" in vwap_data or "error" in summary_data:
            result_label.config(text="Erreur : Vérifiez les paramètres ou l'API.")
        else:
            price = market_data['prices'][0]['price']
            datetime = market_data['prices'][0]['datetime']
            vwap = vwap_data['vwaps'][0]['vwap']
            volume = summary_data['summary']['volume']

            result_label.config(
                text=f"Prix : {price} | VWAP : {vwap} | Volume : {volume}\nDernière mise à jour : {datetime}"
            )

            update_graph(summary_data, vwap)
            calculate_divergence(price, summary_data)
    except Exception as e:
        result_label.config(text=f"Erreur : {str(e)}")

def calculate_sma(prices, window):
    return np.convolve(prices, np.ones(window) / window, mode='valid')

def calculate_divergence(current_price, data):
    try:
        close_prices = [entry['closePrice'] for entry in data['summary']['latestClosePrices']]
        average_price = np.mean(close_prices)
        divergence = ((current_price - average_price) / average_price) * 100

        if divergence < -7:
            recommendation = "Strong Buy"
        elif divergence < -3:
            recommendation = "Buy"
        elif -3 <= divergence <= 3:
            recommendation = "Neutral"
        elif divergence > 3:
            recommendation = "Sell"
        else:
            recommendation = "Strong Sell"

        result_label.config(text=result_label.cget("text") + f"\nDivergence : {divergence:.2f}% | Recommandation : {recommendation}")
    except Exception as e:
        result_label.config(text=f"Erreur de calcul : {str(e)}")

def update_graph(data, vwap):
    try:
        close_prices = data['summary']['latestClosePrices']
        times = [entry['datetime'] for entry in close_prices]
        prices = [entry['closePrice'] for entry in close_prices]

        times = mdates.datestr2num(times)

        figure.clear()
        ax = figure.add_subplot(111)
        ax.plot(times, prices, marker="o", linestyle="-", color="blue", label="Prix")

        if vwap_var.get():
            ax.axhline(y=vwap, color="green", linestyle="--", label="VWAP")

        if sma_var.get():
            sma_window = int(sma_length_entry.get())
            if len(prices) >= sma_window:
                sma = calculate_sma(prices, window=sma_window)
                ax.plot(times[-len(sma):], sma, color="orange", linestyle="-", label=f"SMA ({sma_window})")

        points_count = len(prices)
        points_label.config(text=f"Nombre de points affichés : {points_count}")

        ax.set_title("Évolution des prix")
        ax.set_xlabel("Temps")
        ax.set_ylabel("Prix")
        ax.grid(True)
        ax.legend()

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        figure.autofmt_xdate()

        canvas.draw()
    except KeyError:
        result_label.config(text="Erreur lors de la mise à jour du graphique.")

app = tk.Tk()
app.title("SimCo Broker")
app.geometry("800x700")

frame_top = tk.Frame(app)
frame_top.pack(pady=10)

realm_label = tk.Label(frame_top, text="Realm ID:")
realm_label.grid(row=0, column=0, padx=5)
realm_entry = tk.Entry(frame_top)
realm_entry.grid(row=0, column=1, padx=5)
realm_entry.insert(0, "0")

resource_label = tk.Label(frame_top, text="Resource ID:")
resource_label.grid(row=1, column=0, padx=5)
resource_entry = tk.Entry(frame_top)
resource_entry.grid(row=1, column=1, padx=5)
resource_entry.insert(0, "1")

quality_label = tk.Label(frame_top, text="Quality:")
quality_label.grid(row=2, column=0, padx=5)
quality_entry = tk.Entry(frame_top)
quality_entry.grid(row=2, column=1, padx=5)
quality_entry.insert(0, "1")

interval_label = tk.Label(frame_top, text="Intervalle:")
interval_label.grid(row=3, column=0, padx=5)
interval_var = tk.StringVar(value="1min")
interval_menu = ttk.Combobox(frame_top, textvariable=interval_var, values=["1min", "5min", "15min", "1h", "2h", "4h", "12h", "1J", "2J", "3J", "1Sem", "2sem", "1mois"])
interval_menu.grid(row=3, column=1, padx=5)

fetch_button = tk.Button(frame_top, text="Obtenir les données", command=fetch_data)
fetch_button.grid(row=4, column=0, columnspan=2, pady=10)

vwap_var = tk.BooleanVar(value=True)
vwap_check = tk.Checkbutton(frame_top, text="Afficher VWAP", variable=vwap_var)
vwap_check.grid(row=5, column=0, columnspan=2)

sma_var = tk.BooleanVar(value=False)
sma_check = tk.Checkbutton(frame_top, text="Afficher SMA", variable=sma_var)
sma_check.grid(row=6, column=0, columnspan=2)

sma_length_label = tk.Label(frame_top, text="Longueur SMA:")
sma_length_label.grid(row=7, column=0, padx=5)
sma_length_entry = tk.Entry(frame_top)
sma_length_entry.grid(row=7, column=1, padx=5)
sma_length_entry.insert(0, "5")

result_label = tk.Label(app, text="", font=("Arial", 12))
result_label.pack(pady=10)

points_label = tk.Label(app, text="Nombre de points affichés : 0", font=("Arial", 10))
points_label.pack(pady=5)

frame_bottom = tk.Frame(app)
frame_bottom.pack(fill=tk.BOTH, expand=True)

figure = Figure(figsize=(8, 4), dpi=100)
canvas = FigureCanvasTkAgg(figure, master=frame_bottom)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

app.mainloop()