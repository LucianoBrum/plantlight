from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LightReportRequest(BaseModel):
    lat: float
    lon: float
    dt: Optional[datetime] = None


class SpeciesLightRequest(BaseModel):
    lat: float
    lon: float


class SpeciesCompareRequest(BaseModel):
    lat: float
    lon: float
    species_id_1: int
    species_id_2: int
