import streamlit as st
import pandas as pd
import requests, qrcode, io, os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

st.set_page_config(page_title="DramirenG PRO", layout="wide", page_icon="🏷️")

# --- ESTILO BLANCO PRO COMO TU FOTO ---
st.markdown("""
<style>
.stApp { background: #f6f7f9 !important; }
section[data-testid="stSidebar"] { background: #ffffff !important; border-right: 1px solid #e5e7eb; }
h1,h2,h3,p,label { color: #111827 !important; font-family: 'Inter', sans-serif; }

div[data-testid="stTextInput"] input {
    background: #ffffff !important; border: 1px solid #e5e7eb !important;
    border-radius: 12px !important; height: 46px !important; font-weight: 500;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
label p { font-weight: 700 !important; font-size: 12px !important; text-transform: uppercase; letter-spacing: 0.5px; }

div[data-testid="stDataFrame"] {
    background: white; border-radius: 16px !important; border: 1px solid #e5e7eb !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}
.stButton button { border-radius: 12px !important; height: 46px !important; font-weight: 700 !important; }

#btn-buscar button { background: #111827 !important; color: white !important; }
#btn-agregar button { background: #ff7a5c !important; color: white !important; box-shadow: 0 4px 15px rgba(255,122,92,0.4); }
</style>
""", unsafe_allow_html=True)

if 'data' not in st.session_state:
    st.session_state.data = []

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    token = st.text_input("Token API Perú", type="password")
    formato = st.radio("Formato:", ["A4 Vertical - 4 por hoja (una sobre otra)", "A4 Horizontal - toda la hoja", "Térmica 100x150"])
    st.markdown("**Logo DG arriba derecha**")
    logo_dg_file = st.file_uploader(" ", type=["png","jpg"], key="dg")
    st.markdown("**Marcas abajo**")
    logo_marcas_file = st.file_uploader("  ", type=["png","jpg"], key="marcas")

# --- HEADER ---
st.markdown("<h1>DramirenG <span style='color:#ff7a5c'>PRO</span> <span style='font-size:13px; background:#111827; color:white; padding:4px 12px; border-radius:20px;'>v2.0</span></h1>", unsafe_allow_html=True)

# --- FORMULARIO COMO EN TU FOTO ---
c1, c2 = st.columns([1, 2.5])
with c1: dni = st.text_input("DNI/RUC", value="75098930")
with c2: nombre = st.text_input("Nombre", value="DAVID GRABIEL RAMIREZ NIEVES")

c3, c4, c5, c6 = st.columns([1.2, 1.2, 0.6, 0.6])
with c3: destino = st.text_input("DESTINO", value="sullana")
with c4: celular = st.text_input("CELULAR", value="959237626")
with c5: bulto = st.number_input("Bulto", min_value=1, value=1, step=1)
with c6: total = st.number_input("Total", min_value=1, value=4, step=1)

c7, c8 = st.columns(2)
with c7:
    st.markdown('<div id="btn-buscar">', unsafe_allow_html=True)
    if st.button("🔍 Buscar", use_container_width=True):
        if dni and token:
            try:
                url = f"https://apiperu.dev/api/dni/{dni}" if len(dni)==8 else f"https://apiperu.dev/api/ruc/{dni}"
                r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=5)
                if r.status_code==200:
                    d=r.json()
                    st.session_state.nombre_api = d['data'].get('nombre_completo') or d['data'].get('nombre_o_razon_social')
                    st.rerun()
            except: st.error("Error API o Token")
    st.markdown('</div>', unsafe_allow_html=True)

with c8:
    st.markdown('<div id="btn-agregar">', unsafe_allow_html=True)
    if st.button("+ Agregar", use_container_width=True):
        for i in range(bulto, total+1):
            st.session_state.data.append({
                "dni": dni, "nombre": nombre, "destino": destino.upper(),
                "factura": "F001-5652", "celular": celular, "b1": i, "b2": total
            })
    st.markdown('</div>', unsafe_allow_html=True)

# --- TABLA CON EDITAR Y BORRAR ---
if st.session_state.data:
    df = pd.DataFrame(st.session_state.data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    col_del, col_pdf = st.columns([1,2])
    with col_del:
        if st.button("🗑️ Limpiar", use_container_width=True):
            st.session_state.data = []
            st.rerun()
    with col_pdf:
        # GENERAR PDF
        if st.button("📥 DESCARGAR PDF", use_container_width=True, type="primary"):
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            w, h = A4
            lh = h / 4  # 4 etiquetas por hoja

            for idx, row in enumerate(df.to_dict('records')):
                pos = idx % 4
                y_top = h - (pos * lh)
                
                # Marco
                c.setStrokeColorRGB(0.9,0.9,0.9)
                c.rect(20, y_top - lh + 10, w-40, lh-20)

                # DG ARRIBA DERECHA
                if logo_dg_file:
                    c.drawImage(ImageReader(Image.open(logo_dg_file)), w-120, y_top-50, width=80, height=30, preserveAspectRatio=True)

                # DATOS
                c.setFont("Helvetica-Bold", 14)
                c.drawString(30, y_top-30, f"DESTINO: {row['destino']}")
                c.setFont("Helvetica", 10)
                c.drawString(30, y_top-50, f"{row['nombre']}")
                c.drawString(30, y_top-65, f"DNI: {row['dni']} | CEL: {row['celular']} | FAC: {row['factura']}")
                c.setFont("Helvetica-Bold", 16)
                c.drawString(30, y_top-90, f"BULTO {row['b1']} DE {row['b2']}")

                # QR
                qr = qrcode.make(f"{row['destino']} - {row['nombre']} - B{row['b1']}/{row['b2']}")
                c.drawImage(ImageReader(qr), w-120, y_top-120, width=70, height=70)

                # MARCAS ABAJO
                if logo_marcas_file:
                    c.drawImage(ImageReader(Image.open(logo_marcas_file)), 30, y_top - lh + 25, width=w-80, height=25, preserveAspectRatio=True)

                if pos == 3:
                    c.showPage()
            c.save()
            st.download_button("⬇️ Bajar PDF listo", buffer.getvalue(), "etiquetas_dramireng.pdf", "application/pdf", use_container_width=True)
else:
    st.info("Agrega bultos para ver la tabla")
