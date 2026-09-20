import streamlit as st
import pandas as pd
import qrcode, io, base64, requests
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

st.set_page_config(page_title="Etiquetas PRO", layout="wide", page_icon="🏷️")
if 'logged' not in st.session_state: st.session_state.logged=False
if 'data' not in st.session_state: st.session_state.data=[]
if 'print_now' not in st.session_state: st.session_state.print_now=False
for k,v in [("dni",""),("nombre",""),("factura",""),("nombre2",""),("dni2",""),("celular",""),("bulto",1),("total",1)]:
    if k not in st.session_state: st.session_state[k]=v

def buscar_dni_ruc(doc, token):
    doc=doc.strip()
    # 1. Si tiene token apis.net.pe
    if token:
        try:
            if len(doc)==8:
                r=requests.get(f"https://api.apis.net.pe/v2/reniec/dni?numero={doc}", headers={"Authorization":f"Bearer {token}"}, timeout=8)
                if r.status_code==200:
                    d=r.json()
                    return f"{d.get('nombres','')} {d.get('apellidoPaterno','')} {d.get('apellidoMaterno','')}".strip()
            if len(doc)==11:
                r=requests.get(f"https://api.apis.net.pe/v2/sunat/ruc?numero={doc}", headers={"Authorization":f"Bearer {token}"}, timeout=8)
                if r.status_code==200: return r.json().get('nombre') or r.json().get('razonSocial')
        except: pass
    # 2. API GRATIS sin token - DECOLECTA / API PERU
    apis_libres = [
        f"https://api.decolecta.com/v1/reniec/dni?numero={doc}" if len(doc)==8 else f"https://api.decolecta.com/v1/sunat/ruc?numero={doc}",
        f"https://api.apis.net.pe/v1/dni?numero={doc}" if len(doc)==8 else f"https://api.apis.net.pe/v1/ruc?numero={doc}",
        f"https://dniruc.apisperu.com/api/v1/dni/{doc}" if len(doc)==8 else f"https://dniruc.apisperu.com/api/v1/ruc/{doc}"
    ]
    for url in apis_libres:
        try:
            r=requests.get(url, timeout=6)
            if r.status_code==200:
                d=r.json()
                if len(doc)==8:
                    if 'nombres' in d: return f"{d.get('nombres','')} {d.get('apellidoPaterno','')} {d.get('apellidoMaterno','')}".strip()
                    if 'nombre' in d: return d['nombre']
                    if 'data' in d: return d['data']
                else:
                    if 'razonSocial' in d: return d['razonSocial']
                    if 'nombre' in d: return d['nombre']
        except: continue
    return None

def footer_soporte():
    st.markdown("""<div style="position:fixed; bottom:0; left:0; width:100%; background:#002244; padding:8px 0; text-align:center; z-index:999;">
    <p style="margin:0; color:#99ccff; font-size:11px; font-weight:bold;">Soporte Técnico Soporte.DramirenG:</p>
    <p style="margin:0; color:white; font-size:11px;">📞 959237626 | ✉️ Soporte.DramirenG@hotmail.com</p></div><div style="height:70px;"></div>""", unsafe_allow_html=True)

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

# CSS QUE QUITA LO NEGRO Y QUITA ESPACIOS
st.markdown("""
<style>
.stApp{background:#f8f9fb!important;}
section[data-testid="stSidebar"]{background:white!important; border-right:1px solid #e5e7eb!important; padding-top:10px!important;}
section[data-testid="stSidebar"] *{color:#111827!important;}
div[data-testid="stTextInput"] label p, div[data-testid="stSelectbox"] label p, div[data-testid="stNumberInput"] label p{color:#111827!important; font-weight:800!important; font-size:11px!important;}
div[data-testid="stTextInput"] input{background:white!important; color:#111827!important; border:1.5px solid #d1d5db!important; border-radius:10px!important; height:44px!important;}
/* ARREGLA DESTINO NEGRO DE TU FOTO */
div[data-baseweb="select"] > div{background:white!important; border:1.5px solid #d1d5db!important; color:#111827!important; min-height:44px!important;}
div[data-baseweb="select"] span{color:#111827!important; font-weight:600!important; background:white!important;}
div[data-baseweb="select"] div{background:white!important;}
div[data-testid="stNumberInput"] input{background:white!important; color:#111827!important; border:1.5px solid #d1d5db!important;}
div[data-testid="stNumberInput"] button{background:white!important; border:1px solid #d1d5db!important;}
div[data-testid="stNumberInput"] button svg{fill:#111827!important;}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"]{background:#fefce8!important; border:1.5px solid #fde68a!important; border-radius:12px!important; margin-top:5px!important;}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] section{background:#fefce8!important; border:1px dashed #facc15!important; padding:5px!important;}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] button{background:#fde047!important; color:#422006!important; border:1px solid #facc15!important; font-weight:700!important;}
/* QUITAR ESPACIOS GRANDES */
section[data-testid="stSidebar"].stMarkdown{margin-bottom:2px!important;}
div[data-testid="stDataFrame"]{background:white!important; border:1.5px solid #e5e7eb!important;}
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
    st.markdown("<p style='font-size:11px; font-weight:800; margin:0;'>FORMATO</p>", unsafe_allow_html=True)
    formato=st.radio("FORMATO", ["A4 VERTICAL - 4 POR HOJA","A4 HORIZONTAL - 2 POR HOJA","TÉRMICA 100X150"], label_visibility="collapsed")
    st.markdown("<p style='font-size:11px; font-weight:800; margin:10px 0 2px 0;'>🔑 API DNI/RUC</p>", unsafe_allow_html=True)
    api_token=st.text_input("TOKEN API", type="password", placeholder="Token opcional - funciona sin token", label_visibility="collapsed")
    st.markdown("<p style='font-size:10px; color:#6b7280; margin:0;'>Funciona con o sin token (apis.net.pe)</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:11px; font-weight:800; margin:12px 0 2px 0;'>TU LOGO DE TU EMPRESA (arriba derecha)</p>", unsafe_allow_html=True)
    logo_empresa=st.file_uploader("TU LOGO", type=["png","jpg","jpeg"], key="logo_emp", label_visibility="collapsed")
    st.markdown("<p style='font-size:11px; font-weight:800; margin:8px 0 2px 0;'>LOGO DE MARCAS ABAJO (Opcional)</p>", unsafe_allow_html=True)
    logo_marcas=st.file_uploader("Marcas", type=["png","jpg","jpeg"], key="logo_mar", label_visibility="collapsed")

PROVINCIAS_PERU=sorted(["PIURA - SULLANA","PIURA - PIURA","PIURA - PAITA","PIURA - TALARA","LIMA - LIMA","LIMA - HUACHO","LAMBAYEQUE - CHICLAYO","LA LIBERTAD - TRUJILLO","TUMBES - TUMBES","ANCASH - CHIMBOTE","AREQUIPA - AREQUIPA","CUSCO - CUSCO","ICA - ICA","JUNIN - HUANCAYO","LORETO - IQUITOS","SAN MARTIN - TARAPOTO","UCAYALI - PUCALLPA","PUNO - JULIACA","TACNA - TACNA","CAJAMARCA - CAJAMARCA"])

# FUNCIONES PARA NO DAR ERROR DE WIDGET
def buscar_click():
    doc = st.session_state.w_dni.strip()
    token = st.session_state.get("api_token_input","")
    if not doc:
        st.toast("Escribe DNI/RUC")
        return
    res = buscar_dni_ruc(doc, token)
    if res:
        st.session_state.w_nombre = res
        st.toast(f"Encontrado: {res}")
    else:
        st.toast("No encontrado")

def agregar_click():
    b = st.session_state.w_bulto
    t = st.session_state.w_total
    if not st.session_state.w_nombre:
        st.toast("Falta nombre")
        return
    for i in range(b, t+1):
        st.session_state.data.append({
            "DESTINO": st.session_state.w_destino,
            "BULTOS": f"{i}/{t}",
            "ATT 1": st.session_state.w_nombre,
            "DNI 1": st.session_state.w_dni,
            "FACTURA": st.session_state.w_factura,
            "ATT 2": st.session_state.w_nombre2,
            "DNI 2": st.session_state.w_dni2,
            "CELULAR": st.session_state.w_celular
        })
    # LIMPIAR SIN ERROR
    st.session_state.w_dni=""
    st.session_state.w_nombre=""
    st.session_state.w_factura=""
    st.session_state.w_nombre2=""
    st.session_state.w_dni2=""
    st.session_state.w_celular=""
    st.session_state.w_bulto=1
    st.session_state.w_total=1

st.markdown("<h3 style='color:#111827; margin-top:15px;'>📦 Datos del cliente</h3>", unsafe_allow_html=True)

c1,c2,c3,c4=st.columns([1.1,1.9,1.1,0.6])
with c1: st.text_input("DNI/RUC 1", key="w_dni", placeholder="75098930")
with c2: st.text_input("ATT 1 / NOMBRE PRINCIPAL", key="w_nombre")
with c3: st.text_input("N° FACTURA / GUIA", key="w_factura", placeholder="F001-XXXXX")
with c4:
    st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
    st.button("🔍 Buscar", use_container_width=True, type="primary", on_click=buscar_click)

c5,c6,c7=st.columns([2,1.2,1])
with c5: st.text_input("ATT 2 / SEGUNDO NOMBRE (Opcional)", key="w_nombre2")
with c6: st.text_input("DNI 2", key="w_dni2")
with c7: st.text_input("CELULAR", key="w_celular")

c8,c9,c10,c11=st.columns([1.6,0.6,0.6,0.7])
with c8: st.selectbox("DESTINO (escribe para filtrar)", PROVINCIAS_PERU, key="w_destino")
with c9: st.number_input("BULTO INICIO", min_value=1, step=1, key="w_bulto")
with c10: st.number_input("TOTAL", min_value=1, step=1, key="w_total")
with c11:
    st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
    st.button("➕ Agregar", use_container_width=True, type="primary", on_click=agregar_click)

def generar_pdf_bytes(logo_emp, logo_mar, formato_sel):
    is_horizontal = "HORIZONTAL" in formato_sel
    pagesize = landscape(A4) if is_horizontal else A4
    buffer=io.BytesIO(); c=canvas.Canvas(buffer, pagesize=pagesize); w,h=pagesize
    items_por_hoja = 2 if is_horizontal else 4
    lh = h/items_por_hoja
    for idx,row in enumerate(st.session_state.data):
        pos=idx%items_por_hoja; y_top=h-(pos*lh)
        c.setStrokeColorRGB(0,0,0); c.setLineWidth(1.5); c.rect(10, y_top-lh+10, w-20, lh-20)
        c.setFont("Helvetica-Bold",22); c.drawString(20, y_top-35, f"{row['DESTINO'].split('-')[-1].strip()}")
        c.setFont("Helvetica-Bold",14); c.drawString(w/2-20, y_top-35, f"({row['BULTOS']})")
        c.line(15, y_top-45, w-115, y_top-45)
        c.setFont("Helvetica-Bold",11); c.drawString(20, y_top-62, f"ATT: {row['ATT 1']}")
        c.setFont("Helvetica",9); c.drawString(20, y_top-76, f"DNI/RUC: {row['DNI 1']} | FACTURA: {row['FACTURA']}")
        if row['ATT 2']:
            c.setFont("Helvetica-Bold",10); c.drawString(20, y_top-92, f"ATT 2: {row['ATT 2']}")
            c.setFont("Helvetica",9); c.drawString(20, y_top-105, f"DNI 2: {row['DNI 2']}")
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
        qr=qrcode.make(f"{row['DESTINO']}-{row['BULTOS']}-{row['DNI 1']}"); qb=io.BytesIO(); qr.save(qb,format='PNG'); qb.seek(0)
        c.drawImage(ImageReader(qb), w-70, y_top-lh+18, width=50, height=50)
        if pos==items_por_hoja-1: c.showPage()
    c.save(); return buffer.getvalue()

if st.session_state.print_now and st.session_state.data:
    pdf_bytes=generar_pdf_bytes(logo_empresa, logo_marcas, formato); b64=base64.b64encode(pdf_bytes).decode()
    st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="650"></iframe>', unsafe_allow_html=True)
    st.components.v1.html(f"""<html><body><script>var pdfData="data:application/pdf;base64,{b64}"; var i=document.createElement('iframe'); i.style.display='none'; i.src=pdfData; document.body.appendChild(i); i.onload=function(){{setTimeout(function(){{i.contentWindow.focus(); i.contentWindow.print();}},800);}};</script></body></html>""", height=0)
    st.session_state.print_now=False

if st.session_state.data:
    st.markdown(f"<div style='background:white; border:1.5px solid #111827; padding:12px; border-radius:12px 12px 0 0;'><b style='color:#111827; font-size:14px;'>📦 BULTOS AGREGADOS - {len(st.session_state.data)} etiquetas | FORMATO: {formato}</b></div>", unsafe_allow_html=True)
    df=pd.DataFrame(st.session_state.data)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Aún no hay bultos - agrega clientes arriba")

footer_soporte()
