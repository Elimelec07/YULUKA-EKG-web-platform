let graficasActivas  = {};
let pacienteActual   = 'records500/21000/21344_hr';
let filtroActual     = 'filtrada_total';   // cruda | con_notch | filtrada_total
let datosAlmacenados = {};
let fsGlobal         = 500;

// --- PLUGIN: PAPEL MILIMETRADO CLÍNICO PERFECTO ---
const pluginPapelECG = {
    id: 'papelECG',
    beforeDraw: (chart) => {
        const { ctx, chartArea } = chart;
        if (!chartArea) return;

        ctx.save();
        ctx.fillStyle = '#fff5f5';
        ctx.fillRect(chartArea.left, chartArea.top, chartArea.width, chartArea.height);

        // La magia clínica: 
        // X: 3 segundos a 25mm/s = 75mm exactos en pantalla
        // Y: 5 mV (-2.5 a 2.5) a 10mm/mV = 50mm exactos en pantalla
        const mmX = chartArea.width / 75; 
        const mmY = chartArea.height / 50;

        ctx.beginPath();
        // Líneas Verticales (75 milímetros de tiempo)
        for (let i = 0; i <= 75; i++) {
            let x = chartArea.left + (i * mmX);
            ctx.moveTo(x, chartArea.top); 
            ctx.lineTo(x, chartArea.bottom);
            ctx.lineWidth = (i % 5 === 0) ? 1.0 : 0.4;
            ctx.strokeStyle = (i % 5 === 0) ? 'rgba(255, 99, 132, 0.5)' : 'rgba(255, 99, 132, 0.2)';
            ctx.stroke(); ctx.beginPath();
        }
        // Líneas Horizontales (50 milímetros de voltaje)
        for (let i = 0; i <= 50; i++) {
            let y = chartArea.top + (i * mmY);
            ctx.moveTo(chartArea.left, y); 
            ctx.lineTo(chartArea.right, y);
            ctx.lineWidth = (i % 5 === 0) ? 1.0 : 0.4;
            ctx.strokeStyle = (i % 5 === 0) ? 'rgba(255, 99, 132, 0.5)' : 'rgba(255, 99, 132, 0.2)';
            ctx.stroke(); ctx.beginPath();
        }
        ctx.restore();
    }
};

// --- RENDERIZADO DE GRÁFICA (CORREGIDO) ---
function dibujarDerivacion(idCanvas, datos, fs) {
    const ctx = document.getElementById(idCanvas).getContext('2d');
    if (graficasActivas[idCanvas]) graficasActivas[idCanvas].destroy();

    const etiquetasTiempo = datos.map((_, i) => (i / fs).toFixed(3));

    graficasActivas[idCanvas] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: etiquetasTiempo,
            datasets: [{
                data: datos,
                borderColor: '#111827', // Negro tinta médica
                borderWidth: 1.2,
                pointRadius: 0, 
                tension: 0.1 
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // Fundamental para llenar la cuadrícula CSS
            animation: false,
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            scales: {
                // ELIMINAMOS el min y max del Eje X. 
                // Ahora Chart.js dibujará los 1500 puntos completos de la onda.
                x: { display: false },
                
                // El Eje Y sí mantiene sus límites porque son Voltios (-2.5mV a 2.5mV)
                y: { display: false, min: -2.5, max: 2.5 } 
            },
            layout: { padding: 0 }
        },
        plugins: [pluginPapelECG]
    });
}

// ================================================================
//  FICHA CLÍNICA DIGITAL
// ================================================================

function _set(id, valor, sufijo = '') {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = (valor !== null && valor !== undefined) ? `${valor}${sufijo}` : '—';
}

function _cat(codigo) {
    const PELIGRO = new Set(['MI','IMI','ASMI','AMI','LMI','PMI','ALMI','ILMI',
                             'IPLMI','IPMI','STEMI','AFIB','AFLT','3AVB','STE_']);
    const ALERTA  = new Set(['SBRAD','STACH','LBBB','RBBB','IRBBB','LAFB/LAHB',
                             'LPFB','1AVB','2AVB','LVH','RVH','STTC','LNGQT',
                             'WPW','STD_','ISCA','ISCI','ISCAL','ISCIL']);
    const NORMAL  = new Set(['NORM','SR']);
    if (PELIGRO.has(codigo)) return 'peligro';
    if (ALERTA.has(codigo))  return 'alerta';
    if (NORMAL.has(codigo))  return 'normal';
    return 'info';
}

function poblarFichaClinica(meta) {
    if (!meta) return;

    // Resetear mapa anatómico antes de poblar
    caraSeleccionada = null;
    limpiarResaltadoLeads();
    document.querySelectorAll('.cara-sector').forEach(s =>
        s.classList.remove('cara-activa', 'cara-auto-activa')
    );

    // Cabecera
    _set('f-ecg-id',     meta.ecg_id     ? `#${meta.ecg_id}`     : null);
    _set('f-patient-id', meta.patient_id ? `#${meta.patient_id}` : null);

    // Datos demográficos
    _set('f-edad',   meta.edad,   meta.edad   ? ' años' : '');
    _set('f-sexo',   meta.sexo);
    _set('f-fecha',  meta.fecha_registro);

    const marcapasoRow = document.getElementById('f-marcapaso-row');
    if (marcapasoRow) marcapasoRow.style.display = meta.marcapaso ? 'flex' : 'none';

    // Antropometría
    _set('f-peso',    meta.peso_kg,  meta.peso_kg   ? ' kg' : '');
    _set('f-talla',   meta.talla_cm, meta.talla_cm  ? ' cm' : '');
    _set('f-imc',     meta.imc,      meta.imc       ? ' kg/m²' : '');
    _set('f-eje',     meta.eje_cardiaco);
    _set('f-estadio', meta.estadio_infarto);

    // Diagnóstico SCP
    const scpEl = document.getElementById('f-scp');
    if (meta.scp_codigos && meta.scp_codigos.length > 0) {
        scpEl.innerHTML = meta.scp_codigos.map(s => {
            const cat = s.categoria || _cat(s.codigo);
            return `<span class="scp-badge scp-${cat}" title="${s.codigo}">
                        ${s.nombre}&nbsp;<em>${s.confianza}%</em>
                    </span>`;
        }).join('');
    } else {
        scpEl.textContent = '—';
    }

    // Informe clínico
    _set('f-informe', meta.informe);

    // Alertas de calidad
    const calEl = document.getElementById('f-calidad');
    const alertas = [];
    if (meta.calidad) {
        if (meta.calidad.ruido_basal)         alertas.push('Deriva basal');
        if (meta.calidad.ruido_estatico)       alertas.push('Ruido estático');
        if (meta.calidad.ruido_burst)          alertas.push('Ruido burst');
        if (meta.calidad.problema_electrodos)  alertas.push('Problema electrodos');
    }
    calEl.innerHTML = alertas.map(a => `<span class="calidad-tag">${a}</span>`).join('');

    // Auto-resaltar territorios desde los códigos SCP del diagnóstico
    autoResaltarDesdeSCP(meta.scp_codigos);
}

// --- LÓGICA DE COMUNICACIÓN CON PYTHON ---
function solicitarSenales() {
    fetch(`/api/ecg/ptb-xl/${pacienteActual}?filtro=${filtroActual}`)
        .then(respuesta => respuesta.json())
        .then(datosRecibidos => {
            if (datosRecibidos.estado === 'exito') {
                const fs     = datosRecibidos.frecuencia_muestreo;
                const senales = datosRecibidos.datos_12_derivaciones;

                fsGlobal = fs;
                const derivaciones = ['I','II','III','aVR','aVL','aVF','V1','V2','V3','V4','V5','V6'];
                derivaciones.forEach(canal => {
                    datosAlmacenados[canal] = senales[canal];
                    dibujarDerivacion(`grafica_${canal}`, senales[canal], fs);
                });

                // Poblar la ficha clínica con los metadatos recibidos
                poblarFichaClinica(datosRecibidos.metadatos);

                // Resetear chat si cambió el paciente
                if (_chatUltimoPaciente !== pacienteActual) {
                    _chatUltimoPaciente = pacienteActual;
                    limpiarChatContexto();
                }

                // Si el modal está abierto, refrescar la derivación activa
                if (document.getElementById('modal-zoom').style.display !== 'none' && datosAlmacenados[labelZoom]) {
                    datosZoom = datosAlmacenados[labelZoom];
                    fsZoom    = fs;
                    renderZoom();
                }
            } else {
                alert('Error: ' + datosRecibidos.mensaje);
            }
        });
}

// --- EVENTOS DE BOTONES ---
document.getElementById('btnCargar').addEventListener('click', () => {
    const seleccion = document.getElementById('selectPTB').value;

    if (seleccion === '__random__') {
        solicitarAleatorio();
    } else {
        pacienteActual = seleccion;
        ocultarBadgeAleatorio();
        solicitarSenales();
    }
});

function ocultarBadgeAleatorio() {
    document.getElementById('badge-aleatorio').style.display = 'none';
}

function mostrarBadgeAleatorio(filename_hr, metadatos) {
    const badge = document.getElementById('badge-aleatorio');
    const span  = document.getElementById('badge-aleatorio-id');
    const id    = filename_hr.split('/').pop().replace('_hr', '');
    let diagnostico = '';
    if (metadatos && metadatos.scp_codigos && metadatos.scp_codigos.length > 0) {
        const top = metadatos.scp_codigos[0];
        diagnostico = ` · ${top.nombre} (${top.confianza}%)`;
    }
    span.textContent = `#${id}${diagnostico}`;
    badge.style.display = 'flex';
}

function solicitarAleatorio() {
    fetch(`/api/ecg/random?filtro=${filtroActual}`)
        .then(r => r.json())
        .then(datos => {
            if (datos.estado !== 'exito') { alert('Error: ' + datos.mensaje); return; }

            pacienteActual = datos.paciente;   // guardar para rerenders (ruido, zoom)

            const fs          = datos.frecuencia_muestreo;
            const senales     = datos.datos_12_derivaciones;
            const derivaciones = ['I','II','III','aVR','aVL','aVF','V1','V2','V3','V4','V5','V6'];

            fsGlobal = fs;
            derivaciones.forEach(canal => {
                datosAlmacenados[canal] = senales[canal];
                dibujarDerivacion(`grafica_${canal}`, senales[canal], fs);
            });

            poblarFichaClinica(datos.metadatos);
            mostrarBadgeAleatorio(datos.paciente, datos.metadatos);

            // Resetear chat con nuevo contexto de paciente aleatorio
            if (_chatUltimoPaciente !== pacienteActual) {
                _chatUltimoPaciente = pacienteActual;
                limpiarChatContexto();
            }

            if (document.getElementById('modal-zoom').style.display !== 'none' && datosAlmacenados[labelZoom]) {
                datosZoom = datosAlmacenados[labelZoom];
                fsZoom    = fs;
                renderZoom();
            }
        });
}

// ================================================================
//  MÓDULO DSP EDUCATIVO
// ================================================================

const _DSP_INFO = {
    cruda: {
        icono: '⚠️',
        titulo: 'Señal Cruda (RAW) — Sin procesamiento',
        cuerpo: 'Estás viendo la señal tal como llega del electrodo: con interferencia de 60 Hz de la red eléctrica colombiana y deriva basal por la respiración (~0.2 Hz). En un hospital real, una señal así dificultaría el diagnóstico.',
        consejo: '💡 Si al activar el Filtro de Red la señal mejora notablemente, el problema era interferencia eléctrica, no una arritmia.',
        claseMonitor: 'monitor-cruda',
    },
    con_notch: {
        icono: '🔶',
        titulo: 'Filtro Notch 60 Hz activo',
        cuerpo: 'El filtro notch de fase cero (iirnotch + filtfilt) elimina selectivamente 60 Hz sin afectar las ondas del ECG. La deriva basal por respiración todavía está presente. Útil para identificar si el ruido venía de los cables o de la red.',
        consejo: '💡 Si el trazo sigue oscilando lentamente, el problema residual es deriva basal (movimiento del paciente o respiración). Activa el Modo Diagnóstico para corregirlo.',
        claseMonitor: 'monitor-notch',
    },
    filtrada_total: {
        icono: '✅',
        titulo: 'Modo Diagnóstico — Pasa-banda 0.5–40 Hz',
        cuerpo: 'Filtro Butterworth de 4° orden con fase cero (filtfilt). Elimina la deriva basal (<0.5 Hz) y el ruido muscular de alta frecuencia (>40 Hz). Esta es la señal que un cardiólogo usa para tomar decisiones clínicas.',
        consejo: '💡 A 25 mm/s · 10 mm/mV (estándar clínico), cada cuadro pequeño equivale a 40 ms y 0.1 mV — igual que cualquier monitor ECG hospitalario.',
        claseMonitor: 'monitor-limpio',
    },
};

function _actualizarDSP(modo) {
    const info    = _DSP_INFO[modo];
    const monitor = document.querySelector('.monitor-12-derivaciones');
    if (monitor) {
        monitor.classList.remove('monitor-cruda', 'monitor-notch', 'monitor-limpio');
        monitor.classList.add(info.claseMonitor);
    }

    const expEl = document.getElementById('dsp-explicacion');
    if (expEl && info) {
        expEl.innerHTML =
            `<div class="dsp-exp-icono">${info.icono}</div>` +
            `<div class="dsp-exp-cuerpo">` +
            `<strong>${info.titulo}</strong><p>${info.cuerpo}</p>` +
            `<div class="dsp-exp-consejo">${info.consejo}</div>` +
            `</div>`;
    }

    // Highlight opción activa
    document.querySelectorAll('.dsp-opcion').forEach(el => el.classList.remove('dsp-opcion-activa'));
    const mapa = { cruda: 'dsp-op-cruda', con_notch: 'dsp-op-notch', filtrada_total: 'dsp-op-total' };
    document.getElementById(mapa[modo])?.classList.add('dsp-opcion-activa');
}

function inicializarDSP() {
    document.querySelectorAll('input[name="filtro-ecg"]').forEach(radio => {
        radio.addEventListener('change', () => {
            filtroActual = radio.value;
            _actualizarDSP(filtroActual);
            solicitarSenales();
        });
    });
    _actualizarDSP('filtrada_total');
}

// ================================================================
//  MAPA ANATÓMICO — TERRITORIOS CORONARIOS
// ================================================================

const CARAS = {
    anterior: {
        leads: ['V3','V4'],
        color: '#16a34a', shadow: 'rgba(22,163,74,0.28)',
        bgColor: '#dcfce7',
        nombre: 'Cara Anterior',
        arteria: 'DAI — Descendente Anterior Izquierda', arteriaBadge: 'LAD',
        desc: 'Pared anterior del ventrículo izquierdo. Irrigada por la arteria descendente anterior (rama de la coronaria izquierda).',
        signos: 'Elevación ST en V3-V4 indica compromiso anterior. Patrón QS = Infarto Anterior (AMI). Buscar imagen especular en cara inferior.'
    },
    septal: {
        leads: ['V1','V2'],
        color: '#2563eb', shadow: 'rgba(37,99,235,0.28)',
        bgColor: '#dbeafe',
        nombre: 'Cara Septal',
        arteria: 'DAI — Descendente Anterior Izquierda', arteriaBadge: 'LAD',
        desc: 'Tabique interventricular. Irrigado por ramas septales de la DAI, comprometido en oclusiones proximales.',
        signos: 'Patrón QS en V1-V2 = Infarto Anteroseptal (ASMI). BRIHH de nueva aparición equivale a STEMI septal.'
    },
    inferior: {
        leads: ['II','III','aVF'],
        color: '#dc2626', shadow: 'rgba(220,38,38,0.28)',
        bgColor: '#fee2e2',
        nombre: 'Cara Inferior',
        arteria: 'ACD — Arteria Coronaria Derecha', arteriaBadge: 'RCA',
        desc: 'Pared inferior o diafragmática del VI. Irrigada por la ACD en el 80% (dominancia derecha) o por la LCx (dominancia izquierda).',
        signos: 'Ondas Q + elevación ST en II, III, aVF = Infarto Inferior (IMI). Buscar cambios recíprocos en I y aVL.'
    },
    lateral: {
        leads: ['I','aVL','V5','V6'],
        color: '#ea580c', shadow: 'rgba(234,88,12,0.28)',
        bgColor: '#ffedd5',
        nombre: 'Cara Lateral',
        arteria: 'LCx — Arteria Circunfleja', arteriaBadge: 'LCx',
        desc: 'Pared lateral del ventrículo izquierdo. Irrigada por la arteria circunfleja, rama de la coronaria izquierda.',
        signos: 'Cambios en I, aVL, V5-V6 suelen acompañar infartos anteriores extensos (ALMI). Infarto lateral puro es poco frecuente.'
    },
    derecho: {
        leads: ['aVR'],
        color: '#7c3aed', shadow: 'rgba(124,58,237,0.28)',
        bgColor: '#ede9fe',
        nombre: 'Vector de Referencia (aVR)',
        arteria: 'TCI — Tronco Coronario Izquierdo', arteriaBadge: 'TCI',
        desc: 'aVR mira el corazón desde arriba-derecha. Su polaridad es la inversa de la cara lateral. No se usa para localizar isquemia típica.',
        signos: 'Elevación ST en aVR + depresión difusa en otras derivaciones → Isquemia severa del TCI o enfermedad de 3 vasos.'
    }
};

// Lead → cara
const LEAD_A_CARA = Object.fromEntries(
    Object.entries(CARAS).flatMap(([cara, info]) => info.leads.map(l => [l, cara]))
);

// Código SCP → caras afectadas
const SCP_A_CARAS_MAP = {
    'IMI':  ['inferior'],       'ILMI': ['inferior','lateral'],
    'IPMI': ['inferior'],       'IPLMI':['inferior','lateral'],
    'ASMI': ['septal','anterior'], 'AMI':['anterior'],
    'ALMI': ['anterior','lateral'],'LMI': ['lateral'],
    'ISCI': ['inferior'],       'ISCIL':['inferior','lateral'],
    'ISCA': ['anterior'],       'ISCAL':['anterior','lateral'],
    'ISCAS':['anterior','septal'],'ISCIN':['inferior','anterior'],
    'STEMI':['anterior','septal'],'STE_':['anterior'],
    'STD_': ['inferior'],       'CLBBB':['anterior','septal'],
};

let caraSeleccionada   = null;
let carasAutoResaltadas = new Set();

function inicializarAnatomia() {
    // Clic + hover en sectores del SVG
    document.querySelectorAll('.cara-sector').forEach(el => {
        const cara = el.dataset.cara;
        el.addEventListener('click',      () => toggleResaltadoCara(cara));
        el.addEventListener('mouseenter', () => { _activarSVG(cara); mostrarInfoCara(cara); });
        el.addEventListener('mouseleave', () => {
            if (!caraSeleccionada) { _desactivarSVG(); ocultarInfoCara(); }
            else { _activarSVG(caraSeleccionada); mostrarInfoCara(caraSeleccionada); }
        });
    });

    // Hover sobre derivaciones ECG
    document.querySelectorAll('.contenedor-derivacion').forEach(div => {
        const canvas = div.querySelector('canvas');
        if (!canvas) return;
        const canal = canvas.id.replace('grafica_', '');
        const cara  = LEAD_A_CARA[canal];
        if (!cara) return;

        div.addEventListener('mouseenter', () => {
            if (document.getElementById('modal-zoom').style.display !== 'none') return;
            if (caraSeleccionada) return;
            _activarSVG(cara);
            mostrarInfoCara(cara);
        });
        div.addEventListener('mouseleave', () => {
            if (document.getElementById('modal-zoom').style.display !== 'none') return;
            if (caraSeleccionada) return;
            _desactivarSVG();
            ocultarInfoCara();
        });
    });
}

function toggleResaltadoCara(cara) {
    if (caraSeleccionada === cara) {
        caraSeleccionada = null;
        limpiarResaltadoLeads();
        _desactivarSVG();
        carasAutoResaltadas.forEach(c =>
            document.querySelector(`.cara-sector[data-cara="${c}"]`)?.classList.add('cara-auto-activa')
        );
        ocultarInfoCara();
    } else {
        caraSeleccionada = cara;
        limpiarResaltadoLeads();
        _desactivarSVG();
        _activarSVG(cara);
        resaltarLeadsDeCara(cara);
        mostrarInfoCara(cara);
    }
}

function _activarSVG(cara) {
    document.querySelectorAll('.cara-sector').forEach(s => s.classList.remove('cara-activa'));
    document.querySelector(`.cara-sector[data-cara="${cara}"]`)?.classList.add('cara-activa');
}

function _desactivarSVG() {
    document.querySelectorAll('.cara-sector').forEach(s => s.classList.remove('cara-activa'));
}

function resaltarLeadsDeCara(cara) {
    const info = CARAS[cara];
    if (!info) return;
    info.leads.forEach(lead => {
        const div = document.getElementById(`grafica_${lead}`)?.closest('.contenedor-derivacion');
        if (!div) return;
        div.style.setProperty('--color-cara',  info.color);
        div.style.setProperty('--shadow-cara', info.shadow);
        div.classList.add('lead-resaltado');
    });
}

function limpiarResaltadoLeads() {
    document.querySelectorAll('.contenedor-derivacion.lead-resaltado')
        .forEach(d => d.classList.remove('lead-resaltado'));
}

function mostrarInfoCara(cara) {
    const info = CARAS[cara];
    if (!info) return;
    document.getElementById('anatomia-placeholder').style.display = 'none';
    const infoDiv = document.getElementById('anatomia-info');
    infoDiv.style.display = 'flex';

    const hdr = document.getElementById('anatomia-cara-header');
    hdr.style.borderLeftColor = info.color;
    hdr.style.background      = info.bgColor;

    document.getElementById('anatomia-cara-nombre').textContent = info.nombre;
    document.getElementById('anatomia-cara-leads').textContent  = info.leads.join(' · ');

    const badge = document.getElementById('anatomia-arteria-badge');
    badge.textContent       = info.arteriaBadge;
    badge.style.background  = info.color;

    document.getElementById('anatomia-arteria-nombre').textContent = info.arteria;
    document.getElementById('anatomia-desc').textContent           = info.desc;
    document.getElementById('anatomia-signos').textContent         = info.signos;
}

function ocultarInfoCara() {
    document.getElementById('anatomia-placeholder').style.display = 'flex';
    document.getElementById('anatomia-info').style.display        = 'none';
}

function autoResaltarDesdeSCP(scp_codigos) {
    carasAutoResaltadas.clear();
    document.querySelectorAll('.cara-sector.cara-auto-activa')
        .forEach(s => s.classList.remove('cara-auto-activa'));
    if (!scp_codigos) return;

    scp_codigos.forEach(scp => {
        const caras = SCP_A_CARAS_MAP[scp.codigo];
        if (caras && scp.confianza >= 50) {
            caras.forEach(cara => {
                carasAutoResaltadas.add(cara);
                if (!caraSeleccionada)
                    document.querySelector(`.cara-sector[data-cara="${cara}"]`)
                        ?.classList.add('cara-auto-activa');
            });
        }
    });
}

// Cargar la primera señal automáticamente al abrir la página
window.onload = () => {
    inicializarDSP();
    solicitarSenales();
    inicializarModalZoom();
    inicializarAnatomia();
    inicializarChat();
    // Click en cualquier derivación abre el zoom
    document.querySelectorAll('.contenedor-derivacion').forEach(div => {
        div.addEventListener('click', () => {
            const canvas = div.querySelector('canvas');
            if (!canvas) return;
            const canal = canvas.id.replace('grafica_', '');
            if (!datosAlmacenados[canal]) return;
            abrirModalZoom(canal, datosAlmacenados[canal], fsGlobal);
        });
    });
};

// ================================================================
//  CUADRÍCULA DE PRECISIÓN INTERACTIVA
//  Estándar clínico: 25 mm/s horizontal · 10 mm/mV vertical
//  Papel total: 75 mm (3 s) × 50 mm (5 mV, centrado en 0)
// ================================================================

let datosZoom = null;
let labelZoom  = '';
let fsZoom     = 500;

// Vista expresada en milímetros del papel ECG
let vista = { x: 0, y: 0, ancho: 75, alto: 50 };

// Estado de arrastre
let arrastrandoZoom = false;
let arrastreZoom = { cx0: 0, cy0: 0, vx0: 0, vy0: 0 };

// Estado de medición
let modoMedicion   = false;
let puntosM        = [];          // [{x,y}] en mm, máx 2
let cursorMmActual = null;

// ---- Helpers de coordenadas ----

function canvasAMm(canvasX, canvasY) {
    const c = document.getElementById('canvas-zoom');
    return {
        x: (canvasX / c.offsetWidth)  * vista.ancho + vista.x,
        y: (canvasY / c.offsetHeight) * vista.alto  + vista.y
    };
}

function mmAPx(mmX, mmY) {
    const c = document.getElementById('canvas-zoom');
    return {
        x: (mmX - vista.x) / vista.ancho * c.width,
        y: (mmY - vista.y) / vista.alto  * c.height
    };
}

// ---- Zoom centrado en un punto (en mm) ----

function aplicarZoom(factor, cxMm, cyMm) {
    const nuevoAncho = Math.max(2, Math.min(75, vista.ancho * factor));
    const nuevoAlto  = nuevoAncho * (50 / 75);
    const rx = (cxMm - vista.x) / vista.ancho;
    const ry = (cyMm - vista.y) / vista.alto;
    vista.x    = cxMm - rx * nuevoAncho;
    vista.y    = cyMm - ry * nuevoAlto;
    vista.ancho = nuevoAncho;
    vista.alto  = nuevoAlto;
    document.getElementById('zoom-nivel').textContent =
        `${(75 / vista.ancho).toFixed(1)}×`;
}

// ---- Rectángulo redondeado compatible ----

function rrect(ctx, x, y, w, h, r) {
    if (ctx.roundRect) {
        ctx.roundRect(x, y, w, h, r);
    } else {
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + w - r, y);
        ctx.quadraticCurveTo(x + w, y, x + w, y + r);
        ctx.lineTo(x + w, y + h - r);
        ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
        ctx.lineTo(x + r, y + h);
        ctx.quadraticCurveTo(x, y + h, x, y + h - r);
        ctx.lineTo(x, y + r);
        ctx.quadraticCurveTo(x, y, x + r, y);
        ctx.closePath();
    }
}

// ---- Renderizado principal ----

function renderZoom() {
    const canvas = document.getElementById('canvas-zoom');
    // Resolución física = tamaño CSS (evita blur)
    canvas.width  = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;

    // Fondo papel térmico
    ctx.fillStyle = '#fff5f5';
    ctx.fillRect(0, 0, W, H);

    const pxXpMm = W / vista.ancho;
    const pxYpMm = H / vista.alto;

    // ---- Cuadrícula milimetrada ----
    const x0 = Math.floor(vista.x),   x1 = Math.ceil(vista.x + vista.ancho);
    const y0 = Math.floor(vista.y),   y1 = Math.ceil(vista.y + vista.alto);

    for (let mm = x0; mm <= x1; mm++) {
        const px   = (mm - vista.x) / vista.ancho * W;
        const big  = mm % 5 === 0;
        ctx.strokeStyle = big ? 'rgba(210,50,70,0.55)' : 'rgba(210,50,70,0.2)';
        ctx.lineWidth   = big ? 1.0 : 0.5;
        ctx.beginPath(); ctx.moveTo(px, 0); ctx.lineTo(px, H); ctx.stroke();
        // Etiqueta de tiempo
        if (big && pxXpMm >= 4) {
            ctx.fillStyle = 'rgba(175,45,65,0.65)';
            ctx.font = `${Math.min(11, Math.max(9, pxXpMm * 1.4))}px sans-serif`;
            ctx.fillText(`${mm}mm / ${(mm / 25).toFixed(2)}s`, px + 3, H - 4);
        }
    }

    for (let mm = y0; mm <= y1; mm++) {
        const py   = (mm - vista.y) / vista.alto * H;
        const big  = mm % 5 === 0;
        ctx.strokeStyle = big ? 'rgba(210,50,70,0.55)' : 'rgba(210,50,70,0.2)';
        ctx.lineWidth   = big ? 1.0 : 0.5;
        ctx.beginPath(); ctx.moveTo(0, py); ctx.lineTo(W, py); ctx.stroke();
        // Etiqueta de voltaje (25mm = 0 mV, 10mm = 1 mV)
        if (big && pxYpMm >= 4) {
            const mV = ((25 - mm) / 10).toFixed(1);
            ctx.fillStyle = 'rgba(175,45,65,0.65)';
            ctx.font = `${Math.min(11, Math.max(9, pxYpMm * 1.4))}px sans-serif`;
            ctx.fillText(`${mV}mV`, 3, py - 3);
        }
    }

    // Línea isoeléctrica (25 mm → 0 mV)
    const yIso = (25 - vista.y) / vista.alto * H;
    if (yIso >= 0 && yIso <= H) {
        ctx.strokeStyle = 'rgba(210,50,70,0.38)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([6, 4]);
        ctx.beginPath(); ctx.moveTo(0, yIso); ctx.lineTo(W, yIso); ctx.stroke();
        ctx.setLineDash([]);
    }

    // ---- Señal ECG ----
    if (datosZoom && datosZoom.length > 0) {
        ctx.strokeStyle = '#111827';
        ctx.lineWidth   = Math.max(1, Math.min(2.2, pxXpMm * 0.18));
        ctx.lineJoin    = 'round';
        ctx.beginPath();
        let started = false;
        for (let i = 0; i < datosZoom.length; i++) {
            const mmX = (i / fsZoom) * 25;
            if (mmX < vista.x - 0.5 || mmX > vista.x + vista.ancho + 0.5) continue;
            const mmY = 25 - datosZoom[i] * 10;
            const px  = (mmX - vista.x) / vista.ancho * W;
            const py  = (mmY - vista.y) / vista.alto  * H;
            if (!started) { ctx.moveTo(px, py); started = true; }
            else ctx.lineTo(px, py);
        }
        ctx.stroke();
    }

    // ---- Crosshair del cursor ----
    if (cursorMmActual) {
        const cpx = (cursorMmActual.x - vista.x) / vista.ancho * W;
        const cpy = (cursorMmActual.y - vista.y) / vista.alto  * H;

        ctx.strokeStyle = 'rgba(66,153,225,0.75)';
        ctx.lineWidth   = 1;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(cpx, 0); ctx.lineTo(cpx, H);
        ctx.moveTo(0, cpy); ctx.lineTo(W, cpy);
        ctx.stroke();
        ctx.setLineDash([]);

        const t  = (cursorMmActual.x / 25).toFixed(3);
        const mV = ((25 - cursorMmActual.y) / 10).toFixed(3);
        document.getElementById('info-cursor').textContent =
            `t = ${t} s  (${cursorMmActual.x.toFixed(1)} mm)  ·  ${mV} mV  (${cursorMmActual.y.toFixed(1)} mm)`;
    }

    // ---- Puntos de medición ----
    puntosM.forEach((p, i) => {
        const { x: px, y: py } = mmAPx(p.x, p.y);
        ctx.fillStyle   = i === 0 ? '#48bb78' : '#e53e3e';
        ctx.strokeStyle = 'white';
        ctx.lineWidth   = 2;
        ctx.beginPath(); ctx.arc(px, py, 7, 0, Math.PI * 2);
        ctx.fill(); ctx.stroke();

        ctx.fillStyle     = 'white';
        ctx.font          = 'bold 10px sans-serif';
        ctx.textAlign     = 'center';
        ctx.textBaseline  = 'middle';
        ctx.fillText(i + 1, px, py);
        ctx.textAlign    = 'left';
        ctx.textBaseline = 'alphabetic';
    });

    // ---- Línea y resultado de medición ----
    if (puntosM.length === 2) {
        const { x: px1, y: py1 } = mmAPx(puntosM[0].x, puntosM[0].y);
        const { x: px2, y: py2 } = mmAPx(puntosM[1].x, puntosM[1].y);

        ctx.strokeStyle = '#805ad5';
        ctx.lineWidth   = 2;
        ctx.setLineDash([6, 3]);
        ctx.beginPath(); ctx.moveTo(px1, py1); ctx.lineTo(px2, py2); ctx.stroke();
        ctx.setLineDash([]);

        const dxMm  = Math.abs(puntosM[1].x - puntosM[0].x);
        const dyMm  = Math.abs(puntosM[1].y - puntosM[0].y);
        const dt    = (dxMm / 25).toFixed(3);
        const dv    = (dyMm / 10).toFixed(3);
        const dist  = Math.sqrt(dxMm * dxMm + dyMm * dyMm).toFixed(2);

        const mx = (px1 + px2) / 2, my = (py1 + py2) / 2;
        const bW = 186, bH = 66;
        const bX = Math.max(4, Math.min(W - bW - 4, mx - bW / 2));
        const bY = Math.max(4, Math.min(H - bH - 4, my - bH - 12));

        ctx.fillStyle   = 'rgba(237,233,254,0.95)';
        ctx.strokeStyle = 'rgba(128,90,213,0.7)';
        ctx.lineWidth   = 1.5;
        ctx.beginPath(); rrect(ctx, bX, bY, bW, bH, 6); ctx.fill(); ctx.stroke();

        ctx.fillStyle = '#44337a';
        ctx.font      = 'bold 11px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`Δt = ${dt} s  (${dxMm.toFixed(1)} mm)`,  bX + bW / 2, bY + 18);
        ctx.fillText(`ΔV = ${dv} mV  (${dyMm.toFixed(1)} mm)`, bX + bW / 2, bY + 34);
        ctx.fillText(`Distancia = ${dist} mm`,                       bX + bW / 2, bY + 52);
        ctx.textAlign = 'left';

        document.getElementById('info-medicion').textContent =
            `Δt=${dt}s · ΔV=${dv}mV · Dist=${dist}mm`;
    }
}

// ---- Abrir el modal ----

function abrirModalZoom(label, datos, fs) {
    datosZoom = datos;
    labelZoom = label;
    fsZoom    = fs;
    vista     = { x: 0, y: 0, ancho: 75, alto: 50 };
    modoMedicion   = false;
    puntosM        = [];
    cursorMmActual = null;

    document.getElementById('modal-zoom').style.display = 'flex';
    document.getElementById('modal-zoom-label').textContent = `Derivación ${label}`;
    document.getElementById('zoom-nivel').textContent = '1×';
    document.getElementById('info-cursor').textContent = 'Mueve el cursor sobre la gráfica';
    document.getElementById('info-medicion').textContent = '';
    document.getElementById('modo-medicion-label').style.display = 'none';
    document.getElementById('btn-medir').classList.remove('btn-medir-activo');

    requestAnimationFrame(renderZoom);
}

// ---- Inicializar eventos del modal (se llama una sola vez) ----

function inicializarModalZoom() {
    const modal  = document.getElementById('modal-zoom');
    const canvas = document.getElementById('canvas-zoom');

    // Cerrar
    document.getElementById('btn-cerrar-modal').addEventListener('click',
        () => { modal.style.display = 'none'; });
    modal.addEventListener('click', e => {
        if (e.target === modal) modal.style.display = 'none';
    });

    // Zoom +/-
    document.getElementById('btn-zoom-mas').addEventListener('click', () => {
        aplicarZoom(0.55, vista.x + vista.ancho / 2, vista.y + vista.alto / 2);
        renderZoom();
    });
    document.getElementById('btn-zoom-menos').addEventListener('click', () => {
        aplicarZoom(1.6, vista.x + vista.ancho / 2, vista.y + vista.alto / 2);
        renderZoom();
    });

    // Reset
    document.getElementById('btn-reset-zoom').addEventListener('click', () => {
        vista = { x: 0, y: 0, ancho: 75, alto: 50 };
        document.getElementById('zoom-nivel').textContent = '1×';
        modoMedicion = false; puntosM = [];
        document.getElementById('btn-medir').classList.remove('btn-medir-activo');
        document.getElementById('modo-medicion-label').style.display = 'none';
        document.getElementById('info-medicion').textContent = '';
        canvas.style.cursor = 'grab';
        renderZoom();
    });

    // Herramienta de medición
    document.getElementById('btn-medir').addEventListener('click', () => {
        modoMedicion = !modoMedicion;
        puntosM = [];
        document.getElementById('info-medicion').textContent = '';
        document.getElementById('btn-medir').classList.toggle('btn-medir-activo', modoMedicion);
        document.getElementById('modo-medicion-label').style.display =
            modoMedicion ? 'inline' : 'none';
        canvas.style.cursor = modoMedicion ? 'crosshair' : 'grab';
        renderZoom();
    });

    // Scroll = zoom centrado en cursor
    canvas.addEventListener('wheel', e => {
        e.preventDefault();
        const rect = canvas.getBoundingClientRect();
        const mm   = canvasAMm(e.clientX - rect.left, e.clientY - rect.top);
        aplicarZoom(e.deltaY > 0 ? 1.22 : 0.82, mm.x, mm.y);
        renderZoom();
    }, { passive: false });

    // Movimiento del mouse: crosshair + pan
    canvas.addEventListener('mousemove', e => {
        const rect = canvas.getBoundingClientRect();
        const cx   = e.clientX - rect.left;
        const cy   = e.clientY - rect.top;
        cursorMmActual = canvasAMm(cx, cy);

        if (arrastrandoZoom && !modoMedicion) {
            const dxMm = (arrastreZoom.cx0 - cx) / canvas.offsetWidth  * vista.ancho;
            const dyMm = (arrastreZoom.cy0 - cy) / canvas.offsetHeight * vista.alto;
            vista.x = arrastreZoom.vx0 + dxMm;
            vista.y = arrastreZoom.vy0 + dyMm;
        }
        renderZoom();
    });

    canvas.addEventListener('mouseleave', () => {
        cursorMmActual = null;
        document.getElementById('info-cursor').textContent = 'Mueve el cursor sobre la gráfica';
        renderZoom();
    });

    canvas.addEventListener('mousedown', e => {
        if (modoMedicion) return;
        arrastrandoZoom = true;
        const rect = canvas.getBoundingClientRect();
        arrastreZoom = {
            cx0: e.clientX - rect.left,
            cy0: e.clientY - rect.top,
            vx0: vista.x, vy0: vista.y
        };
        canvas.style.cursor = 'grabbing';
    });

    canvas.addEventListener('mouseup',   () => {
        arrastrandoZoom = false;
        canvas.style.cursor = modoMedicion ? 'crosshair' : 'grab';
    });

    // Click = colocar punto de medición
    canvas.addEventListener('click', e => {
        if (!modoMedicion) return;
        const rect = canvas.getBoundingClientRect();
        const mm   = canvasAMm(e.clientX - rect.left, e.clientY - rect.top);
        if (puntosM.length >= 2) {
            puntosM = [];
            document.getElementById('info-medicion').textContent = '';
        }
        puntosM.push(mm);
        if (puntosM.length === 1)
            document.getElementById('info-medicion').textContent = 'Haz clic en el segundo punto...';
        renderZoom();
    });

    // Pinch-to-zoom en móvil
    let lastPinchDist = null;
    canvas.addEventListener('touchstart', e => {
        if (e.touches.length === 2) {
            const dx = e.touches[0].clientX - e.touches[1].clientX;
            const dy = e.touches[0].clientY - e.touches[1].clientY;
            lastPinchDist = Math.hypot(dx, dy);
        }
    }, { passive: true });

    canvas.addEventListener('touchmove', e => {
        e.preventDefault();
        if (e.touches.length === 2 && lastPinchDist) {
            const dx   = e.touches[0].clientX - e.touches[1].clientX;
            const dy   = e.touches[0].clientY - e.touches[1].clientY;
            const dist = Math.hypot(dx, dy);
            const rect = canvas.getBoundingClientRect();
            const midX = (e.touches[0].clientX + e.touches[1].clientX) / 2 - rect.left;
            const midY = (e.touches[0].clientY + e.touches[1].clientY) / 2 - rect.top;
            const mm   = canvasAMm(midX, midY);
            aplicarZoom(lastPinchDist / dist, mm.x, mm.y);
            lastPinchDist = dist;
            renderZoom();
        }
    }, { passive: false });

    canvas.addEventListener('touchend', () => { lastPinchDist = null; });

    // Atajos de teclado
    document.addEventListener('keydown', e => {
        if (modal.style.display === 'none') return;
        const cx = vista.x + vista.ancho / 2, cy = vista.y + vista.alto / 2;
        const paso = vista.ancho * 0.12;
        switch (e.key) {
            case 'Escape':  modal.style.display = 'none'; break;
            case '+': case '=': aplicarZoom(0.6, cx, cy); renderZoom(); break;
            case '-':           aplicarZoom(1.5, cx, cy); renderZoom(); break;
            case 'ArrowLeft':  vista.x -= paso; renderZoom(); break;
            case 'ArrowRight': vista.x += paso; renderZoom(); break;
            case 'ArrowUp':    vista.y -= paso * (50/75); renderZoom(); break;
            case 'ArrowDown':  vista.y += paso * (50/75); renderZoom(); break;
            case 'm': case 'M': document.getElementById('btn-medir').click(); break;
        }
    });

    // Redimensionar ventana
    window.addEventListener('resize', () => {
        if (modal.style.display !== 'none') renderZoom();
    });
}

// ================================================================
//  MONITOR-BOT — ASISTENTE IA CON CONTEXTO DE PACIENTE
// ================================================================

let _historialChat     = [];
let _chatUltimoPaciente = null;

function inicializarChat() {
    document.getElementById('chat-toggle').addEventListener('click', () => _toggleChat(true));
    document.getElementById('chat-cerrar').addEventListener('click', () => _toggleChat(false));
    document.getElementById('chat-enviar').addEventListener('click', enviarMensajeChat);
    document.getElementById('chat-input').addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); enviarMensajeChat(); }
    });
    _agregarBurbuja('bot',
        '¡Hola! Soy <strong>Monitor-Bot</strong>, tu instructor de ECG.<br>' +
        'He cargado el paciente actual en mi contexto. ¿Qué observas en el trazo?'
    );
}

function _toggleChat(abrir) {
    document.getElementById('chat-panel').style.display  = abrir ? 'flex' : 'none';
    document.getElementById('chat-toggle').style.display = abrir ? 'none' : 'flex';
    if (abrir) _scrollAbajo();
}

function limpiarChatContexto() {
    _historialChat = [];
    document.getElementById('chat-mensajes').innerHTML = '';
    _agregarBurbuja('bot',
        '&#128260; <strong>Nuevo paciente cargado.</strong> He actualizado mi contexto. ' +
        '¿Qué llama tu atención en este nuevo ECG?'
    );
}

function _agregarBurbuja(tipo, html) {
    const cont    = document.getElementById('chat-mensajes');
    const burbuja = document.createElement('div');
    burbuja.className   = `chat-burbuja chat-burbuja-${tipo}`;
    burbuja.innerHTML   = html;
    cont.appendChild(burbuja);
    _scrollAbajo();
}

function _scrollAbajo() {
    const cont = document.getElementById('chat-mensajes');
    cont.scrollTop = cont.scrollHeight;
}

function _escaparHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

async function enviarMensajeChat() {
    const input   = document.getElementById('chat-input');
    const enviar  = document.getElementById('chat-enviar');
    const typing  = document.getElementById('chat-typing');
    const mensaje = input.value.trim();
    if (!mensaje) return;

    input.value      = '';
    input.disabled   = true;
    enviar.disabled  = true;

    _agregarBurbuja('user', _escaparHtml(mensaje));
    typing.style.display = 'flex';
    _scrollAbajo();

    try {
        const resp = await fetch('/api/chat', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                mensaje,
                paciente_id:     pacienteActual,
                historial:       _historialChat,
                contexto_visual: {
                    cara_seleccionada:    caraSeleccionada,
                    caras_auto_resaltadas: [...carasAutoResaltadas],
                    lead_zoom: (document.getElementById('modal-zoom').style.display !== 'none')
                               ? labelZoom : null,
                }
            })
        });
        const data = await resp.json();
        typing.style.display = 'none';

        if (data.error) {
            _agregarBurbuja('bot', `&#9888;&#65039; ${_escaparHtml(data.error)}`);
        } else {
            _historialChat.push({ rol: 'user',  texto: mensaje });
            _historialChat.push({ rol: 'model', texto: data.respuesta });
            // Limitar historial a los últimos 20 intercambios (40 mensajes)
            if (_historialChat.length > 40) _historialChat = _historialChat.slice(-40);
            _agregarBurbuja('bot', data.respuesta);
        }
    } catch {
        typing.style.display = 'none';
        _agregarBurbuja('bot', '&#9888;&#65039; Error de conexión. Verifica que el servidor esté activo.');
    } finally {
        input.disabled  = false;
        enviar.disabled = false;
        input.focus();
    }
}