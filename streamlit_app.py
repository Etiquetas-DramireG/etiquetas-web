import streamlit as st
import pandas as pd
import qrcode
import io
import requests
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

# 1. Configuración de página (SIEMPRE primero)
st.set_page_config(page_title="Etiquetas PRO", layout="wide", page_icon="🏷️")

# Inicialización segura de Session State
if 'logged' not in st.session_state: st.session_state.logged = False
if 'data' not in st.session_state: st.session_state.data = []
if 'print_now' not in st.session_state: st.session_state.print_now = False

for k in ["w_dni", "w_nombre", "w_factura", "w_nombre2", "w_dni2", "w_celular", "api_token_input"]:
    if k not in st.session_state: st.session_state[k] = ""
for k in ["w_bulto", "w_total"]:
    if k not in st.session_state: st.session_state[k] = 1
if "w_destino" not in st.session_state: st.session_state.w_destino = "LIMA - LIMA"

def buscar_dni_ruc(doc, token):
    doc = doc.strip()
    if not doc: return None
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    urls = []
    if len(doc) == 8:
        if token: urls.append(f"https://apis.net.pe{doc}")
        urls.append(f"https://apisperu.com{doc}")
        urls.append(f"https://decolecta.com{doc}")
    if len(doc) == 11:
        if token: urls.append(f"https://apis.net.pe{doc}")
        urls.append(f"https://apisperu.com{doc}")

    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                d = r.json()
                if "nombres" in d:
                    nombre = f"{d.get('nombres','')} {d.get('apellidoPaterno','')} {d.get('apellidoMaterno','')}".strip()
                    if len(nombre) > 3: return nombre
                if d.get("nombre"): return d["nombre"]
                if d.get("razonSocial"): return d["razonSocial"]
        except: continue
    return None

def buscar_click():
    token = st.session_state.api_token_input
    doc1 = st.session_state.w_dni.strip()
    if doc1:
        res1 = buscar_dni_ruc(doc1, token)
        if res1: 
            st.session_state.w_nombre = res1
            st.toast(f"✅ DNI 1: {res1}")
        else: st.toast(f"❌ No se encontró DNI 1")
    doc2 = st.session_state.w_dni2.strip()
    if doc2:
        res2 = buscar_dni_ruc(doc2, token)
        if res2: 
            st.session_state.w_nombre2 = res2
            st.toast(f"✅ DNI 2: {res2}")
        else: st.toast(f"❌ No se encontró DNI 2")
    if not doc1 and not doc2: st.toast("⚠️ Escribe DNI 1 o DNI 2")

def agregar_click():
    if not st.session_state.w_nombre: st.toast("⚠️ Falta ATT 1"); return
    b = int(st.session_state.w_bulto)
    t = int(st.session_state.w_total)
    if b > t: st.toast("⚠️ Bulto inicio no puede ser mayor que Total"); return
    
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
    st.toast("📦 Bultos agregados a la lista")

def footer_soporte():
    st.markdown("""<div style="position:fixed; bottom:0; left:0; width:100%; background:#002244; padding:8px 0; text-align:center; z-index:999;">
    <p style="margin:0; color:#99ccff; font-size:11px; font-weight:bold;">Soporte Técnico Soporte.DramirenG:</p>
    <p style="margin:0; color:white; font-size:11px;">📞 959237626 | ✉️ Soporte.DramirenG@hotmail.com</p></div><div style="height:70px;"></div>""", unsafe_allow_html=True)

# --- VISTA DE LOGIN ---
if not st.session_state.logged:
    st.markdown("""
    <style>
    .stApp{background:#eef1f5!important;}
    [data-testid="stHeader"] { visibility: hidden; }
    .login-card{
        background:white; border-radius:12px; 
        box-shadow:0 6px 25px rgba(0,0,0,0.15);
        border:1px solid #e5e7eb; overflow:hidden;
        max-width:420px; margin:auto;
    }
    .login-header{padding:16px 22px; font-weight:700; font-size:18px; color:#1f2937; border-bottom:1px solid #e5e7eb;}
    .login-body{padding:18px 22px 14px 22px;}
    div[data-testid="stTextInput"]{position:relative; margin-bottom:2px;}
    div[data-testid="stTextInput"] label p{font-size:13px!important; font-weight:600!important; color:#111827!important; margin-bottom:4px!important;}
    div[data-testid="stTextInput"] input{
        background:white!important; color:#111827!important;
        border:1.5px solid #d1d5db!important; border-radius:8px!important;
        height:42px!important; padding-left:42px!important;
        font-size:14px!important;
    }
    div[data-testid="stTextInput"] input:focus{border-color:#93c5fd!important; box-shadow:0 0 0 2px rgba(147,197,253,0.3)!important;}
    
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

# --- APP PRINCIPAL ---
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

def generar_pdf_bytes(logo_emp, logo_mar, formato_sel):
    buffer = io.BytesIO()
    
    # Evaluar formato de hoja
    if "TÉRMICA" in formato_sel:
        # 100mm x 150mm aproximado en puntos ReportLab (1 mm = 2.83465 pt)
        pagesize = (283, 425) 
        items_por_pagina = 1
    elif "HORIZONTAL" in formato_sel:
        pagesize = landscape(A4)
        items_por_pagina = 2
    else:
        pagesize = A4
        items_por_pagina = 4

    w, h = pagesize
    c = canvas.Canvas(buffer, pagesize=pagesize)
    lh = h / items_por_pagina

    for idx, row in enumerate(st.session_state.data):
        pos = idx % items_por_pagina
        y_top = h - (pos * lh)
        
        # Dibujar bordes de etiqueta
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(2)
        c.rect(15, y_top - lh + 15, w - 30, lh - 30)

        # 1. Cabecera - Destino Principal y Bultos
        c.setFont("Helvetica-Bold", 24 if "TÉRMICA" in formato_sel else 28)
        ciudad_destino = row['DESTINO'].split('-')[-1].strip()
        c.drawString(30, y_top - 45, f"DESTINO: {ciudad_destino}")
        
        c.setFont("Helvetica-Bold", 16)
        c.drawRightString(w - 30, y_top - 45, f"BULTOS: {row['BULTOS']}")
        
        c.setLineWidth(1.5)
        c.line(20, y_top - 60, w - 20, y_top - 60)

                # =====================================================================
        # 2. INFORMACIÓN DEL REMITENTE / CLIENTE (BLOQUE RESTAURADO)
        # =====================================================================
        c.setFont("Helvetica-Bold", 13)
        c.drawString(30, y_top - 85, f"ATT 1: {row['ATT 1']}")
        
        c.setFont("Helvetica", 11)
        c.drawString(30, y_top - 105, f"DNI/RUC: {row['DNI 1']}    |    DOC: {row['FACTURA']}")

        # Datos Opcionales (ATT 2) y Celular
        if row['ATT 2']:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(30, y_top - 130, f"ATT 2: {row['ATT 2']}")
            c.setFont("Helvetica", 11)
            c.drawString(30, y_top - 150, f"DNI 2: {row['DNI 2']}    |    CEL: {row['CELULAR']}")
            y_control_logos = y_top - 160  # Coordenada base para logos si hay ATT 2
        else:
            c.setFont("Helvetica", 11)
            c.drawString(30, y_top - 130, f"CELULAR: {row['CELULAR'] if row['CELULAR'] else 'S/N'}")
            y_control_logos = y_top - 140  # Coordenada base para logos si NO hay ATT 2

        # --- GENERACIÓN AUTOMÁTICA DE CÓDIGO QR ---
        try:
            # Creamos un texto compacto para el QR con los datos esenciales del bulto
            qr_text = f"DESTINO: {ciudad_destino}\nBULTO: {row['BULTOS']}\nATT: {row['ATT 1']}\nDOC: {row['FACTURA']}"
            qr = qrcode.QRCode(version=1, box_size=2, border=1)
            qr.add_data(qr_text)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Guardamos el QR generado en memoria para ReportLab
            qr_buffer = io.BytesIO()
            qr_img.save(qr_buffer, format="PNG")
            qr_buffer.seek(0)
            
            # Dibujamos el QR en la parte inferior izquierda de la etiqueta
            c.drawImage(ImageReader(qr_buffer), 30, y_top - lh + 25, width=55, height=55)
        except Exception as e:
            pass # Si falla la generación del QR, la etiqueta se sigue procesando normalmente

        # --- RENDERIZADO SEGURO DE LOGOS (EMPRESA Y MARCAS) ---
        # Logo de la Empresa (Arriba a la derecha del bloque inferior)
        if logo_emp:
            try:
                img_emp = Image.open(logo_emp)
                c.drawImage(ImageReader(img_emp), w - 130, y_top - 120, width=95, height=45, preserveAspectRatio=True, mask='auto')
            except: 
                pass

        # Logo de Marcas (Abajo a la derecha del bloque inferior)
        if logo_mar:
            try:
                img_mar = Image.open(logo_mar)
                c.drawImage(ImageReader(img_mar), w - 130, y_top - lh + 25, width=95, height=40, preserveAspectRatio=True, mask='auto')
            except: 
                pass

        # Control estructural de saltos de página nativos de ReportLab
        if pos == items_por_pagina - 1 and idx < len(st.session_state.data) - 1:
            c.showPage()
        elif "TÉRMICA" in formato_sel and idx < len(st.session_state.data) - 1:
            c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
# =====================================================================
# --- PANEL DE ACCIÓN: PROCESAMIENTO, IMPRESIÓN Y VISTA DE BULTOS ---
# =====================================================================

if st.session_state.print_now and st.session_state.data:
    pdf_bytes = generar_pdf_bytes(logo_empresa, logo_marcas, formato)
    if pdf_bytes:
        st.success(f"✅ PDF Generado - {len(st.session_state.data)} etiquetas")
        c1, c2 = st.columns(2)
        
        with c1: 
            st.download_button(
                "📥 Descargar PDF", 
                data=pdf_bytes, 
                file_name="etiquetas.pdf", 
                mime="application/pdf", 
                use_container_width=True, 
                type="primary"
            )
            
        with c2:
            # Codificación limpia a Base64 para el script de auto-impresión
            b64 = base64.b64encode(pdf_bytes).decode()
            
            # Botón nativo HTML + JS inyectado de forma segura en Streamlit
            st.components.v1.html(f"""
                <button onclick="var w=window.open(); w.document.write('<iframe src=\\'data:application/pdf;base64,{b64}\\' style=\\'width:100%;height:100%;border:none;\\'><\\/iframe>'); setTimeout(function(){{ w.focus(); w.print(); }}, 500);" 
                        style="width:100%; height:46px; background:#4CB978; color:white; border:none; border-radius:8px; font-weight:bold; font-size:15px; cursor:pointer; transition: 0.3s;">
                    🖨️ Imprimir Ahora Directo
                </button>
            """, height=60)
            
    # Apagamos el flag de impresión de forma segura para el próximo clic
    st.session_state.print_now = False

# --- PREVISUALIZACIÓN DE LA TABLA DE BULTOS EN COLA ---
st.markdown("<br>", unsafe_allow_html=True)
if st.session_state.data:
    st.markdown(f"""
        <div style='background:white; border:2px solid #000000; padding:12px; border-radius:10px; margin-bottom:10px;'>
            <b style='color:#000000; font-size:15px;'>📦 BULTOS EN COLA - {len(st.session_state.data)} etiquetas creadas | Modo: {formato}</b>
        </div>
    """, unsafe_allow_html=True)
    
    # Renderizado del DataFrame ocultando el index para una visualización limpia
    st.dataframe(pd.DataFrame(st.session_state.data), use_container_width=True, hide_index=True)
else: 
    st.info("💡 Aún no hay bultos registrados. Completa los datos del cliente arriba y haz clic en '➕ Agregar'.")

# Pie de página técnico siempre visible al fondo
footer_soporte()

