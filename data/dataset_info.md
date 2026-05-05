# 📄 Datasheet del Dataset – Yuluka‑ECG

## 1. Motivación del Dataset

Este dataset se utiliza como recurso educativo y experimental dentro de la plataforma **Yuluka‑ECG**, con el objetivo de facilitar el aprendizaje del procesamiento y análisis de señales electrocardiográficas (ECG). Su propósito principal es apoyar la formación del personal del área de la salud y de estudiantes en ingeniería biomédica, permitiendo la exploración práctica de técnicas de filtrado, detección de eventos cardíacos y evaluación de la calidad de la señal.

---

## 2. Composición del Dataset

El dataset está compuesto por registros de señales electrocardiográficas (ECG) de superficie, provenientes de una base de datos ampliamente aceptada en investigación biomédica.

- **Fuente:** PhysioNet – MIT‑BIH Arrhythmia Database  
- **Tipo de señal:** ECG de superficie  
- **Número de derivaciones:** Según el registro original  
- **Formato:** WFDB (con posibilidad de exportación a CSV y JSON)  

---

## 3. Recolección de los Datos

Los datos fueron recolectados originalmente en entornos clínicos por instituciones médicas asociadas al MIT Laboratory for Computational Physiology. La presente plataforma **no modifica ni amplía la adquisición original**, sino que utiliza los registros como base para análisis y visualización.

---

## 4. Preprocesamiento

Dentro de Yuluka‑ECG, los registros pueden someterse a procesos de:

- Eliminación de interferencia de la red eléctrica (PLI).
- Corrección de deriva de línea base (BW).
- Reducción de ruido muscular (EMG).
- Normalización y segmentación de la señal.
- Detección de complejos QRS (por ejemplo, mediante el algoritmo de Pan‑Tompkins).

El preprocesamiento es configurable y tiene fines demostrativos y educativos.

---

## 5. Usos Previstos

### ✅ Usos Permitidos
- Educación y formación del personal del área de la salud.

``
