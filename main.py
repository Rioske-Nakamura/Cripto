import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import requests
from datetime import datetime, time
import matplotlib.pyplot as plt
import pandas as pd

# Buscar e formatar moedas
def buscar_moedas():
    url = "https://api.coingecko.com/api/v3/coins/list"
    r = requests.get(url)
    moedas = r.json()
    return {f"{m['name']} ({m['symbol']})": m['id'] for m in moedas}

# Obter histórico de preços
def pegar_dados(moeda, moeda_destino, inicio, fim):
    inicio_dt = datetime.combine(inicio, time.min)
    fim_dt = datetime.combine(fim, time.max)
    ts_inicio = int(inicio_dt.timestamp())
    ts_fim = int(fim_dt.timestamp())

    url = f"https://api.coingecko.com/api/v3/coins/{moeda}/market_chart/range"
    params = {
        "vs_currency": moeda_destino,
        "from": ts_inicio,
        "to": ts_fim
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return None
    dados = r.json()
    df = pd.DataFrame(dados["prices"], columns=["timestamp", "price"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df

# Pega valor atual da moeda
def pegar_valor_atual(moeda_id, moeda_base):
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": moeda_id, "vs_currencies": moeda_base}
    r = requests.get(url, params=params)
    try:
        return r.json()[moeda_id][moeda_base]
    except:
        return None

# Cálculo da recomendação (0-100)
def calcular_recomendacao(df):
    if df is None or df.empty:
        return 0
    variacao = (df["price"].iloc[-1] - df["price"].iloc[0]) / df["price"].iloc[0]
    volatilidade = df["price"].std()
    score = 0
    score += max(0, min(50, variacao * 200))  # até 50 pontos por alta
    score += max(0, min(50, 5 / (volatilidade + 0.001)))  # até 50 por estabilidade
    return round(min(100, score))

# Ação ao clicar em "Analisar"
def analisar():
    moeda1_nome = moeda1_var.get()
    moeda2_nome = moeda2_var.get()
    moeda_base = moeda_base_var.get().lower()

    if moeda1_nome not in moedas_dict:
        resultado_label.config(text="Moeda 1 inválida.")
        return

    moeda1_id = moedas_dict[moeda1_nome]
    moeda2_id = moedas_dict.get(moeda2_nome, None)

    inicio = data_inicio.get_date()
    fim = data_fim.get_date()

    df1 = pegar_dados(moeda1_id, moeda_base, inicio, fim)
    df2 = pegar_dados(moeda2_id, moeda_base, inicio, fim) if moeda2_id else None

    plt.figure(figsize=(10, 5))
    plt.plot(df1.index, df1["price"], label=moeda1_nome, color="blue")
    if df2 is not None:
        plt.plot(df2.index, df2["price"], label=moeda2_nome, color="green")
    plt.title(f"Evolução ({moeda_base.upper()})")
    plt.xlabel("Data")
    plt.ylabel(f"Preço ({moeda_base.upper()})")
    plt.grid()
    plt.legend()
    plt.tight_layout()
    plt.show()

    score1 = calcular_recomendacao(df1)
    valor1 = pegar_valor_atual(moeda1_id, moeda_base)
    texto = f"{moeda1_nome}: {score1}/100 — Valor atual: {moeda_base.upper()} {valor1:,.2f}" if valor1 else f"{moeda1_nome}: {score1}/100"

    if df2 is not None and moeda2_id:
        score2 = calcular_recomendacao(df2)
        valor2 = pegar_valor_atual(moeda2_id, moeda_base)
        texto += f"\n{moeda2_nome}: {score2}/100 — Valor atual: {moeda_base.upper()} {valor2:,.2f}" if valor2 else f"\n{moeda2_nome}: {score2}/100"

    resultado_label.config(text=texto)

# ----- INTERFACE -----
root = tk.Tk()
root.title("Conversor e Analisador de Criptomoedas")
root.geometry("520x330")

# Buscar moedas ao iniciar
moedas_dict = buscar_moedas()
moedas_formatadas = sorted(moedas_dict.keys())

# Labels e campos
tk.Label(root, text="Moeda 1:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
moeda1_var = ttk.Combobox(root, values=moedas_formatadas, width=35)
moeda1_var.grid(row=0, column=1)

tk.Label(root, text="Moeda 2 (opcional):").grid(row=1, column=0, padx=5, pady=5, sticky='e')
moeda2_var = ttk.Combobox(root, values=moedas_formatadas, width=35)
moeda2_var.grid(row=1, column=1)

tk.Label(root, text="Converter para:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
moeda_base_var = ttk.Combobox(root, values=["brl", "usd", "eur"], width=10)
moeda_base_var.set("brl")
moeda_base_var.grid(row=2, column=1, sticky="w")

tk.Label(root, text="Data Início:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
data_inicio = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2)
data_inicio.grid(row=3, column=1, sticky="w")

tk.Label(root, text="Data Fim:").grid(row=4, column=0, padx=5, pady=5, sticky='e')
data_fim = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2)
data_fim.grid(row=4, column=1, sticky="w")

ttk.Button(root, text="Analisar", command=analisar).grid(row=5, column=0, columnspan=2, pady=15)

resultado_label = tk.Label(root, text="", font=("Arial", 11, "bold"), justify="left")
resultado_label.grid(row=6, column=0, columnspan=2, pady=5)

root.mainloop()
