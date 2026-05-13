import os
import ast
import copy
import random
import urllib.request
from datetime import datetime
import numpy as np
import pandas as pd
import wfdb
from scipy import signal as sp_signal
from deep_translator import GoogleTranslator
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user,
                         logout_user, login_required, current_user)

try:
    import google.generativeai as genai
    _GEMINI_OK = True
except ImportError:
    _GEMINI_OK = False

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
if _GEMINI_OK and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)

# ================================================================
#  CONFIGURACIÓN DE BASE DE DATOS Y AUTENTICACIÓN
# ================================================================

_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yuluka_ekg.db')
app.config['SECRET_KEY']                     = os.environ.get('SECRET_KEY', 'yuluka-ekg-unimagdalena-2025')
app.config['SQLALCHEMY_DATABASE_URI']        = f'sqlite:///{_DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db            = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'pagina_login'

# ---- Modelos ----

class Usuario(UserMixin, db.Model):
    __tablename__  = 'usuarios'
    id             = db.Column(db.Integer, primary_key=True)
    nombre         = db.Column(db.String(100), nullable=False)
    correo         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash  = db.Column(db.String(256), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    resultados     = db.relationship('ResultadoQuiz', backref='usuario',
                                     lazy='dynamic', cascade='all, delete-orphan')

class ResultadoQuiz(db.Model):
    __tablename__ = 'resultados_quiz'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    caso_id     = db.Column(db.String(50), nullable=False)
    pregunta_id = db.Column(db.String(50), nullable=False)
    categoria   = db.Column(db.String(50), nullable=False)
    es_correcto = db.Column(db.Boolean, nullable=False)
    fecha       = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def _cargar_usuario(uid):
    return db.session.get(Usuario, int(uid))

with app.app_context():
    db.create_all()

# ================================================================
#  METADATOS PTB-XL — cargados una sola vez al iniciar el servidor
# ================================================================

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ptbxl_database.csv')

def _descargar_csv():
    url = 'https://physionet.org/files/ptb-xl/1.0.3/ptbxl_database.csv'
    print('[PTB-XL] Descargando ptbxl_database.csv desde PhysioNet...')
    urllib.request.urlretrieve(url, CSV_PATH)
    print(f'[PTB-XL] CSV guardado en {CSV_PATH}')

if not os.path.exists(CSV_PATH):
    _descargar_csv()

# Indexado por filename_hr → O(1) en cada consulta
_df = pd.read_csv(CSV_PATH, index_col='filename_hr')
print(f'[PTB-XL] Base de datos cargada: {len(_df)} registros.')

# Mapa de códigos SCP → español
_SCP_ES = {
    'NORM': 'Ritmo Normal',        'SR': 'Ritmo Sinusal',
    'SBRAD': 'Bradicardia Sinusal', 'STACH': 'Taquicardia Sinusal',
    'SARRH': 'Arritmia Sinusal',   'AFIB': 'Fibrilación Auricular',
    'AFLT': 'Flutter Auricular',   'PSVT': 'Taquicardia Parox. SV',
    'WPW': 'Wolf-Parkinson-White', 'BIGU': 'Bigeminismo',
    'TRIGU': 'Trigeminismo',       'SVT': 'Taquicardia SV',
    'MI': 'Infarto de Miocardio',  'IMI': 'Infarto Inferior',
    'ASMI': 'Infarto Anteroseptal','AMI': 'Infarto Anterior',
    'LMI': 'Infarto Lateral',      'PMI': 'Infarto Posterior',
    'ALMI': 'Infarto Anterolateral','ILMI': 'Infarto Inferolateral',
    'IPLMI': 'Infarto Infero-Post-Lat.','IPMI': 'Infarto Infero-Post.',
    'SEHYP': 'Hipertrofia Septal', 'LVH': 'Hipertrofia Vent. Izq.',
    'RVH': 'Hipertrofia Vent. Der.','LAO/LAE': 'Agrandamiento AI',
    'RAO/RAE': 'Agrandamiento AD', 'LBBB': 'Bloqueo Rama Izquierda',
    'RBBB': 'Bloqueo Rama Derecha','IRBBB': 'BRDHH Incompleto',
    'LAFB/LAHB': 'Bloqueo Fasc. Ant.','LPFB': 'Bloqueo Fasc. Post.',
    '1AVB': 'BAV 1er Grado',       '2AVB': 'BAV 2do Grado',
    '3AVB': 'BAV 3er Grado',       'IVCD': 'Defecto Cond. Intrav.',
    'STTC': 'Alteración ST-T',     'NST_': 'Cambio ST Inespecífico',
    'ISC_': 'Isquemia Inespecífica','ISCA': 'Isquemia Anterior',
    'ISCI': 'Isquemia Inferior',   'ISCAL': 'Isquemia Anterolateral',
    'ISCIL': 'Isquemia Inferolateral','ISCIN': 'Isquemia Ínfero-Ant.',
    'STD_': 'Descenso de ST',      'STE_': 'Elevación de ST',
    'STEMI': 'Elevación ST (IAMCEST)','LVOLT': 'Bajo Voltaje QRS',
    'HVOLT': 'Alto Voltaje',       'LAD': 'Eje Desviado Izquierda',
    'RAD': 'Eje Desviado Derecha', 'QWAVE': 'Onda Q Patológica',
    'VCLVH': 'Criterios Voltaje HVI','LNGQT': 'QT Prolongado',
    'DIG': 'Efecto Digitálicos',   'EL': 'Trastorno Electrolítico',
    'ANEUR': 'Aneurisma',          'PRC(S)': 'Marcapaso',
}

# Categoría clínica por severidad
_SCP_CAT = {
    'peligro': {'MI','IMI','ASMI','AMI','LMI','PMI','ALMI','ILMI',
                'IPLMI','IPMI','STEMI','AFIB','AFLT','3AVB','STE_'},
    'alerta':  {'SBRAD','STACH','LBBB','RBBB','IRBBB','LAFB/LAHB',
                'LPFB','1AVB','2AVB','LVH','RVH','STTC','LNGQT',
                'WPW','STD_','ISCA','ISCI','ISCAL','ISCIL'},
    'normal':  {'NORM','SR'},
}

def _categoria_scp(codigo):
    for cat, codigos in _SCP_CAT.items():
        if codigo in codigos:
            return cat
    return 'info'

# ================================================================
#  TRADUCTOR DE INFORMES CLÍNICOS (DE/EN → ES)
#  Caché en memoria: cada informe único se traduce solo una vez
#  por sesión de servidor.
# ================================================================

_cache_traducciones: dict[str, str] = {}

def traducir_informe(texto: str) -> str:
    if not texto:
        return texto
    if texto in _cache_traducciones:
        return _cache_traducciones[texto]
    try:
        traduccion = GoogleTranslator(source='auto', target='es').translate(texto)
        _cache_traducciones[texto] = traduccion or texto
    except Exception:
        _cache_traducciones[texto] = texto   # fallback: devolver original
    return _cache_traducciones[texto]


def _valor(fila, col):
    v = fila.get(col)
    return None if (v is None or (isinstance(v, float) and np.isnan(v))) else v

def _tiene_artefacto(fila, col):
    v = _valor(fila, col)
    return bool(v and str(v).strip())

def buscar_metadatos(filename_hr):
    if filename_hr not in _df.index:
        return None
    fila = _df.loc[filename_hr]

    # SCP codes
    try:
        scp_raw = ast.literal_eval(str(fila.get('scp_codes', '{}')))
        scp_lista = sorted(
            [{'codigo': k,
              'nombre': _SCP_ES.get(k, k),
              'confianza': round(float(v), 1),
              'categoria': _categoria_scp(k)}
             for k, v in scp_raw.items()
             if isinstance(v, (int, float)) and v > 0],
            key=lambda x: x['confianza'], reverse=True
        )
    except Exception:
        scp_lista = []

    age    = _valor(fila, 'age')
    weight = _valor(fila, 'weight')
    height = _valor(fila, 'height')
    sex    = _valor(fila, 'sex')

    imc = None
    if weight and height and float(height) > 0:
        imc = round(float(weight) / ((float(height) / 100) ** 2), 1)

    estadio = _valor(fila, 'infarction_stadium1') or _valor(fila, 'infarction_stadium2')

    return {
        'ecg_id':        int(_valor(fila, 'ecg_id') or 0),
        'patient_id':    int(float(_valor(fila, 'patient_id') or 0)),
        'edad':          int(float(age)) if age is not None else None,
        'sexo':          ('Femenino' if int(sex) == 1 else 'Masculino') if sex is not None else None,
        'talla_cm':      float(height) if height is not None else None,
        'peso_kg':       float(weight) if weight is not None else None,
        'imc':           imc,
        'fecha_registro': str(_valor(fila, 'recording_date') or '')[:10] or None,
        'informe':       traducir_informe(str(_valor(fila, 'report') or '').strip()) or None,
        'scp_codigos':   scp_lista,
        'eje_cardiaco':  _valor(fila, 'heart_axis') or None,
        'estadio_infarto': str(estadio).strip() if estadio else None,
        'marcapaso':     bool(_valor(fila, 'pacemaker')),
        'calidad': {
            'ruido_basal':        _tiene_artefacto(fila, 'baseline_drift'),
            'ruido_estatico':     _tiene_artefacto(fila, 'static_noise'),
            'ruido_burst':        _tiene_artefacto(fila, 'burst_noise'),
            'problema_electrodos':_tiene_artefacto(fila, 'electrodes_problems'),
        }
    }


# ================================================================
#  POOL DE PACIENTES ALEATORIOS — precalculado al arrancar
#  Criterios idénticos a los sujetos fijos:
#    · validado por cardiólogo humano
#    · sin artefactos (baseline drift, static/burst noise, electrodos)
#    · edad válida (< 120), peso y talla registrados
#    · confianza máxima en al menos un código SCP >= 80 %
# ================================================================

def _max_confianza_scp(scp_str):
    try:
        d = ast.literal_eval(str(scp_str))
        vals = [v for v in d.values() if isinstance(v, (int, float))]
        return max(vals) if vals else 0
    except Exception:
        return 0

_df_pool = _df[
    (_df['validated_by_human'] == True) &
    (_df['baseline_drift'].isna()) &
    (_df['static_noise'].isna()) &
    (_df['burst_noise'].isna()) &
    (_df['electrodes_problems'].isna()) &
    (_df['age'].notna()) &
    (_df['age'] < 120) &
    (_df['weight'].notna()) &
    (_df['height'].notna()) &
    (_df['height'] > 100)
].copy()

_df_pool['_max_conf'] = _df_pool['scp_codes'].apply(_max_confianza_scp)
_df_pool = _df_pool[_df_pool['_max_conf'] >= 80]

# Lista de filename_hr elegibles (índice del dataframe)
_POOL_IDS = list(_df_pool.index)
print(f'[PTB-XL] Pool aleatorio: {len(_POOL_IDS)} sujetos calificados.')


# ================================================================
#  MÓDULO DSP EDUCATIVO — FILTROS CLÍNICOS
#  Tres estados: cruda | con_notch | filtrada_total
# ================================================================

def _aplicar_filtro(senal_np, fs, modo):
    t = np.linspace(0, len(senal_np) / fs, len(senal_np))

    if modo == 'cruda':
        # Añade interferencia de 60 Hz (red eléctrica) + deriva basal (respiración)
        # para mostrar la "realidad del electrodo" sin procesamiento
        ruido_60hz = 0.18 * np.sin(2 * np.pi * 60 * t)
        baseline   = 0.30 * np.sin(2 * np.pi * 0.20 * t)  # ~12 respiraciones/min
        return (senal_np + ruido_60hz + baseline).tolist()

    elif modo == 'con_notch':
        # Añade el mismo ruido y aplica solo el filtro notch de 60 Hz
        # El estudiante ve cómo desaparece la interferencia eléctrica
        # pero sigue la deriva basal (respiración)
        ruido_60hz = 0.18 * np.sin(2 * np.pi * 60 * t)
        baseline   = 0.30 * np.sin(2 * np.pi * 0.20 * t)
        senal_ruidosa = senal_np + ruido_60hz + baseline
        b, a = sp_signal.iirnotch(w0=60.0, Q=30.0, fs=fs)
        return sp_signal.filtfilt(b, a, senal_ruidosa).tolist()

    else:  # filtrada_total (modo diagnóstico)
        # Filtro pasa-banda Butterworth 4° orden, fase cero (filtfilt)
        # 0.5 Hz elimina deriva basal  |  40 Hz corta ruido muscular y eléctrico
        nyq = fs / 2.0
        b, a = sp_signal.butter(N=4, Wn=[0.5 / nyq, 40.0 / nyq], btype='bandpass')
        return sp_signal.filtfilt(b, a, senal_np).tolist()


# ================================================================
#  RUTAS
# ================================================================

@app.route('/img/<path:filename>')
def servir_imagen(filename):
    return send_from_directory('img', filename)


@app.route('/')
def inicio():
    return render_template('index.html')


@app.route('/api/ecg/ptb-xl/<path:paciente_id>')
def obtener_12_derivaciones(paciente_id):
    try:
        modo_filtro = request.args.get('filtro', 'filtrada_total')

        partes            = paciente_id.split('/')
        carpeta           = f"{partes[0]}/{partes[1]}"
        archivo           = partes[2]
        directorio_exacto = f'ptb-xl/1.0.3/{carpeta}'

        record = wfdb.rdrecord(archivo, pn_dir=directorio_exacto)

        fs                  = record.fs
        muestras_3_segundos = int(fs * 3)

        nombres_canales_db = [str(c).lower().strip() for c in record.sig_name]
        derivaciones       = {}
        canales_deseados   = ['I','II','III','aVR','aVL','aVF','V1','V2','V3','V4','V5','V6']

        for canal in canales_deseados:
            canal_min = canal.lower().strip()
            if canal_min in nombres_canales_db:
                idx         = nombres_canales_db.index(canal_min)
                senal_bruta = np.nan_to_num(record.p_signal[:muestras_3_segundos, idx])
                derivaciones[canal] = _aplicar_filtro(senal_bruta, fs, modo_filtro)
            else:
                derivaciones[canal] = [0] * muestras_3_segundos

        metadatos = buscar_metadatos(paciente_id)

        return jsonify({
            'estado':                'exito',
            'paciente':              paciente_id,
            'frecuencia_muestreo':   fs,
            'datos_12_derivaciones': derivaciones,
            'metadatos':             metadatos,
            'filtro_activo':         modo_filtro,
        })

    except Exception as e:
        return jsonify({'estado': 'error', 'mensaje': f'Error PhysioNet (PTB-XL): {str(e)}'})


@app.route('/api/ecg/random')
def obtener_aleatorio():
    if not _POOL_IDS:
        return jsonify({'estado': 'error', 'mensaje': 'Pool de pacientes vacío.'})
    paciente_id = random.choice(_POOL_IDS)
    modo_filtro = request.args.get('filtro', 'filtrada_total')

    partes            = paciente_id.split('/')
    carpeta           = f"{partes[0]}/{partes[1]}"
    archivo           = partes[2]
    directorio_exacto = f'ptb-xl/1.0.3/{carpeta}'

    try:
        record              = wfdb.rdrecord(archivo, pn_dir=directorio_exacto)
        fs                  = record.fs
        muestras_3_segundos = int(fs * 3)
        nombres_canales_db  = [str(c).lower().strip() for c in record.sig_name]
        derivaciones        = {}
        canales_deseados    = ['I','II','III','aVR','aVL','aVF','V1','V2','V3','V4','V5','V6']

        for canal in canales_deseados:
            canal_min = canal.lower().strip()
            if canal_min in nombres_canales_db:
                idx         = nombres_canales_db.index(canal_min)
                senal_bruta = np.nan_to_num(record.p_signal[:muestras_3_segundos, idx])
                derivaciones[canal] = _aplicar_filtro(senal_bruta, fs, modo_filtro)
            else:
                derivaciones[canal] = [0] * muestras_3_segundos

        return jsonify({
            'estado':                'exito',
            'paciente':              paciente_id,
            'frecuencia_muestreo':   fs,
            'datos_12_derivaciones': derivaciones,
            'metadatos':             buscar_metadatos(paciente_id),
            'filtro_activo':         modo_filtro,
        })

    except Exception as e:
        return jsonify({'estado': 'error', 'mensaje': f'Error PhysioNet (random): {str(e)}'})


# ================================================================
#  CASOS CLÍNICOS PARA EL MÓDULO DE EVALUACIÓN
#  Basados en protocolos de Enfermería en Cuidado Crítico
# ================================================================

CASOS_QUIZ = [
    {
        'id': 'caso_imi',
        'filename_hr': 'records500/18000/18291_hr',
        'caso': {
            'titulo': 'Urgencias — Dolor Torácico con Irradiación',
            'sexo': 'Femenino', 'edad': 68,
            'motivo': (
                'Paciente femenina de 68 años ingresa al servicio de urgencias. '
                'Refiere dolor torácico opresivo de 45 minutos de evolución, irradiado '
                'a mandíbula y hombro izquierdo, acompañado de náuseas, diaforesis profusa '
                'y sensación de muerte inminente.'
            ),
            'signos_vitales': [('TA','88/58 mmHg'),('FC','48 lpm ↓'),('FR','22 rpm'),('SpO₂','90% AA'),('Temp','36.8 °C')],
            'antecedentes': 'HTA de 10 años, DM tipo 2, fumadora activa (20 paq/año). Sin alergias conocidas.',
            'pistas_ecg': 'Observe el segmento ST en las derivaciones inferiores (II, III, aVF) y busque la imagen especular en I y aVL.',
        },
        'preguntas': [
            {
                'id': 'dx', 'numero': 1, 'icono': '🔍',
                'enunciado': '¿Cuál es el diagnóstico más probable según el ECG y el cuadro clínico?',
                'opciones': [
                    {'id':'a','texto':'IAMCEST — Infarto Agudo de Miocardio Inferior (cara inferior, ACD)','correcta':True},
                    {'id':'b','texto':'Angina Inestable sin elevación del ST (SCASEST)','correcta':False},
                    {'id':'c','texto':'Bloqueo AV de 3.° grado (disociación AV completa)','correcta':False},
                    {'id':'d','texto':'Pericarditis Aguda difusa','correcta':False},
                ],
                'derivaciones_clave': ['II','III','aVF'], 'color_clave': '#dc2626',
                'retro_ok': ('El ECG muestra elevación del ST ≥ 1 mm en II, III y aVF (cara inferior), con imagen especular (depresión ST) en I y aVL. '
                             'Corresponde a oclusión aguda de la Arteria Coronaria Derecha (RCA). '
                             'La bradicardia se debe a afectación del nodo sinusal, irrigado por la RCA en el 60% de los pacientes.'),
                'retro_mal': ('Observe el segmento ST en derivaciones INFERIORES (II, III, aVF): hay elevación ≥ 1 mm. '
                              'La angina inestable NO eleva el ST. El BAV 3.° muestra disociación AV y QRS ancho. '
                              'La pericarditis eleva el ST de forma difusa y cóncava, sin imagen especular.'),
            },
            {
                'id': 'conducta', 'numero': 2, 'icono': '💊',
                'enunciado': '¿Cuál es la PRIMERA acción de enfermería prioritaria?',
                'opciones': [
                    {'id':'a','texto':'Activar protocolo IAMCEST (Código Infarto) e informar al médico de guardia de inmediato','correcta':True},
                    {'id':'b','texto':'Administrar Atropina 0.5 mg IV para corregir la bradicardia como medida inicial','correcta':False},
                    {'id':'c','texto':'Solicitar ecocardiograma urgente antes de iniciar cualquier tratamiento','correcta':False},
                    {'id':'d','texto':'Administrar antihipertensivos para normalizar la TA','correcta':False},
                ],
                'derivaciones_clave': [], 'color_clave': '#dc2626',
                'retro_ok': ('En IAMCEST: TIEMPO = MIOCARDIO. '
                             '① Código Infarto + médico → ② O₂ si SpO₂ < 94% → ③ 2 accesos IV + laboratorio → '
                             '④ ASA 300 mg masticable → ⑤ Morfina 2–4 mg IV → '
                             '⑥ Traslado urgente a hemodinamia (ICP primaria < 90 min desde primer contacto médico).'),
                'retro_mal': ('La prioridad ABSOLUTA en IAMCEST es activar el equipo de reperfusión. '
                              'La Atropina puede usarse para la bradicardia, pero DESPUÉS de activar el código. '
                              'Los antihipertensivos están contraindicados con TA 88/58 (hipotensión). '
                              'El ecocardiograma NO debe retrasar el cateterismo.'),
            },
        ],
    },
    {
        'id': 'caso_asmi',
        'filename_hr': 'records500/21000/21040_hr',
        'caso': {
            'titulo': 'Urgencias — Dolor Retroesternal + Síncope',
            'sexo': 'Masculino', 'edad': 58,
            'motivo': (
                'Paciente masculino de 58 años traído por paramédicos tras síncope súbito '
                'en la vía pública. Al recuperar consciencia refiere dolor retroesternal '
                'intenso de 30 minutos, irradiado al brazo izquierdo y diaforesis.'
            ),
            'signos_vitales': [('TA','100/70 mmHg'),('FC','90 lpm'),('FR','24 rpm'),('SpO₂','92% AA'),('Temp','37.1 °C')],
            'antecedentes': 'Dislipidemia con estatinas, DM tipo 2. Sin cardiopatía previa conocida.',
            'pistas_ecg': 'Evalúe el segmento ST en derivaciones precordiales V1 a V4. Busque complejos QS en V1-V2.',
        },
        'preguntas': [
            {
                'id': 'dx', 'numero': 1, 'icono': '🔍',
                'enunciado': '¿Cuál es el diagnóstico más probable?',
                'opciones': [
                    {'id':'a','texto':'IAMCEST Anteroseptal — oclusión proximal de la DAI (Descendente Anterior Izquierda)','correcta':True},
                    {'id':'b','texto':'Tromboembolismo Pulmonar masivo (TEP)','correcta':False},
                    {'id':'c','texto':'Espasmo coronario (Angina de Prinzmetal)','correcta':False},
                    {'id':'d','texto':'Crisis Hipertensiva con dolor atípico','correcta':False},
                ],
                'derivaciones_clave': ['V1','V2','V3','V4'], 'color_clave': '#2563eb',
                'retro_ok': ('El ECG muestra elevación del ST en V1-V4 con complejos QS en V1-V2, '
                             'signo clásico de infarto anteroseptal por oclusión de la DAI proximal. '
                             'El síncope se explica por la caída abrupta del gasto cardíaco debido a la '
                             'disfunción severa de la pared anterior del ventrículo izquierdo.'),
                'retro_mal': ('Observe V1, V2, V3 y V4: hay elevación del ST indicando compromiso anteroseptal (DAI). '
                              'El TEP puede mostrar S1Q3T3 pero no elevación anteroseptal del ST. '
                              'La Angina de Prinzmetal es transitoria y revierte con nitratos. '
                              'La crisis hipertensiva no explica el síncope ni el ST elevado.'),
            },
            {
                'id': 'conducta', 'numero': 2, 'icono': '💊',
                'enunciado': '¿Cuál es la conducta de enfermería MÁS APROPIADA de manera simultánea?',
                'opciones': [
                    {'id':'a','texto':'Activar Código Infarto + O₂ 4 L/min + 2 accesos IV + ASA 300 mg masticable','correcta':True},
                    {'id':'b','texto':'Administrar nitratos sublinguales y reevaluar en 10 minutos','correcta':False},
                    {'id':'c','texto':'Iniciar RCP inmediata (el paciente sufrió un síncope)','correcta':False},
                    {'id':'d','texto':'Solicitar TAC de tórax con contraste para descartar disección aórtica','correcta':False},
                ],
                'derivaciones_clave': [], 'color_clave': '#2563eb',
                'retro_ok': ('Protocolo IAMCEST en paralelo: activar código → O₂ → 2 vías IV + laboratorio '
                             '(troponinas urgentes) → ASA 300 mg + clopidogrel/ticagrelor → morfina para analgesia → '
                             'traslado a hemodinamia. Objetivo: ICP primaria < 90 minutos.'),
                'retro_mal': ('Los nitratos están CONTRAINDICADOS en IAMCEST inferior/derecho (hipotensión severa). '
                              'La RCP no está indicada si el paciente está consciente y con pulso. '
                              'El TAC retrasaría el cateterismo y no es el estudio de primera línea en IAMCEST.'),
            },
        ],
    },
    {
        'id': 'caso_afib',
        'filename_hr': 'records500/14000/14102_hr',
        'caso': {
            'titulo': 'Urgencias — Palpitaciones Irregulares + Disnea',
            'sexo': 'Masculino', 'edad': 59,
            'motivo': (
                'Paciente masculino de 59 años consulta por palpitaciones irregulares '
                'de inicio brusco hace 2 horas, con disnea leve y mareo. '
                'Refiere episodios similares previos que resolvieron solos, '
                'pero nunca de esta duración. Niega dolor torácico.'
            ),
            'signos_vitales': [('TA','130/85 mmHg'),('FC','138 lpm irregular'),('FR','20 rpm'),('SpO₂','94% AA'),('Temp','37.0 °C')],
            'antecedentes': 'HTA con enalapril. Sin anticoagulación previa. Sin cardiopatía estructural conocida.',
            'pistas_ecg': 'Observe la REGULARIDAD del ritmo, la línea de base entre complejos QRS y la presencia o ausencia de ondas P definidas.',
        },
        'preguntas': [
            {
                'id': 'dx', 'numero': 1, 'icono': '🔍',
                'enunciado': '¿Cuál es el diagnóstico del ritmo que muestra el ECG?',
                'opciones': [
                    {'id':'a','texto':'Fibrilación Auricular paroxística con Respuesta Ventricular Rápida (FA-RVR)','correcta':True},
                    {'id':'b','texto':'Taquicardia Supraventricular Paroxística (TSVP) por reentrada nodal','correcta':False},
                    {'id':'c','texto':'Flutter Auricular con conducción variable','correcta':False},
                    {'id':'d','texto':'Taquicardia Sinusal por ansiedad o dolor','correcta':False},
                ],
                'derivaciones_clave': ['II','V1'], 'color_clave': '#ea580c',
                'retro_ok': ('La FA se caracteriza por: ① Ritmo IRREGULARMENTE IRREGULAR (RR variables sin patrón) → '
                             '② Ausencia de ondas P definidas → ③ Línea de base fibrilatoria (ondas f a 350-600/min) → '
                             '④ QRS estrecho (< 120 ms) si no hay aberrancia. Mejor visible en DII y V1.'),
                'retro_mal': ('La TSVP tiene ritmo REGULAR. '
                              'El Flutter tiene ondas F regulares "en dientes de sierra" en II, III, aVF a 300/min. '
                              'La Taquicardia Sinusal tiene onda P positiva y clara antes de cada QRS. '
                              'En la FA: el ritmo es IRREGULARMENTE IRREGULAR y no hay ondas P.'),
            },
            {
                'id': 'conducta', 'numero': 2, 'icono': '💊',
                'enunciado': '¿Cuál es la conducta de enfermería PRIORITARIA en este paciente con FA de 2 horas?',
                'opciones': [
                    {'id':'a','texto':'Monitoreo continuo + O₂ + acceso venoso + anticoagulación + control de FC según prescripción','correcta':True},
                    {'id':'b','texto':'Cardioversión eléctrica sincronizada de inmediato sin valoración previa','correcta':False},
                    {'id':'c','texto':'Administrar digoxina oral como primera línea para controlar la frecuencia','correcta':False},
                    {'id':'d','texto':'No intervenir; esperar que el ritmo revierta espontáneamente','correcta':False},
                ],
                'derivaciones_clave': [], 'color_clave': '#ea580c',
                'retro_ok': ('Manejo inicial de FA estable: '
                             '① Monitoreo continuo → ② O₂ si SpO₂ < 94% → ③ Acceso IV + laboratorio (INR, renal) → '
                             '④ Anticoagulación: HBPM o heparina IV (prevención de tromboembolismo) → '
                             '⑤ Control de FC: metoprolol IV o diltiazem → '
                             '⑥ Valorar cardioversión si FA < 48 h y paciente anticoagulado.'),
                'retro_mal': ('La cardioversión requiere valoración previa del tiempo de evolución y anticoagulación. '
                              'La digoxina tiene inicio lento y no es primera línea en RVR aguda. '
                              'No intervenir con FC 138 lpm y SpO₂ 94% puede llevar al deterioro hemodinámico.'),
            },
        ],
    },
    {
        'id': 'caso_aflt',
        'filename_hr': 'records500/00000/00858_hr',
        'caso': {
            'titulo': 'Urgencias — Palpitaciones Regulares Rápidas + Disnea',
            'sexo': 'Masculino', 'edad': 66,
            'motivo': (
                'Paciente masculino de 66 años con palpitaciones regulares y rápidas '
                'desde ayer, asociadas a disnea al caminar > 100 metros. '
                'Niega dolor torácico ni síncope.'
            ),
            'signos_vitales': [('TA','118/76 mmHg'),('FC','150 lpm regular'),('FR','20 rpm'),('SpO₂','95% AA'),('Temp','36.9 °C')],
            'antecedentes': 'EPOC leve (sin oxigenoterapia), HTA controlada. Sin diagnóstico previo de arritmia.',
            'pistas_ecg': 'Observe la línea de base en derivaciones II, III y aVF. Cuente la frecuencia auricular. ¿Cuántas ondas auriculares hay por cada QRS?',
        },
        'preguntas': [
            {
                'id': 'dx', 'numero': 1, 'icono': '🔍',
                'enunciado': '¿Cuál es el diagnóstico de este ritmo?',
                'opciones': [
                    {'id':'a','texto':'Flutter Auricular con bloqueo AV 2:1 — frecuencia auricular ≈ 300/min','correcta':True},
                    {'id':'b','texto':'Fibrilación Auricular con Respuesta Ventricular Rápida','correcta':False},
                    {'id':'c','texto':'Taquicardia Sinusal secundaria a EPOC descompensado','correcta':False},
                    {'id':'d','texto':'Taquicardia Ventricular sostenida monomórfica','correcta':False},
                ],
                'derivaciones_clave': ['II','III','aVF'], 'color_clave': '#ea580c',
                'retro_ok': ('Flutter Auricular clásico: ① Ondas F "en dientes de sierra" a 250-350/min en II, III, aVF → '
                             '② Ritmo ventricular REGULAR (conducción 2:1 → FC ≈ 150 lpm) → '
                             '③ QRS estrecho (< 120 ms). '
                             'FC exacta de 150 lpm en reposo es una clave diagnóstica clásica del flutter 2:1.'),
                'retro_mal': ('La FA tiene ritmo IRREGULAR sin ondas auriculares regulares. '
                              'La Taquicardia Sinusal tiene onda P clara antes de cada QRS, raramente > 140 lpm en reposo. '
                              'La TV tiene QRS ANCHO (> 120 ms). '
                              'En el flutter: busque los "dientes de sierra" en II, III, aVF: 2 ondas F por cada QRS.'),
            },
            {
                'id': 'conducta', 'numero': 2, 'icono': '💊',
                'enunciado': '¿Cuál es la conducta correcta para este Flutter Auricular hemodinámicamente estable?',
                'opciones': [
                    {'id':'a','texto':'Monitoreo + O₂ + acceso IV + anticoagulación + preparar cardioversión o control de FC según indicación médica','correcta':True},
                    {'id':'b','texto':'RCP inmediata (FC 150 lpm es un "paro cardíaco")','correcta':False},
                    {'id':'c','texto':'Adenosina IV 6 mg rápida para revertir el ritmo','correcta':False},
                    {'id':'d','texto':'Alta con referencia a cardiología ambulatoria, el paciente está estable','correcta':False},
                ],
                'derivaciones_clave': [], 'color_clave': '#ea580c',
                'retro_ok': ('Flutter estable: ① Monitoreo + SpO₂ → ② O₂ si necesario → '
                             '③ Acceso IV + laboratorio (electrolitos, tiroides) → '
                             '④ ANTICOAGULACIÓN (riesgo tromboembólico similar a FA) → '
                             '⑤ Control de FC: betabloqueante o diltiazem IV → '
                             '⑥ Cardioversión eléctrica sincronizada: muy efectiva en flutter (50-100 J). '
                             'La adenosina puede desnmascarar las ondas F pero NO revierte el flutter.'),
                'retro_mal': ('FC 150 lpm con TA estable NO es indicación de RCP. '
                              'La adenosina es diagnóstica, no terapéutica en el flutter. '
                              'El alta es incorrecto: el flutter tiene riesgo tromboembólico igual a la FA.'),
            },
        ],
    },
    {
        'id': 'caso_clbbb',
        'filename_hr': 'records500/18000/18376_hr',
        'caso': {
            'titulo': 'Urgencias — Disnea Progresiva + Edemas Bilaterales',
            'sexo': 'Masculino', 'edad': 66,
            'motivo': (
                'Paciente masculino de 66 años con disnea progresiva durante la última semana, '
                'actualmente en reposo. Presenta edemas maleolares bilaterales, ortopnea '
                'de 2 almohadas y tos nocturna. Niega dolor torácico activo, '
                'pero refiere uno hace 2 años. Trae ECG de control de hace 6 meses.'
            ),
            'signos_vitales': [('TA','145/90 mmHg'),('FC','72 lpm'),('FR','22 rpm'),('SpO₂','90% AA'),('Temp','37.0 °C')],
            'antecedentes': 'IAM hace 2 años (según refiere), HTA, ICC. ECG previo con BRIHH hace 6 meses.',
            'pistas_ecg': 'Observe el ANCHO del complejo QRS. Evalúe la morfología en V1 (onda rS o QS) y en V5-V6 (onda R con muesca o empastamiento).',
        },
        'preguntas': [
            {
                'id': 'dx', 'numero': 1, 'icono': '🔍',
                'enunciado': '¿Cuál es el trastorno de conducción del ECG?',
                'opciones': [
                    {'id':'a','texto':'Bloqueo Completo de Rama Izquierda (BRIHH) — QRS > 120 ms, rS en V1, R empastada en V5-V6','correcta':True},
                    {'id':'b','texto':'Bloqueo Completo de Rama Derecha (BRDHH) — morfología rSR\' en V1','correcta':False},
                    {'id':'c','texto':'Bloqueo AV de 2.° grado Mobitz II (ondas P bloqueadas)','correcta':False},
                    {'id':'d','texto':'Síndrome de Wolf-Parkinson-White (onda delta con PR corto)','correcta':False},
                ],
                'derivaciones_clave': ['V1','V5','V6'], 'color_clave': '#2563eb',
                'retro_ok': ('Criterios BRIHH completo: ① QRS ≥ 120 ms → ② V1: morfología rS o QS → '
                             '③ V5-V6: R con muesca o empastamiento (despolarización tardía) → '
                             '④ Eje desviado a la izquierda frecuente. '
                             'ALERTA: Si este BRIHH es NUEVO en el contexto clínico, '
                             'es un STEMI equivalente y requiere activar protocolo de reperfusión.'),
                'retro_mal': ('El BRDHH muestra rSR\' en V1 (orejas de conejo) y S empastada en I y V6. '
                              'El BAV 2.° Mobitz II tiene PR constante seguido de QRS bloqueado. '
                              'El WPW tiene onda delta y PR < 120 ms. '
                              'En BRIHH: QRS ANCHO con morfología específica en V1 es el dato clave.'),
            },
            {
                'id': 'conducta', 'numero': 2, 'icono': '💊',
                'enunciado': '¿Cuál es la acción de enfermería MÁS URGENTE ante este hallazgo?',
                'opciones': [
                    {'id':'a','texto':'Comparar con ECG previo (¿es nuevo?) + troponinas urgentes + activar equipo médico inmediatamente','correcta':True},
                    {'id':'b','texto':'Administrar atropina 0.5 mg IV para corregir el trastorno de conducción','correcta':False},
                    {'id':'c','texto':'Programar marcapaso definitivo electivo en las próximas 48 horas','correcta':False},
                    {'id':'d','texto':'Tranquilizar al paciente: el BRIHH es un hallazgo benigno sin riesgo inmediato','correcta':False},
                ],
                'derivaciones_clave': [], 'color_clave': '#2563eb',
                'retro_ok': ('BRIHH NUEVO = STEMI equivalente hasta demostrar lo contrario. '
                             '① Comparar con ECG previo (el paciente trae uno de 6 meses) → '
                             '② Troponinas + ECG seriado → '
                             '③ Si es nuevo o hay sospecha isquémica → ACTIVAR CÓDIGO INFARTO → '
                             '④ O₂, acceso IV, monitoreo continuo, posición semifowler → '
                             '⑤ Preparar traslado a hemodinamia urgente.'),
                'retro_mal': ('La atropina trata bradicardia, no el BRIHH. '
                              'Un BRIHH nuevo NO puede esperar 48 horas electivas. '
                              'Ningún BRIHH de nueva aparición en paciente con disnea y SpO₂ 90% debe ignorarse.'),
            },
        ],
    },
    {
        'id': 'caso_lngqt',
        'filename_hr': 'records500/18000/18186_hr',
        'caso': {
            'titulo': 'Urgencias — Síncope Súbito + Uso de Amiodarona',
            'sexo': 'Femenino', 'edad': 68,
            'motivo': (
                'Paciente femenina de 68 años traída por síncope súbito en su domicilio '
                'mientras veía televisión. Recupera consciencia en 2 minutos. '
                'Refiere palpitaciones previas al episodio. Segunda caída en una semana. '
                'Familiares refieren inicio de amiodarona hace 3 semanas por FA previa.'
            ),
            'signos_vitales': [('TA','110/70 mmHg'),('FC','65 lpm'),('FR','16 rpm'),('SpO₂','97% AA'),('Temp','36.7 °C')],
            'antecedentes': 'FA paroxística (amiodarona hace 3 semanas). Lab. reciente: K⁺ = 2.8 mEq/L (hipopotasemia).',
            'pistas_ecg': 'Mida el intervalo desde el inicio del QRS hasta el final de la onda T en derivaciones II y V5. Compare con el intervalo RR.',
        },
        'preguntas': [
            {
                'id': 'dx', 'numero': 1, 'icono': '🔍',
                'enunciado': '¿Cuál es el diagnóstico más probable que explica el síncope?',
                'opciones': [
                    {'id':'a','texto':'Síndrome de QT largo adquirido con riesgo de Torsades de Pointes (amiodarona + hipopotasemia)','correcta':True},
                    {'id':'b','texto':'Accidente Isquémico Transitorio (AIT) de origen cardioembólico','correcta':False},
                    {'id':'c','texto':'Hipoglucemia severa por interacción farmacológica','correcta':False},
                    {'id':'d','texto':'Bloqueo AV de 1.° grado asintomático','correcta':False},
                ],
                'derivaciones_clave': ['II','V5'], 'color_clave': '#7c3aed',
                'retro_ok': ('La amiodarona alarga el QT al bloquear canales de K⁺. Con K⁺ = 2.8 mEq/L '
                             '(hipopotasemia), el riesgo aumenta exponencialmente. '
                             'QTc > 500 ms es umbral de alto riesgo para Torsades de Pointes (TV polimórfica), '
                             'que puede degenerar en FV y muerte súbita. '
                             'El síncope corresponde a un episodio de Torsades autolimitado.'),
                'retro_mal': ('Mida el intervalo QT en II y V5: está prolongado (> 500 ms). '
                              'El contexto (amiodarona + hipopotasemia + síncope + palpitaciones) apunta al QT largo. '
                              'El AIT no genera palpitaciones ni cambios en el ECG. '
                              'El BAV 1.° no causa síncope.'),
            },
            {
                'id': 'conducta', 'numero': 2, 'icono': '💊',
                'enunciado': '¿Cuál es la acción de enfermería PRIORITARIA en esta paciente?',
                'opciones': [
                    {'id':'a','texto':'Monitoreo continuo + SUSPENDER amiodarona + Sulfato de Magnesio 2 g IV lento + corrección IV de potasio','correcta':True},
                    {'id':'b','texto':'Administrar dosis adicional de amiodarona para estabilizar el ritmo','correcta':False},
                    {'id':'c','texto':'Solicitar TAC cerebral urgente como primera medida ante el síncope','correcta':False},
                    {'id':'d','texto':'Alta con instrucción de aumentar el consumo de potasio en la dieta','correcta':False},
                ],
                'derivaciones_clave': [], 'color_clave': '#7c3aed',
                'retro_ok': ('Manejo QT largo adquirido: '
                             '① MONITOREO CONTINUO con desfibrilador al lado (riesgo TV/FV) → '
                             '② SUSPENDER amiodarona (causa del QT largo) → '
                             '③ SULFATO DE MAGNESIO 2 g IV en 10 min (tratamiento de elección para Torsades) → '
                             '④ Corrección IV de K⁺ (objetivo ≥ 4.5 mEq/L) → '
                             '⑤ Preparar desfibrilador al lado de la cama.'),
                'retro_mal': ('Más amiodarona EMPEORARÍA el QT largo: es la causa del problema. '
                              'El TAC cerebral puede hacerse después; el riesgo INMEDIATO es una TV/FV fatal. '
                              'El alta con dieta es totalmente inadecuada: esta paciente necesita UCI urgente.'),
            },
        ],
    },
    {
        'id': 'caso_sbrad',
        'filename_hr': 'records500/20000/20393_hr',
        'caso': {
            'titulo': 'Urgencias — Mareo + Presíncope + FC Baja',
            'sexo': 'Masculino', 'edad': 71,
            'motivo': (
                'Paciente masculino de 71 años por mareo persistente, astenia marcada '
                'y dos episodios de presíncope al incorporarse. '
                'Su esposa refiere que "el corazón le late muy despacio". '
                'Le ajustaron la dosis de metoprolol hace 1 mes.'
            ),
            'signos_vitales': [('TA','92/58 mmHg'),('FC','40 lpm'),('FR','16 rpm'),('SpO₂','96% AA'),('Temp','36.5 °C')],
            'antecedentes': 'HTA con metoprolol 100 mg/día (dosis ajustada hace 1 mes). Sin IAM previo.',
            'pistas_ecg': 'Observe la frecuencia cardíaca, la morfología del QRS y la relación P→QRS. ¿Hay onda P antes de cada QRS?',
        },
        'preguntas': [
            {
                'id': 'dx', 'numero': 1, 'icono': '🔍',
                'enunciado': '¿Cuál es el diagnóstico más probable dado el ECG y el contexto?',
                'opciones': [
                    {'id':'a','texto':'Bradicardia Sinusal sintomática, probablemente por sobredosis de betabloqueante (metoprolol)','correcta':True},
                    {'id':'b','texto':'Bloqueo AV completo (3.° grado) con ritmo de escape ventricular','correcta':False},
                    {'id':'c','texto':'Síndrome del Seno Enfermo con pausas prolongadas en Holter','correcta':False},
                    {'id':'d','texto':'Bradicardia fisiológica de deportista de élite (asintomática)','correcta':False},
                ],
                'derivaciones_clave': ['II'], 'color_clave': '#dc2626',
                'retro_ok': ('Bradicardia Sinusal: ① FC < 60 lpm → ② Onda P positiva antes de cada QRS → '
                             '③ QRS estrecho (morfología normal) → ④ PR normal. '
                             'El metoprolol (betabloqueante) a dosis alta causa bradicardia sintomática '
                             'con hipotensión (TA 92/58) y presíncope: compromiso hemodinámico que requiere acción inmediata.'),
                'retro_mal': ('El BAV 3.° muestra disociación AV: ondas P sin relación con QRS, QRS ancho. '
                              'El Síndrome del Seno Enfermo requiere Holter con pausas > 3 s. '
                              'El deportista tiene bradicardia ASINTOMÁTICA con TA normal. '
                              'Este paciente tiene bradicardia SINTOMÁTICA con hipotensión: emergencia.'),
            },
            {
                'id': 'conducta', 'numero': 2, 'icono': '💊',
                'enunciado': '¿Cuál es la acción de enfermería correcta para esta bradicardia sintomática?',
                'opciones': [
                    {'id':'a','texto':'Suspender metoprolol + Atropina 0.5 mg IV (repetir c/3-5 min hasta 3 mg) + monitoreo + preparar marcapaso transcutáneo','correcta':True},
                    {'id':'b','texto':'Administrar adrenalina 1 mg IV: fármaco de elección para la bradicardia','correcta':False},
                    {'id':'c','texto':'Reposo absoluto y control ambulatorio en 1 semana con cardiología','correcta':False},
                    {'id':'d','texto':'Aplicar maniobra de Valsalva para aumentar la frecuencia cardíaca','correcta':False},
                ],
                'derivaciones_clave': [], 'color_clave': '#dc2626',
                'retro_ok': ('Protocolo Bradicardia Sintomática (ACLS): '
                             '① SUSPENDER metoprolol (causa) → '
                             '② ATROPINA 0.5 mg IV (repetir c/3-5 min, máx 3 mg) → '
                             '③ Monitoreo + O₂ + acceso IV → '
                             '④ Si no responde: MARCAPASO TRANSCUTÁNEO (70-80 lpm) → '
                             '⑤ Refractario: dopamina o adrenalina en infusión continua.'),
                'retro_mal': ('Adrenalina 1 mg IV es para PARO CARDÍACO (asistolia/FV), no para bradicardia con pulso. '
                              'El Valsalva DISMINUYE la FC (indicado para taquicardias). '
                              'Control ambulatorio en 1 semana es inapropiado: TA 92/58 exige manejo hospitalario urgente.'),
            },
        ],
    },
    {
        'id': 'caso_stach',
        'filename_hr': 'records500/04000/04408_hr',
        'caso': {
            'titulo': 'UCI Postoperatoria — Taquicardia en Paciente Quirúrgico',
            'sexo': 'Masculino', 'edad': 77,
            'motivo': (
                'Paciente masculino de 77 años en UCI postoperatoria (día 1 tras '
                'colecistectomía laparoscópica). La enfermera nota alarma de monitor por '
                'FC elevada. El paciente refiere dolor abdominal (EVA 5/10) y sed intensa. '
                'Se observa agitación moderada y diaforesis.'
            ),
            'signos_vitales': [('TA','98/62 mmHg'),('FC','120 lpm'),('FR','22 rpm'),('SpO₂','93%'),('Temp','38.4 °C')],
            'antecedentes': 'HTA, EPOC leve. Balance hídrico: − 800 mL en las últimas 8 horas.',
            'pistas_ecg': 'Identifique el ritmo: ¿hay onda P antes de cada QRS? ¿Es el QRS estrecho? ¿Qué tan regular es el ritmo?',
        },
        'preguntas': [
            {
                'id': 'dx', 'numero': 1, 'icono': '🔍',
                'enunciado': '¿Cuál es el diagnóstico del ritmo y su causa más probable?',
                'opciones': [
                    {'id':'a','texto':'Taquicardia Sinusal secundaria a dolor + hipovolemia + fiebre (contexto postoperatorio)','correcta':True},
                    {'id':'b','texto':'Fibrilación Auricular de nueva aparición postoperatoria','correcta':False},
                    {'id':'c','texto':'Taquicardia Ventricular sostenida monomórfica','correcta':False},
                    {'id':'d','texto':'Taquicardia Supraventricular paroxística por reentrada nodal','correcta':False},
                ],
                'derivaciones_clave': ['II'], 'color_clave': '#16a34a',
                'retro_ok': ('Taquicardia Sinusal: ① Onda P positiva antes de cada QRS en DII → '
                             '② Ritmo REGULAR → ③ QRS ESTRECHO (< 120 ms) → ④ FC 100-150 lpm. '
                             'CAUSA: Dolor activa simpático (taquicardia refleja) + '
                             'Hipovolemia (−800 mL) activa barorreceptores + '
                             'Fiebre 38.4°C aumenta automatismo sinusal ≈ 10 lpm/°C.'),
                'retro_mal': ('La FA tiene ritmo IRREGULARMENTE IRREGULAR sin ondas P definidas. '
                              'La TV tiene QRS ANCHO (> 120 ms) con morfología aberrante. '
                              'La TSVP tiene inicio/fin bruscos y FC típicamente > 150 lpm. '
                              'En la Taquicardia Sinusal: onda P VISIBLE y POSITIVA en DII es el signo clave.'),
            },
            {
                'id': 'conducta', 'numero': 2, 'icono': '💊',
                'enunciado': '¿Cuál es la conducta correcta para esta Taquicardia Sinusal postoperatoria?',
                'opciones': [
                    {'id':'a','texto':'Tratar la CAUSA: analgesia adecuada + reposición de volumen IV + antitérmicos. NO dar antiarrítmicos','correcta':True},
                    {'id':'b','texto':'Administrar metoprolol IV para bajar la FC de inmediato','correcta':False},
                    {'id':'c','texto':'Cardioversión eléctrica sincronizada urgente por FC de 120 lpm','correcta':False},
                    {'id':'d','texto':'Administrar adenosina 6 mg IV rápida para revertir la taquicardia','correcta':False},
                ],
                'derivaciones_clave': [], 'color_clave': '#16a34a',
                'retro_ok': ('La Taquicardia Sinusal es un SÍNTOMA, no una arritmia primaria. '
                             'Tratar la CAUSA: ① Analgesia: ketorolaco o morfina para EVA 5/10 → '
                             '② Hidratación: cristaloides IV 500 mL en 30 min (balance −800 mL) → '
                             '③ Antitérmicos: paracetamol 1 g IV (38.4°C) → ④ O₂ para SpO₂ 93%. '
                             'Al corregir las causas, la FC descenderá progresivamente.'),
                'retro_mal': ('El metoprolol puede causar hipotensión grave en paciente ya hipovolémico (TA 98/62). '
                              'La cardioversión es para arritmias inestables, NO para taquicardias sinusales. '
                              'La adenosina bloquea transitoriamente el nodo AV pero NO tiene efecto en Taquicardia Sinusal '
                              'y puede causar bradicardia paradójica.'),
            },
        ],
    },
]


def _cargar_ecg(filename_hr):
    partes = filename_hr.split('/')
    record = wfdb.rdrecord(partes[2], pn_dir=f'ptb-xl/1.0.3/{partes[0]}/{partes[1]}')
    fs = record.fs
    muestras = int(fs * 3)
    nombres = [str(c).lower().strip() for c in record.sig_name]
    senales = {}
    for canal in ['I','II','III','aVR','aVL','aVF','V1','V2','V3','V4','V5','V6']:
        if canal.lower() in nombres:
            idx = nombres.index(canal.lower())
            senales[canal] = np.nan_to_num(record.p_signal[:muestras, idx]).tolist()
        else:
            senales[canal] = [0] * muestras
    return senales, fs


@app.route('/quiz')
def quiz():
    return render_template('quiz.html')


@app.route('/api/quiz/random')
def quiz_aleatorio():
    caso = random.choice(CASOS_QUIZ)
    try:
        senales, fs = _cargar_ecg(caso['filename_hr'])

        # Mezclar opciones para que la correcta no siempre sea la A
        preguntas_mezcladas = []
        for preg in caso['preguntas']:
            p = copy.deepcopy(preg)
            random.shuffle(p['opciones'])
            preguntas_mezcladas.append(p)

        return jsonify({
            'estado': 'exito',
            'caso_id': caso['id'],
            'caso': caso['caso'],
            'preguntas': preguntas_mezcladas,
            'frecuencia_muestreo': fs,
            'datos_12_derivaciones': senales,
        })
    except Exception as e:
        return jsonify({'estado': 'error', 'mensaje': str(e)})


# ================================================================
#  MONITOR-BOT — ASISTENTE IA CON CONTEXTO COMPLETO DE LA WEB
# ================================================================

# Mapa de hallazgos clínicos esperados por derivación según código SCP
_HALLAZGOS_POR_SCP = {
    'IMI': {
        'II, III, aVF (Cara Inferior)': 'ELEVACIÓN del ST ≥1 mm con posibles ondas Q patológicas. Hallazgo PRIMARIO del infarto inferior.',
        'I, aVL (Cara Lateral alta)':   'DEPRESIÓN recíproca del ST — imagen especular clásica del IMI.',
        'V1 (Cara Septal)':             'Puede mostrar elevación del ST si hay extensión al ventrículo derecho (VD).',
        'V5, V6 (Cara Lateral)':        'Sin cambios primarios en IMI aislado.',
        'aVR':                          'Posible leve depresión del ST.',
    },
    'ASMI': {
        'V1, V2 (Cara Septal)':         'Patrón QS o Qr, elevación del ST. Hallazgo PRIMARIO del infarto anteroseptal.',
        'V3, V4 (Cara Anterior)':       'Elevación del ST, transición anormal, posibles ondas T invertidas.',
        'I, aVL (Cara Lateral alta)':   'Pueden mostrar cambios isquémicos si el infarto es extenso.',
        'II, III, aVF (Cara Inferior)': 'Sin cambios primarios. Posible depresión recíproca leve.',
    },
    'AMI': {
        'V3, V4 (Cara Anterior)':       'ELEVACIÓN del ST, patrón QS. Hallazgo PRIMARIO del infarto anterior.',
        'V1, V2 (Cara Septal)':         'Cambios isquémicos si hay extensión septal.',
        'I, aVL':                       'Posible elevación del ST en infarto anterior extenso.',
        'II, III, aVF':                 'Depresión recíproca del ST (imagen especular).',
    },
    'ALMI': {
        'I, aVL, V5, V6 (Cara Lateral)': 'ELEVACIÓN del ST. Hallazgo PRIMARIO del infarto anterolateral.',
        'V3, V4 (Cara Anterior)':         'Elevación del ST si hay extensión anterior.',
        'II, III, aVF':                   'Depresión recíproca del ST posible.',
    },
    'AFIB': {
        'Todas las derivaciones':         'Ritmo IRREGULARMENTE IRREGULAR — los intervalos RR varían sin patrón fijo.',
        'II y V1 (Derivaciones clave)':   'Ausencia de ondas P definidas. Línea de base fibrilatoria (ondas f a 350-600/min).',
        'QRS en todas':                   'Estrecho (<120 ms) si no hay aberrancia de conducción asociada.',
        'aVR':                            'Puede verse actividad auricular caótica de alta frecuencia.',
    },
    'AFLT': {
        'II, III, aVF (Cara Inferior)':   'Ondas F "en dientes de sierra" regulares a 250-350/min. Hallazgo DIAGNÓSTICO.',
        'V1':                             'Las ondas F suelen ser visibles; ritmo ventricular regular.',
        'Ritmo ventricular (todas)':      'REGULAR con conducción 2:1 → FC aproximada de 150 lpm.',
        'QRS':                            'Estrecho, morfología normal.',
    },
    'CLBBB': {
        'V1 (Clave diagnóstica)':         'Morfología rS o QS — deflexión predominantemente negativa. Hallazgo PRIMARIO.',
        'V5, V6 (Clave diagnóstica)':     'Onda R ancha con muesca o empastamiento (RR\' empastada). Hallazgo PRIMARIO.',
        'I, aVL':                         'Onda R ancha y empastada, sin onda Q inicial.',
        'QRS (todas)':                    'ANCHO ≥120 ms. Eje frecuentemente desviado a la izquierda.',
        'ST y T (todas)':                 'Discordantes con el QRS: ST elevado donde QRS negativo y viceversa.',
    },
    'CRBBB': {
        'V1 (Clave diagnóstica)':         'Morfología rSR\' — patrón "orejas de conejo". Hallazgo PRIMARIO.',
        'V5, V6':                         'Onda S empastada y ancha.',
        'I, aVL':                         'Onda S empastada.',
        'QRS (todas)':                    'ANCHO ≥120 ms.',
    },
    'LNGQT': {
        'II (Medición estándar)':         'Intervalo QT prolongado — medir desde inicio del QRS hasta fin de onda T.',
        'V5 (Confirmación)':              'QT prolongado, posible onda U visible después de la onda T.',
        'Todas':                          'QTc >450 ms (hombre) o >460 ms (mujer) = patológico. QTc >500 ms = riesgo alto de Torsades de Pointes.',
    },
    'SBRAD': {
        'II (Derivación de ritmo)':       'Onda P POSITIVA y de morfología normal antes de cada QRS. FC <60 lpm.',
        'Todas':                          'Ritmo REGULAR sinusal lento. QRS estrecho, PR normal (120-200 ms).',
    },
    'STACH': {
        'II (Derivación de ritmo)':       'Onda P POSITIVA y visible antes de cada QRS. FC >100 lpm.',
        'Todas':                          'Ritmo REGULAR. QRS estrecho. PR normal o levemente corto por frecuencia alta.',
    },
    'NORM': {
        'II (Eje y ritmo)':               'Onda P positiva, PR 120-200 ms, QRS <120 ms, eje normal.',
        'V1-V6 (Progresión)':             'Progresión normal de R: pequeña en V1, creciente hasta V5-V6.',
        'I, aVL':                         'Onda R dominante, eje eléctrico entre -30° y +90°.',
        'Todas':                          'Sin elevación ni depresión del ST. Ondas T simétricas y positivas excepto en aVR.',
    },
    'LVH': {
        'V5, V6 (Clave)':                 'Ondas R ALTAS (>25 mm). Criterio de Sokolow-Lyon: S(V1) + R(V5 o V6) >35 mm.',
        'V1, V2':                         'Ondas S MUY PROFUNDAS.',
        'I, aVL':                         'Eje desviado a la izquierda, posible inversión de onda T (patrón de sobrecarga).',
        'II, III, aVF':                   'Posible depresión del ST y ondas T negativas (strain pattern).',
    },
    'STTC': {
        'Todas':                          'Cambios inespecíficos del segmento ST o de la onda T sin patrón diagnóstico definido.',
        'V4-V6 frecuentemente':           'Depresión o inversión de onda T de origen no isquémico determinado.',
    },
    'WPW': {
        'Todas':                          'PR CORTO (<120 ms) — conducción acelerada por vía accesoria.',
        'I, V4-V6 usualmente':            'Onda DELTA visible — empastamiento inicial del QRS (pre-excitación ventricular).',
        'QRS':                            'Ligeramente ancho por la fusión del frente de activación normal y la pre-excitación.',
    },
    '1AVB': {
        'II (Medición)':                  'Intervalo PR PROLONGADO >200 ms (>5 cuadros pequeños). Morfología normal del QRS.',
        'Todas':                          'Ritmo sinusal regular. Cada P conduce un QRS — no hay bloqueo real de conducción.',
    },
}

_NOMBRES_CARAS = {
    'anterior': 'Cara Anterior (V3-V4) — Arteria DAI',
    'septal':   'Cara Septal (V1-V2) — Arteria DAI proximal',
    'inferior': 'Cara Inferior (II, III, aVF) — Arteria ACD',
    'lateral':  'Cara Lateral (I, aVL, V5-V6) — Arteria LCx',
    'derecho':  'Vector aVR — Referencia del TCI',
}


def _construir_contexto_paciente(meta):
    if not meta:
        return "No hay paciente cargado actualmente en el monitor."
    lineas = []
    if meta.get('sexo') and meta.get('edad') is not None:
        lineas.append(f"• Paciente: {meta['sexo']}, {meta['edad']} años")
    if meta.get('peso_kg') and meta.get('talla_cm'):
        imc = meta.get('imc', '')
        lineas.append(f"• Antropometría: {meta['peso_kg']} kg / {meta['talla_cm']} cm" +
                      (f" (IMC {imc})" if imc else ''))
    if meta.get('scp_codigos'):
        top = meta['scp_codigos'][:4]
        dx = ', '.join([f"{s['nombre']} ({s['confianza']}%)" for s in top])
        lineas.append(f"• Diagnóstico validado por cardiólogo: {dx}")
    if meta.get('informe'):
        lineas.append(f"• Informe clínico completo: {meta['informe'][:500]}")
    if meta.get('eje_cardiaco'):
        lineas.append(f"• Eje cardíaco: {meta['eje_cardiaco']}")
    if meta.get('estadio_infarto'):
        lineas.append(f"• Estadio de infarto: {meta['estadio_infarto']}")
    if meta.get('marcapaso'):
        lineas.append("• Dispositivo: Marcapaso activo")
    return '\n'.join(lineas) if lineas else "Datos del paciente no disponibles."


def _mapa_leads(scp_lista):
    if not scp_lista:
        return "Sin diagnóstico específico para mapear derivaciones."
    bloques = []
    for scp in scp_lista[:3]:
        codigo = scp['codigo']
        if codigo not in _HALLAZGOS_POR_SCP:
            continue
        bloques.append(f"[{scp['nombre']} — confianza {scp['confianza']}%]")
        for lead_grupo, descripcion in _HALLAZGOS_POR_SCP[codigo].items():
            bloques.append(f"  • {lead_grupo}: {descripcion}")
    return '\n'.join(bloques) if bloques else "Diagnóstico registrado sin mapa de derivaciones específico."


def _estado_visual(ctx):
    lineas = []
    cara = ctx.get('cara_seleccionada')
    if cara:
        lineas.append(f"• El estudiante SELECCIONÓ (clic) la cara: {_NOMBRES_CARAS.get(cara, cara)}")
    caras_auto = ctx.get('caras_auto_resaltadas', [])
    if caras_auto:
        nombres = [_NOMBRES_CARAS.get(c, c) for c in caras_auto]
        lineas.append(f"• Territorios auto-resaltados por el diagnóstico: {', '.join(nombres)}")
    lead_zoom = ctx.get('lead_zoom')
    if lead_zoom:
        lineas.append(f"• El estudiante está examinando en ZOOM la derivación: {lead_zoom} (cuadrícula de precisión activa)")
    if not lineas:
        lineas.append("• El estudiante está viendo el monitor completo de 12 derivaciones.")
    return '\n'.join(lineas)


@app.route('/api/chat', methods=['POST'])
def chat_bot():
    if not _GEMINI_OK:
        return jsonify({'error': 'Dependencia faltante. Ejecuta: pip install google-generativeai'}), 500
    if not GEMINI_API_KEY:
        return jsonify({'error': 'Falta la clave API. Define la variable de entorno GEMINI_API_KEY.'}), 500

    data           = request.get_json(silent=True) or {}
    mensaje        = str(data.get('mensaje', '')).strip()
    paciente_id    = str(data.get('paciente_id', '')).strip()
    historial      = data.get('historial', [])
    ctx_visual     = data.get('contexto_visual', {})

    if not mensaje:
        return jsonify({'error': 'Mensaje vacío'}), 400

    meta           = buscar_metadatos(paciente_id) if paciente_id else None
    ctx_paciente   = _construir_contexto_paciente(meta)
    mapa           = _mapa_leads(meta.get('scp_codigos', []) if meta else [])
    visual         = _estado_visual(ctx_visual)

    system_prompt = f"""Eres Monitor-Bot, el Instructor de IA de Cuidado Crítico de la Universidad del Magdalena. \
Tienes acceso completo al estado actual del Monitor Clínico de ECG que está viendo el estudiante: \
sabes qué paciente está cargado, su diagnóstico verificado por cardiólogo, el informe clínico completo \
y exactamente qué debería mostrar cada derivación del ECG según ese diagnóstico.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATOS DEL PACIENTE ACTUALMENTE EN EL MONITOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{ctx_paciente}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAPA CLÍNICO DE DERIVACIONES (qué debe mostrar cada lead según el diagnóstico)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{mapa}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTADO ACTUAL DE LA INTERFAZ (qué está mirando el estudiante ahora mismo)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{visual}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTRUCCIONES DE COMPORTAMIENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODO EXPLICACIÓN: Si el estudiante pide que expliques una derivación específica (ej: "explica V2", \
"qué está pasando en DII"), describe DETALLADAMENTE lo que esa derivación muestra en ESTE paciente: \
morfología de la onda, amplitud estimada, significado clínico, por qué se ve así dado el diagnóstico \
y qué territorio miocárdico representa. Puedes ser completamente explícito en explicaciones.

MODO SOCRÁTICO: Si el estudiante pregunta por el DIAGNÓSTICO (ej: "¿qué tiene?", "¿cuál es el problema?"), \
NUNCA lo digas directamente. Usa el mapa de derivaciones para formular preguntas guía hacia los hallazgos clave.

MODO CONFIRMACIÓN: Si el estudiante acierta el diagnóstico, felicítalo con entusiasmo y explica la \
fisiopatología completa.

REGLAS GLOBALES:
• Responde SIEMPRE en español colombiano formal.
• Usa terminología clínica precisa para un Diplomado en Cuidado Crítico.
• Cuando expliques una derivación, menciona: morfología de ondas (P, QRS, T), segmento ST, \
  intervalo PR/QT si es relevante, y su correlación con el territorio coronario afectado.
• Si el estudiante menciona una derivación por su nombre (V2, DII, aVF, etc.), \
  usa el mapa de derivaciones para dar una respuesta específica y detallada."""

    try:
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=system_prompt
        )

        history_gemini = []
        for h in historial:
            role  = h.get('rol', 'user')
            texto = str(h.get('texto', '')).strip()
            if role in ('user', 'model') and texto:
                history_gemini.append({'role': role, 'parts': [texto]})

        chat_session = model.start_chat(history=history_gemini)
        response     = chat_session.send_message(mensaje)
        return jsonify({'respuesta': response.text})

    except Exception as e:
        return jsonify({'error': f'Error Gemini API: {str(e)}'}), 500


# ================================================================
#  HISTORIAL Y METACOGNICIÓN
# ================================================================

_CATEGORIA_CASO = {
    'caso_imi':   'Isquemia',   'caso_asmi':  'Isquemia',
    'caso_afib':  'Arritmias',  'caso_aflt':  'Arritmias',
    'caso_sbrad': 'Arritmias',  'caso_stach': 'Arritmias',
    'caso_clbbb': 'Conducción', 'caso_lngqt': 'Conducción',
}
_CATEGORIAS = ['Arritmias', 'Isquemia', 'Conducción']


def _insight(cat, total, pct, incorrectas):
    if total == 0:
        return (f"Aún no has practicado <strong>{cat}</strong>. "
                f"¡Empieza con un caso de esta categoría!")
    if total < 3:
        return (f"Solo llevas {total} pregunta(s) de <strong>{cat}</strong>. "
                f"Necesitas más práctica para obtener retroalimentación precisa.")
    if pct < 50:
        return (f"Llevas {total} preguntas de <strong>{cat}</strong> "
                f"pero has fallado {incorrectas}. Repasa los hallazgos "
                f"clave del ECG de esta área antes de continuar.")
    if pct < 75:
        return (f"Progresando en <strong>{cat}</strong> ({pct}% de acierto). "
                f"Intenta explicar la fisiopatología en voz alta para consolidar.")
    return (f"¡Dominio sólido de <strong>{cat}</strong>! "
            f"({pct}% de acierto). Sigue practicando para mantener el nivel.")


def _badges(stats, total):
    b = []
    if total >= 1:
        b.append({'icono': '🩺', 'titulo': 'Primer Paso',
                  'desc': 'Primera pregunta respondida'})
    if total >= 10:
        b.append({'icono': '📚', 'titulo': 'Estudiante Aplicado',
                  'desc': '10 preguntas respondidas'})
    if total >= 25:
        b.append({'icono': '⚡', 'titulo': 'Comprometido',
                  'desc': '25 preguntas respondidas'})
    if total >= 50:
        b.append({'icono': '🔬', 'titulo': 'Investigador',
                  'desc': '50 preguntas respondidas'})
    iconos_cat = {'Arritmias': '❤️', 'Isquemia': '🔴', 'Conducción': '⚡'}
    for cat, d in stats.items():
        if d['total'] >= 4 and d['pct'] >= 80:
            b.append({'icono': iconos_cat.get(cat, '🏆'),
                      'titulo': f'Experto en {cat}',
                      'desc': f"{d['pct']}% de acierto en {d['total']} preguntas"})
    con_datos = [d for d in stats.values() if d['total'] >= 4]
    if len(con_datos) == len(_CATEGORIAS) and all(d['pct'] >= 75 for d in con_datos):
        b.append({'icono': '🏆', 'titulo': 'Clínico Redondo',
                  'desc': 'Dominio ≥ 75% en todas las áreas'})
    return b


# ---- Rutas de autenticación ----

@app.route('/login')
def pagina_login():
    if current_user.is_authenticated:
        return redirect('/perfil')
    return render_template('login.html')


@app.route('/api/register', methods=['POST'])
def api_register():
    data     = request.get_json(silent=True) or {}
    nombre   = str(data.get('nombre', '')).strip()
    correo   = str(data.get('correo', '')).strip().lower()
    password = str(data.get('password', ''))
    if not nombre or not correo or len(password) < 6:
        return jsonify({'ok': False,
                        'error': 'Datos inválidos. La contraseña debe tener al menos 6 caracteres.'}), 400
    if Usuario.query.filter_by(correo=correo).first():
        return jsonify({'ok': False, 'error': 'Ese correo ya está registrado.'}), 409
    u = Usuario(nombre=nombre, correo=correo,
                password_hash=generate_password_hash(password))
    db.session.add(u)
    db.session.commit()
    login_user(u, remember=True)
    return jsonify({'ok': True, 'nombre': u.nombre})


@app.route('/api/login', methods=['POST'])
def api_login():
    data     = request.get_json(silent=True) or {}
    correo   = str(data.get('correo', '')).strip().lower()
    password = str(data.get('password', ''))
    u        = Usuario.query.filter_by(correo=correo).first()
    if not u or not check_password_hash(u.password_hash, password):
        return jsonify({'ok': False, 'error': 'Correo o contraseña incorrectos.'}), 401
    login_user(u, remember=True)
    return jsonify({'ok': True, 'nombre': u.nombre})


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html', usuario=current_user)


# ---- Rutas de progreso ----

@app.route('/api/guardar_resultado', methods=['POST'])
def guardar_resultado():
    if not current_user.is_authenticated:
        return jsonify({'ok': False}), 401
    data        = request.get_json(silent=True) or {}
    caso_id     = str(data.get('caso_id', '')).strip()
    pregunta_id = str(data.get('pregunta_id', '')).strip()
    es_correcto = bool(data.get('es_correcto', False))
    r = ResultadoQuiz(
        user_id=current_user.id, caso_id=caso_id,
        pregunta_id=pregunta_id,
        categoria=_CATEGORIA_CASO.get(caso_id, 'General'),
        es_correcto=es_correcto,
    )
    db.session.add(r)
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/progreso')
@login_required
def api_progreso():
    todos   = current_user.resultados.all()
    total   = len(todos)
    stats   = {}
    for cat in _CATEGORIAS:
        grupo      = [r for r in todos if r.categoria == cat]
        correctas  = sum(1 for r in grupo if r.es_correcto)
        total_cat  = len(grupo)
        pct        = round(correctas / total_cat * 100) if total_cat else 0
        stats[cat] = {'total': total_cat, 'correctas': correctas,
                      'incorrectas': total_cat - correctas, 'pct': pct}

    total_ok   = sum(1 for r in todos if r.es_correcto)
    pct_global = round(total_ok / total * 100) if total else 0

    return jsonify({
        'nombre':      current_user.nombre,
        'total':       total,
        'total_ok':    total_ok,
        'pct_global':  pct_global,
        'stats':       stats,
        'categorias':  _CATEGORIAS,
        'insights':    [_insight(c, stats[c]['total'], stats[c]['pct'],
                                 stats[c]['incorrectas']) for c in _CATEGORIAS],
        'badges':      _badges(stats, total),
    })


@app.route('/api/reiniciar_progreso', methods=['POST'])
@login_required
def reiniciar_progreso():
    current_user.resultados.delete()
    db.session.commit()
    return jsonify({'ok': True})


if __name__ == '__main__':
    app.run(debug=True)
