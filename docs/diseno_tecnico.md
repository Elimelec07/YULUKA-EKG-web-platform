# 📐 Documento de Diseño Técnico
## Plataforma Yuluka‑ECG

---

## 1. Introducción

El presente documento describe el **diseño técnico** de la plataforma **Yuluka‑ECG**, una herramienta web de arquitectura híbrida orientada al aprendizaje y análisis de señales electrocardiográficas (ECG). Este documento tiene como propósito detallar la arquitectura del sistema, los componentes que lo conforman, el flujo de procesamiento de la señal y las decisiones técnicas adoptadas durante su desarrollo.

El diseño técnico constituye el vínculo entre la fundamentación teórica del proyecto y su implementación práctica, permitiendo comprender cómo las técnicas revisadas en el estado del arte se materializan en una solución funcional.

---

## 2. Alcance del Diseño

El alcance del diseño técnico de Yuluka‑ECG abarca:

- Procesamiento automático de señales ECG previamente adquiridas.
- Aplicación de técnicas de filtrado digital para reducción de ruido.
- Detección de eventos cardíacos relevantes (complejos QRS).
- Visualización interactiva de señales y métricas.
- Uso con fines **educativos y formativos** para personal del área de la salud.

Quedan excluidos del alcance del diseño:

- Diagnóstico clínico automatizado.
- Certificación como dispositivo médico.
- Toma de decisiones clínicas reales.
- Adquisición directa de señales desde hardware biomédico.

---

## 3. Arquitectura General del Sistema

Yuluka‑ECG se implementa bajo una **arquitectura web híbrida local–cloud**, organizada en capas funcionales:

- **Capa de Presentación (Frontend Web)**
- **Capa de Servicios (Backend API REST)**
- **Capa de Procesamiento de Señales**
- **Capa de Datos**

Esta organización permite la separación de responsabilidades, mejora la mantenibilidad del sistema y facilita la escalabilidad.

---

## 4. Diseño de Componentes

### 4.1 Frontend Web

**Función:**  
Proporcionar una interfaz gráfica accesible e interactiva para la visualización y análisis educativo de señales ECG.

**Tecnologías utilizadas:**
- HTML5  
- CSS3  
- JavaScript  
- Plotly.js  

**Funciones principales:**
- Carga de señales ECG desde el backend.
- Visualización de señal cruda y señal filtrada.
- Comparación entre métodos de filtrado.
- Visualización de eventos detectados (picos R).
- Interacción diferenciada para usuarios expertos y no expertos.

---

### 4.2 Backend (API REST)

**Función:**  
Gestionar la lógica del sistema y ejecutar los algoritmos de procesamiento de señales.

**Tecnologías utilizadas:**
- Python  
- FastAPI  
- Pydantic  

**Responsabilidades:**
- Exponer servicios REST para carga y procesamiento de señales ECG.
- Coordinar el flujo de datos entre frontend y módulos de procesamiento.
- Garantizar respuestas eficientes para aplicaciones web interactivas.

---

### 4.3 Módulo de Procesamiento de Señales ECG

Este módulo constituye el núcleo funcional del sistema.

**Algoritmos implementados:**
- Filtro Notch (50/60 Hz) para interferencia de red.
- Filtros adaptativos LMS y NLMS.
- Filtrado basado en Transformada Wavelet Discreta (DWT).
- Detección de complejos QRS mediante el algoritmo de Pan‑Tompkins.

**Librerías utilizadas:**
- NumPy  
- SciPy  
- BioSPPy  
- NeuroKit2  

**Objetivo educativo:**  
Permitir observar el impacto de distintas técnicas de filtrado y detección sobre la señal ECG.

---

### 4.4 Capa de Datos

**Origen de los datos:**
- PhysioNet – MIT‑BIH Arrhythmia Database.

**Formatos de trabajo:**
- WFDB (formato original).
- CSV / JSON (intercambio con la API).

**Uso de los datos:**
- Demostración.
- Aprendizaje.
- Validación de algoritmos.

No se almacenan datos personales identificables.

---

## 5. Flujo de Procesamiento de la Señal (Yuluka Flow)

El procesamiento de una señal ECG en Yuluka‑ECG sigue las siguientes etapas:

1. **Ingesta:**  
   Carga de registros ECG en formato CSV o JSON.

2. **Filtrado:**  
   Aplicación de filtros Notch y Wavelet para alcanzar el estado de *Yuluka* (señal depurada).

3. **Detección:**  
   Identificación de complejos QRS mediante el algoritmo de Pan‑Tompkins.

4. **Análisis:**  
   Extracción de características de variabilidad de la frecuencia cardíaca (HRV) y procesos de clasificación cuando aplica.

5. **Visualización:**  
   Representación interactiva de resultados en el frontend.

---

## 6. Tecnologías y Herramientas

| Componente | Tecnología |
|---------|-----------|
| Lenguaje principal | Python |
| Backend | FastAPI |
| Procesamiento de señales | NumPy, SciPy |
| Bioseñales | BioSPPy, NeuroKit2 |
| Frontend | HTML, CSS, JavaScript |
| Visualización | Plotly.js |
| Dataset | WFDB – PhysioNet |

---

## 7. Consideraciones Técnicas

- **Rendimiento:** Optimizado para uso educativo en tiempo casi real.
- **Escalabilidad:** Posibilidad de delegar tareas complejas a la nube.
- **Usabilidad:** Interfaz orientada al aprendizaje progresivo.
- **Seguridad:** No se manejan datos clínicos reales ni sensibles.

---

## 8. Limitaciones del Diseño

- No sustituye software clínico certificado.
- No debe utilizarse para diagnóstico médico.
- Optimizado para entornos educativos, no clínicos.

---

## 9. Advertencia de Uso

> ⚠️ **Advertencia:**  
> Yuluka‑ECG es una plataforma con fines **educativos y de investigación**.  
> Los resultados generados **no deben utilizarse para diagnóstico ni decisiones clínicas reales**.  
> El autor y colaboradores no se responsabilizan por el uso indebido del sistema.

---

## 10. Conclusión del Diseño Técnico

El diseño técnico de Yuluka‑ECG define una plataforma modular, accesible y técnicamente sólida que integra procesamiento de señales ECG y visualización interactiva bajo una arquitectura web moderna. Su enfoque educativo la posiciona como una herramienta eficaz para el aprendizaje del análisis de bioseñales en el área de la salud y la ingeniería biomédica.

---
``
