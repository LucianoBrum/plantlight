/**
 * PlantLight — app.js
 * Mapa Leaflet, geolocalización, fetch del reporte de luz e inicialización de Chart.js
 */

// ─── Estado global ──────────────────────────────────────────────────────────
let currentLat = -34.6;   // Buenos Aires por defecto
let currentLon = -58.4;
let spectrumChart = null;
let dailyChart = null;
let map = null;
let marker = null;

// ─── Inicialización ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    setupGeolocateButton();
    setupDatetimeButton();
    setupModalClose();
});

// ─── Mapa Leaflet ─────────────────────────────────────────────────────────
function initMap() {
    const mapEl = document.getElementById('map');
    if (!mapEl || typeof L === 'undefined') return;

    map = L.map('map').setView([currentLat, currentLon], 4);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a>',
        maxZoom: 18,
    }).addTo(map);

    // Icono personalizado (verde)
    const greenIcon = L.divIcon({
        html: '<div class="map-marker-pin"></div>',
        className: '',
        iconSize: [22, 22],
        iconAnchor: [11, 11],
    });

    marker = L.marker([currentLat, currentLon], { icon: greenIcon, draggable: true }).addTo(map);
    updateCoordsDisplay(currentLat, currentLon);

    // Click en el mapa → mover marcador y cargar reporte
    map.on('click', (e) => {
        const { lat, lng } = e.latlng;
        moveMarker(lat, lng);
        fetchReport(lat, lng);
    });

    // Drag del marcador
    marker.on('dragend', () => {
        const { lat, lng } = marker.getLatLng();
        currentLat = lat;
        currentLon = lng;
        updateCoordsDisplay(lat, lng);
        fetchReport(lat, lng);
    });
}

function moveMarker(lat, lng) {
    currentLat = lat;
    currentLon = lng;
    if (marker) marker.setLatLng([lat, lng]);
    if (map) map.panTo([lat, lng]);
    updateCoordsDisplay(lat, lng);
}

async function reverseGeocode(lat, lng) {
    try {
        const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`,
            { headers: { 'Accept-Language': 'es' } }
        );
        const data = await res.json();
        const city    = data.address?.city || data.address?.town || data.address?.village || '';
        const country = data.address?.country_code?.toUpperCase() || '';
        return city && country ? `${city}, ${country}` : null;
    } catch {
        return null;
    }
}

function updateCoordsDisplay(lat, lng) {
    const el = document.getElementById('coords-display');
    if (!el) return;
    const latStr = lat.toFixed(2);
    const lngStr = lng.toFixed(2);
    el.textContent = `(${latStr}, ${lngStr})`;
    // Intentar reverse geocoding en background
    reverseGeocode(lat, lng).then(name => {
        if (name && el) el.textContent = `${name} (${latStr}, ${lngStr})`;
    });
}

// ─── Botón de geolocalización ─────────────────────────────────────────────
function setupGeolocateButton() {
    const btn = document.getElementById('btn-geolocate');
    if (!btn) return;

    btn.addEventListener('click', () => {
        if (!navigator.geolocation) {
            moveMarker(-34.6, -58.4);
            fetchReport(-34.6, -58.4);
            return;
        }
        btn.disabled = true;
        btn.innerHTML = '<span class="btn-icon">⏳</span> Detectando…';

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const { latitude, longitude } = pos.coords;
                btn.disabled = false;
                btn.innerHTML = '<span class="btn-icon">📍</span> Mi ubicación';
                moveMarker(latitude, longitude);
                if (map) map.setView([latitude, longitude], 10);
                fetchReport(latitude, longitude);
            },
            () => {
                btn.disabled = false;
                btn.innerHTML = '<span class="btn-icon">📍</span> Mi ubicación';
                moveMarker(-34.6, -58.4);
                fetchReport(-34.6, -58.4);
            },
            { timeout: 8000 }
        );
    });
}

// ─── Botón de fecha/hora ──────────────────────────────────────────────────
function setupDatetimeButton() {
    const btn = document.getElementById('btn-datetime');
    if (!btn) return;

    btn.addEventListener('click', () => {
        const input = document.getElementById('input-datetime');
        const dt = input?.value ? new Date(input.value).toISOString() : null;
        fetchReport(currentLat, currentLon, dt);
    });
}

// ─── Fetch del reporte ────────────────────────────────────────────────────
async function fetchReport(lat, lon, dt = null, _label = null) {
    showLoading(true);
    clearReport();

    const body = { lat, lon };
    if (dt) body.dt = dt;

    try {
        const res = await fetch('/api/light-report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'text/html',
            },
            body: JSON.stringify(body),
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const html = await res.text();

        const container = document.getElementById('light-report-container');
        if (container) {
            container.innerHTML = html;
            initSpectrumChart();
            initDailyChart();
            initGaugeColor();
        }
    } catch (err) {
        const container = document.getElementById('light-report-container');
        if (container) {
            container.innerHTML = `<div class="card" style="text-align:center;padding:2rem;color:#b84040">
                Error al obtener el reporte de luz. Intentá de nuevo.
            </div>`;
        }
    } finally {
        showLoading(false);
    }
}

// ─── Reporte de especie desde modal ──────────────────────────────────────
async function openSpeciesDetail(speciesId) {
    const modal = document.getElementById('species-modal');
    const body  = document.getElementById('modal-body');
    if (!modal || !body) return;

    modal.classList.remove('hidden');
    body.innerHTML = '<div class="loading"><div class="spinner"></div><p>Cargando…</p></div>';

    try {
        const res = await fetch(`/api/species/${speciesId}/light`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'text/html',
            },
            body: JSON.stringify({ lat: currentLat, lon: currentLon }),
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const html = await res.text();
        body.innerHTML = html;
        initSpectrumChartIn(body);
        initDailyChartIn(body);
        initGaugeColorIn(body);
    } catch {
        body.innerHTML = '<p style="color:#b84040;padding:2rem">Error al cargar el análisis.</p>';
    }
}

// ─── Modal close ─────────────────────────────────────────────────────────
function setupModalClose() {
    document.getElementById('modal-close')?.addEventListener('click', closeModal);
    document.getElementById('modal-backdrop')?.addEventListener('click', closeModal);
}

function closeModal() {
    const modal = document.getElementById('species-modal');
    modal?.classList.add('hidden');
    // Destruir chart del modal si existe
    if (window._modalChart) { window._modalChart.destroy(); window._modalChart = null; }
    if (window._modalDailyChart) { window._modalDailyChart.destroy(); window._modalDailyChart = null; }
}

// ─── Inicializar Chart.js ────────────────────────────────────────────────
function initSpectrumChart() {
    initSpectrumChartIn(document);
}

function initSpectrumChartIn(root) {
    const canvas = root.querySelector('#spectrum-chart');
    if (!canvas) return;

    // Destruir chart anterior si existe
    if (spectrumChart) { spectrumChart.destroy(); spectrumChart = null; }

    let wl, irr;
    try {
        wl  = JSON.parse(canvas.dataset.wavelengths);
        irr = JSON.parse(canvas.dataset.irradiance);
    } catch { return; }

    // Filtrar al rango 300–800 nm (lo relevante para plantas)
    const filtered = wl.reduce((acc, w, i) => {
        if (w >= 300 && w <= 800) { acc.wl.push(w); acc.irr.push(irr[i]); }
        return acc;
    }, { wl: [], irr: [] });

    const ctx = canvas.getContext('2d');

    // Gradiente que representa los colores reales del espectro
    const gradient = ctx.createLinearGradient(0, 0, canvas.offsetWidth || 600, 0);
    gradient.addColorStop(0,    'rgba(140, 0, 255, 0.7)');  // UV (~300-400nm)
    gradient.addColorStop(0.2,  'rgba(52, 152, 219, 0.85)'); // azul (~400-500nm)
    gradient.addColorStop(0.4,  'rgba(39, 174, 96, 0.85)');  // verde (~500-600nm)
    gradient.addColorStop(0.6,  'rgba(231, 76, 60, 0.85)');  // rojo (~600-700nm)
    gradient.addColorStop(0.75, 'rgba(142, 48, 48, 0.7)');   // rojo lejano (~700-750nm)
    gradient.addColorStop(1,    'rgba(100, 30, 30, 0.3)');   // IR cercano

    // Bandas de fondo
    const bandAnnotations = {
        uv:      { xMin: 300, xMax: 400, color: 'rgba(155, 89, 182, 0.06)' },
        blue:    { xMin: 400, xMax: 500, color: 'rgba(52, 152, 219, 0.06)' },
        green:   { xMin: 500, xMax: 600, color: 'rgba(39, 174, 96, 0.06)' },
        red:     { xMin: 600, xMax: 700, color: 'rgba(231, 76, 60, 0.06)' },
        farred:  { xMin: 700, xMax: 750, color: 'rgba(142, 48, 48, 0.06)' },
    };

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: filtered.wl,
            datasets: [{
                label: 'Irradiancia (W/m²/nm)',
                data: filtered.irr,
                borderColor: gradient,
                backgroundColor: gradient,
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (items) => `${items[0].label} nm`,
                        label: (item)  => `${item.raw.toFixed(3)} W/m²/nm`,
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    min: 300, max: 800,
                    title: { display: true, text: 'Longitud de onda (nm)', color: '#6b6452', font: { size: 11 } },
                    ticks: {
                        color: '#6b6452',
                        font: { size: 10 },
                        callback: (v) => `${v}nm`,
                        maxTicksLimit: 10,
                    },
                    grid: { color: 'rgba(0,0,0,0.04)' },
                },
                y: {
                    title: { display: true, text: 'W/m²/nm', color: '#6b6452', font: { size: 11 } },
                    ticks: { color: '#6b6452', font: { size: 10 } },
                    grid: { color: 'rgba(0,0,0,0.04)' },
                    beginAtZero: true,
                }
            },
        },
        plugins: [{
            // Plugin custom para pintar las bandas de fondo
            beforeDraw(chart) {
                const { ctx, scales: { x, y } } = chart;
                Object.values(bandAnnotations).forEach(({ xMin, xMax, color }) => {
                    const x1 = x.getPixelForValue(xMin);
                    const x2 = x.getPixelForValue(xMax);
                    const y1 = y.top;
                    const y2 = y.bottom;
                    ctx.save();
                    ctx.fillStyle = color;
                    ctx.fillRect(x1, y1, x2 - x1, y2 - y1);
                    ctx.restore();
                });
            }
        }]
    });

    if (root === document) {
        spectrumChart = chart;
    } else {
        window._modalChart = chart;
    }
}

// ─── Gráfico diario de PAR ───────────────────────────────────────────────
function initDailyChart() { initDailyChartIn(document); }

function initDailyChartIn(root) {
    const canvas = root.querySelector('#daily-par-chart');
    if (!canvas) return;

    if (dailyChart) { dailyChart.destroy(); dailyChart = null; }

    let hours, parValues, currentHour;
    try {
        hours       = JSON.parse(canvas.dataset.hours);
        parValues   = JSON.parse(canvas.dataset.par);
        currentHour = parseInt(canvas.dataset.currentHour);
    } catch { return; }

    // Etiquetas de hora en formato "6h", "12h", etc.
    const labels = hours.map(h => `${h}h`);

    // Punto actual resaltado
    const pointColors = hours.map(h =>
        h === currentHour ? '#2d5a27' : 'transparent'
    );
    const pointRadius = hours.map(h => h === currentHour ? 6 : 0);

    const ctx = canvas.getContext('2d');

    // Gradiente vertical: verde arriba, claro abajo
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.offsetHeight || 200);
    gradient.addColorStop(0,   'rgba(45, 90, 39, 0.35)');
    gradient.addColorStop(1,   'rgba(45, 90, 39, 0.02)');

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'PAR (µmol/m²/s)',
                data: parValues,
                borderColor: '#2d5a27',
                backgroundColor: gradient,
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius,
                pointBackgroundColor: pointColors,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (items) => `${items[0].label}`,
                        label: (item)  => `PAR: ${item.raw.toFixed(0)} µmol/m²/s`,
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#6b6452',
                        font: { size: 10 },
                        maxTicksLimit: 13,
                    },
                    grid: { color: 'rgba(0,0,0,0.04)' },
                },
                y: {
                    title: { display: true, text: 'µmol/m²/s', color: '#6b6452', font: { size: 11 } },
                    ticks: { color: '#6b6452', font: { size: 10 } },
                    grid: { color: 'rgba(0,0,0,0.04)' },
                    beginAtZero: true,
                }
            },
        },
        plugins: [{
            // Línea vertical en la hora actual
            afterDraw(chart) {
                const { ctx, scales: { x, y } } = chart;
                const idx = hours.indexOf(currentHour);
                if (idx < 0) return;
                const xPos = x.getPixelForValue(idx);
                ctx.save();
                ctx.beginPath();
                ctx.moveTo(xPos, y.top);
                ctx.lineTo(xPos, y.bottom);
                ctx.strokeStyle = 'rgba(45,90,39,0.5)';
                ctx.lineWidth = 1.5;
                ctx.setLineDash([4, 3]);
                ctx.stroke();
                ctx.restore();
            }
        }]
    });

    if (root === document) {
        dailyChart = chart;
    } else {
        window._modalDailyChart = chart;
    }
}

// ─── Color del gauge según score ────────────────────────────────────────
function initGaugeColor() { initGaugeColorIn(document); }

function initGaugeColorIn(root) {
    const gauge = root.querySelector('.gauge');
    if (!gauge) return;

    const scoreMatch = gauge.getAttribute('style')?.match(/--score:\s*(\d+)/);
    const score = scoreMatch ? parseInt(scoreMatch[1]) : 0;

    let color;
    if (score < 20)      color = '#e74c3c';
    else if (score < 40) color = '#e67e22';
    else if (score < 60) color = '#f1c40f';
    else if (score < 80) color = '#2ecc71';
    else                 color = '#27ae60';

    gauge.style.setProperty('--gauge-color', color);
}

// ─── Toggle de idioma ────────────────────────────────────────────────────
async function setLang(lang) {
    await fetch('/set-lang', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lang }),
    });
    window.location.reload();
}

// ─── Modo comparación de especies ────────────────────────────────────────
let compareMode = false;
let compareSlots = [null, null]; // [{id, name}, {id, name}]

function toggleCompareMode() {
    compareMode = !compareMode;
    const btn = document.getElementById('btn-compare-mode');
    const panel = document.getElementById('compare-panel');

    if (compareMode) {
        btn.classList.add('active');
        btn.textContent = '✕ Cancelar comparación';
        panel.classList.remove('hidden');
    } else {
        compareMode = false;
        compareSlots = [null, null];
        btn.classList.remove('active');
        btn.textContent = '⚖️ Comparar especies';
        panel.classList.add('hidden');
        clearCompareSlot(1);
        clearCompareSlot(2);
    }

    // Alternar botones en las cards ya cargadas
    document.querySelectorAll('.btn-species-detail').forEach(b => b.classList.toggle('hidden', compareMode));
    document.querySelectorAll('.btn-species-select').forEach(b => b.classList.toggle('hidden', !compareMode));
}

function selectForCompare(id, name) {
    // Si ya está seleccionada, no hacer nada
    if (compareSlots.some(s => s && s.id === id)) return;

    const slot = compareSlots[0] === null ? 0 : (compareSlots[1] === null ? 1 : -1);
    if (slot === -1) return; // ya hay 2

    compareSlots[slot] = { id, name };

    const nameEl = document.getElementById(`compare-name-${slot + 1}`);
    const clearBtn = document.getElementById(`compare-clear-${slot + 1}`);
    const slotEl = document.getElementById(`compare-slot-${slot + 1}`);

    if (nameEl) nameEl.textContent = name;
    if (clearBtn) clearBtn.classList.remove('hidden');
    if (slotEl) slotEl.classList.add('filled');

    // Marcar la card como seleccionada
    document.querySelectorAll('.species-card').forEach(card => {
        if (parseInt(card.dataset.speciesId) === id) {
            card.classList.add('compare-selected');
            card.querySelector('.btn-species-select').textContent = '✓ Seleccionada';
            card.querySelector('.btn-species-select').disabled = true;
        }
    });

    // Mostrar botón comparar si hay 2
    const runBtn = document.getElementById('btn-run-compare');
    if (compareSlots[0] && compareSlots[1] && runBtn) {
        runBtn.classList.remove('hidden');
    }
}

function clearCompareSlot(num) {
    const idx = num - 1;
    const prev = compareSlots[idx];
    compareSlots[idx] = null;

    const nameEl = document.getElementById(`compare-name-${num}`);
    const clearBtn = document.getElementById(`compare-clear-${num}`);
    const slotEl = document.getElementById(`compare-slot-${num}`);

    if (nameEl) nameEl.textContent = '—';
    if (clearBtn) clearBtn.classList.add('hidden');
    if (slotEl) slotEl.classList.remove('filled');

    // Desmarcar la card
    if (prev) {
        document.querySelectorAll('.species-card').forEach(card => {
            if (parseInt(card.dataset.speciesId) === prev.id) {
                card.classList.remove('compare-selected');
                const btn = card.querySelector('.btn-species-select');
                if (btn) { btn.textContent = '+ Seleccionar'; btn.disabled = false; }
            }
        });
    }

    document.getElementById('btn-run-compare')?.classList.add('hidden');
}

async function runComparison() {
    if (!compareSlots[0] || !compareSlots[1]) return;

    const modal = document.getElementById('species-modal');
    const body = document.getElementById('modal-body');
    if (!modal || !body) return;

    modal.classList.remove('hidden');
    body.innerHTML = '<div class="loading"><div class="spinner"></div><p>Comparando especies…</p></div>';

    try {
        const res = await fetch('/api/species/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'text/html' },
            body: JSON.stringify({
                lat: currentLat,
                lon: currentLon,
                species_id_1: compareSlots[0].id,
                species_id_2: compareSlots[1].id,
            }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        body.innerHTML = await res.text();
    } catch {
        body.innerHTML = '<p style="color:#b84040;padding:2rem">Error al comparar las especies.</p>';
    }
}

// Al cargar nuevas cards, sincronizar visibilidad de botones
document.addEventListener('htmx:afterSwap', (e) => {
    if (!e.target || e.target.id !== 'species-results') return;
    document.querySelectorAll('.btn-species-detail').forEach(b => b.classList.toggle('hidden', compareMode));
    document.querySelectorAll('.btn-species-select').forEach(b => b.classList.toggle('hidden', !compareMode));
    // Re-marcar cards ya seleccionadas
    compareSlots.forEach(slot => {
        if (!slot) return;
        document.querySelectorAll('.species-card').forEach(card => {
            if (parseInt(card.dataset.speciesId) === slot.id) {
                card.classList.add('compare-selected');
                const btn = card.querySelector('.btn-species-select');
                if (btn) { btn.textContent = '✓ Seleccionada'; btn.disabled = true; }
            }
        });
    });
});

// ─── Helpers UI ──────────────────────────────────────────────────────────
function showLoading(show) {
    const el = document.getElementById('loading');
    if (el) el.classList.toggle('hidden', !show);
}

function clearReport() {
    const container = document.getElementById('light-report-container');
    if (container) container.innerHTML = '';
    if (spectrumChart) { spectrumChart.destroy(); spectrumChart = null; }
    if (dailyChart)    { dailyChart.destroy();    dailyChart = null;    }
}
