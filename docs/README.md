# Documento de Diseño Técnico: Yuluka-ECG

**Yuluka-ECG** es una plataforma de arquitectura híbrida concebida como una herramienta educativa para el aprendizaje y fortalecimiento de competencias del personal del área de la salud en el análisis de bioseñales, particularmente señales electrocardiográficas. La plataforma está orientada a facilitar la comprensión de los procesos de filtrado, análisis e interpretación de señales ECG mediante visualizaciones interactivas y comparativas, promoviendo un enfoque formativo que integra fundamentos técnicos y clínicos.

## 🏗️ Arquitectura del Sistema
El sistema opera bajo un modelo cliente-servidor (Local-Cloud) para optimizar la latencia y la capacidad de cómputo:

1. **Backend Científico (Python):** 
   - Desarrollado con **Flask** para exposición de servicios REST.
   - Procesamiento de señales con **NumPy**, **SciPy** y **PyWavelets**.
   - Acceso a bases de datos **PTB-XL**.

2. **Frontend Interactivo (Web):**
   - Interfaz responsiva con **HTML5/CSS3**.
   - Visualización dinámica de señales con **Plotly.js** y **D3.js** para mostrar la "armonización" de la señal.

## 🔄 Pipeline de Procesamiento (Yuluka Flow)
Siguiendo la estructura del proyecto, la señal atraviesa las siguientes etapas:
1. **Ingesta:** Carga de registros crudos de la base de datos PTB-XL.
2. **Filtrado:** Aplicación de filtros Notch y Wavelet para alcanzar el estado de "Yuluka" (señal pura).
3. **Detección:** Algoritmo Pan-Tompkins para identificar complejos QRS.
4. **Análisis:** Extracción de características HRV y clasificación con Deep Learning.

# 📂 Documentación y Fundamentación Yuluka-ECG

En esta sección se encuentra la base científica y técnica que soporta las decisiones de diseño de la plataforma.

### Enlaces rápidos a los entregables:
* 📄 **[Resumen del Reporte de Fundamentación](reporte_fundamentacion.md):** Justificación técnica y resumen del estado del arte.
* 📚 **[Versión Extendida del Estado del Arte](ESTADO%20DEL%20ARTE%20Y%20DE%20LA%20TÉCNICA.docx):** Documento original completo con todas las referencias bibliográficas.
* 📊 **[Matriz Comparativa de Alternativas Tecnológicas](matriz_comparativa_alternativas.md):** Análisis comparativo de soluciones existentes y justificación de la selección de Yuluka‑ECG como alternativa óptima.
* 📐 **[Documento de Diseño Técnico](diseno_tecnico.md):** Descripción de la arquitectura del sistema, componentes, flujo de procesamiento y decisiones técnicas de implementación.
