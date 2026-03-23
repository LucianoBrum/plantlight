/**
 * PlantLight — app.js
 * Geolocalización, fetch del reporte de luz e inicialización de Chart.js
 */

// ─── Estado global ──────────────────────────────────────────────────────────
let currentLat = -34.6;   // Buenos Aires por defecto
let currentLon = -58.4;
let spectrumChart = null;
let dailyChart = null;

// ─── Inicialización ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    setupGeolocateButton();
    setupDatetimeButton();
    setupModalClose();
});

// ─── Botón de geolocalización ─────────────────────────────────────────────
function setupGeolocateButton() {
    const btn = document.getElementById('btn-geolocate');
    if (!btn) return;

    btn.addEventListener('click', () => {
        if (!navigator.geolocation) {
            fetchReport(-34.6, -58.4, null, 'Buenos Aires (defecto)');
            return;
        }
        btn.disabled = true;
        btn.textContent = 'Detectando…';
        showLoading(true);

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                currentLat = pos.coords.latitude;
                currentLon = pos.coords.longitude;
                btn.disabled = false;
                btn.innerHTML = '<span class="btn-icon">📍</span> Detectar mi ubicación';
                fetchReport(currentLat, currentLon);
            },
            () => {
                btn.disabled = false;
                btn.innerHTML = '<span class="btn-icon">📍</span> Detectar mi ubicación';
                fetchReport(-34.6, -58.4);   // fallback Buenos Aires
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
