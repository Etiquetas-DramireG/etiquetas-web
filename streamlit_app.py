import streamlit as st
from fpdf import FPDF
import os, qrcode, requests

st.set_page_config(page_title="DramirenG", layout="centered")
if "login" not in st.session_state: st.session_state.login=False
if "lista" not in st.session_state: st.session_state.lista=[]
if "clientes" not in st.session_state: st.session_state.clientes={}

if st.session_state.get("do_clear"):
    for k in ["dni","nombre","destino","factura","celular"]:
        st.session_state.pop(k, None)
    st.session_state["do_clear"]=False

if os.path.exists("clientes_guardados.txt"):
    try:
        with open("clientes_guardados.txt","r",encoding="utf-8") as f:
            for l in f:
                p=l.strip().split(",")
                if len(p)>=2: st.session_state.clientes[p[0]]=p
    except: pass

PROVINCIAS = ["LIMA","AREQUIPA","TRUJILLO","CHICLAYO","PIURA","SULLANA","TALARA","CUSCO","PUNO","TACNA","ICA","HUANCAYO","IQUITOS","PISCO","CHACHAPOYAS","HUARAZ","AYACUCHO","CAJAMARCA","CALLAO","TUMBES","MOYOBAMBA","TARAPOTO"]

def buscar_dni_api(dni, token):
    dni=dni.strip()
    if len(dni)==7 and dni.isdigit(): dni="0"+dni
    if dni in st.session_state.clientes:
        return st.session_state.clientes[dni][1]
    if not token: return None
    try:
        if len(dni)==8:
            r=requests.post("https://apiperu.dev/api/dni", json={"dni":dni}, headers={"Authorization":f"Bearer {token}"}, timeout=6, verify=False)
            if r.status_code==200 and r.json().get("success"):
                d=r.json()["data"]
                return f"{d.get('nombres','')} {d.get('apellido_paterno','')} {d.get('apellido_materno','')}".strip().upper()
        else:
            r=requests.post("https://apiperu.dev/api/ruc", json={"ruc":dni}, headers={"Authorization":f"Bearer {token}"}, timeout=6, verify=False)
            if r.status_code==200 and r.json().get("success"):
                return r.json()["data"].get("nombre_o_razon_social","").upper()
    except: pass
    try:
        t="dni" if len(dni)==8 else "ruc"
        r=requests.get(f"https://api.apis.net.pe/v1/{t}?numero={dni}", headers={"Authorization":f"Bearer {token}"}, timeout=5).json()
        return (r.get('nombre') or r.get('razonSocial') or "").upper()
    except: return None

import datetime

if not st.session_state.login:
    # CSS PARA QUE SE VEA COMO TU TKINTER
    st.markdown("""
        <style>
        .stApp { background-color: #001a33; }
        .login-card {
            background-color: #003366;
            padding: 25px 30px 0px 30px;
            border-radius: 8px;
            border: 2px solid #002244;
            text-align: center;
            max-width: 400px;
            margin: 40px auto 0 auto;
        }
        .soporte-box {
            background-color: #002244;
            margin-top: 20px;
            padding: 10px;
            border-radius: 0 0 8px 8px;
            margin-left: -30px;
            margin-right: -30px;
        }
        </style>
    """, unsafe_allow_html=True)

    ano_actual = datetime.datetime.now().strftime("%Y")

    # CONTENEDOR CENTRADO
    c1,c2,c3 = st.columns([1,1.2,1])
    with c2:
        st.markdown(f"""
        <div class="login-card">
            <p style="color:white; font-weight:bold; font-family:Arial; font-size:16px; margin-bottom:2px;">¡BIENVENIDO!</p>
            <p style="color:#b3d9ff; font-style:italic; font-family:Arial; font-size:12px; margin-top:0px;">Control de Despachos Oficial {ano_actual}</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container(border=False):
            # inputs estilo Tkinter
            u = st.text_input("Nombre de Usuario:", key="user_login", placeholder="", label_visibility="visible")
            p = st.text_input("Contraseña de Seguridad:", type="password", key="pass_login", label_visibility="visible")
            
            # Estilo para labels blancos
            st.markdown("""
                <style>
                label { color: white !important; font-weight: bold !important; font-family: Arial !important; font-size: 13px !important; }
                div[data-testid="stTextInput"] input { text-align: center; }
                </style>
            """, unsafe_allow_html=True)

            btn = st.button("🔓 INGRESAR AL SISTEMA", use_container_width=True, type="primary")

            if btn:
                if u == "admin" and p == "dramiren2026":
                    st.session_state.login = True
                    st.rerun()
                else:
                    st.error("Acceso Denegado: El usuario o la contraseña son incorrectos.")

        # SOPORTE ABAJO COMO TU TKINTER
        st.markdown("""
        <div style="background-color:#002244; padding:10px; border-radius:6px; text-align:center; border:1px solid #001a33; margin-top:15px;">
            <p style="color:#99ccff; font-weight:bold; font-size:11px; font-family:Arial; margin:0px;">Soporte Técnico de Control Soporte.DramirenG:</p>
            <p style="color:white; font-size:11px; font-family:Arial; margin:2px;">📞 Celular: 959237626</p>
            <p style="color:white; font-size:11px; font-family:Arial; margin:2px;">✉️ Correo: Soporte.DramirenG@hotmail.com</p>
        </div>
        """, unsafe_allow_html=True)

    st.stop()

st.sidebar.title("⚙️ Configuración")
api_token = st.sidebar.text_input("Token API Perú", type="password")
formato = st.sidebar.radio("Formato:", ["A4 Vertical - 4 por hoja (una sobre otra)", "A4 Horizontal - toda la hoja", "Térmica 100x150"])
up1 = st.sidebar.file_uploader("Logo DG arriba derecha", type=["png","jpg","jpeg"])
if up1:
    open("logo_dg.png","wb").write(up1.getbuffer())
    open("logo_imagen1.png","wb").write(up1.getbuffer())
up2 = st.sidebar.file_uploader("Marcas abajo", type=["png","jpg","jpeg"])
if up2:
    open("marcas.png","wb").write(up2.getbuffer())
    open("logo_imagen2.png","wb").write(up2.getbuffer())

st.title("🏷️ DramirenG")
c1,c2,c3,c4,c5 = st.columns([1.2,1.8,1.2,1,1])
with c1:
    dni=st.text_input("DNI/RUC", key="dni")
    if st.button("🔍 Buscar"):
        nom=buscar_dni_api(dni, api_token)
        if nom: st.session_state["nombre"]=nom; st.rerun()
        else: st.warning("No encontrado")
with c2: nombre=st.text_input("Nombre", key="nombre")
with c3:
    destino_input=st.text_input("DESTINO", key="destino", placeholder="LIMA")
    ms=[p for p in PROVINCIAS if destino_input.upper() in p][:5] if destino_input else []
    if ms and destino_input.upper() not in PROVINCIAS:
        sel=st.selectbox("Sugerencias", ms)
        if st.button("✅ Usar"): st.session_state["destino"]=sel; st.rerun()
    destino=st.session_state.get("destino","").upper()
with c4: factura=st.text_input("FACTURA", key="factura").upper()
with c5: celular=st.text_input("CELULAR", key="celular")

c6,c7,c8=st.columns([1,1,2])
with c6: b1=st.number_input("Bulto",1,99,1)
with c7: b2=st.number_input("Total",1,99,4)
with c8:
    if st.button("➕ Agregar", type="primary", use_container_width=True):
        if dni and nombre and destino:
            for i in range(1,b2+1):
                st.session_state.lista.append({"dni":dni,"nombre":nombre,"destino":destino,"factura":factura,"celular":celular,"b1":i,"b2":b2})
            st.session_state["do_clear"]=True; st.rerun()

# FUNCION UNICA CON MAS MARGEN - COMO TU FOTO LIMA
def dibujar(x,y,d,w,h,pdf):
    pdf.set_draw_color(0,0,0)
    pdf.set_line_width(0.9 if h<100 else 1.2)
    pdf.rect(x,y,w,h)
    pdf.line(x, y+22, x+w, y+22)

    # HEADER - AREQUIPA + (1/4)
    pdf.set_font("Helvetica","B", 32 if h<100 else 55) # LETRA MAS GRANDE
    pdf.set_xy(x+6, y+4)
    pdf.cell(95, 13, d['destino'], align='L')

    pdf.set_font("Helvetica","B", 18 if h<100 else 30)
    pdf.set_xy(x+95, y+6)
    pdf.cell(35, 11, f"({d['b1']}/{d['b2']})", align='C')

    # LOGO DG ARRIBA DEL QR - A LA DERECHA GRANDE
    l1="logo_dg.png" if os.path.exists("logo_dg.png") else "logo_imagen1.png" if os.path.exists("logo_imagen1.png") else None
    if l1:
        # ARRIBA DEL QR, lado derecho, como tu foto AREQUIPA
        pdf.image(l1, x+w-48, y+2, 44, 28 if h<100 else 50)

    # CUERPO - deja espacio a la derecha para el DG
    pdf.set_font("Arial","B", 12 if h<100 else 20)
    pdf.set_xy(x+6, y+26)
    pdf.cell(w-55, 6, f"ATT: {d['nombre'].upper()}")

    pdf.set_xy(x+6, y+33)
    pdf.set_font("Arial","", 10 if h<100 else 14)
    pdf.cell(w-55, 5, f"DNI/RUC: {d['dni']}  |  FACTURA: {d['factura'].upper()}")

    pdf.set_xy(x+6, y+40)
    pdf.set_font("Arial","B", 11 if h<100 else 16)
    pdf.cell(w-55, 5, f"CELULAR: {d['celular']}")

    # MARCAS ABAJO
    l2="marcas.png" if os.path.exists("marcas.png") else "logo_imagen2.png" if os.path.exists("logo_imagen2.png") else None
    if l2:
        pdf.image(l2, x+6, y+h-14, 120, 9)

    # QR ABAJO DEL DG
    qr=qrcode.make(f"{d['nombre']}|{d['destino']}|{d['dni']}"); qr.save("qr.png")
    pdf.image("qr.png", x+w-20, y+h-16, 13, 13)

# GENERAR PDF
if st.session_state.lista:
    st.dataframe(st.session_state.lista, use_container_width=True)

    if "Térmica" in formato:
        pdf=FPDF(orientation='P', unit='mm', format=(100,150))
        pdf.set_auto_page_break(auto=False)
        for d in st.session_state.lista:
            pdf.add_page()
            dibujar(3,3,d,94,144,pdf)
    elif "Horizontal" in formato:
        pdf=FPDF(orientation='L', format='A4')
        for d in st.session_state.lista:
            pdf.add_page()
            dibujar(5,5,d,287,200,pdf)
    else:
        pdf=FPDF(orientation='P', format='A4')
        pdf.set_auto_page_break(auto=False)
        pos_y=[14, 82, 150, 218] # mas separacion
        for i,d in enumerate(st.session_state.lista):
            if i%4==0: pdf.add_page()
            dibujar(10,pos_y[i%4],d,190,60,pdf)

    pdf_bytes = bytes(pdf.output())
    c1,c2=st.columns(2)
    with c1:
        st.download_button("⬇️ DESCARGAR PDF", pdf_bytes, "etiquetas_DramirenG.pdf", "application/pdf", use_container_width=True, type="primary")
    with c2:
        if st.button("🗑️ Limpiar", use_container_width=True):
            st.session_state.lista=[]; st.rerun()
else:
    st.info("Vacío. Agrega clientes.")                                                                                                                                                             
