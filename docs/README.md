# Documento de Diseño Técnico: Yuluka-ECG

**Yuluka-ECG** es una plataforma de arquitectura híbrida diseñada para la limpieza y análisis de bioseñales, inspirada en el concepto de armonía de las culturas de la Sierra Nevada de Santa Marta.

## 🏗️ Arquitectura del Sistema
El sistema opera bajo un modelo cliente-servidor (Local-Cloud) para optimizar la latencia y la capacidad de cómputo:

1. **Backend Científico (Python):** 
   - Desarrollado con **FastAPI** para exposición de servicios REST.
   - Procesamiento de señales con **NumPy**, **SciPy** y **PyWavelets**.
   - Acceso a bases de datos **WFDB** (MIT-BIH).

2. **Frontend Interactivo (Web):**
   - Interfaz responsiva con **HTML5/CSS3** y **Tailwind CSS**.
   - Visualización dinámica de señales con **Plotly.js** y **D3.js** para mostrar la "armonización" de la señal[cite: 1].

## 🔄 Pipeline de Procesamiento (Yuluka Flow)
Siguiendo la estructura del proyecto, la señal atraviesa las siguientes etapas:
1. **Ingesta:** Carga de registros crudos en formato CSV/JSON.
2. **Filtrado:** Aplicación de filtros Notch y Wavelet para alcanzar el estado de "Yuluka" (señal pura).
3. **Detección:** Algoritmo Pan-Tompkins para identificar complejos QRS.
4. **Análisis:** Extracción de características HRV y clasificación con Deep Learning[cite: 1].

# 📂 Documentación y Fundamentación Yuluka-ECG

En esta sección se encuentra la base científica y técnica que soporta las decisiones de diseño de la plataforma.

### Enlaces rápidos a los entregables:
* 📄 **[Resumen del Reporte de Fundamentación](reporte_fundamentacion.md):** Justificación técnica y resumen del estado del arte.
* 📚 **[Versión Extendida del Estado del Arte](ESTADO%20DEL%20ARTE%20Y%20DE%20LA%20TÉCNICA.docx):** Documento original completo con todas las referencias bibliográficas.
