"""
Servicio de cálculos solares usando pvlib.

Calcula posición solar, masa de aire, espectro estimado,
PAR, DLI y ratio R:FR para una ubicación y momento dados.
"""

from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd
import pvlib

# Coordenadas default: Buenos Aires
DEFAULT_LAT = -34.6
DEFAULT_LON = -58.4

# Rangos espectrales (nm)
BAND_UV_A = (320, 400)
BAND_BLUE = (400, 500)
BAND_GREEN = (500, 600)
BAND_RED = (600, 700)
BAND_FAR_RED = (700, 750)
BAND_PAR = (400, 700)


def get_solar_position(lat: float, lon: float, dt: Optional[datetime] = None) -> dict:
    """
    Calcula la posición solar (azimut, elevación, cenit) para una ubicación y momento.

    Args:
        lat: Latitud en grados decimales.
        lon: Longitud en grados decimales.
        dt: Momento de cálculo. Si es None, usa el momento actual en UTC.

    Returns:
        Dict con azimuth, elevation, zenith (todos en grados).
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    times = pd.DatetimeIndex([dt])
    location = pvlib.location.Location(latitude=lat, longitude=lon)
    pos = location.get_solarposition(times)

    return {
        "azimuth": float(pos["azimuth"].iloc[0]),
        "elevation": float(pos["elevation"].iloc[0]),
        "zenith": float(pos["zenith"].iloc[0]),
        "apparent_elevation": float(pos["apparent_elevation"].iloc[0]),
        "apparent_zenith": float(pos["apparent_zenith"].iloc[0]),
    }


def get_airmass(zenith_deg: float) -> Optional[float]:
    """
    Calcula la masa de aire relativa dado el ángulo cenital solar.

    Returns None si el sol está bajo el horizonte (zenith > 90°).
    """
    if zenith_deg >= 90:
        return None
    am = pvlib.atmosphere.get_relative_airmass(zenith_deg)
    return float(am)


def get_spectrum(lat: float, lon: float, dt: Optional[datetime] = None) -> dict:
    """
    Estima el espectro solar en superficie usando el modelo de pvlib (Spectrl2).

    Returns:
        Dict con:
          - wavelengths: array de longitudes de onda (nm)
          - irradiance: irradiancia espectral (W/m²/nm)
          - airmass: masa de aire relativa
          - solar_position: dict de posición solar
    """
    solar_pos = get_solar_position(lat, lon, dt)
    zenith = solar_pos["apparent_zenith"]
    airmass = get_airmass(zenith)

    if airmass is None or solar_pos["elevation"] <= 0:
        # Sol bajo el horizonte: espectro cero
        wl = np.arange(300, 4001, 1.0)
        return {
            "wavelengths": wl.tolist(),
            "irradiance": np.zeros_like(wl).tolist(),
            "airmass": None,
            "solar_position": solar_pos,
            "sun_is_up": False,
        }

    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    times = pd.DatetimeIndex([dt])
    location = pvlib.location.Location(latitude=lat, longitude=lon)

    # Usamos el modelo Spectrl2 de pvlib para espectro en superficie
    airmass_abs = pvlib.atmosphere.get_absolute_airmass(airmass)
    pressure = pvlib.atmosphere.alt2pres(0)  # nivel del mar

    # Parámetros del modelo (condiciones estándar limpias)
    spectrl2 = pvlib.spectrum.spectrl2(
        apparent_zenith=zenith,
        aoi=zenith,              # superficie horizontal
        surface_tilt=0,
        ground_albedo=0.25,
        surface_pressure=pressure,
        relative_airmass=airmass,
        ozone=0.31,
        precipitable_water=1.5,
        aerosol_turbidity_500nm=0.1,
        dayofyear=pd.Timestamp(dt).dayofyear,
    )

    wl = np.array(spectrl2["wavelength"], dtype=float)
    irr = np.array(spectrl2["poa_global"], dtype=float).flatten()
    irr = np.maximum(irr, 0)  # sin negativos

    return {
        "wavelengths": wl.tolist(),
        "irradiance": irr.tolist(),
        "airmass": float(airmass),
        "solar_position": solar_pos,
        "sun_is_up": True,
    }


def _integrate_band(wavelengths: np.ndarray, irradiance: np.ndarray, wl_min: float, wl_max: float) -> float:
    """Integra la irradiancia en una banda espectral (W/m²)."""
    mask = (wavelengths >= wl_min) & (wavelengths <= wl_max)
    if mask.sum() < 2:
        return 0.0
    return float(np.trapezoid(irradiance[mask], wavelengths[mask]))


def irradiance_to_par(w_per_m2: float) -> float:
    """
    Convierte irradiancia PAR (W/m²) a flujo de fotones (µmol/m²/s).

    Usa el factor de conversión promedio ~4.57 µmol/J para luz visible.
    """
    return w_per_m2 * 4.57


def get_light_metrics(lat: float, lon: float, dt: Optional[datetime] = None) -> dict:
    """
    Calcula todas las métricas de luz relevantes para plantas.

    Returns:
        Dict con PAR, DLI estimado, bandas espectrales, ratio R:FR y más.
    """
    spectrum = get_spectrum(lat, lon, dt)
    wl = np.array(spectrum["wavelengths"])
    irr = np.array(spectrum["irradiance"])

    if not spectrum["sun_is_up"]:
        # Igual calculamos horas de luz del día para mostrar en el reporte nocturno
        location = pvlib.location.Location(latitude=lat, longitude=lon)
        if dt is None:
            dt_calc = datetime.now(timezone.utc)
        else:
            dt_calc = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        day_start = pd.Timestamp(dt_calc).normalize().tz_localize(None)
        times_day = pd.date_range(start=day_start, periods=24, freq="1h", tz="UTC")
        sun_positions = location.get_solarposition(times_day)
        daylight_hours = float((sun_positions["elevation"] > 0).sum())

        clearsky_night = location.get_clearsky(times_day)
        par_umol_night = clearsky_night["ghi"].values * 0.45 * 4.57
        current_hour_night = int(pd.Timestamp(dt_calc).hour)

        return {
            "sun_is_up": False,
            "par_umol": 0.0,
            "dli_estimated": 0.0,
            "daylight_hours": daylight_hours,
            "daily_par_chart": {
                "hours": list(range(24)),
                "par_umol": [round(float(v), 1) for v in par_umol_night],
                "current_hour": current_hour_night,
            },
            "bands_w_m2": {k: 0.0 for k in ["uv_a", "blue", "green", "red", "far_red", "par"]},
            "bands_percent": {k: 0.0 for k in ["uv_a", "blue", "green", "red", "far_red"]},
            "r_fr_ratio": None,
            "airmass": None,
            "solar_position": spectrum["solar_position"],
            "spectrum": {"wavelengths": spectrum["wavelengths"], "irradiance": spectrum["irradiance"]},
        }

    # Integrar bandas
    par_w = _integrate_band(wl, irr, *BAND_PAR)
    uv_a_w = _integrate_band(wl, irr, *BAND_UV_A)
    blue_w = _integrate_band(wl, irr, *BAND_BLUE)
    green_w = _integrate_band(wl, irr, *BAND_GREEN)
    red_w = _integrate_band(wl, irr, *BAND_RED)
    far_red_w = _integrate_band(wl, irr, *BAND_FAR_RED)

    par_umol = irradiance_to_par(par_w)

    # DLI estimado: integrar el PAR a lo largo del día usando clearsky de pvlib
    location = pvlib.location.Location(latitude=lat, longitude=lon)
    if dt is None:
        dt_calc = datetime.now(timezone.utc)
    else:
        dt_calc = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    day_start = pd.Timestamp(dt_calc).normalize().tz_localize(None)
    times_day = pd.date_range(start=day_start, periods=24, freq="1h", tz="UTC")
    sun_positions = location.get_solarposition(times_day)
    daylight_hours = float((sun_positions["elevation"] > 0).sum())

    # Clearsky GHI horario → PAR horario → DLI (mol/m²/día)
    clearsky = location.get_clearsky(times_day)
    ghi_hourly = clearsky["ghi"].values
    par_w_hourly = ghi_hourly * 0.45       # PAR ≈ 45% de la irradiancia global
    par_umol_hourly = par_w_hourly * 4.57
    dli = float((par_umol_hourly * 3600 / 1_000_000).sum())

    # Historial diario: PAR hora a hora para el gráfico de evolución del día
    current_hour = int(pd.Timestamp(dt_calc).hour)
    daily_par_chart = {
        "hours": list(range(24)),
        "par_umol": [round(float(v), 1) for v in par_umol_hourly],
        "current_hour": current_hour,
    }

    # Porcentajes respecto al total PAR
    total_par_bands = blue_w + green_w + red_w  # solo 400-700nm
    def pct(val: float) -> float:
        return round(val / total_par_bands * 100, 1) if total_par_bands > 0 else 0.0

    # Ratio R:FR
    r_fr = red_w / far_red_w if far_red_w > 0 else None

    return {
        "sun_is_up": True,
        "par_umol": round(par_umol, 2),
        "dli_estimated": round(dli, 2),
        "bands_w_m2": {
            "uv_a": round(uv_a_w, 2),
            "blue": round(blue_w, 2),
            "green": round(green_w, 2),
            "red": round(red_w, 2),
            "far_red": round(far_red_w, 2),
            "par": round(par_w, 2),
        },
        "bands_percent": {
            "blue": pct(blue_w),
            "green": pct(green_w),
            "red": pct(red_w),
        },
        "r_fr_ratio": round(r_fr, 3) if r_fr is not None else None,
        "airmass": spectrum["airmass"],
        "solar_position": spectrum["solar_position"],
        "daylight_hours": daylight_hours,
        "daily_par_chart": daily_par_chart,
        "spectrum": {
            "wavelengths": spectrum["wavelengths"],
            "irradiance": spectrum["irradiance"],
        },
    }
