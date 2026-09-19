import streamlit as st
from fpdf import FPDF
import requests, os, qrcode

st.set_page_config(page_title="DramirenG", layout="wide")
if "login" not in st.session_state: st.session_state.login=False
if "lista" not in st.session_state: st.session_state.lista=[]
if "clientes" not in st.session_state: st.session_state.clientes={}

# Limpiar campos ANTES de crearlos (para evitar el error rojo)
if st.session_state.get("limpiar"):
    for k in ["dni","nombre","destino","factura","celular"]:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state["limpiar"]=False

if os.path.exists("clientes_guardados.txt"):
    try:
        with open("clientes_guardados.txt","r",encoding="utf-8") as f:
            for l in f:
                p=l.strip().split("|")
                if len(p)>=2: st.session_state.clientes[p[0]]=p
    except: pass

def guardar_cliente(dni,nom,cel):
    with open("clientes_guardados.txt","a",encoding="utf-8") as f:
        f.write(f"{dni}|{nom}||{cel}\n")

if not st.session_state.login:
    st.title("🔐 DramirenG")
    u=st.text_input("Usuario"); p=st.text_input("Clave",type="password")
    if st.button("Ingresar"):
        if u=="admin" and p=="dramiren2026":
            st.session_state.login=True; st.rerun()
        else: st.error("Error")
    st.stop()

st.sidebar.title("⚙️ Config")
api_token = st.sidebar.text_input("Token API (opcional)", type="password", placeholder="Vacío = funciona")
st.sidebar.divider()
st.sidebar.subheader("🖨️ Tipo de Impresora")
tipo_impresora = st.sidebar.radio("Elige:", ["🖨️ Impresora Normal (A4)", "🏷️ Impresora Térmica (100x150)"])
if "Normal" in tipo_impresora:
    formato = st.sidebar.selectbox("Formato", ["Horizontal - 1 por hoja (Grande)", "Vertical - 4 por hoja (Ahorra papel)"])
else:
    formato = st.sidebar.selectbox("Formato", ["100x150mm - 1 por sticker", "80x100mm - Pequeña"])

up_logo = st.sidebar.file_uploader("Logo DG", type=["png","jpg","jpeg"])
if up_logo: open("logo_dg.png","wb").write(up_logo.getbuffer())
up_marcas = st.sidebar.file_uploader("Marcas (Nike etc)", type=["png","jpg"])
if up_marcas: open("marcas.png","wb").write(up_marcas.getbuffer())
if st.sidebar.button("Cerrar sesión"): st.session_state.login=False; st.rerun()

st.title("🏷️ DramirenG - Despacho")

c1,c2,c3,c4,c5 = st.columns(5)
with c1:
    dni=st.text_input("DNI/RUC", key="dni", placeholder="")
    if st.button("🔍 Buscar"):
        if dni in st.session_state.clientes:
            st.session_state["nombre"]=st.session_state.clientes[dni][1]
            st.rerun()
        else:
            try:
                tipo="dni" if len(dni)==8 else "ruc"
                h={"Authorization": f"Bearer {api_token}"} if api_token else {}
                r=requests.get(f"https://api.apis.net.pe/v1/{tipo}?numero={dni}",headers=h,timeout=6).json()
                nom=r.get('nombre') or r.get('razonSocial') or ""
                if nom:
                    st.session_state["nombre"]=nom
                    st.rerun()
            except: st.warning("Escribe manual")
with c2: nombre=st.text_input("Nombre", key="nombre", placeholder="")
with c3: destino=st.text_input("DESTINO", key="destino", placeholder="")
with c4: factura=st.text_input("FACTURA", key="factura", placeholder="")
with c5: celular=st.text_input("CELULAR", key="celular", placeholder="")

c6,c7,c8 = st.columns([1,1,2])
with c6: b1=st.number_input("Bulto N°",1,100,1)
with c7: b2=st.number_input("Total",1,100,1)
with c8:
    st.write("")
    if st.button("➕ Agregar", type="primary", use_container_width=True):
        if dni and nombre and destino:
            st.session_state.lista.append({"dni":dni,"nombre":nombre,"destino":destino.upper(),"factura":factura,"celular":celular,"b1":b1,"b2":b2})
            guardar_cliente(dni,nombre,celular)
            st.session_state["limpiar"]=True
            st.rerun()
        else: st.error("Falta DNI / Nombre / Destino")

if st.session_state.lista:
    st.divider()
    st.dataframe(st.session_state.lista,use_container_width=True)
    col1,col2=st.columns(2)
    with col1:
        if st.button(f"📄 GENERAR PDF ({len(st.session_state.lista)})", type="primary", use_container_width=True):
            def dibujar(pdf, item, x, y, w, h):
                pdf.rect(x,y,w,h)
                pdf.set_xy(x+3,y+2); pdf.set_font("Arial","B",22 if w<150 else 32)
                pdf.cell(w*0.6,12 if w<150 else 18,item['destino'],align="L")
                pdf.set_xy(x+w*0.6,y+2); pdf.set_font("Arial","B",12 if w<150 else 20)
                pdf.cell(w*0.15,12 if w<150 else 18,f"({item['b1']}/{item['b2']})",align="C")
                logo_path = "logo_dg.png" if os.path.exists("logo_dg.png") else "logo_imagen1.png" if os.path.exists("logo_imagen1.png") else None
                if logo_path:
                    pdf.image(logo_path, x=x+w-30 if w<150 else x+w-48, y=y+1, w=28 if w<150 else 44, h=28 if w<150 else 44)
                pdf.line(x, y+16 if w<150 else y+26, x+w, y+16 if w<150 else y+26)
                pdf.set_xy(x+3,y+18 if w<150 else y+28); pdf.set_font("Arial","B",8 if w<150 else 13)
                pdf.cell(w-6,5 if w<150 else 7,f"ATT: {item['nombre'].upper()[:38]}",ln=True)
                pdf.set_x(x+3); pdf.set_font("Arial","",6 if w<150 else 9)
                pdf.cell(w-6,4 if w<150 else 5,f"DNI: {item['dni']} | FACT: {item['factura']}",ln=True)
                pdf.set_x(x+3); pdf.set_font("Arial","B",7 if w<150 else 11)
                pdf.cell(w-6,4 if w<150 else 5,f"CEL: {item['celular']}",ln=True)
                yy = y+h-20 if w<150 else y+h-32
                pdf.line(x, yy-3, x+w, yy-3)
                marcas_path = "marcas.png" if os.path.exists("marcas.png") else "logo_imagen2.png" if os.path.exists("logo_imagen2.png") else None
                if marcas_path:
                    pdf.image(marcas_path, x=x+2, y=yy, w=w-24 if w<150 else w-40, h=16 if w<150 else 24)
                qr = qrcode.make(f"{item['nombre']}|{item['destino']}|{item['dni']}")
                qr.save("qr.png")
                pdf.image("qr.png", x=x+w-20 if w<150 else x+w-32, y=yy, w=18 if w<150 else 28, h=18 if w<150 else 28)

            if "Térmica" in tipo_impresora:
                fmt = (100,150) if "100x150" in formato else (80,100)
                pdf=FPDF(orientation='P', unit='mm', format=fmt)
                for item in st.session_state.lista:
                    pdf.add_page()
                    dibujar(pdf,item,0,0,fmt[0],fmt[1])
            else:
                if "Vertical" in formato:
                    pdf=FPDF(orientation='P', format='A4')
                    for i,item in enumerate(st.session_state.lista):
                        if i%4==0: pdf.add_page()
                        pos=i%4; x=10 if pos%2==0 else 110; y=10 if pos<2 else 150
                        dibujar(pdf,item,x,y,90,130)
                else:
                    pdf=FPDF(orientation='L', format='A4')
                    for item in st.session_state.lista:
                        pdf.add_page()
                        dibujar(pdf,item,10,10,277,190)

            pdf_bytes = bytes(pdf.output())
            st.download_button("⬇️ DESCARGAR PDF", pdf_bytes, "etiquetas.pdf", mime="application/pdf", use_container_width=True)
            st.balloons()
    with col2:
        if st.button("🗑️ Limpiar lista", use_container_width=True):
            st.session_state.lista=[]; st.rerun()
else:
    st.info("Todo vacío. Agrega clientes. Ahora sí sin error.")
