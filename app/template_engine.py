"""Instancia compartida de Jinja2Templates para toda la app."""
import json
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

# Filtro tojson para pasar datos a JavaScript desde templates
templates.env.filters["tojson"] = lambda v: json.dumps(v)
