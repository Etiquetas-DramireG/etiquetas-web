import streamlit as st
from fpdf import FPDF
import os, qrcode, requests

st.set_page_config(page_title="DramirenG", layout="wide")
if "login" not in st.session_state: st.session_state.login=False
if "lista" not in st.session_state: st.session_state.lista=[]

# ESTO ARREGLA EL ERROR ROJO QUE TE SALÍA
if st.session_state.get("do_clear"):
    for k in ["dni","nombre","destino","factura","celular"]:
        st.session_state.pop(k, None)
    st.session_state["do_clear"]=False

if not st.session_state.login:
    st.title("🔐 DramirenG")
    u=st.text_input("Usuario"); p=st.text_input("Clave",type="password")
    if st.button("Ingresar"):
        if u=="admin" and p=="dramiren2026":
            st.session_state.login=True; st.rerun()
        else: st.error("Error")
    st.stop()

st.sidebar.title("⚙️ Config")
formato = st.sidebar.selectbox("🖨️ Formato de Impresión", ["A4 Vertical - 4 por hoja (Como tu foto)", "A4 Horizontal - 1 Gigante", "Térmica 100x150"])
api_token = st.sidebar.text_input("Token API (opcional)", type="password")

up1 = st.sidebar.file_uploader("Logo DG arriba", type=["png","jpg","jpeg"])
if up1: open("logo_dg.png","wb").write(up1.getbuffer())
up2 = st.sidebar.file_uploader("Marcas Nike etc abajo", type=["png","jpg","jpeg"])
if up2: open("marcas.png","wb").write(up2.getbuffer())

if st.sidebar.button("Cerrar"): st.session_state.login=False; st.rerun()

st.title("🏷️ DramirenG - Despacho")
c1,c2,c3,c4,c5 = st.columns(5)
with c1:
    dni=st.text_input("DNI/RUC", key="dni", placeholder="")
    if st.button("🔍 Buscar") and api_token:
        try:
            t="dni" if len(dni)==8 else "ruc"
            h={"Authorization": f"Bearer {api_token}"}
            r=requests.get(f"https://api.apis.net.pe/v1/{t}?numero={dni}",headers=h,timeout=6).json()
            nom=r.get('nombre') or r.get('razonSocial') or ""
            if nom: st.session_state["nombre"]=nom; st.rerun()
        except: pass
with c2: nombre=st.text_input("Nombre", key="nombre", placeholder="")
with c3: destino=st.text_input("DESTINO", key="destino", placeholder="")
with c4: factura=st.text_input("FACTURA", key="factura", placeholder="")
with c5: celular=st.text_input("CELULAR", key="celular", placeholder="")

c6,c7,c8 = st.columns([1,1,2])
with c6: b_inicio=st.number_input("Bulto Inicio",1,99,1)
with c7: b_total=st.number_input("Total Bultos",1,99,4)
with c8:
    if st.button("➕ Agregar", type="primary", use_container_width=True):
        if dni and nombre and destino:
            for i in range(b_inicio, b_total+1):
                # si pones 4 clientes diferentes, agregas 1 por 1 con total 1
                # si pones 1 cliente con total 4, se crean 4 etiquetas (1/4)(2/4)(3/4)(4/4)
                st.session_state.lista.append({"dni":dni,"nombre":nombre,"destino":destino.upper(),"factura":factura,"celular":celular,"b1":i,"b2":b_total})
            st.session_state["do_clear"]=True
            st.rerun()
        else: st.error("Falta DNI / Nombre / Destino")

if st.session_state.lista:
    st.dataframe(st.session_state.lista,use_container_width=True)
    if st.button(f"📄 GENERAR PDF ({len(st.session_state.lista)} etiquetas)", type="primary", use_container_width=True):

        def dibujar_mini(pdf, x, y, d):
            pdf.set_draw_color(0,0,0); pdf.set_line_width(0.6)
            pdf.rect(x, y, 195, 65)
            pdf.set_font("Helvetica","B",34)
            pdf.set_xy(x+4, y+3); pdf.cell(130,12,d['destino'].upper(),align='L')
            pdf.set_font("Helvetica","B",24)
            pdf.set_xy(x+105, y+4.5); pdf.cell(30,10,f"({d['b1']}/{d['b2']})",align='L')
            pdf.line(x+2, y+17, x+134, y+17)
            pdf.set_font("Arial","B",17.5)
            pdf.set_xy(x+4, y+19); pdf.multi_cell(130,6,f"ATT: {d['nombre'].upper()}",align='L')
            yd=pdf.get_y()+1
            pdf.set_font("Arial","",12.5); pdf.set_xy(x+4, yd); pdf.cell(48,4.5,f"DNI/RUC: {d['dni']}")
            pdf.set_font("Arial","B",12.5); pdf.set_xy(x+55, yd); pdf.cell(75,4.5,f"  |  FACTURA: {d['factura']}")
            yd=pdf.get_y()+1
            pdf.set_font("Arial","B",13); pdf.set_xy(x+4, yd); pdf.cell(130,4.5,f"CELULAR: {d['celular']}")

            l1 = "logo_dg.png" if os.path.exists("logo_dg.png") else "logo_imagen1.png" if os.path.exists("logo_imagen1.png") else None
            if l1: pdf.image(l1, x+136, y+2, 57, 38)
            l2 = "marcas.png" if os.path.exists("marcas.png") else "logo_imagen2.png" if os.path.exists("logo_imagen2.png") else None
            if l2: pdf.image(l2, x+4, y+48, 150, 13.5)
            qr=qrcode.make(f"{d['nombre']}|{d['destino']}|{d['dni']}|{d['b1']}/{d['b2']}")
            qr.save("qr.png")
            pdf.image("qr.png", x+172, y+43, 19.5, 19.5)

        def dibujar_maxi(pdf, x, y, d):
            pdf.set_line_width(1.2); pdf.rect(x+5,y+5,287,200)
            pdf.set_font("Helvetica","B",56); pdf.set_xy(x+10,y+10); pdf.cell(200,22,d['destino'].upper(),align='L')
            pdf.set_font("Helvetica","B",38); pdf.set_xy(x+210,y+11); pdf.cell(75,20,f"({d['b1']}/{d['b2']})",align='R')
            pdf.line(x+5,y+36,x+292,y+36)
            pdf.set_font("Arial","B",26); pdf.set_xy(x+10,y+42); pdf.multi_cell(180,10,f"ATT: {d['nombre'].upper()}",align='L')
            yd=pdf.get_y()+4
            pdf.set_font("Arial","",18); pdf.set_xy(x+10,yd); pdf.cell(180,8,f"DNI/RUC: {d['dni']}   |   FACTURA: {d['factura']}")
            yd=pdf.get_y()+4
            pdf.set_font("Arial","B",20); pdf.set_xy(x+10,yd); pdf.cell(180,8,f"CELULAR: {d['celular']}")
            l1 = "logo_dg.png" if os.path.exists("logo_dg.png") else "logo_imagen1.png" if os.path.exists("logo_imagen1.png") else None
            if l1: pdf.image(l1, x=x+200, y=y+40, w=87, h=65)
            l2 = "marcas.png" if os.path.exists("marcas.png") else "logo_imagen2.png" if os.path.exists("logo_imagen2.png") else None
            if l2: pdf.image(l2, x=x+10, y=y+150, w=220, h=45)
            qr=qrcode.make(f"{d['nombre']}|{d['destino']}|{d['dni']}"); qr.save("qr.png")
            pdf.image("qr.png", x=x+240, y=y+150, w=45, h=45)

        def dibujar_termica(pdf, x, y, d):
            pdf.set_line_width(0.8); pdf.rect(x+3,y+3,94,144)
            pdf.set_font("Helvetica","B",36 if len(d['destino'])<9 else 24); pdf.set_xy(x+4,y+4); pdf.cell(63,12,d['destino'].upper(),align='L')
            pdf.set_font("Helvetica","B",18); pdf.set_xy(x+68,y+7); pdf.cell(25,8,f"({d['b1']}/{d['b2']})",align='R')
            pdf.set_font("Arial","B",13); pdf.set_xy(x+6,y+21); pdf.multi_cell(88,5,f"ATT: {d['nombre'].upper()}",align='L')
            yd=pdf.get_y()+1.5
            pdf.set_font("Arial","",10.5); pdf.set_xy(x+6,yd); pdf.cell(88,4.5,f"DNI/RUC: {d['dni']}")
            pdf.set_xy(x+6,pdf.get_y()+0.5); pdf.cell(88,4.5,f"FACTURA: {d['factura']}")
            pdf.set_xy(x+6,pdf.get_y()+0.5); pdf.set_font("Arial","B",11); pdf.cell(88,4.5,f"CELULAR: {d['celular']}")
            pdf.line(x+3,y+62,x+97,y+62); pdf.line(x+3,y+120,x+97,y+120)
            l1 = "logo_dg.png" if os.path.exists("logo_dg.png") else "logo_imagen1.png" if os.path.exists("logo_imagen1.png") else None
            if l1: pdf.image(l1, x+7, y+66, 86, 48)
            l2 = "marcas.png" if os.path.exists("marcas.png") else "logo_imagen2.png" if os.path.exists("logo_imagen2.png") else None
            if l2: pdf.image(l2, x+6, y+124, 60, 18)
            qr=qrcode.make(f"{d['nombre']}|{d['destino']}"); qr.save("qr.png")
            pdf.image("qr.png", x+72, y+122, 22, 22)

        # DISTRIBUCIÓN COMO TU CÓDIGO ORIGINAL
        if formato == "A4 Horizontal - 1 Gigante":
            pdf=FPDF(orientation='L', format='A4')
            for d in st.session_state.lista:
                pdf.add_page(); dibujar_maxi(pdf,0,0,d)
        elif "Térmica" in formato:
            pdf=FPDF(orientation='P', unit='mm', format=(100,150))
            pdf.set_auto_page_break(auto=False)
            for d in st.session_state.lista:
                pdf.add_page(); dibujar_termica(pdf,0,0,d)
        else: # A4 Vertical - 4 por hoja
            pdf=FPDF(orientation='P', format='A4')
            pos=[(8,5),(8,75),(8,145),(8,215)]
            for i,d in enumerate(st.session_state.lista):
                if i%4==0: pdf.add_page()
                x,y=pos[i%4]
                dibujar_mini(pdf,x,y,d)

        pdf_bytes = bytes(pdf.output())
        st.download_button("⬇️ DESCARGAR PDF - 4 POR HOJA", pdf_bytes, "etiquetas_4x1.pdf", mime="application/pdf", use_container_width=True)
        st.balloons()

    if st.button("🗑️ Limpiar lista"): st.session_state.lista=[]; st.rerun()
else:
    st.info("Todo vacío. Agrega clientes. Si pones Total 4, te genera (1/4)(2/4)(3/4)(4/4) en 1 sola hoja A4.")
