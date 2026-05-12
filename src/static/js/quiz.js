'use strict';

// ================================================================
//  MOTOR ECG (mismo estándar clínico que el monitor principal)
// ================================================================

const pluginPapelECG = {
    id: 'papelECG',
    beforeDraw: (chart) => {
        const { ctx, chartArea } = chart;
        if (!chartArea) return;
        ctx.save();
        ctx.fillStyle = '#fff5f5';
        ctx.fillRect(chartArea.left, chartArea.top, chartArea.width, chartArea.height);
        const mmX = chartArea.width / 75;
        const mmY = chartArea.height / 50;
        ctx.beginPath();
        for (let i = 0; i <= 75; i++) {
            const x = chartArea.left + i * mmX;
            ctx.lineWidth   = i % 5 === 0 ? 1.0 : 0.4;
            ctx.strokeStyle = i % 5 === 0 ? 'rgba(255,99,132,0.5)' : 'rgba(255,99,132,0.2)';
            ctx.moveTo(x, chartArea.top); ctx.lineTo(x, chartArea.bottom);
            ctx.stroke(); ctx.beginPath();
        }
        for (let i = 0; i <= 50; i++) {
            const y = chartArea.top + i * mmY;
            ctx.lineWidth   = i % 5 === 0 ? 1.0 : 0.4;
            ctx.strokeStyle = i % 5 === 0 ? 'rgba(255,99,132,0.5)' : 'rgba(255,99,132,0.2)';
            ctx.moveTo(chartArea.left, y); ctx.lineTo(chartArea.right, y);
            ctx.stroke(); ctx.beginPath();
        }
        ctx.restore();
    }
};

const graficasQuiz = {};

function dibujarCanal(canvasId, datos, fs) {
    const el = document.getElementById(canvasId);
    if (!el) return;
    const ctx = el.getContext('2d');
    if (graficasQuiz[canvasId]) graficasQuiz[canvasId].destroy();
    graficasQuiz[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: datos.map((_, i) => (i / fs).toFixed(3)),
            datasets: [{ data: datos, borderColor: '#111827', borderWidth: 1.2,
                         pointRadius: 0, tension: 0.1 }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, animation: false,
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            scales: {
                x: { display: false },
                y: { display: false, min: -2.5, max: 2.5 }
            },
            layout: { padding: 0 }
        },
        plugins: [pluginPapelECG]
    });
}

// ================================================================
//  ESTADO DEL QUIZ
// ================================================================

let casoActual       = null;
let correctas        = 0;
let totalRespondidas = 0;
let respuestasDadas  = {};   // { preguntaId: opcionId }
let preguntasOrden   = [];   // orden de IDs de preguntas
let casosVistosHoy   = 0;

// ================================================================
//  CARGA DEL CASO
// ================================================================

function cargarCaso() {
    mostrarEstado('cargando');
    fetch('/api/quiz/random')
        .then(r => r.json())
        .then(data => {
            if (data.estado !== 'exito') throw new Error(data.mensaje);
            casoActual      = data;
            respuestasDadas = {};
            casosVistosHoy++;
            renderCaso(data);
            renderMonitor(data.datos_12_derivaciones, data.frecuencia_muestreo);
            renderPreguntas(data.preguntas);
            document.getElementById('quiz-nav').style.display = 'none';
            mostrarEstado('contenido');
        })
        .catch(err => {
            document.getElementById('quiz-error-msg').textContent =
                'Error al cargar el caso: ' + err.message;
            mostrarEstado('error');
        });
}

function mostrarEstado(estado) {
    document.getElementById('quiz-cargando').style.display  = estado === 'cargando'  ? 'flex' : 'none';
    document.getElementById('quiz-error').style.display     = estado === 'error'     ? 'flex' : 'none';
    document.getElementById('quiz-contenido').style.display = estado === 'contenido' ? 'block': 'none';
}

// ================================================================
//  RENDER: HISTORIA CLÍNICA
// ================================================================

function renderCaso(data) {
    const c = data.caso;
    document.getElementById('caso-numero').textContent =
        `CASO CLÍNICO • ${String(casosVistosHoy).padStart(2,'0')}`;
    document.getElementById('caso-titulo').textContent   = c.titulo;
    document.getElementById('caso-paciente').textContent =
        `${c.sexo} · ${c.edad} años`;
    document.getElementById('caso-motivo').textContent   = c.motivo;
    document.getElementById('caso-antecedentes').textContent = c.antecedentes;
    document.getElementById('caso-pistas-texto').textContent = c.pistas_ecg;

    const signosEl = document.getElementById('caso-signos');
    signosEl.innerHTML = '';
    const alertas = new Set(['FC','SpO₂','TA']);
    (c.signos_vitales || []).forEach(([nombre, valor]) => {
        const esAlerta = alertas.has(nombre) && (
            valor.includes('↓') || valor.includes('↑') ||
            parseFloat(valor) < 60 || parseFloat(valor) > 100
        );
        const fila = document.createElement('div');
        fila.className = 'signo-fila';
        fila.innerHTML = `<span class="signo-nombre">${nombre}</span>
                          <span class="signo-valor${esAlerta ? ' alerta' : ''}">${valor}</span>`;
        signosEl.appendChild(fila);
    });
}

// ================================================================
//  RENDER: MONITOR 12 DERIVACIONES
// ================================================================

const ORDEN_DISPLAY = [
    ['I','aVR','V1','V4'],
    ['II','aVL','V2','V5'],
    ['III','aVF','V3','V6'],
];

function renderMonitor(senales, fs) {
    const grid = document.getElementById('quiz-monitor-grid');
    grid.innerHTML = '';

    ORDEN_DISPLAY.forEach(fila => {
        fila.forEach(canal => {
            const div    = document.createElement('div');
            div.className = 'quiz-derivacion';
            div.id        = `qd-${canal}`;

            const label  = document.createElement('div');
            label.className = 'quiz-derivacion-label';
            label.textContent = canal === 'I' ? 'DI' : canal === 'II' ? 'DII' : canal === 'III' ? 'DIII' : canal;

            const badge = document.createElement('div');
            badge.className = 'quiz-derivacion-badge';
            badge.id        = `badge-${canal}`;
            badge.textContent = 'CLAVE';

            const canvas = document.createElement('canvas');
            canvas.id = `qcanvas_${canal}`;

            div.appendChild(label);
            div.appendChild(badge);
            div.appendChild(canvas);
            grid.appendChild(div);
        });
    });

    // Pequeño delay para asegurar layout antes de dibujar
    requestAnimationFrame(() => {
        Object.keys(senales).forEach(canal => {
            dibujarCanal(`qcanvas_${canal}`, senales[canal], fs);
        });
    });
}

// ================================================================
//  RENDER: PREGUNTAS
// ================================================================

function renderPreguntas(preguntas) {
    preguntasOrden = preguntas.map(p => p.id);
    const container = document.getElementById('preguntas-container');
    container.innerHTML = '';

    preguntas.forEach((preg, idx) => {
        const card = document.createElement('div');
        card.className = 'pregunta-card' + (idx > 0 ? ' bloqueada' : '');
        card.id        = `pregunta-card-${preg.id}`;

        card.innerHTML = `
            <div class="pregunta-header">
                <div class="pregunta-numero">${preg.numero}</div>
                <div class="pregunta-icono">${preg.icono}</div>
                <div class="pregunta-enunciado">${preg.enunciado}</div>
            </div>
            <div class="pregunta-cuerpo">
                <div class="opciones-grid" id="opciones-${preg.id}"></div>
                <div class="retroalimentacion" id="retro-${preg.id}"></div>
            </div>`;

        container.appendChild(card);

        const opcionesEl = card.querySelector(`#opciones-${preg.id}`);
        const letras = ['A','B','C','D'];
        preg.opciones.forEach((op, oi) => {
            const btn = document.createElement('button');
            btn.className = 'opcion-btn';
            btn.id        = `opcion-${preg.id}-${op.id}`;
            btn.innerHTML = `<span class="opcion-letra">${letras[oi]}</span><span>${op.texto}</span>`;
            btn.addEventListener('click', () => responder(preg, op));
            opcionesEl.appendChild(btn);
        });
    });
}

// ================================================================
//  GUÍA PEDAGÓGICA — Patrones ECG por caso y pregunta
// ================================================================

const GUIA_PEDAGOGICA = {
    caso_imi_dx: {
        patron: '🔴 Elevación de ST en Cara Inferior',
        hallazgo: '<strong>Segmento ST</strong> elevado ≥ 1 mm en derivaciones II, III y aVF',
        medida: 'ST ≥ 1 mm en ≥ 2 derivaciones contiguas inferiores + imagen especular (depresión) en I y aVL',
        fisio: 'La oclusión de la <strong>ACD</strong> genera corriente de lesión subepicárdica que desplaza el ST hacia arriba en la cara inferior. La depresión recíproca en I-aVL descarta pericarditis (que eleva ST difusamente sin imagen especular).',
    },
    caso_imi_conducta: {
        patron: '⏱️ Protocolo IAMCEST — Tiempo = Miocardio',
        hallazgo: 'Activación del <strong>Código Infarto</strong> como primera acción: cada minuto cuesta miocardio',
        medida: 'Objetivo ICP primaria < 90 min desde primer contacto médico · ASA 300 mg masticable + O₂ si SpO₂ < 94%',
        fisio: 'Cada minuto de isquemia destruye aproximadamente <strong>2 millones de cardiomiocitos</strong>. Los antihipertensivos están contraindicados con TA 88/58 (hipotensión activa). La atropina solo se usa para la bradicardia, DESPUÉS de activar el código.',
    },
    caso_asmi_dx: {
        patron: '🔵 Patrón QS + Elevación ST Anteroseptal',
        hallazgo: '<strong>Patrón QS</strong> en V1-V2 con elevación del ST: indica necrosis transmural activa',
        medida: 'Ondas Q ≥ 40 ms o ≥ 25% de la amplitud del QRS · Elevación ST ≥ 1 mm en V1-V4',
        fisio: 'La <strong>DAI proximal</strong> irriga tabique y pared anterior (~40% del VI). Su oclusión produce QS por pérdida total de la onda r septal y ST elevado por corriente de lesión activa. El síncope previo refleja la caída brusca del gasto cardíaco.',
    },
    caso_asmi_conducta: {
        patron: '⚡ IAMCEST Anteroseptal — Mayor Mortalidad',
        hallazgo: 'Acciones <strong>simultáneas y en paralelo</strong>: Código + O₂ + 2 accesos IV + ASA',
        medida: 'SpO₂ objetivo ≥ 94% · ICP primaria < 90 min · NO nitratos (contraindicados en hipotensión)',
        fisio: 'El IAMCEST anteroseptal tiene <strong>mayor mortalidad</strong> que el inferior por el volumen miocárdico comprometido (DAI irriga ~40% del VI vs ~20% de la ACD). El síncope durante isquemia indica FV inminente — emergencia máxima.',
    },
    caso_afib_dx: {
        patron: '🌊 Fibrilación Auricular — Ritmo Irregularmente Irregular',
        hallazgo: '<strong>Ausencia de ondas P</strong> + intervalos RR variables sin ningún patrón fijo',
        medida: 'Línea de base fibrilatoria (ondas f) a 350-600/min · QRS estrecho < 120 ms si no hay aberrancia',
        fisio: 'Cientos de frentes de activación caóticos en ambas aurículas impiden la formación de ondas P organizadas. El nodo AV recibe estímulos al azar, produciendo el ritmo ventricular <strong>irregularmente irregular</strong> — el sello diagnóstico de la FA.',
    },
    caso_afib_conducta: {
        patron: '🩸 FA — Anticoagulación + Control de Frecuencia',
        hallazgo: '<strong>Monitoreo + anticoagulación</strong> como pilares: el mayor riesgo es el tromboembolismo',
        medida: 'FC objetivo < 110 lpm en FA aguda estable · Metoprolol o Diltiazem IV · HBPM o Heparina',
        fisio: 'La FA produce éstasis en la orejuela auricular izquierda, favoreciendo trombos con riesgo de <strong>ACV embólico</strong>. La cardioversión sin anticoagulación previa puede movilizar trombos ya formados. Primero anticoagular, luego cardiovertir.',
    },
    caso_aflt_dx: {
        patron: '🦷 Flutter Auricular — Dientes de Sierra',
        hallazgo: '<strong>Ondas F regulares</strong> "en dientes de sierra" a 250-350/min en cara inferior',
        medida: 'FC auricular ~300/min · Conducción 2:1 → FC ventricular ~150 lpm (clave diagnóstica clásica)',
        fisio: 'Un circuito de <strong>macroreentrada</strong> en el istmo cavo-tricuspídeo genera activación auricular organizada y rápida. El nodo AV solo conduce 1 de cada 2 impulsos (bloqueo 2:1 fisiológico), resultando en FC ventricular característica de ~150 lpm.',
    },
    caso_aflt_conducta: {
        patron: '⚡ Flutter — Alta Respuesta a Cardioversión',
        hallazgo: 'Anticoagulación + preparación para <strong>cardioversión eléctrica</strong> (eficacia > 95%)',
        medida: 'Cardioversión sincronizada 50-100 J · Adenosina: diagnóstica (desenmasca ondas F), NO terapéutica',
        fisio: 'La adenosina bloquea transitoriamente el nodo AV, revelando las ondas F del flutter, pero <strong>no interrumpe el circuito de reentrada</strong>. El riesgo tromboembólico del flutter es equivalente al de la FA — anticoagular siempre.',
    },
    caso_clbbb_dx: {
        patron: '📐 BRIHH — Ancho del QRS y Morfología Específica',
        hallazgo: '<strong>QRS ≥ 120 ms</strong> + morfología rS o QS en V1 + R con muesca o empastada en V5-V6',
        medida: 'V1: deflexión negativa amplia (rS o QS) · V5-V6: onda R ancha con empastamiento o muesca (RR\')',
        fisio: 'El bloqueo de la rama izquierda obliga al impulso a activar el VI de forma lenta y <strong>tortuosa desde el VD</strong>. Esta activación retardada produce el QRS ancho, el empastamiento en V5-V6 y la discordancia ST-T (hallazgo normal en BRIHH, no indica isquemia por sí solo).',
    },
    caso_clbbb_conducta: {
        patron: '🚨 BRIHH Nuevo = STEMI Equivalente',
        hallazgo: 'Comparar con ECG previo + <strong>troponinas urgentes</strong> + activar Código Infarto si es nuevo',
        medida: 'Criterio de Sgarbossa: ST ≥ 1 mm concordante con QRS = isquemia activa probable · Sensibilidad ~36%',
        fisio: 'Un BRIHH de <strong>nueva aparición</strong> con sintomatología isquémica activa es un STEMI equivalente — el BRIHH enmascara los cambios clásicos del ST. La atropina trata bradicardia, no el BRIHH. El BRIHH crónico puede coexistir con isquemia activa.',
    },
    caso_lngqt_dx: {
        patron: '📏 QT Prolongado — Riesgo de Torsades de Pointes',
        hallazgo: '<strong>Intervalo QT prolongado</strong>: medir desde inicio del QRS hasta el fin de la onda T en DII y V5',
        medida: 'QTc > 500 ms = riesgo ALTO de Torsades · Normal: < 450 ms (hombre) / < 460 ms (mujer)',
        fisio: 'La amiodarona bloquea canales de K⁺ (corriente I<sub>kr</sub>), prolongando la repolarización. La hipopotasemia <strong>potencia dramáticamente este efecto</strong>. El período vulnerable prolongado permite post-despolarizaciones tempranas que desencadenan TV polimórfica (Torsades).',
    },
    caso_lngqt_conducta: {
        patron: '💊 QT Largo Adquirido — Protocolo de Emergencia',
        hallazgo: 'Suspender la causa + <strong>MgSO₄ 2g IV</strong> + corregir K⁺ + desfibrilador al lado',
        medida: 'K⁺ objetivo ≥ 4.5 mEq/L · MgSO₄ 2g en 10 min · UCI con monitoreo continuo',
        fisio: 'El <strong>Magnesio</strong> suprime las post-despolarizaciones tempranas aunque no corrija el QT. La amiodarona está absolutamente contraindicada — es la causa del problema. Si ocurre Torsades → desfibrilación inmediata (no sincronizada si es TV polimórfica).',
    },
    caso_sbrad_dx: {
        patron: '🐢 Bradicardia Sinusal Sintomática',
        hallazgo: 'Onda P <strong>positiva</strong> en DII antes de cada QRS · FC < 60 lpm · QRS estrecho y regular',
        medida: 'FC < 60 lpm · PR 120-200 ms · Cada P conduce un QRS: no hay bloqueo verdadero',
        fisio: 'El metoprolol (betabloqueante β1) frena el nodo sinusal al bloquear la estimulación adrenérgica. La TA 92/58 y el presíncope indican <strong>compromiso hemodinámico</strong> — el mecanismo compensador (FC) ya está agotado. Emergencia real.',
    },
    caso_sbrad_conducta: {
        patron: '💉 Bradicardia Sintomática — Protocolo ACLS',
        hallazgo: 'Suspender metoprolol + <strong>Atropina 0.5 mg IV</strong> repetible c/3-5 min hasta 3 mg',
        medida: 'Si no responde a Atropina: Marcapaso transcutáneo 70-80 lpm · Dopamina o Adrenalina en infusión',
        fisio: 'La Atropina bloquea el nervio vago, liberando la inhibición sobre el nodo sinusal. La adrenalina 1 mg IV es para <strong>paro cardíaco sin pulso</strong> — en bradicardia con pulso generaría vasoconstricción excesiva y riesgo de FV. Maniobra de Valsalva disminuye la FC: indicada para taquicardias, nunca para bradicardias.',
    },
    caso_stach_dx: {
        patron: '🏃 Taquicardia Sinusal — Síntoma, no Arritmia',
        hallazgo: 'Onda P <strong>positiva y visible</strong> antes de cada QRS en DII · FC > 100 lpm · Ritmo regular',
        medida: 'Morfología P-QRS-T completamente normal · PR y QRS dentro de rangos · Origen: nodo sinusal',
        fisio: 'La taquicardia sinusal es un <strong>mecanismo compensador fisiológico</strong>, no una arritmia primaria. Dolor → simpático (+FC), hipovolemia → barorreceptores (+FC), fiebre → automatismo sinusal +10 lpm/°C. Tratar la causa siempre es suficiente.',
    },
    caso_stach_conducta: {
        patron: '🎯 Tratar la CAUSA de la Taquicardia Sinusal',
        hallazgo: 'Analgesia + hidratación IV + antitérmicos: la FC <strong>descenderá espontáneamente</strong>',
        medida: 'Metoprolol contraindicado en hipovolemia con TA 98/62 · Adenosina solo para TSVP, no sinusal',
        fisio: 'Un betabloqueante en paciente hipovolémico y taquicárdico puede precipitar <strong>colapso hemodinámico</strong>: la taquicardia es el único mecanismo que mantiene el gasto cardíaco cuando el volumen es bajo. Frena el corazón → cae el gasto → choque.',
    },
};

// ================================================================
//  MODAL DE RETROALIMENTACIÓN PEDAGÓGICA
// ================================================================

let _modalCallback = null;   // función a ejecutar al cerrar el modal

function abrirModalRetro(pregunta, esCorrecta) {
    const clave   = `${casoActual.caso_id}_${pregunta.id}`;
    const guia    = GUIA_PEDAGOGICA[clave] || null;
    const modal   = document.getElementById('modal-retro');
    const header  = document.getElementById('modal-retro-header');

    // ---- Cabecera (color semántico) ----
    header.className = 'modal-retro-header ' + (esCorrecta ? 'retro-ok' : 'retro-mal');
    document.getElementById('modal-retro-icono').textContent    = esCorrecta ? '✅' : '💡';
    document.getElementById('modal-retro-titulo').textContent   = esCorrecta
        ? '¡Excelente ojo clínico!'
        : 'Respuesta incorrecta';
    document.getElementById('modal-retro-subtitulo').textContent = esCorrecta
        ? 'Identificaste correctamente el patrón'
        : 'Analicemos juntos la clave diagnóstica';

    // ---- Texto de retroalimentación clínica ----
    document.getElementById('modal-retro-texto').innerHTML =
        esCorrecta ? pregunta.retro_ok : pregunta.retro_mal;

    // ---- Guía pedagógica ----
    const patronEl = document.getElementById('modal-retro-patron');
    if (guia) {
        patronEl.style.display = 'block';
        document.getElementById('patron-titulo').textContent   = guia.patron;
        document.getElementById('patron-hallazgo').innerHTML   = `<strong>Hallazgo clave:</strong> ${guia.hallazgo}`;
        document.getElementById('patron-medida').innerHTML     = `<strong>Medida técnica:</strong> ${guia.medida}`;
        document.getElementById('patron-fisio').innerHTML      = `<strong>Fisiopatología:</strong> ${guia.fisio}`;
    } else {
        patronEl.style.display = 'none';
    }

    // ---- Derivaciones clave (siempre, no solo en acierto) ----
    const leadsEl = document.getElementById('modal-retro-leads');
    if (pregunta.derivaciones_clave && pregunta.derivaciones_clave.length > 0) {
        leadsEl.style.display = 'flex';
        leadsEl.innerHTML =
            `<span class="retro-leads-label">Derivaciones clave:</span>` +
            pregunta.derivaciones_clave.map(l =>
                `<span class="retro-lead-chip" style="background:${pregunta.color_clave}20;
                 color:${pregunta.color_clave};border-color:${pregunta.color_clave}80">${l}</span>`
            ).join('');
    } else {
        leadsEl.style.display = 'none';
    }

    // ---- Resaltar las derivaciones SIEMPRE (no solo en acierto) ----
    if (pregunta.derivaciones_clave && pregunta.derivaciones_clave.length > 0) {
        resaltarDerivaciones(pregunta.derivaciones_clave, pregunta.color_clave);
        // Scroll suave al monitor para que el estudiante vea el resaltado
        setTimeout(() =>
            document.getElementById('quiz-monitor-grid')
                ?.scrollIntoView({ behavior: 'smooth', block: 'center' }),
        250);
    }

    modal.style.display = 'flex';

    // Al cerrar: desbloquear siguiente pregunta o mostrar nav final
    const idxActual   = preguntasOrden.indexOf(pregunta.id);
    const siguienteId = preguntasOrden[idxActual + 1];
    _modalCallback = () => {
        modal.style.display = 'none';
        if (siguienteId) {
            const nextCard = document.getElementById(`pregunta-card-${siguienteId}`);
            nextCard?.classList.remove('bloqueada');
            setTimeout(() => nextCard?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 150);
        } else {
            setTimeout(mostrarNavFinal, 400);
        }
    };
}

function inicializarModalRetro() {
    document.getElementById('modal-retro-continuar')
        .addEventListener('click', () => _modalCallback?.());
    // Cerrar con Escape
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && document.getElementById('modal-retro').style.display !== 'none')
            _modalCallback?.();
    });
}

// ================================================================
//  LÓGICA DE RESPUESTA Y RETROALIMENTACIÓN
// ================================================================

function responder(pregunta, opcionElegida) {
    if (respuestasDadas[pregunta.id]) return;
    respuestasDadas[pregunta.id] = opcionElegida.id;

    const esCorrecta = opcionElegida.correcta;
    if (esCorrecta) correctas++;
    totalRespondidas++;
    actualizarPuntaje();

    // Deshabilitar botones y colorear opciones
    const card = document.getElementById(`pregunta-card-${pregunta.id}`);
    card.querySelectorAll('.opcion-btn').forEach(btn => { btn.disabled = true; });

    pregunta.opciones.forEach(op => {
        const btn = document.getElementById(`opcion-${pregunta.id}-${op.id}`);
        if (!btn) return;
        if (op.correcta)                          btn.classList.add('correcta-mostrada');
        else if (op.id === opcionElegida.id)      btn.classList.add('elegida-incorrecta');
        else                                      btn.classList.add('incorrecta-mostrada');
    });

    card.classList.add(esCorrecta ? 'respondida-ok' : 'respondida-mal');

    // Guardar resultado en servidor (fire-and-forget, no bloquea el quiz)
    fetch('/api/guardar_resultado', {
        method:  'POST',
        headers: {'Content-Type': 'application/json'},
        body:    JSON.stringify({
            caso_id:     casoActual.caso_id,
            pregunta_id: pregunta.id,
            es_correcto: esCorrecta,
        })
    }).catch(() => {});   // silencioso si no hay sesión iniciada

    // Abrir modal pedagógico (con pequeño delay para ver el color del botón)
    setTimeout(() => abrirModalRetro(pregunta, esCorrecta), 320);
}

// ================================================================
//  RESALTADO DE DERIVACIONES CLAVE
// ================================================================

function resaltarDerivaciones(canales, color) {
    // Extraer R,G,B del color hex para CSS
    const rgb = hexARGB(color);

    canales.forEach(canal => {
        const div = document.getElementById(`qd-${canal}`);
        if (!div) return;
        div.classList.add('derivacion-clave');
        div.style.borderColor = color;
        div.style.setProperty('--clave-rgb', rgb);

        const badge = document.getElementById(`badge-${canal}`);
        if (badge) {
            badge.style.background = color;
            badge.textContent = 'CLAVE';
        }
    });
}

function limpiarResaltadoDerivaciones() {
    document.querySelectorAll('.quiz-derivacion.derivacion-clave').forEach(div => {
        div.classList.remove('derivacion-clave');
        div.style.borderColor = '';
    });
    document.querySelectorAll('.quiz-derivacion-badge').forEach(b => {
        b.style.background = '';
    });
}

function hexARGB(hex) {
    const r = parseInt(hex.slice(1,3), 16);
    const g = parseInt(hex.slice(3,5), 16);
    const b = parseInt(hex.slice(5,7), 16);
    return `${r},${g},${b}`;
}

// ================================================================
//  PUNTAJE Y NAVEGACIÓN FINAL
// ================================================================

function actualizarPuntaje() {
    document.getElementById('puntaje-correctas').textContent = correctas;
    document.getElementById('puntaje-total').textContent     = totalRespondidas;
}

function mostrarNavFinal() {
    const nav = document.getElementById('quiz-nav');
    nav.style.display = 'flex';

    const pct = Math.round((correctas / totalRespondidas) * 100);
    const emoji = pct === 100 ? '🏆' : pct >= 75 ? '✅' : pct >= 50 ? '📚' : '🔄';
    document.getElementById('resultado-resumen').textContent =
        `${emoji}  Aciertos acumulados: ${correctas} / ${totalRespondidas} (${pct}%)`;

    nav.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ================================================================
//  INICIO
// ================================================================

window.onload = () => {
    inicializarModalRetro();
    cargarCaso();
};
