from datetime import datetime, timedelta
import requests
import streamlit as st

st.set_page_config(page_title="Perry's Burgers - Dashboard", page_icon="🍔")
st.title("🍔 Perry's Burgers - Control Semanal")


# --- FUNCIÓN PARA CONSULTAR SUMUP AUTOMÁTICAMENTE ---
def obtener_ventas_sumup():
    try:
        api_key = st.secrets["SUMUP_API_KEY"]
        # Consultar los últimos 7 días
        fecha_fin = datetime.now().strftime("%Y-%m-%d")
        fecha_inicio = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        url = f"https://api.sumup.com/v0.1/me/transactions/history?statuses[]=SUCCESSFUL&changes_since={fecha_inicio}T00:00:00Z"
        headers = {"Authorization": f"Bearer {api_key}"}

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            datos = response.json()
            items = datos.get("items", [])
            total_euros = sum(tx.get("amount", 0.0) for tx in items)
            total_operaciones = len(items)
            return round(total_euros, 2), total_operaciones
        else:
            st.warning("No se pudo obtener datos de SumUp automáticamente.")
            return 0.0, 0
    except Exception as e:
        st.error(f"Error al conectar con la API de SumUp: {e}")
        return 0.0, 0


# --- CARGA DE DATOS AUTOMÁTICA DE SUMUP ---
sumup_euros, sumup_burgers = obtener_ventas_sumup()

st.markdown("---")
st.header("📊 Resumen de la Semana")

# Mostrar métricas de SumUp recuperadas por la API
col_s1, col_s2 = st.columns(2)
col_s1.metric("💳 SumUp Local (€)", f"{sumup_euros:.2f} €")
col_s2.metric("🍔 Burgers / Ventas SumUp", f"{sumup_burgers} uds")

st.markdown("---")
st.header("🥖 Control de Inventario (Único dato manual)")

panes_iniciales = st.number_input(
    "Panes iniciales (Miércoles)", value=150, step=1
)
panes_sobrantes = st.number_input(
    "Panes sobrantes (Domingo cierre)", value=10, step=1
)
panes_consumidos = panes_iniciales - panes_sobrantes

st.info(f"🍔 **Consumo total de panes de la semana:** {panes_consumidos} uds")

st.markdown("---")

# --- BOTÓN DE ENVÍO Y REGISTRO EN GOOGLE SHEETS ---
if st.button("🚀 Guardar Cierre Semanal"):
    payload = {
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "panes_consumidos": panes_consumidos,
        "sumup_euros": sumup_euros,
        "sumup_burgers": sumup_burgers,
    }

    try:
        res = requests.get(st.secrets["URL_WEBAPP"], params=payload)
        if "OK" in res.text:
            st.success("✅ ¡Datos registrados con éxito en Google Sheets!")
        else:
            st.error("⚠️ Hubo un detalle al enviar los datos a la hoja.")
    except Exception as err:
        st.error(f"Error al conectar con Google Sheets: {err}")

