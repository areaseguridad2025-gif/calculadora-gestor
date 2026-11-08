import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# Configuración de la interfaz
st.set_page_config(page_title="Calculadora Estándar", page_icon="🧮", layout="centered")

# --- CONEXIÓN SEGURA CON GOOGLE SHEETS ---
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def conectar_google_sheets():
    # Lee directamente los secretos configurados en Streamlit
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open("gestor_datos_seguridad.xlsx").sheet1
    return sheet

# Control de sesión
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = ""

# Diccionario de PINs autorizados
PINS = {
    "1020": "COORDINADOR",
    "1030": "ANALISTA",
    "1040": "AUXILIAR"
}

# --- MODO GESTOR DE DATOS (DESBLOQUEADO) ---
if st.session_state.authenticated:
    st.sidebar.success(f"Sesión activa: {st.session_state.user_role}")
    if st.sidebar.button("Cerrar Sesión (Volver a Calculadora)"):
        st.session_state.authenticated = False
        st.session_state.user_role = ""
        st.rerun()

    st.title("📋 Panel de Gestión de Datos")
    st.markdown("Ingrese la información requerida en la ficha:")

    with st.form("form_gestion"):
        col1, col2 = st.columns(2)
        with col1:
            placa = st.text_input("PLACA")
            serie = st.text_input("SERIE")
            centro_costo = st.text_input("CENTRO DE COSTO")
            punto_venta = st.text_input("PUNTO DE VENTA")
        with col2:
            ciap_1 = st.text_input("CIAP 1")
            ciap_2 = st.text_input("CIAP 2")
            funcionario_seguridad = st.text_input("FUNCIONARIO DE SEGURIDAD")
        
        submitted = st.form_submit_button("Guardar y Sincronizar en Google Drive")
        
        if submitted:
            if not placa or not serie:
                st.error("Por favor completa al menos Placa y Serie.")
            else:
                try:
                    sheet = conectar_google_sheets()
                    data = sheet.get_all_records()
                    nuevo_id = len(data) + 1
                    
                    nueva_fila = [
                        nuevo_id,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        placa.upper(),
                        serie.upper(),
                        centro_costo.upper(),
                        punto_venta.upper(),
                        ciap_1,
                        ciap_2,
                        funcionario_seguridad.upper(),
                        st.session_state.user_role
                    ]
                    
                    sheet.append_row(nueva_fila)
                    st.success(f"¡Registro #{nuevo_id} guardado y sincronizado en Google Drive en tiempo real!")
                except Exception as e:
                    st.error(f"Error al sincronizar con Google Drive: {e}")

    st.subheader("Registros Recientes en la Nube")
    try:
        sheet = conectar_google_sheets()
        df_view = pd.DataFrame(sheet.get_all_records())
        if not df_view.empty:
            st.dataframe(df_view.tail(10))
        else:
            st.info("Aún no hay registros guardados.")
    except Exception as e:
        st.warning("No se pudieron cargar los registros previos.")

# --- MODO SEÑUELO: CALCULADORA FUNCIONAL ---
else:
    st.title("🧮 Calculadora Científica")
    st.write("Ingrese una operación matemática o introduzca su PIN de acceso.")

    entrada = st.text_input("Pantalla", value="", placeholder="Ej. 45 * 12 o PIN de usuario")

    if st.button("Calcular / Acceder"):
        if entrada.strip() in PINS:
            st.session_state.authenticated = True
            st.session_state.user_role = PINS[entrada.strip()]
            st.success("Acceso concedido. Cargando gestor...")
            st.rerun()
        else:
            try:
                allowed_chars = set("0123456789+-*/(). ")
                if all(c in allowed_chars for c in entrada):
                    resultado = eval(entrada)
                    st.info(f"Resultado: {resultado}")
                else:
                    st.error("Operación no válida o PIN incorrecto.")
            except Exception:
                st.error("Operación no válida.")

    st.markdown("---")
    st.caption("v1.0.4 - Sistema estándar de cálculo")
