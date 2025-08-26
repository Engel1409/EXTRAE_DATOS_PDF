import os
import re
import io
import pdfplumber
import pandas as pd
import streamlit as st

st.set_page_config(page_title="📄 Procesador de Pólizas", layout="wide")
st.title("📄 Procesador de Pólizas en PDF")

# Inicializar session_state
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame()
if "pagina" not in st.session_state:
    st.session_state.pagina = 1

# Subida de archivos PDF
uploaded_files = st.file_uploader("Sube tus archivos PDF", type="pdf", accept_multiple_files=True)

# Procesar PDFs
if uploaded_files:
    all_rows = []

    for uploaded_file in uploaded_files:
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"

            # Buscar placa
            placa_match = re.search(r"Placa\s*:?[\s\n]*([A-Z0-9-]{5,10})", text, re.IGNORECASE)
            placa = placa_match.group(1) if placa_match else "No encontrada"

            # Regex flexible para ítems
            items = re.findall(r"(\d+)\s+([A-Za-zÁÉÍÓÚÑ0-9\- ]+?)\s+(\d+(?:\.\d{1,2})?)\s+(\d+(?:\.\d{1,2})?)", text)

            for item in items:
                all_rows.append({
                    "Archivo": uploaded_file.name,
                    "Placa": placa,
                    "Código": item[0],
                    "Descripción": item[1].strip(),
                    "Prima": item[2],
                    "Total": item[3]
                })

    if all_rows:
        st.session_state.data = pd.DataFrame(all_rows)
        st.session_state.pagina = 1  # resetear a primera página

# Si hay datos procesados
if not st.session_state.data.empty:
    df = st.session_state.data

    # Tarjetas resumen
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total registros", len(df))
    with col2:
        st.metric("🚗 Placas únicas", df["Placa"].nunique())
    with col3:
        st.metric("📂 PDFs procesados", df["Archivo"].nunique())

    # Paginación
    registros_por_pagina = 10
    total_paginas = (len(df) - 1) // registros_por_pagina + 1

    colA, colB, colC = st.columns([1,2,1])
    with colA:
        if st.button("⬅️ Anterior") and st.session_state.pagina > 1:
            st.session_state.pagina -= 1
    with colC:
        if st.button("Siguiente ➡️") and st.session_state.pagina < total_paginas:
            st.session_state.pagina += 1

    inicio = (st.session_state.pagina - 1) * registros_por_pagina
    fin = inicio + registros_por_pagina

    st.dataframe(df.iloc[inicio:fin], use_container_width=True)
    st.caption(f"Página {st.session_state.pagina} de {total_paginas}")

    # Botón descarga Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Pólizas")
    st.download_button(
        label="📥 Descargar Excel",
        data=output.getvalue(),
        file_name="polizas_procesadas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Botón limpiar
    if st.button("🗑️ Limpiar todo"):
        st.session_state.data = pd.DataFrame()
        st.session_state.pagina = 1
        st.rerun()

else:
    st.info("👆 Sube tus archivos PDF para procesarlos.") 
