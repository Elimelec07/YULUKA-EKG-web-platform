# 🫀 Yuluka‑ECG
## Reporte de Fundamentación Técnica

---

## 📌 1. Introducción y Justificación

El **electrocardiograma (ECG)** es la herramienta de referencia para la detección y monitorización de enfermedades cardiovasculares; sin embargo, su análisis automatizado depende de forma crítica de la calidad del procesamiento aplicado a la señal. En la práctica, muchas soluciones existentes requieren software especializado y conocimientos técnicos avanzados, lo que limita su accesibilidad en contextos educativos y de formación clínica.

**Yuluka‑ECG** surge con el propósito de cerrar la brecha entre la investigación biomédica y la práctica clínica‑formativa, ofreciendo una **plataforma web accesible** que integra técnicas avanzadas de procesamiento de señales ECG junto con **visualización interactiva**. La herramienta está concebida como un entorno de **aprendizaje para el personal del área de la salud**, facilitando la comprensión de los efectos del filtrado, la detección de eventos cardíacos y la interpretación básica de resultados.

---

## 📚 2. Estado del Arte (Resumen Técnico)

Con base en una revisión exhaustiva de la literatura científica reciente, se identifican los siguientes aspectos clave en el procesamiento de señales ECG:

### 🔊 Tipos de Ruido en Señales ECG

Las señales ECG suelen estar contaminadas por diversos tipos de interferencia:

- **Deriva de línea base (BW):** asociada a respiración y movimientos del paciente.  
- **Interferencia de la red eléctrica (PLI):** típicamente a 50/60 Hz.  
- **Ruido muscular (EMG):** ruido no estacionario de alta frecuencia.  

Estos ruidos degradan la calidad de la señal y justifican la necesidad de un filtrado previo al análisis.

---

### 🔧 Técnicas de Filtrado

#### ✅ Filtros Clásicos
Los filtros digitales clásicos, especialmente los **filtros Notch**, son altamente eficaces para suprimir la interferencia de la red eléctrica (50/60 Hz) con una baja carga computacional. No obstante, su desempeño es limitado frente a ruidos no estacionarios.

#### ✅ Filtros Adaptativos
Algoritmos como **LMS** y **NLMS** se destacan por su capacidad de ajustar dinámicamente sus coeficientes, lo que los hace adecuados para la eliminación de ruidos no estacionarios como EMG y artefactos de movimiento, incluso en tiempo real.

#### ✅ Transformada Wavelet Discreta (DWT)
La **DWT** es uno de los métodos más utilizados en el procesamiento de señales ECG debido a su capacidad de descomponer la señal en múltiples resoluciones temporales y frecuenciales, alcanzando mejoras de hasta **25 dB en la relación señal‑ruido (SNR)**.

---

### ❤️ Detección de Complejos QRS

El algoritmo de **Pan‑Tompkins** continúa siendo el estándar de referencia para la detección de complejos QRS, gracias a su robustez y a una precisión superior al **99 %** en bases de datos estandarizadas como **MIT‑BIH**.

---

## 🧠 3. Estado de la Técnica y Tecnologías Seleccionadas

Yuluka‑ECG adopta un **stack tecnológico moderno** para garantizar eficiencia, accesibilidad y escalabilidad.

### ⚙️ Backend
- **Lenguaje:** Python  
- **Framework:** FastAPI (servicios REST)  
- **Librerías científicas:**  
  - `SciPy` para filtrado digital  
  - `BioSPPy` o `NeuroKit2` para detección y extracción de características  

### 🎨 Frontend
- **Tecnologías:** HTML5, CSS3 y JavaScript  
- **Visualización:** `Plotly.js` para señales y métricas interactivas  

### ☁️ Arquitectura
La plataforma se implementa bajo una **arquitectura híbrida local–cloud**, lo que permite:

- Procesamiento ligero e interactivo en el entorno local o navegador.  
- Delegar tareas computacionalmente intensivas (por ejemplo, entrenamiento de modelos de *Deep Learning*) a la nube.  

Este enfoque resulta ideal para escenarios educativos y de formación con recursos limitados.

---

## 📐 4. Estándares y Normatividad

El desarrollo de Yuluka‑ECG se alinea conceptualmente con estándares internacionales reconocidos:

- **AAMI** e **IEC 60601‑2‑25:** evaluación de algoritmos y preservación morfológica del ECG.  
- **Formatos de datos:**  
  - `WFDB` como estándar de investigación fisiológica.  
  - `CSV` y `JSON` como formatos universales para interoperabilidad web.

> ⚠️ *Yuluka‑ECG no es un dispositivo médico certificado; está orientado a fines educativos, formativos y de apoyo al aprendizaje en el área de la salud.*

---

## 🚀 Enfoque del Proyecto

Yuluka‑ECG se posiciona como una **herramienta de aprendizaje interactiva** que permite al personal de salud:

- Explorar el impacto de diferentes técnicas de filtrado.  
- Visualizar señales ECG antes y después del procesamiento.  
- Comprender fundamentos técnicos sin requerir conocimientos avanzados de programación.  

---

📘 **Contacto y Proyecto Académico**  
Proyecto desarrollado con fines educativos y de investigación en procesamiento de bioseñales.
