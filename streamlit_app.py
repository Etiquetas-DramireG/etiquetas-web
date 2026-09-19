import streamlit as st
from fpdf import FPDF
import requests, os
from datetime import datetime

st.set_page_config(page_title="DramirenG - Despacho", layout="wide")
if "login" not in st.session_state: st.session_state.login=False
if "lista" not in st.session_state: st.session_state.lista=[]
if "clientes" not in st.session_state: st.session_state.clientes={}

# Cargar clientes
if os.path.exists("clientes_guardados.txt"):
    try:
        with open("clientes_guardados.txt","r",encoding="utf-8") as f:
            for line in f:
                p=line.strip().split("|")
                if len(p)>=2: st.session_state.clientes[p[0]]=p
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

# SIDEBAR
st.sidebar.title("⚙️ Configuración")
st.sidebar.success("Conectado: admin")

st.sidebar.subheader("🔑 API (opcional)")
st.sidebar.caption("Si la búsqueda falla, pega tu API aquí")
api_token = st.sidebar.text_input("Token API apis.net.pe", placeholder="Pega tu token si tienes", type="password")
api_url_custom = st.sidebar.text_input("URL API propia (opcional)", placeholder="https://tu-api.com/ruc=")

logo1_on = st.sidebar.checkbox("Usar Logo 1", value=True)
logo2_on = st.sidebar.checkbox("Usar Logo 2", value=False)
up1 = st.sidebar.file_uploader("Cambiar Logo 1", type=["png","jpg","jpeg"])
up2 = st.sidebar.file_uploader("Cambiar Logo 2", type=["png","jpg","jpeg"])
if up1: open("logo_imagen1.png","wb").write(up1.getbuffer())
if up2: open("logo_imagen2.png","wb").write(up2.getbuffer())

formato = st.sidebar.selectbox("🖨️ Impresora", ["A3 - 1 gigante (Recomendado)", "A4 - 4 por hoja", "Termica 100x150mm"], index=0)
if st.sidebar.button("Cerrar sesión"):
    st.session_state.login=False; st.rerun()

# APP
st.title("🏷️ DramirenG - Despacho Masivo")
c1,c2,c3 = st.columns([1,1,1])

with c1:
    dni = st.text_input("DNI / RUC", placeholder="", value="") # VACIO, sin ejemplo
    if st.button("🔍 Buscar"):
        if dni in st.session_state.clientes:
            d=st.session_state.clientes[dni]
            st.session_state['nombre_temp']=d[1]
            st.session_state['direc_temp']=d[3] if len(d)>3 else ""
            st.success(f"Guardado: {d[1]}")
        else:
            encontrado=False
            # 1. Si puso URL propia
            if api_url_custom:
                try:
                    r=requests.get(f"{api_url_custom}{dni}",timeout=6).json()
                    nom=r.get('nombre') or r.get('razonSocial') or r.get('nombreCompleto') or ""
                    if nom:
                        st.session_state['nombre_temp']=nom
                        st.success(nom); encontrado=True
                except: pass
            # 2. Si puso token
            if not encontrado and api_token:
                try:
                    tipo="dni" if len(dni)==8 else "ruc"
                    url=f"https://api.apis.net.pe/v1/{tipo}?numero={dni}"
                    r=requests.get(url,headers={"Authorization":f"Bearer {api_token}"},timeout=6).json()
                    nom=r.get('nombre') or r.get('razonSocial') or ""
                    if nom:
                        st.session_state['nombre_temp']=nom
                        st.success(nom); encontrado=True
                except: pass
            # 3. Intento sin token (puede fallar)
            if not encontrado:
                try:
                    tipo="dni" if len(dni)==8 else "ruc"
                    url=f"https://api.apis.net.pe/v1/{tipo}?numero={dni}"
                    r=requests.get(url,timeout=6).json()
                    nom=r.get('nombre') or r.get('razonSocial') or ""
                    if nom:
                        st.session_state['nombre_temp']=nom
                        st.success(nom); encontrado=True
                except: pass
            if not encontrado:
                st.warning("No se encontró online. Escribe manual. Si sigue fallando, pega tu token a la izquierda.")

with c2:
    nombre = st.text_input("Nombre Cliente", value=st.session_state.get('nombre_temp',''), placeholder="")
    destino = st.selectbox("Destino", ["","LIMA","ICA","PIURA","SULLANA","TRUJILLO","CHICLAYO","AREQUIPA","CUSCO","TUMBES","CHIMBOTE","HUANCAYO","TACNA","JULIACA","PUNO","OTRO"])
    if destino=="OTRO": destino=st.text_input("Escribe destino")

with c3:
    direccion = st.text_input("Dirección (opcional)", value=st.session_state.get('direc_temp',''), placeholder="")
    nota = st.text_input("Nota opcional", placeholder="")
    col_a,col_b=st.columns(2)
    with col_a:
        if st.button("➕ Agregar a lista",type="primary"):
            if dni and nombre and destino:
                st.session_state.lista.append({"dni":dni,"nombre":nombre,"destino":destino,"direc":direccion,"nota":nota})
                guardar_cliente(dni,nombre,destino,direccion)
                st.success(f"Agregado: {nombre}")
                # Limpiar para siguiente
                st.session_state['nombre_temp']=""; st.session_state['direc_temp']=""
            else: st.error("Falta DNI/Nombre/Destino")
    with col_b:
        if st.button("🗑️ Limpiar lista"): st.session_state.lista=[]; st.rerun()

if st.session_state.lista:
    st.divider()
    st.subheader(f"📦 Lista: {len(st.session_state.lista)} etiquetas")
    st.dataframe(st.session_state.lista, use_container_width=True)
    if st.button(f"📄 GENERAR PDF MASIVO ({len(st.session_state.lista)})",type="primary"):
        pdf=FPDF(orientation='P',unit='mm',format=(100,150) if "Termica" in formato else 'A4' if "A4" in formato else 'A3')
        def dibujar(pdf,data,x,y,w,h):
            # Fondo blanco y borde grueso
            pdf.set_fill_color(255,255,255)
            pdf.rect(x,y,w,h,'DF')
            # Logo grande a la izquierda
            if logo1_on and os.path.exists("logo_imagen1.png"):
                try: pdf.image("logo_imagen1.png", x=x+3, y=y+3, w=22, h=18)
                except: pass
            # DESTINO GIGANTE
            pdf.set_xy(x, y+2)
            pdf.set_font("Arial","B",22)
            pdf.cell(w,12,f"{data['destino'].upper()}",align="C",ln=True)
            
            # NOMBRE GIGANTE CENTRADO
            pdf.set_xy(x+5, y+30)
            pdf.set_font("Arial","B",16)
            pdf.multi_cell(w-10, 9, f"{data['nombre'].upper()}", align="C")
            
            # DNI GRANDE ABAJO
            pdf.set_xy(x, y+h-25)
            pdf.set_font("Arial","B",14)
            pdf.cell(w,10,f"{data['dni']}",align="C",ln=True)
            
            # Direccion / Nota chiquito
            if data['direc']:
                pdf.set_xy(x, y+h-15)
                pdf.set_font("Arial","",9)
                pdf.cell(w,5,f"{data['direc'][:40]}",align="C",ln=True)
            
            # Logo 2 a la derecha si quiere
            if logo2_on and os.path.exists("logo_imagen2.png"):
                try: pdf.image("logo_imagen2.png", x=x+w-25, y=y+3, w=20)
                except: pass
            pdf.set_xy(x,y+10); pdf.set_font("Arial","B",10); pdf.cell(w,6,f"{data['nombre'][:30]}",align="C",ln=True)
            pdf.set_x(x); pdf.set_font("Arial","",8); pdf.cell(w,5,f"{data['dni']}",align="C",ln=True)
            if data['direc']: pdf.set_x(x); pdf.cell(w,5,f"{data['direc'][:35]}",align="C",ln=True)
            if data['nota']: pdf.set_x(x); pdf.set_font("Arial","I",8); pdf.cell(w,5,f"{data['nota']}",align="C",ln=True)
            pdf.rect(x,y,w,h)
        if "Termica" in formato:
            for it in st.session_state.lista: pdf.add_page(); dibujar(pdf,it,0,0,100,150)
        elif "A3" in formato:
            for it in st.session_state.lista: pdf.add_page(); dibujar(pdf,it,10,10,277,400)
        else:
            for i,it in enumerate(st.session_state.lista):
                if i%4==0: pdf.add_page()
                pos=i%4; x=10 if pos%2==0 else 110; y=10 if pos<2 else 150
                dibujar(pdf,it,x,y,90,120)
        pdf_bytes=pdf.output(dest='S').encode('latin-1')
        st.download_button("⬇️ DESCARGAR PDF",pdf_bytes,file_name=f"despacho_{datetime.now().strftime('%d%m')}.pdf")
        st.balloons()
else:
    st.info("👆 Agrega clientes arriba. Se guardan automático.")
