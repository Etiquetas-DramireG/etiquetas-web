import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io

st.set_page_config(page_title="Etiquetas DramireG", layout="centered")
st.title("🏷️ Etiquetas - DramireG Sullana")
st.write("Sube tu Excel y genera tu PDF listo para imprimir")

archivo = st.file_uploader("📁 Sube tu Excel", type=["xlsx","xls"])

if archivo:
    df = pd.read_excel(archivo)
    st.success(f"✅ {len(df)} etiquetas encontradas")
    st.dataframe(df.head(10))

    if st.button("🚀 Generar PDF de Etiquetas"):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        x, y = 10*mm, height - 30*mm
        count = 0
        
        for i, row in df.iterrows():
            texto = " | ".join([f"{k}: {v}" for k,v in row.items() if pd.notna(v)])
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x, y, texto[:110])
            c.rect(x-2*mm, y-5*mm, 90*mm, 15*mm)
            
            x += 95*mm
            if x > width - 90*mm:
                x = 10*mm
                y -= 25*mm
            if y < 20*mm:
                c.showPage()
                y = height - 30*mm
            
            count += 1

        c.save()
        buffer.seek(0)
        
        st.balloons()
        st.download_button("📥 Descargar PDF", buffer, "etiquetas_dramireG.pdf", "application/pdf")
else:
    st.info("👆 Sube tu archivo Excel para empezar")
