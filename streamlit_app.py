import streamlit as st
import pandas as pd
import qrcode, io, base64
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

st.set_page_config(page_title="Bienvenido", layout="wide", page_icon="🏷️")
if 'logged' not in st.session_state: st.session_state.logged = False
if 'data' not in st.session_state: st.session_state.data = []
if 'print_now' not in st.session_state: st.session_state.print_now = False

def footer_soporte():
    st.markdown("""<div style="position:fixed; bottom:0; left:0; width:100%; background:#002244; padding:10px 0; text-align:center; z-index:999;">
    <p style="margin:0; color:#99ccff; font-size:11px; font-weight:bold;">Soporte Técnico de Control Soporte.DramirenG:</p>
    <p style="margin:0; color:white; font-size:11px;">📞 Celular: 959237626 | ✉️ Correo: Soporte.DramirenG@hotmail.com</p></div><div style="height:80px;"></div>""", unsafe_allow_html=True)

if not st.session_state.logged:
    st.markdown("<style>.stApp{background:#f2f3f7 !important;} div[data-testid='stTextInput'] input{background:white !important; color:#111827 !important; border:2px solid #111827 !important; border-radius:12px !important; height:50px !important;} div[data-testid='stTextInput'] label p{color:#111827 !important; font-weight:800 !important;}</style>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns([1,1.2,1])
    with c2:
        st.markdown("<br><br><h1 style='text-align:center; color:#111827;'>Bienvenido</h1>", unsafe_allow_html=True)
        u = st.text_input("USUARIO", placeholder="Ingresa tu usuario")
        p = st.text_input("CLAVE", type="password", placeholder="Ingresa tu clave")
        if st.button("🔐 Entrar", use_container_width=True, type="primary"):
            if u=="admin" and p=="dramireng123": 
                st.session_state.logged=True; st.rerun()
            else:
                st.error("Usuario o clave incorrecta")
    footer_soporte(); st.stop()

st.markdown("""
<style>
.stApp{background:#f8f9fb !important;} 
section[data-testid="stSidebar"]{background:white !important;} 
section[data-testid="stSidebar"] *{color:#111827 !important;}

div[data-testid="stTextInput"] label p, div[data-testid="stSelectbox"] label p{color:#111827 !important; font-weight:800 !important; font-size:11px !important;}
div[data-testid="stTextInput"] input{background:white !important; color:#111827 !important; border:1.5px solid #d1d5db !important; border-radius:10px !important;}
div[data-baseweb="select"] > div{background:white !important; border:1.5px solid #d1d5db !important; border-radius:10px !important;}

/* --- CAJAS AMARILLO CLARO COMO PIDES --- */
section[data-testid="stSidebar"] div[data-testid="stFileUploader"]{
    background:#fefce8 !important; 
    border:1.5px solid #fde68a !important; 
    border-radius:12px !important;
}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] section{
    background:#fefce8 !important; 
    border:1px dashed #facc15 !important;
    border-radius:10px !important;
}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] button{
    background:#fde047 !important; /* AMARILLO CLARO */
    color:#422006 !important; 
    border:1px solid #facc15 !important;
    border-radius:8px !important;
    font-weight:700 !important;
}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] button div{
    color:#422006 !important;
}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] small{
    color:#854d0e !important;
}
</style>
""", unsafe_allow_html=True)
col_titulo, col_imp, col_limpiar, col_logout = st.columns([4.2, 1.4, 1.4, 1.4])
with col_titulo: 
    st.markdown("<h1 style='margin:0; color:#111827;'>Etiquetas <span style='color:#ff7a5c'>PRO</span> <span style='font-size:12px; background:#111827; color:white; padding:4px 12px; border-radius:20px;'>v2.0</span></h1>", unsafe_allow_html=True)
with col_imp:
    if st.button("🖨️ Imprimir", use_container_width=True, type="primary"):
        if st.session_state.data: st.session_state.print_now = True
        else: st.toast("Agrega bultos primero")
with col_limpiar:
    if st.button("🗑️ Limpiar Lista", use_container_width=True):
        st.session_state.data=[]; st.rerun()
with col_logout:
    if st.button("🚪 Cerrar sesión", use_container_width=True): st.session_state.logged=False; st.rerun()

with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    st.markdown("**FORMATO**")
    formato = st.radio("FORMATO", ["A4 VERTICAL - 4 POR HOJA", "A4 HORIZONTAL - TODA LA HOJA", "TÉRMICA 100X150"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**TU LOGO DE TU EMPRESA (arriba derecha)**")
    logo_empresa = st.file_uploader("TU LOGO DE TU EMPRESA", type=["png","jpg","jpeg"], key="dg", label_visibility="collapsed")
    st.markdown("**LOGO DE MARCAS ABAJO (Opcional)**")
    logo_marcas = st.file_uploader("Marcas abajo", type=["png","jpg","jpeg"], key="marcas", label_visibility="collapsed")
    st.markdown("<p style='font-size:10px; color:#6b7280;'>El cliente sube aquí su logo.</p>", unsafe_allow_html=True)

# TODAS LAS PROVINCIAS DEL PERU CON AUTOCOMPLETAR
PROVINCIAS_PERU = sorted([
    "AMAZONAS - CHACHAPOYAS","AMAZONAS - BAGUA","AMAZONAS - UTCUBAMBA",
    "ANCASH - HUARAZ","ANCASH - CHIMBOTE","ANCASH - HUARMEY","ANCASH - CARAZ","ANCASH - CASMA",
    "APURIMAC - ABANCAY","APURIMAC - ANDAHUAYLAS",
    "AREQUIPA - AREQUIPA","AREQUIPA - CAMANA","AREQUIPA - MOLLENDO",
    "AYACUCHO - AYACUCHO","AYACUCHO - HUANTA",
    "CAJAMARCA - CAJAMARCA","CAJAMARCA - JAEN","CAJAMARCA - CUTERVO","CAJAMARCA - CHOTA",
    "CALLAO - CALLAO","CUSCO - CUSCO","CUSCO - SICUANI","CUSCO - QUILLABAMBA",
    "HUANCAVELICA - HUANCAVELICA","HUANUCO - HUANUCO","HUANUCO - TINGO MARIA",
    "ICA - ICA","ICA - CHINCHA","ICA - PISCO","ICA - NAZCA","ICA - PALPA",
    "JUNIN - HUANCAYO","JUNIN - TARMA","JUNIN - JAUJA","JUNIN - LA OROYA","JUNIN - CHANCHAMAYO","JUNIN - SATIPO",
    "LA LIBERTAD - TRUJILLO","LA LIBERTAD - CHEPEN","LA LIBERTAD - PACASMAYO","LA LIBERTAD - HUAMACHUCO","LA LIBERTAD - VIRU",
    "LAMBAYEQUE - CHICLAYO","LAMBAYEQUE - LAMBAYEQUE","LAMBAYEQUE - FERREÑAFE",
    "LIMA - LIMA","LIMA - HUARAL","LIMA - HUACHO","LIMA - CAÑETE","LIMA - BARRANCA","LIMA - CHOSICA","LIMA - HUAROCHIRI",
    "LORETO - IQUITOS","LORETO - YURIMAGUAS","LORETO - NAUTA",
    "MADRE DE DIOS - PUERTO MALDONADO","MOQUEGUA - MOQUEGUA","MOQUEGUA - ILO",
    "PASCO - CERRO DE PASCO","PASCO - OXAPAMPA",
    "PIURA - PIURA","PIURA - SULLANA","PIURA - PAITA","PIURA - TALARA","PIURA - SECHURA","PIURA - CHULUCANAS","PIURA - AYABACA","PIURA - HUANCABAMBA",
    "PUNO - PUNO","PUNO - JULIACA","PUNO - ILAVE","PUNO - AZANGARO",
    "SAN MARTIN - TARAPOTO","SAN MARTIN - MOYOBAMBA","SAN MARTIN - RIOJA","SAN MARTIN - TOCACHE",
    "TACNA - TACNA","TUMBES - TUMBES","TUMBES - ZARUMILLA","UCAYALI - PUCALLPA","UCAYALI - ATALAYA"
])

c1,c2 = st.columns([1,2.5])
with c1: dni = st.text_input("DNI/RUC", value="75098930")
with c2: nombre = st.text_input("NOMBRE", value="DAVID GRABIEL RAMIREZ NIEVES")
c3,c4,c5,c6 = st.columns([1.2,1.2,0.4,0.4])
with c3: 
    destino = st.selectbox("DESTINO (Escribe para autocompletar)", PROVINCIAS_PERU, index=PROVINCIAS_PERU.index("PIURA - SULLANA") if "PIURA - SULLANA" in PROVINCIAS_PERU else 0)
with c4: celular = st.text_input("CELULAR", value="959237626")
with c5: bulto = st.number_input("BULTO", 1, value=1)
with c6: total = st.number_input("TOTAL", 1, value=4)

b1,b2 = st.columns(2)
with b1:
    if st.button("🔍 Buscar DNI", use_container_width=True): st.toast("Buscando...")
with b2:
    if st.button("➕ Agregar", use_container_width=True):
        for i in range(bulto, total+1): st.session_state.data.append({"DNI/RUC":dni,"NOMBRE":nombre,"DESTINO":destino,"CELULAR":celular,"B1":i,"B2":total})
        st.rerun()

def generar_pdf_bytes(logo_emp_file, logo_marcas_file):
    buffer = io.BytesIO(); c = canvas.Canvas(buffer, pagesize=A4); w,h = A4; lh = h/4
    for idx, row in enumerate(st.session_state.data):
        pos = idx % 4; y_top = h - (pos * lh)
        c.setStrokeColorRGB(0.8,0.8,0.8); c.rect(20, y_top-lh+10, w-40, lh-20)
        if logo_emp_file:
            try: img_dg = Image.open(logo_emp_file); b=io.BytesIO(); img_dg.save(b, format='PNG'); b.seek(0); c.drawImage(ImageReader(b), w-110, y_top-45, width=70, height=28, preserveAspectRatio=True)
            except: pass
        c.setFont("Helvetica-Bold",14); c.drawString(30,y_top-30,f"DESTINO: {row['DESTINO']}")
        c.setFont("Helvetica",10); c.drawString(30,y_top-50,f"{row['NOMBRE']}"); c.drawString(30,y_top-65,f"DNI: {row['DNI/RUC']} | CEL: {row['CELULAR']}")
        c.setFont("Helvetica-Bold",16); c.drawString(30,y_top-90,f"BULTO {row['B1']} DE {row['B2']}")
        qr_img = qrcode.make(f"{row['DESTINO']}-{row['B1']}/{row['B2']}"); qb=io.BytesIO(); qr_img.save(qb, format='PNG'); qb.seek(0); c.drawImage(ImageReader(qb), w-105, y_top-115, width=60, height=60)
        if logo_marcas_file:
            try: img_m = Image.open(logo_marcas_file); bm=io.BytesIO(); img_m.save(bm, format='PNG'); bm.seek(0); c.drawImage(ImageReader(bm), 30, y_top-lh+22, width=w-80, height=22, preserveAspectRatio=True)
            except: pass
        if pos==3: c.showPage()
    c.save(); return buffer.getvalue()

if st.session_state.print_now and st.session_state.data:
    pdf_bytes = generar_pdf_bytes(logo_empresa, logo_marcas); b64 = base64.b64encode(pdf_bytes).decode()
    st.markdown("### 🖨️ Vista Previa - Imprimiendo directo...")
    st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600"></iframe>', unsafe_allow_html=True)
    st.components.v1.html(f"""<html><body><script>
        var pdfData = "data:application/pdf;base64,{b64}"; var iframe = document.createElement('iframe'); iframe.style.display='none'; iframe.src=pdfData; document.body.appendChild(iframe);
        iframe.onload = function(){{ setTimeout(function(){{ iframe.contentWindow.focus(); iframe.contentWindow.print(); }}, 800); }};
        </script></body></html>""", height=0)
    st.session_state.print_now = False

if st.session_state.data:
    st.markdown("""
    <div style="background:white; border:1.5px solid #e5e7eb; border-radius:12px 12px 0 0; padding:12px 15px; margin-top:15px;">
        <h4 style="margin:0; color:#111827; font-weight:800;">📦 BULTOS AGREGADOS - LISTA PARA IMPRIMIR</h4>
    </div>
    """, unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(st.session_state.data), use_container_width=True, hide_index=True)
else:
    st.markdown("""
    <div style="background:white; border:1.5px dashed #d1d5db; border-radius:12px; padding:20px; margin-top:15px; text-align:center;">
        <h4 style="margin:0; color:#111827;">📦 BULTOS AGREGADOS</h4>
        <p style="margin:0; color:#6b7280;">Aún no hay bultos, agrega arriba</p>
    </div>
    """, unsafe_allow_html=True)

footer_soporte()
