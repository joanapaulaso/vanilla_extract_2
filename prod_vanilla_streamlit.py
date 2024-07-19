import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from io import BytesIO

CUSTO_POR_MUDA = 0.85  # US$

def calcular_produtividade_baunilha(num_mudas, ano, usar_modelo_linear=False):
    producao_por_hectare = {
        3: 500,
        4: 1000,
        5: 1600,
        6: 2500,
    }

    hectares = num_mudas / 4000  # Agora usamos um valor fixo de mudas por hectare

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

    # Cálculo do preço de cada fava
    unidade_fava_verde = (20 * 15) / 1000  # US$/kg
    unidade_fava_curada = (4 * 139.75) / 1000  # US$/kg

    # Cálculo do valor de mercado
    valor_favas_verdes = unidade_fava_verde * numero_favas  # US$
    valor_favas_curadas = unidade_fava_curada * numero_favas  # US$
    valor_extrato = valor_favas_curadas * 2.25  # US$

    return (
        producao_kg,
        produtividade_por_pe,
        numero_favas,
        peso_favas_verdes,
        peso_favas_curadas,
        valor_favas_verdes,
        valor_favas_curadas,
        valor_extrato,
    )


def calcular_cumulativo(num_mudas, anos, usar_modelo_linear=False):
    resultados_cumulativos = {
        "Produção Total (kg)": 0,
        "Número de Favas": 0,
        "Peso Favas Verdes (kg)": 0,
        "Peso Favas Curadas (kg)": 0,
        "Valor Favas Verdes (US$)": 0,
        "Valor Favas Curadas (US$)": 0,
        "Valor Extrato 1-fold (US$)": 0,
        "Faturamento Bruto (US$)": 0,
        "Custo Inicial Mudas (US$)": num_mudas * CUSTO_POR_MUDA,
    }
    resultados_anuais = []

    for ano in range(1, anos + 1):
        res = calcular_produtividade_baunilha(num_mudas, ano, usar_modelo_linear)
        faturamento_bruto = res[7]
        lucro_bruto = faturamento_bruto * 0.2130  # 21.30% do faturamento bruto
        custo_inicial_mudas = num_mudas * CUSTO_POR_MUDA if ano == 1 else 0
        lucro_liquido = lucro_bruto - custo_inicial_mudas

        resultados_anuais.append(
            {
                "Ano": ano,
                "Produção Total (kg)": res[0],
                "Número de Favas": res[2],
                "Peso Favas Verdes (kg)": res[3],
                "Peso Favas Curadas (kg)": res[4],
                "Valor Favas Verdes (US$)": res[5],
                "Valor Favas Curadas (US$)": res[6],
                "Valor Extrato 1-fold (US$)": res[7],
                "Faturamento Bruto (US$)": faturamento_bruto,
                "Faturamento Líquido (US$)": lucro_liquido,
            }
        )
        for key in resultados_cumulativos:
            if key != "Custo Inicial Mudas (US$)":
                resultados_cumulativos[key] += resultados_anuais[-1][key]

    # Calcular o faturamento líquido cumulativo
    faturamento_bruto_total = resultados_cumulativos["Faturamento Bruto (US$)"]
    custo_inicial_mudas = resultados_cumulativos["Custo Inicial Mudas (US$)"]
    lucro_bruto = faturamento_bruto_total * 0.2130  # 21.30% do faturamento bruto
    lucro_liquido = lucro_bruto - custo_inicial_mudas

    resultados_cumulativos["Faturamento Líquido (US$)"] = lucro_liquido

    return resultados_cumulativos, resultados_anuais


def calcular_area_necessaria(num_mudas, sistema):
    if sistema == "SAF":
        return (num_mudas * 4) / 10000  # 4m² por muda no SAF
    else:  # Semi-intensivo
        return (num_mudas * 2.5) / 10000  # 2.5m² por muda no semi-intensivo


def gerar_excel(resultados_anuais, resultados_cumulativos):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine="openpyxl")

    df_anuais = pd.DataFrame(resultados_anuais)
    df_cumulativos = pd.DataFrame([resultados_cumulativos])

    df_anuais.to_excel(writer, sheet_name="Anuais", index=False)
    df_cumulativos.to_excel(writer, sheet_name="Cumulativos", index=False)

    writer.close()
    output.seek(0)

    return output


def calcular_plano_acao(
    num_mudas_inicial, faturamento_objetivo, anos, taxa_crescimento_maxima=1.5
):
    def calcular_faturamento_total(mudas_inicial, taxa_crescimento, anos_calc):
        fat_total = 0
        mudas = mudas_inicial
        for ano in range(1, anos_calc + 1):
            fat_anual = 0
            for ano_impl in range(1, ano + 1):
                mudas_impl = mudas_inicial * (taxa_crescimento ** (ano_impl - 1))
                _, _, _, _, _, _, _, valor_extrato = calcular_produtividade_baunilha(
                    mudas_impl, ano - ano_impl + 1
                )
                fat_anual += valor_extrato * 0.22
            fat_total += fat_anual
            mudas *= taxa_crescimento
        return fat_total

    # Verificar se é possível atingir o objetivo com o crescimento máximo
    faturamento_maximo = calcular_faturamento_total(
        num_mudas_inicial, taxa_crescimento_maxima, anos
    )
    if faturamento_maximo < faturamento_objetivo:
        # Calcular o número mínimo de mudas iniciais necessárias
        mudas_min = num_mudas_inicial
        while (
            calcular_faturamento_total(mudas_min, taxa_crescimento_maxima, anos)
            < faturamento_objetivo
        ):
            mudas_min *= 1.1  # Aumentar em 10% e tentar novamente

        # Calcular o número de anos necessários com as mudas iniciais fornecidas
        anos_necessarios = anos
        while (
            anos_necessarios <= 15
            and calcular_faturamento_total(
                num_mudas_inicial, taxa_crescimento_maxima, anos_necessarios
            )
            < faturamento_objetivo
        ):
            anos_necessarios += 1

        return (
            None,
            None,
            None,
            {
                "possivel": False,
                "faturamento_maximo": faturamento_maximo,
                "mudas_minimas": mudas_min,
                "anos_necessarios": (
                    anos_necessarios if anos_necessarios <= 15 else None
                ),
            },
        )

    # Encontrar a taxa de crescimento ideal usando busca binária
    taxa_min, taxa_max = 1.0, taxa_crescimento_maxima
    while taxa_max - taxa_min > 0.0001:
        taxa_meio = (taxa_min + taxa_max) / 2
        if (
            calcular_faturamento_total(num_mudas_inicial, taxa_meio, anos)
            < faturamento_objetivo
        ):
            taxa_min = taxa_meio
        else:
            taxa_max = taxa_meio

    taxa_crescimento = (taxa_min + taxa_max) / 2

    # Calcular o plano com a taxa de crescimento encontrada
    resultados_plano = []
    resultados_detalhados = []
    num_mudas = num_mudas_inicial
    faturamento_acumulado = 0

    for ano in range(1, anos + 1):
        faturamento_liquido_anual = 0
        for ano_impl in range(1, ano + 1):
            mudas_impl = num_mudas_inicial * (taxa_crescimento ** (ano_impl - 1))
            _, _, _, _, _, _, _, valor_extrato = calcular_produtividade_baunilha(
                mudas_impl, ano - ano_impl + 1
            )
            faturamento_liquido_anual += valor_extrato * 0.22
            resultados_detalhados.append(
                {
                    "Ano de Implementação": ano_impl,
                    "Ano": ano,
                    "Número de Mudas": mudas_impl,
                    "Faturamento Líquido (US$)": valor_extrato * 0.22,
                }
            )

        faturamento_acumulado += faturamento_liquido_anual
        resultados_plano.append(
            {
                "Ano": ano,
                "Número de Mudas": num_mudas,
                "Faturamento Líquido (US$)": faturamento_liquido_anual,
                "Faturamento Acumulado (US$)": faturamento_acumulado,
            }
        )
        num_mudas = num_mudas * taxa_crescimento

    return (
        pd.DataFrame(resultados_plano),
        pd.DataFrame(resultados_detalhados),
        taxa_crescimento,
        {"possivel": True},
    )


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
    faturamento_objetivo = st.number_input(
        "Faturamento Líquido Objetivo (US$)", min_value=1.0, value=10000.0, step=1000.0
    )

with col2:
    st.subheader("Informações de Mercado")
    st.write("Preços de referência:")
    st.write("- Fava verde: US$ 15/kg")
    st.write("- Fava verde (unidade): US$ 0.30")
    st.write("- Fava curada: US$ 139.75/kg")
    st.write("- Fava curada (unidade): US$ 0.56")
    st.write("- Extrato 1-fold: 2,25x o preço da fava curada")
    st.write("- Margem de lucro: 21,30% do faturamento bruto")

resultados_cumulativos, resultados_anuais = calcular_cumulativo(
    num_mudas, anos_projecao, usar_modelo_linear
)
area_necessaria = calcular_area_necessaria(num_mudas, sistema)

st.header(f"Resultados Cumulativos após {anos_projecao} anos")
col1, col2, col3 = st.columns(3)
col1.metric(
    "Produção Total Acumulada",
    f"{resultados_cumulativos['Produção Total (kg)']:,.2f} kg",
)
col2.metric(
    "Número Total de Favas", f"{resultados_cumulativos['Número de Favas']:,.0f}"
)
col3.metric("Área Necessária", f"{area_necessaria:,.0f} hectares")

st.subheader("Projeção Cumulativa de Favas")
col1, col2 = st.columns(2)
col1.metric(
    "Peso Total Favas Verdes",
    f"{resultados_cumulativos['Peso Favas Verdes (kg)']:,.2f} kg",
)
col2.metric(
    "Peso Total Favas Curadas",
    f"{resultados_cumulativos['Peso Favas Curadas (kg)']:,.2f} kg",
)

st.subheader("Projeção Cumulativa de Valor de Mercado e Lucro (US$)")
col1, col2, col3 = st.columns(3)
col1.metric(
    "Valor Total Extrato 1-fold",
    f"$ {resultados_cumulativos['Valor Extrato 1-fold (US$)']:,.2f}",
)
col2.metric(
    "Custo Inicial Mudas",
    f"$ {resultados_cumulativos['Custo Inicial Mudas (US$)']:,.2f}",
)
col3.metric(
    "Faturamento Líquido",
    f"$ {resultados_cumulativos['Faturamento Líquido (US$)']:,.2f}",
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
df_resultados_anuais = pd.DataFrame(resultados_anuais).set_index("Ano")
st.dataframe(
    df_resultados_anuais.style.format(
        {
            "Produção Total (kg)": "{:,.2f}",
            "Número de Favas": "{:,.0f}",
            "Peso Favas Verdes (kg)": "{:,.2f}",
            "Peso Favas Curadas (kg)": "{:,.2f}",
            "Valor Favas Verdes (US$)": "${:,.2f}",
            "Valor Favas Curadas (US$)": "${:,.2f}",
            "Valor Extrato 1-fold (US$)": "${:,.2f}",
            "Faturamento Bruto (US$)": "${:,.2f}",
            "Faturamento Líquido (US$)": "${:,.2f}",
        }
    )
)

if st.button("Gerar Tabela Excel"):
    excel_data = gerar_excel(resultados_anuais, resultados_cumulativos)
    st.download_button(
        label="Baixar Tabela Excel",
        data=excel_data.getvalue(),
        file_name="resultados_baunilha.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

if st.button("Gerar Plano de Ação"):
    plano_acao, resultados_detalhados, taxa_crescimento, info = calcular_plano_acao(
        num_mudas, faturamento_objetivo, anos_projecao
    )

    if info["possivel"]:
        st.success(
            f"Plano de ação gerado para atingir o faturamento objetivo em {anos_projecao} anos."
        )
        st.info(
            f"Taxa de crescimento anual necessária: {(taxa_crescimento - 1) * 100:,.2f}%"
        )

        st.write(plano_acao)
        st.write(resultados_detalhados)

        # Gráfico de crescimento do número de mudas
        chart_mudas = (
            alt.Chart(plano_acao)
            .mark_line()
            .encode(x="Ano", y="Número de Mudas", tooltip=["Ano", "Número de Mudas"])
            .properties(title="Crescimento do Número de Mudas", width=600, height=400)
        )
        st.altair_chart(chart_mudas, use_container_width=True)

        # Gráfico de faturamento acumulado
        chart_faturamento = (
            alt.Chart(plano_acao)
            .mark_line()
            .encode(
                x="Ano",
                y="Faturamento Acumulado (US$)",
                tooltip=["Ano", "Faturamento Acumulado (US$)"],
            )
            .properties(title="Faturamento Acumulado", width=600, height=400)
        )
        st.altair_chart(chart_faturamento, use_container_width=True)

        # Botões de download
        if st.button("Gerar Tabela Excel 2"):
            excel_data = gerar_excel(
                resultados_detalhados, plano_acao.to_dict("records")
            )
            st.download_button(
                label="Baixar Tabela Excel",
                data=excel_data.getvalue(),
                file_name="plano_acao_baunilha.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        # Botão para baixar o plano de ação como CSV
        st.download_button(
            label="Baixar Plano de Ação (CSV)",
            data=plano_acao.to_csv(index=False).encode("utf-8"),
            file_name="plano_acao.csv",
            mime="text/csv",
        )

        # Botão para baixar os resultados detalhados como CSV
        st.download_button(
            label="Baixar Resultados Detalhados (CSV)",
            data=resultados_detalhados.to_csv(index=False).encode("utf-8"),
            file_name="resultados_detalhados.csv",
            mime="text/csv",
        )

        st.header("Gráfico de Detalhamento do Plano de Ação")
        chart_detalhado = (
            alt.Chart(resultados_detalhados)
            .mark_line()
            .encode(
                x="Ano",
                y="Faturamento Líquido (US$)",
                color="Ano de Implementação:N",
                tooltip=["Ano de Implementação", "Ano", "Faturamento Líquido (US$)"],
            )
            .properties(
                title="Faturamento Líquido por Ano de Implementação",
                width=600,
                height=400,
            )
        )
        st.altair_chart(chart_detalhado, use_container_width=True)

    else:
        st.warning(
            "Não é possível atingir o faturamento objetivo com os parâmetros fornecidos."
        )
        st.info(f"Faturamento máximo possível: $ {info['faturamento_maximo']:,.2f}")

        if info["anos_necessarios"]:
            st.info(
                f"Anos necessários para atingir o objetivo com o número atual de mudas: {info['anos_necessarios']}"
            )
        else:
            st.info(
                "Não é possível atingir o objetivo mesmo em 15 anos com o número atual de mudas."
            )

        st.info(
            f"Número mínimo de mudas iniciais necessárias: {info['mudas_minimas']:,.0f}"
        )

        st.write("Sugestões de ajuste:")
        st.write(
            f"1. Aumente o número inicial de mudas para pelo menos {info['mudas_minimas']:,.0f}."
        )
        if info["anos_necessarios"] and info["anos_necessarios"] <= 15:
            st.write(
                f"2. Aumente o número de anos de projeção para {info['anos_necessarios']}."
            )
        else:
            st.write(
                "2. Não é possível atingir o objetivo apenas aumentando o número de anos."
            )
        st.write("3. Considere reduzir o faturamento objetivo.")

    # Adicione verificações antes de tentar acessar os atributos
    if plano_acao is not None and resultados_detalhados is not None:
        try:
            st.download_button(
                label="Baixar Plano de Ação",
                data=plano_acao.to_csv(index=False).encode("utf-8"),
                file_name="plano_acao.csv",
                mime="text/csv",
            )
            st.download_button(
                label="Baixar Resultados Detalhados",
                data=resultados_detalhados.to_csv(index=False).encode("utf-8"),
                file_name="resultados_detalhados.csv",
                mime="text/csv",
            )

            st.header("Gráfico de Detalhamento do Plano de Ação")
            chart_detalhado = (
                alt.Chart(resultados_detalhados)
                .mark_line()
                .encode(
                    x="Ano",
                    y="Faturamento Líquido (US$)",
                    color="Ano de Implementação:N",
                    tooltip=[
                        "Ano de Implementação",
                        "Ano",
                        "Faturamento Líquido (US$)",
                    ],
                )
                .properties(
                    title="Faturamento Líquido por Ano de Implementação",
                    width=600,
                    height=400,
                )
            )
            st.altair_chart(chart_detalhado, use_container_width=True)
        except Exception as e:
            st.error("Ocorreu um erro ao gerar os downloads ou o gráfico.")
            # Se quiser ver o erro no console para depuração:
            # print(f"Erro: {e}")

st.header("Sobre a Cultura da Baunilheira")
st.write(
    """
- A baunilha fica produtiva durante 15 anos, chegando à máxima produção depois de seis anos.
- Em um sistema de produção semi intensivo, com 4000 mudas por hectare, os seguintes rendimentos podem ser esperados:
  - Ano 3: 500 kilos
  - Ano 4: 1 tonelada
  - Ano 5: 1.6 tonelada
  - Ano 6: 2.5 toneladas
  - Demais anos: Entre 2.5 e 3 toneladas
- A produtividade média sugerida é de 0.5 a 1 kilo por pé de baunilha.
- Para os anos 1 e 2, um modelo linear é usado para estimar a produção, assumindo um crescimento gradual até o ano 3.
- Uma muda na produtividade mais alta (aos 6 anos) produz aproximadamente 30 favas.
- Cada fava verde tem cerca de 20g.
- Cada fava curada tem cerca de 4g.
- No sistema agroflorestal (SAF), cada muda ocupa 4m².
- No sistema semi-intensivo, cada muda ocupa 2.5m².
- Preços de referência (sujeitos a variações de mercado):
  - Fava verde: US$ 15/kg
  - Fava curada: US$ 139.75/kg
  - Extrato 1-fold: 2.25x o preço da fava curada
"""
)
