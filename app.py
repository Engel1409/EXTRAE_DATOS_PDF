import os
import re
import io
import pdfplumber
import pandas as pd
import streamlit as st

st.title("📄POLIDATA")
st.caption("Extracción automática de datos desde PDF empresariales")

# --- ESTILOS ---
st.markdown("""
<style>
.stApp {
    background-color: #f6f8fa;
    font-family: 'Segoe UI', Arial, sans-serif;
}
h1 {
    color: #0a3d62;
}
.stMetric {
    background: #dff9fb !important;
    border-radius: 10px;
    padding: 5px;
    text-align: center;
}
.stDataFrame {
    background: #f1f2f6;
    border-radius: 8px;
}
button, .stDownloadButton {
    background-color: #DA291C !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES ROBUSTAS ---

def limpiar_texto(text):
    return re.sub(r"\s+", " ", text)


def extraer_poliza(text):
    patrones = [
        r"P[oó]liza\s*[:\-]?\s*(\d+)",
        r"P\s*l\s*i\s*z\s*a\s*[:\-]?\s*(\d+)",
        r"P\s*liza\s*[:\-]?\s*(\d+)",
        r"Poliza\s*[:\-]?\s*(\d+)"
    ]

    for patron in patrones:
        match = re.search(patron, text, re.IGNORECASE)
        if match:
            return match.group(1)

    match = re.search(r"Operaci[oó]n\s*:?\s*\d+.*?(\d{4,})", text, re.IGNORECASE)
    if match:
        return match.group(1)

    numeros = re.findall(r"\b\d{5,}\b", text)
    return numeros[0] if numeros else "SIN_POLIZA"


def extraer_operacion(text):
    patrones = [
        r"Operaci[oó]n\s*[:\-]?\s*(\d+)",
        r"Operaci\s*n\s*[:\-]?\s*(\d+)",
        r"Nro\.?\s*Operaci[oó]n\s*[:\-]?\s*(\d+)",
        r"Operacion\s*[:\-]?\s*(\d+)"
    ]

    for patron in patrones:
        match = re.search(patron, text, re.IGNORECASE)
        if match:
            return match.group(1)

    match = re.search(r"Operaci.*?(\d{5,})", text, re.IGNORECASE)
    return match.group(1) if match else "SIN_OPERACION"


# --- CARGA DE ARCHIVOS ---
st.markdown("**Arrastra y suelta tus PDFs o haz clic en Browse files**")
uploaded_files = st.file_uploader("Sube tus archivos PDF", type="pdf", accept_multiple_files=True)


if uploaded_files:
    all_rows = []

    for uploaded_file in uploaded_files:
        with pdfplumber.open(uploaded_file) as pdf:
            text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

        # 🔥 LIMPIEZA CLAVE
        text = limpiar_texto(text)

        # --- EXTRACCIÓN ---
        nro_poliza = extraer_poliza(text)
        nro_operacion = extraer_operacion(text)

        cliente = re.search(r"Cliente\s+([A-Z ,]+)", text, re.IGNORECASE)
        vigencia = re.search(r"Vigencia\s+(\d{2}/\d{2}/\d{4} - \d{2}/\d{2}/\d{4})", text)

        nombre_cliente = cliente.group(1).strip() if cliente else "SIN_CLIENTE"
        rango_vigencia = vigencia.group(1) if vigencia else "SIN_VIGENCIA"

        # --- SECCIONES ---
        seccion_pattern = re.compile(r"(SECCION: \d{3} [A-ZÑÁÉÍÓÚ ]+)")
        seccion_indices = [(m.start(), m.group()) for m in seccion_pattern.finditer(text)]
        seccion_indices.append((len(text), None))

        seccion_data = {}
        for i in range(len(seccion_indices) - 1):
            start_idx = seccion_indices[i][0]
            end_idx = seccion_indices[i + 1][0]
            seccion = seccion_indices[i][1]
            seccion_data[seccion] = text[start_idx:end_idx]

        # --- ITEMS ---
        for sec, content in seccion_data.items():
            lines = content.split("\n")

            for i, line in enumerate(lines):
                line = line.strip()

                match = re.match(r"^(.*?)(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d{1,3}(?:,\d{3})*\.\d{2})$", line)

                if match:
                    item_desc = match.group(1).strip()
                    valor = match.group(2)
                    prima = match.group(3)

                    placa = ""
                    for j in range(i, max(i - 3, -1), -1):
                        placa_match = re.search(r"PLACA:\s*([A-Z0-9]+)", lines[j])
                        if placa_match:
                            placa = placa_match.group(1)
                            break

                    all_rows.append([
                        nro_poliza,
                        nro_operacion,
                        nombre_cliente,
                        rango_vigencia,
                        sec,
                        item_desc,
                        valor,
                        prima,
                        placa
                    ])

    # --- DATAFRAME ---
    df = pd.DataFrame(
        all_rows,
        columns=[
            "Póliza",
            "Operación",
            "Cliente",
            "Vigencia",
            "Sección",
            "Ítem",
            "Valor Asegurado",
            "Prima Neta",
            "Placa"
        ]
    )

    # --- KPIs ---
    total_prima = pd.to_numeric(df["Prima Neta"].str.replace(",", ""), errors="coerce").sum()
    total_valor = pd.to_numeric(df["Valor Asegurado"].str.replace(",", ""), errors="coerce").sum()
    polizas_unicas = df["Póliza"].nunique()

    c1, c2, c3 = st.columns(3)
    c1.metric("🛡️ Cantidad Pólizas", polizas_unicas)
    c2.metric("💵 Prima Total", f"${total_prima:,.2f}")
    c3.metric("🏦 Valor Asegurado", f"${total_valor:,.2f}")

    # --- TABLA ---
    st.success("✅ Procesamiento completado")
    st.dataframe(df.head(10))

    # --- EXPORTAR EXCEL ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    output.seek(0)

    st.download_button(
        label="⬇️ Descargar Excel",
        data=output,
        file_name="Renovaciones_Procesadas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
