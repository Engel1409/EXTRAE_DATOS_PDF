import os
import re
import io
import pdfplumber
import pandas as pd
import streamlit as st

st.title("📄 Procesador de Pólizas en PDF")

# Subida de archivos PDF
uploaded_files = st.file_uploader("Sube tus archivos PDF", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_rows = []

    for uploaded_file in uploaded_files:
        # Leer PDF en memoria
        with pdfplumber.open(uploaded_file) as pdf:
            text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

        # Extraer datos generales
        poliza = re.search(r"Póliza\s+(\d+)", text)
        cliente = re.search(r"Cliente\s+([A-Z ,]+)", text)
        vigencia = re.search(r"Vigencia\s+(\d{2}/\d{2}/\d{4} - \d{2}/\d{2}/\d{4})", text)

        nro_poliza = poliza.group(1) if poliza else "SIN_POLIZA"
        nombre_cliente = cliente.group(1).strip() if cliente else "SIN_CLIENTE"
        rango_vigencia = vigencia.group(1) if vigencia else "SIN_VIGENCIA"

        # Buscar secciones
        seccion_pattern = re.compile(r"SECCION: \d{3} [A-Z ]+")
        secciones = seccion_pattern.findall(text)

        # Dividir texto por secciones
        seccion_data = {}
        for i, sec in enumerate(secciones):
            start = text.find(sec)
            end = text.find(secciones[i+1]) if i+1 < len(secciones) else len(text)
            seccion_data[sec] = text[start:end]

        # Extraer ítems con valor asegurado y prima neta
        for sec, content in seccion_data.items():
            lines = content.split("\n")
            for i in range(len(lines)):
                line = lines[i].strip()
                match = re.match(
                    r"^(\d+\.|[A-Z]\.)\s+(.*?)(\d{1,3}(?:,\d{3})*(?:\.\d{2}))\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2}))$",
                    line
                )
                if match:
                    item_desc = match.group(2).strip()
                    valor = match.group(3)
                    prima = match.group(4)
                    all_rows.append([nro_poliza, nombre_cliente, rango_vigencia, sec, item_desc, valor, prima])
                else:
                    if re.match(r"^(\d+\.|[A-Z]\.)\s+", line):
                        item_desc = line
                        valor = ""
                        prima = ""
                        for j in range(i+1, min(i+5, len(lines))):
                            nums = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d{2})", lines[j])
                            if len(nums) >= 2:
                                valor, prima = nums[0], nums[1]
                                break
                        all_rows.append([nro_poliza, nombre_cliente, rango_vigencia, sec, item_desc, valor, prima])

    # Crear DataFrame y mostrar en Streamlit
    df = pd.DataFrame(all_rows, columns=["Póliza", "Cliente", "Vigencia", "Sección", "Ítem", "Valor Asegurado", "Prima Neta"])
    st.success("✅ Archivos procesados correctamente")

    # Mostrar tabla
    st.dataframe(df)

    # Guardar Excel en memoria
    output = io.BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    # Botón de descarga
    st.download_button(
        label="⬇️ Descargar Excel",
        data=output,
        file_name="Renovaciones_Procesadas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

