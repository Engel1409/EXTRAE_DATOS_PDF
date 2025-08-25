import os
import re
import pdfplumber
import pandas as pd
import streamlit as st

# -------------------------------
# CONFIGURACIÓN DE LA APP
# -------------------------------
st.set_page_config(page_title="Procesador de Pólizas", page_icon="📄", layout="wide")

st.title("📄 Procesador de Pólizas en PDF")
st.markdown("Sube tus pólizas en formato PDF y obtén un **Excel procesado automáticamente**.")
st.divider()

# -------------------------------
# SUBIDA DE ARCHIVOS
# -------------------------------
uploaded_files = st.file_uploader("📂 Sube tus PDFs aquí", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_rows = []

    for uploaded_file in uploaded_files:
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"

            # Buscar con expresiones regulares
            poliza = re.search(r"Póliza\s*:\s*(\S+)", text)
            cliente = re.search(r"Cliente\s*:\s*(.+)", text)
            placa = re.search(r"Placa\s*:\s*(\S+)", text)

            all_rows.append({
                "Archivo": uploaded_file.name,
                "Póliza": poliza.group(1) if poliza else "No encontrado",
                "Cliente": cliente.group(1) if cliente else "No encontrado",
                "Placa": placa.group(1) if placa else "No encontrado"
            })

    # -------------------------------
    # CREAR DATAFRAME
    # -------------------------------
    df = pd.DataFrame(all_rows)

    # -------------------------------
    # MOSTRAR MÉTRICAS
    # -------------------------------
    st.subheader("📊 Resumen")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Pólizas procesadas", len(df["Póliza"].unique()))
    with col2:
        st.metric("Clientes encontrados", len(df["Cliente"].unique()))
    with col3:
        st.metric("Placas detectadas", df["Placa"].ne("No encontrado").sum())

    st.divider()

    # -------------------------------
    # PESTAÑAS DE VISUALIZACIÓN
    # -------------------------------
    tab1, tab2 = st.tabs(["📑 Tabla de datos", "📈 Análisis"])

    with tab1:
        st.dataframe(df, use_container_width=True, height=500)

    with tab2:
        st.bar_chart(df["Cliente"].value_counts(), use_container_width=True)

    # -------------------------------
    # DESCARGA DE RESULTADOS
    # -------------------------------
    st.divider()
    st.success("✅ Archivos procesados correctamente")

    @st.cache_data
    def convertir_excel(df):
        return df.to_excel(index=False, engine="openpyxl")

    excel_bytes = convertir_excel(df)

    st.download_button(
        label="⬇️ Descargar Excel",
        data=excel_bytes,
        file_name="polizas_procesadas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("📌 Sube al menos un archivo PDF para comenzar")
