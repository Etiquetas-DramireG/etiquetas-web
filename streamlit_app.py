import streamlit as st
import pandas as pd
import qrcode, io, base64
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

st.set_page_config(page_title="Etiquetas PRO", layout="wide", page_icon="🏷️")
if 'logged' not in st.session_state: st.session_state.logged=False
if 'data' not in st.session_state: st.session_state.data=[]
if 'print_now' not in st.session_state: st.session_state.print_now=False

# INICIALIZAR BIEN (TEXTO VACIO, NUMEROS EN 1)
if "dni" not in st.session_state: st.session_state.dni=""
if "nombre" not in st.session_state: st.session_state.nombre=""
if "factura" not in st.session_state: st.session_state.factura=""
if "nombre2" not in st.session_state: st.session_state.nombre2=""
if "dni2" not in st.session_state: st.session_state.dni2=""
if "celular" not in st.session_state: st.session_state.celular=""
if "bulto" not in st.session_state: st.session_state.bulto=1
if "total" not in st.session_state: st.session_state.total=1

def footer_soporte():
    st.markdown("""<div style="position:fixed; bottom:0; left:0; width:100%; background:#002244; padding:10px 0; text-align:center; z-index:999;">
    <p style="margin:0; color:#99ccff; font-size:11px; font-weight:bold;">Soporte Técnico de Control Soporte.DramirenG:</p>
    <p style="margin:0; color:white; font-size:11px;">📞 Celular: 959237626 | ✉️ Correo: Soporte.DramirenG@hotmail.com</p></div><div style="height:80px;"></div>""", unsafe_allow_html=True)

if not st.session_state.logged:
    st.markdown("<style>.stApp{background:#f2f3f7!important;} div[data-testid='stTextInput'] input{background:white!important; color:#111827!important; border:2px solid #111827!important; border-radius:12px!important; height:50px!important;} div[data-testid='stTextInput'] label p{color:#111827!important; font-weight:800!important;}</style>", unsafe_allow_html=True)
    c1,c2,c3=st.columns([1,1.2,1])
    with c2:
        st.markdown("<br><br><h1 style='text-align:center; color:#111827;'>Bienvenido</h1>", unsafe_allow_html=True)
        u=st.text_input("USUARIO", placeholder="Ingresa tu usuario"); p=st.text_input("CLAVE", type="password", placeholder="Ingresa tu clave")
        if st.button("🔐 Entrar", use_container_width=True, type="primary"):
            if u=="admin" and p=="dramireng123": st.session_state.logged=True; st.rerun()
            else: st.error("Usuario o clave incorrecta")
    footer_soporte(); st.stop()

st.markdown("""
<style>
.stApp{background:#f8f9fb!important;}
section[data-testid="stSidebar"]{background:white!important;}
section[data-testid="stSidebar"] *{color:#111827!important;}
div[data-testid="stTextInput"] label p, div[data-testid="stSelectbox"] label p, div[data-testid="stNumberInput"] label p{color:#111827!important; font-weight:800!important; font-size:11px!important;}
div[data-testid="stTextInput"] input{background:white!important; color:#111827!important; border:1.5px solid #d1d5db!important; border-radius:10px!important; height:44px!important;}
div[data-baseweb="select"] > div{background:white!important; border:1.5px solid #d1d5db!important; border-radius:10px!important;}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"]{background:#fefce8!important; border:1.5px solid #fde68a!important; border-radius:12px!important;}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] section{background:#fefce8!important; border:1px dashed #facc15!important;}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] button{background:#fde047!important; color:#422006!important; border:1px solid #facc15!important; font-weight:700!important;}
</style>
""", unsafe_allow_html=True)

col_titulo, col_imp, col_limpiar, col_logout = st.columns([4.2, 1.4, 1.4, 1.4])
with col_titulo: st.markdown("<h1 style='margin:0; color:#111827;'>Etiquetas <span style='color:#ff7a5c'>PRO</span></h1>", unsafe_allow_html=True)
with col_imp:
    if st.button("🖨️ Imprimir", use_container_width=True, type="primary"):
        if st.session_state.data: st.session_state.print_now=True
        else: st.toast("Agrega bultos")
with col_limpiar:
    if st.button("🗑️ Limpiar Lista", use_container_width=True): st.session_state.data=[]; st.rerun()
with col_logout:
    if st.button("🚪 Cerrar sesión", use_container_width=True): st.session_state.logged=False; st.rerun()

with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    formato=st.radio("FORMATO", ["A4 VERTICAL - 4 POR HOJA","TÉRMICA 100X150"], label_visibility="collapsed")
    st.markdown("**TU LOGO DE TU EMPRESA (arriba derecha)**")
    logo_empresa=st.file_uploader("TU LOGO", type=["png","jpg","jpeg"], key="logo_emp", label_visibility="collapsed")
    st.markdown("**LOGO DE MARCAS ABAJO (Opcional)**")
    logo_marcas=st.file_uploader("Marcas", type=["png","jpg","jpeg"], key="logo_mar", label_visibility="collapsed")

PROVINCIAS_PERU=sorted(["PIURA - SULLANA","PIURA - PIURA","PIURA - PAITA","PIURA - TALARA","LIMA - LIMA","LAMBAYEQUE - CHICLAYO","LA LIBERTAD - TRUJILLO","TUMBES - TUMBES","ANCASH - CHIMBOTE","AREQUIPA - AREQUIPA","CUSCO - CUSCO","ICA - ICA","JUNIN - HUANCAYO","LORETO - IQUITOS","SAN MARTIN - TARAPOTO","UCAYALI - PUCALLPA","PUNO - JULIACA","TACNA - TACNA","CAJAMARCA - CAJAMARCA"])

st.markdown("#### 📝 Datos del cliente")
c1,c2,c3=st.columns([1.2,2,1.2])
with c1: dni=st.text_input("DNI/RUC 1", key="dni")
with c2: nombre=st.text_input("ATT 1 / NOMBRE PRINCIPAL", key="nombre")
with c3: factura=st.text_input("N° FACTURA / GUIA", key="factura", placeholder="F001-XXXXX")

c4,c5,c6=st.columns([2,1.2,1])
with c4: nombre2=st.text_input("ATT 2 / SEGUNDO NOMBRE (Opcional)", key="nombre2")
with c5: dni2=st.text_input("DNI 2", key="dni2")
with c6: celular=st.text_input("CELULAR", key="celular")

c7,c8,c9=st.columns([1.5,0.6,0.6])
with c7: destino=st.selectbox("DESTINO", PROVINCIAS_PERU)
with c8: bulto=st.number_input("BULTO INICIO", min_value=1, step=1, key="bulto")
with c9: total=st.number_input("TOTAL", min_value=1, step=1, key="total")

if st.button("➕ Agregar a la Lista", use_container_width=True, type="primary"):
    for i in range(bulto, total+1):
        st.session_state.data.append({"DESTINO":destino,"B1":i,"B2":total,"NOMBRE":nombre,"DNI":dni,"FACTURA":factura,"NOMBRE2":nombre2,"DNI2":dni2,"CELULAR":celular})
    st.session_state.dni=""; st.session_state.nombre=""; st.session_state.factura=""; st.session_state.nombre2=""; st.session_state.dni2=""; st.session_state.celular=""
    st.session_state.bulto=1; st.session_state.total=1
    st.rerun()

def generar_pdf_bytes(logo_emp, logo_mar):
    buffer=io.BytesIO(); c=canvas.Canvas(buffer, pagesize=A4); w,h=A4; lh=h/4
    for idx,row in enumerate(st.session_state.data):
        pos=idx%4; y_top=h-(pos*lh)
        c.setStrokeColorRGB(0,0,0); c.setLineWidth(1.5); c.rect(10, y_top-lh+10, w-20, lh-20)
        c.setFont("Helvetica-Bold",22); c.drawString(20, y_top-35, f"{row['DESTINO'].split('-')[-1].strip()}")
        c.setFont("Helvetica-Bold",14); c.drawString(w/2-20, y_top-35, f"({row['B1']}/{row['B2']})")
        c.line(15, y_top-45, w-115, y_top-45)
        c.setFont("Helvetica-Bold",11); c.drawString(20, y_top-62, f"ATT: {row['NOMBRE']}")
        c.setFont("Helvetica",9); c.drawString(20, y_top-76, f"DNI/RUC: {row['DNI']} | FACTURA: {row['FACTURA']}")
        if row['NOMBRE2']:
            c.setFont("Helvetica-Bold",10); c.drawString(20, y_top-92, f"ATT 2: {row['NOMBRE2']}")
            c.setFont("Helvetica",9); c.drawString(20, y_top-105, f"DNI 2: {row['DNI2']}")
            c.setFont("Helvetica-Bold",10); c.drawString(20, y_top-120, f"CELULAR: {row['CELULAR']}")
        else:
            c.setFont("Helvetica-Bold",10); c.drawString(20, y_top-92, f"CELULAR: {row['CELULAR']}")
        if logo_emp:
            try:
                im=Image.open(logo_emp); b=io.BytesIO(); im.save(b,format='PNG'); b.seek(0)
                c.drawImage(ImageReader(b), w-110, y_top-110, width=90, height=75, preserveAspectRatio=True, mask='auto')
            except: pass
        if logo_mar:
            try:
                im2=Image.open(logo_mar); bm=io.BytesIO(); im2.save(bm,format='PNG'); bm.seek(0)
                c.drawImage(ImageReader(bm), 25, y_top-lh+30, width=300, height=22, preserveAspectRatio=True, mask='auto')
            except: pass
        qr=qrcode.make(f"{row['DESTINO']}-{row['B1']}/{row['B2']}-{row['DNI']}"); qb=io.BytesIO(); qr.save(qb,format='PNG'); qb.seek(0)
        c.drawImage(ImageReader(qb), w-70, y_top-lh+18, width=50, height=50)
        if pos==3: c.showPage()
    c.save(); return buffer.getvalue()

if st.session_state.print_now and st.session_state.data:
    pdf_bytes=generar_pdf_bytes(logo_empresa, logo_marcas); b64=base64.b64encode(pdf_bytes).decode()
    st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="650"></iframe>', unsafe_allow_html=True)
    st.components.v1.html(f"""<html><body><script>var pdfData="data:application/pdf;base64,{b64}"; var i=document.createElement('iframe'); i.style.display='none'; i.src=pdfData; document.body.appendChild(i); i.onload=function(){{setTimeout(function(){{i.contentWindow.focus(); i.contentWindow.print();}},800);}};</script></body></html>""", height=0)
    st.session_state.print_now=False

if st.session_state.data:
    st.markdown(f"<div style='background:white; border:1.5px solid #e5e7eb; padding:12px; border-radius:12px 12px 0 0;'><b style='color:#111827'>📦 BULTOS AGREGADOS - {len(st.session_state.data)} etiquetas</b></div>", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(st.session_state.data), use_container_width=True, hide_index=True)
else:
    st.info("Aún no hay bultos")

footer_soporte()
