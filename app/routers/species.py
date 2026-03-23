"""
Router de endpoints de búsqueda y detalle de especies.
"""

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import JSONResponse

from app.models.schemas import SpeciesLightRequest
from app.services import solar, light_quality, species_db
from app.template_engine import templates

router = APIRouter(prefix="/api/species", tags=["species"])


@router.get("/search")
async def search(request: Request, q: str = Query(default="")):
    """
    Búsqueda full-text de especies.

    Devuelve HTML partial (HTMX) o JSON según el header Accept.
    """
    results = await species_db.search_species(q, limit=20)

    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            request, "partials/species_card.html", {"species_list": results},
        )
    return JSONResponse(content=results)


@router.get("/{species_id}")
async def get_species(species_id: int):
    """Devuelve el detalle de una especie por ID."""
    sp = await species_db.get_species_by_id(species_id)
    if sp is None:
        raise HTTPException(status_code=404, detail="Especie no encontrada")
    return JSONResponse(content=sp)


@router.post("/{species_id}/light")
async def species_light(species_id: int, payload: SpeciesLightRequest, request: Request):
    """
    Reporte de luz para una especie específica en una ubicación.

    Compara la luz actual con los requerimientos de la especie.
    """
    sp = await species_db.get_species_by_id(species_id)
    if sp is None:
        raise HTTPException(status_code=404, detail="Especie no encontrada")

    metrics = solar.get_light_metrics(lat=payload.lat, lon=payload.lon)
    report = light_quality.build_light_report(metrics, species=sp)

    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            request, "partials/light_report.html", {"report": report, "species": sp},
        )
    return JSONResponse(content=report)
