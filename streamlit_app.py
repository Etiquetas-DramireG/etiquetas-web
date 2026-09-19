import streamlit as st
from fpdf import FPDF
import requests
import os
from datetime import datetime

# --- LOGIN ---
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 DramirenG - Login")
    user = st.text_input("Usuario")
    pwd = st.text_input("Clave", type="password")
    if st.button("Ingresar"):
        if user == "admin" and pwd == "dramiren2026":
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Usuario o clave incorrecta")
    st.stop()

# --- APP ---
st.set_page_config(page_title="Etiquetas - DramirenG", layout="centered")
st.title("🏷️ Etiquetas - DramirenG")
st.sidebar.success("Conectado: admin")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.login = False
    st.rerun()

DESTINOS = ["LIMA","ICA","PIURA","SULLANA","TRUJILLO","CHICLAYO","AREQUIPA","CUSCO","TUMBES","CHIMBOTE","HUANCAYO","TACNA","JULIACA"]

col1, col2 = st.columns(2)
with col1:
    dni = st.text_input("DNI / RUC")
    if st.button("🔍 Buscar"):
        try:
            url = f"https://api.apis.net.pe/v1/dni?numero={dni}" if len(dni)==8 else f"https://api.apis.net.pe/v1/ruc?numero={dni}"
            r = requests.get(url, timeout=5).json()
            nombre_auto = r.get('nombre') or r.get('razonSocial') or ""
            st.session_state['nombre_buscado'] = nombre_auto
            st.success(nombre_auto)
        except:
            st.warning("Escribe manual, no hay internet")
    nombre = st.text_input("Nombre Cliente", value=st.session_state.get('nombre_buscado',''))
    destino = st.selectbox("Destino", DESTINOS)
    direccion = st.text_input("Dirección")

with col2:
    producto = st.text_input("Producto", "Pantalón")
    cantidad = st.number_input("Cantidad", 1, 100, 1)
    agencia = st.selectbox("Agencia", ["Shalom","Marvisur","Olva","Flores","Otros"])
    formato = st.radio("Formato", ["A4 (4 etiquetas)", "A3 (1 gigante)"])

if st.button("📦 Generar PDF", type="primary"):
    pdf = FPDF(format='A4' if 'A4' in formato else 'A3')
    pdf.add_page()
    pdf.set_font("Arial","B",20)
    pdf.cell(0,15,f"DESTINO: {destino}",ln=True,align="C")
    pdf.set_font("Arial","",12)
    pdf.cell(0,8,f"Cliente: {nombre}",ln=True)
    pdf.cell(0,8,f"DNI/RUC: {dni}",ln=True)
    pdf.cell(0,8,f"Dirección: {direccion}",ln=True)
    pdf.cell(0,8,f"Producto: {producto} x{cantidad}",ln=True)
    pdf.cell(0,8,f"Agencia: {agencia}",ln=True)
    pdf.cell(0,8,f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}",ln=True)
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    st.download_button("⬇️ Descargar PDF", pdf_bytes, file_name=f"etiqueta_{dni}.pdf")
    st.success("¡Listo!")
