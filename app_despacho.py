import sys
import subprocess
import os
import re
import ctypes
import webbrowser
import requests
import datetime
import io
import tkinter as tk
from tkinter import messagebox, ttk
from fpdf import FPDF
import qrcode
import urllib3

# === VARIABLES GLOBALES DE RUTA (CORREGIDO DE RAÍZ) ===
if getattr(sys, 'frozen', False):
    directorio_real_app = os.path.dirname(sys.executable)
else:
    directorio_real_app = os.path.dirname(os.path.abspath(sys.argv[0]))

ruta_lic = os.path.join(directorio_real_app, "licencia.txt")
ruta_acc = os.path.join(directorio_real_app, "acceso_config.txt")
ruta_config_drive = os.path.join(directorio_real_app, "drive_config.txt")
ruta_token_drive = os.path.join(directorio_real_app, "token_drive.json")

# =========================================================================
# 🚨 PEGA ESTA FUNCIÓN AQUÍ (ARRIBA DEL TODO) PARA ELIMINAR EL ERROR
# =========================================================================
def recurso_path(relative_path):
    """ Gestiona los recursos internos empaquetados por PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def obtener_ruta_salida(relative_path):
    """ Gestiona la ruta de salida para archivos generados por el usuario """
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

class GeneradorEtiquetasA4(FPDF):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # CORREGIDO: Apunta siempre a la carpeta exterior del ejecutable
        self.ruta_logo1 = os.path.join(directorio_real_app, "logo_imagen1.png")
        self.ruta_logo2 = os.path.join(directorio_real_app, "logo_imagen2.png")

    def generar_codigo_qr(self, datos):
        """Genera el código QR de manera limpia en un archivo temporal de alta velocidad"""
        tipo_comp = datos.get("tipo_doc", "FACTURA").upper()
        serie_num = f"{datos.get('serie', '')}-{datos.get('numero', '')}".upper()
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y")

        texto_qr = (
            f"DOCUMENTO: {tipo_comp} {serie_num}\n"
            f"FECHA: {fecha_actual}\n"
            f"CLIENTE: {datos.get('atencion', '').upper()}\n"
            f"DNI/RUC: {datos.get('dni', '')}\n"
            f"CELULAR: {datos.get('celular', '')}"
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(texto_qr)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # El código QR temporal se genera de forma segura en la raíz de la app
        ruta_temporal_qr = os.path.join(directorio_real_app, "temp_qr_print.png")
        img.save(ruta_temporal_qr, format="PNG")
        
        return ruta_temporal_qr

    def dibujar_etiqueta_mini(self, x, y, datos):
        """ Renderiza el formato de etiqueta pequeña (A4) optimizado en alta velocidad """
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.6)
        self.rect(x, y, 195, 65)
        
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "B", 34)
        texto_destino = f"{datos.get('destino', '').upper()}"
        self.set_xy(x + 4.0, y + 3.0)
        self.cell(130, 12, texto_destino, ln=False, align='L')
        
        texto_bulto = datos.get('bulto_texto', '(1/1)')
        self.set_xy(x + 105, y + 4.5)
        self.set_font("Helvetica", "B", 24)
        self.cell(30, 10, texto_bulto, ln=False, align='L')
        
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.6)
        self.line(x + 2, y + 17, x + 134, y + 17)
        
        self.set_font("Arial", "B", 17.5)
        self.set_xy(x + 4, y + 19)
        self.multi_cell(130, 6.0, f"ATT: {datos.get('atencion', '').upper()}", border=0, align='L')
        
        y_dinamico = self.get_y() + 1.0
       
        self.set_font("Arial", "", 12.5)
        self.set_xy(x + 4, y_dinamico)
        self.cell(48, 4.5, f"DNI/RUC: {datos.get('dni', '')}", ln=False) 
        
        self.set_font("Arial", "B", 12.5)
        self.set_xy(x + 55, y_dinamico)
        tipo_doc = datos.get('tipo_doc', 'FACTURA').upper()
        serie_num = f"{datos.get('serie', '')}-{datos.get('numero', '')}".upper()
        self.cell(75, 4.5, f"  |  {tipo_doc}: {serie_num}", ln=True)
        
        if datos.get('atencion2'):
            y_dinamico = self.get_y() + 1.0
            self.set_xy(x + 4, y_dinamico)
            self.set_font("Arial", "B", 11.5)  
            self.cell(130, 4.5, f"ATT 2: {datos['atencion2'].upper()}", ln=True)
            
            doc2 = str(datos.get('dni2', '')).strip()
            tipo_doc2 = "RUC 2" if len(doc2) == 11 else "DNI 2"
            
            y_dinamico = self.get_y() + 1.0
            self.set_xy(x + 4, y_dinamico)
            self.set_font("Arial", "", 11.5)  
            self.cell(130, 4.5, f"{tipo_doc2}: {doc2}", ln=True)
        
        if datos.get('celular'):
            y_dinamico = self.get_y() + 1.0
            self.set_xy(x + 4, y_dinamico)
            self.set_font("Arial", "B", 13)
            self.cell(130, 4.5, f"CELULAR: {datos['celular']}", ln=True)
            
        if datos.get('agencia'):
            y_dinamico = self.get_y() + 1.0
            self.set_xy(x + 4, y_dinamico)
            self.set_font("Arial", "B", 12.5)
            self.cell(130, 4.5, f"AGENCIA: {datos['agencia'].upper()}", ln=True)

        if hasattr(self, 'ruta_logo1') and os.path.exists(self.ruta_logo1):
            self.image(self.ruta_logo1, x + 136, y + 2, 57, 38)
        elif os.path.exists(os.path.abspath("logo_imagen1.png")):
            self.image(os.path.abspath("logo_imagen1.png"), x + 136, y + 2, 57, 38)

        if hasattr(self, 'ruta_logo2') and os.path.exists(self.ruta_logo2):
            self.image(self.ruta_logo2, x + 4, y + 48, 150, 13.5)
        elif os.path.exists(os.path.abspath("logo_imagen2.png")):
            self.image(os.path.abspath("logo_imagen2.png"), x + 4, y + 48, 150, 13.5)

        try:
            ruta_qr = self.generar_codigo_qr(datos)
            if ruta_qr and os.path.exists(ruta_qr):
                self.image(ruta_qr, x + 172, y + 43, 19.5, 19.5) 
        except Exception as e:
            print(f"Error generando QR en mini: {e}")

        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.6)

    def dibujar_etiqueta_maxi(self, x, y, datos):
        """ Renderiza la etiqueta grande ocupando el 100% de la hoja A4 Horizontal de manera instantánea """
        self.set_draw_color(0, 0, 0)
        self.set_line_width(1.2)
        self.rect(x + 5, y + 5, 287, 200) 
        
        self.set_text_color(0, 0, 0) 
        self.set_font("Helvetica", "B", 56) 
        texto_destino = f"{datos.get('destino', '').upper()}"
        self.set_xy(x + 10, y + 10)
        self.cell(200, 22, texto_destino, ln=False, align='L')
        
        texto_bulto = datos.get('bulto_texto', '(1/1)')
        self.set_font("Helvetica", "B", 38) 
        self.set_xy(x + 210, y + 11)
        self.cell(75, 20, texto_bulto, ln=False, align='R')
        
        self.line(x + 5, y + 36, x + 292, y + 36)
        
        self.set_font("Arial", "B", 26)
        self.set_xy(x + 10, y + 42)
        self.multi_cell(180, 10, f"ATT: {datos.get('atencion', '').upper()}", border=0, align='L')
        
        y_dinamico = self.get_y() + 4.0
        self.set_font("Arial", "", 18)
        self.set_xy(x + 10, y_dinamico)
        tipo_doc = datos.get('tipo_doc', 'FACTURA').upper()
        serie_num = f"{datos.get('serie', '')}-{datos.get('numero', '')}".upper()
        self.cell(180, 8, f"DNI/RUC: {datos.get('dni', '')}   |   {tipo_doc}: {serie_num}", ln=True)
        
        y_dinamico = self.get_y() + 4.0
        if datos.get('celular'):
            self.set_xy(x + 10, y_dinamico)
            self.set_font("Arial", "B", 20)
            self.cell(180, 8, f"CELULAR: {datos['celular']}", ln=True)
            y_dinamico = self.get_y() + 4.0
            
        if datos.get('atencion2'):
            self.set_xy(x + 10, y_dinamico)
            self.set_font("Arial", "B", 16)
            self.cell(180, 8, f"ATT 2: {datos['atencion2'].upper()}", ln=True)
            
            doc2 = str(datos.get('dni2', '')).strip()
            tipo_doc2 = "RUC 2" if len(doc2) == 11 else "DNI 2"
            
            y_dinamico = self.get_y() + 2.0
            self.set_xy(x + 10, y_dinamico)
            self.set_font("Arial", "", 16)
            self.cell(180, 8, f"{tipo_doc2}: {doc2}", ln=True)
            y_dinamico = self.get_y() + 4.0
            
        if datos.get('agencia'):
            self.set_xy(x + 10, y_dinamico)
            self.set_font("Arial", "B", 18)
            self.cell(180, 8, f"AGENCIA: {datos['agencia'].upper()}", ln=True)

        if hasattr(self, 'ruta_logo1') and os.path.exists(self.ruta_logo1):
            self.image(self.ruta_logo1, x=x+200, y=y+40, w=87, h=65)
        elif os.path.exists(os.path.abspath("logo_imagen1.png")):
            self.image(os.path.abspath("logo_imagen1.png"), x=x+200, y=y+40, w=87, h=65)

        if hasattr(self, 'ruta_logo2') and os.path.exists(self.ruta_logo2):
            self.image(self.ruta_logo2, x=x+10, y=y+150, w=220, h=45)
        elif os.path.exists(os.path.abspath("logo_imagen2.png")):
            self.image(os.path.abspath("logo_imagen2.png"), x=x+10, y=y+150, w=220, h=45)
            
        try:
            ruta_qr = self.generar_codigo_qr(datos)
            if ruta_qr and os.path.exists(ruta_qr):
                self.image(ruta_qr, x=x+240, y=y+150, w=45, h=45)
        except Exception as e:
            print(f"Error generando el QR en la Maxi: {e}")
    def dibujar_etiqueta_termica(self, x, y, datos):
        """ Renderiza la etiqueta vertical para rollos térmicos sin delays de disco """
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.8)
        self.rect(x + 3, y + 3, 94, 144)
        
        texto_destino = f"{datos.get('destino', '').upper()}"
        if len(texto_destino) >= 9:
            self.set_font("Helvetica", "B", 24)
            self.set_xy(x + 5, y + 5)
            self.cell(63, 10, texto_destino, ln=False, align='L')
        else:
            self.set_font("Helvetica", "B", 36)
            self.set_xy(x + 4, y + 4)
            self.cell(63, 12, texto_destino, ln=False, align='L')
        
        texto_bulto = datos.get('bulto_texto', '(1/1)')
        self.set_font("Helvetica", "B", 18)
        self.set_xy(x + 68, y + 7)
        self.cell(25, 8, texto_bulto, ln=False, align='R')
        
        self.set_font("Arial", "B", 13)
        self.set_xy(x + 6, y + 21)
        self.multi_cell(88, 5.0, f"ATT: {datos.get('atencion', '').upper()}", border=0, align='L')
        
        y_dinamico = self.get_y() + 1.5
        self.set_font("Arial", "", 10.5)
        self.set_xy(x + 6, y_dinamico)
        self.cell(88, 4.5, f"DNI/RUC: {datos.get('dni', '')}", ln=True)
        
        y_dinamico = self.get_y() + 0.5
        self.set_xy(x + 6, y_dinamico)
        tipo_doc = datos.get('tipo_doc', 'FACTURA').upper()
        serie_num = f"{datos.get('serie', '')}-{datos.get('numero', '')}".upper()
        self.cell(88, 4.5, f"{tipo_doc}: {serie_num}", ln=True)
        
        if datos.get('celular'):
            y_dinamico = self.get_y() + 0.5
            self.set_xy(x + 6, y_dinamico)
            self.set_font("Arial", "B", 11)
            self.cell(88, 4.5, f"CELULAR: {datos['celular']}", ln=True)
            
        if datos.get('atencion2'):
            y_dinamico = self.get_y() + 0.5
            self.set_xy(x + 6, y_dinamico)
            self.set_font("Arial", "B", 9.5)
            self.cell(88, 4.5, f"ATT 2: {datos['atencion2'].upper()}", ln=True)
            
            doc2 = str(datos.get('dni2', '')).strip()
            tipo_doc2 = "RUC 2" if len(doc2) == 11 else "DNI 2"
            
            y_dinamico = self.get_y() + 0.5
            self.set_xy(x + 6, y_dinamico)
            self.set_font("Arial", "", 9.5)
            self.cell(88, 4.5, f"{tipo_doc2}: {doc2}", ln=True)
            
        if datos.get('agencia'):
            y_dinamico = self.get_y() + 0.5
            self.set_xy(x + 6, y_dinamico)
            self.set_font("Arial", "B", 10.5)
            self.cell(88, 4.5, f"AGENCIA: {datos['agencia'].upper()}", ln=True)

        y_linea_central = y + 62.0
        y_linea_base = y + 120.0

        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.6)
        self.line(x + 3, y_linea_central, x + 97, y_linea_central)
        self.line(x + 3, y_linea_base, x + 97, y_linea_base)

        ruta_l1 = getattr(self, 'ruta_logo1', os.path.abspath("logo_imagen1.png"))
        if os.path.exists(ruta_l1):
            self.image(ruta_l1, x + 7, y_linea_central + 4.0, 86, 48)

        ruta_l2 = getattr(self, 'ruta_logo2', os.path.abspath("logo_imagen2.png"))
        if os.path.exists(ruta_l2):
            self.image(ruta_l2, x + 6, y_linea_base + 4, 60, 18)

        try:
            ruta_qr = self.generar_codigo_qr(datos)
            if ruta_qr and os.path.exists(ruta_qr):
                self.image(ruta_qr, x + 72, y_linea_base + 2, 22, 22)
        except Exception as e:
            print(f"Error generando el QR en térmica: {e}")

        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.6)
        self.line(x + 3, y + 18, x + 97, y + 18)       
        self.line(x + 3, y_linea_central, x + 97, y_linea_central) 
        self.line(x + 3, y_linea_base, x + 97, y_linea_base)       

    def generar_hoja_automatica(self, lista_envios, formato_seleccionado):
        """ Distribuye los envíos de forma automática según el formato seleccionado """
        if formato_seleccionado == "A4 Horizontal":  
            for datos in lista_envios:
                self.add_page(orientation='L', format='A4') 
                self.dibujar_etiqueta_maxi(0, 0, datos)       

        elif formato_seleccionado == "Térmica 100x150":  
            self.set_auto_page_break(auto=False, margin=0)
            for datos in lista_envios:
                self.add_page(orientation='P', format=(100, 150))
                self.dibujar_etiqueta_termica(0, 0, datos)

        else:  
            posiciones_a4 = [(8, 5), (8, 75), (8, 145), (8, 215)]
            for i, datos in enumerate(lista_envios):
                if i % 4 == 0:
                    self.add_page(orientation='P', format='A4')
                indice_hoja = i % 4
                x_pos, y_pos = posiciones_a4[indice_hoja]
                self.dibujar_etiqueta_mini(x_pos, y_pos, datos)

class VentanaDespachoMasivo:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Despacho DramirenG")
        self.root.geometry("950x820") 
        self.root.configure(bg="#E9ECEF")

        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("dramireng.sistema.despacho.1.0")
        except:
            pass
            
        self.lista_espera = []
        self.archivo_bd = "clientes_guardados.txt"
        self.url_drive_tsv = self.cargar_enlace_guardado()
        
        self.provincias_peru = [
            "CHACHAPOYAS", "BAGUA", "BONGARÁ", "HUARAZ", "CASMA", "HUARMEY", "SANTA", "YUNGAY",
            "ABANCAY", "ANDAHUAYLAS", "AREQUIPA", "CAMANÁ", "ISLAY", "AYACUCHO", "HUAMANGA",
            "CAJAMARCA", "JAÉN", "CALLAO", "CUSCO", "URUBAMBA", "HUANCAVELICA", "HUÁNUCO", 
            "LEONCIO PRADO", "ICA", "PISCO", "HUANCAYO", "SATIPO", "TARMA", "TRUJILLO", "CHEPÉN", 
            "PACASMAYO", "CHICLAYO", "LAMBAYEQUE", "LIMA", "BARRANCA", "CAÑETE", "HUARAL", 
            "HUAURA", "IQUITOS", "PUERTO MALDONADO", "MOQUEGUA", "ILO", "PASCO", "OXAPAMPA", 
            "PIURA", "SULLANA", "TALARA", "PUNO", "SAN ROMÁN", "MOYOBAMBA", "TARAPOTO", 
            "TACNA", "TUMBES", "PUCALLPA", "CORONEL PORTILLO"
        ]

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Rounded.TEntry", borderwidth=1, relief="flat", background="white", fieldbackground="white", lightcolor="#CED4DA", darkcolor="#CED4DA", bordercolor="#CED4DA")

        # --- CABECERA ---
        frame_header = tk.Frame(self.root, bg="#0A1F3D", height=50)
        frame_header.pack(fill="x", side="top")
        frame_header.pack_propagate(False)
        
        tk.Label(frame_header, text="📝 REGISTRO DE ENVÍOS NACIONALES", font=("Arial", 11, "bold"), bg="#0A1F3D", fg="white").pack(side="left", padx=20)
        
        self.btn_config = tk.Button(frame_header, text="⚙️ Configurar Drive", font=("Arial", 8, "bold"), bg="#0A1F3D", fg="#A2C2E8", activebackground="#0A1F3D", activeforeground="white", bd=0, cursor="hand2", command=self.ventana_configurar_enlace)
        self.btn_config.pack(side="right", padx=20)
        
        tk.Label(frame_header, text="BIENVENIDO   | ", font=("Arial", 9, "bold"), bg="#0A1F3D", fg="#A2C2E8").pack(side="right")

        frame_central_fijo = tk.Frame(self.root, bg="#E9ECEF", width=910)
        frame_central_fijo.pack(fill="y", expand=True, pady=10)
        frame_central_fijo.pack_propagate(False)

        # --- CONFIGURACIÓN DE ESTILOS PREMIUM PARA LOS BOTONES NATIVOS ---
        estilo_interfaz = ttk.Style()
        # Usamos el motor 'clam' que permite colores planos y bordes limpios sin degradados viejos
        estilo_interfaz.theme_use('clam') 

        # Configuración Botón Imprimir (Verde)
        estilo_interfaz.configure("Imprimir.TButton", font=("Arial", 9, "bold"), background="#28A745", foreground="white", borderwidth=0, focuscolor="none")
        estilo_interfaz.map("Imprimir.TButton", background=[("active", "#218838")])

        # Configuración Botón Eliminar (Rojo)
        estilo_interfaz.configure("Borrar.TButton", font=("Arial", 9, "bold"), background="#DC3545", foreground="white", borderwidth=0, focuscolor="none")
        estilo_interfaz.map("Borrar.TButton", background=[("active", "#C82333")])

        # Configuración Botón WhatsApp (Verde Oficial)
        estilo_interfaz.configure("WhatsApp.TButton", font=("Arial", 9, "bold"), background="#128C7E", foreground="white", borderwidth=0, focuscolor="none")
        estilo_interfaz.map("WhatsApp.TButton", background=[("active", "#075E54")])

        # --- BARRA DE HERRAMIENTAS SUPERIOR ---
        frame_formato_superior = tk.Frame(frame_central_fijo, bg="#E9ECEF")
        frame_formato_superior.pack(fill="x", pady=(0, 10))
        
        tk.Label(frame_formato_superior, text="Formato de Impresión:", font=("Arial", 9, "bold"), bg="#E9ECEF", fg="#495057").pack(side="left", padx=(5, 5))
        
        # Selector de formato
        self.combo_formato = ttk.Combobox(frame_formato_superior, values=["A4 Vertical", "A4 Horizontal", "Térmica 100x150"], font=("Arial", 9), state="readonly", width=18)
        self.combo_formato.set("A4 Vertical")
        self.combo_formato.pack(side="left", padx=(0, 15))

        # 1. BOTÓN IMPRIMIR CORREGIDO
        self.btn_imprimir = ttk.Button(frame_formato_superior, text="🖨️ IMPRIMIR", style="Imprimir.TButton", cursor="hand2", command=self.generar_impresion_dinamica)
        self.btn_imprimir.pack(side="left", padx=5, ipady=4)

        # 2. BOTÓN ELIMINAR CORREGIDO
        self.btn_borrar = ttk.Button(frame_formato_superior, text="🗑️ ELIMINAR", style="Borrar.TButton", cursor="hand2", command=self.limpiar_lista_completa)
        self.btn_borrar.pack(side="left", padx=5, ipady=4)

        # 3. BOTÓN WHATSAPP CORREGIDO
        self.btn_paste_wa = ttk.Button(frame_formato_superior, text="📋 IMPORTAR WA", style="WhatsApp.TButton", cursor="hand2", command=self.procesar_texto_whatsapp_inteligente)
        self.btn_paste_wa.pack(side="left", padx=5, ipady=4)

        # --- SECCIÓN: FORMULARIO ---
        lbl_sec2 = tk.Label(frame_central_fijo, text="  Formulario de Registro de Envíos", font=("Arial", 9, "bold"), bg="#0A1F3D", fg="white", anchor="w")
        lbl_sec2.pack(fill="x", pady=(5, 0))
        
        frame_form = tk.Frame(frame_central_fijo, bg="white", bd=1, relief="solid")
        frame_form.pack(fill="x", pady=(0, 10), ipady=5)
        frame_form.columnconfigure(1, weight=1)
        frame_form.columnconfigure(3, weight=1)

        self.entries = {}
        
        # FILA 0
        tk.Label(frame_form, text="DNI / RUC:", font=("Arial", 9, "bold"), bg="white", fg="#000000", anchor="w").grid(row=0, column=0, padx=(20, 5), pady=6, sticky="w")
        f_dni1 = tk.Frame(frame_form, bg="white")
        f_dni1.grid(row=0, column=1, padx=5, pady=6, sticky="ew")
        self.entries["DNI / RUC 1"] = ttk.Entry(f_dni1, font=("Arial", 10), style="Rounded.TEntry", width=22)
        self.entries["DNI / RUC 1"].pack(side="left", ipady=3)
        tk.Button(f_dni1, text=" 🔍 Buscar ", font=("Arial", 8, "bold"), bg="#0A1F3D", fg="white", bd=0, cursor="hand2", command=lambda: self.buscar_dni_inteligente("DNI / RUC 1", "Nombre Completo 1")).pack(side="left", padx=8, ipady=2)

        tk.Label(frame_form, text="Agencia:", font=("Arial", 9, "bold"), bg="white", fg="#000000", anchor="w").grid(row=0, column=2, padx=(15, 5), pady=6, sticky="w")
        self.entries["Agencia"] = ttk.Entry(frame_form, font=("Arial", 10), style="Rounded.TEntry")
        self.entries["Agencia"].grid(row=0, column=3, padx=(5, 20), pady=6, sticky="ew", ipady=3)

        # FILA 1
        tk.Label(frame_form, text="Nombres y Apellidos:", font=("Arial", 9, "bold"), bg="white", fg="#000000", anchor="w").grid(row=1, column=0, padx=(20, 5), pady=6, sticky="w")
        self.entries["Nombre Completo 1"] = ttk.Entry(frame_form, font=("Arial", 10), style="Rounded.TEntry")
        self.entries["Nombre Completo 1"].grid(row=1, column=1, columnspan=3, padx=(5, 20), pady=6, sticky="ew", ipady=3)

        # FILA 2
        tk.Label(frame_form, text="DNI / RUC (Opcional):", font=("Arial", 9, "bold"), bg="white", fg="#000000", anchor="w").grid(row=2, column=0, padx=(20, 5), pady=6, sticky="w")
        f_dni2 = tk.Frame(frame_form, bg="white")
        f_dni2.grid(row=2, column=1, columnspan=3, padx=5, pady=6, sticky="w")
        self.entries["DNI / RUC 2 (Opcional)"] = ttk.Entry(f_dni2, font=("Arial", 10), style="Rounded.TEntry", width=22)
        self.entries["DNI / RUC 2 (Opcional)"].pack(side="left", ipady=3)
        tk.Button(f_dni2, text=" 🔍 Buscar ", font=("Arial", 8, "bold"), bg="#0A1F3D", fg="white", bd=0, cursor="hand2", command=lambda: self.buscar_dni_inteligente("DNI / RUC 2 (Opcional)", "Nombre Completo 2 (Opcional)")).pack(side="left", padx=8, ipady=2)

        # FILA 3
        tk.Label(frame_form, text="Nombres y Apellidos (Opcional):", font=("Arial", 9, "bold"), bg="white", fg="#000000", anchor="w").grid(row=3, column=0, padx=(20, 5), pady=6, sticky="w")
        self.entries["Nombre Completo 2 (Opcional)"] = ttk.Entry(frame_form, font=("Arial", 10), style="Rounded.TEntry")
        self.entries["Nombre Completo 2 (Opcional)"].grid(row=3, column=1, columnspan=3, padx=(5, 20), pady=6, sticky="ew", ipady=3)

        # FILA 4
        tk.Label(frame_form, text="Destino:", font=("Arial", 9, "bold"), bg="white", fg="#000000", anchor="w").grid(row=4, column=0, padx=(20, 5), pady=6, sticky="w")
        self.entries["Destino"] = ttk.Entry(frame_form, font=("Arial", 10), style="Rounded.TEntry")
        self.entries["Destino"].grid(row=4, column=1, padx=5, pady=6, sticky="ew", ipady=3)

        tk.Label(frame_form, text="Celular:", font=("Arial", 9, "bold"), bg="white", fg="#000000", anchor="w").grid(row=4, column=2, padx=(15, 5), pady=6, sticky="w")
        self.entries["Celular"] = ttk.Entry(frame_form, font=("Arial", 10), style="Rounded.TEntry")
        self.entries["Celular"].grid(row=4, column=3, padx=(5, 20), pady=6, sticky="ew", ipady=3)

        # FILA 5
        tk.Label(frame_form, text="Tipo Comprobante:", font=("Arial", 9, "bold"), bg="white", fg="#000000", anchor="w").grid(row=5, column=0, padx=(20, 5), pady=6, sticky="w")
        self.combo_tipo_doc = ttk.Combobox(frame_form, values=["Factura", "Guia de Remision"], font=("Arial", 9), state="readonly")
        self.combo_tipo_doc.set("Factura")
        self.combo_tipo_doc.grid(row=5, column=1, padx=5, pady=6, sticky="ew")

        f_comprobante = tk.Frame(frame_form, bg="white")
        f_comprobante.grid(row=5, column=3, padx=(5, 20), pady=6, sticky="ew")
        f_comprobante.columnconfigure(1, weight=1)
        f_comprobante.columnconfigure(3, weight=2)

        tk.Label(f_comprobante, text="Serie:", font=("Arial", 9, "bold"), bg="white", fg="#000000").grid(row=0, column=0, padx=(0, 5))
        self.entries["Serie"] = ttk.Entry(f_comprobante, font=("Arial", 10), style="Rounded.TEntry", width=8)
        self.entries["Serie"].insert(0, "F001") 
        self.entries["Serie"].grid(row=0, column=1, sticky="ew", ipady=3)

        tk.Label(f_comprobante, text=" Nro:", font=("Arial", 9, "bold"), bg="white", fg="#000000").grid(row=0, column=2, padx=5)
        self.entries["Numero"] = ttk.Entry(f_comprobante, font=("Arial", 10), style="Rounded.TEntry")
        self.entries["Numero"].grid(row=0, column=3, sticky="ew", ipady=3)

        # FILA 6
        frame_botones_form = tk.Frame(frame_form, bg="white")
        frame_botones_form.grid(row=6, column=0, columnspan=4, pady=12, sticky="n")

        tk.Label(frame_botones_form, text="Cant. Bultos:", font=("Arial", 9, "bold"), bg="white", fg="#000000").pack(side="left", padx=(0, 5))
        self.entries["Bultos"] = ttk.Entry(frame_botones_form, font=("Arial", 10, "bold"), style="Rounded.TEntry", width=6, justify="center")
        self.entries["Bultos"].pack(side="left", padx=(0, 15), ipady=3)
        self.entries["Bultos"].insert(0, "1")
        
        self.btn_add = tk.Button(frame_botones_form, text="💾 Grabar", font=("Arial", 9, "bold"), bg="#E75E35", fg="white", activebackground="#D04E27", bd=0, width=14, cursor="hand2", command=self.agregar_a_lista)
        self.btn_add.pack(side="left", ipady=5, padx=10)

        self.btn_clear_fields = tk.Button(frame_botones_form, text="🧹 Limpiar", font=("Arial", 9, "bold"), bg="#6C757D", fg="white", activebackground="#5A6268", bd=0, width=14, cursor="hand2", command=self.limpiar_campos_formulario)
        self.btn_clear_fields.pack(side="left", ipady=5, padx=10)
        
        self.entries["DNI / RUC 1"].bind('<KeyRelease>', lambda e: self.detectar_borrado_documento("DNI / RUC 1"))
        self.entries["DNI / RUC 2 (Opcional)"].bind('<KeyRelease>', lambda e: self.detectar_borrado_documento("DNI / RUC 2 (Opcional)"))
        self.entries["Destino"].bind('<KeyRelease>', self.evento_autocompletar_texto, add="+")
        # --- SECCIÓN: TABLA ---
        lbl_sec3 = tk.Label(frame_central_fijo, text="  Envíos Pendientes en esta Hoja", font=("Arial", 9, "bold"), bg="#0A1F3D", fg="white", anchor="w")
        lbl_sec3.pack(fill="x", pady=(5, 0))
        
        frame_tabla = tk.Frame(frame_central_fijo, bg="white", bd=1, relief="solid")
        frame_tabla.pack(fill="both", expand=True, pady=(0, 10))
        
        estilo_tabla = ttk.Style()
        estilo_tabla.theme_use("clam")
        estilo_tabla.configure("Treeview.Heading", font=("Arial", 9, "bold"), background="#0A1F3D", foreground="white", relief="flat")
        estilo_tabla.configure("Treeview", font=("Arial", 9), rowheight=26, background="white", fieldbackground="white")
        estilo_tabla.map("Treeview", background=[("selected", "#FFFF00")], foreground=[("selected", "#000000")])

        columnas = ("No", "Titular Principal", "Nro. Documento", "Destino", "Cell", "Comprobante")
        self.tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
        self.tabla.heading("No", text="Nº")
        self.tabla.column("No", width=40, anchor="center")
        self.tabla.heading("Titular Principal", text="Nombres y Apellidos")
        self.tabla.column("Titular Principal", width=280)
        self.tabla.heading("Nro. Documento", text="Nro. Documento")
        self.tabla.column("Nro. Documento", width=110, anchor="center")
        self.tabla.heading("Destino", text="Destino")
        self.tabla.column("Destino", width=140, anchor="center")
        self.tabla.heading("Cell", text="Celular")
        self.tabla.column("Cell", width=110, anchor="center")
        self.tabla.heading("Comprobante", text="Doc/Serie-Num")
        self.tabla.column("Comprobante", width=140, anchor="center")
        
        scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        
        scroll_y.pack(side="right", fill="y")
        self.tabla.pack(fill="both", expand=True, padx=(6, 0), pady=6)

        self.tabla.bind("<Double-1>", self.eliminar_fila_lista_espera)

    def detectar_borrado_documento(self, campo):
        texto = self.entries[campo].get().strip()
        if not texto:  
            if campo == "DNI / RUC 1":
                self.entries["Nombre Completo 1"].delete(0, tk.END)
                self.entries["Destino"].delete(0, tk.END)
                self.entries["Celular"].delete(0, tk.END)
                self.entries["Agencia"].delete(0, tk.END)
            elif campo == "DNI / RUC 2 (Opcional)":
                self.entries["Nombre Completo 2 (Opcional)"].delete(0, tk.END)

    def eliminar_fila_lista_espera(self, event):
        item_seleccionado = self.tabla.focus() 
        if not item_seleccionado:
            return
            
        indice_fila = self.tabla.index(item_seleccionado)
        valores = self.tabla.item(item_seleccionado, 'values')
        nombre_cliente = valores[1] if (valores and len(valores) > 1) else "este registro"

        pregunta = messagebox.askyesno("Quitar de la lista", f"¿Deseas quitar a '{nombre_cliente}' de la lista de impresión actual?")
        if pregunta:
            try:
                if 0 <= indice_fila < len(self.lista_espera):
                    self.lista_espera.pop(indice_fila)
                self.actualizar_tabla_visual()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo quitar el elemento: {e}")
    def cargar_enlace_guardado(self):
        if os.path.exists(ruta_config_drive):
            with open(ruta_config_drive, "r", encoding="utf-8") as f:
                return f.read().strip()
        return ""

    def ventana_configurar_enlace(self):
        v_candado = tk.Toplevel(self.root)
        v_candado.title("🔐 Seguridad")
        v_candado.geometry("340x160")
        v_candado.resizable(False, False)
        v_candado.configure(bg="#002244")
        v_candado.grab_set()
        
        tk.Label(v_candado, text="INGRESE LA CLAVE DE ADMINISTRADOR:", font=("Arial", 9, "bold"), bg="#002244", fg="white").pack(pady=(15, 5))
        
        ent_clave_adm = tk.Entry(v_candado, font=("Arial", 10), bd=2, relief="flat", show="*", justify="center", width=22)
        ent_clave_adm.pack(pady=5, ipady=2)
        ent_clave_adm.focus()

        def verificar_acceso_config():
            if ent_clave_adm.get() == "Admi2026":
                v_candado.destroy() 
                self.abrir_panel_configuracion_real() 
            else:
                messagebox.showerror("Acceso Denegado", "La contraseña de administrador es incorrecta.")
                v_candado.destroy()

        tk.Button(v_candado, text="🔑 VERIFICAR ACCESO", bg="#ff9900", fg="white", font=("Arial", 8, "bold"), relief="flat", cursor="hand2", command=verificar_acceso_config).pack(pady=12, ipadx=10, ipady=2)

    def abrir_panel_configuracion_real(self):
        v_config = tk.Toplevel(self.root)
        v_config.title("Configuración Base de Datos y API")
        v_config.geometry("580x240") 
        v_config.resizable(False, False)
        v_config.grab_set() 
        
        tk.Label(v_config, text="Pegue el enlace publicado (Debe terminar en output=tsv):", font=("Arial", 9, "bold")).pack(pady=(10, 2))
        ent_url = tk.Entry(v_config, font=("Arial", 10), bd=2, relief="groove", width=65)
        ent_url.pack(padx=20, pady=2)
        ent_url.insert(0, self.cargar_enlace_guardado())
        
        tk.Label(v_config, text="Pegue el Token de API Perú del Cliente (DNI/RUC):", font=("Arial", 9, "bold")).pack(pady=(12, 2))
        frame_token = tk.Frame(v_config)
        frame_token.pack(padx=20, pady=2, fill="x")
        
        ent_token = tk.Entry(frame_token, font=("Arial", 10), bd=2, relief="groove", width=55, show="*")
        ent_token.pack(side="left", padx=(15, 5))
        
        if os.path.exists(ruta_token_drive):
            with open(ruta_token_drive, "r", encoding="utf-8") as f:
                ent_token.insert(0, f.read().strip())
        
        def alternar_visibilidad_token():
            if ent_token.cget("show") == "*":
                ent_token.config(show="") 
                btn_ojo.config(text="🔒 Ocultar")
            else:
                ent_token.config(show="*") 
                btn_ojo.config(text="👁️ Mostrar")
        
        btn_ojo = tk.Button(frame_token, text="👁️ Mostrar", font=("Arial", 8, "bold"), bg="#e6e6e6", fg="black", bd=1, relief="raised", cursor="hand2", command=alternar_visibilidad_token)
        btn_ojo.pack(side="left", padx=2, ipady=1)
        
        def guardar():
            url = ent_url.get().strip()
            token = ent_token.get().strip()
            
            if url or token: 
                with open(ruta_config_drive, "w", encoding="utf-8") as f:
                    f.write(url)
                self.url_drive_tsv = url
                
                with open(ruta_token_drive, "w", encoding="utf-8") as f:
                    f.write(token)
                
                messagebox.showinfo("Guardado", "Configuración actualizada con éxito.")
                v_config.destroy()
            else:
                messagebox.showerror("Error", "Debe llenar al menos una casilla para guardar.")
                
        tk.Button(v_config, text="💾 Guardar Configuración", bg="#003366", fg="white", font=("Arial", 9, "bold"), command=guardar, bd=0, cursor="hand2").pack(pady=18)
    def verificar_autocompletado_local(self, campo_dni, campo_nombre, ignorar_web=False):
        num_dni = self.entries[campo_dni].get().strip()
        if len(num_dni) == 7 and num_dni.isdigit():
            num_dni = "0" + num_dni
            self.entries[campo_dni].delete(0, tk.END)
            self.entries[campo_dni].insert(0, num_dni)

        if len(num_dni) != 8 and len(num_dni) != 11:
            return False

        ruta_bd_local = recurso_path(self.archivo_bd)
        if os.path.exists(ruta_bd_local):
            with open(ruta_bd_local, "r", encoding="utf-8") as f:
                lineas = [l.strip() for l in f.readlines() if l.strip()]
                for linea in lineas:
                    partes_local = linea.split(",")
                    if len(partes_local) >= 2:
                        doc_guardado = str(partes_local[0]).strip()
                        if doc_guardado == num_dni:
                            nombre_completo = partes_local[1].replace('\n', ' ').replace('\r', ' ').strip().upper()
                            self.entries[campo_nombre].delete(0, tk.END)
                            self.entries[campo_nombre].insert(0, nombre_completo)
                            
                            if campo_dni == "DNI / RUC 1":
                                if len(partes_local) >= 3 and partes_local[2].strip():
                                    self.entries["Celular"].delete(0, tk.END)
                                    self.entries["Celular"].insert(0, partes_local[2].strip())
                                if len(partes_local) >= 4 and partes_local[3].strip():
                                    self.entries["Destino"].delete(0, tk.END)
                                    self.entries["Destino"].insert(0, partes_local[3].strip().upper())
                                if len(partes_local) >= 5 and partes_local[4].strip():
                                    self.entries["Agencia"].delete(0, tk.END)
                                    self.entries["Agencia"].insert(0, partes_local[4].strip().upper())
                                    
                            self.entries["Destino"].focus()
                            return True

        if not self.url_drive_tsv or "http" not in str(self.url_drive_tsv).lower():
            return False

        if not ignorar_web:
            try:
                response = requests.get(self.url_drive_tsv, timeout=4)
                if response.status_code == 200:
                    for linea in response.text.splitlines():
                        datos_tsv = linea.split("\t")
                        if len(datos_tsv) >= 6:
                            codigo_hoja = str(datos_tsv[1]).strip()
                            if len(codigo_hoja) == 7 and codigo_hoja.isdigit():
                                codigo_hoja = "0" + codigo_hoja
                            
                            if codigo_hoja == num_dni:
                                nombre_tsv = datos_tsv[2].strip().replace('\n', ' ').upper()
                                self.entries[campo_nombre].delete(0, tk.END)
                                self.entries[campo_nombre].insert(0, nombre_tsv)
                                
                                if campo_dni == "DNI / RUC 1":
                                    if datos_tsv[3].strip():
                                        self.entries["Destino"].delete(0, tk.END)
                                        self.entries["Destino"].insert(0, datos_tsv[3].strip().upper())
                                    if datos_tsv[5].strip():
                                        self.entries["Celular"].delete(0, tk.END)
                                        self.entries["Celular"].insert(0, datos_tsv[5].strip())
                                        
                                if "Agencia" in self.entries:
                                    self.entries["Agencia"].focus()
                                else:
                                    self.entries["Destino"].focus()
                                return True
            except Exception as e:
                print(f"Error leyendo Google Drive: {e}")
                
        return False
                
    def buscar_dni_inteligente(self, campo_dni, campo_nombre):
        num_doc = self.entries[campo_dni].get().strip()
        if len(num_doc) == 7 and num_doc.isdigit():
            num_doc = "0" + num_doc
            self.entries[campo_dni].delete(0, tk.END)
            self.entries[campo_dni].insert(0, num_doc)

        if len(num_doc) != 8 and len(num_doc) != 11:
            messagebox.showwarning("Documento Inválido", "Ingrese un DNI de 8 números o un RUC de 11 números.")
            return

        if self.verificar_autocompletado_local(campo_dni, campo_nombre):
            return

        TOKEN_SISTEMA = ""
        if os.path.exists(ruta_token_drive):
            with open(ruta_token_drive, "r", encoding="utf-8") as f:
                TOKEN_SISTEMA = f.read().strip()
        
        if not TOKEN_SISTEMA:
            self.entries[campo_nombre].delete(0, tk.END)
            messagebox.showwarning("Falta Configuración", "No se ha configurado ningún Token de API.\nPor favor, vaya al botón '⚙️ Configurar Drive' y pegue su clave.")
            return 

        self.entries[campo_nombre].delete(0, tk.END)
        self.entries[campo_nombre].insert(0, "BUSCANDO...")
        self.root.update_idletasks()
        
        headers = {
            "Authorization": f"Bearer {TOKEN_SISTEMA}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        try:
            if len(num_doc) == 8:
                url_api = "https://apiperu.dev/api/dni"
                payload = {"dni": num_doc} 
                response = requests.post(url_api, json=payload, headers=headers, timeout=6, verify=False)
                if response.status_code == 200:
                    datos = response.json()
                    if datos.get("success"):
                        res_data = datos.get("data", {})
                        nombres = res_data.get("nombres", "").strip().upper()
                        ape_paterno = res_data.get("apellido_paterno", "").strip().upper()
                        ape_materno = res_data.get("apellido_materno", "").strip().upper()
                        if nombres:
                            nombre_ordenado = f"{nombres} {ape_paterno} {ape_materno}".strip()
                            self.entries[campo_nombre].delete(0, tk.END)
                            self.entries[campo_nombre].insert(0, nombre_ordenado)
                            if campo_dni == "DNI / RUC 1":
                                self.entries["Destino"].focus()
                            return
            elif len(num_doc) == 11:
                url_api = "https://apiperu.dev/api/ruc"
                payload = {"ruc": num_doc}
                response = requests.post(url_api, json=payload, headers=headers, timeout=6, verify=False)
                if response.status_code == 200:
                    datos = response.json()
                    if datos.get("success"):
                        razon_social = datos.get("data", {}).get("nombre_o_razon_social", "").upper()
                        if razon_social:
                            self.entries[campo_nombre].delete(0, tk.END)
                            self.entries[campo_nombre].insert(0, razon_social)
                            if campo_dni == "DNI / RUC 1":
                                self.entries["Destino"].focus()
                            return

            self.entries[campo_nombre].delete(0, tk.END)
            messagebox.showinfo("Sin Resultados", "El documento no figura en el padrón o el Token es inválido.")
        except Exception as e:
            self.entries[campo_nombre].delete(0, tk.END)
            messagebox.showerror("Error de Red", f"No se pudo conectar con el servidor: {e}")
    def registrar_en_historial_excel(self, datos, total_bultos):
        """ Guarda de forma automatica y permanente el despacho en un archivo CSV/Excel """
        archivo_reporte = os.path.join(directorio_real_app, "reporte_despachos.csv")
        fecha_registro = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Combinamos el tipo y numero de documento para el reporte comercial
        comprobante = f"{datos.get('tipo_doc', 'FACTURA').upper()} {datos.get('serie', '')}-{datos.get('numero', '')}"
        
        # CORREGIDO: Usamos punto y coma (;) como separador para el Excel en Peru
        encabezados = "FECHA Y HORA;TITULAR PRINCIPAL;DNI/RUC;DESTINO;CELULAR;AGENCIA;COMPROBANTE;CANT BULTOS\n"
        
        # Limpiamos los textos de posibles signos que rompan las celdas de Excel
        atencion = str(datos.get('atencion', '')).replace(';', ' ').replace(',', ' ').strip().upper()
        dni = str(datos.get('dni', '')).replace(';', ' ').replace(',', ' ').strip()
        destino = str(datos.get('destino', '')).replace(';', ' ').replace(',', ' ').strip().upper()
        celular = str(datos.get('celular', '')).replace(';', ' ').replace(',', ' ').strip()
        agencia = str(datos.get('agencia', '')).replace(';', ' ').replace(',', ' ').strip().upper()
        
        # Estructuramos la fila con formato separado por punto y coma (;)
        nueva_fila = f"{fecha_registro};{atencion};{dni};{destino};{celular};{agencia};{comprobante};{total_bultos}\n"
        
        try:
            # Si el archivo no existe, lo creamos e insertamos los encabezados primero
            if not os.path.exists(archivo_reporte):
                with open(archivo_reporte, "w", encoding="utf-8-sig") as f:
                    f.write(encabezados)
            
            # Añadimos la nueva operacion al final del documento
            with open(archivo_reporte, "a", encoding="utf-8-sig") as f:
                f.write(nueva_fila)
                
        except Exception as e:
            print(f"Error interno al escribir el historial comercial: {e}")
    def agregar_a_lista(self):
        txt_bultos = self.entries["Bultos"].get().strip()
        total_bultos = int(txt_bultos) if (txt_bultos.isdigit() and int(txt_bultos) > 0) else 1

        datos_base = {
            "atencion": self.entries["Nombre Completo 1"].get().strip(),
            "dni": self.entries["DNI / RUC 1"].get().strip(),
            "atencion2": self.entries["Nombre Completo 2 (Opcional)"].get().strip(),
            "dni2": self.entries["DNI / RUC 2 (Opcional)"].get().strip(),
            "destino": self.entries["Destino"].get().strip(),
            "celular": self.entries["Celular"].get().strip(),
            "agencia": self.entries["Agencia"].get().strip(),
            "tipo_doc": self.combo_tipo_doc.get(),
            "serie": self.entries["Serie"].get().strip(),
            "numero": self.entries["Numero"].get().strip()
        }

        if (not datos_base.get('atencion') or not datos_base.get('dni') or not datos_base.get('destino') 
            or not datos_base.get('serie') or not datos_base.get('numero')):
            messagebox.showerror("Campos Vacíos", "Nombre, DNI, Destino, Serie y Número de documento son obligatorios.")
            return

        ruta_bd_local = recurso_path(self.archivo_bd)
        lineas_actualizadas = []
        dni_encontrado = False

        dni_guardar = str(datos_base.get('dni', '')).strip()
        atencion_guardar = str(datos_base.get('atencion', '')).strip().upper()
        celular_guardar = str(datos_base.get('celular', '')).strip()
        destino_guardar = str(datos_base.get('destino', '')).strip().upper()
        agencia_guardar = str(datos_base.get('agencia', '')).strip().upper()
        atencion2_guardar = str(datos_base.get('atencion2', '')).strip().upper()
        dni2_guardar = str(datos_base.get('dni2', '')).strip()

        nueva_linea = f"{dni_guardar},{atencion_guardar},{celular_guardar},{destino_guardar},{agencia_guardar},{atencion2_guardar},{dni2_guardar}\n"

        if os.path.exists(ruta_bd_local):
            with open(ruta_bd_local, "r", encoding="utf-8") as f:
                for linea in f:
                    linea_limpia = linea.strip()
                    if not linea_limpia:
                        continue
                    partes = linea_limpia.split(",")
                    if len(partes) >= 1 and partes[0].strip() == dni_guardar:
                        lineas_actualizadas.append(nueva_linea)
                        dni_encontrado = True
                    else:
                        lineas_actualizadas.append(linea_limpia + "\n")

        if not dni_encontrado:
            lineas_actualizadas.append(nueva_linea)

        with open(ruta_bd_local, "w", encoding="utf-8") as f:
            f.writelines(lineas_actualizadas)
            
        # === ENVIAMOS LOS DATOS AL REPORTADOR CORPORATIVO ===
        self.registrar_en_historial_excel(datos_base, total_bultos)
            
        for i in range(1, total_bultos + 1):
            copia_datos = datos_base.copy()
            copia_datos["atencion"] = datos_base['atencion']
            copia_datos["bulto_texto"] = f"({i}/{total_bultos})"
            self.lista_espera.append(copia_datos)

        self.actualizar_tabla_visual()
        self.limpiar_campos_formulario()

    def actualizar_tabla_visual(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        for i, item in enumerate(self.lista_espera, start=1):
            comp_formato = f"{item['tipo_doc'][:4].upper()}: {item['serie']}-{item['numero']}"
            self.tabla.insert("", "end", values=(i, item["atencion"].upper(), item["dni"], item["destino"].upper(), item["celular"], comp_formato), tags=("fila",))

    def limpiar_campos_formulario(self):
        for ent in self.entries.values(): 
            ent.delete(0, tk.END)
        if "Serie" in self.entries:
            self.entries["Serie"].insert(0, "F001")
        if "Bultos" in self.entries:
            self.entries["Bultos"].insert(0, "1")
        self.entries["DNI / RUC 1"].focus()

    def evento_autocompletar_texto(self, event):
        texto_actual = self.entries["Destino"].get().upper()
        if not texto_actual:
            return
        for provincia in self.provincias_peru:
            if provincia.startswith(texto_actual):
                self.entries["Destino"].delete(0, tk.END)
                self.entries["Destino"].insert(0, provincia)
                self.entries["Destino"].select_range(len(texto_actual), tk.END)
                self.entries["Destino"].icursor(len(texto_actual))
                break
    def generar_impresion_dinamica(self):
        if not self.lista_espera:
            messagebox.showwarning("Lista Vacía", "No hay elementos en la lista de espera.")
            return
            
        formato = self.combo_formato.get()
        
        # CORREGIDO: Forzamos a que el PDF se cree físicamente en el lugar exacto del ejecutable
        nombre_archivo = obtener_ruta_salida("etiquetas_distribucion.pdf")
        
        if os.path.exists(nombre_archivo):
            try:
                open(nombre_archivo, "a").close()
            except IOError:
                messagebox.showerror("Archivo Bloqueado", "El PDF 'etiquetas_distribucion.pdf' está abierto en otro programa.\nPor favor, ciérrelo antes de imprimir un nuevo lote.")
                return
        try:
            # === DETECTA EL FORMATO ELEGIDO AL MOMENTO DE IMPRIMIR ===
            if formato == "A4 Horizontal":
                # CORREGIDO: Una etiqueta MAXI gigante que ocupa toda la hoja A4 por cada envío
                pdf = GeneradorEtiquetasA4(orientation='L', unit='mm', format='A4')
                for datos in self.lista_espera:
                    pdf.add_page()
                    pdf.dibujar_etiqueta_maxi(0, 0, datos)
                    
            elif formato == "Térmica 100x150":
                # CONEXIÓN TÉRMICA: Configuramos FPDF con tupla segura (100, 150) para evitar giros
                pdf = GeneradorEtiquetasA4(orientation='P', unit='mm', format=(100, 150))
                pdf.set_auto_page_break(auto=False, margin=0)
                
                for datos in self.lista_espera:
                    pdf.add_page()
                    pdf.dibujar_etiqueta_termica(0, 0, datos)
                    
            else:
                # CORREGIDO: Bloque else ahora contiene correctamente la distribución A4 Vertical
                pdf = GeneradorEtiquetasA4(orientation='P', unit='mm', format='A4')
                posiciones_a4 = [(8, 8), (8, 78), (8, 148), (8, 218)]
                
                for indice, datos in enumerate(self.lista_espera):
                    if indice % 4 == 0:
                        pdf.add_page()
                    indice_hoja = indice % 4
                    x_pos, y_pos = posiciones_a4[indice_hoja]
                    pdf.dibujar_etiqueta_mini(x_pos, y_pos, datos)
            
            # Guardamos y abrimos la vista previa de forma limpia en Windows
            pdf.output(nombre_archivo)
            if hasattr(os, 'startfile'):
                os.startfile(nombre_archivo)
            else:
                webbrowser.open(os.path.abspath(nombre_archivo))
                
        except Exception as e:
            import traceback
            error_detallado = traceback.format_exc()
            messagebox.showerror("Diagnóstico Técnico", f"El proceso falló en:\n\n{error_detallado}")

    def limpiar_lista_completa(self):
        seleccionado = self.tabla.selection()
        if seleccionado:
            for fila in reversed(seleccionado):
                valores = self.tabla.item(fila, "values")
                if valores:
                    indice_visible = int(valores[0])
                    indice_lista = indice_visible - 1
                    if 0 <= indice_lista < len(self.lista_espera): 
                        del self.lista_espera[indice_lista]
            messagebox.showinfo("Registro Eliminado", "Se quitaron los elementos de la lista.")
        else:
            if messagebox.askyesno("Confirmar", "¿Deseas limpiar todos los registros?"): 
                self.lista_espera.clear()
        self.actualizar_tabla_visual()

        # --- FUNCIÓN DE IMPORTACIÓN DE WHATSAPP CON ALINEACIÓN CORREGIDA ---
    def procesar_texto_whatsapp_inteligente(self):
        """ Extrae de forma inteligente DNI/RUC, celular, destino, nombres, bultos y series desde el portapapeles """
        try:
            texto = self.root.clipboard_get().strip()
        except Exception:
            messagebox.showwarning("Portapapeles Vacío", "No se detectó ningún texto copiado.\nPor favor, copie el mensaje de WhatsApp primero.")
            return

        if not texto:
            return

        # Limpiamos los campos antes de la importación mágica
        if hasattr(self, 'limpiar_campos_formulario'):
            self.limpiar_campos_formulario()
        else:
            # Respaldo seguro si la función de limpieza tiene otro nombre
            for clave in ["DNI / RUC 1", "DNI / RUC 2 (Opcional)", "Nombre Completo 1", "Destino", "Celular", "Agencia", "Numero", "Bultos", "Serie"]:
                if clave in self.entries:
                    self.entries[clave].delete(0, tk.END)

        # 1. Buscador Inteligente de Documentos (DNI de 8 dígitos o RUC de 11)
        documentos = re.findall(r'\b\d{8}\b|\b\d{11}\b', texto)
        dni_principal = ""
        if documentos:
            dni_principal = documentos[0]
            if "DNI / RUC 1" in self.entries:
                self.entries["DNI / RUC 1"].insert(0, dni_principal)
            if len(documentos) > 1 and "DNI / RUC 2 (Opcional)" in self.entries:
                self.entries["DNI / RUC 2 (Opcional)"].insert(0, documentos[1])

        # 2. Buscador Inteligente de Celulares (Números de 9 dígitos que empiezan con 9)
        celulares = re.findall(r'\b9\d{8}\b', texto)
        if celulares and "Celular" in self.entries:
            self.entries["Celular"].delete(0, tk.END)  # CORREGIDO: Limpieza antes de insertar
            self.entries["Celular"].insert(0, celulares[0])

        # 3. Buscador de Cantidad de Bultos (Protegido contra variaciones de clave en entries)
        match_bultos = re.search(r'(?i)(\d+)\s*(bulto|paquete|caja|pqte|cant)', texto)
        if match_bultos:
            if "Bultos" in self.entries:
                self.entries["Bultos"].delete(0, tk.END)
                self.entries["Bultos"].insert(0, match_bultos.group(1))
            elif hasattr(self, 'entry_bultos'): 
                self.entry_bultos.delete(0, tk.END)
                self.entry_bultos.insert(0, match_bultos.group(1))

        # 4. Buscador de Comprobante Contable (Busca patrones tipo F001-24, E001-0025, etc.)
        match_comp = re.search(r'(?i)\b([f|e|b]\d{3})[-|\s]*(\d+)\b', texto)
        if match_comp:
            if "Serie" in self.entries:
                self.entries["Serie"].delete(0, tk.END)
                self.entries["Serie"].insert(0, match_comp.group(1).upper())
            if "Numero" in self.entries:
                self.entries["Numero"].delete(0, tk.END)
                self.entries["Numero"].insert(0, match_comp.group(2))

        # 5. Buscador Inteligente de Destinos (Cruza el texto contra tu lista de Provincias del Perú)
        destino_detectado = ""
        if hasattr(self, 'provincias_peru'):
            for provincia in self.provincias_peru:
                if re.search(r'(?i)\b' + re.escape(provincia) + r'\b', texto):
                    destino_detectado = provincia
                    if "Destino" in self.entries:
                        self.entries["Destino"].delete(0, tk.END)  # CORREGIDO: Limpieza antes de insertar
                        self.entries["Destino"].insert(0, destino_detectado)
                    break

        # 6. Extractor de Nombres y Apellidos (Lógica de descarte limpia)
        lineas = [l.strip() for l in texto.splitlines() if l.strip()]
        nombre_detectado = ""
         
        for linea in lineas:
            # Ignoramos líneas que contengan metadatos de agencias, comprobantes o números
            if any(x in linea.lower() for x in ["dni", "ruc", "cel", "9", "bulto", "shalo", "olva", "f00", "b00", "e00", "agencia"]):
                continue
            if destino_detectado and destino_detectado.lower() in linea.lower():
                continue
             
            # Limpieza exacta de caracteres especiales manteniendo letras del alfabeto castellano
            linea_limpia = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', '', linea).strip()
            if len(linea_limpia.split()) >= 2:
                nombre_detectado = linea_limpia.upper()
                break

        # CORREGIDO: Primero limpiamos e intentamos el autocompletado desde la Base de Datos Local
        if "Nombre Completo 1" in self.entries:
            self.entries["Nombre Completo 1"].delete(0, tk.END)

        if dni_principal and hasattr(self, 'verificar_autocompletado_local'):
            self.verificar_autocompletado_local("DNI / RUC 1", "Nombre Completo 1", ignorar_web=True)
             
        # Si la base de datos no tenía el nombre pero el extractor por expresiones regulares sí lo obtuvo, se inyecta
        if nombre_detectado and "Nombre Completo 1" in self.entries:
            if not self.entries["Nombre Completo 1"].get().strip():
                self.entries["Nombre Completo 1"].insert(0, nombre_detectado)

        messagebox.showinfo("Importación Exitosa", "Los datos legibles de WhatsApp han sido distribuidos en las casillas.")

# --- FUNCIONES GLOBALES INDEPENDIENTES ---
def obtener_hwid():
    try:
        # Usamos PowerShell nativo para extraer el ID único del procesador (Seguro en Windows 10 y 11)
        comando = 'powershell -Command "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty ProcessorId"'
        id_maquina = subprocess.check_output(comando, shell=True, creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
        
        if id_maquina:
            return id_maquina
        return "HARDWARE_ID_GENERICO_2026"
    except:
        try:
            # Respaldo clásico alternativo por si PowerShell estuviera bloqueado por políticas de grupo
            comando_alt = 'powershell -Command "(Get-WmiObject Win32_Processor).ProcessorId"'
            id_maquina = subprocess.check_output(comando_alt, shell=True, creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
            if id_maquina:
                return id_maquina
        except:
            pass
        return "HARDWARE_ID_GENERICO_2026"

def verificar_licencia_valida():
    if not os.path.exists(ruta_lic):
        return "FALTA_ARCHIVO"
    try:
        with open(ruta_lic, "r", encoding="utf-8") as f:
            clave_guardada = f.read().strip()
        
        # Desencriptamos la cadena completa volteándola y restando posiciones
        texto_descifrado = "".join(chr(ord(c) - 3) for c in clave_guardada[::-1])
        
        # Separamos el HWID de la fecha usando el divisor secreto "|"
        if "|" not in texto_descifrado:
            return "LICENCIA_CORRUPTA"
            
        hwid_licencia, fecha_vence_str = texto_descifrado.split("|")
        
        # 1. Validación estricta del Hardware (Que no se use en otra PC)
        if hwid_licencia != obtener_hwid():
            return "PC_NO_AUTORIZADA"
            
        # 2. Validación estricta de la Fecha de Soporte/Mantenimiento
        fecha_vence = datetime.datetime.strptime(fecha_vence_str, "%d/%m/%Y").date()
        fecha_actual = datetime.date.today()
        
        if fecha_actual > fecha_vence:
            return "SOPORTE_VENCIDO"
            
        return "VALIDA"
    except:
        return "ERROR_INTERNO"

def llamar_ventana_login():
    ventana_login = tk.Tk()
    ventana_login.title("Acceso al Sistema - DramirenG")
    ventana_login.geometry("380x420")
    ventana_login.configure(bg="#003366")
    ventana_login.resizable(False, False)
    
    ruta_icono = recurso_path("logo_dg.ico")
    if os.path.exists(ruta_icono):
        try: ventana_login.iconbitmap(ruta_icono)
        except: pass

    def ejecutar_validacion():
        usuario_ingresado = ent_user.get().strip()
        contrasena_ingresada = ent_pass.get()

        # Evaluamos el estado detallado del candado de seguridad
        estado_licencia = verificar_licencia_valida()
        
        if estado_licencia == "FALTA_ARCHIVO" or estado_licencia == "PC_NO_AUTORIZADA":
            pc_id = obtener_hwid()
            ventana_login.clipboard_clear()
            ventana_login.clipboard_append(pc_id)
            messagebox.showwarning("Licencia Requerida", f"Computadora no autorizada para este cliente.\n\nCódigo de Máquina: {pc_id}\n(Copiado al portapapeles)\n\nEnvíe este código al administrador.")
            return
            
        elif estado_licencia == "SOPORTE_VENCIDO":
            messagebox.showerror("Mantenimiento Requerido", "El periodo de soporte y actualización técnica de 6 meses ha caducado.\n\nPor favor, contacte con el administrador técnico para renovar su cobertura y habilitar el sistema.")
            return
            
        elif estado_licencia != "VALIDA":
            messagebox.showerror("Error de Seguridad", "El archivo de licencia es inválido o está corrupto.")
            return

        if not os.path.exists(ruta_acc):
            if not usuario_ingresado or not contrasena_ingresada:
                messagebox.showwarning("Configuración Inicial", "Por favor, defina el Usuario y la Contraseña para este cliente.")
                return
            
            usuario_enc = "".join(chr(ord(c) + 2) for c in usuario_ingresado)
            clave_enc = "".join(chr(ord(c) + 2) for c in contrasena_ingresada)
            try:
                with open(ruta_acc, "w", encoding="utf-8") as f:
                    f.write(f"{usuario_enc}\n{clave_enc}")
                messagebox.showinfo("Éxito", "¡Usuario y Contraseña registrados correctamente!\nReabra el programa para iniciar sesión.")
                ventana_login.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron registrar las credenciales: {e}")
            return

        try:
            with open(ruta_acc, "r", encoding="utf-8") as f:
                lineas = f.read().splitlines()
        except:
            messagebox.showerror("Error", "No se pudo leer el archivo de acceso.")
            return
        
        if len(lineas) >= 2:
            user_real = "".join(chr(ord(c) - 2) for c in lineas[0])
            pass_real = "".join(chr(ord(c) - 2) for c in lineas[1])
            
            if usuario_ingresado == user_real and contrasena_ingresada == pass_real:
                ventana_login.destroy()
                root_app = tk.Tk()
                root_app.title("Sistema de Despacho DramirenG")
                root_app.geometry("950x820")
                
                ruta_icono_principal = recurso_path("logo_dg.ico")
                if os.path.exists(ruta_icono_principal):
                    try: root_app.iconbitmap(ruta_icono_principal)
                    except: pass
                
                VentanaDespachoMasivo(root_app)
                root_app.mainloop()
            else:
                messagebox.showerror("Acceso Denegado", "El usuario o la contraseña son incorrectos.")

    lbl_bienvenida = tk.Label(ventana_login, text="¡BIENVENIDO!", font=("Arial", 12, "bold"), bg="#003366", fg="white")
    lbl_bienvenida.pack(pady=(15, 2))
    
    ano_actual = datetime.datetime.now().strftime("%Y")
    txt_sub = f"Control de Despachos Oficial {ano_actual}" if os.path.exists(ruta_acc) else "⚙️ MODO INSTALACIÓN:      Configure el acceso"
    lbl_sub = tk.Label(ventana_login, text=txt_sub, font=("Arial", 9, "italic"), bg="#003366", fg="#b3d9ff")
    lbl_sub.pack(pady=(0, 15))
    
    tk.Label(ventana_login, text="Nombre de Usuario:", font=("Arial", 9, "bold"), bg="#003366", fg="white").pack(pady=2)
    ent_user = tk.Entry(ventana_login, font=("Arial", 10), bd=2, relief="flat", justify="center", width=22)
    ent_user.pack(pady=2, ipady=2)
    
    if os.path.exists(ruta_acc):
        try:
            with open(ruta_acc, "r", encoding="utf-8") as f:
                lineas = f.read().splitlines()
            if len(lineas) >= 1:
                user_sugerido = "".join(chr(ord(c) - 2) for c in lineas[0])
                ent_user.insert(0, user_sugerido)
        except:
            pass
    
    tk.Label(ventana_login, text="Contraseña de Seguridad:", font=("Arial", 9, "bold"), bg="#003366", fg="white").pack(pady=5)
    ent_pass = tk.Entry(ventana_login, font=("Arial", 10), bd=2, relief="flat", show="*", justify="center", width=22)
    ent_pass.pack(pady=2, ipady=2)
    
    txt_btn = "🔓 INGRESAR AL SISTEMA" if os.path.exists(ruta_acc) else "💾 REGISTRAR ACCESO"
    btn_ingresar = tk.Button(ventana_login, text=txt_btn, bg="#ff9900", fg="white", font=("Arial", 9, "bold"), relief="flat", cursor="hand2", command=ejecutar_validacion)
    btn_ingresar.pack(pady=15, ipadx=10, ipady=2)
    
    frame_soporte = tk.Frame(ventana_login, bg="#002244", bd=1)
    frame_soporte.pack(fill="x", side="bottom", ipady=4)
    
    tk.Label(frame_soporte, text="Soporte Técnico de Control Soporte.DramirenG:", font=("Arial", 8, "bold"), bg="#002244", fg="#99ccff").pack()
    tk.Label(frame_soporte, text="📞 Celular: 959237626", font=("Arial", 8), bg="#002244", fg="white").pack()
    tk.Label(frame_soporte, text="✉️ Correo: Soporte.DramirenG@hotmail.com", font=("Arial", 8), bg="#002244", fg="white").pack()
    
    ventana_login.mainloop()

if __name__ == "__main__":
    llamar_ventana_login()




