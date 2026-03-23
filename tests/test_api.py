"""
Tests de integración de la API.

Usa TestClient de FastAPI/httpx para testear todos los endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Coordenadas de Buenos Aires, mediodía de verano
PAYLOAD_NOON = {
    "lat": -34.6,
    "lon": -58.4,
    "dt": "2024-12-21T15:00:00Z",
}

PAYLOAD_NIGHT = {
    "lat": -34.6,
    "lon": -58.4,
    "dt": "2024-12-21T03:00:00Z",
}


class TestHealth:
    def test_health_ok(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestPages:
    def test_index_returns_html(self):
        r = client.get("/")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_species_page_returns_html(self):
        r = client.get("/species")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]


class TestLightReport:
    def test_post_light_report_json(self):
        r = client.post("/api/light-report", json=PAYLOAD_NOON)
        assert r.status_code == 200
        data = r.json()
        assert "quality" in data
        assert "par_umol" in data
        assert "sun_is_up" in data

    def test_post_light_report_night(self):
        r = client.post("/api/light-report", json=PAYLOAD_NIGHT)
        assert r.status_code == 200
        data = r.json()
        assert data["sun_is_up"] is False
        assert data["par_umol"] == 0.0

    def test_post_light_report_quality_score_range(self):
        r = client.post("/api/light-report", json=PAYLOAD_NOON)
        data = r.json()
        assert 0 <= data["quality"]["total"] <= 100

    def test_post_light_report_without_datetime(self):
        """Debe funcionar sin datetime (usa el momento actual)."""
        r = client.post("/api/light-report", json={"lat": -34.6, "lon": -58.4})
        assert r.status_code == 200

    def test_post_light_report_active_processes(self):
        r = client.post("/api/light-report", json=PAYLOAD_NOON)
        data = r.json()
        assert "active_processes" in data
        assert isinstance(data["active_processes"], list)

    def test_post_light_report_bands(self):
        r = client.post("/api/light-report", json=PAYLOAD_NOON)
        data = r.json()
        assert "bands_w_m2" in data
        assert "par" in data["bands_w_m2"]

    def test_post_light_report_invalid_payload(self):
        r = client.post("/api/light-report", json={"lat": "no_es_numero", "lon": -58.4})
        assert r.status_code == 422


class TestSpectrum:
    def test_get_spectrum_noon(self):
        r = client.get("/api/spectrum/-34.6/-58.4?dt=2024-12-21T15:00:00Z")
        assert r.status_code == 200
        data = r.json()
        assert "wavelengths" in data
        assert "irradiance" in data
        assert data["sun_is_up"] is True
        assert len(data["wavelengths"]) > 0

    def test_get_spectrum_night(self):
        r = client.get("/api/spectrum/-34.6/-58.4?dt=2024-12-21T03:00:00Z")
        assert r.status_code == 200
        data = r.json()
        assert data["sun_is_up"] is False

    def test_get_spectrum_no_dt(self):
        r = client.get("/api/spectrum/-34.6/-58.4")
        assert r.status_code == 200

    def test_get_spectrum_wavelengths_and_irradiance_same_length(self):
        r = client.get("/api/spectrum/-34.6/-58.4?dt=2024-12-21T15:00:00+00:00")
        data = r.json()
        assert len(data["wavelengths"]) == len(data["irradiance"])


class TestSpeciesSearch:
    def test_search_empty_returns_list(self):
        r = client.get("/api/species/search")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_search_tomate(self):
        r = client.get("/api/species/search?q=tomate")
        assert r.status_code == 200
        data = r.json()
        assert any("tomate" in sp["common_name"].lower() for sp in data)

    def test_search_nonexistent(self):
        r = client.get("/api/species/search?q=xyzxyzxyz_no_existe")
        assert r.status_code == 200
        assert r.json() == []


class TestSpeciesDetail:
    def test_get_species_by_id(self):
        r = client.get("/api/species/1")
        assert r.status_code == 200
        data = r.json()
        assert "common_name" in data
        assert "scientific_name" in data

    def test_get_species_not_found(self):
        r = client.get("/api/species/99999")
        assert r.status_code == 404

    def test_get_species_has_par_data(self):
        r = client.get("/api/species/1")
        data = r.json()
        assert data["par_min_umol"] is not None
        assert data["par_optimal_umol"] is not None


class TestSpeciesLight:
    def test_species_light_report(self):
        r = client.post(
            "/api/species/1/light",
            json={"lat": -34.6, "lon": -58.4},
        )
        assert r.status_code == 200
        data = r.json()
        assert "quality" in data
        assert data["species_comparison"] is not None

    def test_species_light_has_recommendation(self):
        r = client.post(
            "/api/species/1/light",
            json={"lat": -34.6, "lon": -58.4},
        )
        data = r.json()
        comp = data["species_comparison"]
        assert "recommendation" in comp
        assert "par_status" in comp

    def test_species_light_not_found(self):
        r = client.post(
            "/api/species/99999/light",
            json={"lat": -34.6, "lon": -58.4},
        )
        assert r.status_code == 404
