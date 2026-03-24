"""
Sistema de internacionalización simple para PlantLight.

Uso en templates: {{ t('clave', lang) }}
Uso en Python:    from app.i18n import t; t('clave', lang)
"""

from fastapi import Request

STRINGS: dict[str, dict[str, str]] = {
    # ── Navegación ──────────────────────────────────────────────────────
    "nav.home":           {"es": "Inicio",    "en": "Home"},
    "nav.species":        {"es": "Especies",  "en": "Species"},

    # ── Header / Footer ─────────────────────────────────────────────────
    "site.tagline":       {"es": "Calidad de luz solar para tus plantas",
                           "en": "Solar light quality for your plants"},

    # ── Página principal ─────────────────────────────────────────────────
    "home.hero_title":    {"es": "¿Cuánta luz solar<br><em>tienen tus plantas</em> hoy?",
                           "en": "How much solar light<br><em>do your plants have</em> today?"},
    "home.hero_subtitle": {"es": "Seleccioná tu ubicación en el mapa o usá la geolocalización para analizar la calidad de la luz solar en tiempo real.",
                           "en": "Select your location on the map or use geolocation to analyze solar light quality in real time."},
    "home.btn_geolocate": {"es": "Mi ubicación",     "en": "My location"},
    "home.btn_detecting": {"es": "Detectando…",      "en": "Detecting…"},
    "home.btn_calculate": {"es": "Calcular",          "en": "Calculate"},
    "home.datetime_title":{"es": "Simular otro momento del día", "en": "Simulate another time of day"},
    "home.map_hint":      {"es": "Hacé click en cualquier punto del mapa para analizar esa ubicación.",
                           "en": "Click anywhere on the map to analyze that location."},
    "home.loading":       {"es": "Calculando la luz solar…", "en": "Calculating solar light…"},
    "home.empty_state":   {"es": "Hacé click en el mapa o usá",
                           "en": "Click on the map or use"},
    "home.empty_state2":  {"es": "para ver el análisis de luz solar.",
                           "en": "to see the solar light analysis."},

    # ── Reporte de luz ───────────────────────────────────────────────────
    "report.day_summary":       {"es": "Resumen del día",               "en": "Day summary"},
    "report.par_current":       {"es": "PAR actual",                    "en": "Current PAR"},
    "report.dli_estimated":     {"es": "DLI estimado",                  "en": "Estimated DLI"},
    "report.daylight_hours":    {"es": "Horas de luz",                  "en": "Daylight hours"},
    "report.r_fr_ratio":        {"es": "Ratio rojo/lejano",             "en": "Red/far-red ratio"},
    "report.elevation":         {"es": "Elevación",                     "en": "Elevation"},
    "report.azimuth":           {"es": "Azimut",                        "en": "Azimuth"},
    "report.airmass":           {"es": "Masa de aire",                  "en": "Air mass"},
    "report.solar_spectrum":    {"es": "Espectro solar",                "en": "Solar spectrum"},
    "report.spectral_dist":     {"es": "Distribución espectral (PAR)",  "en": "Spectral distribution (PAR)"},
    "report.phys_processes":    {"es": "Procesos fisiológicos activos", "en": "Active physiological processes"},
    "report.no_processes":      {"es": "No hay procesos activos detectados.", "en": "No active processes detected."},
    "report.par_evolution":     {"es": "Evolución del PAR durante el día", "en": "PAR evolution throughout the day"},
    "report.par_caption":       {"es": "Radiación fotosintéticamente activa estimada (µmol/m²/s) hora a hora. La línea vertical marca el momento actual.",
                                 "en": "Estimated photosynthetically active radiation (µmol/m²/s) hour by hour. The vertical line marks the current time."},
    "report.species_compare":   {"es": "Comparación con la especie",    "en": "Species comparison"},
    "report.dli_unit":          {"es": "mol/m²/día",                    "en": "mol/m²/day"},

    # ── Bandas espectrales ───────────────────────────────────────────────
    "band.uv_a":      {"es": "UV-A",               "en": "UV-A"},
    "band.blue":      {"es": "Azul",               "en": "Blue"},
    "band.green":     {"es": "Verde",              "en": "Green"},
    "band.red":       {"es": "Rojo",               "en": "Red"},
    "band.far_red":   {"es": "Rojo lejano",        "en": "Far red"},
    "band.blue_nm":   {"es": "Azul (400–500 nm)",  "en": "Blue (400–500 nm)"},
    "band.green_nm":  {"es": "Verde (500–600 nm)", "en": "Green (500–600 nm)"},
    "band.red_nm":    {"es": "Rojo (600–700 nm)",  "en": "Red (600–700 nm)"},

    # ── Noche ────────────────────────────────────────────────────────────
    "night.title":         {"es": "El sol está bajo el horizonte",    "en": "The sun is below the horizon"},
    "night.body":          {"es": "No hay luz solar disponible en este momento en tu ubicación.",
                            "en": "No solar light available at this moment in your location."},
    "night.hours_today":   {"es": "Horas de luz hoy",                 "en": "Daylight hours today"},
    "night.solar_elev":    {"es": "Elevación solar",                  "en": "Solar elevation"},
    "night.tip":           {"es": "Usá el selector de fecha y hora para simular la luz a otro momento del día.",
                            "en": "Use the date and time selector to simulate light at another time of day."},

    # ── Calidad de luz (labels generados por light_quality.py) ──────────
    "quality.no_sun":      {"es": "Sin luz solar",   "en": "No sunlight"},
    "quality.very_poor":   {"es": "Muy deficiente",  "en": "Very poor"},
    "quality.poor":        {"es": "Deficiente",      "en": "Poor"},
    "quality.moderate":    {"es": "Moderada",        "en": "Moderate"},
    "quality.good":        {"es": "Buena",           "en": "Good"},
    "quality.excellent":   {"es": "Excelente",       "en": "Excellent"},

    # ── Clasificaciones PAR / DLI ────────────────────────────────────────
    "par.very_low":   {"es": "muy baja",  "en": "very low"},
    "par.low":        {"es": "baja",      "en": "low"},
    "par.medium":     {"es": "media",     "en": "medium"},
    "par.high":       {"es": "alta",      "en": "high"},
    "par.very_high":  {"es": "muy alta",  "en": "very high"},
    "par.extreme":    {"es": "extrema",   "en": "extreme"},
    "dli.very_low":   {"es": "muy bajo",  "en": "very low"},
    "dli.low":        {"es": "bajo",      "en": "low"},
    "dli.medium":     {"es": "medio",     "en": "medium"},
    "dli.high":       {"es": "alto",      "en": "high"},
    "dli.very_high":  {"es": "muy alto",  "en": "very high"},
    "dli.extreme":    {"es": "extremo",   "en": "extreme"},

    # ── Recomendaciones de especie ───────────────────────────────────────
    "rec.needs_more_light":   {"es": "Necesita más luz",               "en": "Needs more light"},
    "rec.too_much_light":     {"es": "Cuidado: exceso de luz",         "en": "Warning: too much light"},
    "rec.good_location":      {"es": "Buena ubicación para esta especie", "en": "Good location for this species"},
    "rec.acceptable":         {"es": "Ubicación aceptable",            "en": "Acceptable location"},

    # ── Niveles de proceso fisiológico ───────────────────────────────────
    "level.high":     {"es": "alto",     "en": "high"},
    "level.moderate": {"es": "moderado", "en": "moderate"},
    "level.low":      {"es": "bajo",     "en": "low"},

    # ── Requerimiento de luz (badges) ────────────────────────────────────
    "light.full_sun":       {"es": "Sol pleno",      "en": "Full sun"},
    "light.partial_shade":  {"es": "Sombra parcial", "en": "Partial shade"},
    "light.full_shade":     {"es": "Sombra total",   "en": "Full shade"},
    "light.variable":       {"es": "Variable",       "en": "Variable"},

    # ── Fotoperiodo ──────────────────────────────────────────────────────
    "photo.short_day":  {"es": "Día corto",       "en": "Short day"},
    "photo.long_day":   {"es": "Día largo",        "en": "Long day"},
    "photo.neutral":    {"es": "Neutro",           "en": "Neutral"},
    "photo.neutral2":   {"es": "Fotoperiodo neutro", "en": "Day-neutral"},

    # ── Búsqueda de especies ─────────────────────────────────────────────
    "species.hero_title":    {"es": "Buscador de <em>Especies</em>",   "en": "Species <em>Search</em>"},
    "species.hero_subtitle": {"es": "Encontrá los requerimientos de luz de tu planta y compará con tu ubicación actual.",
                              "en": "Find your plant's light requirements and compare with your current location."},
    "species.placeholder":   {"es": "Buscá por nombre común o científico… (ej: tomate, Lactuca)",
                              "en": "Search by common or scientific name… (e.g.: tomato, Lactuca)"},
    "species.compare_btn":   {"es": "Comparar especies",  "en": "Compare species"},
    "species.cancel_compare":{"es": "Cancelar comparación", "en": "Cancel comparison"},
    "species.placeholder_empty": {"es": "Escribí para buscar especies…", "en": "Type to search species…"},
    "species.no_results":    {"es": "No se encontraron especies. Probá con otro término.",
                              "en": "No species found. Try another term."},
    "species.family":        {"es": "Familia:",          "en": "Family:"},
    "species.par_optimal":   {"es": "PAR óptimo",        "en": "Optimal PAR"},
    "species.dli_optimal":   {"es": "DLI óptimo",        "en": "Optimal DLI"},
    "species.view_analysis": {"es": "Ver análisis →",    "en": "View analysis →"},
    "species.select":        {"es": "+ Seleccionar",     "en": "+ Select"},
    "species.selected":      {"es": "✓ Seleccionada",    "en": "✓ Selected"},

    # ── Comparación de especies ──────────────────────────────────────────
    "compare.species_n":     {"es": "Especie",          "en": "Species"},
    "compare.vs":            {"es": "VS",               "en": "VS"},
    "compare.run_btn":       {"es": "Ver comparación →", "en": "View comparison →"},
    "compare.current_light": {"es": "Luz actual",       "en": "Current light"},
    "compare.hours":         {"es": "Horas de luz",     "en": "Daylight hours"},
    "compare.par_label":     {"es": "PAR (µmol/m²/s)",  "en": "PAR (µmol/m²/s)"},
    "compare.dli_label":     {"es": "DLI (mol/m²/día)", "en": "DLI (mol/m²/day)"},
    "compare.min":           {"es": "Mín:",             "en": "Min:"},
    "compare.opt":           {"es": "Ópt:",             "en": "Opt:"},
    "compare.current":       {"es": "Actual:",          "en": "Current:"},
    "compare.night_notice":  {"es": "🌙 Sol bajo el horizonte — los datos son del día de hoy",
                              "en": "🌙 Sun below the horizon — data is from today"},
    "compare.slot1":         {"es": "Especie 1",        "en": "Species 1"},
    "compare.slot2":         {"es": "Especie 2",        "en": "Species 2"},

    # ── Idioma ───────────────────────────────────────────────────────────
    "lang.es": {"es": "ES", "en": "ES"},
    "lang.en": {"es": "EN", "en": "EN"},
}


def t(key: str, lang: str = "es") -> str:
    """Retorna la traducción de una clave para el idioma dado."""
    entry = STRINGS.get(key)
    if entry is None:
        return key  # fallback: devuelve la clave
    return entry.get(lang) or entry.get("es") or key


def get_lang(request: Request) -> str:
    """Extrae el idioma de la cookie 'lang'. Default: 'es'."""
    lang = request.cookies.get("lang", "es")
    return lang if lang in ("es", "en") else "es"
