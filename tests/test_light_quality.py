"""
Tests del servicio de calidad de luz.

Verifica que el score, desglose espectral y comparación con especies
son coherentes para distintos escenarios.
"""

import pytest
from app.services.light_quality import (
    calculate_quality_score,
    classify_par,
    classify_dli,
    get_active_processes,
    compare_with_species,
    build_light_report,
)

# --- Fixtures de métricas solares ---

METRICS_NOON = {
    "sun_is_up": True,
    "par_umol": 1500.0,
    "dli_estimated": 35.0,
    "daylight_hours": 14.0,
    "r_fr_ratio": 1.15,
    "airmass": 1.1,
    "bands_w_m2": {
        "uv_a": 18.0,
        "blue": 55.0,
        "green": 110.0,
        "red": 130.0,
        "far_red": 45.0,
        "par": 295.0,
    },
    "bands_percent": {
        "blue": 18.6,
        "green": 37.3,
        "red": 44.1,
    },
    "solar_position": {"elevation": 70.0, "azimuth": 180.0, "zenith": 20.0,
                       "apparent_elevation": 69.9, "apparent_zenith": 20.1},
}

METRICS_NIGHT = {
    "sun_is_up": False,
    "par_umol": 0.0,
    "dli_estimated": 0.0,
    "daylight_hours": 0.0,
    "r_fr_ratio": None,
    "airmass": None,
    "bands_w_m2": {k: 0.0 for k in ["uv_a", "blue", "green", "red", "far_red", "par"]},
    "bands_percent": {"blue": 0.0, "green": 0.0, "red": 0.0},
    "solar_position": {"elevation": -30.0, "azimuth": 0.0, "zenith": 120.0,
                       "apparent_elevation": -30.0, "apparent_zenith": 120.0},
}

METRICS_LOW_LIGHT = {
    "sun_is_up": True,
    "par_umol": 80.0,
    "dli_estimated": 4.0,
    "daylight_hours": 8.0,
    "r_fr_ratio": 0.6,
    "airmass": 5.0,
    "bands_w_m2": {
        "uv_a": 1.0,
        "blue": 5.0,
        "green": 10.0,
        "red": 9.0,
        "far_red": 8.0,
        "par": 24.0,
    },
    "bands_percent": {
        "blue": 20.8,
        "green": 41.7,
        "red": 37.5,
    },
    "solar_position": {"elevation": 10.0, "azimuth": 90.0, "zenith": 80.0,
                       "apparent_elevation": 9.8, "apparent_zenith": 80.2},
}

# --- Fixtures de especies ---

SPECIES_SUN = {
    "id": 1,
    "common_name": "Tomate",
    "scientific_name": "Solanum lycopersicum",
    "light_requirement": "full_sun",
    "par_min_umol": 400.0,
    "par_optimal_umol": 1000.0,
    "par_max_umol": 2000.0,
    "dli_min": 20.0,
    "dli_optimal": 30.0,
}

SPECIES_SHADE = {
    "id": 2,
    "common_name": "Pothos",
    "scientific_name": "Epipremnum aureum",
    "light_requirement": "full_shade",
    "par_min_umol": 20.0,
    "par_optimal_umol": 100.0,
    "par_max_umol": 300.0,
    "dli_min": 2.0,
    "dli_optimal": 8.0,
}


class TestClassifyPar:
    def test_very_low(self):
        assert classify_par(10) == "muy baja"

    def test_low(self):
        assert classify_par(100) == "baja"

    def test_medium(self):
        assert classify_par(300) == "media"

    def test_high(self):
        assert classify_par(700) == "alta"

    def test_very_high(self):
        assert classify_par(1500) == "muy alta"

    def test_extreme(self):
        assert classify_par(2500) == "extrema"


class TestClassifyDli:
    def test_very_low(self):
        assert classify_dli(2) == "muy bajo"

    def test_low(self):
        assert classify_dli(8) == "bajo"

    def test_medium(self):
        assert classify_dli(18) == "medio"

    def test_high(self):
        assert classify_dli(35) == "alto"

    def test_very_high(self):
        assert classify_dli(55) == "muy alto"

    def test_extreme(self):
        assert classify_dli(80) == "extremo"


class TestCalculateQualityScore:
    def test_noon_score_range(self):
        """Score al mediodía debe estar entre 60 y 100."""
        result = calculate_quality_score(METRICS_NOON)
        assert 60 <= result["total"] <= 100

    def test_night_score_zero(self):
        """Score de noche debe ser 0."""
        result = calculate_quality_score(METRICS_NIGHT)
        assert result["total"] == 0
        assert result["label"] == "Sin luz solar"

    def test_noon_better_than_low_light(self):
        """El mediodía debe tener mejor score que luz baja."""
        noon = calculate_quality_score(METRICS_NOON)
        low = calculate_quality_score(METRICS_LOW_LIGHT)
        assert noon["total"] > low["total"]

    def test_score_has_required_keys(self):
        result = calculate_quality_score(METRICS_NOON)
        for key in ["total", "par_score", "spectrum_score", "dli_score", "label"]:
            assert key in result

    def test_sub_scores_non_negative(self):
        result = calculate_quality_score(METRICS_NOON)
        assert result["par_score"] >= 0
        assert result["spectrum_score"] >= 0
        assert result["dli_score"] >= 0

    def test_sub_scores_sum_approximately_equals_total(self):
        result = calculate_quality_score(METRICS_NOON)
        sub_total = result["par_score"] + result["spectrum_score"] + result["dli_score"]
        assert abs(sub_total - result["total"]) <= 1

    def test_label_is_string(self):
        result = calculate_quality_score(METRICS_NOON)
        assert isinstance(result["label"], str)
        assert len(result["label"]) > 0


class TestGetActiveProcesses:
    def test_night_returns_empty(self):
        processes = get_active_processes(METRICS_NIGHT)
        assert processes == []

    def test_noon_returns_processes(self):
        processes = get_active_processes(METRICS_NOON)
        assert len(processes) > 0

    def test_each_process_has_required_keys(self):
        processes = get_active_processes(METRICS_NOON)
        for p in processes:
            assert "band" in p
            assert "level" in p
            assert "processes" in p
            assert isinstance(p["processes"], list)

    def test_level_valid_values(self):
        processes = get_active_processes(METRICS_NOON)
        valid_levels = {"alto", "moderado", "bajo"}
        for p in processes:
            assert p["level"] in valid_levels

    def test_red_band_present_at_noon(self):
        """La banda roja debe aparecer activa al mediodía."""
        processes = get_active_processes(METRICS_NOON)
        bands = [p["band"] for p in processes]
        assert "red" in bands


class TestCompareWithSpecies:
    def test_noon_with_sun_species_optimal(self):
        """Con luz alta y especie de sol, el PAR debe ser óptimo."""
        result = compare_with_species(METRICS_NOON, SPECIES_SUN)
        assert result["par_status"] in ("optimo", "adecuado")

    def test_noon_with_shade_species_excess(self):
        """Con luz alta y especie de sombra, debe detectar exceso."""
        result = compare_with_species(METRICS_NOON, SPECIES_SHADE)
        assert result["par_status"] == "exceso"
        assert result["recommendation_level"] == "danger"

    def test_low_light_with_sun_species_insufficient(self):
        """Con luz baja y especie de sol, debe detectar insuficiencia."""
        result = compare_with_species(METRICS_LOW_LIGHT, SPECIES_SUN)
        assert result["par_status"] == "insuficiente"
        assert result["recommendation_level"] == "warning"

    def test_low_light_with_shade_species_ok(self):
        """Con luz baja y especie de sombra, debe ser adecuado u óptimo."""
        result = compare_with_species(METRICS_LOW_LIGHT, SPECIES_SHADE)
        assert result["par_status"] in ("optimo", "adecuado")

    def test_comparison_has_required_keys(self):
        result = compare_with_species(METRICS_NOON, SPECIES_SUN)
        for key in ["par_status", "dli_status", "recommendation", "recommendation_level",
                    "current_par", "current_dli"]:
            assert key in result


class TestBuildLightReport:
    def test_report_keys_present(self):
        report = build_light_report(METRICS_NOON)
        for key in ["sun_is_up", "quality", "par_umol", "dli_estimated",
                    "active_processes", "species_comparison"]:
            assert key in report

    def test_no_species_comparison_is_none(self):
        report = build_light_report(METRICS_NOON)
        assert report["species_comparison"] is None

    def test_with_species_comparison_present(self):
        report = build_light_report(METRICS_NOON, SPECIES_SUN)
        assert report["species_comparison"] is not None

    def test_night_report_sun_is_up_false(self):
        report = build_light_report(METRICS_NIGHT)
        assert report["sun_is_up"] is False
        assert report["quality"]["total"] == 0
