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

# --- Título principal ---
st.title("📑 Buscador de Pólizas en PDFs")

# --- Subida de archivos PDF ---
uploaded_files = st.file_uploader("Sube tus archivos PDF", type=["pdf"], accept_multiple_files=True)

# --- Procesar PDFs ---
if uploaded_files:
    all_rows = []

    for uploaded_file in uploaded_files:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # Regex de ejemplo (ajústalo a tus datos reales)
                    matches = re.findall(r"Poliza:\s*(\S+).*?Placa:\s*(\S+).*?Valor:\s*(\d+).*?Prima:\s*(\d+)", text, re.S)
                    for m in matches:
                        all_rows.append({
                            "Poliza": m[0],
                            "Placa": m[1],
                            "ValorAsegurado": float(m[2]),
                            "PrimaNeta": float(m[3]),
                            "Archivo": uploaded_file.name
                        })

    # Convertir a DataFrame
    df = pd.DataFrame(all_rows)

    if not df.empty:
        # --- Resumen en tarjetas ---
        col1, col2, col3, col4 = st.columns(4)

        polizas_unicas = df['Poliza'].nunique()
        nro_placas = df['Placa'].notna().sum()
        total_asegurado = df['ValorAsegurado'].sum()
        total_prima = df['PrimaNeta'].sum()

        col1.metric("📄 Pólizas únicas", polizas_unicas)
        col2.metric("🚗 Placas encontradas", nro_placas)
        col3.metric("💰 Total Asegurado", f"S/. {total_asegurado:,.2f}")
        col4.metric("💵 Total Prima Neta", f"S/. {total_prima:,.2f}")

        # --- Mostrar primeros 10 registros ---
        st.write("### Resultados (primeros 10 registros)")
        st.dataframe(df.head(10))

        # --- Botones (Descargar + Limpiar) ---
        col_descargar, col_limpiar = st.columns([2, 1])
        with col_descargar:
            st.download_button(
                label="📥 Descargar Excel",
                data=to_excel(df),  # 🔹 Aquí siempre se exporta el DataFrame completo
                file_name="resultados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col_limpiar:
            if st.button("🧹 Limpiar"):
                st.session_state.clear()
                st.rerun()
    else:
        st.warning("⚠️ No se encontraron coincidencias en los PDFs.") 
