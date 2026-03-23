"""
Servicio de evaluación de calidad de luz para plantas.

Recibe métricas del servicio solar y genera un reporte de calidad
con score, desglose espectral, procesos fisiológicos activos y
comparación opcional contra los requerimientos de una especie.
"""

from typing import Optional


# Procesos fisiológicos por banda espectral
PHYSIOLOGICAL_PROCESSES = {
    "uv_a": [
        "Biosíntesis de flavonoides y antocianinas",
        "Engrosamiento de cutícula",
        "Respuesta al estrés UV",
    ],
    "blue": [
        "Fototropismo (orientación hacia la luz)",
        "Apertura estomática",
        "Inhibición de elongación (plantas compactas)",
        "Activación de criptocromos",
    ],
    "green": [
        "Fotosíntesis en hojas internas de la canopia",
        "Penetración profunda en tejido foliar",
    ],
    "red": [
        "Fotosíntesis primaria (absorción máxima de Clorofila a y b)",
        "Fotoperiodismo",
        "Activación del fitocromo Pr→Pfr",
    ],
    "far_red": [
        "Respuesta de sombra (elongación de tallo)",
        "Inducción floral en plantas de día corto",
        "Conversión fitocromo Pfr→Pr",
    ],
}

# Umbrales de PAR para clasificación general (µmol/m²/s)
PAR_THRESHOLDS = {
    "muy_baja": 50,
    "baja": 200,
    "media": 500,
    "alta": 1000,
    "muy_alta": 2000,
}

# Umbrales de DLI para clasificación (mol/m²/día)
DLI_THRESHOLDS = {
    "muy_bajo": 5,
    "bajo": 12,
    "medio": 25,
    "alto": 40,
    "muy_alto": 60,
}

# Ratio R:FR de referencia (luz solar directa ≈ 1.2)
R_FR_REFERENCE = 1.2
R_FR_SHADE = 0.5  # sombra profunda


def classify_par(par_umol: float) -> str:
    """Clasifica el nivel de PAR en categorías descriptivas."""
    if par_umol < PAR_THRESHOLDS["muy_baja"]:
        return "muy baja"
    elif par_umol < PAR_THRESHOLDS["baja"]:
        return "baja"
    elif par_umol < PAR_THRESHOLDS["media"]:
        return "media"
    elif par_umol < PAR_THRESHOLDS["alta"]:
        return "alta"
    elif par_umol < PAR_THRESHOLDS["muy_alta"]:
        return "muy alta"
    else:
        return "extrema"


def classify_dli(dli: float) -> str:
    """Clasifica el DLI diario en categorías descriptivas."""
    if dli < DLI_THRESHOLDS["muy_bajo"]:
        return "muy bajo"
    elif dli < DLI_THRESHOLDS["bajo"]:
        return "bajo"
    elif dli < DLI_THRESHOLDS["medio"]:
        return "medio"
    elif dli < DLI_THRESHOLDS["alto"]:
        return "alto"
    elif dli < DLI_THRESHOLDS["muy_alto"]:
        return "muy alto"
    else:
        return "extremo"


def _score_par(par_umol: float) -> float:
    """
    Puntaje de PAR (0–40 puntos).

    Escala logarítmica: sube rápido al principio, se aplana en valores altos.
    """
    if par_umol <= 0:
        return 0.0
    import math
    # 1000 µmol/m²/s = 40 puntos (techo)
    score = min(40.0, 40.0 * math.log10(par_umol + 1) / math.log10(1001))
    return round(score, 1)


def _score_spectrum(bands_percent: dict) -> float:
    """
    Puntaje espectral (0–40 puntos).

    La luz solar ideal para plantas tiene:
      - Azul: ~18-22% del PAR
      - Verde: ~35-40% del PAR
      - Rojo: ~38-45% del PAR
    Penaliza desviaciones de estos rangos.
    """
    blue = bands_percent.get("blue", 0)
    green = bands_percent.get("green", 0)
    red = bands_percent.get("red", 0)

    # Ideales
    ideal_blue = 20.0
    ideal_green = 38.0
    ideal_red = 42.0

    # Penalización por desviación (máx 13 pts por banda)
    def band_score(actual: float, ideal: float, weight: float) -> float:
        deviation = abs(actual - ideal) / ideal
        return weight * max(0.0, 1.0 - deviation)

    score = (
        band_score(blue, ideal_blue, 13.0)
        + band_score(green, ideal_green, 13.0)
        + band_score(red, ideal_red, 14.0)
    )
    return round(score, 1)


def _score_dli(dli: float) -> float:
    """
    Puntaje de DLI (0–20 puntos).

    Un DLI entre 20 y 40 mol/m²/día es óptimo para la mayoría de las plantas.
    """
    if dli <= 0:
        return 0.0
    import math
    score = min(20.0, 20.0 * math.log10(dli + 1) / math.log10(41))
    return round(score, 1)


def calculate_quality_score(metrics: dict) -> dict:
    """
    Calcula el score general de calidad de luz (0–100) y su desglose.

    Args:
        metrics: Resultado de solar.get_light_metrics()

    Returns:
        Dict con score total y sub-scores por componente.
    """
    if not metrics.get("sun_is_up", False):
        return {
            "total": 0,
            "par_score": 0.0,
            "spectrum_score": 0.0,
            "dli_score": 0.0,
            "label": "Sin luz solar",
        }

    par_score = _score_par(metrics["par_umol"])
    spectrum_score = _score_spectrum(metrics.get("bands_percent", {}))
    dli_score = _score_dli(metrics.get("dli_estimated", 0))
    total = round(par_score + spectrum_score + dli_score)

    return {
        "total": min(100, total),
        "par_score": par_score,
        "spectrum_score": spectrum_score,
        "dli_score": dli_score,
        "label": _score_label(total),
    }


def _score_label(score: float) -> str:
    if score < 20:
        return "Muy deficiente"
    elif score < 40:
        return "Deficiente"
    elif score < 60:
        return "Moderada"
    elif score < 80:
        return "Buena"
    else:
        return "Excelente"


def get_active_processes(metrics: dict) -> list[dict]:
    """
    Determina los procesos fisiológicos activos según la distribución espectral.

    Returns:
        Lista de dicts con banda, nivel de actividad y procesos.
    """
    if not metrics.get("sun_is_up", False):
        return []

    bands_w = metrics.get("bands_w_m2", {})
    par_w = bands_w.get("par", 1)

    result = []
    band_order = ["red", "blue", "green", "far_red", "uv_a"]

    for band in band_order:
        w = bands_w.get(band, 0)
        if par_w > 0:
            relative = w / par_w
        else:
            relative = 0

        if relative > 0.3:
            level = "alto"
        elif relative > 0.1:
            level = "moderado"
        elif relative > 0.01:
            level = "bajo"
        else:
            continue  # banda insignificante

        result.append({
            "band": band,
            "level": level,
            "processes": PHYSIOLOGICAL_PROCESSES.get(band, []),
            "w_m2": bands_w.get(band, 0),
        })

    return result


def compare_with_species(metrics: dict, species: dict) -> dict:
    """
    Compara la luz actual con los requerimientos de una especie.

    Args:
        metrics: Resultado de solar.get_light_metrics()
        species: Dict con campos par_min_umol, par_optimal_umol, par_max_umol,
                 dli_min, dli_optimal, light_requirement

    Returns:
        Dict con evaluación, recomendación y estado de PAR y DLI.
    """
    par = metrics.get("par_umol", 0)
    dli = metrics.get("dli_estimated", 0)

    par_min = species.get("par_min_umol") or 0
    par_opt = species.get("par_optimal_umol") or 0
    par_max = species.get("par_max_umol") or float("inf")
    dli_min = species.get("dli_min") or 0
    dli_opt = species.get("dli_optimal") or 0

    # Evaluación PAR
    if par < par_min:
        par_status = "insuficiente"
        par_msg = f"Luz insuficiente ({par:.0f} µmol/m²/s, mínimo: {par_min:.0f})"
    elif par > par_max:
        par_status = "exceso"
        par_msg = f"Exceso de luz ({par:.0f} µmol/m²/s, máximo: {par_max:.0f})"
    elif par >= par_opt * 0.8:
        par_status = "optimo"
        par_msg = f"Luz óptima ({par:.0f} µmol/m²/s)"
    else:
        par_status = "adecuado"
        par_msg = f"Luz adecuada ({par:.0f} µmol/m²/s, óptimo: {par_opt:.0f})"

    # Evaluación DLI
    if dli < dli_min:
        dli_status = "insuficiente"
        dli_msg = f"DLI diario insuficiente ({dli:.1f} mol/m²/día, mínimo: {dli_min:.1f})"
    elif dli >= dli_opt * 0.8:
        dli_status = "optimo"
        dli_msg = f"DLI diario óptimo ({dli:.1f} mol/m²/día)"
    else:
        dli_status = "adecuado"
        dli_msg = f"DLI adecuado ({dli:.1f} mol/m²/día, óptimo: {dli_opt:.1f})"

    # Recomendación general
    if par_status == "insuficiente" or dli_status == "insuficiente":
        recommendation = "Necesita más luz"
        recommendation_level = "warning"
    elif par_status == "exceso":
        recommendation = "Cuidado: exceso de luz"
        recommendation_level = "danger"
    elif par_status == "optimo" and dli_status in ("optimo", "adecuado"):
        recommendation = "Buena ubicación para esta especie"
        recommendation_level = "success"
    else:
        recommendation = "Ubicación aceptable"
        recommendation_level = "info"

    return {
        "par_status": par_status,
        "par_message": par_msg,
        "dli_status": dli_status,
        "dli_message": dli_msg,
        "recommendation": recommendation,
        "recommendation_level": recommendation_level,
        "current_par": par,
        "current_dli": dli,
        "species_par_min": par_min,
        "species_par_optimal": par_opt,
        "species_par_max": par_max,
        "species_dli_min": dli_min,
        "species_dli_optimal": dli_opt,
    }


def build_light_report(metrics: dict, species: Optional[dict] = None) -> dict:
    """
    Construye el reporte completo de calidad de luz.

    Args:
        metrics: Resultado de solar.get_light_metrics()
        species: (opcional) datos de especie para comparación

    Returns:
        Reporte completo con score, procesos activos y comparación de especie.
    """
    quality = calculate_quality_score(metrics)
    processes = get_active_processes(metrics)

    report = {
        "sun_is_up": metrics.get("sun_is_up", False),
        "quality": quality,
        "par_umol": metrics.get("par_umol", 0),
        "par_classification": classify_par(metrics.get("par_umol", 0)),
        "dli_estimated": metrics.get("dli_estimated", 0),
        "dli_classification": classify_dli(metrics.get("dli_estimated", 0)),
        "daylight_hours": metrics.get("daylight_hours", 0),
        "r_fr_ratio": metrics.get("r_fr_ratio"),
        "bands_w_m2": metrics.get("bands_w_m2", {}),
        "bands_percent": metrics.get("bands_percent", {}),
        "active_processes": processes,
        "solar_position": metrics.get("solar_position", {}),
        "airmass": metrics.get("airmass"),
        "spectrum": metrics.get("spectrum", {"wavelengths": [], "irradiance": []}),
        "species_comparison": None,
    }

    if species:
        report["species_comparison"] = compare_with_species(metrics, species)

    return report
