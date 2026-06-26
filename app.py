import os
import re
import io
import pdfplumber
import pandas as pd
import streamlit as st

# 1. Configuración de página
st.set_page_config(page_title="POLIDATA & TXT", layout="wide")

# 2. Estilos personalizados para un look corporativo y limpio
st.markdown("""
    <style>
    /* Ocultar elementos de Streamlit para que parezca una app nativa */
    #MainMenu, footer, header { visibility: hidden; }
    .stApp { background-color: #f6f8fa; font-family: 'Segoe UI', Arial, sans-serif; }
    
    /* Botones y diseño */
    h1 { color: #0a3d62; border-left: 5px solid #DA291C; padding-left: 10px; }
    div.stButton > button { background-color: #DA291C !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; }
    div.stDownloadButton > button { background-color: #1e293b !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; }
    </style>
""", unsafe_allow_html=True)

# 3. Navegación superior (Pestañas)
tab1, tab2 = st.tabs(["📄 POLIDATA (PDF)", "🔍 FILTRADOR (TXT)"])

# --- LÓGICA TAB 1: POLIDATA ---
with tab1:
    st.title("📄 POLIDATA")
    st.caption("Extracción automática de datos desde PDF empresariales")
    
    uploaded_files = st.file_uploader("Sube tus archivos PDF aquí", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        all_rows = []
        for uploaded_file in uploaded_files:
            with pdfplumber.open(uploaded_file) as pdf:
                text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
            
            # Extracción de campos clave
            poliza = re.search(r"(?:P\s*[ÓO]?\s*L\s*I\s*Z\s*A|P[ÓO]LIZA)\s*[:\-]?\s*(\d{4,})", text, re.IGNORECASE)
            cliente = re.search(r"Cliente\s+([A-Z ,]+)", text)
            vigencia = re.search(r"Vigencia\s+(\d{2}/\d{2}/\d{4} - \d{2}/\d{2}/\d{4})", text)

            nro_poliza = poliza.group(1) if poliza else "SIN_POLIZA"
            nombre_cliente = cliente.group(1).strip() if cliente else "SIN_CLIENTE"
            rango_vigencia = vigencia.group(1) if vigencia else "SIN_VIGENCIA"

            seccion_pattern = re.compile(r"(SECCION: \d{3} [A-ZÑÁÉÍÓÚ ]+)")
            seccion_indices = [(m.start(), m.group()) for m in seccion_pattern.finditer(text)]
            seccion_indices.append((len(text), None))

            for i in range(len(seccion_indices) - 1):
                sec = seccion_indices[i][1]
                content = text[seccion_indices[i][0]:seccion_indices[i+1][0]]
                for line in content.split("\n"):
                    match = re.match(r"^(.*?)(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d{1,3}(?:,\d{3})*\.\d{2})$", line.strip())
                    if match:
                        all_rows.append([nro_poliza, nombre_cliente, rango_vigencia, sec, match.group(1).strip(), match.group(2), match.group(3)])

        df = pd.DataFrame(all_rows, columns=["Póliza", "Cliente", "Vigencia", "Sección", "Ítem", "Valor Asegurado", "Prima Neta"])
        st.success("✅ Archivos procesados correctamente")
        st.dataframe(df, use_container_width=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        st.download_button("⬇️ Descargar Excel", data=output.getvalue(), file_name="Renovaciones.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- LÓGICA TAB 2: FILTRADOR TXT ---
with tab2:
    st.title("📄 Filtrar líneas (TXT)")
    txt_archivos = st.file_uploader("Sube tus archivos .txt", type=["txt"], accept_multiple_files=True)
    prefijos = ('121', '101', '301', '203', '260')

    if st.button("Procesar TXT") and txt_archivos:
        lineas_filtradas = []
        for archivo in txt_archivos:
            contenido = archivo.read().decode('utf-8', errors='ignore')
            for linea in contenido.splitlines():
                if linea.startswith(prefijos):
                    lineas_filtradas.append({'archivo': archivo.name, 'linea': linea.strip()})
        
        df_txt = pd.DataFrame(lineas_filtradas)
        if not df_txt.empty:
            st.dataframe(df_txt, use_container_width=True)
            st.download_button("📥 Descargar CSV", data=df_txt.to_csv(index=False), file_name="filtrado.csv", mime="text/csv")
        else:
            st.warning("No se encontraron líneas con los prefijos seleccionados.")
