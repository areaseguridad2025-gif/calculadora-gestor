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
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.session_state.user_role = ""
        st.rerun()

    st.title("📋 Panel de Gestión de Datos")
    
    tab1, tab2, tab3 = st.tabs(["➕ Nuevo Registro", "✏️ Editar Registro", "🔍 Consultar y Buscar"])

    with tab1:
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
                            st.success(f"¡Registro #{resultado.get('id')} guardado y sincronizado exitosamente!")
                        elif resultado.get("status") == "duplicate":
                            st.warning(resultado.get("message"))
                        else:
                            st.error(f"Error en el servidor de Google: {resultado.get('message')}")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")

    with tab2:
        st.markdown("Escribe la **Placa** del registro que deseas buscar y editar:")
        
        busqueda_edicion = st.text_input("🔍 Ingresar Placa a buscar para editar...", "").strip().upper()
        
        if busqueda_edicion:
            try:
                resp_get = requests.get(WEBHOOK_URL)
                res_json = resp_get.json()
                if res_json.get("status") == "success":
                    rows_data = res_json.get("data", [])
                    if len(rows_data) > 1:
                        df_edit = pd.DataFrame(rows_data[1:], columns=rows_data[0])
                        df_edit.columns = [str(col).strip().upper() for col in df_edit.columns]
                        
                        if "PLACA" in df_edit.columns:
                            fila_match = df_edit[df_edit["PLACA"].astype(str).str.upper() == busqueda_edicion]
                            
                            if not fila_match.empty:
                                row_vals = fila_match.iloc[0]
                                target_id = row_vals.get("ID", "")
                                
                                def get_field(col_name, fallback_index):
                                    if col_name in row_vals and pd.notna(row_vals[col_name]):
                                        return str(row_vals[col_name])
                                    try:
                                        return str(fila_match.iloc[0, fallback_index])
                                    except:
                                        return ""

                                val_placa = get_field("PLACA", 2)
                                val_serie = get_field("SERIE", 3)
                                val_cc = get_field("CENTRO_COSTO", 4) if "CENTRO_COSTO" in df_edit.columns else get_field("CENTRO DE COSTO", 4)
                                val_pv = get_field("PUNTO_VENTA", 5) if "PUNTO_VENTA" in df_edit.columns else get_field("PUNTO DE VENTA", 5)
                                val_c1 = get_field("CIAP_1", 6)
                                val_c2 = get_field("CIAP_2", 7)
                                val_func = get_field("FUNCIONARIO_SEGURIDAD", 8)

                                st.success(f"¡Registro encontrado! (ID: {target_id}) Modifica los campos necesarios:")
                                
                                with st.form("form_edicion"):
                                    e_col1, e_col2 = st.columns(2)
                                    with e_col1:
                                        n_placa = st.text_input("PLACA", value=val_placa)
                                        n_serie = st.text_input("SERIE", value=val_serie)
                                        n_cc = st.text_input("CENTRO DE COSTO", value=val_cc if val_cc else "")
                                        n_pv = st.text_input("PUNTO DE VENTA", value=val_pv if val_pv else "")
                                    with e_col2:
                                        n_c1 = st.text_input("CIAP 1", value=val_c1)
                                        n_c2 = st.text_input("CIAP 2", value=val_c2)
                                        n_func = st.text_input("FUNCIONARIO DE SEGURIDAD", value=val_func)
                                    
                                    update_submitted = st.form_submit_button("Actualizar Registro en Google Sheets")
                                    
                                    if update_submitted:
                                        payload_update = {
                                            "action": "update",
                                            "id": target_id,
                                            "placa": n_placa.upper(),
                                            "serie": n_serie.upper(),
                                            "centro_costo": n_cc.upper(),
                                            "punto_venta": n_pv.upper(),
                                            "ciap_1": n_c1,
                                            "ciap_2": n_c2,
                                            "funcionario_seguridad": n_func.upper(),
                                            "rol": st.session_state.user_role
                                        }
                                        
                                        resp_up = requests.post(WEBHOOK_URL, json=payload_update)
                                        res_up_json = resp_up.json()
                                        
                                        if res_up_json.get("status") == "success":
                                            st.success("¡Registro actualizado exitosamente en la nube!")
                                        else:
                                            st.error(f"Error: {res_up_json.get('message')}")
                            else:
                                st.warning("No se encontró ningún registro con esa placa exacta.")
                        else:
                            st.error("No se encontró la columna PLACA en la hoja de cálculo.")
            except Exception as e:
                st.warning(f"Error de conexión: {e}")

    with tab3:
        st.subheader("🔍 Consultar y Buscar Registro")
        st.markdown("Escribe la **Placa** para consultar la información en formato de formulario:")
        
        busqueda_consulta = st.text_input("🔍 Ingresar Placa a consultar...", "").strip().upper()
        
        if busqueda_consulta:
            try:
                response = requests.get(WEBHOOK_URL)
                resultado = response.json()
                if resultado.get("status") == "success":
                    rows = resultado.get("data", [])
                    if len(rows) > 1:
                        df_view = pd.DataFrame(rows[1:], columns=rows[0])
                        df_view.columns = [str(col).strip().upper() for col in df_view.columns]
                        
                        if "PLACA" in df_view.columns:
                            fila_match = df_view[df_view["PLACA"].astype(str).str.upper() == busqueda_consulta]
                            
                            if not fila_match.empty:
                                row_vals = fila_match.iloc[0]
                                target_id = row_vals.get("ID", "")
                                
                                def get_field_c(col_name, fallback_index):
                                    if col_name in row_vals and pd.notna(row_vals[col_name]):
                                        return str(row_vals[col_name])
                                    try:
                                        return str(fila_match.iloc[0, fallback_index])
                                    except:
                                        return ""

                                c_placa = get_field_c("PLACA", 2)
                                c_serie = get_field_c("SERIE", 3)
                                c_cc = get_field_c("CENTRO_COSTO", 4) if "CENTRO_COSTO" in df_view.columns else get_field_c("CENTRO DE COSTO", 4)
                                c_pv = get_field_c("PUNTO_VENTA", 5) if "PUNTO_VENTA" in df_view.columns else get_field_c("PUNTO DE VENTA", 5)
                                c_c1 = get_field_c("CIAP_1", 6)
                                c_c2 = get_field_c("CIAP_2", 7)
                                c_func = get_field_c("FUNCIONARIO_SEGURIDAD", 8)

                                st.success(f"¡Registro encontrado! (ID: {target_id})")
                                
                                c_col1, c_col2 = st.columns(2)
                                with c_col1:
                                    st.text_input("PLACA (Consulta)", value=c_placa, disabled=True, key="c_placa")
                                    st.text_input("SERIE (Consulta)", value=c_serie, disabled=True, key="c_serie")
                                    st.text_input("CENTRO DE COSTO (Consulta)", value=c_cc, disabled=True, key="c_cc")
                                    st.text_input("PUNTO DE VENTA (Consulta)", value=c_pv, disabled=True, key="c_pv")
                                with c_col2:
                                    st.text_input("CIAP 1 (Consulta)", value=c_c1, disabled=True, key="c_c1")
                                    st.text_input("CIAP 2 (Consulta)", value=c_c2, disabled=True, key="c_c2")
                                    st.text_input("FUNCIONARIO DE SEGURIDAD (Consulta)", value=c_func, disabled=True, key="c_func")
                            else:
                                st.warning("No se encontró ningún registro con esa placa exacta.")
            except Exception as e:
                st.warning(f"Error de conexión: {e}")
        else:
            st.info("Escribe una Placa en la barra superior para desplegar su ficha informativa.")

else:
    st.title("🧮 Calculadora Científica")
    st.write("Ingrese una operación matemática.")

    entrada = st.text_input("Pantalla", value="", placeholder="Ej. 45 * 12")

    if st.button("Calcular"):
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
                    st.error("Operación no válida.")
            except Exception:
                st.error("Operación no válida.")

    st.markdown("---")
    st.caption("v1.2.1 - Sistema estándar de cálculo")
