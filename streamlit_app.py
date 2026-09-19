import streamlit as st
from fpdf import FPDF
import requests, os, qrcode

st.set_page_config(page_title="DramirenG", layout="wide")

if "login" not in st.session_state: st.session_state.login=False
if "lista" not in st.session_state: st.session_state.lista=[]
if "clientes" not in st.session_state: st.session_state.clientes={}

# FIX DEL ERROR: limpiar ANTES de crear los inputs
if st.session_state.get("do_clear"):
    for k in ["dni","nombre","destino","factura","celular"]:
        st.session_state.pop(k, None)
    st.session_state["do_clear"]=False

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
api_token = st.sidebar.text_input("Token API (si falla el API)", type="password", placeholder="Vacío = funciona")
st.sidebar.divider()
st.sidebar.subheader("🖨️ Impresora")
tipo = st.sidebar.radio("Elige:", ["🖨️ Normal A4", "🏷️ Térmica 100x150"])
modo = st.sidebar.selectbox("Formato", ["Vertical 1 por hoja (Como tu foto)", "Vertical 4 por hoja (Diferentes clientes)", "Horizontal 1 por hoja"] if "Normal" in tipo else ["100x150 - 1 por sticker"])

up1 = st.sidebar.file_uploader("Logo DG (arriba derecha)", type=["png","jpg","jpeg"])
if up1: open("logo_dg.png","wb").write(up1.getbuffer())
up2 = st.sidebar.file_uploader("Marcas Nike etc (abajo)", type=["png","jpg","jpeg"])
if up2: open("marcas.png","wb").write(up2.getbuffer())

if st.sidebar.button("Cerrar"): st.session_state.login=False; st.rerun()

st.title("🏷️ DramirenG - Despacho")

c1,c2,c3,c4,c5 = st.columns(5)
with c1:
    dni = st.text_input("DNI/RUC", key="dni", placeholder="")
    if st.button("🔍 Buscar"):
        if dni in st.session_state.clientes:
            st.session_state["nombre"]=st.session_state.clientes[dni][1]
            st.rerun()
        else:
            try:
                t="dni" if len(dni)==8 else "ruc"
                h={"Authorization": f"Bearer {api_token}"} if api_token else {}
                r=requests.get(f"https://api.apis.net.pe/v1/{t}?numero={dni}",headers=h,timeout=6).json()
                nom=r.get('nombre') or r.get('razonSocial') or ""
                if nom:
                    st.session_state["nombre"]=nom
                    st.rerun()
            except: pass
with c2: nombre = st.text_input("Nombre", key="nombre", placeholder="")
with c3: destino = st.text_input("DESTINO", key="destino", placeholder="")
with c4: factura = st.text_input("FACTURA", key="factura", placeholder="")
with c5: celular = st.text_input("CELULAR", key="celular", placeholder="")

c6,c7,c8 = st.columns([1,1,2])
with c6: b1=st.number_input("Bulto",1,99,1)
with c7: b2=st.number_input("Total",1,99,1)
with c8:
    if st.button("➕ Agregar", type="primary", use_container_width=True):
        if dni and nombre and destino:
            st.session_state.lista.append({"dni":dni,"nombre":nombre,"destino":destino.upper(),"factura":factura,"celular":celular,"b1":b1,"b2":b2})
            guardar_cliente(dni,nombre,celular)
            st.session_state["do_clear"]=True
            st.rerun()
        else: st.error("Falta DNI / Nombre / Destino")

if st.session_state.lista:
    st.dataframe(st.session_state.lista,use_container_width=True)
    if st.button(f"📄 GENERAR PDF ({len(st.session_state.lista)})", type="primary"):

        def dibujar_etiqueta_foto(pdf, item, x, y, w, h):
            # === EXACTO A TU FOTO ===
            pdf.rect(x,y,w,h) # borde total

            # 1. CABECERA SULLANA + (1 + LOGO
            h_header = 18
            pdf.rect(x,y,w,h_header)
            pdf.set_xy(x+3, y+1); pdf.set_font("Arial","B",16)
            pdf.cell(w*0.55, h_header-2, item['destino'].upper(), align="L")
            pdf.set_xy(x+w*0.55, y+1); pdf.set_font("Arial","B",11)
            pdf.cell(15, h_header-2, f"({item['b1']}", align="C")

            logo_path = "logo_dg.png" if os.path.exists("logo_dg.png") else "logo_imagen1.png" if os.path.exists("logo_imagen1.png") else None
            if logo_path:
                pdf.image(logo_path, x=x+w-32, y=y+1, w=30, h=16)

            # 2. DATOS
            y_datos = y + h_header
            pdf.set_xy(x+3, y_datos+2); pdf.set_font("Arial","B",8)
            pdf.cell(w-6, 4, f"ATT: {item['nombre'].upper()}", ln=True)
            pdf.set_x(x+3); pdf.set_font("Arial","",6)
            pdf.cell(w-6, 3.5, f"DNI: {item['dni']} | FACT: {item['factura']}", ln=True)
            pdf.set_x(x+3); pdf.set_font("Arial","B",6.5)
            pdf.cell(w-6, 4, f"CEL: {item['celular']}", ln=True)

            # 3. ZONA BLANCA GRANDE (como tu foto)
            y_marcas = y + h - 22
            pdf.line(x, y_marcas, x+w, y_marcas) # linea inferior

            # 4. MARCAS + QR ABAJO
            marcas_path = "marcas.png" if os.path.exists("marcas.png") else "logo_imagen2.png" if os.path.exists("logo_imagen2.png") else None
            if marcas_path:
                pdf.image(marcas_path, x=x+2, y=y_marcas+1, w=w-26, h=20)

            qr = qrcode.make(f"{item['nombre']}|{item['destino']}|{item['dni']}|{item['celular']}")
            qr.save("qr.png")
            pdf.image("qr.png", x=x+w-22, y=y_marcas+1, w=20, h=20)

        # GENERAR SEGUN IMPRESORA
        if "Térmica" in tipo:
            pdf=FPDF(orientation='P', unit='mm', format=(100,150))
            for it in st.session_state.lista:
                pdf.add_page()
                dibujar_etiqueta_foto(pdf,it,0,0,100,150)
        else:
            if "4 por hoja" in modo:
                pdf=FPDF(orientation='P', format='A4')
                for i,it in enumerate(st.session_state.lista):
                    if i%4==0: pdf.add_page()
                    pos=i%4
                    xx=10 if pos%2==0 else 110
                    yy=10 if pos<2 else 150
                    dibujar_etiqueta_foto(pdf,it,xx,yy,90,130)
            elif "Horizontal" in modo:
                pdf=FPDF(orientation='L', format='A4')
                for it in st.session_state.lista:
                    pdf.add_page()
                    dibujar_etiqueta_foto(pdf,it,10,10,277,190)
            else: # Vertical 1 por hoja COMO TU FOTO
                pdf=FPDF(orientation='P', format='A4')
                for it in st.session_state.lista:
                    pdf.add_page()
                    dibujar_etiqueta_foto(pdf,it,20,10,170,270)

        pdf_bytes = bytes(pdf.output())
        st.download_button("⬇️ DESCARGAR PDF", pdf_bytes, "etiquetas_DramirenG.pdf", mime="application/pdf")
        st.balloons()

    if st.button("🗑️ Limpiar lista"):
        st.session_state.lista=[]; st.rerun()
else:
    st.info("Todo vacío, como pediste. Agrega clientes.")
