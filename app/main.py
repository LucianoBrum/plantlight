from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.routers import location, species
from app.template_engine import templates
from app.i18n import get_lang

app = FastAPI(title="PlantLight", version="0.1.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(location.router)
app.include_router(species.router)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"lang": get_lang(request)})


@app.get("/species")
async def species_page(request: Request):
    return templates.TemplateResponse(request, "species_search.html", {"lang": get_lang(request)})


@app.post("/set-lang")
async def set_lang(request: Request):
    body = await request.json()
    lang = body.get("lang", "es")
    if lang not in ("es", "en"):
        lang = "es"
    resp = JSONResponse({"ok": True})
    resp.set_cookie("lang", lang, max_age=60 * 60 * 24 * 365, samesite="lax")
    return resp


@app.get("/api/health")
async def health():
    return {"status": "ok"}
