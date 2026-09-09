import datetime
import math
import urllib.parse
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Perry's Burgers - Control Total Pro",
    page_icon="🍔",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.title("🍔 Perry's Burgers")

# URL del conector de Google Sheets desde Secrets
URL_WEBAPP = st.secrets.get("URL_WEBAPP", "")
TEL_MI_NUMERO = "34643277489"  # Teléfono configurado para lista de compra


# 1. CARGA DE HISTORIAL
@st.cache_data(ttl=5)
def cargar_historial(url):
    if url:
        try:
            res = requests.get(f"{url}?action=read", timeout=5).json()
            if isinstance(res, list) and len(res) > 0:
                return res
        except Exception:
            pass
    return [55, 50, 58]


historial_ventas = cargar_historial(URL_WEBAPP)
base_aprendida = math.ceil(sum(historial_ventas) / len(historial_ventas))
ultimas_ventas = historial_ventas[-1] if historial_ventas else 50


# 2. PRONÓSTICO CLIMÁTICO (MIÉRCOLES A DOMINGO)
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


# 3. DETECTOR DE EVENTOS
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

factor_clima = 1.0 + (dias_lluvia_total * 0.07)
factor_evento = 1.15 if hay_partido_casa else 1.0
burgers_estimadas = math.ceil(base_aprendida * factor_clima * factor_evento)

# METRICAS PRINCIPALES EN CABECERA
col_h1, col_h2, col_h3 = st.columns(3)
with col_h1:
    st.metric("Ventas Última Sem.", f"{ultimas_ventas} uds")
with col_h2:
    st.metric("Promedio Histórico", f"{base_aprendida} uds")
with col_h3:
    st.metric("Estimación Próx.", f"~{burgers_estimadas} uds")

st.divider()

# ==========================================================
# NAVEGACIÓN POR PESTAÑAS DÍA A DÍA
# ==========================================================
tab_martes, tab_miercoles, tab_domingo = st.tabs(
    ["🛒 Martes (Pedidos)", "👨‍🍳 Miércoles (Cocina)", "📋 Domingo (Cierre)"]
)

# ----------------------------------------------------------
# PESTAÑA 1: MARTES (GESTIÓN Y PEDIDOS)
# ----------------------------------------------------------
with tab_martes:
    st.subheader("🗓️ Gestión de Pedidos del Martes")

    st.markdown("**🌤️ Tiempo en Vitoria (Mié - Dom)**")
    if pronostico_diario:
        cols = st.columns(5)
        for idx, d in enumerate(pronostico_diario):
            with cols[idx]:
                emoji = "🌧️" if d["llueve"] else "☀️"
                st.caption(f"**{d['dia']}**")
                st.write(f"{emoji} {d['temp']}")

    if hay_partido_casa:
        st.info(f"📌 **{detalle_evento}**")
    else:
        st.success("✅ Sin partidos locales multitudinarios esta semana.")

    st.markdown("---")
    st.markdown("### 🍞🥩 Pedidos Principales")

    col_pan, col_carne, col_patatas = st.columns(3)
    with col_pan:
        pan_sobrante_martes = st.number_input(
            "🍞 Panes sobrantes (domingo):", min_value=0, value=15, step=1
        )
    with col_carne:
        carne_sobrante_martes = st.number_input(
            "🥩 Kg carne sobrantes:", min_value=0.0, value=0.0, step=0.5
        )
    with col_patatas:
        patatas_sobrantes_martes = st.number_input(
            "🍟 Kg patatas sobrantes:", min_value=0.0, value=2.0, step=0.5
        )

    panes_necesarios = max(0, burgers_estimadas - pan_sobrante_martes)
    cajas_pan_pedir = math.ceil(panes_necesarios / 18)

    kg_vacuno_total = (burgers_estimadas * 0.8) * 0.180
    kg_vacuno_pedir = max(0.0, kg_vacuno_total - carne_sobrante_martes)

    kg_patatas_total = (burgers_estimadas * 0.5) * 0.150
    cajas_patatas_pedir = math.ceil(
        max(0.0, kg_patatas_total - patatas_sobrantes_martes) / 12.5
    )

    kg_por_entrega = kg_vacuno_pedir / 2
    pecho_kg = round(kg_por_entrega * 0.35)
    aguja_kg = round(kg_por_entrega * 0.65)
    if (pecho_kg + aguja_kg) != round(kg_por_entrega) and kg_por_entrega > 0:
        aguja_kg = max(0, round(kg_por_entrega) - pecho_kg)

    TEL_BEDARONA = "34656783379"
    TEL_XURBANO = "34657798229"

    msg_bedarona = f"Buenas, para esta semana necesito:\n- {cajas_pan_pedir} cajas de pan\n- {cajas_patatas_pedir} cajas de patatas"
    msg_carne = f"Buenas, para esta semana necesito:\n- Miércoles: {pecho_kg} kg de pecho y {aguja_kg} kg de aguja de vaca\n- Viernes: {pecho_kg} kg de pecho y {aguja_kg} kg de aguja de vaca"

    url_bedarona = (
        f"https://wa.me/{TEL_BEDARONA}?text={urllib.parse.quote(msg_bedarona)}"
    )
    url_carne = (
        f"https://wa.me/{TEL_XURBANO}?text={urllib.parse.quote(msg_carne)}"
    )

    st.markdown("#### 📲 Enviar Pedidos Directos")
    col_b1, col_b2 = st.columns([3, 2])
    with col_b1:
        st.info(
            f"🍞🍟 **Manuel:** {cajas_pan_pedir} cajas pan | {cajas_patatas_pedir} cajas patatas"
        )
    with col_b2:
        st.link_button("📲 Pedir a Manuel", url_bedarona)

    col_x1, col_x2 = st.columns([3, 2])
    with col_x1:
        st.info(
            f"🥩 **Xurbano:** {pecho_kg} kg Pecho + {aguja_kg} kg Aguja (Mié y Vie)"
        )
    with col_x2:
        st.link_button("📲 Pedir a Xurbano", url_carne)


# ----------------------------------------------------------
# PESTAÑA 2: MIÉRCOLES (PREPARACIÓN EN COCINA)
# ----------------------------------------------------------
with tab_miercoles:
    st.subheader("👨‍🍳 Tanda de Producción de Salsas")
    st.caption(
        "Escandallos integrados: Sweet (Sweet & Classic @ 20g/ud), Lima (Chicken @ 30g/ud), Trufa (Trufada)."
    )

    salsas_nombres = ["Sweet", "Trufa", "Lima", "BBQ", "Cheddar", "Mex"]
    salsas_hechas = {}
    salsas_sobrantes = {}

    with st.expander("📝 Editar datos de la semana anterior (Mermas)"):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("**Gramos Elaborados:**")
            for s in salsas_nombres:
                salsas_hechas[s] = st.number_input(
                    f"{s} hechos (g):",
                    min_value=0,
                    value=1000,
                    step=100,
                    key=f"h_{s}",
                )
        with col_s2:
            st.markdown("**Gramos Tirados (Merma):**")
            for s in salsas_nombres:
                salsas_sobrantes[s] = st.number_input(
                    f"{s} tirados (g):",
                    min_value=0,
                    value=150,
                    step=50,
                    key=f"s_{s}",
                )

    ratio_ventas = (
        (burgers_estimadas / ultimas_ventas) if ultimas_ventas > 0 else 1.0
    )

    st.markdown("### 🥣 Cantidad Exacta a Elaborar Hoy:")

    total_merma_g = 0
    for s in salsas_nombres:
        consumo_real = max(0, salsas_hechas[s] - salsas_sobrantes[s])
        gramos_recomendados = (
            math.ceil((consumo_real * ratio_ventas) / 50) * 50
        )
        if gramos_recomendados < 200 and consumo_real > 0:
            gramos_recomendados = 200

        total_merma_g += salsas_sobrantes[s]

        nota_escandallo = ""
        if s == "Sweet":
            nota_escandallo = " (Chesse/Classic + Sweet & Cryspy)"
        elif s == "Lima":
            nota_escandallo = " (Lima Cryspy Chicken @ 30g)"

        st.success(
            f"👉 **Salsa {s}{nota_escandallo}:** Preparar **{gramos_recomendados} g**"
        )

    coste_estimado_merma = round(total_merma_g * 0.012, 2)
    st.warning(
        f"🗑️ **Mermas del domingo:** Tiraste {total_merma_g}g de salsa en total (~{coste_estimado_merma}€ perdidos)."
    )


# ----------------------------------------------------------
# PESTAÑA 3: DOMINGO (INVENTARIO DE ALMACÉN Y CIERRE)
# ----------------------------------------------------------
with tab_domingo:
    st.subheader("📋 Recuento de Almacén (Domingo Noche)")

    items_stock = {
        "Papel de cera": {"min": 100, "unidad": "uds", "val": 120},
        "Cajas de burgers": {"min": 100, "unidad": "uds", "val": 150},
        "Servilletas": {"min": 100, "unidad": "uds", "val": 110},
        "Petacas de papas": {"min": 100, "unidad": "uds", "val": 90},
        "Queso cheddar": {"min": 3, "unidad": "paquetes (1kg)", "val": 4},
        "Queso gouda": {"min": 2, "unidad": "paquetes", "val": 2},
        "Jalapeño": {"min": 1, "unidad": "bote", "val": 1},
        "Chili chipotle": {"min": 1, "unidad": "bote", "val": 2},
        "Cebolla": {"min": 1.0, "unidad": "kg", "val": 1.5},
        "Rúcula": {"min": 300, "unidad": "g", "val": 200},
        "Cajas para pollo": {"min": 15, "unidad": "uds", "val": 10},
        "Salseras": {"min": 50, "unidad": "uds", "val": 60},
        "Aceite": {"min": 10.0, "unidad": "litros", "val": 8.0},
        "Aceite de trufa": {"min": 1, "unidad": "uds", "val": 1},
        "Trufa": {"min": 70, "unidad": "g", "val": 100},
        "Cilantro": {"min": 200, "unidad": "g", "val": 150},
        "Lima": {"min": 4, "unidad": "limas", "val": 6},
        "Tomate": {"min": 1, "unidad": "tomate", "val": 2},
        "Tiras de bacon": {"min": 1, "unidad": "paquete", "val": 0},
        "Bites de bacon": {"min": 1, "unidad": "paquete", "val": 1},
        "Pollo": {"min": 1.0, "unidad": "kg", "val": 1.5},
        "Corn flakes": {"min": 1.0, "unidad": "kg", "val": 0.5},
        "Harina": {"min": 300, "unidad": "g", "val": 500},
        "Huevo": {"min": 12, "unidad": "huevos", "val": 15},
        "Nata para cocinar": {"min": 500, "unidad": "g", "val": 300},
        "Nata para montar": {"min": 500, "unidad": "g", "val": 600},
        "Crema de pistacho": {"min": 300, "unidad": "g", "val": 200},
        "Azúcar": {"min": 200, "unidad": "g", "val": 300},
        "Queso crema": {"min": 500, "unidad": "g", "val": 400},
        "Coca Cola original": {"min": 15, "unidad": "latas", "val": 12},
        "Coca Cola zero": {"min": 15, "unidad": "latas", "val": 20},
        "Agua": {"min": 10, "unidad": "botellas", "val": 15},
        "Estrella (lata)": {"min": 10, "unidad": "latas", "val": 5},
    }

    def get_step(unidad):
        if unidad == "kg":
            return 0.5
        elif unidad == "g":
            return 10.0
        return 1.0

    stock_actual = {}
    col_st1, col_st2 = st.columns(2)
    items_keys = list(items_stock.keys())
    mitad = math.ceil(len(items_keys) / 2)

    with col_st1:
        for item in items_keys[:mitad]:
            conf = items_stock[item]
            stock_actual[item] = st.number_input(
                f"Queda {item} ({conf['unidad']}):",
                min_value=0.0,
                value=float(conf["val"]),
                step=get_step(conf["unidad"]),
                key=f"st_{item}",
            )

    with col_st2:
        for item in items_keys[mitad:]:
            conf = items_stock[item]
            stock_actual[item] = st.number_input(
                f"Queda {item} ({conf['unidad']}):",
                min_value=0.0,
                value=float(conf["val"]),
                step=get_step(conf["unidad"]),
                key=f"st_{item}",
            )

    st.markdown("---")
    st.markdown("### 🛒 Lista de Compra Necesaria")

    lista_compra_txt = "🛒 *LISTA DE COMPRA PERRY'S BURGERS*\n\n"
    hay_compras = False

    for item, conf in items_stock.items():
        sobra = stock_actual[item]
        minimo = conf["min"]
        if sobra < minimo:
            faltante = minimo - sobra
            hay_compras = True
            st.warning(
                f"⚠️ **{item}:** Quedan {sobra} {conf['unidad']}. Comprar **{faltante} {conf['unidad']}**."
            )
            lista_compra_txt += f"• {item}: comprar {faltante} {conf['unidad']}\n"

    if not hay_compras:
        st.success("✅ Todo el stock de almacén supera los mínimos.")
        lista_compra_txt += "Todo en orden. No hace falta comprar nada."

    # Enviar directo a +34 643 27 74 89
    url_lista_wa = (
        f"https://wa.me/{TEL_MI_NUMERO}?text={urllib.parse.quote(lista_compra_txt)}"
    )
    st.link_button(
        "📲 Enviar Lista de Compra por WhatsApp (+34 643 27 74 89)", url_lista_wa
    )

    st.markdown("---")
    st.markdown("### 🤖 Cierre de Semana y Envío a Sheets")

    panes_totales_disponibles = pan_sobrante_martes + (cajas_pan_pedir * 18)
    pan_sobrante_domingo = st.number_input(
        "🍞 Panes sueltos que quedan el DOMINGO AL CERRAR:",
        min_value=0,
        value=5,
        step=1,
    )

    confirmar = st.checkbox("✔ Confirmar que quiero registrar el cierre hoy")

    if st.button("Guardar Cierre en Google Sheets", disabled=not confirmar):
        ventas_calculadas = panes_totales_disponibles - pan_sobrante_domingo
        if ventas_calculadas >= 0:
            fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
            if URL_WEBAPP:
                try:
                    r = requests.get(
                        URL_WEBAPP,
                        params={
                            "fecha": fecha_hoy,
                            "ventas": ventas_calculadas,
                        },
                        timeout=10,
                    )
                    if "OK" in r.text:
                        st.success(
                            f"🎯 **¡Guardado con éxito!** Registradas ~{ventas_calculadas} burgers vendidas."
                        )
                        st.cache_data.clear()
                    else:
                        st.error("Error al escribir en la hoja de Google.")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")
            else:
                st.error("Falta la URL_WEBAPP en Secrets.")
        else:
            st.error(
                "El sobrante del domingo no puede superar los panes disponibles."
            )
