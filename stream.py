import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import difflib
import locale
import plotly.graph_objects as go

# Configuração inicial
locale.setlocale(locale.LC_ALL, 'pt_BR')
st.set_page_config(page_title="Analisador de Criptomoedas", layout="wide")

# -------------------------
# Funções da API
# -------------------------
# buscar moedas
@st.cache_data(ttl=3600)
def buscar_moedas():
    url = "https://api.coingecko.com/api/v3/coins/list"
    try:
        r = requests.get(url, timeout=100)
        r.raise_for_status()
        moedas = r.json()
        if isinstance(moedas, list):
            return {f"{m['name']} ({m['symbol']})": m['id'] for m in moedas}
        else:
            st.error("Resposta inesperada da API")
            return {}
    except Exception as e:
        st.error(f"Erro ao buscar moedas: {e}")
        return {}


# pegar dados
@st.cache_data(ttl=300)
def pegar_dados(moeda, moeda_destino, inicio, fim):
    inicio_dt = datetime.combine(inicio, datetime.min.time())
    fim_dt = datetime.combine(fim, datetime.max.time())
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


# pegar valor atual
@st.cache_data(ttl=60)  
def pegar_valor_atual(moeda_id, moeda_base):
    """Obtém o valor atual de uma moeda"""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": moeda_id,
        "vs_currencies": moeda_base
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data[moeda_id][moeda_base]
    except Exception as e:
        st.error(f"Erro ao obter valor atual: {e}")
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
# Interface Streamlit
# -------------------------
def main():
    st.title("📊 Analisador de Criptomoedas")
    
    # Carrega a lista de moedas
    moedas_dict = buscar_moedas()
    moedas_formatadas = sorted(moedas_dict.keys())
    
    # Inicializa o session_state se necessário
    if 'moeda1' not in st.session_state:
        st.session_state.moeda1 =  ""
    if 'moeda2' not in st.session_state:
        st.session_state.moeda2 = ""
    
    # Sidebar para inputs
    with st.sidebar:
        st.header("Parâmetros de Análise")
        
        # Input para Moeda 1 com sugestões
        moeda1_input = st.text_input("Digite Moeda 1:", value=st.session_state.moeda1, key="moeda1_input")
        
        # Filtra sugestões baseadas no input
        if moeda1_input:
            matches = difflib.get_close_matches(moeda1_input.lower(), moedas_formatadas, n=5, cutoff=0.1)
            if matches:
                st.write("Sugestões:")
                for m in matches:
                    if st.button(m, key=f"sug_m1_{m}"):
                        st.session_state.moeda1 = m
                        st.rerun()
        
        # Input para Moeda 2 com sugestões
        moeda2_input = st.text_input("Digite Moeda 2 (opcional):", value=st.session_state.moeda2, key="moeda2_input")
        
        if moeda2_input:
            matches = difflib.get_close_matches(moeda2_input.lower(), moedas_formatadas, n=5, cutoff=0.1)
            if matches:
                st.write("Sugestões:")
                for m in matches:
                    if st.button(m, key=f"sug_m2_{m}"):
                        st.session_state.moeda2 = m
                        st.rerun()
        
        # Outros parâmetros
        moeda_base = st.selectbox("Moeda de referência:", ["brl", "usd", "eur"])
        
        # Datas padrão: início do mês até hoje
        hoje = datetime.now().date()
        inicio_mes = hoje.replace(day=1)
        
        data_inicio = st.date_input("Data início:", inicio_mes)
        data_fim = st.date_input("Data fim:", hoje)
        
        if st.button("🔍 Analisar", use_container_width=True):
            st.session_state.analisar = True
    
    # Área de resultados
    if st.session_state.get('analisar', False):
        if not st.session_state.moeda1 or st.session_state.moeda1 not in moedas_dict:
            st.error("Selecione uma Moeda 1 válida")
            return
        
        with st.spinner("Obtendo dados..."):
            # Processamento dos dados
            moeda1_id = moedas_dict[st.session_state.moeda1]
            df1 = pegar_dados(moeda1_id, moeda_base, data_inicio, data_fim)
            
            if st.session_state.moeda2 and st.session_state.moeda2 in moedas_dict:
                moeda2_id = moedas_dict[st.session_state.moeda2]
                df2 = pegar_dados(moeda2_id, moeda_base, data_inicio, data_fim)
            else:
                df2 = None
            
            # Exibição dos resultados
            if df1 is not None:
                # Criar gráfico interativo com Plotly
                fig = go.Figure()
                
                # Adicionar primeira moeda
                fig.add_trace(go.Scatter(
                    x=df1.index,
                    y=df1["price"],
                    name=st.session_state.moeda1,
                    line=dict(color='blue'),
                    hovertemplate='<b>%{x|%d/%m/%Y %H:%M}</b><br>Valor: %{y:,.2f} '+moeda_base.upper(),
                    mode='lines'
                ))
                
                # Adicionar segunda moeda se existir
                if df2 is not None:
                    fig.add_trace(go.Scatter(
                        x=df2.index,
                        y=df2["price"],
                        name=st.session_state.moeda2,
                        line=dict(color='green'),
                        hovertemplate='<b>%{x|%d/%m/%Y %H:%M}</b><br>Valor: %{y:,.2f} '+moeda_base.upper(),
                        mode='lines'
                    ))
                
                # Configurações do layout
                fig.update_layout(
                    title=f'Evolução de Preço ({moeda_base.upper()})',
                    xaxis_title='Data',
                    yaxis_title=f'Preço ({moeda_base.upper()})',
                    hovermode="x unified",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    height=500
                )
                
                # Mostrar o gráfico
                st.plotly_chart(fig, use_container_width=True)
                
                # Métricas
                score1 = calcular_recomendacao(df1)
                valor1 = pegar_valor_atual(moeda1_id, moeda_base)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(f"{st.session_state.moeda1} - Score", f"{score1}/100")
                    if valor1:
                        st.metric("Valor Atual", f"{moeda_base.upper()} {valor1:,.2f}")
                
                if df2 is not None and st.session_state.moeda2:
                    score2 = calcular_recomendacao(df2)
                    valor2 = pegar_valor_atual(moeda2_id, moeda_base)
                    
                    with col2:
                        st.metric(f"{st.session_state.moeda2} - Score", f"{score2}/100")
                        if valor2:
                            st.metric("Valor Atual", f"{moeda_base.upper()} {valor2:,.2f}")

if __name__ == "__main__":
    main()