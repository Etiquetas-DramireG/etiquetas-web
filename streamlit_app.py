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

# --- LOGIN ---
if not st.session_state.logged:
    st.markdown("""
    <style>
    .stApp { background: #f8f9fb !important; }
    div[data-testid="stTextInput"] input { background:white !important; color:#111827 !important; -webkit-text-fill-color:#111827 !important; border-radius:12px !important; height:48px !important; }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1.2,1])
    with col2:
        st.markdown("<br><br><h1 style='text-align:center;'>DramirenG <span style='color:#ff7a5c'>PRO</span> v2.0</h1><p style='text-align:center;'>Inicia sesión para continuar</p>", unsafe_allow_html=True)
        user = st.text_input("Usuario")
        clave = st.text_input("Clave", type="password")
        if st.button("🔐 Entrar", use_container_width=True, type="primary"):
            if user == "admin" and clave == "dramireng123":
                st.session_state.logged = True
                st.rerun()
            else:
                st.error("Usuario o clave incorrecta")
        st.stop()

# --- SI YA ESTA LOGEADO - TU APP NORMAL ---
st.markdown("""
<style>
.stApp { background: #f8f9fb !important; }
section[data-testid="stSidebar"] { background: #ffffff !important; }
div[data-testid="stTextInput"] input { background: #ffffff !important; color: #111827 !important; -webkit-text-fill-color: #111827 !important; border: 1px solid #e5e7eb !important; border-radius: 12px !important; height: 48px !important; }
div[data-baseweb="select"] > div { background: #ffffff !important; border-radius: 12px !important; border: 1px solid #e5e7eb !important; min-height: 48px !important; }
div[data-baseweb="select"] span { color: #111827 !important; -webkit-text-fill-color: #111827 !important; }
div[data-baseweb="input"] { background: #ffffff !important; }
div[data-testid="stNumberInput"] input { background: #ffffff !important; color: #111827 !important; -webkit-text-fill-color: #111827 !important; }
div[data-testid="stButton"] button { background: #111827 !important; border-radius: 12px !important; height: 50px !important; }
div[data-testid="stButton"] button p { color: white !important; font-weight: 700 !important; }
div[data-testid="stDataFrame"] thead tr th { font-size: 14px !important; font-weight: 800 !important; text-transform: uppercase !important; }
</style>
""", unsafe_allow_html=True)

col_titulo, col_logout = st.columns([7, 1.5])
with col_titulo:
    st.markdown("<h1 style='margin:0; color:#111827;'>DramirenG <span style='color:#ff7a5c'>PRO</span> <span style='font-size:12px; background:#111827; color:white; padding:4px 12px; border-radius:20px;'>v2.0</span></h1>", unsafe_allow_html=True)
with col_logout:
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        st.session_state.logged = False
        st.session_state.data = []
        st.rerun()

with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    token = st.text_input("TOKEN API PERÚ", type="password", placeholder="Tu token")
    formato = st.radio("FORMATO", ["A4 VERTICAL - 4 POR HOJA", "A4 HORIZONTAL", "TÉRMICA 100X150"], label_visibility="collapsed")
    logo_dg = st.file_uploader("Logo DG arriba derecha", type=["png","jpg","jpeg"])
    logo_marcas = st.file_uploader("Marcas abajo", type=["png","jpg","jpeg"], key="marcas")

PROVINCIAS = ["SULLANA","PIURA","PAITA","TALARA","LIMA","CALLAO","TRUJILLO","CHICLAYO","TUMBES","CHIMBOTE","CAJAMARCA","JAEN","IQUITOS","PUCALLPA","TARAPOTO","CUSCO","AREQUIPA","TACNA","JULIACA","HUANCAYO","ICA","PISCO"]

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
        if len(dni)==8 and token:
            try:
                r = requests.get(f"https://apiperu.dev/api/dni/{dni}", headers={"Authorization": f"Bearer {token}"}, timeout=5)
                if r.status_code==200: st.success("Encontrado")
            except: st.error("Error API")
with b2:
    if st.button("➕ Agregar", use_container_width=True):
        for i in range(bulto, total+1):
            st.session_state.data.append({"DNI/RUC":dni,"NOMBRE":nombre,"DESTINO":destino,"CELULAR":celular,"B1":i,"B2":total,"FACTURA":"F001"})
        st.rerun()

if st.session_state.data:
    df = pd.DataFrame(st.session_state.data)
    st.dataframe(df, use_container_width=True, hide_index=True, height=350)
    if st.button("🖨️ VISTA PREVIA E IMPRIMIR", type="primary", use_container_width=True):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4
        lh = h/4
        for idx, row in enumerate(df.to_dict('records')):
            pos = idx % 4
            y_top = h - (pos * lh)
            c.rect(20, y_top-lh+10, w-40, lh-20)
            c.setFont("Helvetica-Bold", 14); c.drawString(30, y_top-30, f"DESTINO: {row['DESTINO']}")
            c.setFont("Helvetica", 10); c.drawString(30, y_top-50, f"{row['NOMBRE']}")
            c.drawString(30, y_top-65, f"DNI: {row['DNI/RUC']} | CEL: {row['CELULAR']}")
            c.setFont("Helvetica-Bold", 16); c.drawString(30, y_top-90, f"BULTO {row['B1']} DE {row['B2']}")
            qr = qrcode.make(f"{row['DESTINO']}-{row['B1']}/{row['B2']}")
            c.drawImage(ImageReader(qr), w-105, y_top-115, width=60, height=60)
            if pos==3: c.showPage()
        c.save()
        b64 = base64.b64encode(buffer.getvalue()).decode()
        st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="700"></iframe>', unsafe_allow_html=True)
else:
    st.info("Agrega bultos para ver la tabla")
