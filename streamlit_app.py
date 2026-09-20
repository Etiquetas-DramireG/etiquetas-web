import streamlit as st
import pandas as pd
import qrcode, io, base64, requests
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

st.set_page_config(page_title="Etiquetas PRO", layout="wide", page_icon="🏷️")

# ESTADOS INICIALES
if 'logged' not in st.session_state: st.session_state.logged=False
if 'data' not in st.session_state: st.session_state.data=[]
if 'print_now' not in st.session_state: st.session_state.print_now=False
for k in ["w_dni","w_nombre","w_factura","w_nombre2","w_dni2","w_celular"]:
    if k not in st.session_state: st.session_state[k]=""
for k in ["w_bulto","w_total"]:
    if k not in st.session_state: st.session_state[k]=1
if "w_destino" not in st.session_state: st.session_state.w_destino="LIMA - LIMA"
if "api_token_input" not in st.session_state: st.session_state.api_token_input=""

def buscar_dni_ruc(doc, token):
    doc=doc.strip()
    # con token apis.net.pe
    if token:
        try:
            if len(doc)==8:
                r=requests.get(f"https://api.apis.net.pe/v2/reniec/dni?numero={doc}", headers={"Authorization":f"Bearer {token}"}, timeout=8)
                if r.status_code==200:
                    d=r.json()
                    nombre = f"{d.get('nombres','')} {d.get('apellidoPaterno','')} {d.get('apellidoMaterno','')}".strip()
                    if nombre: return nombre
            if len(doc)==11:
                r=requests.get(f"https://api.apis.net.pe/v2/sunat/ruc?numero={doc}", headers={"Authorization":f"Bearer {token}"}, timeout=8)
                if r.status_code==200:
                    return r.json().get('nombre') or r.json().get('razonSocial')
        except: pass
    # sin token - intenta gratis
    try:
        if len(doc)==8:
            r=requests.get(f"https://api.decolecta.com/v1/reniec/dni?numero={doc}", headers={"Authorization":f"Bearer {token}"} if token else {}, timeout=6)
            if r.status_code==200 and r.json().get('first_name'):
                d=r.json()
                return f"{d.get('first_name','')} {d.get('first_last_name','')} {d.get('second_last_name','')}"
    except: pass
    return None

def buscar_click():
    token = st.session_state.api_token_input
    # BUSCAR DNI 1 -> ATT 1
    doc1 = st.session_state.w_dni.strip()
    if doc1:
        res1 = buscar_dni_ruc(doc1, token)
        if res1: 
            st.session_state.w_nombre = res1
            st.toast(f"DNI 1: {res1}")
    
    # BUSCAR DNI 2 -> ATT 2 CON EL MISMO BOTON
    doc2 = st.session_state.w_dni2.strip()
    if doc2:
        res2 = buscar_dni_ruc(doc2, token)
        if res2:
            st.session_state.w_nombre2 = res2
            st.toast(f"DNI 2: {res2}")
    
    if not doc1 and not doc2:
        st.toast("Escribe DNI 1 o DNI 2")
def agregar_click():
    if not st.session_state.w_nombre: st.toast("Falta ATT 1"); return
    b = st.session_state.w_bulto
    t = st.session_state.w_total
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
    st.session_state.w_dni=""; st.session_state.w_nombre=""; st.session_state.w_factura=""
    st.session_state.w_nombre2=""; st.session_state.w_dni2=""; st.session_state.w_celular=""
    st.session_state.w_bulto=1; st.session_state.w_total=1

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

st.markdown("""
<style>
.stApp{background:#f8f9fb!important;}
section[data-testid="stSidebar"]{background:#ffffff!important;}
section[data-testid="stSidebar"] *{color:#111827!important;}

/* LABELS NEGROS BIEN VISIBLES */
div[data-testid="stTextInput"] label p, 
div[data-testid="stSelectbox"] label p, 
div[data-testid="stNumberInput"] label p {
    color:#000000!important; font-weight:900!important; font-size:13px!important; opacity:1!important;
}
h3{color:#000000!important;}

/* CAJAS BLANCAS CON BORDE NEGRO Y LETRA NEGRA */
div[data-testid="stTextInput"] input{
    background:white!important; color:#000000!important; 
    border:2px solid #000000!important; border-radius:10px!important; 
    height:46px!important; font-weight:700!important;
}
div[data-baseweb="select"] > div{
    background:white!important; border:2px solid #000000!important; color:#000000!important;
}
div[data-baseweb="select"] span{color:#000000!important; font-weight:700!important; background:white!important;}
div[data-baseweb="select"] div{background:white!important;}
div[data-testid="stNumberInput"] input{
    background:white!important; color:#000000!important; border:2px solid #000000!important; font-weight:700!important;
}
div[data-testid="stNumberInput"] button{background:#000000!important;}
div[data-testid="stNumberInput"] button svg{fill:white!important;}

/* UPLOAD */
section[data-testid="stSidebar"] div[data-testid="stFileUploader"]{
    background:#fefce8!important; border:2px solid #000000!important; border-radius:12px!important;
}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] button{
    background:#fde047!important; color:#000000!important; border:1px solid black!important; font-weight:800!important;
}
</style>
""", unsafe_allow_html=True)

col_titulo, col_imp, col_limpiar, col_logout = st.columns([4.2, 1.4, 1.4, 1.4])
with col_titulo: st.markdown("<h1 style='margin:0; color:#111827;'>Etiquetas <span style='color:#ff7a5c'>PRO</span></h1>", unsafe_allow_html=True)
with col_imp:
    if st.button("🖨️ Imprimir", use_container_width=True, type="primary"):
        if st.session_state.data: st.session_state.print_now=True
        else: st.toast("Agrega bultos")
with col_limpiar:
    if st.button("🗑️ Limpiar Lista", use_container_width=True): st.session_state.data=[]; st.session_state.print_now=False; st.rerun()
with col_logout:
    if st.button("🚪 Cerrar sesión", use_container_width=True): st.session_state.logged=False; st.rerun()

with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    st.markdown("<p style='font-size:11px; font-weight:800; margin:0;'>FORMATO</p>", unsafe_allow_html=True)
    formato=st.radio("FORMATO", ["A4 VERTICAL - 4 POR HOJA","A4 HORIZONTAL - 2 POR HOJA","TÉRMICA 100X150"], label_visibility="collapsed")
    st.markdown("<p style='font-size:11px; font-weight:800; margin:10px 0 2px 0;'>🔑 API DNI/RUC</p>", unsafe_allow_html=True)
    st.text_input("TOKEN API", type="password", placeholder="Token opcional - funciona sin token", key="api_token_input", label_visibility="collapsed")
    st.markdown("<p style='font-size:10px; color:#6b7280; margin:0;'>Funciona con o sin token (apis.net.pe)</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:11px; font-weight:800; margin:12px 0 2px 0;'>TU LOGO DE TU EMPRESA (arriba derecha)</p>", unsafe_allow_html=True)
    logo_empresa=st.file_uploader("TU LOGO", type=["png","jpg","jpeg"], key="logo_emp", label_visibility="collapsed")
    st.markdown("<p style='font-size:11px; font-weight:800; margin:8px 0 2px 0;'>LOGO DE MARCAS ABAJO (Opcional)</p>", unsafe_allow_html=True)
    logo_marcas=st.file_uploader("Marcas", type=["png","jpg","jpeg"], key="logo_mar", label_visibility="collapsed")

PROVINCIAS_PERU=sorted(["PIURA - SULLANA","PIURA - PIURA","PIURA - PAITA","PIURA - TALARA","LIMA - LIMA","LAMBAYEQUE - CHICLAYO","LA LIBERTAD - TRUJILLO","TUMBES - TUMBES","ANCASH - CHIMBOTE","AREQUIPA - AREQUIPA","CUSCO - CUSCO","ICA - ICA","JUNIN - HUANCAYO","LORETO - IQUITOS","SAN MARTIN - TARAPOTO","UCAYALI - PUCALLPA","PUNO - JULIACA","TACNA - TACNA"])

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
    buffer=io.BytesIO()
    c=canvas.Canvas(buffer, pagesize=pagesize)
    w,h=pagesize
    items = 2 if is_horizontal else 4
    lh = h/items
    for idx,row in enumerate(st.session_state.data):
        pos=idx%items; y_top=h-(pos*lh)
        c.setStrokeColorRGB(0,0,0); c.setLineWidth(1.5)
        c.rect(10, y_top-lh+10, w-20, lh-20)
        c.setFont("Helvetica-Bold",20); c.drawString(20, y_top-32, f"{row['DESTINO'].split('-')[-1].strip()}")
        c.setFont("Helvetica-Bold",13); c.drawString(w/2-20, y_top-32, f"({row['BULTOS']})")
        c.line(15, y_top-42, w-115, y_top-42)
        c.setFont("Helvetica-Bold",10); c.drawString(20, y_top-58, f"ATT: {row['ATT 1']}")
        c.setFont("Helvetica",8); c.drawString(20, y_top-71, f"DNI/RUC: {row['DNI 1']} | FACTURA: {row['FACTURA']}")
        if row['ATT 2']:
            c.setFont("Helvetica-Bold",9); c.drawString(20, y_top-84, f"ATT 2: {row['ATT 2']} - DNI 2: {row['DNI 2']}")
            c.setFont("Helvetica-Bold",9); c.drawString(20, y_top-97, f"CELULAR: {row['CELULAR']}")
        else:
            c.setFont("Helvetica-Bold",9); c.drawString(20, y_top-84, f"CELULAR: {row['CELULAR']}")
        # LOGO ARRIBA DERECHA
        if logo_emp is not None:
            try:
                logo_emp.seek(0)
                im=Image.open(logo_emp).convert("RGBA")
                b=io.BytesIO(); im.save(b,format='PNG'); b.seek(0)
                c.drawImage(ImageReader(b), w-110, y_top-105, width=85, height=65, preserveAspectRatio=True, mask='auto')
            except: pass
        if logo_mar is not None:
            try:
                logo_mar.seek(0)
                im2=Image.open(logo_mar).convert("RGBA")
                bm=io.BytesIO(); im2.save(bm,format='PNG'); bm.seek(0)
                c.drawImage(ImageReader(bm), 20, y_top-lh+22, width=280, height=18, preserveAspectRatio=True, mask='auto')
            except: pass
        # QR
        try:
            qr=qrcode.make(f"{row['DESTINO']}-{row['BULTOS']}-{row['DNI 1']}"); qb=io.BytesIO(); qr.save(qb,format='PNG'); qb.seek(0)
            c.drawImage(ImageReader(qb), w-65, y_top-lh+15, width=45, height=45)
        except: pass
        if pos==items-1:
            c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

if st.session_state.print_now and st.session_state.data:
    pdf_bytes = generar_pdf_bytes(logo_empresa, logo_marcas, formato)
    if pdf_bytes:
        b64 = base64.b64encode(pdf_bytes).decode()
        # VISOR CORREGIDO
        st.success("PDF Generado - Dale a Descargar o Imprimir")
        st.download_button("📥 Descargar PDF", data=pdf_bytes, file_name="etiquetas.pdf", mime="application/pdf", use_container_width=True)
        pdf_display = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
        # Auto print
        st.components.v1.html(f"""
        <script>
        var pdfData="data:application/pdf;base64,{b64}";
        var iframe=document.createElement('iframe'); iframe.style.display='none'; iframe.src=pdfData;
        document.body.appendChild(iframe);
        iframe.onload=function(){{setTimeout(function(){{iframe.contentWindow.focus(); iframe.contentWindow.print();}},600);}}
        </script>
        """, height=0)
    st.session_state.print_now=False

if st.session_state.data:
    st.markdown(f"<div style='background:white; border:1.5px solid #111827; padding:10px; border-radius:10px;'><b style='color:#111827;'>📦 BULTOS AGREGADOS - {len(st.session_state.data)} etiquetas | {formato}</b></div>", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(st.session_state.data), use_container_width=True, hide_index=True)
else:
    st.info("Aún no hay bultos - agrega clientes arriba")

footer_soporte()
