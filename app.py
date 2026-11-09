import streamlit as st
import pandas as pd
from datetime import datetime
import requests

st.set_page_config(page_title="Calculadora Estándar", page_icon="🧮", layout="centered")

WEBHOOK_URL = st.secrets["WEBHOOK_URL"]

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = ""

PINS = {
    "1020": "COORDINADOR",
    "1030": "ANALISTA",
    "1040": "AUXILIAR"
}

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
                    payload = {
                        "placa": placa.upper(),
                        "serie": serie.upper(),
                        "centro_costo": centro_costo.upper(),
                        "punto_venta": punto_venta.upper(),
                        "ciap_1": ciap_1,
                        "ciap_2": ciap_2,
                        "funcionario_seguridad": funcionario_seguridad.upper(),
                        "rol": st.session_state.user_role
                    }
                    
                    response = requests.post(WEBHOOK_URL, json=payload)
                    resultado = response.json()
                    
                    if resultado.get("status") == "success":
                        st.success("¡Registro guardado y sincronizado en Google Drive en tiempo real!")
                        st.rerun()
                    else:
                        st.error(f"Error en el servidor de Google: {resultado.get('message')}")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

    st.subheader("Registros Recientes en la Nube")
    try:
        response = requests.get(WEBHOOK_URL)
        resultado = response.json()
        if resultado.get("status") == "success":
            rows = resultado.get("data", [])
            if len(rows) > 1:
                # La primera fila son los encabezados
                df_view = pd.DataFrame(rows[1:], columns=rows[0])
                st.dataframe(df_view.tail(10))
            else:
                st.info("Aún no hay registros guardados en la hoja.")
        else:
            st.warning("No se pudieron cargar los registros previos.")
    except Exception as e:
        st.warning("No se pudieron cargar los registros previos.")

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
    st.caption("v1.0.6 - Sistema estándar de cálculo")
