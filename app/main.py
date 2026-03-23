from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request

from app.routers import location, species
from app.template_engine import templates

app = FastAPI(title="PlantLight", version="0.1.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(location.router)
app.include_router(species.router)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/species")
async def species_page(request: Request):
    return templates.TemplateResponse(request, "species_search.html")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
