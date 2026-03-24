"""Instancia compartida de Jinja2Templates para toda la app."""
import json
from fastapi.templating import Jinja2Templates
from app.i18n import t

templates = Jinja2Templates(directory="app/templates")

# Filtro tojson para pasar datos a JavaScript desde templates
templates.env.filters["tojson"] = lambda v: json.dumps(v)

# Global de traducción disponible en todos los templates como t('clave', lang)
templates.env.globals["t"] = t
