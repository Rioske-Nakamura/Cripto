import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import requests
from datetime import datetime, time
import matplotlib.pyplot as plt
import pandas as pd
import difflib
import locale

# -------------------------
# Locale brasileiro para datas
# -------------------------
locale.setlocale(locale.LC_ALL, 'pt_BR')

# -------------------------
# Lista dinâmica com Entry + Listbox
# -------------------------
class AutocompleteEntry(tk.Entry):
    def __init__(self, lista, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lista = lista
        self.var = self["textvariable"] = tk.StringVar()
        self.var.trace("w", self.changed)
        self.bind("<Down>", self.move_down)
        self.listbox = None

    def changed(self, *args):
        value = self.var.get().lower()
        if value == '':
            self.hide_listbox()
        else:
            matches = difflib.get_close_matches(value, self.lista, n=10, cutoff=0.1)
            self.show_listbox(matches)

    def show_listbox(self, matches):
        if self.listbox:
            self.listbox.destroy()
        self.listbox = tk.Listbox(self.master, height=6, bg="#eeeeee", fg="#333", font=("Arial", 10), relief="flat")
        self.listbox.bind("<Double-Button-1>", self.selection)
        self.listbox.bind("<Right>", self.selection)

        for m in matches:
            self.listbox.insert(tk.END, m)

        self.listbox.place(x=self.winfo_x(), y=self.winfo_y() + self.winfo_height())

    def hide_listbox(self):
        if self.listbox:
            self.listbox.destroy()
            self.listbox = None

    def selection(self, event):
        if self.listbox:
            selection = self.listbox.get(tk.ACTIVE)
            self.var.set(selection)
            self.hide_listbox()

    def move_down(self, event):
        if self.listbox:
            self.listbox.focus_set()
            self.listbox.selection_set(0)

# -------------------------
# API & Lógica
# -------------------------
def buscar_moedas():
    url = "https://api.coingecko.com/api/v3/coins/list"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        moedas = r.json()
        if isinstance(moedas, list):
            return {f"{m['name']} ({m['symbol']})": m['id'] for m in moedas}
        else:
            print("Resposta inesperada da API:", moedas)
            return {}
    except Exception as e:
        print("Erro ao buscar moedas:", e)
        return {}

def pegar_dados(moeda, moeda_destino, inicio, fim):
    inicio_dt = datetime.combine(inicio, time.min)
    fim_dt = datetime.combine(fim, time.max)
    ts_inicio = int(inicio_dt.timestamp())
    ts_fim = int(fim_dt.timestamp())

    url = f"https://api.coingecko.com/api/v3/coins/{moeda}/market_chart/range"
    params = {"vs_currency": moeda_destino, "from": ts_inicio, "to": ts_fim}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return None
    dados = r.json()
    df = pd.DataFrame(dados["prices"], columns=["timestamp", "price"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df

def pegar_valor_atual(moeda_id, moeda_base):
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": moeda_id, "vs_currencies": moeda_base}
    r = requests.get(url, params=params)
    try:
        return r.json()[moeda_id][moeda_base]
    except:
        return None

def calcular_recomendacao(df):
    if df is None or df.empty:
        return 0
    variacao = (df["price"].iloc[-1] - df["price"].iloc[0]) / df["price"].iloc[0]
    volatilidade = df["price"].std()
    score = 0
    score += max(0, min(50, variacao * 200))
    score += max(0, min(50, 5 / (volatilidade + 0.001)))
    return round(min(100, score))

# -------------------------
# Interface Principal
# -------------------------
root = tk.Tk()
root.title("Analisador de Criptomoedas")
root.geometry("640x480")
root.configure(bg="#2c2c2c")

style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background="#2c2c2c", foreground="white", font=("Segoe UI", 10))
style.configure("TButton", font=("Segoe UI", 10), padding=6)
style.configure("TCombobox", padding=6)

root.option_add("*TCombobox*Listbox.background", "#f0f0f0")
root.option_add("*TCombobox*Listbox.foreground", "black")

moedas_dict = buscar_moedas()
moedas_formatadas = sorted(moedas_dict.keys())

campo_padrao = {"bg": "#eeeeee", "font": ("Segoe UI", 10), "relief": "flat", "highlightthickness": 1, "highlightbackground": "#888"}

moeda1_entry = AutocompleteEntry(moedas_formatadas, root, width=40, **campo_padrao)
moeda2_entry = AutocompleteEntry(moedas_formatadas, root, width=40, **campo_padrao)
moeda_base_var = ttk.Combobox(root, values=["brl", "usd", "eur"], width=10, font=("Segoe UI", 10))
moeda_base_var.set("brl")

labels = ["Moeda 1:", "Moeda 2 (opcional):", "Converter para:", "Data Início:", "Data Fim:"]
for i, texto in enumerate(labels):
    ttk.Label(root, text=texto).grid(row=i, column=0, padx=12, pady=8, sticky='e')

moeda1_entry.grid(row=0, column=1, padx=10, pady=5)
moeda2_entry.grid(row=1, column=1, padx=10, pady=5)
moeda_base_var.grid(row=2, column=1, padx=10, pady=5, sticky="w")

data_inicio = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=0,
                        locale='pt_BR', date_pattern='dd/MM/yyyy')
data_inicio.grid(row=3, column=1, padx=10, pady=5, sticky="w")

data_fim = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=0,
                     locale='pt_BR', date_pattern='dd/MM/yyyy')
data_fim.grid(row=4, column=1, padx=10, pady=5, sticky="w")

def analisar():
    moeda1_nome = moeda1_entry.get()
    moeda2_nome = moeda2_entry.get()
    moeda_base = moeda_base_var.get().lower()

    if moeda1_nome not in moedas_dict:
        resultado_label.config(text="Moeda 1 inválida.")
        return

    moeda1_id = moedas_dict[moeda1_nome]

    if moeda2_nome and moeda2_nome in moedas_dict:
        moeda2_id = moedas_dict[moeda2_nome]
        df2 = pegar_dados(moeda2_id, moeda_base, data_inicio.get_date(), data_fim.get_date())
    else:
        moeda2_id = None
        df2 = None

    df1 = pegar_dados(moeda1_id, moeda_base, data_inicio.get_date(), data_fim.get_date())

    plt.figure(figsize=(10, 5))
    plt.plot(df1.index, df1["price"], label=moeda1_nome, color="blue")

    if df2 is not None and not df2.empty:
        plt.plot(df2.index, df2["price"], label=moeda2_nome, color="green")
    else:
        print(f"Aviso: Sem dados para {moeda2_nome} ou moeda inválida.")

    plt.title(f"Evolução ({moeda_base.upper()})")
    plt.xlabel("Data")
    plt.ylabel(f"Preço ({moeda_base.upper()})")
    plt.grid()
    plt.legend()
    plt.tight_layout()
    plt.show()

    score1 = calcular_recomendacao(df1)
    valor1 = pegar_valor_atual(moeda1_id, moeda_base)
    texto = f"{moeda1_nome}: {score1}/100\nValor atual: {moeda_base.upper()} {valor1:,.2f}" if valor1 else f"{moeda1_nome}: {score1}/100"

    if df2 is not None and moeda2_id:
        score2 = calcular_recomendacao(df2)
        valor2 = pegar_valor_atual(moeda2_id, moeda_base)
        texto += f"\n\n{moeda2_nome}: {score2}/100\nValor atual: {moeda_base.upper()} {valor2:,.2f}" if valor2 else f"\n\n{moeda2_nome}: {score2}/100"

    resultado_label.config(text=texto)

# Botão e resultado
botao = ttk.Button(root, text="Analisar", command=analisar)
botao.grid(row=5, column=0, columnspan=2, pady=20)

resultado_label = tk.Label(root, text="", font=("Segoe UI", 11), justify="left", bg="#2c2c2c", fg="white")
resultado_label.grid(row=6, column=0, columnspan=2, padx=15, pady=10, sticky="w")

root.mainloop()
