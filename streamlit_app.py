import streamlit as st
from fpdf import FPDF
import requests, os, csv
from datetime import datetime

st.set_page_config(page_title="DramirenG - Despacho", layout="wide")
if "login" not in st.session_state: st.session_state.login=False
if "lista" not in st.session_state: st.session_state.lista=[]
if "clientes" not in st.session_state: st.session_state.clientes={}

# Cargar clientes guardados
if os.path.exists("clientes_guardados.txt"):
    try:
        with open("clientes_guardados.txt","r",encoding="utf-8") as f:
            for line in f:
                parts=line.strip().split("|")
                if len(parts)>=2: st.session_state.clientes[parts[0]]=parts
    except: pass

def guardar_cliente(dni,nombre,destino,direc):
    with open("clientes_guardados.txt","a",encoding="utf-8") as f:
        f.write(f"{dni}|{nombre}|{destino}|{direc}\n")
    st.session_state.clientes[dni]=[dni,nombre,destino,direc]

# LOGIN
if not st.session_state.login:
    st.title("🔐 DramirenG - Login")
    u=st.text_input("Usuario"); p=st.text_input("Clave",type="password")
    if st.button("Ingresar"):
        if u=="admin" and p=="dramiren2026":
            st.session_state.login=True; st.rerun()
        else: st.error("Incorrecto")
    st.stop()

# SIDEBAR - LOGOS
st.sidebar.title("⚙️ Configuración")
st.sidebar.success("Conectado: admin")
logo1_on = st.sidebar.checkbox("Usar Logo 1", value=True)
logo2_on = st.sidebar.checkbox("Usar Logo 2", value=False)
uploaded1 = st.sidebar.file_uploader("Cambiar Logo 1 (PNG/JPG)", type=["png","jpg","jpeg"])
uploaded2 = st.sidebar.file_uploader("Cambiar Logo 2", type=["png","jpg","jpeg"])
if uploaded1:
    open("logo_imagen1.png","wb").write(uploaded1.getbuffer())
    st.sidebar.success("Logo 1 actualizado")
if uploaded2:
    open("logo_imagen2.png","wb").write(uploaded2.getbuffer())
    st.sidebar.success("Logo 2 actualizado")

formato = st.sidebar.selectbox("🖨️ Tipo Impresora", ["A4 - 4 etiquetas por hoja", "A3 - 1 gigante", "Termica 100x150mm"])
if st.sidebar.button("Cerrar sesión"):
    st.session_state.login=False; st.rerun()

# APP
st.title("🏷️ DramirenG - Despacho Masivo")

c1,c2,c3 = st.columns([1,1,1])
with c1:
    dni = st.text_input("DNI / RUC", placeholder="20601298733")
    # BUSQUEDA INTELIGENTE: primero en guardados, luego API
    if st.button("🔍 Buscar"):
        if dni in st.session_state.clientes:
            d = st.session_state.clientes[dni]
            st.session_state['nombre_temp']=d[1]
            st.session_state['destino_temp']=d[2] if len(d)>2 else "LIMA"
            st.session_state['direc_temp']=d[3] if len(d)>3 else ""
            st.success(f"Cliente guardado: {d[1]}")
        else:
            try:
                url = f"https://api.apis.net.pe/v1/dni?numero={dni}" if len(dni)==8 else f"https://api.apis.net.pe/v1/ruc?numero={dni}"
                r=requests.get(url,timeout=6).json()
                nom=r.get('nombre') or r.get('razonSocial') or r.get('nombreCompleto') or ""
                if nom:
                    st.session_state['nombre_temp']=nom
                    st.success(nom)
                else: st.warning("No encontrado, escribe manual")
            except: st.warning("Sin internet, escribe manual")

with c2:
    nombre = st.text_input("Nombre Cliente", value=st.session_state.get('nombre_temp',''))
    destino = st.selectbox("Destino", ["LIMA","ICA","PIURA","SULLANA","TRUJILLO","CHICLAYO","AREQUIPA","CUSCO","TUMBES","CHIMBOTE","HUANCAYO","TACNA","JULIACA","PUNO","OTRO"], index=0)
    if destino=="OTRO": destino = st.text_input("Escribe destino")

with c3:
    direccion = st.text_input("Dirección (opcional)", value=st.session_state.get('direc_temp',''))
    nota = st.text_input("Nota opcional (ej: Producto)", placeholder="Dejar vacío si no quiere")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("➕ Agregar a lista", type="primary"):
            if dni and nombre and destino:
                st.session_state.lista.append({"dni":dni,"nombre":nombre,"destino":destino,"direc":direccion,"nota":nota})
                guardar_cliente(dni,nombre,destino,direccion)
                st.success(f"Agregado: {nombre}")
            else: st.error("Falta DNI/Nombre/Destino")
    with col_b:
        if st.button("🗑️ Limpiar lista"):
            st.session_state.lista=[]; st.rerun()

# LISTA MASIVA
if st.session_state.lista:
    st.divider()
    st.subheader(f"📦 Lista para imprimir: {len(st.session_state.lista)} etiquetas")
    st.dataframe(st.session_state.lista, use_container_width=True)

    if st.button(f"📄 GENERAR PDF MASIVO ({len(st.session_state.lista)} etiquetas)", type="primary"):
        if "Termica" in formato:
            pdf=FPDF(orientation='P', unit='mm', format=(100,150))
        elif "A3" in formato:
            pdf=FPDF(format='A3')
        else:
            pdf=FPDF(format='A4')

        def dibujar_etiqueta(pdf, data, x, y, w, h):
            pdf.set_xy(x,y)
            pdf.set_font("Arial","B",14 if h>50 else 10)
            pdf.cell(w,8,f"{data['destino']}",align="C", ln=True)
            # logos
            if logo1_on and os.path.exists("logo_imagen1.png"):
                try: pdf.image("logo_imagen1.png", x=x+2, y=y+2, w=15)
                except: pass
            if logo2_on and os.path.exists("logo_imagen2.png"):
                try: pdf.image("logo_imagen2.png", x=x+w-17, y=y+2, w=15)
                except: pass

            pdf.set_xy(x, y+10)
            pdf.set_font("Arial","B",11 if h>50 else 8)
            pdf.cell(w,6,f"{data['nombre'][:30]}",align="C",ln=True)
            pdf.set_x(x)
            pdf.set_font("Arial","",9 if h>50 else 7)
            pdf.cell(w,5,f"DNI/RUC: {data['dni']}",align="C",ln=True)
            if data['direc']:
                pdf.set_x(x); pdf.cell(w,5,f"{data['direc'][:35]}",align="C",ln=True)
            if data['nota']:
                pdf.set_x(x); pdf.set_font("Arial","I",8); pdf.cell(w,5,f"{data['nota'][:30]}",align="C",ln=True)
            # borde
            pdf.rect(x,y,w,h)

        if "Termica" in formato:
            for item in st.session_state.lista:
                pdf.add_page()
                dibujar_etiqueta(pdf,item,0,0,100,150)
        elif "A3" in formato:
            for item in st.session_state.lista:
                pdf.add_page()
                dibujar_etiqueta(pdf,item,10,10,277,400)
        else: # A4 4 por hoja
            for i, item in enumerate(st.session_state.lista):
                if i%4==0: pdf.add_page()
                pos = i%4
                x = 10 if pos%2==0 else 110
                y = 10 if pos<2 else 150
                dibujar_etiqueta(pdf,item,x,y,90,120)

        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button("⬇️ DESCARGAR PDF MASIVO", pdf_bytes, file_name=f"despacho_masivo_{datetime.now().strftime('%d%m%Y')}.pdf")
        st.balloons()

else:
    st.info("👆 Agrega clientes arriba para impresión masiva. Ya se guardan automáticamente para la próxima.")
    if st.session_state.clientes:
        st.write(f"Tienes {len(st.session_state.clientes)} clientes guardados")
