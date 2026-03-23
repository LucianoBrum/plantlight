"""
Tests del servicio solar.

Verifica posición solar, masa de aire, espectro y métricas de luz
con coordenadas y fechas conocidas.
"""

import pytest
from datetime import datetime, timezone
from app.services.solar import (
    get_solar_position,
    get_airmass,
    get_spectrum,
    get_light_metrics,
    irradiance_to_par,
)

# Buenos Aires: -34.6, -58.4
LAT_BA = -34.6
LON_BA = -58.4

# Solsticio de verano austral (diciembre) mediodía UTC-3 → 15:00 UTC
SUMMER_NOON = datetime(2024, 12, 21, 15, 0, 0, tzinfo=timezone.utc)

# Solsticio de invierno austral (junio) mediodía UTC-3 → 15:00 UTC
WINTER_NOON = datetime(2024, 6, 21, 15, 0, 0, tzinfo=timezone.utc)

# Medianoche (sol bajo el horizonte)
MIDNIGHT = datetime(2024, 6, 21, 3, 0, 0, tzinfo=timezone.utc)


class TestSolarPosition:
    def test_summer_noon_ba_elevation_high(self):
        """En verano austral al mediodía, la elevación en BA debe ser alta (>60°)."""
        pos = get_solar_position(LAT_BA, LON_BA, SUMMER_NOON)
        assert pos["elevation"] > 60, f"Elevación esperada >60°, obtenida: {pos['elevation']:.1f}°"

    def test_winter_noon_ba_elevation_lower(self):
        """En invierno austral al mediodía, la elevación debe ser menor que en verano."""
        pos_summer = get_solar_position(LAT_BA, LON_BA, SUMMER_NOON)
        pos_winter = get_solar_position(LAT_BA, LON_BA, WINTER_NOON)
        assert pos_winter["elevation"] < pos_summer["elevation"]

    def test_winter_noon_ba_elevation_positive(self):
        """En invierno al mediodía, el sol sigue sobre el horizonte."""
        pos = get_solar_position(LAT_BA, LON_BA, WINTER_NOON)
        assert pos["elevation"] > 0

    def test_midnight_elevation_negative(self):
        """A medianoche el sol está bajo el horizonte."""
        pos = get_solar_position(LAT_BA, LON_BA, MIDNIGHT)
        assert pos["elevation"] < 0

    def test_keys_present(self):
        pos = get_solar_position(LAT_BA, LON_BA, SUMMER_NOON)
        for key in ["azimuth", "elevation", "zenith", "apparent_elevation", "apparent_zenith"]:
            assert key in pos

    def test_zenith_complements_elevation(self):
        """zenith + elevation deben sumar ~90°."""
        pos = get_solar_position(LAT_BA, LON_BA, SUMMER_NOON)
        assert abs(pos["zenith"] + pos["elevation"] - 90) < 1.0


class TestAirmass:
    def test_low_zenith_airmass_near_one(self):
        """Con el sol casi en el cenit (zenith~0), AM ≈ 1."""
        am = get_airmass(0.1)
        assert 0.9 < am < 1.1

    def test_high_zenith_large_airmass(self):
        """Con el sol bajo (zenith=80°), AM debe ser grande (>5)."""
        am = get_airmass(80)
        assert am > 5

    def test_below_horizon_returns_none(self):
        """Con el sol bajo el horizonte, retorna None."""
        assert get_airmass(90) is None
        assert get_airmass(95) is None


class TestSpectrum:
    def test_sun_up_returns_nonzero_irradiance(self):
        """Con el sol arriba, la irradiancia debe ser > 0 en al menos parte del espectro."""
        spec = get_spectrum(LAT_BA, LON_BA, SUMMER_NOON)
        assert spec["sun_is_up"] is True
        total = sum(spec["irradiance"])
        assert total > 0

    def test_sun_down_returns_zero_irradiance(self):
        """Con el sol abajo, la irradiancia debe ser cero."""
        spec = get_spectrum(LAT_BA, LON_BA, MIDNIGHT)
        assert spec["sun_is_up"] is False
        assert all(v == 0.0 for v in spec["irradiance"])

    def test_spectrum_wavelengths_range(self):
        """Las longitudes de onda deben cubrir al menos 300–4000 nm."""
        spec = get_spectrum(LAT_BA, LON_BA, SUMMER_NOON)
        wl = spec["wavelengths"]
        assert min(wl) <= 310
        assert max(wl) >= 3000

    def test_no_negative_irradiance(self):
        """No debe haber irradiancia negativa."""
        spec = get_spectrum(LAT_BA, LON_BA, SUMMER_NOON)
        assert all(v >= 0 for v in spec["irradiance"])


class TestLightMetrics:
    def test_summer_noon_par_reasonable(self):
        """En verano al mediodía en BA, PAR debe estar entre 500 y 2500 µmol/m²/s."""
        metrics = get_light_metrics(LAT_BA, LON_BA, SUMMER_NOON)
        assert metrics["sun_is_up"] is True
        assert 500 < metrics["par_umol"] < 2500, f"PAR fuera de rango: {metrics['par_umol']}"

    def test_winter_noon_par_lower_than_summer(self):
        """En invierno, el PAR al mediodía debe ser menor que en verano."""
        summer = get_light_metrics(LAT_BA, LON_BA, SUMMER_NOON)
        winter = get_light_metrics(LAT_BA, LON_BA, WINTER_NOON)
        assert winter["par_umol"] < summer["par_umol"]

    def test_midnight_par_zero(self):
        """A medianoche, PAR = 0."""
        metrics = get_light_metrics(LAT_BA, LON_BA, MIDNIGHT)
        assert metrics["par_umol"] == 0.0
        assert metrics["sun_is_up"] is False

    def test_dli_reasonable_summer(self):
        """DLI estimado en verano debe estar entre 15 y 70 mol/m²/día."""
        metrics = get_light_metrics(LAT_BA, LON_BA, SUMMER_NOON)
        assert 15 < metrics["dli_estimated"] < 70, f"DLI fuera de rango: {metrics['dli_estimated']}"

    def test_r_fr_ratio_present(self):
        """El ratio R:FR debe estar presente y ser positivo con el sol arriba."""
        metrics = get_light_metrics(LAT_BA, LON_BA, SUMMER_NOON)
        assert metrics["r_fr_ratio"] is not None
        assert metrics["r_fr_ratio"] > 0

    def test_band_percentages_sum_to_100(self):
        """Los porcentajes de las bandas PAR (azul+verde+rojo) deben sumar ~100%."""
        metrics = get_light_metrics(LAT_BA, LON_BA, SUMMER_NOON)
        pcts = metrics["bands_percent"]
        total = pcts["blue"] + pcts["green"] + pcts["red"]
        assert abs(total - 100) < 1.0, f"Porcentajes suman {total}, esperado ~100"

    def test_daylight_hours_reasonable(self):
        """Las horas de luz en verano austral deben ser más que en invierno."""
        summer = get_light_metrics(LAT_BA, LON_BA, SUMMER_NOON)
        winter = get_light_metrics(LAT_BA, LON_BA, WINTER_NOON)
        assert summer["daylight_hours"] > winter["daylight_hours"]


class TestIrradianceToPar:
    def test_conversion_factor(self):
        """100 W/m² → ~457 µmol/m²/s."""
        result = irradiance_to_par(100)
        assert abs(result - 457) < 1
