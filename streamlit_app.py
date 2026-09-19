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
            r=requests.post("https://apiperu.dev/api/dni", json={"dni":dni}, headers={"Authorization":f"Bearer {token}"}, timeout=6, verify=False)
            if r.status_code==200 and r.json().get("success"):
                d=r.json()["data"]
                return f"{d.get('nombres','')} {d.get('apellido_paterno','')} {d.get('apellido_materno','')}".strip().upper()
        else:
            r=requests.post("https://apiperu.dev/api/ruc", json={"ruc":dni}, headers={"Authorization":f"Bearer {token}"}, timeout=6, verify=False)
            if r.status_code==200 and r.json().get("success"):
                return r.json()["data"].get("nombre_o_razon_social","").upper()
    except: pass
    # 3. Fallback apis.net.pe
    try:
        t="dni" if len(dni)==8 else "ruc"
        r=requests.get(f"https://api.apis.net.pe/v1/{t}?numero={dni}", headers={"Authorization":f"Bearer {token}"} if token else {}, timeout=5).json()
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

# SIDEBAR - DONDE VAN LAS IMAGENES Y API
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
            # si tiene datos guardados local
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
            # guardar en txt como tu.exe
            with open("clientes_guardados.txt","a",encoding="utf-8") as f:
                f.write(f"{dni},{nombre.upper()},{celular},{destino},,\n")
            st.session_state["do_clear"]=True; st.rerun()

if st.session_state.lista:
    st.dataframe(st.session_state.lista,use_container_width=True)
    if st.button(f"📄 GENERAR PDF - {formato}", type="primary", use_container_width=True):
        def dibujar(x,y,d,w,h,pdf):
            pdf.set_draw_color(0,0,0); pdf.set_line_width(0.6 if h<100 else 1.2)
            pdf.rect(x,y,w,h)
            # CABECERA DESTINO + BULTOS + LOGO DG
            pdf.set_font("Helvetica","B", 28 if h<100 else 50)
            pdf.set_xy(x+3,y+2); pdf.cell(w*0.6,12 if h<100 else 22, d['destino'], align='L')
            pdf.set_font("Helvetica","B", 18 if h<100 else 30)
            pdf.set_xy(x+w*0.6,y+2); pdf.cell(w*0.2,12 if h<100 else 22, f"({d['b1']}/{d['b2']})", align='C')
            l1="logo_dg.png" if os.path.exists("logo_dg.png") else "logo_imagen1.png" if os.path.exists("logo_imagen1.png") else None
            if l1: pdf.image(l1, x+w-35 if h<100 else x+w-70, y+1, 33 if h<100 else 65, 14 if h<100 else 28)
            pdf.line(x,y+16 if h<100 else y+28, x+w, y+16 if h<100 else y+28)
            # DATOS
            pdf.set_font("Arial","B",10 if h<100 else 18); pdf.set_xy(x+3,y+18 if h<100 else y+32); pdf.cell(w,5,f"ATT: {d['nombre'].upper()}")
            pdf.set_xy(x+3,y+24 if h<100 else y+44); pdf.set_font("Arial","",8 if h<100 else 13); pdf.cell(w,4,f"DNI/RUC: {d['dni']} | FACTURA: {d['factura'].upper()}")
            pdf.set_xy(x+3,y+30 if h<100 else y+54); pdf.set_font("Arial","B",9 if h<100 else 15); pdf.cell(w,4,f"CELULAR: {d['celular']}")
            # FOOTER MARCAS + QR
            l2="marcas.png" if os.path.exists("marcas.png") else "logo_imagen2.png" if os.path.exists("logo_imagen2.png") else None
            if l2: pdf.image(l2, x+5, y+h-18 if h<100 else y+h-35, 120 if h<100 else 170, 12 if h<100 else 22)
            qr=qrcode.make(f"{d['nombre']}|{d['destino']}|{d['dni']}"); qr.save("qr.png")
            pdf.image("qr.png", x+w-22 if h<100 else x+w-40, y+h-20 if h<100 else y+h-38, 16 if h<100 else 32, 16 if h<100 else 32)

        if "Térmica" in formato:
            pdf=FPDF(orientation='P', unit='mm', format=(100,150)); pdf.set_auto_page_break(auto=False)
            for d in st.session_state.lista: pdf.add_page(); dibujar(3,3,d,94,144,pdf)
        elif "Horizontal" in formato:
            pdf=FPDF(orientation='L', format='A4')
            for d in st.session_state.lista: pdf.add_page(); dibujar(5,5,d,287,200,pdf)
        else:
            pdf=FPDF(orientation='P', format='A4'); pdf.set_auto_page_break(auto=False)
            pos_y=[10,75,140,205]
            for i,d in enumerate(st.session_state.lista):
                if i%4==0: pdf.add_page()
                dibujar(10,pos_y[i%4],d,190,60,pdf)

        st.download_button("⬇️ DESCARGAR PDF", bytes(pdf.output()), "etiquetas_DramirenG.pdf", mime="application/pdf", use_container_width=True)
        st.balloons()
    if st.button("🗑️ Limpiar lista"): st.session_state.lista=[]; st.rerun()
else:
    st.info("Vacío. Sube los 2 logos en la barra izquierda y pega tu Token API para buscar clientes.")
