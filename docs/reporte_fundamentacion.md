Reporte de Fundamentación Técnica: Yuluka-ECG
1. Introducción y Justificación
El electrocardiograma (ECG) es la herramienta de referencia para detectar enfermedades cardiovasculares, pero su análisis automatizado depende críticamente de la calidad del procesamiento aplicado a la señal. Yuluka-ECG surge para cerrar la brecha entre la investigación biomédica y la práctica clínica, ofreciendo una plataforma web accesible que integra filtrado avanzado y visualización interactiva.  
+1

2. Estado del Arte (Resumen Técnico)
Basado en la revisión exhaustiva de la literatura actual, se identifican las siguientes áreas críticas:

Tipos de Ruido: Las señales ECG enfrentan interferencias como la deriva de línea base (BW), la interferencia de la red eléctrica (PLI a 60 Hz) y ruidos musculares (EMG).  

Técnicas de Filtrado:

Filtros Clásicos: Los filtros Notch son altamente eficaces para suprimir la PLI de 50/60 Hz con baja carga computacional.  

Filtros Adaptativos: Algoritmos como LMS y NLMS son ideales para ruidos no estacionarios debido a su capacidad de ajustar coeficientes en tiempo real.  

Transformada Wavelet (DWT): Es uno de los métodos más empleados por su capacidad de descomponer la señal en múltiples resoluciones, logrando mejoras de hasta 25 dB en la relación señal-ruido (SNR).  

Detección de QRS: El algoritmo de Pan-Tompkins sigue siendo el estándar de oro por su robustez y precisión superior al 99% en bases de datos como MIT-BIH.  

3. Estado de la Técnica y Tecnologías Seleccionadas
La plataforma adopta un stack tecnológico moderno para garantizar eficiencia y accesibilidad:

Backend: Utiliza Python con FastAPI para la exposición de servicios REST, integrando librerías científicas como SciPy para filtros e IBioSPPy o NeuroKit2 para extracción de características.  

Frontend: Se implementa con HTML5, CSS3 y JavaScript, empleando Plotly.js para la visualización interactiva de señales y métricas.  

Arquitectura: Se define como una arquitectura híbrida local-cloud, permitiendo el procesamiento ligero en el borde y delegando tareas complejas (como entrenamiento de modelos Deep Learning) a la nube.  

4. Estándares y Normatividad
El desarrollo se alinea conceptualmente con estándares internacionales como:

AAMI e IEC 60601-2-25: Para la evaluación de algoritmos y preservación morfológica.  

Formatos de Datos: Adopción de estándares de investigación como WFDB, además de formatos universales como CSV y JSON para asegurar la interoperabilidad.
