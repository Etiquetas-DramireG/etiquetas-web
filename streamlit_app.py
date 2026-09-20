import streamlit as st
import pandas as pd
import qrcode
import io
import os
import requests
import base64
import tempfile
from fpdf import FPDF

# 1. Configuración de página (SIEMPRE debe ser lo primero)
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

# =====================================================================
# --- CLASE DEL MOTOR GRÁFICO PARA CONSTRUCCIÓN DE PDFs ---
# =====================================================================
class MotorEtiquetasFPDF(FPDF):
    def __init__(self, logo_emp, logo_mar):
        super().__init__()
        self.logo_emp = logo_emp
        self.logo_mar = logo_mar

    def generar_codigo_qr(self, datos):
        """ Genera el código QR de manera temporal en disco """
        try:
            txt = f"DESTINO: {datos.get('destino','')}\nBULTO: {datos.get('bulto_texto','')}\nATT: {datos.get('atencion','')}\nDOC: {datos.get('serie','')}"
            qr = qrcode.QRCode(version=1, box_size=2, border=1)
            qr.add_data(txt)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            ruta_tmp = os.path.join(tempfile.gettempdir(), "tmp_qr_fpdf.png")
            img.save(ruta_tmp)
            return ruta_tmp
        except:
            return None

    def dibujar_etiqueta_mini(self, x, y, datos):
        """ Renderiza el formato de etiqueta pequeña (A4) optimizado """
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.6)
        self.rect(x, y, 195, 65)
        
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "B", 34)
        texto_destino = f"{datos.get('destino', '').upper()}"
        self.set_xy(x + 4.0, y + 3.0)
        self.cell(130, 12, texto_destino, ln=False, align='L')
        
        texto_bulto = datos.get('bulto_texto', '(1/1)')
        self.set_xy(x + 105, y + 4.5)
        self.set_font("Helvetica", "B", 24)
        self.cell(30, 10, texto_bulto, ln=False, align='L')
        
        self.line(x + 2, y + 17, x + 134, y + 17)
        
        self.set_font("Arial", "B", 17.5)
        self.set_xy(x + 4, y + 19)
        self.multi_cell(130, 6.0, f"ATT: {datos.get('atencion', '').upper()}", border=0, align='L')
        
        y_dinamico = self.get_y() + 1.0
        self.set_font("Arial", "", 12.5)
        self.set_xy(x + 4, y_dinamico)
        self.cell(48, 4.5, f"DNI/RUC: {datos.get('dni', '')}", ln=False) 
        
        self.set_font("Arial", "B", 12.5)
        self.set_xy(x + 55, y_dinamico)
        tipo_doc = datos.get('tipo_doc', 'FACTURA').upper()
        serie_num = f"{datos.get('serie', '')}".upper()
        self.cell(75, 4.5, f"  |  {tipo_doc}: {serie_num}", ln=True)
        
        if datos.get('atencion2'):
            y_dinamico = self.get_y() + 1.0
            self.set_xy(x + 4, y_dinamico)
            self.set_font("Arial", "B", 11.5)  
            self.cell(130, 4.5, f"ATT 2: {datos['atencion2'].upper()}", ln=True)
            doc2 = str(datos.get('dni2', '')).strip()
            tipo_doc2 = "RUC 2" if len(doc2) == 11 else "DNI 2"
            y_dinamico = self.get_y() + 1.0
            self.set_xy(x + 4, y_dinamico)
            self.set_font("Arial", "", 11.5)  
            self.cell(130, 4.5, f"{tipo_doc2}: {doc2}", ln=True)
        
        if datos.get('celular'):
            y_dinamico = self.get_y() + 1.0
            self.set_xy(x + 4, y_dinamico)
            self.set_font("Arial", "B", 13)
            self.cell(130, 4.5, f"CELULAR: {datos['celular']}", ln=True)

        if self.logo_emp:
            try: self.image(self.logo_emp, x + 136, y + 2, 57, 38)
            except: pass
        if self.logo_mar:
            try: self.image(self.logo_mar, x + 4, y + 48, 150, 13.5)
            except: pass

        try:
            ruta_qr = self.generar_codigo_qr(datos)
            if ruta_qr and os.path.exists(ruta_qr):
                self.image(ruta_qr, x + 172, y + 43, 19.5, 19.5)
                os.unlink(ruta_qr)
        except: pass
    def dibujar_etiqueta_maxi(self, x, y, datos):
        """ Renderiza la etiqueta grande ocupando el 100% de la hoja A4 Horizontal """
        self.set_draw_color(0, 0, 0)
        self.set_line_width(1.2)
        self.rect(x + 5, y + 5, 287, 200) 
        
        self.set_text_color(0, 0, 0) 
        self.set_font("Helvetica", "B", 56) 
        texto_destino = f"{datos.get('destino', '').upper()}"
        self.set_xy(x + 10, y + 10)
        self.cell(200, 22, texto_destino, ln=False, align='L')
        
        texto_bulto = datos.get('bulto_texto', '(1/1)')
        self.set_font("Helvetica", "B", 38) 
        self.set_xy(x + 210, y + 11)
        self.cell(75, 20, texto_bulto, ln=False, align='R')
        
        self.line(x + 5, y + 36, x + 292, y + 36)
        
        self.set_font("Arial", "B", 26)
        self.set_xy(x + 10, y + 42)
        self.multi_cell(180, 10, f"ATT: {datos.get('atencion', '').upper()}", border=0, align='L')
        
        y_dinamico = self.get_y() + 4.0
        self.set_font("Arial", "", 18)
        self.set_xy(x + 10, y_dinamico)
        tipo_doc = datos.get('tipo_doc', 'FACTURA').upper()
        serie_num = f"{datos.get('serie', '')}".upper()
        self.cell(180, 8, f"DNI/RUC: {datos.get('dni', '')}   |   {tipo_doc}: {serie_num}", ln=True)
        
        if datos.get('celular'):
            y_dinamico = self.get_y() + 4.0
            self.set_xy(x + 10, y_dinamico)
            self.set_font("Arial", "B", 20)
            self.cell(180, 8, f"CELULAR: {datos['celular']}", ln=True)
            
        if datos.get('atencion2'):
            y_dinamico = self.get_y() + 4.0
            self.set_xy(x + 10, y_dinamico)
            self.set_font("Arial", "B", 16)
            self.cell(180, 8, f"ATT 2: {datos['atencion2'].upper()}", ln=True)
            doc2 = str(datos.get('dni2', '')).strip()
            tipo_doc2 = "RUC 2" if len(doc2) == 11 else "DNI 2"
            y_dinamico = self.get_y() + 2.0
            self.set_xy(x + 10, y_dinamico)
            self.set_font("Arial", "", 16)
            self.cell(180, 8, f"{tipo_doc2}: {doc2}", ln=True)

        if self.logo_emp:
            try: self.image(self.logo_emp, x=x+200, y=y+40, w=87, h=65)
            except: pass
        if self.logo_mar:
            try: self.image(self.logo_mar, x=x+10, y=y+150, w=220, h=45)
            except: pass
            
        try:
            ruta_qr = self.generar_codigo_qr(datos)
            if ruta_qr and os.path.exists(ruta_qr):
                self.image(ruta_qr, x=x+240, y=y+150, w=45, h=45)
                os.unlink(ruta_qr)
        except: pass

    def dibujar_etiqueta_termica(self, x, y, datos):
        """ Renderiza la etiqueta vertical para rollos térmicos sin delays """
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.8)
        self.rect(x + 3, y + 3, 94, 144)
        
        texto_destino = f"{datos.get('destino', '').upper()}"
        if len(texto_destino) >= 9:
            self.set_font("Helvetica", "B", 24)
            self.set_xy(x + 5, y + 5)
            self.cell(63, 10, texto_destino, ln=False, align='L')
        else:
            self.set_font("Helvetica", "B", 36)
            self.set_xy(x + 4, y + 4)
            self.cell(63, 12, texto_destino, ln=False, align='L')
        
        texto_bulto = datos.get('bulto_texto', '(1/1)')
        self.set_font("Helvetica", "B", 18)
        self.set_xy(x + 68, y + 7)
        self.cell(25, 8, texto_bulto, ln=False, align='R')
        
        self.set_font("Arial", "B", 13)
        self.set_xy(x + 6, y + 21)
        self.multi_cell(88, 5.0, f"ATT: {datos.get('atencion', '').upper()}", border=0, align='L')
        
        y_dinamico = self.get_y() + 1.5
        self.set_font("Arial", "", 10.5)
        self.set_xy(x + 6, y_dinamico)
        self.cell(88, 4.5, f"DNI/RUC: {datos.get('dni', '')}", ln=True)

        y_dinamico = self.get_y() + 0.5
        self.set_xy(x + 6, y_dinamico)
        tipo_doc = datos.get('tipo_doc', 'FACTURA').upper()
        serie_num = f"{datos.get('serie', '')}".upper()
        self.cell(88, 4.5, f"{tipo_doc}: {serie_num}", ln=True)
        
        if datos.get('celular'):
            y_dinamico = self.get_y() + 0.5
            self.set_xy(x + 6, y_dinamico)
            self.set_font("Arial", "B", 11)
            self.cell(88, 4.5, f"CELULAR: {datos['celular']}", ln=True)
            
        if datos.get('atencion2'):
            y_dinamico = self.get_y() + 0.5
            self.set_xy(x + 6, y_dinamico)
            self.set_font("Arial", "B", 9.5)
            self.cell(88, 4.5, f"ATT 2: {datos['atencion2'].upper()}", ln=True)
            doc2 = str(datos.get('dni2', '')).strip()
            tipo_doc2 = "RUC 2" if len(doc2) == 11 else "DNI 2"
            y_dinamico = self.get_y() + 0.5
            self.set_xy(x + 6, y_dinamico)
            self.set_font("Arial", "", 9.5)
            self.cell(88, 4.5, f"{tipo_doc2}: {doc2}", ln=True)

        y_linea_central = y + 62.0
        y_linea_base = y + 120.0
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.6)
        self.line(x + 3, y_linea_central, x + 97, y_linea_central)
        self.line(x + 3, y_linea_base, x + 97, y_linea_base)

        if self.logo_emp:
            try: self.image(self.logo_emp, x + 7, y_linea_central + 4.0, 86, 48)
            except: pass
        if self.logo_mar:
            try: self.image(self.logo_mar, x + 6, y_linea_base + 4, 60, 18)
            except: pass

        try:
            ruta_qr = self.generar_codigo_qr(datos)
            if ruta_qr and os.path.exists(ruta_qr):
                self.image(ruta_qr, x + 72, y_linea_base + 2, 22, 22)
                os.unlink(ruta_qr)
        except: pass

        self.line(x + 3, y + 18, x + 97, y + 18)       
        self.line(x + 3, y_linea_central, x + 97, y_linea_central) 
        self.line(x + 3, y_linea_base, x + 97, y_linea_base)       

# --- FUNCIONES DE LÓGICA DE INTERFAZ ---
def generar_pdf_bytes(logo_empresa, logo_marcas, formato_seleccionado):
    """ Función conectora principal corregida para agrupar múltiples bultos por hoja """
    pdf = MotorEtiquetasFPDF(logo_empresa, logo_marcas)
    lista_envios = []
    
    # Adaptar los estados de Streamlit al diccionario que espera el motor
    for row in st.session_state.data:
        ciudad = row["DESTINO"].split("-")[-1].strip() if "-" in row["DESTINO"] else row["DESTINO"]
        lista_envios.append({
            "destino": ciudad,
            "bulto_texto": f"({row['BULTOS']})",
            "atencion": row["ATT 1"],
            "dni": row["DNI 1"],
            "tipo_doc": "DOC",
            "serie": row["FACTURA"],
            "atencion2": row["ATT 2"],
            "dni2": row["DNI 2"],
            "celular": row["CELULAR"]
        })

    # Procesar distribución de páginas e inyección gráfica CORREGIDA
    if "HORIZONTAL" in formato_seleccionado:  
        for datos in lista_envios:
            pdf.add_page(orientation='L', format='A4') 
            pdf.dibujar_etiqueta_maxi(0, 0, datos)       
            
    elif "TÉRMICA" in formato_seleccionado:  
        pdf.set_auto_page_break(auto=False, margin=0)
        for datos in lista_envios:
            pdf.add_page(orientation='P', format=(100, 150))
            pdf.dibujar_etiqueta_termica(0, 0, datos)
            
    else:  # --- A4 VERTICAL ESTÁNDAR (4 BULTOS POR HOJA) CORREGIDO ---
        # Posiciones exactas en milímetros (X, Y) para las 4 ranuras de la hoja A4
        posiciones_a4 = [(8, 5), (8, 75), (8, 145), (8, 215)]
        
        for i, datos in enumerate(lista_envios):
            idx_hoja = i % 4
            
            # SOLO crea una página nueva al inicio (bulto 0) o cada vez que completamos 4 bultos
            if idx_hoja == 0:
                pdf.add_page(orientation='P', format='A4')
                
            x_pos, y_pos = posiciones_a4[idx_hoja]
            pdf.dibujar_etiqueta_mini(x_pos, y_pos, datos)

    return bytes(pdf.output())

def buscar_dni_ruc(doc, token):
    doc = doc.strip()
    if not doc: return None
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    urls = []
    if len(doc) == 8:
        if token: urls.append((f"https://apis.net.pe{doc}", "apis_net"))
        urls.append((f"https://apisperu.com{doc}", "apisperu"))
    elif len(doc) == 11:
        if token: urls.append((f"https://apis.net.pe{doc}", "apis_net"))
        urls.append((f"https://apisperu.com{doc}", "apisperu"))

    for url, proveedor in urls:
        try:
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                d = r.json()
                if proveedor == "apis_net":
                    if "nombres" in d:
                        return f"{d.get('nombres','')} {d.get('apellidoPaterno','')} {d.get('apellidoMaterno','')}".strip()
                    if "razonSocial" in d: return d["razonSocial"]
                if d.get("nombre"): return d["nombre"]
                if d.get("razonSocial"): return d["razonSocial"]
        except: continue
    return None

def buscar_click():
    token = st.session_state.api_token_input
    doc1 = st.session_state.w_dni.strip()
    if doc1:
        res1 = buscar_dni_ruc(doc1, token)
        if res1: st.session_state.w_nombre = res1; st.toast(f"✅ DNI 1: {res1}")
        else: st.toast("❌ No encontrado DNI 1")
    doc2 = st.session_state.w_dni2.strip()
    if doc2:
        res2 = buscar_dni_ruc(doc2, token)
        if res2: st.session_state.w_nombre2 = res2; st.toast(f"✅ DNI 2: {res2}")
        else: st.toast("❌ No encontrado DNI 2")

def agregar_click():
    if not st.session_state.w_nombre: st.toast("⚠️ Falta ATT 1"); return
    b = int(st.session_state.w_bulto)
    t = int(st.session_state.w_total)
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

# --- PANEL DE LOGIN ---
if not st.session_state.logged:
    st.markdown("""
    <style>
    .stApp{background:#eef1f5!important;}
    [data-testid="stHeader"] { visibility: hidden; }
    .login-card{
        background:white; border-radius:12px; box-shadow:0 6px 25px rgba(0,0,0,0.15);
        border:1px solid #e5e7eb; overflow:hidden; max-width:420px; margin:auto;
    }
    .login-header{padding:16px 22px; font-weight:700; font-size:18px; color:#1f2937; border-bottom:1px solid #e5e7eb;}
    .login-body{padding:18px 22px 14px 22px;}
    div[data-testid="stTextInput"]{position:relative; margin-bottom:2px;}
    div[data-testid="stTextInput"] label p{font-size:13px!important; font-weight:600!important; color:#111827!important; margin-bottom:4px!important;}
    div[data-testid="stTextInput"] input{
        background:white!important; color:#111827!important; border:1.5px solid #d1d5db!important;
        border-radius:8px!important; height:42px!important; padding-left:42px!important; font-size:14px!important;
    }
    div[data-testid="stButton"] button[kind="primary"]{
        background:#4CB978!important; color:white!important; border:0!important;
        border-radius:8px!important; height:42px!important; font-weight:700!important; font-size:15px!important;
        width:100%!important; margin-top:10px!important;
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
        with col2: cancelar = st.button("Cancelar", key="cancelar_final")
        st.markdown('</div></div>', unsafe_allow_html=True)

        if aceptar:
            if u=="admin" and p=="dramireng123":
                st.session_state.logged=True
                st.rerun()
            else: st.error("Usuario o contraseña incorrecta")
        if cancelar:
            st.session_state.login_user_final=""
            st.session_state.login_pass_final=""
            st.rerun()
    footer_soporte()
    st.stop()

else:
    # --- INTERFAZ PRINCIPAL LOGUEADO ---
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
        formato=st.radio("FORMATO", ["A4 VERTICAL - 4 POR HOJA","A4 HORIZONTAL - 2 POR HOJA","TÉRMICA 100X150"], label_visibility="visible")
        st.text_input("TOKEN API", type="password", placeholder="Token opcional", key="api_token_input")
        logo_empresa=st.file_uploader("TU LOGO", type=["png","jpg","jpeg"], key="logo_emp")
        logo_marcas=st.file_uploader("Marcas", type=["png","jpg","jpeg"], key="logo_mar")

    PROVINCIAS_PERU=sorted(["PIURA - SULLANA","PIURA - PIURA","LIMA - LIMA","LAMBAYEQUE - CHICLAYO","LA LIBERTAD - TRUJILLO","TUMBES - TUMBES","ANCASH - CHIMBOTE","AREQUIPA - AREQUIPA","CUSCO - CUSCO","ICA - ICA","JUNIN - HUANCAYO","LORETO - IQUITOS","SAN MARTIN - TARAPOTO","UCAYALI - PUCALLPA","PUNO - JULIACA","TACNA - TACNA"])

    st.markdown("<h3 style='color:#111827; margin-top:15px;'>Datos del cliente</h3>", unsafe_allow_html=True)
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
    with c8: st.selectbox("DESTINO", PROVINCIAS_PERU, key="w_destino")
    with c9: st.number_input("BULTO INICIO", min_value=1, step=1, key="w_bulto")
    with c10: st.number_input("TOTAL", min_value=1, step=1, key="w_total")
    with c11:
        st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
        st.button("➕ Agregar", use_container_width=True, type="primary", on_click=agregar_click)

    # --- PROCESAMIENTO E IMPRESIÓN DIRECTA ---
    if st.session_state.print_now and st.session_state.data:
        pdf_bytes = generar_pdf_bytes(logo_empresa, logo_marcas, formato)
        if pdf_bytes:
            st.success(f"✅ PDF Generado - {len(st.session_state.data)} etiquetas")
            c1,c2 = st.columns(2)
            with c1: st.download_button("📥 Descargar PDF", data=pdf_bytes, file_name="etiquetas.pdf", mime="application/pdf", use_container_width=True, type="primary")
            with c2:
                b64 = base64.b64encode(pdf_bytes).decode()
                st.components.v1.html(f"""<button onclick="var w=window.open(); w.document.write('<iframe src=\\'data:application/pdf;base64,{b64}\\' style=\\'width:100%;height:100%\\'><\\/iframe>'); setTimeout(function(){{ w.focus(); w.print(); }}, 500);" style="width:100%;height:46px;background:#4CB978;color:white;border-radius:10px;font-weight:bold;cursor:pointer;border:none;">🖨️ Imprimir Ahora</button>""", height=60)
        st.session_state.print_now=False

    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.data:
        st.markdown(f"<div style='background:white; border:1.5px solid #111827; padding:10px; border-radius:10px;'><b style='color:#111827;'>BULTOS - {len(st.session_state.data)} etiquetas | {formato}</b></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(st.session_state.data), use_container_width=True, hide_index=True)
    else: st.info("Aún no hay bultos - agrega clientes arriba")
    
    footer_soporte()
