# 📐 Documento de Diseño Técnico
## Plataforma Yuluka‑EKG

---

## 1. Introducción

Yuluka-EKG es una plataforma web interactiva diseñada para la formación clínica en cuidado crítico. El sistema permite la visualización simultánea de electrocardiogramas (EKG) de 12 derivaciones, la manipulación de filtros digitales para la remoción de artefactos técnicos, y la evaluación interactiva mediante quices dinámicos respaldados por un tutor cognitivo basado en Inteligencia Artificial.

### Objetivos Técnicos
- **Procesamiento en Backend: Filtrar bioseñales reales de la base de datos PTB-XL reduciendo el ruido de la red eléctrica colombiana (60 Hz) y variaciones de línea base sin introducir distorsiones de fase.**
- **Persistencia Local Eficiente: Registrar de forma segura sesiones de usuarios y métricas de rendimiento clínico sin requerir infraestructura de servidores pesada.**
- **Inteligencia Artificial de Bajo Costo: Implementar un agente conversacional contextualizado capaz de guiar de forma pedagógica a los usuarios sin comprometer la cuota de tokens disponibles.**

---

## 2. Alcance del Diseño

Arquitectura del Sistema

El software sigue un patrón arquitectónico Cliente-Servidor de Capa Ligera, optimizado para ejecuciones locales con capacidad de escalamiento inmediato a entornos de nube públicos (PaaS).
- **Capa de Presentación (Frontend): Interfaz SPA (Single Page Application) construida sobre estándares web (HTML5, CSS3, JS ES6). Utiliza el elemento Canvas mediante Chart.js para renderizar flujos vectoriales de 12 canales simulando papel milimetrado clínico a 25mm/s y 1mV/cm.**
- **Capa de Lógica de Negocio (Backend): Servidor asíncrono basado en Flask (Python). Se encarga de la orquestación de la base de datos, el consumo de la API de IA externa y la ejecución de los algoritmos de procesamiento digital de señales (DSP).**
- **Servicios Externos: Conexión HTTPS hacia la API de Google AI Studio para el procesamiento del lenguaje natural mediante el modelo Gemini 1.5 Flash.**
 
---

### 3. Arquitectura General del Sistema

Se implementa una arquitectura de almacenamiento relacional basada en SQLite gestionada a través del ORM Flask-SQLAlchemy. Este enfoque garantiza portabilidad absoluta al guardar la base de datos en un único archivo físico (.db) en el directorio raíz.

- **Capa de Presentación (Frontend Web)**
- **Capa de Servicios (Backend API REST)**
- **Capa de Procesamiento de Señales**
- **Capa de Datos**
Esta organización permite la separación de responsabilidades, mejora la mantenibilidad del sistema y facilita la escalabilidad.

### Diccionario de Datos Clave
Tabla: Usuarios
- **id (Integer, Primary Key): Identificador único autoincremental.**
- **nombre (String): Nombre o identificador del estudiante.**
- **correo (String, Unique): Correo electrónico para el inicio de sesión.**
- **password_hash (String): Clave encriptada utilizando algoritmos de derivación de funciones criptográficas (vía Werkzeug).**

Tabla: ResultadosQuiz
- **id (Integer, Primary Key): Identificador único del intento.**
- **user_id (Integer, Foreign Key): Referencia apuntando a Usuarios.id.**
- **categoria_patologia (String): Clasificación del caso evaluado (NORM, MI [Infarto], ARRH [Arritmia], CD [Bloqueos de Conducción]).**
- **es_correcto (Boolean): Almacena si el estudiante acertó la conducta y el diagnóstico.**
- **fecha (DateTime): Registro temporal automático del intento para cálculos de analítica evolutiva.**

---

## 4. Diseño de modulo criticos

### Módulo 1: Procesamiento Digital de Señales (DSP)
Módulo encargado de la remoción de ruido mediante la librería SciPy.signal. Para evitar el desfase temporal de las ondas P-QRS-T (lo cual alteraría los diagnósticos clínicos de intervalos), todas las operaciones se ejecutan empleando filtrado bidireccional de fase cero (filtfilt).
- **Filtro Notch (Rechazo de Banda): Configurado exactamente a una frecuencia central de $f_0 = 60.0\text{ Hz}$ con un factor de calidad $Q = 30.0$ enfocado en neutralizar la inducción de las redes eléctricas locales.**
- **Filtro Clínico (Pasa-Banda): Filtro Butterworth de 3er orden con frecuencias de corte entre $0.5\text{ Hz}$ y $40\text{ Hz}$. Elimina el baseline wander (causado por la respiración de baja frecuencia) y los potenciales de acción musculares (alta frecuencia).**
- **Filtro Adaptativo de Suavizado (Savitzky-Golay): Configurado con una ventana de longitud fija y un polinomio de 3er orden para suavizar las transiciones de la señal respetando la amplitud real de los picos R.**
### Módulo 2: Motor de Simulación y Quiz (quiz.html)
Este componente desacopla la evaluación clínica del monitor principal para evitar sobrecargas visuales.
- **Consume un set de datos JSON preconfigurado con 15 registros de control procedentes de la base de datos PTB-XL.**
- **Almacena las opciones de respuesta y las asocia a una matriz de Retroalimentación Fisiopatológica. Si el estudiante selecciona una conducta errónea, la UI renderiza un cuadro de diálogo dinámico que contrasta la respuesta del estudiante con medidas métricas específicas (longitud del intervalo PR, deflexiones del segmento ST, presencia de ondas fibrilatorias).**
### Módulo 3: Asistente Cognitivo (Monitor-Bot)
Integración mediante el SDK oficial de Google (google-generativeai) utilizando el modelo Gemini 1.5 Flash.
- **Estrategia de Prompt Engineering (Inyección de Contexto Dinámico): Cada mensaje enviado por el usuario es interceptado en el backend y envuelto dentro de una instrucción de sistema invariable:**
Plaintext
[SYSTEM INSTRUCTION]: Eres un tutor clínico especializado de soporte para Yuluka-EKG. 
El estudiante está analizando actualmente el registro de PTB-XL con ID: {id_actual}.
El diagnóstico clínico real es: {diagnostico_paciente}.
REGLA STRICTA: No entregues el diagnóstico de forma directa. Si el estudiante tiene dudas, 
guíalo analizando la morfología de la señal en pantalla (ej. intervalos PR, amplitud de la onda T).
- **Seguridad de Consumo: Para mitigar el agotamiento de cuotas gratuitas, el servidor valida los tokens de sesión activos y puede restringir el número máximo de consultas permitidas por usuario en las tablas relacionales.**


---

## 5. strategia de Despliegue y Configuración del Entorno (Fase de Pruebas)
Para ejecutar pruebas remotas con usuarios reales (compañeros de la facultad y docentes de control) sin incurrir en costos de alojamiento en la nube, el entorno se despliega utilizando una arquitectura de Túnel Seguro Inverso (Tunneling).
---

## 6. Tecnologías y Herramientas

| Componente | Tecnología |
|---------|-----------|
| Lenguaje principal | Python |
| Backend | Flask |
| Procesamiento de señales | NumPy, SciPy |
| Bioseñales | BioSPPy, NeuroKit2 |
| Frontend | HTML, CSS, JavaScript |
| Visualización | Plotly.js |
| Dataset | PTB-XL – PhysioNet |

---

## 7. Consideraciones Técnicas

- **Rendimiento:** Optimizado para uso educativO.
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
> Yuluka‑EKG es una plataforma con fines **educativos y de investigación**.  
> Los resultados generados **no deben utilizarse para diagnóstico ni decisiones clínicas reales**.  
> Los autores y colaboradores no se responsabilizan por el uso indebido del sistema.

---

## 10. Conclusión del Diseño Técnico

El diseño técnico de Yuluka‑EKG define una plataforma modular, accesible y técnicamente sólida que integra procesamiento de señales EKG y visualización interactiva bajo una arquitectura web moderna. Su enfoque educativo la posiciona como una herramienta eficaz para el aprendizaje del análisis de bioseñales en el área de la salud y la ingeniería biomédica.

---

