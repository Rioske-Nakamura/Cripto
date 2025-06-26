
# Analisador de Criptomoedas

Este é um aplicativo de interface gráfica feito em Python com `Tkinter` para analisar a variação de preços de criptomoedas, utilizando dados da API pública da CoinGecko.

## 💡 Funcionalidades

- Autocompletar para seleção de moedas
- Comparação entre duas criptomoedas
- Seleção de intervalo de datas
- Gráfico com evolução do preço
- Cálculo de “score de recomendação”
- Consulta ao valor atual da moeda
- Interface amigável e em português

## 🖼️ Interface do Aplicativo

### Tela principal:

![Tela principal](/Cripto-main/img/figura.png)

### Exemplo de gráfico gerado:

![Gráfico de exemplo](/Cripto-main/img/Figure_1.png)

## ⚙️ Tecnologias Utilizadas

- Python 3.x
- Tkinter
- tkcalendar
- matplotlib
- pandas
- requests
- CoinGecko API

## 🧪 Como Executar

1. Instale as dependências:
   ```bash
   pip install requests pandas matplotlib tkcalendar
   ```

2. Execute o programa:
   ```bash
   python app.py
   ```

## 📥 Instalação

Você pode clonar este repositório e executar localmente:

```bash
git clone https://github.com/Rioske-Nakamura/Cripto

```

## 📄 Licença

Este projeto está sob a licença MIT.

## 👤

- GitHub: [@Rioske-Nakamura](https://github.com/Rioske-Nakamura)
- GitHub: [@Victor14791012](https://github.com/Victor14791012)

## Apresentação

- Canva: https://www.canva.com/design/DAGrd2Lb9Hs/9kt-L-DQro5QKENS8NU6uw/edit?ui=eyJBIjp7fX0



## 📐 Conceitos Matemáticos Utilizados

### 🔹 Variação Percentual
Usada para medir o crescimento ou queda do preço da criptomoeda ao longo do período:

```
Variação = (Preço final - Preço inicial) / Preço inicial
```

### 🔹 Volatilidade (Desvio Padrão)
Serve como medida de risco e instabilidade dos preços no período analisado:

```
Volatilidade = Desvio padrão dos preços
```

### 🔹 Score de Recomendação
Fórmula combinada baseada em:
- Crescimento percentual multiplicado por um fator de peso
- Inverso da volatilidade, para penalizar ativos muito instáveis
- Score final limitado a um máximo de 100 pontos

### 🔹 Média Aritmética Simples
Utilizada implicitamente nos cálculos de análise com `pandas` para representar médias de preços.

Esses cálculos ajudam a oferecer uma análise objetiva e quantitativa do desempenho das criptomoedas no período selecionado.



