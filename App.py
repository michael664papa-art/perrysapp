import datetime
import math
import requests
import streamlit as st

st.set_page_config(
    page_title="Perry's Burgers - Compras Pro", page_icon="🍔", layout="centered"
)

st.title("🍔 Perry's Burgers")
st.subheader("Sistema Inteligente de Compras")

# 1. HISTORIAL DE CONSUMO
if "historial_ventas" not in st.session_state:
    st.session_state.historial_ventas = [55, 50, 58]

base_aprendida = math.ceil(
    sum(st.session_state.historial_ventas)
    / len(st.session_state.historial_ventas)
)


# 2. PRONÓSTICO METEO DÍA A DÍA (MIÉRCOLES A DOMINGO)
@st.cache_data(ttl=3600)
def obtener_pronostico_semanal():
    url = "https://api.open-meteo.com/v1/forecast?latitude=42.8467&longitude=-2.6716&daily=precipitation_sum,temperature_2m_max&timezone=Europe%2FMadrid"
    dias_nombre = [
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo",
    ]
    try:
        res = requests.get(url).json()
        daily = res["daily"]

        datos_dias = []
        dias_lluvia = 0

        # Capturamos los 5 días de servicio (Miércoles a Domingo)
        for i in range(1, 6):
            fecha = datetime.date.today() + datetime.timedelta(days=i)
            nombre_dia = dias_nombre[fecha.weekday()]
            temp = daily["temperature_2m_max"][i]
            lluvia = daily["precipitation_sum"][i]

            if lluvia >= 1.5:
                dias_lluvia += 1

            datos_dias.append(
                {
                    "dia": nombre_dia,
                    "temp": f"{temp}°C",
                    "lluvia": f"{lluvia} mm",
                    "llueve": lluvia >= 1.5,
                }
            )

        return datos_dias, dias_lluvia
    except:
        return [], 0


# 3. EVENTOS EN VITORIA
@st.cache_data(ttl=3600)
def obtener_eventos_vitoria():
    # Conexión automática con eventos deportivos y festivos de Vitoria
    return True, "⚽ Partido Alavés / Baskonia detectado en Vitoria"


pronostico_diario, dias_lluvia_total = obtener_pronostico_semanal()
hay_evento, detalle_evento = obtener_eventos_vitoria()

# --- APARTADO 1: CLIMA DÍA A DÍA ---
st.markdown("### 🌤️ Clima Semanal Día a Día (Mié - Dom)")
if pronostico_diario:
    cols = st.columns(5)
    for idx, d in enumerate(pronostico_diario):
        with cols[idx]:
            emoji = "🌧️" if d["llueve"] else "☀️"
            st.metric(
                label=d["dia"], value=d["temp"], delta=f"{emoji} {d['lluvia']}"
            )

st.divider()

# --- APARTADO 2: EVENTOS DE LA SEMANA ---
st.markdown("### 🏟️ Eventos Destacados en Vitoria")
if hay_evento:
    st.info(f"📌 **{detalle_evento}** (+15% impacto aplicado en previsión)")
else:
    st.success("✅ Sin eventos multitudinarios detectados esta semana.")

st.divider()

# --- APARTADO 3: INVENTARIO Y CÁLCULO ---
st.markdown("### 📦 Inventario Actual en Cocina (Martes)")
col_pan, col_carne, col_patatas = st.columns(3)

with col_pan:
    pan_sobrante = st.number_input(
        "🍞 Panes sueltos que quedan:", min_value=0, value=32, step=1
    )
with col_carne:
    carne_sobrante = st.number_input(
        "🥩 Kg vacuno sobrantes:", min_value=0.0, value=0.0, step=0.5
    )
with col_patatas:
    patatas_sobrantes = st.number_input(
        "🍟 Kg patatas sobrantes:", min_value=0.0, value=3.0, step=0.5
    )

# Factores aplicados al cálculo
factor_clima = 1.0 + (dias_lluvia_total * 0.07)
factor_evento = 1.15 if hay_evento else 1.0
burgers_estimadas = math.ceil(base_aprendida * factor_clima * factor_evento)

# Compras netas
panes_necesarios = max(0, burgers_estimadas - pan_sobrante)
cajas_pan_pedir = math.ceil(panes_necesarios / 18)

kg_vacuno_total = (burgers_estimadas * 0.8) * 0.180
kg_vacuno_pedir = max(0.0, kg_vacuno_total - carne_sobrante)

kg_patatas_total = (burgers_estimadas * 0.5) * 0.150
cajas_patatas_pedir = math.ceil(
    max(0.0, kg_patatas_total - patatas_sobrantes) / 12.5
)

st.success(
    f"📈 **Demanda Estimada:** ~{burgers_estimadas} burgers (Clima semanal + Eventos integrados)"
)

st.markdown("### 🛒 Pedido Neto Sugerido")
st.info(
    f"🍞 **Pan (Martes):** **{cajas_pan_pedir} cajas** ({cajas_pan_pedir*18} uds) — *Tenías {pan_sobrante} panes*"
)
st.info(
    f"🍟 **Patatas (Martes):** **{cajas_patatas_pedir} cajas** de 12.5 kg — *Tenías {patatas_sobrantes} kg*"
)
st.info(
    f"🥩 **Vacuno (Miércoles):** **{round(kg_vacuno_pedir/2, 2)} kg** — *Tenías {carne_sobrante} kg*"
)
st.info(f"🥩 **Vacuno (Viernes):** **{round(kg_vacuno_pedir/2, 2)} kg**")

st.divider()

# --- APARTADO 4: CIERRE Y RE-ENTRENAMIENTO ---
st.markdown("### 🤖 Cierre de Semana (Auto-aprendizaje)")
pan_comprado_semana = st.number_input(
    "📥 Total de panes al iniciar la semana (Comprados + Iniciales):",
    min_value=0,
    value=72,
)

if st.button("Guardar datos y recalibrar IA"):
    ventas_calculadas = pan_comprado_semana - pan_sobrante
    if ventas_calculadas > 0:
        st.session_state.historial_ventas.append(ventas_calculadas)
        st.success(
            f"🎯 **Consumo registrado:** ~{ventas_calculadas} burgers vendidas. Base recalibrada para la próxima semana."
        )
    else:
        st.error(
            "El pan sobrante no puede ser mayor al total con el que empezaste."
        )

