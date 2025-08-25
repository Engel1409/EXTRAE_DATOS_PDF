import os
import re
import io
import pdfplumber
import pandas as pd
import streamlit as st

# --- Función para exportar a Excel ---
def to_excel(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")
    df.to_excel(writer, index=False, sheet_name="Resultados")
    writer.close()
    processed_data = output.getvalue()
    return processed_data

st.title("📑 Buscador de Pólizas en PDFs")

# Subida de PDFs
uploaded_files = st.file_uploader("Sube tus archivos PDF", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_rows = []

    # 🔹 Tu lógica original para recorrer PDFs
    for uploaded_file in uploaded_files:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # 🔹 Aquí NO toqué tu regex, sigue como lo tenías
                    matches = re.findall(r"Poliza:\s*(\S+).*?Placa:\s*(\S+).*?Valor:\s*(\d+).*?Prima:\s*(\d+)", text, re.S)
                    for m in matches:
                        all_rows.append({
                            "Poliza": m[0],
                            "Placa": m[1],
                            "ValorAsegurado": float(m[2]),
                            "PrimaNeta": float(m[3]),
                            "Archivo": uploaded_file.name
                        })

    df = pd.DataFrame(all_rows)

    if not df.empty:
        # --- 🔹 Tarjetas resumen ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📄 Pólizas únicas", df['Poliza'].nunique())
        col2.metric("🚗 Placas encontradas", df['Placa'].notna().sum())
        col3.metric("💰 Total Asegurado", f"S/. {df['ValorAsegurado'].sum():,.2f}")
        col4.metric("💵 Total Prima Neta", f"S/. {df['PrimaNeta'].sum():,.2f}")

        # --- 🔹 Mostrar solo los 10 primeros ---
        st.write("### Resultados (primeros 10 registros)")
        st.dataframe(df.head(10))

        # --- 🔹 Botones de acción ---
        col_descargar, col_limpiar = st.columns([2, 1])
        with col_descargar:
            st.download_button(
                label="📥 Descargar Excel",
                data=to_excel(df),   # 👉 aquí va SIEMPRE el df completo
                file_name="resultados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col_limpiar:
            if st.button("🧹 Limpiar"):
                st.session_state.clear()
                st.rerun()
    else:
        st.warning("⚠️ No se encontraron coincidencias en los PDFs.") 
