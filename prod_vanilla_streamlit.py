import streamlit as st
import pandas as pd
import altair as alt
import numpy as np


def calcular_produtividade_baunilha(num_mudas, ano, sistema, usar_modelo_linear=False):
    producao_por_hectare = {
        3: 500,
        4: 1000,
        5: 1600,
        6: 2500,
    }

    if sistema == "SAF":
        area_por_muda = 4
    else:  # Semi-intensivo
        area_por_muda = 2.5

    hectares = (num_mudas * area_por_muda) / 10000  # Convertendo para hectares

    if usar_modelo_linear and ano <= 2:
        coef = (500 - 0) / (3 - 0)
        producao = max(0, coef * (ano - 0)) * hectares
    elif ano <= 6:
        producao = producao_por_hectare.get(ano, 0) * hectares
    else:
        producao = 2750 * hectares

    producao_kg = producao
    produtividade_por_pe = producao_kg / num_mudas

    # Cálculo do número de favas
    favas_por_pe_max = 30
    fator_producao = min(1, producao_kg / (2500 * hectares))
    favas_por_pe = favas_por_pe_max * fator_producao
    numero_favas = favas_por_pe * num_mudas

    # Cálculo do peso das favas
    peso_favas_verdes = numero_favas * 20 / 1000  # em kg
    peso_favas_curadas = numero_favas * 4 / 1000  # em kg

    # Cálculo do valor de mercado
    valor_favas_verdes = peso_favas_verdes * 47  # US$
    valor_favas_curadas = peso_favas_curadas * 154  # US$
    valor_extrato = valor_favas_curadas * 2.25  # US$

    return (
        producao_kg,
        produtividade_por_pe,
        numero_favas,
        peso_favas_verdes,
        peso_favas_curadas,
        hectares,
        valor_favas_verdes,
        valor_favas_curadas,
        valor_extrato,
    )


def calcular_cumulativo(num_mudas, anos, sistema, usar_modelo_linear=False):
    resultados_cumulativos = {
        "Produção Total (kg)": 0,
        "Número de Favas": 0,
        "Peso Favas Verdes (kg)": 0,
        "Peso Favas Curadas (kg)": 0,
        "Valor Favas Verdes (US$)": 0,
        "Valor Favas Curadas (US$)": 0,
        "Valor Extrato 1-fold (US$)": 0,
    }
    resultados_anuais = []

    for ano in range(1, anos + 1):
        res = calcular_produtividade_baunilha(
            num_mudas, ano, sistema, usar_modelo_linear
        )
        resultados_anuais.append(
            {
                "Ano": ano,
                "Produção Total (kg)": res[0],
                "Número de Favas": res[2],
                "Peso Favas Verdes (kg)": res[3],
                "Peso Favas Curadas (kg)": res[4],
                "Valor Favas Verdes (US$)": res[6],
                "Valor Favas Curadas (US$)": res[7],
                "Valor Extrato 1-fold (US$)": res[8],
            }
        )
        for key in resultados_cumulativos:
            resultados_cumulativos[key] += resultados_anuais[-1][key]

    return resultados_cumulativos, resultados_anuais


st.set_page_config(
    page_title="Calculadora de Produtividade de Baunilha", page_icon="🌿", layout="wide"
)

st.title("Calculadora de Produtividade de Baunilha 🌿")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Parâmetros de Entrada")
    num_mudas = st.number_input("Número de Mudas", min_value=1, value=4000, step=100)
    anos_projecao = st.slider("Anos de Projeção", min_value=1, max_value=15, value=6)
    sistema = st.radio("Sistema de Cultivo", ["SAF", "Semi-intensivo"])
    usar_modelo_linear = st.checkbox("Usar modelo linear para anos 1 e 2", value=True)

with col2:
    st.subheader("Informações de Mercado")
    st.write("Preços de referência:")
    st.write("- Fava verde: US$ 47/kg")
    st.write("- Fava curada: US$ 154/kg")
    st.write("- Extrato 1-fold: 2,25x o preço da fava curada")

resultados_cumulativos, resultados_anuais = calcular_cumulativo(
    num_mudas, anos_projecao, sistema, usar_modelo_linear
)

st.header(f"Resultados Cumulativos após {anos_projecao} anos")
col1, col2, col3 = st.columns(3)
col1.metric(
    "Produção Total Acumulada",
    f"{resultados_cumulativos['Produção Total (kg)']:.2f} kg",
)
col2.metric("Número Total de Favas", f"{resultados_cumulativos['Número de Favas']:.0f}")
col3.metric(
    "Área Necessária",
    f"{(num_mudas * (4 if sistema == 'SAF' else 2.5) / 10000):.2f} hectares",
)

st.subheader("Projeção Cumulativa de Favas")
col1, col2 = st.columns(2)
col1.metric(
    "Peso Total Favas Verdes",
    f"{resultados_cumulativos['Peso Favas Verdes (kg)']:.2f} kg",
)
col2.metric(
    "Peso Total Favas Curadas",
    f"{resultados_cumulativos['Peso Favas Curadas (kg)']:.2f} kg",
)

st.subheader("Projeção Cumulativa de Valor de Mercado (US$)")
col1, col2, col3 = st.columns(3)
col1.metric(
    "Valor Total Favas Verdes",
    f"${resultados_cumulativos['Valor Favas Verdes (US$)']:.2f}",
)
col2.metric(
    "Valor Total Favas Curadas",
    f"${resultados_cumulativos['Valor Favas Curadas (US$)']:.2f}",
)
col3.metric(
    "Valor Total Extrato 1-fold",
    f"${resultados_cumulativos['Valor Extrato 1-fold (US$)']:.2f}",
)

st.header("Gráficos de Produção Cumulativa")

df_cumulativo = pd.DataFrame(resultados_anuais)
df_cumulativo = df_cumulativo.cumsum().reset_index()
df_cumulativo["Ano"] = range(1, anos_projecao + 1)

# Gráfico de Produção Cumulativa
chart_producao = (
    alt.Chart(df_cumulativo)
    .mark_area()
    .encode(x="Ano", y="Produção Total (kg)", tooltip=["Ano", "Produção Total (kg)"])
    .properties(title="Produção Total Cumulativa (kg)", width=600, height=400)
)
st.altair_chart(chart_producao, use_container_width=True)

# Gráfico de Valor de Mercado Cumulativo
chart_valor = (
    alt.Chart(df_cumulativo)
    .mark_line()
    .encode(
        x="Ano",
        y="Valor Favas Curadas (US$)",
        tooltip=["Ano", "Valor Favas Curadas (US$)"],
    )
    .properties(
        title="Valor de Mercado Cumulativo - Favas Curadas (US$)", width=600, height=400
    )
)
st.altair_chart(chart_valor, use_container_width=True)

st.header("Tabela de Resultados Anuais")
st.dataframe(pd.DataFrame(resultados_anuais).set_index("Ano"))

st.header("Sobre a Cultura da Baunilheira")
st.write(
    """
- A baunilha fica produtiva durante 15 anos, chegando à máxima produção depois de seis anos.
- Em um sistema de produção semi intensivo, com 4000 mudas por hectare, os seguintes rendimentos podem ser esperados:
  - Ano 3: 500 kilos
  - Ano 4: 1 tonelada
  - Ano 5: 1,6 tonelada
  - Ano 6: 2,5 toneladas
  - Demais anos: Entre 2,5 e 3 toneladas
- A produtividade média sugerida é de 0,5 a 1 kilo por pé de baunilha.
- Para os anos 1 e 2, um modelo linear é usado para estimar a produção, assumindo um crescimento gradual até o ano 3.
- Uma muda na produtividade mais alta (aos 6 anos) produz aproximadamente 30 favas.
- Cada fava verde tem cerca de 20g.
- Cada fava curada tem cerca de 4g.
- No sistema agroflorestal (SAF), cada muda ocupa 4m².
- No sistema semi-intensivo, cada muda ocupa 2,5m².
- Preços de referência (sujeitos a variações de mercado):
  - Fava verde: US$ 47/kg
  - Fava curada: US$ 154/kg
  - Extrato 1-fold: 2,25x o preço da fava curada
"""
)
