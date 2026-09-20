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
for k in ["w_dni","w_nombre","w_factura","w_nombre2","w_dni2","w_celular","login_user","login_pass","api_token_input"]:
    if k not in st.session_state: st.session_state[k]=""
for k in ["w_bulto","w_total"]:
    if k not in st.session_state: st.session_state[k]=1
if "w_destino" not in st.session_state: st.session_state.w_destino="LIMA - LIMA"

def buscar_dni_ruc(doc, token):
    doc = doc.strip()
    if not doc: return None
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    # Intentamos con y sin token en varios endpoints gratis
    urls = []
    if len(doc) == 8:
        if token: urls.append(f"https://api.apis.net.pe/v2/reniec/dni?numero={doc}")
        urls.append(f"https://dniruc.apisperu.com/api/v1/dni/{doc}")
        urls.append(f"https://api.decolecta.com/v1/reniec/dni?numero={doc}")
    if len(doc) == 11:
        if token: urls.append(f"https://api.apis.net.pe/v2/sunat/ruc?numero={doc}")
        urls.append(f"https://dniruc.apisperu.com/api/v1/ruc/{doc}")

    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code == 200:
                d = r.json()
                # RENIEC
                if "nombres" in d:
                    nombre = f"{d.get('nombres','')} {d.get('apellidoPaterno','')} {d.get('apellidoMaterno','')}".strip()
                    if len(nombre) > 3: return nombre
                if "nombre" in d and d["nombre"]: return d["nombre"]
                if "razonSocial" in d and d["razonSocial"]: return d["razonSocial"]
                if "nombres" in d and "apellido" in str(d).lower():
                    return d.get("nombre") or d.get("razonSocial")
        except: continue
    return None

def buscar_dni_logic():
    token = st.session_state.get("api_token_input","").strip()
    doc1 = st.session_state.get("w_dni","").strip()
    doc2 = st.session_state.get("w_dni2","").strip()
    
    encontro = False
    if doc1:
        res1 = buscar_dni_ruc(doc1, token)
        if res1:
            st.session_state.w_nombre = res1
            st.toast(f"✅ DNI 1 encontrado: {res1}")
            encontro = True
        else:
            st.toast(f"❌ No se encontró DNI 1: {doc1}")

    if doc2:
        res2 = buscar_dni_ruc(doc2, token)
        if res2:
            st.session_state.w_nombre2 = res2
            st.toast(f"✅ DNI 2 encontrado: {res2}")
            encontro = True
        else:
            st.toast(f"❌ No se encontró DNI 2: {doc2}")
    
    if not doc1 and not doc2:
        st.toast("⚠️ Escribe DNI 1 o DNI 2")

def buscar_click():
    token = st.session_state.api_token_input
    doc1 = st.session_state.w_dni.strip()
    if doc1:
        res1 = buscar_dni_ruc(doc1, token)
        if res1: st.session_state.w_nombre = res1; st.toast(f"DNI 1: {res1}")
    doc2 = st.session_state.w_dni2.strip()
    if doc2:
        res2 = buscar_dni_ruc(doc2, token)
        if res2: st.session_state.w_nombre2 = res2; st.toast(f"DNI 2: {res2}")
    if not doc1 and not doc2: st.toast("Escribe DNI 1 o DNI 2")

def agregar_click():
    if not st.session_state.w_nombre: st.toast("Falta ATT 1"); return
    b = st.session_state.w_bulto; t = st.session_state.w_total
    for i in range(b, t+1):
        st.session_state.data.append({
            "DESTINO": st.session_state.w_destino, "BULTOS": f"{i}/{t}",
            "ATT 1": st.session_state.w_nombre, "DNI 1": st.session_state.w_dni,
            "FACTURA": st.session_state.w_factura, "ATT 2": st.session_state.w_nombre2,
            "DNI 2": st.session_state.w_dni2, "CELULAR": st.session_state.w_celular
        })
    st.session_state.w_dni=""; st.session_state.w_nombre=""; st.session_state.w_factura=""
    st.session_state.w_nombre2=""; st.session_state.w_dni2=""; st.session_state.w_celular=""
    st.session_state.w_bulto=1; st.session_state.w_total=1

def footer_soporte():
    st.markdown("""<div style="position:fixed; bottom:0; left:0; width:100%; background:#002244; padding:8px 0; text-align:center; z-index:999;">
    <p style="margin:0; color:#99ccff; font-size:11px; font-weight:bold;">Soporte Técnico Soporte.DramirenG:</p>
    <p style="margin:0; color:white; font-size:11px;">📞 959237626 | ✉️ Soporte.DramirenG@hotmail.com</p></div><div style="height:70px;"></div>""", unsafe_allow_html=True)

if not st.session_state.logged:
    st.markdown("""
    <style>
    .stApp{background:#eef1f5!important;}
    #MainMenu, footer, header{visibility:hidden;}
    .login-card{
        background:white; border-radius:12px; 
        box-shadow:0 6px 25px rgba(0,0,0,0.15);
        border:1px solid #e5e7eb; overflow:hidden;
        max-width:420px; margin:auto;
    }
    .login-header{padding:16px 22px; font-weight:700; font-size:18px; color:#1f2937; border-bottom:1px solid #e5e7eb;}
    .login-body{padding:18px 22px 14px 22px;}
    /* INPUTS COMO TU FOTO */
    div[data-testid="stTextInput"]{position:relative; margin-bottom:2px;}
    div[data-testid="stTextInput"] label p{font-size:13px!important; font-weight:600!important; color:#111827!important; margin-bottom:4px!important;}
    div[data-testid="stTextInput"] input{
        background:white!important; color:#111827!important;
        border:1.5px solid #d1d5db!important; border-radius:8px!important;
        height:42px!important; padding-left:42px!important;
        font-size:14px!important;
    }
    div[data-testid="stTextInput"] input:focus{border-color:#93c5fd!important; box-shadow:0 0 0 2px rgba(147,197,253,0.3)!important;}
    /* ICONO GRIS IZQUIERDA */
    div[data-testid="stTextInput"]:nth-of-type(1) > div:before{
        content:'👤'; position:absolute; left:1px; top:25px; z-index:9;
        background:#e5e7eb; width:36px; height:40px; display:flex; align-items:center; justify-content:center;
        border-radius:7px 0 0 7px; border-right:1px solid #d1d5db; font-size:14px;
        line-height:40px; text-align:center;
    }
    div[data-testid="stTextInput"]:nth-of-type(2) > div:before{
        content:'🔒'; position:absolute; left:1px; top:25px; z-index:9;
        background:#e5e7eb; width:36px; height:40px; display:flex; align-items:center; justify-content:center;
        border-radius:7px 0 0 7px; border-right:1px solid #d1d5db; font-size:14px;
        line-height:40px; text-align:center;
    }
    /* BOTON VERDE ACEPTAR */
    div[data-testid="stButton"] button[kind="primary"]{
        background:#4CB978!important; color:white!important; border:0!important;
        border-radius:8px!important; height:42px!important; font-weight:700!important; font-size:15px!important;
        width:100%!important; margin-top:10px!important;
    }
    div[data-testid="stButton"] button[kind="secondary"]{
        background:white!important; color:#374151!important; border:1.5px solid #d1d5db!important;
        border-radius:8px!important; height:34px!important; font-size:13px!important; float:right;
    }
    </style>
    """, unsafe_allow_html=True)

    c1,c2,c3 = st.columns([1,0.9,1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown('<div class="login-card"><div class="login-header">Iniciar Sesión</div><div class="login-body">', unsafe_allow_html=True)
        
        u = st.text_input("Usuario", placeholder="Ingrese su usuario", key="login_user_final")
        p = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña", key="login_pass_final")
        
        aceptar = st.button("→ Aceptar", type="primary", use_container_width=True)
        
        col1,col2 = st.columns([2.5,1])
        with col2:
            cancelar = st.button("Cancelar", key="cancelar_final")
        
        st.markdown('</div></div>', unsafe_allow_html=True)

        if aceptar:
            if u=="admin" and p=="dramireng123":
                st.session_state.logged=True
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrecta")
        if cancelar:
            st.session_state.login_user_final=""
            st.session_state.login_pass_final=""
            st.rerun()

    footer_soporte()
    st.stop()

# APP PRINCIPAL
st.markdown("""
<style>
.stApp{background:#ffffff!important;}
section[data-testid="stSidebar"]{background:#ffffff!important;}
section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label p, section[data-testid="stSidebar"] span{color:#000000!important; font-weight:800!important; opacity:1!important;}
div[data-testid="stTextInput"] label p, div[data-testid="stSelectbox"] label p, div[data-testid="stNumberInput"] label p{color:#000000!important; font-weight:900!important; font-size:13px!important;}
div[data-testid="stTextInput"] input{background:#ffffff!important; color:#000000!important; border:2px solid #000000!important; height:46px!important; font-weight:700!important;}
div[data-baseweb="select"] > div{background:#ffffff!important; border:2px solid #000000!important;}
div[data-baseweb="select"] span{color:#000000!important; font-weight:700!important;}
div[data-testid="stNumberInput"] input{background:#ffffff!important; color:#000000!important; border:2px solid #000000!important;}
div[data-testid="stFileUploader"]{background:#FFFBEB!important; border:2px dashed #FACC15!important; border-radius:14px!important;}
div[data-testid="stFileUploader"] section{background:#FFFBEB!important; border:0px!important;}
div[data-testid="stFileUploader"] button{background:#FDE047!important; color:#000000!important; border:1.5px solid #000000!important; font-weight:900!important;}
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
    st.markdown("<p style='font-size:11px; font-weight:800; margin:12px 0 2px 0;'>TU LOGO DE TU EMPRESA (arriba derecha)</p>", unsafe_allow_html=True)
    logo_empresa=st.file_uploader("TU LOGO", type=["png","jpg","jpeg"], key="logo_emp", label_visibility="collapsed")
    st.markdown("<p style='font-size:11px; font-weight:800; margin:8px 0 2px 0;'>LOGO DE MARCAS ABAJO (Opcional)</p>", unsafe_allow_html=True)
    logo_marcas=st.file_uploader("Marcas", type=["png","jpg","jpeg"], key="logo_mar", label_visibility="collapsed")

PROVINCIAS_PERU=sorted(["PIURA - SULLANA","PIURA - PIURA","LIMA - LIMA","LAMBAYEQUE - CHICLAYO","LA LIBERTAD - TRUJILLO","TUMBES - TUMBES","ANCASH - CHIMBOTE","AREQUIPA - AREQUIPA","CUSCO - CUSCO","ICA - ICA","JUNIN - HUANCAYO","LORETO - IQUITOS","SAN MARTIN - TARAPOTO","UCAYALI - PUCALLPA","PUNO - JULIACA","TACNA - TACNA"])

st.markdown("<h3 style='color:#111827; margin-top:15px;'>📦 Datos del cliente</h3>", unsafe_allow_html=True)
c1,c2,c3,c4=st.columns([1.1,1.9,1.1,0.6])
with c1: st.text_input("DNI/RUC 1", key="w_dni", placeholder="75098930")
with c2: st.text_input("ATT 1 / NOMBRE PRINCIPAL", key="w_nombre")
with c3: st.text_input("N° FACTURA / GUIA", key="w_factura", placeholder="F001-XXXXX")
with c4:
    st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
    st.button("🔍 Buscar (DNI 1 y 2)", use_container_width=True, type="primary", on_click=buscar_click)
c5,c6,c7=st.columns([2,1.2,1])
with c5: st.text_input("ATT 2 / SEGUNDO NOMBRE (Opcional)", key="w_nombre2")
with c6: st.text_input("DNI 2", key="w_dni2")
with c7: st.text_input("CELULAR", key="w_celular")
c8,c9,c10,c11=st.columns([1.6,0.6,0.6,0.7])
with c8: st.selectbox("DESTINO", PROVINCIAS_PERU, key="w_destino")
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
        pos=idx%items
        y_top=h-(pos*lh)
        
        # BORDE
        c.setStrokeColorRGB(0,0,0)
        c.setLineWidth(1.8)
        c.rect(10, y_top-lh+10, w-20, lh-20)

        # 1. DESTINO MAS GRANDE
        c.setFont("Helvetica-Bold", 26)
        c.drawString(22, y_top-38, f"{row['DESTINO'].split('-')[-1].strip()}")
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(w/2-15, y_top-38, f"({row['BULTOS']})")
        
        c.setLineWidth(1.2)
        c.line(15, y_top-50, w-15, y_top-50)

        # 2. LETRA MAS GRANDE Y NEGRITA
        c.setFont("Helvetica-Bold", 14)
        c.drawString(20, y_top-72, f"ATT: {row['ATT 1']}")
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20, y_top-90, f"DNI/RUC: {row['DNI 1']} | FACTURA: {row['FACTURA']}")

        if row['ATT 2']:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(20, y_top-108, f"ATT 2: {row['ATT 2']} - DNI 2: {row['DNI 2']}")
            c.setFont("Helvetica-Bold", 12)
            c.drawString(20, y_top-126, f"CELULAR: {row['CELULAR']}")
        else:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(20, y_top-108, f"CELULAR: {row['CELULAR']}")

        # 3. LOGO 1 ARRIBA DERECHA - MAS GRANDE (como tu marca rosada)
        if logo_emp is not None:
            try:
                logo_emp.seek(0)
                im=Image.open(logo_emp).convert("RGBA")
                b=io.BytesIO()
                im.save(b,format='PNG')
                b.seek(0)
                # ANTES 85x65 -> AHORA 135x95 MUCHO MAS GRANDE
                c.drawImage(ImageReader(b), w-155, y_top-120, width=135, height=95, preserveAspectRatio=True, mask='auto')
            except: pass

        # 4. QR MAS GRANDE - ABAJO DERECHA
        try:
            qr=qrcode.make(f"{row['DESTINO']}-{row['BULTOS']}-{row['DNI 1']}")
            qb=io.BytesIO()
            qr.save(qb,format='PNG')
            qb.seek(0)
            # ANTES 45x45 -> AHORA 75x75
            c.drawImage(ImageReader(qb), w-95, y_top-lh+18, width=75, height=75)
        except: pass

        # 5. LOGO 2 ABAJO - MARCAS MAS GRANDE Y LARGO
        if logo_mar is not None:
            try:
                logo_mar.seek(0)
                im2=Image.open(logo_mar).convert("RGBA")
                bm=io.BytesIO()
                im2.save(bm,format='PNG')
                bm.seek(0)
                # ANTES 280x18 -> AHORA 400x35 MAS GRANDE
                c.drawImage(ImageReader(bm), 20, y_top-lh+20, width=400, height=35, preserveAspectRatio=True, mask='auto')
            except: pass

        if pos==items-1:
            c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

if st.session_state.print_now and st.session_state.data:
    pdf_bytes = generar_pdf_bytes(logo_empresa, logo_marcas, formato)
    if pdf_bytes:
        st.success(f"✅ PDF Generado - {len(st.session_state.data)} etiquetas")
        c1,c2 = st.columns(2)
        with c1: st.download_button("📥 Descargar PDF", data=pdf_bytes, file_name="etiquetas.pdf", mime="application/pdf", use_container_width=True, type="primary")
        with c2:
            b64 = base64.b64encode(pdf_bytes).decode()
            st.components.v1.html(f"""<button onclick="var w=window.open(); w.document.write('<iframe src=data:application/pdf;base64,{b64} style=width:100%;height:100%><\\/iframe>'); w.document.close(); w.focus(); w.print();" style="width:100%;height:46px;background:#000;color:white;border-radius:10px;font-weight:bold;">🖨️ Imprimir Ahora</button>""", height=60)
    st.session_state.print_now=False

if st.session_state.data:
    st.markdown(f"<div style='background:white; border:1.5px solid #111827; padding:10px; border-radius:10px;'><b style='color:#111827;'>📦 BULTOS - {len(st.session_state.data)} etiquetas | {formato}</b></div>", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(st.session_state.data), use_container_width=True, hide_index=True)
else: st.info("Aún no hay bultos - agrega clientes arriba")
footer_soporte()
