import datetime
import math
import requests
import streamlit as st

st.set_page_config(
    page_title="Perry's Burgers - Compras", page_icon="🍔", layout="centered"
)

st.title("🍔 Perry's Burgers")
st.subheader("Sistema Inteligente de Previsión de Compras")


@st.cache_data(ttl=3600)
def obtener_clima_vitoria():
    url = "https://api.open-meteo.com/v1/forecast?latitude=42.8467&longitude=-2.6716&daily=precipitation_sum,temperature_2m_max&timezone=Europe%2FMadrid"
    try:
        res = requests.get(url).json()
        lluvia_hoy = res["daily"]["precipitation_sum"][0] > 2.0
        temp_max = res["daily"]["temperature_2m_max"][0]
        return lluvia_hoy, temp_max
    except:
        return False, 20.0


hay_lluvia, temp_max = obtener_clima_vitoria()

col1, col2 = st.columns(2)
with col1:
    st.metric("🌡️ Temp. Máxima Vitoria", f"{temp_max} °C")
with col2:
    st.metric("🌧️ Lluvia Detectada", "Sí" if hay_lluvia else "No")

st.divider()

st.markdown("**Ajustes de la Semana**")
partido_hoy = st.checkbox("⚽ ¿Hay partido del Alavés / Baskonia?")
stock_patatas = st.number_input(
    "🍟 Kg de patatas sobrantes en almacén:", value=2.0, step=0.5
)

factor_clima = 1.20 if hay_lluvia else 1.0
factor_partido = 1.15 if partido_hoy else 1.0
multiplicador = factor_clima * factor_partido

base_burgers = 55
burgers_estimadas = math.ceil(base_burgers * multiplicador)

cajas_pan = math.ceil(burgers_estimadas / 18)
kg_carne_vacuno = round((burgers_estimadas * 0.8) * 0.180, 2)
kg_patatas_necesarios = math.ceil((burgers_estimadas * 0.5) * 0.150)
cajas_patatas = math.ceil(
    max(0, kg_patatas_necesarios - stock_patatas) / 12.5
)

st.success(f"📈 **Previsión de demanda:** ~{burgers_estimadas} burgers")

st.markdown("### 🛒 Pedidos Sugeridos")
st.info(
    f"🍞 **Pan (Martes):** **{cajas_pan} cajas** de 18 uds ({cajas_pan*18} unidades totales)"
)
st.info(
    f"🍟 **Patatas (Martes):** **{cajas_patatas} cajas** de 12.5 kg (Makro)"
)
st.info(
    f"🥩 **Vacuno (Miércoles):** **{round(kg_carne_vacuno / 2, 2)} kg**"
)
st.info(f"🥩 **Vacuno (Viernes):** **{round(kg_carne_vacuno / 2, 2)} kg**")
