# 📊 Resultados y Sustentación
## Evidencias del Proyecto Yuluka‑ECG

Este directorio consolida las **evidencias técnicas y resultados finales** del proyecto **Yuluka‑ECG**, como soporte a la fundamentación teórica y al documento de diseño técnico.  
La información aquí presentada permite validar el correcto funcionamiento del pipeline de procesamiento y las decisiones adoptadas durante el desarrollo.

---

## 1. Propósito de la Sección de Evidencias

El objetivo de esta sección es:

- Documentar los **resultados obtenidos** durante el desarrollo del proyecto.
- Evidenciar el desempeño de las técnicas de filtrado y análisis aplicadas.
- Proveer material de **soporte académico y técnico** para evaluaciones, presentaciones y demostraciones.
- Facilitar la trazabilidad entre teoría, diseño e implementación.

---

## 2. Pipeline de Procesamiento (Yuluka Flow)

Siguiendo la arquitectura definida en el documento de diseño técnico, la señal ECG atraviesa las siguientes etapas:

1. **Ingesta**  
   Carga de señales ECG crudas en formatos **CSV** o **JSON**.

2. **Filtrado**  
   Aplicación de filtros **Notch** y técnicas basadas en **Transformada Wavelet**, con el objetivo de alcanzar el estado de *Yuluka* (señal depurada).

3. **Detección**  
   Identificación de complejos **QRS** mediante el algoritmo de **Pan‑Tompkins**.

4. **Análisis**  
   Extracción de características de **variabilidad de la frecuencia cardíaca (HRV)** y procesos de clasificación mediante técnicas de *Deep Learning* (cuando aplica).

---

## 3. Evidencias Disponibles

### 3.1 Resultados Cuantitativos

Incluyen métricas de desempeño obtenidas tras la aplicación de las distintas técnicas de procesamiento:

- Gráficas comparativas de señal ECG (cruda vs filtrada).
- Métricas de calidad:
  - **SNR (Signal‑to‑Noise Ratio)**
  - **MSE (Mean Squared Error)**
  - **PRD (Percent Root Difference)**
- Comparación entre métodos de filtrado.

📂 *Archivos asociados:*  
- Gráficas
- Capturas de resultados
- Exportaciones numéricas

---

### 3.2 Pitch del Proyecto

Material de presentación ejecutiva que resume:

- Problema abordado
- Enfoque de solución
- Arquitectura propuesta
- Principales resultados
- Impacto educativo del sistema

📂 *Archivos asociados:*  
- Presentación (PDF / PPT)

---

### 3.3 Demostración Funcional

Evidencia del funcionamiento real de la plataforma Yuluka‑ECG mediante:

- Video demostrativo del pipeline completo.
- Capturas del frontend web.
- Enlaces a despliegue local o demostración en vivo (si aplica).

📂 *Archivos asociados:*  
- Video
- Capturas de pantalla
- Enlaces externos (cuando corresponda)

---

## 4. Relación con la Documentación del Proyecto

Esta sección se complementa directamente con los siguientes documentos:

- 📘 **Documento de Diseño Técnico:**  
  `docs/diseno_tecnico.md`

- 📄 **Reporte de Fundamentación Técnica (Resumen):**  
  `docs/fundamentacion_resumen.md`

- 📚 **Estado del Arte (Versión Extendida):**  
  `docs/estado_del_arte_completo.md`

Las evidencias aquí presentadas permiten validar de forma práctica los conceptos y decisiones descritos en dichos documentos.

---

## 5. Consideraciones Finales

- Las evidencias tienen un **propósito educativo y académico**.
- Los resultados **no deben interpretarse como diagnóstico clínico**.
- Este material respalda la correcta implementación del sistema conforme a su diseño técnico.

---

📌 **Proyecto:** Yuluka‑ECG  
📌 **Área:** Procesamiento de Bioseñales / Ingeniería Biomédica / Salud Digital  
📌 **Autor:** Elimelec J. R. Melo
``
