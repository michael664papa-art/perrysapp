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

# URL del conector de Google Sheets y Secrets
URL_WEBAPP = st.secrets.get("URL_WEBAPP", "")
SUMUP_API_KEY = st.secrets.get("SUMUP_API_KEY", "")
TEL_MI_NUMERO = "34643277489"

# Nombres de salsas
salsas_nombres = ["Sweet", "Trufa", "Lima", "BBQ", "Cheddar", "Mex"]

# Inicializar estados de producción y mermas en sesión si no existen
if "salsas_hechas" not in st.session_state:
    st.session_state.salsas_hechas = {s: 850 for s in salsas_nombres}

if "salsas_sobrantes" not in st.session_state:
    st.session_state.salsas_sobrantes = {s: 100 for s in salsas_nombres}


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


# 2. CONSULTA AUTOMÁTICA A SUMUP
@st.cache_data(ttl=300)
def obtener_ventas_sumup(api_key):
    if not api_key:
        return 0.0, 0
    try:
        fecha_fin = datetime.date.today().strftime("%Y-%m-%d")
        fecha_inicio = (
            datetime.date.today() - datetime.timedelta(days=7)
        ).strftime("%Y-%m-%d")

        url = f"https://api.sumup.com/v0.1/me/transactions/history?statuses[]=SUCCESSFUL&changes_since={fecha_inicio}T00:00:00Z"
        headers = {"Authorization": f"Bearer {api_key}"}

        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            datos = response.json()
            items = datos.get("items", [])
            total_euros = sum(tx.get("amount", 0.0) for tx in items)
            total_operaciones = len(items)
            return round(total_euros, 2), total_operaciones
    except Exception:
        pass
    return 0.0, 0


historial_ventas = cargar_historial(URL_WEBAPP)
base_aprendida = math.ceil(sum(historial_ventas) / len(historial_ventas))
ultimas_ventas = historial_ventas[-1] if historial_ventas else 50


# 3. PRONÓSTICO CLIMÁTICO (MIÉRCOLES A DOMINGO)
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
        res = requests.get(url, timeout=5).json()
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


# 4. DETECTOR DE EVENTOS
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
    st.subheader("👨‍🍳 Producción de Salsas del Miércoles")
    st.caption(
        "Aquí registras la cantidad de salsa que cocinas hoy. La sugerencia se ajusta restando lo que tiraste el domingo anterior."
    )

    ratio_ventas = (
        (burgers_estimadas / ultimas_ventas) if ultimas_ventas > 0 else 1.0
    )

    salsas_recomendadas = {}
    for s in salsas_nombres:
        hecho_prev = st.session_state.salsas_hechas.get(s, 850)
        sobra_prev = st.session_state.salsas_sobrantes.get(s, 100)

        consumo_real = max(0, hecho_prev - sobra_prev)

        rec = math.ceil((consumo_real * ratio_ventas) / 50) * 50
        if rec < 200 and consumo_real > 0:
            rec = 200
        salsas_recomendadas[s] = rec if rec > 0 else 800

    st.markdown("### 🥣 Registra la cantidad preparada hoy:")

    nuevas_cantidades_hechas = {}
    col_s1, col_s2 = st.columns(2)

    for idx, s in enumerate(salsas_nombres):
        target_col = col_s1 if idx % 2 == 0 else col_s2
        with target_col:
            rec_val = salsas_recomendadas[s]
            val_actual = st.session_state.salsas_hechas.get(s, rec_val)

            nota_salsa = ""
            if s == "Sweet":
                nota_salsa = " (Classic + Sweet)"
            elif s == "Lima":
                nota_salsa = " (Chicken)"

            nuevas_cantidades_hechas[s] = st.number_input(
                f"Salsa {s}{nota_salsa} (Sugerido: {rec_val}g):",
                min_value=0,
                value=int(val_actual),
                step=50,
                key=f"prod_mie_{s}",
            )

    if st.button("💾 Guardar Producción del Miércoles", type="primary"):
        st.session_state.salsas_hechas = nuevas_cantidades_hechas
        st.success(
            "✅ ¡Gramos elaborados guardados! El domingo introducirás lo sobrante para calcular el consumo neto real."
        )

    st.info(
        "📌 **Guardado actualmente para esta semana:** "
        + " | ".join(
            [
                f"**{k}:** {v}g"
                for k, v in st.session_state.salsas_hechas.items()
            ]
        )
    )


# ----------------------------------------------------------
# PESTAÑA 3: DOMINGO (INVENTARIO DE ALMACÉN Y CIERRE)
# ----------------------------------------------------------
with tab_domingo:
    st.subheader("📋 Recuento y Cierre (Domingo Noche)")

    # VENTAS AUTOMÁTICAS DESDE SUMUP
    st.markdown("### 💳 Facturación Local (SumUp API)")
    sumup_euros_auto, sumup_ops_auto = obtener_ventas_sumup(SUMUP_API_KEY)

    col_sum1, col_sum2 = st.columns(2)
    with col_sum1:
        st.metric("Total Cobrado SumUp (7 días)", f"{sumup_euros_auto:.2f} €")
    with col_sum2:
        st.metric("Operaciones Concretadas", f"{sumup_ops_auto} ops")

    with st.expander("⚙️ Modificar manualmente datos de SumUp (Opcional)"):
        sumup_euros = st.number_input(
            "Euros SumUp:", value=sumup_euros_auto, step=1.0
        )
        sumup_ops = st.number_input(
            "Operaciones SumUp:", value=sumup_ops_auto, step=1
        )

    st.markdown("---")

    # RECUENTO DE SALSAS SOBRANTES DEL DOMINGO
    st.markdown("### 🥣 Gramos de Salsa Sobrantes (Sobrante/Tirado)")
    st.caption(
        "Introduce lo que ha quedado en los recipientes el domingo al cerrar."
    )

    nuevas_mermas = {}
    col_m1, col_m2 = st.columns(2)

    for idx, s in enumerate(salsas_nombres):
        target_col = col_m1 if idx % 2 == 0 else col_m2
        with target_col:
            hecho_mie = st.session_state.salsas_hechas.get(s, 0)
            val_sobra = st.session_state.salsas_sobrantes.get(s, 0)

            nuevas_mermas[s] = st.number_input(
                f"Salsa {s} sobrante (Elaborado el mié: {hecho_mie}g):",
                min_value=0,
                value=int(val_sobra),
                step=50,
                key=f"merma_dom_{s}",
            )

    total_merma_g = sum(nuevas_mermas.values())
    coste_estimado_merma = round(total_merma_g * 0.012, 2)

    st.warning(
        f"🗑️ **Sobrantes totales:** {total_merma_g}g tirados (~{coste_estimado_merma}€ en mermas)."
    )

    st.markdown("---")
    st.markdown("### 📦 Stock de Almacén")

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

    url_lista_wa = (
        f"https://wa.me/{TEL_MI_NUMERO}?text={urllib.parse.quote(lista_compra_txt)}"
    )
    st.link_button("📲 Enviar Lista de Compra por WhatsApp", url_lista_wa)

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
        st.session_state.salsas_sobrantes = nuevas_mermas
        ventas_calculadas = panes_totales_disponibles - pan_sobrante_domingo
        if ventas_calculadas >= 0:
            fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
            if URL_WEBAPP:
                try:
                    params_envio = {
                        "fecha": fecha_hoy,
                        "ventas": ventas_calculadas,
                        "sumup_euros": sumup_euros,
                        "sumup_operaciones": sumup_ops,
                    }
                    r = requests.get(
                        URL_WEBAPP, params=params_envio, timeout=10
                    )
                    if "OK" in r.text:
                        st.success(
                            f"🎯 **¡Guardado con éxito!** Se registraron ~{ventas_calculadas} burgers, {sumup_euros}€ de SumUp y las mermas de salsa."
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
