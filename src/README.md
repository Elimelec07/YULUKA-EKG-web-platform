# ECG Atlas — Monitor Clínico & Módulo de Evaluación
### Diplomado en Cuidado Crítico · Universidad del Magdalena

Plataforma web educativa para el estudio de electrocardiografía clínica. Integra señales reales de la base de datos PTB-XL (PhysioNet), procesamiento digital de señales, un asistente IA y un sistema de evaluación con historial de progreso.

---

## Tabla de Contenidos

1. [Estructura del Proyecto](#estructura-del-proyecto)
2. [Instalación y Arranque](#instalación-y-arranque)
3. [Configuración de API Keys](#configuración-de-api-keys)
4. [Backend — `app.py`](#backend--apppy)
   - [Base de Datos y Autenticación](#base-de-datos-y-autenticación)
   - [Módulo PTB-XL](#módulo-ptb-xl)
   - [Módulo DSP — Filtros Clínicos](#módulo-dsp--filtros-clínicos)
   - [Rutas de la API REST](#rutas-de-la-api-rest)
   - [Monitor-Bot (IA)](#monitor-bot-ia)
   - [Sistema de Quiz](#sistema-de-quiz)
   - [Historial y Metacognición](#historial-y-metacognición)
5. [Frontend Monitor — `main.js`](#frontend-monitor--mainjs)
6. [Frontend Quiz — `quiz.js`](#frontend-quiz--quizjs)
7. [Páginas y Templates](#páginas-y-templates)
8. [Base de Datos SQLite](#base-de-datos-sqlite)
9. [Referencia Rápida de Endpoints](#referencia-rápida-de-endpoints)

---

## Estructura del Proyecto

```
ProjectMain/
├── app.py                    ← Servidor Flask (toda la lógica backend)
├── ecg_atlas.db              ← Base de datos SQLite (auto-creada)
├── ptbxl_database.csv        ← Metadatos PTB-XL (auto-descargada)
├── templates/
│   ├── index.html            ← Monitor clínico principal
│   ├── quiz.html             ← Módulo de evaluación
│   ├── login.html            ← Inicio de sesión / registro
│   └── perfil.html           ← Dashboard de progreso
├── static/
│   ├── js/
│   │   ├── main.js           ← Lógica del monitor (gráficas, DSP, chat, zoom)
│   │   └── quiz.js           ← Lógica del quiz (casos, preguntas, modal)
│   └── css/
│       ├── style.css         ← Estilos del monitor principal
│       ├── quiz.css          ← Estilos del módulo de quiz
│       ├── login.css         ← Estilos de la pantalla de login
│       └── perfil.css        ← Estilos del dashboard de progreso
└── img/
    └── Unimagdalena.png      ← Logo institucional
```

---

## Instalación y Arranque

### Requisitos previos
- Python 3.10+
- Entorno virtual `.venv` creado en la raíz del proyecto

### Pasos

```powershell
# 1. Activar entorno virtual
.venv\Scripts\Activate.ps1

# 2. Instalar dependencias (solo la primera vez)
pip install flask flask-sqlalchemy flask-login werkzeug
pip install numpy pandas wfdb scipy deep-translator
pip install google-generativeai

# 3. Iniciar el servidor
python app.py
```

El servidor arranca en `http://127.0.0.1:5000`.

Al primer arranque, `ptbxl_database.csv` se descarga automáticamente desde PhysioNet (~16 MB). La base de datos `ecg_atlas.db` se crea automáticamente.

---

## Configuración de API Keys

### Gemini (Monitor-Bot IA)

En `app.py`, línea 24:

```python
# Opción A — Variable de entorno (recomendado para producción)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# Opción B — Hardcodeada (desarrollo local)
GEMINI_API_KEY = 'AIza...'   # ← pegar tu clave aquí
```

Para obtener una clave: [Google AI Studio](https://aistudio.google.com/app/apikey)

> Si `GEMINI_API_KEY` está vacío, el monitor funciona completamente pero Monitor-Bot devuelve un error informativo. El resto de la plataforma no se ve afectado.

---

## Backend — `app.py`

---

### Base de Datos y Autenticación

#### Modelos de SQLAlchemy

**`Usuario`** — tabla `usuarios`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | Integer PK | Identificador único |
| `nombre` | String(100) | Nombre completo del estudiante |
| `correo` | String(150) UNIQUE | Correo electrónico (login) |
| `password_hash` | String(256) | Hash bcrypt de la contraseña |
| `fecha_registro` | DateTime | Fecha de alta automática |
| `resultados` | Relación | Lista de `ResultadoQuiz` del usuario |

**`ResultadoQuiz`** — tabla `resultados_quiz`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | Integer PK | Identificador único |
| `user_id` | FK → usuarios | Usuario que respondió |
| `caso_id` | String(50) | Ej: `'caso_imi'`, `'caso_afib'` |
| `pregunta_id` | String(50) | `'dx'` (diagnóstico) o `'conducta'` |
| `categoria` | String(50) | `'Isquemia'`, `'Arritmias'`, `'Conducción'` |
| `es_correcto` | Boolean | Si la respuesta fue correcta |
| `fecha` | DateTime | Marca de tiempo automática |

#### `_cargar_usuario(uid)` — `@login_manager.user_loader`
Carga un usuario por ID entero desde la sesión de Flask-Login. Llamado automáticamente en cada request autenticado.

---

### Módulo PTB-XL

#### `_descargar_csv()`
Descarga `ptbxl_database.csv` desde PhysioNet si no existe localmente. Se llama automáticamente al arrancar el servidor.

#### `_max_confianza_scp(scp_str) → float`
Parsea la columna `scp_codes` (string JSON) y devuelve la confianza máxima entre todos los códigos.

```python
_max_confianza_scp("{'NORM': 100.0, 'SR': 0.0}")  # → 100.0
```

#### `_categoria_scp(codigo) → str`
Clasifica un código SCP en:
- `'peligro'` — IAM, AFIB, AFLT, BAV 3°, STEMI, etc.
- `'alerta'` — Bradicardia, BRIHH, BRDHH, LVH, QT largo, etc.
- `'normal'` — NORM, SR
- `'info'` — Todo lo demás

Usado para colorear los badges de diagnóstico en la ficha clínica.

#### `traducir_informe(texto) → str`
Traduce el informe clínico del alemán/inglés al español usando Google Translator. Implementa caché en memoria (`_cache_traducciones`): cada texto único se traduce solo una vez por sesión de servidor. Si la traducción falla, devuelve el texto original como fallback.

#### `_valor(fila, col) → valor | None`
Extrae un valor del DataFrame evitando NaN. Devuelve `None` si el valor es NaN o ausente.

#### `_tiene_artefacto(fila, col) → bool`
Devuelve `True` si la columna de calidad tiene contenido (indica presencia de artefacto en la señal).

#### `buscar_metadatos(filename_hr) → dict | None`
Función principal de consulta de paciente. Recibe el path del archivo (ej: `'records500/18000/18291_hr'`) y devuelve un diccionario completo:

```python
{
    'ecg_id':          18291,
    'patient_id':      14053,
    'edad':            68,
    'sexo':            'Femenino',
    'talla_cm':        165.0,
    'peso_kg':         75.0,
    'imc':             27.5,
    'fecha_registro':  '1984-11-14',
    'informe':         'Texto traducido al español...',
    'scp_codigos':     [{'codigo': 'IMI', 'nombre': 'Infarto Inferior',
                         'confianza': 100.0, 'categoria': 'peligro'}],
    'eje_cardiaco':    None,
    'estadio_infarto': None,
    'marcapaso':       False,
    'calidad': {
        'ruido_basal': False,
        'ruido_estatico': False,
        'ruido_burst': False,
        'problema_electrodos': False,
    }
}
```

Devuelve `None` si el `filename_hr` no está en el índice.

---

### Módulo DSP — Filtros Clínicos

#### `_aplicar_filtro(senal_np, fs, modo) → list[float]`

Procesa una señal ECG numpy según el modo seleccionado:

| Modo | Procesamiento | Propósito pedagógico |
|---|---|---|
| `'cruda'` | Añade ruido 60 Hz (0.18 mV) + deriva basal 0.2 Hz (0.30 mV) | Muestra cómo se ve la señal sin procesar del electrodo |
| `'con_notch'` | Mismo ruido + filtro notch IIR Q=30 a 60 Hz (filtfilt) | Muestra eliminación de interferencia eléctrica, queda deriva basal |
| `'filtrada_total'` | Butterworth 4° orden pasa-banda 0.5–40 Hz (filtfilt) | Señal lista para diagnóstico clínico estándar |

**Parámetros:**
- `senal_np` — array numpy 1D de la señal en mV
- `fs` — frecuencia de muestreo en Hz (típicamente 500 Hz en PTB-XL)
- `modo` — uno de los tres strings anteriores

**Retorna:** lista Python de floats (serializable a JSON)

---

### Rutas de la API REST

#### `GET /`
Renderiza la página principal del monitor clínico (`index.html`).

#### `GET /api/ecg/ptb-xl/<path:paciente_id>`
Obtiene las 12 derivaciones de un paciente específico.

**Parámetros de URL:**
- `paciente_id` — path del archivo, ej: `records500/18000/18291_hr`

**Query params:**
- `filtro` — `'cruda'` | `'con_notch'` | `'filtrada_total'` (default: `'filtrada_total'`)

**Respuesta exitosa:**
```json
{
    "estado": "exito",
    "paciente": "records500/18000/18291_hr",
    "frecuencia_muestreo": 500,
    "datos_12_derivaciones": {
        "I": [0.12, 0.15, ...],
        "II": [...],
        "III": [...],
        "aVR": [...],
        "aVL": [...],
        "aVF": [...],
        "V1": [...],
        "V2": [...],
        "V3": [...],
        "V4": [...],
        "V5": [...],
        "V6": [...]
    },
    "metadatos": { ... },
    "filtro_activo": "filtrada_total"
}
```

Cada derivación contiene 1500 muestras (3 segundos a 500 Hz).

#### `GET /api/ecg/random`
Igual a la ruta anterior pero selecciona un paciente aleatorio del pool precalculado. El pool filtra pacientes validados por cardiólogo, sin artefactos, con datos demográficos completos y confianza SCP ≥ 80%.

**Query params:**
- `filtro` — mismo que la ruta fija

#### `GET /quiz`
Renderiza la página del módulo de evaluación (`quiz.html`).

#### `GET /api/quiz/random`
Devuelve un caso clínico aleatorio con señal ECG y preguntas mezcladas.

**Respuesta:**
```json
{
    "estado": "exito",
    "caso_id": "caso_imi",
    "caso": {
        "titulo": "Urgencias — Dolor Torácico con Irradiación",
        "sexo": "Femenino",
        "edad": 68,
        "motivo": "...",
        "signos_vitales": [["TA","88/58 mmHg"], ...],
        "antecedentes": "...",
        "pistas_ecg": "..."
    },
    "preguntas": [
        {
            "id": "dx",
            "numero": 1,
            "icono": "🔍",
            "enunciado": "¿Cuál es el diagnóstico...?",
            "opciones": [
                {"id": "b", "texto": "...", "correcta": false},
                {"id": "a", "texto": "...", "correcta": true},
                ...
            ],
            "derivaciones_clave": ["II","III","aVF"],
            "color_clave": "#dc2626",
            "retro_ok": "Retroalimentación si es correcto...",
            "retro_mal": "Retroalimentación si es incorrecto..."
        }
    ],
    "frecuencia_muestreo": 500,
    "datos_12_derivaciones": { ... }
}
```

> Las opciones están mezcladas aleatoriamente usando `random.shuffle()`. La respuesta correcta no siempre es la primera.

#### `POST /api/chat`
Endpoint del asistente IA Monitor-Bot. Requiere la clave Gemini configurada.

**Body JSON:**
```json
{
    "mensaje": "¿Qué está pasando en la derivación V2?",
    "paciente_id": "records500/18000/18291_hr",
    "historial": [
        {"rol": "user", "texto": "mensaje anterior"},
        {"rol": "model", "texto": "respuesta anterior"}
    ],
    "contexto_visual": {
        "cara_seleccionada": "inferior",
        "caras_auto_resaltadas": ["inferior"],
        "lead_zoom": "V2"
    }
}
```

**Respuesta:**
```json
{ "respuesta": "Texto de respuesta del modelo..." }
```

El modelo opera en tres modos automáticos:
- **Explicación** — cuando el estudiante pregunta por una derivación específica
- **Socrático** — cuando pregunta por el diagnóstico (nunca lo revela directamente)
- **Confirmación** — cuando el estudiante acierta el diagnóstico

---

### Monitor-Bot (IA)

#### `_construir_contexto_paciente(meta) → str`
Formatea los metadatos del paciente en texto estructurado para el prompt de sistema del LLM. Incluye sexo, edad, antropometría, diagnóstico SCP con confianza, informe clínico (primeros 500 caracteres), eje cardíaco, estadio de infarto y presencia de marcapaso.

#### `_mapa_leads(scp_lista) → str`
Genera el mapa de derivaciones esperadas para el LLM. Para cada código SCP del diagnóstico (máx. 3), enumera qué hallazgo debería mostrar cada grupo de derivaciones según `_HALLAZGOS_POR_SCP`. Cubre 15+ patrones: IMI, ASMI, AMI, AFIB, AFLT, CLBBB, LNGQT, SBRAD, STACH, NORM, LVH, WPW, 1AVB, etc.

#### `_estado_visual(ctx) → str`
Convierte el contexto visual del frontend en texto legible para el LLM:
- Cara seleccionada por clic del estudiante
- Territorios auto-resaltados por el diagnóstico
- Derivación abierta en zoom (si aplica)

---

### Sistema de Quiz

#### `_cargar_ecg(filename_hr) → (dict, float)`
Carga la señal ECG de un caso de quiz desde PhysioNet. Devuelve las 12 derivaciones (3 segundos, sin filtro de ruido simulado) y la frecuencia de muestreo.

#### Casos disponibles (`CASOS_QUIZ`)

| ID | Diagnóstico | Categoría | Archivo PTB-XL |
|---|---|---|---|
| `caso_imi` | IAMCEST Inferior (ACD) | Isquemia | `18291_hr` |
| `caso_asmi` | IAMCEST Anteroseptal (DAI) | Isquemia | `21040_hr` |
| `caso_afib` | Fibrilación Auricular paroxística | Arritmias | `14102_hr` |
| `caso_aflt` | Flutter Auricular 2:1 | Arritmias | `00858_hr` |
| `caso_clbbb` | Bloqueo Completo Rama Izquierda | Conducción | `18376_hr` |
| `caso_lngqt` | QT largo adquirido (amiodarona) | Conducción | `18186_hr` |
| `caso_sbrad` | Bradicardia Sinusal sintomática | Arritmias | `20393_hr` |
| `caso_stach` | Taquicardia Sinusal postoperatoria | Arritmias | `04408_hr` |

Cada caso tiene 2 preguntas: diagnóstico (`dx`) y conducta de enfermería (`conducta`).

---

### Historial y Metacognición

#### `_insight(cat, total, pct, incorrectas) → str (HTML)`
Genera un mensaje de retroalimentación metacognitiva para una categoría. Lógica:
- `total == 0` → invitación a comenzar
- `total < 3` → demasiado pocas muestras para retroalimentar
- `pct < 50` → indica repaso urgente
- `pct < 75` → progreso moderado, sugiere explicar en voz alta
- `pct ≥ 75` → dominio sólido

#### `_badges(stats, total) → list[dict]`
Calcula los badges desbloqueados:

| Badge | Condición |
|---|---|
| 🩺 Primer Paso | ≥ 1 pregunta respondida |
| 📚 Estudiante Aplicado | ≥ 10 preguntas |
| ⚡ Comprometido | ≥ 25 preguntas |
| 🔬 Investigador | ≥ 50 preguntas |
| ❤️/🔴/⚡ Experto en {Cat} | ≥ 4 preguntas en la categoría con ≥ 80% |
| 🏆 Clínico Redondo | Dominio ≥ 75% en las 3 categorías (con ≥ 4 preguntas c/u) |

#### Rutas de autenticación y progreso

| Ruta | Método | Descripción |
|---|---|---|
| `GET /login` | GET | Renderiza la página de login/registro |
| `POST /api/register` | POST | Registra un nuevo usuario (nombre, correo, password) |
| `POST /api/login` | POST | Inicia sesión con correo y contraseña |
| `GET /logout` | GET | Cierra la sesión y redirige a `/` |
| `GET /perfil` | GET | Renderiza el dashboard de progreso (requiere login) |
| `POST /api/guardar_resultado` | POST | Guarda una respuesta de quiz (silencioso si no autenticado) |
| `GET /api/progreso` | GET | Devuelve estadísticas completas del usuario (requiere login) |
| `POST /api/reiniciar_progreso` | POST | Borra todos los resultados del usuario (requiere login) |

**Body de `/api/guardar_resultado`:**
```json
{
    "caso_id": "caso_imi",
    "pregunta_id": "dx",
    "es_correcto": true
}
```

**Respuesta de `/api/progreso`:**
```json
{
    "nombre": "Juan Carlos Orozco",
    "total": 16,
    "total_ok": 12,
    "pct_global": 75,
    "stats": {
        "Arritmias":  {"total": 8, "correctas": 7, "incorrectas": 1, "pct": 87},
        "Isquemia":   {"total": 4, "correctas": 2, "incorrectas": 2, "pct": 50},
        "Conducción": {"total": 4, "correctas": 3, "incorrectas": 1, "pct": 75}
    },
    "categorias": ["Arritmias", "Isquemia", "Conducción"],
    "insights": ["Mensaje para Arritmias...", "Mensaje para Isquemia...", "..."],
    "badges": [
        {"icono": "🩺", "titulo": "Primer Paso", "desc": "Primera pregunta respondida"},
        ...
    ]
}
```

---

## Frontend Monitor — `main.js`

### Variables de estado globales

| Variable | Tipo | Descripción |
|---|---|---|
| `graficasActivas` | Object | Instancias activas de Chart.js por ID de canvas |
| `pacienteActual` | String | Path del paciente cargado actualmente |
| `filtroActual` | String | Modo DSP activo: `'cruda'` / `'con_notch'` / `'filtrada_total'` |
| `datosAlmacenados` | Object | Señales en mV por derivación, para el zoom |
| `fsGlobal` | Number | Frecuencia de muestreo actual (Hz) |
| `caraSeleccionada` | String / null | Cara seleccionada por clic en el mapa anatómico |
| `carasAutoResaltadas` | Set | Caras resaltadas automáticamente por el diagnóstico SCP |

### Funciones principales

#### `dibujarDerivacion(idCanvas, datos, fs)`
Renderiza una derivación ECG usando Chart.js con el plugin de papel milimetrado clínico (`pluginPapelECG`). Destruye la instancia anterior si existía.

- Estándar: 25 mm/s horizontal, 10 mm/mV vertical
- 75mm × 50mm de papel (3 segundos × 5 mV)
- Cuadrícula rosa con líneas mayores cada 5 mm (200 ms / 0.5 mV)

#### `poblarFichaClinica(meta)`
Rellena todos los elementos HTML de la ficha clínica del paciente con los metadatos recibidos del backend. También llama a `autoResaltarDesdeSCP()`.

#### `solicitarSenales()`
Llama a `GET /api/ecg/ptb-xl/{pacienteActual}?filtro={filtroActual}`, dibuja las 12 derivaciones y actualiza la ficha clínica. Detecta cambio de paciente para resetear el chat.

#### `solicitarAleatorio()`
Llama a `GET /api/ecg/random?filtro={filtroActual}`. Igual que `solicitarSenales()` pero para paciente aleatorio. Muestra el badge identificador del paciente.

#### `ocultarBadgeAleatorio()` / `mostrarBadgeAleatorio(filename_hr, metadatos)`
Controlan la visibilidad del badge que muestra el ID y diagnóstico del paciente aleatorio cargado.

---

### Módulo DSP

#### `inicializarDSP()`
Adjunta los listeners a los radio buttons de filtro DSP y aplica el modo inicial (`'filtrada_total'`). Llamada una vez en `window.onload`.

#### `_actualizarDSP(modo)`
Actualiza visualmente la interfaz cuando cambia el filtro:
1. Cambia la clase CSS del monitor (`monitor-cruda` / `monitor-notch` / `monitor-limpio`)
2. Actualiza el panel explicativo con ícono, título, descripción y consejo del modo
3. Marca la opción activa con `dsp-opcion-activa`

---

### Mapa Anatómico

#### `inicializarAnatomia()`
Adjunta eventos de clic, mouseenter y mouseleave a los sectores SVG del corazón y a los contenedores de derivaciones. Llamada una vez en `window.onload`.

#### `toggleResaltadoCara(cara)`
Activa o desactiva la selección de una cara cardíaca. Si ya estaba seleccionada, la deselecciona y restaura el auto-resaltado. Si es nueva, resalta las derivaciones correspondientes.

#### `resaltarLeadsDeCara(cara)`
Aplica la clase `lead-resaltado` y las variables CSS `--color-cara` / `--shadow-cara` a los contenedores de las derivaciones que pertenecen a la cara seleccionada.

#### `limpiarResaltadoLeads()`
Elimina el resaltado de todas las derivaciones.

#### `mostrarInfoCara(cara)` / `ocultarInfoCara()`
Muestran/ocultan el panel lateral de información de la cara seleccionada: nombre, derivaciones, arteria coronaria, descripción y signos ECG esperados.

#### `autoResaltarDesdeSCP(scp_codigos)`
Al cargar un paciente, resalta automáticamente los territorios afectados según los códigos SCP del diagnóstico (usando `SCP_A_CARAS_MAP`). Solo actúa si la confianza del código es ≥ 50%.

---

### Módulo Zoom de Precisión

#### `inicializarModalZoom()`
Adjunta todos los eventos del modal de zoom (una vez en `window.onload`):
- Botones cerrar, zoom +/-, reset, medir
- Scroll del mouse (zoom centrado en cursor)
- Arrastre para pan
- Clic para puntos de medición
- Pinch-to-zoom táctil
- Atajos de teclado: `Esc`, `+/-`, flechas, `M`

#### `abrirModalZoom(label, datos, fs)`
Abre el modal de zoom para una derivación específica. Inicializa la vista al papel completo (75×50 mm).

#### `aplicarZoom(factor, cxMm, cyMm)`
Aplica un factor de zoom manteniendo el punto `(cxMm, cyMm)` fijo en pantalla. Limita el zoom entre 1× (papel completo, 75 mm) y 37.5× (ventana de 2 mm).

#### `renderZoom()`
Redibuja el canvas del modal con:
- Fondo de papel térmico
- Cuadrícula milimetrada con etiquetas de tiempo (mm / s) y voltaje (mV)
- Línea isoeléctrica punteada en 0 mV
- Señal ECG con grosor proporcional al zoom
- Crosshair del cursor con coordenadas en tiempo y voltaje
- Puntos de medición (verde = punto 1, rojo = punto 2) con línea y caja de resultado (Δt, ΔV, distancia)

#### `canvasAMm(canvasX, canvasY) → {x, y}`
Convierte coordenadas de píxeles del canvas a milímetros del papel ECG considerando la ventana de vista actual.

#### `mmAPx(mmX, mmY) → {x, y}`
Conversión inversa: mm del papel → píxeles del canvas.

#### `rrect(ctx, x, y, w, h, r)`
Dibuja un rectángulo redondeado compatible con navegadores que no soportan `ctx.roundRect`.

---

### Monitor-Bot (Chat)

#### `inicializarChat()`
Adjunta eventos al botón toggle, botón cerrar, botón enviar e input (Enter para enviar). Muestra el mensaje de bienvenida inicial. Llamada una vez en `window.onload`.

#### `_toggleChat(abrir)`
Muestra u oculta el panel de chat. Al abrir, hace scroll al final del historial.

#### `limpiarChatContexto()`
Limpia el historial de conversación y el DOM del chat cuando se carga un nuevo paciente. Muestra un mensaje informando el cambio de contexto.

#### `_agregarBurbuja(tipo, html)`
Agrega un mensaje al chat. `tipo` puede ser `'user'` o `'bot'`. Acepta HTML para el contenido del bot.

#### `enviarMensajeChat()` — `async`
Función principal de envío:
1. Desactiva el input y muestra el indicador de escritura (tres puntos animados)
2. Llama a `POST /api/chat` con el mensaje, el `paciente_id` actual, el historial (máx. últimos 40 mensajes) y el contexto visual actual
3. Agrega la respuesta al historial y al DOM
4. Limita el historial a 20 intercambios (40 entradas) para controlar el contexto

#### `_escaparHtml(str) → str`
Escapa los caracteres `&`, `<`, `>` en el input del usuario antes de mostrarlo, para prevenir XSS.

---

## Frontend Quiz — `quiz.js`

### Variables de estado

| Variable | Tipo | Descripción |
|---|---|---|
| `casoActual` | Object | Datos del caso activo (respuesta completa de la API) |
| `correctas` | Number | Contador global de respuestas correctas |
| `totalRespondidas` | Number | Contador global de preguntas respondidas |
| `respuestasDadas` | Object | `{preguntaId: opcionId}` por caso actual |
| `preguntasOrden` | Array | IDs de preguntas en orden para navegación |
| `casosVistosHoy` | Number | Contador de casos en la sesión actual |
| `_modalCallback` | Function / null | Acción a ejecutar al cerrar el modal de retroalimentación |

### Funciones principales

#### `cargarCaso()`
Función principal de carga. Llama a `GET /api/quiz/random`, renderiza el caso completo y resetea el estado. Maneja estados de carga, error y contenido.

#### `mostrarEstado(estado)`
Alterna la visibilidad entre `'cargando'`, `'error'` y `'contenido'`.

#### `renderCaso(data)`
Rellena la tarjeta de historia clínica: número de caso, título, datos del paciente, motivo de consulta, signos vitales (con alertas visuales para valores anormales), antecedentes y pistas ECG.

#### `renderMonitor(senales, fs)`
Genera la cuadrícula de 12 derivaciones en layout 4×3 (columnas: I/II/III, aVR/aVL/aVF, V1/V2/V3, V4/V5/V6) con canvas individuales.

#### `renderPreguntas(preguntas)`
Genera el HTML de las preguntas con sus opciones. La primera pregunta está habilitada; las siguientes quedan bloqueadas hasta responder la anterior. Adjunta el listener de clic a cada opción.

#### `resaltarDerivaciones(pregunta)`
Aplica un borde de color a las derivaciones clave de la pregunta (definidas en `derivaciones_clave` con su `color_clave`). Ejecutado al abrir el modal de retroalimentación.

#### `responder(preguntaId, opcionSeleccionada, esCorrecta, pregunta)`
Manejador de respuesta:
1. Registra la respuesta en `respuestasDadas` y actualiza contadores
2. Deshabilita todas las opciones de la pregunta
3. Llama en background (fire-and-forget) a `POST /api/guardar_resultado` si el usuario está autenticado
4. Espera 320 ms y luego abre el modal de retroalimentación

#### `inicializarModalRetro()`
Adjunta los eventos del modal de retroalimentación: botón "Continuar" y tecla `Escape`. Ejecuta `_modalCallback` al cerrar.

#### `abrirModalRetro(pregunta, esCorrecta)`
Muestra el modal pedagógico:
- **Header**: color verde (`retro-ok`) o naranja (`retro-mal`) con ícono y título
- **Texto**: retroalimentación clínica específica (`retro_ok` o `retro_mal` del caso)
- **Guía pedagógica**: tarjeta amarilla con `patron`, `hallazgo`, `medida` y `fisio` de `GUIA_PEDAGOGICA`
- **Chips de derivaciones**: siempre visibles (incluso en respuesta incorrecta) con color semántico (rojo = cara inferior, azul = septal, etc.)
- Hace scroll al monitor ECG con 250 ms de delay

#### `_cerrarModal()`
Oculta el modal y ejecuta `_modalCallback` si existe (para habilitar la siguiente pregunta o mostrar navegación).

#### `actualizarPuntaje()`
Actualiza el contador de aciertos en el encabezado del quiz (`puntaje-correctas` / `puntaje-total`).

### Diccionario `GUIA_PEDAGOGICA`

Contiene entradas para cada caso × pregunta con 4 campos:

| Campo | Descripción |
|---|---|
| `patron` | Nombre del patrón ECG |
| `hallazgo` | Hallazgo principal a buscar en el trazo |
| `medida` | Valores de referencia / umbrales clínicos |
| `fisio` | Fisiopatología en 1–2 oraciones |

Claves: `caso_imi_dx`, `caso_imi_conducta`, `caso_asmi_dx`, `caso_asmi_conducta`, ... (16 entradas en total).

---

## Páginas y Templates

| Template | URL | Descripción |
|---|---|---|
| `index.html` | `/` | Monitor clínico con 12 derivaciones, ficha clínica, mapa anatómico, módulo DSP, chat Monitor-Bot |
| `quiz.html` | `/quiz` | Casos clínicos, monitor 12D, preguntas con opciones, modal de retroalimentación |
| `login.html` | `/login` | Dos pestañas: Iniciar Sesión y Registrarse. Redirecciona a `/perfil` tras login exitoso |
| `perfil.html` | `/perfil` | Gráfico de radar (Chart.js), barras de progreso por categoría, insights metacognitivos, badges, botón reset |

---

## Base de Datos SQLite

### Inspección manual

```python
# Ejecutar desde la raíz del proyecto con Python
import sqlite3
conn = sqlite3.connect('ecg_atlas.db')
cur  = conn.cursor()

# Ver todos los usuarios registrados
cur.execute("SELECT id, nombre, correo, fecha_registro FROM usuarios")
for fila in cur.fetchall():
    print(fila)

# Ver resultados de un usuario
cur.execute("""
    SELECT caso_id, pregunta_id, categoria, es_correcto, fecha
    FROM resultados_quiz
    WHERE user_id = 1
    ORDER BY fecha DESC
""")
for fila in cur.fetchall():
    print(fila)

conn.close()
```

### Eliminar un usuario

```python
cur.execute("DELETE FROM usuarios WHERE correo = 'ejemplo@correo.com'")
conn.commit()
# Los resultados se eliminan en cascada automáticamente
```

---

## Referencia Rápida de Endpoints

| Método | URL | Auth | Descripción |
|---|---|---|---|
| GET | `/` | No | Monitor clínico |
| GET | `/quiz` | No | Módulo de evaluación |
| GET | `/login` | No | Login / Registro |
| GET | `/logout` | No | Cerrar sesión |
| GET | `/perfil` | Sí | Dashboard de progreso |
| GET | `/api/ecg/ptb-xl/<id>` | No | ECG de paciente específico |
| GET | `/api/ecg/random` | No | ECG de paciente aleatorio |
| GET | `/api/quiz/random` | No | Caso clínico aleatorio |
| POST | `/api/chat` | No* | Monitor-Bot IA |
| POST | `/api/register` | No | Registrar usuario nuevo |
| POST | `/api/login` | No | Iniciar sesión |
| GET | `/api/progreso` | Sí | Estadísticas del usuario |
| POST | `/api/guardar_resultado` | Sí* | Guardar respuesta del quiz |
| POST | `/api/reiniciar_progreso` | Sí | Borrar historial del usuario |

> *`/api/chat` no requiere autenticación pero sí la clave Gemini configurada.
> *`/api/guardar_resultado` devuelve 401 silencioso si no hay sesión activa (el quiz funciona igual sin login).

---

*Documento generado para el proyecto ECG Atlas — Diplomado en Cuidado Crítico, Universidad del Magdalena.*
