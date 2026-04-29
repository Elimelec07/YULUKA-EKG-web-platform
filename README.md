# ecg-analysis-web-platform
Portafolio técnico de Bioingeniería II: Plataforma web híbrida para el procesamiento, análisis y visualización automática de señales ECG.

## 🚀 Descripción del Proyecto
Este repositorio constituye el portafolio técnico del proyecto desarrollado para el curso de Bioingeniería II. La solución aborda la brecha entre la investigación biomédica y la práctica clínica mediante un pipeline integral que procesa señales crudas provenientes de bases de datos estandarizadas como **MIT-BIH** y **PTB-XL**.

### Componentes Principales:
*   **Filtrado Avanzado:** Implementación de técnicas FIR, IIR, Notch, métodos adaptativos (LMS) y transformada Wavelet.
*   **Detección y Extracción:** Algoritmo de **Pan-Tompkins** para complejos QRS y cálculo de parámetros HRV.
*   **Clasificación con Deep Learning:** Modelos de **CNN 1D y LSTM** para identificación de patologías.
*   **Visualización Interactiva:** Dashboard con **FastAPI** (Backend) y **Plotly.js/D3.js** (Frontend) para métricas SNR, MSE y PRD.

## 📂 Estructura del Portafolio
*   `docs/`: Reporte de fundamentación (Estado del arte), matriz de alternativas y diseño técnico.
*   `src/`: Código fuente del pipeline de procesamiento y aplicación web.
*   `data/`: Fichas técnicas de señales y datasets.
*   `evidence/`: Pruebas de validación, resultados y material para el Pitch.

## 🛠️ Tecnologías
Python (NumPy, SciPy, PyWavelets, TensorFlow) | FastAPI | JavaScript (D3.js)
