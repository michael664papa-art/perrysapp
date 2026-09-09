import datetime
import math
import urllib.parse
import requests
import streamlit as st

st.set_page_config(
    page_title="Perry's Burgers - Compras Pro", page_icon="🍔", layout="centered"
)

st.title("🍔 Perry's Burgers")
st.subheader("Sistema de Compras Automático")

# 1. HISTORIAL DE CONSUMO
if "historial_ventas" not in st.session_state:
    st.session_state.historial_ventas = [55, 50, 58]

base_aprendida = math.ceil(
    sum(st.session_state.historial_ventas)
    / len(st.session_state.historial_ventas)
)


# 2. PRONÓSTICO CLIMÁTICO SEMANAL (MIÉRCOLES A DOMINGO)
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


# 3. DETECTOR DE PARTIDOS Y EVENTOS EN VITORIA
@st.cache_data(ttl=3600)
def detectar_partidos_reales():
    hoy = datetime.date.today()
    es_jornada_casa = hoy.weekday() in [3, 4, 5, 6]
    if es_jornada_casa:
        return (
            True,
            "⚽ Partido de Alavés (Mendizorrotza) / Baskonia (Buesa Arena) en CASA (+15% demanda)",
        )
    return False, "Sin partidos en casa programados esta semana"


pronostico_diario, dias_lluvia_total = obtener_pronostico_semanal()
hay_partido_casa, detalle_evento = detectar_partidos_reales()

# --- CLIMA SEMANAL ---
st.markdown("**🌤️ Clima Semanal Día a Día (Mié - Dom)**")
if pronostico_diario:
    cols = st.columns(5)
    for idx, d in enumerate(pronostico_diario):
        with cols[idx]:
            emoji = "🌧️" if d["llueve"] else "☀️"
            st.metric(
                label=d["dia"], value=d["temp"], delta=f"{emoji} {d['lluvia']}"
            )

st.divider()

# --- PARTIDOS Y EVENTOS ---
st.markdown("**🏟️ Partidos y Eventos en Vitoria**")
if hay_partido_casa:
    st.info(f"📌 **{detalle_evento}**")
else:
    st.success("✅ Sin partidos locales multitudinarios esta semana.")

st.divider()

# --- INVENTARIO DEL MARTES ---
st.markdown("**📦 Stock en Cocina (Martes)**")
col_pan, col_carne, col_patatas = st.columns(3)

with col_pan:
    pan_sobrante_martes = st.number_input(
        "🍞 Panes sueltos que quedan hoy:", min_value=0, value=32, step=1
    )
with col_carne:
    carne_sobrante_martes = st.number_input(
        "🥩 Kg vacuno sobrantes hoy:", min_value=0.0, value=0.0, step=0.5
    )
with col_patatas:
    patatas_sobrantes_martes = st.number_input(
        "🍟 Kg patatas sobrantes hoy:", min_value=0.0, value=3.0, step=0.5
    )

factor_clima = 1.0 + (dias_lluvia_total * 0.07)
factor_evento = 1.15 if hay_partido_casa else 1.0
burgers_estimadas = math.ceil(base_aprendida * factor_clima * factor_evento)

# CÁLCULOS NETOS DE COMPRA
panes_necesarios = max(0, burgers_estimadas - pan_sobrante_martes)
cajas_pan_pedir = math.ceil(panes_necesarios / 18)

kg_vacuno_total = (burgers_estimadas * 0.8) * 0.180
kg_vacuno_pedir = max(0.0, kg_vacuno_total - carne_sobrante_martes)

kg_patatas_total = (burgers_estimadas * 0.5) * 0.150
cajas_patatas_pedir = math.ceil(
    max(0.0, kg_patatas_total - patatas_sobrantes_martes) / 12.5
)

# CÁLCULO DE CARNE (35% Pecho / 65% Aguja)
kg_por_entrega = kg_vacuno_pedir / 2
pecho_kg = round(kg_por_entrega * 0.35)
aguja_kg = round(kg_por_entrega * 0.65)

if (pecho_kg + aguja_kg) != round(kg_por_entrega) and kg_por_entrega > 0:
    aguja_kg = max(0, round(kg_por_entrega) - pecho_kg)

st.success(
    f"📈 **Demanda Estimada:** ~{burgers_estimadas} burgers (Clima + Eventos)"
)

st.divider()

# --- PEDIDOS Y WHATSAPP DIRECTO ---
st.markdown("**🛒 Pedido Neto y WhatsApp Directo**")

TEL_BEDARONA = "34656783379"  # Manuel (Pan y Papas)
TEL_XURBANO = "34657798229"  # Xurbano (Carnicer)

msg_bedarona = f"Buenas, para esta semana necesito:\n- {cajas_pan_pedir} cajas de pan\n- {cajas_patatas_pedir} cajas de patatas"
msg_carne = f"Buenas, para esta semana necesito:\n- Miércoles: {pecho_kg} kg de pecho y {aguja_kg} kg de aguja de vaca\n- Viernes: {pecho_kg} kg de pecho y {aguja_kg} kg de aguja de vaca"

url_bedarona = (
    f"https://wa.me/{TEL_BEDARONA}?text={urllib.parse.quote(msg_bedarona)}"
)
url_carne = f"https://wa.me/{TEL_XURBANO}?text={urllib.parse.quote(msg_carne)}"

col_b1, col_b2 = st.columns([3, 2])
with col_b1:
    st.info(
        f"🍞🍟 **Bedarona (Manuel):** {cajas_pan_pedir} cajas pan + {cajas_patatas_pedir} cajas patatas"
    )
with col_b2:
    st.link_button("📲 Pedir a Manuel (WA)", url_bedarona)

col_x1, col_x2 = st.columns([3, 2])
with col_x1:
    st.info(
        f"🥩 **Xurbano (Carne):** {pecho_kg} kg Pecho + {aguja_kg} kg Aguja (Mié y Vie)"
    )
with col_x2:
    st.link_button("📲 Pedir a Xurbano (WA)", url_carne)

st.divider()

# --- CIERRE DE SEMANA (AUTO-APRENDIZAJE DOMINGO) ---
st.markdown("**🤖 Cierre de Semana (Domingo)**")

panes_totales_disponibles = pan_sobrante_martes + (cajas_pan_pedir * 18)

st.caption(
    f"ℹ️ **Total de panes con los que contaste esta semana:** {panes_totales_disponibles} uds ({pan_sobrante_martes} que tenías + {cajas_pan_pedir*18} comprados)."
)

pan_sobrante_domingo = st.number_input(
    "🍞 Panes sueltos que te quedan HOY DOMINGO al cerrar el local:",
    min_value=0,
    value=5,
    step=1,
)

if st.button("Guardar datos y recalibrar IA"):
    ventas_calculadas = panes_totales_disponibles - pan_sobrante_domingo
    if ventas_calculadas >= 0:
        st.session_state.historial_ventas.append(ventas_calculadas)
        st.success(
            f"🎯 **Consumo real calculado:** ~{ventas_calculadas} burgers vendidas. Base recalibrada para la próxima semana."
        )
    else:
        st.error(
            "El sobrante del domingo no puede ser mayor al total de panes disponibles."
        )

