            import streamlit as st
from fpdf import FPDF
import os, qrcode, requests, sys

st.set_page_config(page_title="DramirenG", layout="wide")
if "login" not in st.session_state: st.session_state.login=False
if "lista" not in st.session_state: st.session_state.lista=[]
if "clientes" not in st.session_state: st.session_state.clientes={}

# FIX ERROR ROJO
if st.session_state.get("do_clear"):
    for k in ["dni","nombre","destino","factura","celular"]:
        st.session_state.pop(k, None)
    st.session_state["do_clear"]=False

# Cargar BD local como tu.exe
if os.path.exists("clientes_guardados.txt"):
    try:
        with open("clientes_guardados.txt","r",encoding="utf-8") as f:
            for l in f:
                p=l.strip().split(",")
                if len(p)>=2: st.session_state.clientes[p[0]]=p
    except: pass

PROVINCIAS = ["CHACHAPOYAS","BAGUA","BONGARA","HUARAZ","CASMA","HUARMEY","SANTA","YUNGAY","ABANCAY","ANDAHUAYLAS","AREQUIPA","CAMANA","ISLAY","AYACUCHO","HUAMANGA","CAJAMARCA","JAEN","CALLAO","CUSCO","URUBAMBA","HUANCAVELICA","HUANUCO","LEONCIO PRADO","ICA","PISCO","HUANCAYO","SATIPO","TARMA","TRUJILLO","CHEPEN","PACASMAYO","CHICLAYO","LAMBAYEQUE","LIMA","BARRANCA","CAÑETE","HUARAL","HUAURA","IQUITOS","PUERTO MALDONADO","MOQUEGUA","ILO","PASCO","OXAPAMPA","PIURA","SULLANA","TALARA","PUNO","SAN ROMAN","MOYOBAMBA","TARAPOTO","TACNA","TUMBES","PUCALLPA","CORONEL PORTILLO"]

def buscar_dni_api(dni, token):
    dni=dni.strip()
    if len(dni)==7 and dni.isdigit(): dni="0"+dni
    # 1. Buscar en TXT local
    if dni in st.session_state.clientes:
        return st.session_state.clientes[dni][1]
    # 2. Buscar en API
    if not token: return None
    try:
        if len(dni)==8:
            r=requests.post("https://apiperu.dev", json={"dni":dni}, headers={"Authorization":f"Bearer {token}"}, timeout=6, verify=False)
            if r.status_code==200 and r.json().get("success"):
                d=r.json()["data"]
                return f"{d.get('nombres','')} {d.get('apellido_paterno','')} {d.get('apellido_materno','')}".strip().upper()
        else:
            r=requests.post("https://apiperu.dev", json={"ruc":dni}, headers={"Authorization":f"Bearer {token}"}, timeout=6, verify=False)
            if r.status_code==200 and r.json().get("success"):
                return r.json()["data"].get("nombre_o_razon_social","").upper()
    except: pass
    # 3. Fallback apis.net.pe
    try:
        t="dni" if len(dni)==8 else "ruc"
        r=requests.get(f"https://apis.net.pe{t}?numero={dni}", headers={"Authorization":f"Bearer {token}"} if token else {}, timeout=5).json()
        return (r.get('nombre') or r.get('razonSocial') or "").upper()
    except: return None

if not st.session_state.login:
    st.title("🔐 DramirenG")
    u=st.text_input("Usuario"); p=st.text_input("Clave",type="password")
    if st.button("Ingresar"):
        if u=="admin" and p=="dramiren2026":
            st.session_state.login=True; st.rerun()
        else: st.error("Error")
    st.stop()

# SIDEBAR - CONFIGURACIÓN e IMÁGENES
st.sidebar.title("⚙️ Configuración")
api_token = st.sidebar.text_input("Token API Perú", type="password", help="Pega tu token de apiperu.dev")
st.sidebar.divider()
st.sidebar.subheader("🖨️ Formato")
formato = st.sidebar.radio("Impresión:", ["A4 Vertical - 4 por hoja (una sobre otra)", "A4 Horizontal - toda la hoja", "Térmica 100x150"])

st.sidebar.divider()
st.sidebar.subheader("🖼️ Logos - DONDE VAN")
up_logo1 = st.sidebar.file_uploader("Logo DG (arriba derecha)", type=["png","jpg","jpeg"])
if up_logo1:
    with open("logo_dg.png","wb") as f: f.write(up_logo1.getbuffer())
    with open("logo_imagen1.png","wb") as f: f.write(up_logo1.getbuffer())
    st.sidebar.success("✅ Logo DG guardado")

up_logo2 = st.sidebar.file_uploader("Marcas Nike Puma Adidas (abajo)", type=["png","jpg","jpeg"])
if up_logo2:
    with open("marcas.png","wb") as f: f.write(up_logo2.getbuffer())
    with open("logo_imagen2.png","wb") as f: f.write(up_logo2.getbuffer())
    st.sidebar.success("✅ Marcas guardadas")

if os.path.exists("logo_imagen1.png"): st.sidebar.image("logo_imagen1.png", width=100)
if os.path.exists("logo_imagen2.png"): st.sidebar.image("logo_imagen2.png", width=150)

if st.sidebar.button("Cerrar sesión"): st.session_state.login=False; st.rerun()

st.title("🏷️ DramirenG - Despacho")
c1,c2,c3,c4,c5 = st.columns([1.2,1.8,1.2,1,1])
with c1:
    dni=st.text_input("DNI/RUC", key="dni", placeholder="")
    if st.button("🔍 Buscar DNI/RUC", use_container_width=True):
        nom = buscar_dni_api(dni, api_token)
        if nom:
            st.session_state["nombre"]=nom
            if dni in st.session_state.clientes:
                cli=st.session_state.clientes[dni]
                if len(cli)>=3 and cli[2]: st.session_state["celular"]=cli[2]
                if len(cli)>=4 and cli[3]: st.session_state["destino"]=cli[3]
            st.success(f"Encontrado: {nom}")
            st.rerun()
        else:
            st.warning("No encontrado, escribe manual o revisa token")

with c2: nombre=st.text_input("Nombre", key="nombre", placeholder="")
with c3:
    destino_input = st.text_input("DESTINO", key="destino", placeholder="Ej: AREQ")
    if destino_input:
        ms = [p for p in PROVINCIAS if destino_input.upper() in p][:5]
        if ms and destino_input.upper() not in PROVINCIAS:
            sel=st.selectbox("Sugerencias:", ms, key="sug")
            if st.button("✅ Usar destino"):
                st.session_state["destino"]=sel; st.rerun()
    destino = st.session_state.get("destino","").upper()

with c4:
    fact_raw=st.text_input("FACTURA/GUIA", key="factura", placeholder="F001-123")
    factura=fact_raw.upper()
with c5: celular=st.text_input("CELULAR", key="celular", placeholder="")

c6,c7,c8 = st.columns([1,1,2])
with c6: b1=st.number_input("Bulto",1,99,1)
with c7: b2=st.number_input("Total",1,99,4)
with c8:
    if st.button("➕ Agregar", type="primary", use_container_width=True):
        if dni and nombre and destino:
            for i in range(1, b2+1):
                st.session_state.lista.append({"dni":dni,"nombre":nombre,"destino":destino,"factura":factura,"celular":celular,"b1":i,"b2":b2})
            with open("clientes_guardados.txt","a",encoding="utf-8") as f:
                f.write(f"{dni},{nombre.upper()},{celular},{destino},,\n")
            st.session_state["do_clear"]=True; st.rerun()

def dibujar(x,y,d,w,h,pdf):
    # MÁS MARGEN EXTERNO
    pdf.set_draw_color(0,0,0)
    pdf.set_line_width(0.7 if h<100 else 1.2)
    pdf.rect(x,y,w,h)

    # 1. HEADER CON MÁS AIRE
    pdf.set_font("Helvetica","B", 26 if h<100 else 48)
    pdf.set_xy(x+5, y+3)
    pdf.cell(100, 12 if h<100 else 22, d['destino'], align='L')

    # (1/4) - lo alejamos del logo DG
    pdf.set_font("Helvetica","B", 16 if h<100 else 28)
    pdf.set_xy(x+108, y+4)
    pdf.cell(30, 10 if h<100 else 20, f"({d['b1']}/{d['b2']})", align='C')

    # LOGO DG
    l1="logo_dg.png" if os.path.exists("logo_dg.png") else "logo_imagen1.png" if os.path.exists("logo_imagen1.png") else None
    if l1:
        pdf.image(l1, x+w-34, y+2.5, 28, 12 if h<100 else 28)

    pdf.line(x, y+18, x+w, y+18)

    # 2. DATOS CON MÁS MARGEN IZQUIERDO
    pdf.set_font("Arial","B",10 if h<100 else 18)
    pdf.set_xy(x+5, y+20)
    pdf.cell(w-10,5,f"ATT: {d['nombre'].upper()}")
    
    pdf.set_xy(x+5, y+26)
    pdf.set_font("Arial","",8 if h<100 else 13)
    pdf.cell(w-10,4,f"DNI/RUC: {d['dni']} | FACTURA: {d['factura'].upper()}")
    
    pdf.set_xy(x+5, y+32)
    pdf.set_font("Arial","B",9 if h<100 else 15)
    pdf.cell(w-10,4,f"CELULAR: {d['celular']}")

    # 3. FOOTER - MARCAS Y QR CON MÁS MARGEN
    l2="marcas.png" if os.path.exists("marcas.png") else "logo_imagen2.png" if os.path.exists("logo_imagen2.png") else None
    if l2:
        pdf.image(l2, x+6, y+h-16, 115, 10 if h<100 else 20)

    # QR
    qr=qrcode.make(f"{d['nombre']}|{d['destino']}|{d['dni']}"); qr.save("qr.png")
    pdf.image("qr.png", x+w-24, y+h-20, 16, 16 if h<100 else 32)

# SECCIÓN DE PROCESAMIENTO DE LA LISTA
if st.session_state.lista:
    st.dataframe(st.session_state.lista, use_container_width=True)
    
    col_acciones = st.columns([1, 1])
    with col_acciones[0]:
        if st.button("🖨️ Generar PDF", type="secondary", use_container_width=True):
            pass # Mantenemos el botón estructural si quieres procesar algo antes
            
        # Lógica para armar el PDF según formato seleccionado
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
            pos_y=[12, 80, 148, 216] 
            for i, d in enumerate(st.session_state.lista):
                if i%4==0: pdf.add_page()
                dibujar(10,pos_y[i%4],d,190,60,pdf)

        # Botón de Descarga real
        pdf_bytes = pdf.output(dest='S').encode('latin-1') if isinstance(pdf.output(dest='S'), str) else pdf.output(dest='S')
        st.download_button("⬇️ DESCARGAR PDF", data=pdf_bytes, file_name="etiquetas_DramirenG.pdf", mime="application/pdf", use_container_width=True)
        st.balloons()
        
    with col_acciones[1]:
        if st.button("🗑️ Limpiar lista", use_container_width=True): 
            st.session_state.lista=[]
            st.rerun()
else:
    st.info("Vacío. Sube los 2 logos en la barra izquierda y pega tu Token API para buscar clientes.")
                                                                                                                                                                      
