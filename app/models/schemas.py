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
