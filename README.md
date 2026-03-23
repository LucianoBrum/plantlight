# 🌿 PlantLight

Aplicación web que muestra la calidad de luz solar disponible para plantas según la ubicación geográfica del usuario y la época del año.

## Stack

- **Backend**: FastAPI (Python 3.11)
- **Frontend**: Jinja2 + HTMX + Chart.js
- **Base de datos**: SQLite (especies)
- **Cálculos solares**: pvlib (Spectrl2)
- **Deploy**: Render (Docker, free tier)

## Funcionalidades

- Detecta la ubicación del usuario (geolocalización del navegador)
- Calcula posición solar, espectro, PAR, DLI y ratio R:FR en tiempo real
- Muestra un gauge de calidad de luz (0–100)
- Gráfico de espectro solar con colores reales de cada longitud de onda
- Desglose por bandas espectrales y procesos fisiológicos activos
- Buscador de especies con comparación de luz actual vs requerimientos
- Simulador de fecha/hora para cualquier momento del año

## Desarrollo local

```bash
# Crear entorno
conda create -n plantlight python=3.11 -y
conda activate plantlight
pip install -r requirements.txt

# Poblar DB de especies
python -m app.data.seed_species

# Correr servidor
uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
pytest tests/ -v
```

## Deploy

El proyecto incluye `Dockerfile` y `render.yaml` para deploy directo en [Render](https://render.com).
