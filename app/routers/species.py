"""
Router de endpoints de búsqueda y detalle de especies.
"""

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import JSONResponse

from app.models.schemas import SpeciesLightRequest, SpeciesCompareRequest
from app.services import solar, light_quality, species_db
from app.template_engine import templates
from app.i18n import get_lang

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
            request, "partials/species_card.html", {"species_list": results, "lang": get_lang(request)},
        )
    return JSONResponse(content=results)


@router.post("/compare")
async def compare_species(payload: SpeciesCompareRequest, request: Request):
    """
    Compara dos especies lado a lado para una misma ubicación.
    Debe estar antes de /{species_id} para que Starlette no lo capture primero.
    """
    sp1 = await species_db.get_species_by_id(payload.species_id_1)
    sp2 = await species_db.get_species_by_id(payload.species_id_2)
    if sp1 is None or sp2 is None:
        raise HTTPException(status_code=404, detail="Especie no encontrada")

    metrics = solar.get_light_metrics(lat=payload.lat, lon=payload.lon)
    comp1 = light_quality.compare_with_species(metrics, sp1)
    comp2 = light_quality.compare_with_species(metrics, sp2)

    context = {
        "metrics": metrics,
        "species1": sp1,
        "species2": sp2,
        "comp1": comp1,
        "comp2": comp2,
    }

    context["lang"] = get_lang(request)
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(request, "partials/species_compare.html", context)
    return JSONResponse(content=context)


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
            request, "partials/light_report.html", {"report": report, "species": sp, "lang": get_lang(request)},
        )
    return JSONResponse(content=report)
