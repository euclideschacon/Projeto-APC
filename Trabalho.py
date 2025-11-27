import streamlit as st

# ============================================================
# Funções de cálculo
# ============================================================

def calcular_tdp_total(gpu_data, gpus):
    """Calcula o TDP total das GPUs selecionadas (em Watts)."""
    return sum(gpus[g["modelo"]]["tdp"] * g["quantidade"] for g in gpu_data)


def calcular_custo_gpus(gpu_data):
    """Calcula o custo total de aquisição das GPUs."""
    return sum(g["quantidade"] * g["preco_unitario"] for g in gpu_data)


def calcular_consumo_total_servidor(tdp_total):
    """Estima o TDP total do servidor considerando que as GPUs representam 40% do consumo."""
    return tdp_total * 2.5


def calcular_custo_energia_mensal(tdp_total_servidor, tarifa_kwh, horas_mensais=24*30):
    """Calcula o custo mensal de energia em reais."""
    consumo_kwh_mensal = (tdp_total_servidor * horas_mensais) / 1000
    custo_mensal = consumo_kwh_mensal * tarifa_kwh
    return consumo_kwh_mensal, custo_mensal


def calcular_custo_concorrente(preco_gpu_usd, cotacao_dolar):
    """Calcula o custo mensal do concorrente (AWS, Azure, GCP) em reais."""
    preco_gpu_brl = preco_gpu_usd * cotacao_dolar
    custo_mensal = preco_gpu_brl * 24 * 30
    return custo_mensal


def calcular_receita_mensal(custo_concorrente_mensal_total, desconto, assinantes):
    """Calcula a receita mensal com desconto aplicado e número de assinantes."""
    return (custo_concorrente_mensal_total * (1 - desconto / 100)) * assinantes


def calcular_break_even(custo_energia_mensal, receita_mensal, investimento_total):
    """Calcula o tempo de break-even (meses e horas)."""
    if receita_mensal > custo_energia_mensal:
        meses = investimento_total / (receita_mensal - custo_energia_mensal)
        horas = meses * 30 * 24
    else:
        meses, horas = float("inf"), float("inf")
    return meses, horas


# ============================================================
# Interface Streamlit
# ============================================================

st.sidebar.title("Informações do Projeto")
st.sidebar.markdown("""
**Disciplina:** CIC 0004 - Algoritmos e Programação de Computadores – Turma 06 – 2025/2
**Professor:** Edison Ishikawa  

### PROJETO SUSTENTABILIDADE E COMPUTAÇÃO
**Título:** Sustentabilidade Energética em Data Centers no Brasil:
Uma Análise da Viabilidade Financeira da Compensação por Energia Solar Fotovoltaica.

**Integrantes:**
- Ana Beatriz de Sousa Ciro
- Davi Carneiro Da Costa
- José Euclides Chacon Neto
- Julia Letícia Candido Luz
""")

st.title("💡 Simulador de Sustentabilidade Energética em Data Centers")

# --------------------------------
# Seção: GPUs e consumo energético
# --------------------------------
st.header("⚙️ Seleção de GPUs")


# Informações de TDP foram retiradas do site https://www.nvidia.com
gpus = {
    "NVIDIA T4": {"tdp": 70, "preco": 15000},
    "NVIDIA A100": {"tdp": 400, "preco": 120000},
    "NVIDIA H100": {"tdp": 700, "preco": 200000},
    "NVIDIA RTX 4090": {"tdp": 450, "preco": 12000},
    "NVIDIA L40S": {"tdp": 350, "preco": 80000},
}

gpu_data = []
add_gpu = True
while add_gpu:
    col1, col2, col3 = st.columns(3)
    with col1:
        modelo = st.selectbox("Modelo de GPU", list(gpus.keys()), key=f"modelo_{len(gpu_data)}")
    with col2:
        qtd = st.number_input("Quantidade", min_value=1, value=1, key=f"qtd_{len(gpu_data)}")
    with col3:
        preco_unitario = st.number_input(
            "Preço unitário (R$)",
            min_value=1000.0,
            value=float(gpus[modelo]["preco"]),
            step=1000.0,
            key=f"preco_{len(gpu_data)}"
        )
    gpu_data.append({"modelo": modelo, "quantidade": qtd, "preco_unitario": preco_unitario})
    add_gpu = st.checkbox("Adicionar outra GPU?", key=f"add_{len(gpu_data)}")
    if not add_gpu:
        break

# --------------------------------
# Bandeira tarifária
# --------------------------------
# O preço da bandeira verde foi extraído do site da Neonergia (https://www.neoenergia.com/web/brasilia/sua-casa/composicao-tarifaria).
# O incremento de valor para as demais bandeiras foi extrído do site da ANEEL (https://www.gov.br/aneel/pt-br/assuntos/tarifas/bandeiras-tarifarias)
st.header("⚡ Bandeira Tarifária (ANEEL)")
bandeiras = {
    "🟩 Verde": 0.82672,
    "🟨 Amarela": 0.82672 + 0.01885,
    "🟥 Vermelha 1": 0.82672 + 0.04463,
    "🟥 Vermelha 2": 0.82672 + 0.07877,
}
bandeira = st.radio("Selecione a bandeira:", list(bandeiras.keys()))
tarifa_kwh = bandeiras[bandeira]

# --------------------------------
# Cotação do dólar
# --------------------------------
st.header("💲 Cotação do Dólar")
cotacao_dolar = st.number_input("Informe a cotação atual do dólar (R$):", min_value=0.01, max_value=100.0, value=5.5)

# --------------------------------
# Concorrentes
# --------------------------------
st.header("☁️ Comparação com Nuvens")

# Fontes de referência para preços (novembro/2025):
# AWS: https://aws.amazon.com/ec2/pricing/on-demand/
# Azure: https://azure.microsoft.com/en-us/pricing/details/virtual-machines/linux/
# GCP: https://cloud.google.com/compute/vm-instance-pricing?hl=en#accelerator-optimized-machine-type-family

concorrentes = {
    "AWS (p4d.24xlarge)": {"preco_usd_h": 21.96},
    "AWS (p5.48xlarge)": {"preco_usd_h": 55.04},
    "AWS (p6-b200.48xlarge)": {"preco_usd_h": 113.93},
    "Azure (ND40rs)": {"preco_usd_h": 22.03},
    "Azure (ND96asr)": {"preco_usd_h": 27.20},
    "Azure (ND96isr)": {"preco_usd_h": 98.32},
    "GCP (a2-highgpu-8g)": {"preco_usd_h": 29.39},
    "GCP (a2-ultragpu-8g)": {"preco_usd_h": 40.55},
    "GCP (a4-highgpu-8g)": {"preco_usd_h": 88.93},
}

concorrente = st.selectbox(
    "Selecione o concorrente:",
    [f"{nome} – USD{dados['preco_usd_h']}/h" for nome, dados in concorrentes.items()]
)
concorrente_nome = concorrente.split(" – USD")[0]
preco_gpu_usd = concorrentes[concorrente_nome]["preco_usd_h"]

# Desconto e assinantes
col1, col2 = st.columns(2)
with col1:
    desconto = st.slider("Desconto oferecido (%)", 0, 100, 25)
with col2:
    assinantes = st.number_input("Quantidade de assinantes previstos:", min_value=1, value=1)

# --------------------------------
# Cálculos usando as funções
# --------------------------------
tdp_total = calcular_tdp_total(gpu_data, gpus)
custo_gpus = calcular_custo_gpus(gpu_data)
tdp_total_servidor = calcular_consumo_total_servidor(tdp_total)
consumo_kwh_mensal, custo_energia_mensal = calcular_custo_energia_mensal(tdp_total_servidor, tarifa_kwh)
custo_concorrente_mensal_total = calcular_custo_concorrente(preco_gpu_usd, cotacao_dolar)
receita_mensal = calcular_receita_mensal(custo_concorrente_mensal_total, desconto, assinantes)


# Custo de implementação de energia solar, conforme:
# https://www.portalsolar.com.br/noticias/tecnologia/armazenamento/quanto-custa-um-sistema-residencial-de-baterias-no-brasil 
custo_solar_implementacao = 31050.0


investimento_total = custo_solar_implementacao + custo_gpus

meses_break_even, horas_break_even = calcular_break_even(custo_energia_mensal, receita_mensal, investimento_total)

# --------------------------------
# Resultados
# --------------------------------
st.header("📊 Resultados da Simulação")

# TDP significa Thermal Design Power que é a Potência Máxima na qual a GPU foi projetada
st.write(f"**TDP total das GPUs:** {tdp_total} W")
st.write(f"**Potência total do servidor (estimado):** {tdp_total_servidor:.0f} W")
st.write(f"**Consumo mensal de energia:** {consumo_kwh_mensal:.2f} kWh")
st.write(f"**Custo mensal de energia (bandeira {bandeira}):** R$ {custo_energia_mensal:,.2f}")
st.write(f"**Custo mensal cobrado por {concorrente_nome}:** R$ {custo_concorrente_mensal_total:,.2f}")
st.write(f"**Receita mensal estimada (com {assinantes} assinantes e {desconto}% de desconto):** R$ {receita_mensal:,.2f}")
st.write(f"**Custo de implementação solar:** R$ {custo_solar_implementacao:,.2f}")
st.write(f"**Custo total de aquisição das GPUs:** R$ {custo_gpus:,.2f}")
st.write(f"**Investimento total:** R$ {investimento_total:,.2f}")

if meses_break_even != float("inf"):
    st.success(f"💰 Lucro estimado a partir de **{meses_break_even:.1f} meses** ou **{horas_break_even:,.0f} horas**.")
else:
    st.error("🚫 Receita insuficiente para atingir o break-even.")

