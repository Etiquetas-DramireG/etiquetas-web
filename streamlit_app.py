import streamlit as st
import pandas as pd
import requests, qrcode, io, base64
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

st.set_page_config(page_title="DramirenG PRO", layout="wide", page_icon="🏷️")

if 'logged' not in st.session_state:
    st.session_state.logged = False
if 'data' not in st.session_state:
    st.session_state.data = []

# --- LOGIN CON COLORES ARREGLADOS ---
if not st.session_state.logged:
    st.markdown("""
    <style>
    .stApp { background: #f2f3f7 !important; }
    
    /* TITULO VISIBLE */
    h1 { color: #111827 !important; }
    
    /* INPUTS BLANCOS CON BORDE NEGRO VISIBLE */
    div[data-testid="stTextInput"] input {
        background: #ffffff !important;
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        border: 2px solid #111827 !important;
        border-radius: 12px !important;
        height: 50px !important;
    }
    div[data-testid="stTextInput"] label p {
        color: #111827 !important;
        font-weight: 800 !important;
        font-size: 14px !important;
    }
    /* OJO DE CLAVE EN NEGRO */
    div[data-testid="stTextInput"] button {
        background: #111827 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1,1.2,1])
    with c2:
        st.markdown("<br><br><h1 style='text-align:center; color:#111827;'>DramirenG <span style='color:#ff7a5c;'>PRO</span> <span style='background:#111827; color:white; padding:4px 10px; border-radius:20px; font-size:14px;'>v2.0</span></h1><p style='text-align:center; color:#6b7280;'>Inicia sesión para continuar</p>", unsafe_allow_html=True)
        
        user = st.text_input("USUARIO", placeholder="admin")
        clave = st.text_input("CLAVE", type="password", placeholder="dramireng123")
        
        if st.button("🔐 Entrar", use_container_width=True, type="primary"):
            if user == "admin" and clave == "dramireng123":
                st.session_state.logged = True
                st.rerun()
            else:
                st.error("Usuario o clave incorrecta - Usa admin / dramireng123")
        st.stop()

# --- APP PRINCIPAL ---
st.markdown("""
<style>
.stApp { background: #f8f9fb !important; }
section[data-testid="stSidebar"] { background: #ffffff !important; }
div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
    background: #ffffff !important; color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
    border: 1px solid #d1d5db !important; border-radius: 12px !important; height: 48px !important;
}
div[data-baseweb="select"] > div { background: #ffffff !important; border-radius: 12px !important; border: 1px solid #d1d5db !important; }
div[data-baseweb="select"] span { color: #111827 !important; -webkit-text-fill-color: #111827 !important; }
div[data-testid="stButton"] button { background: #111827 !important; border-radius: 12px !important; height: 50px !important; }
div[data-testid="stButton"] button p { color: white !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

col_t, col_l = st.columns([7, 1.5])
with col_t:
    st.markdown("<h1 style='margin:0; color:#111827;'>DramirenG <span style='color:#ff7a5c'>PRO</span> <span style='font-size:12px; background:#111827; color:white; padding:4px 12px; border-radius:20px;'>v2.0</span></h1>", unsafe_allow_html=True)
with col_l:
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        st.session_state.logged = False
        st.rerun()

with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    token = st.text_input("TOKEN API PERÚ", type="password")
    logo_dg = st.file_uploader("Logo DG", type=["png","jpg","jpeg"])
    logo_marcas = st.file_uploader("Marcas", type=["png","jpg","jpeg"])

PROVINCIAS = ["SULLANA","PIURA","PAITA","TALARA","LIMA","TRUJILLO","CHICLAYO","TUMBES"]

c1, c2 = st.columns([1, 2.5])
with c1: dni = st.text_input("DNI/RUC", value="75098930")
with c2: nombre = st.text_input("NOMBRE", value="DAVID GRABIEL RAMIREZ NIEVES")

c3, c4, c5, c6 = st.columns([1.2, 1.2, 0.4, 0.4])
with c3: destino = st.selectbox("DESTINO", PROVINCIAS, index=0)
with c4: celular = st.text_input("CELULAR", value="959237626")
with c5: bulto = st.number_input("BULTO", 1, value=1)
with c6: total = st.number_input("TOTAL", 1, value=4)

b1, b2 = st.columns(2)
with b1:
    if st.button("🔍 Buscar DNI", use_container_width=True):
        st.toast("Buscando...")
with b2:
    if st.button("➕ Agregar", use_container_width=True):
        for i in range(bulto, total+1):
            st.session_state.data.append({"DNI/RUC":dni,"NOMBRE":nombre,"DESTINO":destino,"CELULAR":celular,"B1":i,"B2":total})
        st.rerun()

if st.session_state.data:
    df = pd.DataFrame(st.session_state.data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    if st.button("🖨️ VISTA PREVIA E IMPRIMIR", type="primary", use_container_width=True):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4; lh = h/4
        for idx, row in enumerate(df.to_dict('records')):
            pos = idx % 4; y_top = h - (pos * lh)
            c.rect(20, y_top-lh+10, w-40, lh-20)
            c.setFont("Helvetica-Bold", 14); c.drawString(30, y_top-30, f"DESTINO: {row['DESTINO']}")
            c.drawString(30, y_top-65, f"DNI: {row['DNI/RUC']} | CEL: {row['CELULAR']}")
            c.setFont("Helvetica-Bold", 16); c.drawString(30, y_top-90, f"BULTO {row['B1']} DE {row['B2']}")
            qr = qrcode.make(f"{row['DESTINO']}-{row['B1']}/{row['B2']}")
            c.drawImage(ImageReader(qr), w-105, y_top-115, width=60, height=60)
            if pos==3: c.showPage()
        c.save()
        b64 = base64.b64encode(buffer.getvalue()).decode()
        st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="700"></iframe>', unsafe_allow_html=True)
