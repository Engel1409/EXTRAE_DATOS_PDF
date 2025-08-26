import os
import re
import io
import pdfplumber
import pandas as pd
import streamlit as st

st.title("📄 Procesador de Pólizas en PDF")

# -- Estado para reiniciar widgets --
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

def limpiar():
    # Incrementa la key para recrear el file_uploader
    st.session_state.uploader_key += 1
    # Limpia caches (por si acaso) y estado excepto la key del uploader
    try:
        st.cache_data.clear()
        st.cache_resource.clear()
    except Exception:
        pass
    # Elimina cualquier otra variable de estado que se haya guardado
    for k in list(st.session_state.keys()):
        if k not in ("uploader_key",):
            del st.session_state[k]
    st.rerun()

# Subida de archivos PDF con key dinámica
uploaded_files = st.file_uploader(
    "Sube tus archivos PDF",
    type="pdf",
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}"
)

# Función para extraer la placa desde la columna "Ítem"
def extraer_placa_desde_item(item):
    if isinstance(item, str):
        match = re.search(r"PLACA:\s*([A-Z0-9]+)", item)
        return match.group(1) if match else ""
    return ""

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

        # Extraer ítems con valor asegurado y prima neta (regex flexible)
        for sec, content in seccion_data.items():
            lines = content.split("\n")
            for i in range(len(lines)):
                line = lines[i].strip()

                match = re.match(
                    r"^(\d+\.|[A-Z]\.)\s+(.*?)(\d{1,3}(?:,\d{3})*(?:\.\d{2}))?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2}))?$",
                    line
                )
                if match:
                    item_desc = match.group(2).strip()
                    valor = match.group(3) if match.group(3) else ""
                    prima = match.group(4) if match.group(4) else ""
                    all_rows.append([nro_poliza, nombre_cliente, rango_vigencia, sec, item_desc, valor, prima])
                else:
                    if re.match(r"^(\d+\.|[A-Z]\.)\s+", line):
                        item_desc = line
                        valor = ""
                        prima = ""
                        for j in range(i+1, min(i+5, len(lines))):
                            nums = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d{2})", lines[j])
                            if len(nums) >= 1:
                                valor = nums[0]
                            if len(nums) >= 2:
                                prima = nums[1]
                                break
                        all_rows.append([nro_poliza, nombre_cliente, rango_vigencia, sec, item_desc, valor, prima])

    # Crear DataFrame
    df = pd.DataFrame(
        all_rows,
        columns=["Póliza", "Cliente", "Vigencia", "Sección", "Ítem", "Valor Asegurado", "Prima Neta"]
    )

    # Extraer la placa desde la columna "Ítem"
    df["Placa"] = df["Ítem"].apply(extraer_placa_desde_item)

    if not df.empty:
        # --- Tarjetas resumen ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Pólizas únicas", df["Póliza"].nunique())
        col2.metric("Placas encontradas", (df["Placa"].astype(str).str.len() > 0).sum())

        # Manejo de conversión de números con comas
        try:
            total_asegurado = df["Valor Asegurado"].replace({",": ""}, regex=True).astype(float).sum()
            total_prima = df["Prima Neta"].replace({",": ""}, regex=True).astype(float).sum()
        except Exception:
            total_asegurado = 0.0
            total_prima = 0.0
        col3.metric("Total Asegurado", f"S/. {total_asegurado:,.2f}")
        col4.metric("Total Prima Neta", f"S/. {total_prima:,.2f}")

        # Mostrar cantidad total procesada
        st.info(f"📊 Registros extraídos: {len(df)}")

        # Mostrar tabla (solo 10 registros)
        st.success("✅ Archivos procesados correctamente")
        st.dataframe(df.head(10), use_container_width=True)

        # Guardar Excel en memoria (todos los registros)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        # Botones en columnas
        col_descargar, col_limpiar = st.columns([2, 1])
        with col_descargar:
            st.download_button(
                label="⬇️ Descargar Excel",
                data=output,
                file_name="Renovaciones_Procesadas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with col_limpiar:
            st.button("🧹 Limpiar", on_click=limpiar, use_container_width=True)
    else:
        st.warning("No se encontraron ítems en los PDFs subidos.")
        # Botón de limpiar visible aunque no haya datos
        st.button("🧹 Limpiar", on_click=limpiar)
else:
    # Si aún no se suben archivos, igual mostramos el botón de limpiar por si quedó algo cargado
    st.button("🧹 Limpiar", on_click=limpiar)
