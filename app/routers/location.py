"""
Router de endpoints de análisis de luz por ubicación.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.models.schemas import LightReportRequest
from app.services import solar, light_quality
from app.template_engine import templates
from app.i18n import get_lang

router = APIRouter(prefix="/api", tags=["location"])


@router.post("/light-report")
async def light_report(payload: LightReportRequest, request: Request):
    """
    Genera un reporte completo de calidad de luz para una ubicación.

    Acepta JSON y devuelve HTML partial (HTMX) o JSON según el header Accept.
    """
    metrics = solar.get_light_metrics(
        lat=payload.lat,
        lon=payload.lon,
        dt=payload.dt,
    )
    report = light_quality.build_light_report(metrics)

    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            request, "partials/light_report.html", {"report": report, "lang": get_lang(request)},
        )
    return JSONResponse(content=report)


@router.get("/spectrum/{lat}/{lon}")
async def spectrum(lat: float, lon: float, dt: Optional[str] = None):
    """
    Devuelve los datos de espectro solar para graficar.

    Parámetro opcional `dt` en formato ISO 8601.
    """
    parsed_dt: Optional[datetime] = None
    if dt:
        try:
            parsed_dt = datetime.fromisoformat(dt)
        except ValueError:
            pass

    spec = solar.get_spectrum(lat=lat, lon=lon, dt=parsed_dt)
    return {
        "wavelengths": spec["wavelengths"],
        "irradiance": spec["irradiance"],
        "sun_is_up": spec["sun_is_up"],
        "airmass": spec["airmass"],
        "solar_position": spec["solar_position"],
    }
