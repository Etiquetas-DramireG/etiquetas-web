import streamlit as st
from fpdf import FPDF
import os, qrcode

st.set_page_config(page_title="DramirenG", layout="wide")
if "login" not in st.session_state: st.session_state.login=False
if "lista" not in st.session_state: st.session_state.lista=[]

if st.session_state.get("do_clear"):
    for k in ["dni","nombre","destino","factura","celular"]:
        st.session_state.pop(k, None)
    st.session_state["do_clear"]=False

# LISTA DE PROVINCIAS COMO TU PROGRAMA ORIGINAL
PROVINCIAS = ["CHACHAPOYAS","BAGUA","BONGARA","HUARAZ","CASMA","HUARMEY","SANTA","YUNGAY","ABANCAY","ANDAHUAYLAS","AREQUIPA","CAMANA","ISLAY","AYACUCHO","HUAMANGA","CAJAMARCA","JAEN","CALLAO","CUSCO","URUBAMBA","HUANCAVELICA","HUANUCO","LEONCIO PRADO","ICA","PISCO","HUANCAYO","SATIPO","TARMA","TRUJILLO","CHEPEN","PACASMAYO","CHICLAYO","LAMBAYEQUE","LIMA","BARRANCA","CAÑETE","HUARAL","HUAURA","IQUITOS","PUERTO MALDONADO","MOQUEGUA","ILO","PASCO","OXAPAMPA","PIURA","SULLANA","TALARA","PUNO","SAN ROMAN","MOYOBAMBA","TARAPOTO","TACNA","TUMBES","PUCALLPA","CORONEL PORTILLO"]

if not st.session_state.login:
    st.title("🔐 DramirenG")
    u=st.text_input("Usuario"); p=st.text_input("Clave",type="password")
    if st.button("Ingresar"):
        if u=="admin" and p=="dramiren2026":
            st.session_state.login=True; st.rerun()
    st.stop()

st.sidebar.title("🖨️ Formato")
formato = st.sidebar.radio("Elige:", ["A4 Vertical - 4 por hoja", "A4 Horizontal - toda la hoja", "Térmica 100x150"])

st.title("🏷️ DramirenG")
c1,c2,c3,c4,c5 = st.columns(5)
with c1: dni=st.text_input("DNI/RUC", key="dni", placeholder="")
with c2: nombre=st.text_input("Nombre", key="nombre", placeholder="")

with c3: 
    # DESTINO CON AUTOCOMPLETADO
    destino_input = st.text_input("DESTINO", key="destino", placeholder="Escribe AREQ...")
    if destino_input:
        matches = [p for p in PROVINCIAS if destino_input.upper() in p][:5]
        if matches:
            sel = st.selectbox("👇 Sugerencias:", matches, key="sug_destino")
            if st.button("✅ Usar", key="btn_dest"):
                st.session_state["destino"] = sel
                st.rerun()
    destino = st.session_state.get("destino","").upper()

with c4: 
    # FACTURA EN MAYUSCULAS
    factura_raw = st.text_input("FACTURA / GUIA", key="factura", placeholder="F001-XXXXXX")
    factura = factura_raw.upper()
with c5: celular=st.text_input("CELULAR", key="celular", placeholder="")

c6,c7,c8 = st.columns([1,1,2])
with c6: b1=st.number_input("Bulto",1,99,1)
with c7: b2=st.number_input("Total",1,99,4)
with c8:
    if st.button("➕ Agregar", type="primary", use_container_width=True):
        if dni and nombre and destino:
            for i in range(1, b2+1):
                st.session_state.lista.append({"dni":dni,"nombre":nombre,"destino":destino,"factura":factura,"celular":celular,"b1":i,"b2":b2})
            st.session_state["do_clear"]=True; st.rerun()

if st.session_state.lista:
    st.dataframe(st.session_state.lista,use_container_width=True)
    if st.button(f"📄 GENERAR PDF - {formato}", type="primary", use_container_width=True):
        def dibujar(x,y,d,w,h, pdf):
            pdf.rect(x,y,w,h)
            pdf.set_font("Helvetica","B", 28 if h<100 else 50)
            pdf.set_xy(x+3,y+2); pdf.cell(w*0.6,12 if h<100 else 22, d['destino'], align='L')
            pdf.set_font("Helvetica","B", 20 if h<100 else 32)
            pdf.set_xy(x+w*0.6,y+2); pdf.cell(w*0.2,12 if h<100 else 22, f"({d['b1']}/{d['b2']})", align='C')
            l1 = "logo_dg.png" if os.path.exists("logo_dg.png") else "logo_imagen1.png" if os.path.exists("logo_imagen1.png") else None
            if l1: pdf.image(l1, x+w-35 if h<100 else x+w-70, y+1, 33 if h<100 else 65, 18 if h<100 else 35)
            pdf.line(x,y+16 if h<100 else y+30, x+w, y+16 if h<100 else y+30)
            pdf.set_font("Arial","B",10 if h<100 else 20); pdf.set_xy(x+3,y+18 if h<100 else y+35); pdf.cell(w,5 if h<100 else 10,f"ATT: {d['nombre'].upper()}")
            pdf.set_xy(x+3,y+24 if h<100 else y+48); pdf.set_font("Arial","",8 if h<100 else 14); pdf.cell(w,4,f"DNI/RUC: {d['dni']} | FACTURA: {d['factura'].upper()}")
            pdf.set_xy(x+3,y+29 if h<100 else y+58); pdf.set_font("Arial","B",9 if h<100 else 16); pdf.cell(w,4,f"CELULAR: {d['celular']}")
            l2 = "marcas.png" if os.path.exists("marcas.png") else "logo_imagen2.png" if os.path.exists("logo_imagen2.png") else None
            if l2: pdf.image(l2, x+5, y+h-22 if h<100 else y+h-45, 130 if h<100 else 180, 12 if h<100 else 28)
            qr=qrcode.make(f"{d['nombre']}|{d['destino']}"); qr.save("qr.png")
            pdf.image("qr.png", x+w-23 if h<100 else x+w-45, y+h-22 if h<100 else y+h-45, 18 if h<100 else 38, 18 if h<100 else 38)

        if "Térmica" in formato:
            pdf=FPDF(orientation='P', unit='mm', format=(100,150))
            pdf.set_auto_page_break(auto=False)
            for d in st.session_state.lista: pdf.add_page(); dibujar(3,3,d,94,144,pdf)
        elif "Horizontal" in formato:
            pdf=FPDF(orientation='L', format='A4')
            for d in st.session_state.lista: pdf.add_page(); dibujar(5,5,d,287,200,pdf)
        else:
            pdf=FPDF(orientation='P', format='A4'); pdf.set_auto_page_break(auto=False)
            pos_y = [10, 75, 140, 205]
            for i,d in enumerate(st.session_state.lista):
                if i%4==0: pdf.add_page()
                dibujar(10, pos_y[i%4], d, 190, 60, pdf)

        st.download_button("⬇️ DESCARGAR PDF", bytes(pdf.output()), "etiquetas_DramirenG.pdf", mime="application/pdf", use_container_width=True)
        st.balloons()
    if st.button("🗑️ Limpiar"): st.session_state.lista=[]; st.rerun()
