# 📄 Extractor de Datos PDF – MARSH

Aplicación web desarrollada con **Streamlit** para **extraer, consolidar y exportar información clave desde archivos PDF de pólizas MARSH**, enfocada en procesos de **renovaciones y análisis de emisiones**.

Permite cargar múltiples PDFs, procesarlos automáticamente y descargar un **Excel consolidado** con los datos relevantes.

---

## 🚀 Funcionalidades principales

✅ Carga múltiple de archivos PDF  
✅ Extracción automática de:
- Número de **Póliza**
- **Cliente**
- **Vigencia**
- **Secciones**
- **Ítems**
- **Valor Asegurado**
- **Prima Neta**
- **Placa** (si existe)

✅ Resumen de métricas:
- Cantidad de pólizas únicas del grupo

✅ Visualización previa de los datos procesados  
✅ Descarga del resultado en formato **Excel (.xlsx)**  
✅ Interfaz moderna con estilos personalizados

---

## 🛠️ Tecnologías utilizadas

- **Python 3.9+**
- **Streamlit**
- **pdfplumber**
- **Pandas**
- **Regex (re)**
- **OpenPyXL**

---

## 📦 Instalación

```bash
git clone https://github.com/tu-usuario/tu-repositorio.git
cd tu-repositorio
```

```bash
pip install -r requirements.txt
```

---

## ▶️ Ejecución

```bash
streamlit run app.py
```

Abrir en navegador:
```
http://localhost:8501
```

---

## 📂 Estructura del proyecto

```
extractor-pdf-marsh/
│── app.py
│── requirements.txt
│── README.md
```

---

## 📊 Salida del sistema

El Excel generado contiene:

- Póliza
- Cliente
- Vigencia
- Sección
- Ítem
- Valor Asegurado
- Prima Neta
- Placa

---

## 👤 Autor

**Engel García Gama**  
Emisor Profesional – Emisiones Masivas  
Lima, Perú

---

## 📜 Licencia

Uso interno / educativo.
