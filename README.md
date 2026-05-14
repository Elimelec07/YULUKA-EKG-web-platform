# Yuluka-EKG: Plataforma Web para el Análisis Armónico de Señales
Hola. Bienvenidos al portafolio Yuluka-EKG este nace de la necesidad de evolucionar la forma en que presentamos la ingeniería. En lugar de informes tradicionales, aquí encontrarás un ecosistema digital que documenta el desarrollo de nuestro proyecto.

## 🚀 Descripción del Proyecto
Este repositorio constituye el portafolio técnico del proyecto Yuluka-EKG. Este proyecto aborda el uso de una herramienta de apoyo para estudiantes del area de la salud interesados en aprender a analizar y diagnosticar señales EKG esto se logra mediante un ecosistema web integral que procesa datos y señales reales provenientes de la base de datos clínica estandarizada **PTB-XL (PhysioNet)**, transformándolas en herramientas pedagógicas interactivas.

### Componentes Principales:
*   **DSP Pedagógico:** Filtros en tiempo real (SciPy: Notch 60 Hz, Butterworth 0.5-40 Hz y Savitzky-Golay) para la eliminación guiada de ruidos hospitalarios comunes (red eléctrica y respiración).
*   **Quiz Clínico Simulado:** Evaluación interactiva (quiz.html) basada en casos reales de PTB-XL, enfocada en el reconocimiento de patrones y toma de decisiones.
*   **Retroalimentación Fisiopatológica:** Corrección inmediata que vincula los errores o aciertos con medidas clínicas exactas (como el intervalo PR o segmento ST) y su causa biológica.
*   **Tutor Inteligente (Monitor-Bot):** Asistente integrado con la API de Google Gemini 2.5 Flash que lee el contexto dinámico del paciente en pantalla y ofrece pistas visuales sin dar la respuesta directa.
*   **Métricas y Metacognición:** Base de datos relacional (SQLite + Flask-Login) que registra el progreso del estudiante para identificar sus debilidades y sugerir temas de repaso.
*   **Interfaz y Despliegue:** Dashboard responsivo de 12 derivaciones en papel milimetrado (Flask + Chart.js), optimizado para pruebas remotas en tiempo real a través de Ngrok.

## 📂 Estructura del Portafolio
*   `docs/`: Reporte de fundamentación (Estado del arte), matriz de alternativas y diseño técnico.
*   `src/`: Código fuente del pipeline de la aplicación web.
*   `data/`: Fichas técnicas de señales y datasets.
*   `evidence/`: Pruebas de validación, resultados y material para el Pitch.

## 🛠️ Tecnologías
* Backend: Python | Flask | Flask-Login | Flask-SQLAlchemy
* Procesamiento de Señales (DSP) e IA: SciPy | WFDB (PhysioNet) | Google Gemini API
* Base de Datos: SQLite
* Frontend: JavaScript (ES6+) | Chart.js | HTML5 | CSS3
* Despliegue y Pruebas: Ngrok | Git
