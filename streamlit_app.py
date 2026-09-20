import streamlit as st
import pandas as pd
import requests, qrcode, io, base64
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

st.set_page_config(page_title="DramirenG PRO v2.0", layout="wide", page_icon="🏷️")

if 'data' not in st.session_state:
    st.session_state.data = []

# --- ESTILO FINAL CORREGIDO - TEXTO NEGRO VISIBLE ---
st.markdown("""
<style>
.stApp { background: #f6f7f9 !important; }
section[data-testid="stSidebar"] { background: #ffffff !important; }

/* INPUTS BLANCOS CON TEXTO NEGRO FORZADO */
div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
    background: #ffffff !important;
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 12px !important;
    height: 46px !important;
    font-size: 15px !important;
    font-weight: 500 !important;
}
div[data-testid="stTextInput"] label p, div[data-testid="stNumberInput"] label p {
    font-size: 13px !important; font-weight: 800 !important; color: #111827 !important;
}

/* BULTO Y TOTAL EN BLANCO TAMBIEN */
div[data-baseweb="input"] { background: white !important; }
div[data-testid="stNumberInput"] button { background: #e5e7eb !important; }

/* BOTONES */
div[data-testid="stButton"] button { border-radius: 12px !important; height: 48px !important; font-weight: 700 !important; background: #111827 !important; }
div[data-testid="stButton"] button p { color: white !important; }

/* TABLA - TITULOS GRANDES COMO PEDISTE */
div[data-testid="stDataFrame"] { border-radius: 16px !important; background: white !important; }
div[data-testid="stDataFrame"] thead tr th { font-size: 14px !important; font-weight: 800 !important; text-transform: uppercase; color: #111827 !important; background: #f9fafb !important; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    token = st.text_input("TOKEN API PERÚ", type="password")
    formato = st.radio("FORMATO:", ["A4 VERTICAL - 4 POR HOJA (UNA SOBRE OTRA)", "A4 HORIZONTAL - TODA LA HOJA", "TÉRMICA 100X150"])
    st.markdown("**Logo DG arriba derecha**")
    logo_dg_file = st.file_uploader("DG", type=["png","jpg","jpeg"], label_visibility="collapsed")
    st.markdown("**Marcas abajo**")
    logo_marcas_file = st.file_uploader("Marcas", type=["png","jpg","jpeg"], label_visibility="collapsed")

# --- HEADER CON ESPACIO PARA LOGOS COMO MARCASTE ---
c_header, c_logo1, c_logo2 = st.columns([6,1,1])
with c_header:
    st.markdown("<h1 style='margin:0;'>DramirenG <span style='color:#ff7a5c'>PRO</span> <span style='font-size:13px; background:#111827; color:white; padding:4px 10px; border-radius:20px;'>v2.0</span></h1>", unsafe_allow_html=True)
with c_logo1:
    if logo_dg_file: st.image(logo_dg_file, width=90)
with c_logo2:
    if logo_marcas_file: st.image(logo_marcas_file, width=90)

PROVINCIAS = ["SULLANA","PIURA","PAITA","TALARA","LIMA","TRUJILLO","CHICLAYO","TUMBES","CHIMBOTE","CAJAMARCA","JAEN","IQUITOS","PUCALLPA","TARAPOTO","CUSCO","AREQUIPA","TACNA","JULIACA","HUANCAYO","ICA","PISCO"]

# --- FORMULARIO ---
col1, col2 = st.columns([1, 2.5])
with col1: dni = st.text_input("DNI/RUC", placeholder="75098930")
with col2: nombre = st.text_input("NOMBRE", placeholder="DAVID GRABIEL RAMIREZ NIEVES")

col3, col4, col5, col6 = st.columns([1.5,1.5,0.5,0.5])
with col3: 
    destino = st.selectbox("DESTINO - Se autocompleta", PROVINCIAS, index=0)
with col4: celular = st.text_input("CELULAR", placeholder="959237626")
with col5: bulto = st.number_input("BULTO", 1, 100, 1)
with col6: total = st.number_input("TOTAL", 1, 100, 4)

b1, b2 = st.columns(2)
with b1:
    if st.button("🔍 Buscar DNI", use_container_width=True):
        if len(dni)==8 and token:
            try:
                r = requests.get(f"https://apiperu.dev/api/dni/{dni}", headers={"Authorization": f"Bearer {token}"}, timeout=5)
                if r.status_code==200:
                    data = r.json()['data']
                    st.success(f"Encontrado: {data.get('nombre_completo')}")
            except: st.error("Token inválido")
with b2:
    if st.button("➕ Agregar", use_container_width=True):
        for i in range(bulto, total+1):
            st.session_state.data.append({"dni":dni,"nombre":nombre,"destino":destino,"celular":celular,"b1":i,"b2":total,"factura":"F001"})
        st.rerun()

# --- TABLA ABAJO CON TITULOS GRANDES ---
if st.session_state.data:
    df = pd.DataFrame(st.session_state.data)
    st.markdown("### 📦 Bultos Agregados")
    st.dataframe(df, use_container_width=True, hide_index=True, height=300)

    if st.button("🖨️ GENERAR VISTA PREVIA PARA IMPRIMIR", type="primary", use_container_width=True):
        # GENERAR PDF
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4
        lh = h/4
        for idx, row in enumerate(df.to_dict('records')):
            pos = idx % 4
            y_top = h - (pos * lh)
            c.setStrokeColorRGB(0.9,0.9,0.9); c.rect(20, y_top-lh+10, w-40, lh-20)
            if logo_dg_file:
                c.drawImage(ImageReader(Image.open(logo_dg_file)), w-110, y_top-45, width=70, height=30, preserveAspectRatio=True)
            c.setFont("Helvetica-Bold", 14); c.drawString(30, y_top-30, f"DESTINO: {row['destino']}")
            c.setFont("Helvetica", 10); c.drawString(30, y_top-50, f"{row['nombre']}")
            c.drawString(30, y_top-65, f"DNI: {row['dni']} | CEL: {row['celular']}")
            c.setFont("Helvetica-Bold", 16); c.drawString(30, y_top-90, f"BULTO {row['b1']} DE {row['b2']}")
            qr = qrcode.make(f"{row['destino']}-{row['b1']}/{row['b2']}")
            c.drawImage(ImageReader(qr), w-110, y_top-110, width=60, height=60)
            if logo_marcas_file:
                c.drawImage(ImageReader(Image.open(logo_marcas_file)), 30, y_top-lh+25, width=w-80, height=20, preserveAspectRatio=True)
            if pos==3: c.showPage()
        c.save()
        pdf_bytes = buffer.getvalue()
        b64 = base64.b64encode(pdf_bytes).decode()
        
        # VISTA PREVIA + IMPRIMIR DIRECTO
        st.markdown("### 👀 Vista Previa - Dale a Imprimir")
        pdf_display = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        st.download_button("⬇️ Si quieres descargar también", pdf_bytes, "etiquetas.pdf", use_container_width=True)
        # BOTON IMPRIMIR DIRECTO
        st.components.v1.html(f"""
            <script>
            function printPDF() {{
                var iframe = document.createElement('iframe');
                iframe.style.display = 'none';
                iframe.src = 'data:application/pdf;base64,{b64}';
                document.body.appendChild(iframe);
                iframe.onload = function() {{ iframe.contentWindow.print(); }};
            }}
            </script>
            <button onclick="printPDF()" style="width:100%; height:50px; background:#111827; color:white; border-radius:12px; font-weight:700; margin-top:10px;">🖨️ IMPRIMIR AHORA</button>
        """, height=70)

    if st.button("🗑️ Limpiar todo"): 
        st.session_state.data=[]; st.rerun()
else:
    st.info("Agrega bultos para ver la tabla")
