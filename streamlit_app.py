import streamlit as st
from fpdf import FPDF
import requests, os, qrcode

st.set_page_config(page_title="DramirenG", layout="wide")
if "login" not in st.session_state: st.session_state.login=False
if "lista" not in st.session_state: st.session_state.lista=[]
if "clientes" not in st.session_state: st.session_state.clientes={}

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

st.sidebar.title("⚙️")
api_token = st.sidebar.text_input("Token API (opcional)", type="password")
up_logo = st.sidebar.file_uploader("Sube tu logo DG", type=["png","jpg","jpeg"])
if up_logo: open("logo_dg.png","wb").write(up_logo.getbuffer())
up_marcas = st.sidebar.file_uploader("Sube marcas (Nike etc) - opcional", type=["png","jpg"])
if up_marcas: open("marcas.png","wb").write(up_marcas.getbuffer())

if st.sidebar.button("Cerrar"): st.session_state.login=False; st.rerun()

st.title("🏷️ DramirenG - Etiqueta Horizontal")
c1,c2,c3,c4,c5 = st.columns(5)
with c1:
    dni=st.text_input("DNI/RUC")
    if st.button("🔍 Buscar"):
        if dni in st.session_state.clientes:
            st.session_state['nom']=st.session_state.clientes[dni][1]
        else:
            try:
                tipo="dni" if len(dni)==8 else "ruc"
                h={"Authorization": f"Bearer {api_token}"} if api_token else {}
                r=requests.get(f"https://api.apis.net.pe/v1/{tipo}?numero={dni}",headers=h,timeout=6).json()
                nom=r.get('nombre') or r.get('razonSocial') or ""
                if nom: st.session_state['nom']=nom; st.success(nom)
            except: pass
with c2: nombre=st.text_input("Nombre", value=st.session_state.get('nom',''))
with c3: destino=st.text_input("DESTINO", value="AREQUIPA")
with c4: factura=st.text_input("FACTURA", value="F001-XXXXXX")
with c5: celular=st.text_input("CELULAR", value="959237626")

c6,c7,c8 = st.columns(3)
with c6: b1=st.number_input("Bulto",1,100,1)
with c7: b2=st.number_input("Total",1,100,4)
with c8:
    st.write("")
    if st.button("➕ Agregar",type="primary"):
        st.session_state.lista.append({"dni":dni,"nombre":nombre,"destino":destino.upper(),"factura":factura,"celular":celular,"b1":b1,"b2":b2})
        guardar_cliente(dni,nombre,celular)
        st.success("Agregado")

if st.session_state.lista:
    st.dataframe(st.session_state.lista,use_container_width=True)
    if st.button(f"📄 GENERAR PDF ({len(st.session_state.lista)})",type="primary"):
        pdf=FPDF(orientation='L', format='A4') # Horizontal
        for item in st.session_state.lista:
            pdf.add_page()
            x,y,w,h = 10,10,277,190
            pdf.rect(x,y,w,h)

            # Destino
            pdf.set_xy(x+5,y+2); pdf.set_font("Arial","B",45)
            pdf.cell(170,25,item['destino'],align="L")
            pdf.set_xy(x+140,y+2); pdf.set_font("Arial","B",28)
            pdf.cell(40,25,f"({item['b1']}/{item['b2']})",align="C")

            # Logo DG derecha (grande)
            if os.path.exists("logo_dg.png"):
                pdf.image("logo_dg.png", x=x+w-75, y=y+2, w=70, h=70)
            elif os.path.exists("logo_imagen1.png"):
                pdf.image("logo_imagen1.png", x=x+w-75, y=y+2, w=70, h=70)

            # Linea
            pdf.line(x, y+28, x+w, y+28)

            # Datos
            pdf.set_xy(x+5,y+30); pdf.set_font("Arial","B",20)
            pdf.cell(190,10,f"ATT: {item['nombre'].upper()[:45]}",ln=True)
            pdf.set_x(x+5); pdf.set_font("Arial","",13)
            pdf.cell(190,7,f"DNI/RUC: {item['dni']} | FACTURA: {item['factura']}",ln=True)
            pdf.set_x(x+5); pdf.set_font("Arial","B",14)
            pdf.cell(190,8,f"CELULAR: {item['celular']}",ln=True)

            # Marcas abajo
            yy = y+110
            if os.path.exists("marcas.png"):
                pdf.image("marcas.png", x=x+5, y=yy, w=180, h=30)
            else:
                pdf.set_xy(x+5,yy); pdf.set_font("Arial","B",12)
                # Dibuja texto si no hay imagen
                pdf.image("https://upload.wikimedia.org/wikipedia/commons/a/a6/Logo_NIKE.svg", x=x+10, y=yy, w=35)
                # Fallback texto
                pdf.set_xy(x+5,yy+5); pdf.cell(180,20,"NIKE PUMA adidas Reebok",align="L")

            # QR
            qr = qrcode.make(f"{item['nombre']}|{item['destino']}|{item['dni']}|{item['celular']}")
            qr.save("qr.png")
            pdf.image("qr.png", x=x+w-40, y=yy, w=35, h=35)

        pdf_bytes=pdf.output(dest='S').encode('latin-1')
        st.download_button("⬇️ DESCARGAR PDF", pdf_bytes, "etiquetas_DramirenG.pdf")
        st.balloons()

st.info("Sube tu logo DG en la izquierda. Sin logo igual funciona.")
