# CLAUDE.md — Proyecto "PlantLight"

## Identidad del proyecto

Sos el asistente de desarrollo para **PlantLight**, una aplicación web que muestra la calidad de luz solar disponible para plantas según la ubicación geográfica del usuario y la época del año. El proyecto es 100% Python con deploy gratuito.

---

## Stack técnico

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: Templates Jinja2 servidos por FastAPI + HTMX para interactividad sin escribir JS frameworks. CSS vanilla con variables custom. Charts con Chart.js o Plotly.js (cargados por CDN).
- **Base de datos**: SQLite para datos de especies (archivo local, sin servidor externo)
- **Deploy**: Render free tier (web service). Alternativa: Railway free tier.
- **Geolocalización**: API del navegador (`navigator.geolocation`) para obtener lat/lon del usuario.
- **Datos solares**: Cálculos astronómicos con la librería `pvlib` (o `astropy`/`ephem` como fallback) para calcular posición solar, ángulo de elevación, masa de aire y espectro solar estimado.

---

## Arquitectura del proyecto

```
plantlight/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, rutas principales
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── location.py       # Endpoints de análisis por ubicación
│   │   └── species.py        # Endpoints de búsqueda de especies
│   ├── services/
│   │   ├── __init__.py
│   │   ├── solar.py          # Cálculos solares (posición, espectro, PAR)
│   │   ├── light_quality.py  # Evaluación de calidad de luz para plantas
│   │   └── species_db.py     # Consultas a la DB de especies
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py        # Pydantic models para request/response
│   ├── data/
│   │   ├── species.db        # SQLite con datos de especies
│   │   └── seed_species.py   # Script para popular la DB inicial
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   └── app.js        # Geolocalización + llamadas HTMX + charts
│   │   └── img/
│   └── templates/
│       ├── base.html          # Layout base
│       ├── index.html         # Página principal con mapa de luz
│       ├── partials/
│       │   ├── light_report.html    # Reporte de calidad de luz (HTMX partial)
│       │   ├── spectrum_chart.html  # Gráfico de espectro (partial)
│       │   └── species_card.html    # Card de especie individual (partial)
│       └── species_search.html      # Página de búsqueda de especies
├── tests/
│   ├── test_solar.py
│   ├── test_light_quality.py
│   └── test_api.py
├── requirements.txt
├── Dockerfile              # Para deploy en Render
├── render.yaml             # Config de Render (opcional)
├── .env.example
├── README.md
└── CLAUDE.md               # Este archivo
```

---

## Modelo de datos de especies (SQLite)

```sql
CREATE TABLE species (
    id INTEGER PRIMARY KEY,
    common_name TEXT NOT NULL,
    scientific_name TEXT NOT NULL UNIQUE,
    family TEXT,
    light_requirement TEXT CHECK(light_requirement IN ('full_sun', 'partial_shade', 'full_shade', 'variable')),
    par_min_umol REAL,            -- PAR mínimo útil (µmol/m²/s)
    par_optimal_umol REAL,        -- PAR óptimo
    par_max_umol REAL,            -- PAR máximo tolerable
    dli_min REAL,                 -- Daily Light Integral mínimo (mol/m²/día)
    dli_optimal REAL,             -- DLI óptimo
    photoperiod_type TEXT CHECK(photoperiod_type IN ('short_day', 'long_day', 'day_neutral')),
    key_wavelengths_json TEXT,    -- JSON: {"red_660": 0.9, "blue_450": 0.7, "far_red_730": 0.3, ...}
    physiological_notes TEXT,     -- Texto: qué procesos benefician qué longitudes de onda
    description TEXT,
    image_url TEXT
);

CREATE VIRTUAL TABLE species_fts USING fts5(common_name, scientific_name, family);
```

La tabla `species_fts` permite búsqueda full-text rápida desde el buscador.

Seed inicial: incluir al menos 15-20 especies comunes (tomate, lechuga, cannabis, rosa, lavanda, albahaca, ficus, pothos, monstera, suculentas, orquídea, pimiento, frutilla, girasol, helecho, etc). Los datos PAR/DLI deben basarse en literatura agronómica real.

---

## Lógica core: servicio solar (`services/solar.py`)

Usando `pvlib`, calcular para una latitud/longitud y fecha/hora dadas:

1. **Posición solar**: azimut, elevación, zenith.
2. **Masa de aire (AM)**: con `pvlib.atmosphere.get_relative_airmass()`.
3. **Espectro solar estimado**: usar el modelo de espectro de referencia AM1.5 y ajustarlo por la masa de aire real. Esto da la distribución de longitudes de onda (W/m²/nm) que llega a la superficie.
4. **PAR (Photosynthetically Active Radiation)**: integrar el espectro entre 400-700nm y convertir a µmol/m²/s.
5. **Componentes espectrales clave para plantas**:
   - UV-A (320-400nm): estrés, producción de antocianinas
   - Azul (400-500nm): fototropismo, apertura estomática, crecimiento compacto
   - Verde (500-600nm): penetración en canopia, fotosíntesis profunda
   - Rojo (600-700nm): fotosíntesis primaria (pico clorofila)
   - Rojo lejano (700-750nm): respuesta fitocromo, elongación, floración
6. **DLI estimado**: extrapolar el PAR instantáneo al Daily Light Integral considerando las horas de sol del día.
7. **Ratio Rojo/Rojo lejano (R:FR)**: indicador clave de calidad de luz.

---

## Lógica core: calidad de luz (`services/light_quality.py`)

Recibe los datos del servicio solar y genera un reporte:

- **Score general de calidad** (0-100): ponderando PAR, distribución espectral, duración del día.
- **Desglose por banda espectral**: porcentaje de cada banda respecto al total PAR.
- **Procesos fisiológicos activos**: mapear cada banda a los procesos que beneficia:
  - Azul → fototropismo, regulación estomática, inhibición de elongación
  - Rojo → fotosíntesis (Clorofila a y b), fotoperiodismo
  - Rojo lejano → fitocromo Pfr→Pr, respuesta de sombra, inducción floral en plantas de día corto
  - UV-A → biosíntesis de flavonoides, engrosamiento de cutícula
  - Verde → fotosíntesis en hojas internas de la canopia
- **Comparación con especie**: si se pasa una especie, comparar el PAR/DLI actual contra los rangos de la especie y dar recomendaciones.

---

## Endpoints API

```
GET  /                          → Página principal (template index.html)
GET  /species                   → Página de búsqueda de especies

# API endpoints (responden HTML partials para HTMX o JSON si Accept: application/json)
POST /api/light-report          → Body: {lat, lon, datetime?} → Reporte de luz
GET  /api/spectrum/{lat}/{lon}  → Datos de espectro para gráfico
GET  /api/species/search?q=...  → Búsqueda de especies (FTS)
GET  /api/species/{id}          → Detalle de especie
POST /api/species/{id}/light    → Body: {lat, lon} → Reporte de luz para esa especie
GET  /api/health                → Healthcheck para Render
```

---

## Frontend: comportamiento esperado

### Página principal (`/`)
1. Al cargar, pedir geolocalización al navegador.
2. Mostrar un **indicador de calidad de luz** grande y visual (gauge, termómetro, o similar) con el score 0-100.
3. Debajo, un **gráfico de espectro** (Chart.js o Plotly): eje X = longitud de onda (nm), eje Y = irradiancia relativa. Las bandas coloreadas según su color real (UV violeta, azul, verde, rojo, etc).
4. Una sección de **procesos fisiológicos**: cards o lista visual mostrando qué procesos están más activos según la luz actual.
5. Un **resumen del día**: horas de sol, DLI estimado, PAR actual, ratio R:FR.
6. Un selector de fecha/hora para simular otros momentos del año.
7. Un botón/link "Ver por especie" que lleva al buscador.

### Buscador de especies (`/species`)
1. Input de búsqueda con autocomplete (HTMX: `hx-trigger="keyup changed delay:300ms"`).
2. Resultados como cards con nombre común, nombre científico, imagen.
3. Al hacer click en una especie: se abre un detalle que muestra:
   - Datos de la especie (requerimientos de luz)
   - El mismo reporte de luz pero **comparado**: "Tu luz actual: X µmol — Esta especie necesita: Y µmol"
   - Gráfico de espectro con overlay de las bandas que más le importan a esa especie.
   - Recomendaciones: "Buena ubicación" / "Necesita más luz" / "Cuidado, exceso de luz".

### Diseño visual
- Estética **orgánica/botánica**: tonos verdes oscuros, cremas, acentos en ámbar/dorado.
- Tipografía: una display con carácter (ej: "Fraunces", "Playfair Display") + una sans limpia para cuerpo (ej: "DM Sans", "Outfit").
- El gráfico de espectro debe ser el hero visual de la app: grande, con gradientes que representen los colores reales de cada longitud de onda.
- Responsive: funcionar bien en móvil (la mayoría va a usarlo desde el teléfono en su balcón/jardín).
- Dark mode NO es prioridad. Mantener tema claro con acentos naturales.

---

## Testing

- `tests/test_solar.py`: testear cálculos solares con coordenadas y fechas conocidas (ej: Buenos Aires, 21 de diciembre mediodía → elevación solar alta; 21 de junio → baja).
- `tests/test_light_quality.py`: testear que el score y desglose espectral son coherentes.
- `tests/test_api.py`: tests de integración con TestClient de FastAPI.
- Correr tests con: `pytest tests/ -v`

---

## Deploy en Render (free tier)

1. El `Dockerfile` debe:
   - Usar `python:3.11-slim`
   - Instalar dependencias de `requirements.txt`
   - Exponer puerto 10000 (default de Render)
   - CMD: `uvicorn app.main:app --host 0.0.0.0 --port 10000`

2. `render.yaml` (Blueprint):
```yaml
services:
  - type: web
    name: plantlight
    runtime: docker
    plan: free
    envVars:
      - key: PYTHON_ENV
        value: production
```

3. La DB SQLite se incluye en el repo (es chica y de solo lectura en producción).

---

## Reglas de desarrollo

1. **Paso a paso**: no generar todo de una. Seguir este orden:
   - Primero: setup del proyecto, `requirements.txt`, estructura de carpetas.
   - Segundo: servicio solar (`solar.py`) + tests.
   - Tercero: servicio de calidad de luz (`light_quality.py`) + tests.
   - Cuarto: base de datos de especies + seed.
   - Quinto: API endpoints + tests de integración.
   - Sexto: frontend templates + CSS + JS.
   - Séptimo: Dockerfile + config deploy.
   - Octavo: testing E2E, pulir, documentar.

2. **Cada módulo debe tener tests** antes de pasar al siguiente.

3. **Commits atómicos**: un commit por cada paso completado.

4. **Código limpio**: type hints en todo Python, docstrings en funciones públicas, Pydantic para validación.

5. **Sin APIs externas pagas**: todo el cálculo solar es local con `pvlib`. No depender de APIs de clima o sol que requieran API key.

6. **Español**: los comentarios y docstrings pueden ser en inglés, pero toda la UI (textos, labels, tooltips) debe estar en **español**.

7. **requirements.txt** mínimo:
   ```
   fastapi>=0.104.0
   uvicorn[standard]>=0.24.0
   jinja2>=3.1.2
   pvlib>=0.10.0
   pandas>=2.1.0
   numpy>=1.25.0
   pydantic>=2.5.0
   aiosqlite>=0.19.0
   pytest>=7.4.0
   httpx>=0.25.0
   ```

---

## Contexto importante

- El usuario principal está en Buenos Aires, Argentina (-34.6, -58.4). Usar esas coordenadas como default/fallback si la geolocalización falla.
- La app debe funcionar para **cualquier ubicación del mundo**.
- Los datos de especies se van a ampliar después. El schema debe ser extensible.
- Prioridad: que funcione bien y sea visualmente atractivo. Perfección científica es secundaria (pero los cálculos deben ser razonables y basados en modelos reales).

---

## Cómo usar este archivo

Este es tu `CLAUDE.md`. Al iniciar Claude Code en el directorio del proyecto, va a leer este archivo automáticamente y tener todo el contexto. Trabajá paso a paso siguiendo el orden de la sección "Reglas de desarrollo". Ante dudas, preguntá antes de asumir.