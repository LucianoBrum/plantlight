"""
Script para crear y poblar la base de datos de especies.

Ejecutar desde la raíz del proyecto:
    python -m app.data.seed_species
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "species.db"

CREATE_SPECIES = """
CREATE TABLE IF NOT EXISTS species (
    id INTEGER PRIMARY KEY,
    common_name TEXT NOT NULL,
    scientific_name TEXT NOT NULL UNIQUE,
    family TEXT,
    light_requirement TEXT CHECK(light_requirement IN ('full_sun', 'partial_shade', 'full_shade', 'variable')),
    par_min_umol REAL,
    par_optimal_umol REAL,
    par_max_umol REAL,
    dli_min REAL,
    dli_optimal REAL,
    photoperiod_type TEXT CHECK(photoperiod_type IN ('short_day', 'long_day', 'day_neutral', NULL)),
    key_wavelengths_json TEXT,
    physiological_notes TEXT,
    description TEXT,
    image_url TEXT
);
"""

CREATE_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS species_fts
USING fts5(common_name, scientific_name, family, content='species', content_rowid='id');
"""

TRIGGER_INSERT = """
CREATE TRIGGER IF NOT EXISTS species_ai AFTER INSERT ON species BEGIN
    INSERT INTO species_fts(rowid, common_name, scientific_name, family)
    VALUES (new.id, new.common_name, new.scientific_name, new.family);
END
"""

TRIGGER_DELETE = """
CREATE TRIGGER IF NOT EXISTS species_ad AFTER DELETE ON species BEGIN
    INSERT INTO species_fts(species_fts, rowid, common_name, scientific_name, family)
    VALUES ('delete', old.id, old.common_name, old.scientific_name, old.family);
END
"""

TRIGGER_UPDATE = """
CREATE TRIGGER IF NOT EXISTS species_au AFTER UPDATE ON species BEGIN
    INSERT INTO species_fts(species_fts, rowid, common_name, scientific_name, family)
    VALUES ('delete', old.id, old.common_name, old.scientific_name, old.family);
    INSERT INTO species_fts(rowid, common_name, scientific_name, family)
    VALUES (new.id, new.common_name, new.scientific_name, new.family);
END
"""

# Datos basados en literatura agronómica real
# Fuentes: Taiz & Zeiger (Plant Physiology), Massa et al. (HortScience),
#          Both et al. (ISHS), Folta & Klee (Plant Cell)
SPECIES_DATA = [
    {
        "common_name": "Tomate",
        "scientific_name": "Solanum lycopersicum",
        "family": "Solanaceae",
        "light_requirement": "full_sun",
        "par_min_umol": 200.0,
        "par_optimal_umol": 800.0,
        "par_max_umol": 2000.0,
        "dli_min": 15.0,
        "dli_optimal": 30.0,
        "photoperiod_type": "day_neutral",
        "key_wavelengths_json": json.dumps({"red_660": 0.9, "blue_450": 0.7, "far_red_730": 0.4}),
        "physiological_notes": "Alta demanda de rojo para fotosíntesis. El azul favorece el cuajado de frutos. Responde bien a la luz continua.",
        "description": "Cultivo frutal anual de alta demanda lumínica. Requiere al menos 8 horas de sol directo.",
        "image_url": None,
    },
    {
        "common_name": "Lechuga",
        "scientific_name": "Lactuca sativa",
        "family": "Asteraceae",
        "light_requirement": "partial_shade",
        "par_min_umol": 100.0,
        "par_optimal_umol": 250.0,
        "par_max_umol": 700.0,
        "dli_min": 8.0,
        "dli_optimal": 17.0,
        "photoperiod_type": "long_day",
        "key_wavelengths_json": json.dumps({"red_660": 0.8, "blue_450": 0.9, "far_red_730": 0.3}),
        "physiological_notes": "El azul es crítico para hojas compactas y sabor. Días largos inducen floración (bolting). Tolera sombra parcial en verano.",
        "description": "Hortícola de hoja anual. Ideal para cultivo en interior o sombra parcial. Sensible al calor.",
        "image_url": None,
    },
    {
        "common_name": "Albahaca",
        "scientific_name": "Ocimum basilicum",
        "family": "Lamiaceae",
        "light_requirement": "full_sun",
        "par_min_umol": 200.0,
        "par_optimal_umol": 600.0,
        "par_max_umol": 1500.0,
        "dli_min": 12.0,
        "dli_optimal": 22.0,
        "photoperiod_type": "day_neutral",
        "key_wavelengths_json": json.dumps({"red_660": 0.8, "blue_450": 0.9, "uv_a_380": 0.6}),
        "physiological_notes": "UV-A estimula producción de aceites esenciales y aromas. El azul favorece hojas compactas y ricas en aceites.",
        "description": "Hierba aromática anual muy usada en cocina. Necesita sol directo y calor. Sensible al frío.",
        "image_url": None,
    },
    {
        "common_name": "Pimiento",
        "scientific_name": "Capsicum annuum",
        "family": "Solanaceae",
        "light_requirement": "full_sun",
        "par_min_umol": 250.0,
        "par_optimal_umol": 900.0,
        "par_max_umol": 2000.0,
        "dli_min": 18.0,
        "dli_optimal": 32.0,
        "photoperiod_type": "day_neutral",
        "key_wavelengths_json": json.dumps({"red_660": 0.9, "blue_450": 0.7, "far_red_730": 0.3}),
        "physiological_notes": "Similar al tomate en demanda lumínica. El rojo es crítico para maduración y síntesis de capsaicina.",
        "description": "Cultivo frutal anual de alta demanda de luz y calor. Incluye pimientos dulces y picantes.",
        "image_url": None,
    },
    {
        "common_name": "Frutilla",
        "scientific_name": "Fragaria × ananassa",
        "family": "Rosaceae",
        "light_requirement": "full_sun",
        "par_min_umol": 200.0,
        "par_optimal_umol": 700.0,
        "par_max_umol": 1800.0,
        "dli_min": 12.0,
        "dli_optimal": 25.0,
        "photoperiod_type": "short_day",
        "key_wavelengths_json": json.dumps({"red_660": 0.9, "blue_450": 0.6, "far_red_730": 0.8}),
        "physiological_notes": "Floración inducida por días cortos (< 12 h) y temperatura baja. Rojo lejano crítico para señal fotoperiódica.",
        "description": "Frutal rastrero perenne. Florece en otoño-invierno (días cortos). Requiere sol directo para buen dulzor.",
        "image_url": None,
    },
    {
        "common_name": "Girasol",
        "scientific_name": "Helianthus annuus",
        "family": "Asteraceae",
        "light_requirement": "full_sun",
        "par_min_umol": 300.0,
        "par_optimal_umol": 1200.0,
        "par_max_umol": 2500.0,
        "dli_min": 20.0,
        "dli_optimal": 40.0,
        "photoperiod_type": "day_neutral",
        "key_wavelengths_json": json.dumps({"red_660": 0.9, "blue_450": 0.7, "far_red_730": 0.5}),
        "physiological_notes": "Heliotropismo marcado en etapa vegetativa. Alta eficiencia fotosintética con luz plena.",
        "description": "Anual de gran porte con flores características. Uso ornamental y oleaginoso. Máxima demanda de sol.",
        "image_url": None,
    },
    {
        "common_name": "Lavanda",
        "scientific_name": "Lavandula angustifolia",
        "family": "Lamiaceae",
        "light_requirement": "full_sun",
        "par_min_umol": 200.0,
        "par_optimal_umol": 700.0,
        "par_max_umol": 2000.0,
        "dli_min": 14.0,
        "dli_optimal": 28.0,
        "photoperiod_type": "long_day",
        "key_wavelengths_json": json.dumps({"red_660": 0.7, "blue_450": 0.8, "uv_a_380": 0.8}),
        "physiological_notes": "UV-A potencia síntesis de aceites esenciales y pigmentos. Días largos inducen floración.",
        "description": "Arbusto perenne aromático de origen mediterráneo. Extremadamente resistente a sequía y sol pleno.",
        "image_url": None,
    },
    {
        "common_name": "Rosa",
        "scientific_name": "Rosa × hybrida",
        "family": "Rosaceae",
        "light_requirement": "full_sun",
        "par_min_umol": 250.0,
        "par_optimal_umol": 800.0,
        "par_max_umol": 2000.0,
        "dli_min": 15.0,
        "dli_optimal": 28.0,
        "photoperiod_type": "day_neutral",
        "key_wavelengths_json": json.dumps({"red_660": 0.9, "blue_450": 0.7, "far_red_730": 0.4}),
        "physiological_notes": "Alta demanda fotosintética. La luz influye en tamaño y color de flores. Mínimo 6 h de sol directo.",
        "description": "Arbusto ornamental con flores fragantes. Requiere sol directo y buena circulación de aire.",
        "image_url": None,
    },
    {
        "common_name": "Monstera",
        "scientific_name": "Monstera deliciosa",
        "family": "Araceae",
        "light_requirement": "partial_shade",
        "par_min_umol": 50.0,
        "par_optimal_umol": 200.0,
        "par_max_umol": 600.0,
        "dli_min": 3.0,
        "dli_optimal": 10.0,
        "photoperiod_type": "day_neutral",
        "key_wavelengths_json": json.dumps({"red_660": 0.8, "blue_450": 0.7, "green_550": 0.9}),
        "physiological_notes": "Verde penetra profundo en hojas grandes. Adaptada a luz filtrada de selva tropical. Tolera baja luz pero crece lento.",
        "description": "Planta tropical de interior con hojas perforadas características. Adaptada a luz indirecta brillante.",
        "image_url": None,
    },
    {
        "common_name": "Pothos",
        "scientific_name": "Epipremnum aureum",
        "family": "Araceae",
        "light_requirement": "full_shade",
        "par_min_umol": 15.0,
        "par_optimal_umol": 80.0,
        "par_max_umol": 300.0,
        "dli_min": 1.5,
        "dli_optimal": 6.0,
        "photoperiod_type": "day_neutral",
        "key_wavelengths_json": json.dumps({"red_660": 0.8, "blue_450": 0.6, "green_550": 0.9}),
        "physiological_notes": "Una de las plantas más tolerantes a baja luz. El verde es importante para fotosíntesis en condiciones de sombra.",
        "description": "Planta trepadora tropical de interior, muy resistente. Tolera rincones oscuros pero crece mejor con luz indirecta.",
        "image_url": None,
    },
    {
        "common_name": "Ficus",
        "scientific_name": "Ficus benjamina",
        "family": "Moraceae",
        "light_requirement": "partial_shade",
        "par_min_umol": 80.0,
        "par_optimal_umol": 300.0,
        "par_max_umol": 800.0,
        "dli_min": 5.0,
        "dli_optimal": 15.0,
        "photoperiod_type": "day_neutral",
        "key_wavelengths_json": json.dumps({"red_660": 0.8, "blue_450": 0.7, "green_550": 0.8}),
        "physiological_notes": "Árbol adaptado a luz filtrada. Sensible a cambios bruscos de luz que causan caída de hojas.",
        "description": "Árbol ornamental de interior. Prefiere luz indirecta brillante y estabilidad en su ubicación.",
        "image_url": None,
    },
    {
        "common_name": "Orquídea mariposa",
        "scientific_name": "Phalaenopsis amabilis",
        "family": "Orchidaceae",
        "light_requirement": "partial_shade",
        "par_min_umol": 50.0,
        "par_optimal_umol": 150.0,
        "par_max_umol": 350.0,
        "dli_min": 3.0,
        "dli_optimal": 8.0,
        "photoperiod_type": "day_neutral",
        "key_wavelengths_json": json.dumps({"red_660": 0.7, "blue_450": 0.6, "far_red_730": 0.5}),
        "physiological_notes": "Fotosíntesis CAM: activa de noche, eficiente con luz moderada. Rojo lejano puede inducir floración.",
        "description": "Orquídea epífita de interior muy popular. Requiere luz indirecta brillante. No tolera sol directo.",
        "image_url": None,
    },
    {
        "common_name": "Suculenta (Echeveria)",
        "scientific_name": "Echeveria elegans",
        "family": "Crassulaceae",
        "light_requirement": "full_sun",
        "par_min_umol": 150.0,
        "par_optimal_umol": 600.0,
        "par_max_umol": 2500.0,
        "dli_min": 10.0,
        "dli_optimal": 25.0,
        "photoperiod_type": "day_neutral",
        "key_wavelengths_json": json.dumps({"red_660": 0.7, "blue_450": 0.9, "uv_a_380": 0.7}),
        "physiological_notes": "Fotosíntesis CAM. UV-A y azul intensifican coloración rojiza (estrés lumínico controlado). Alta tolerancia a luz plena.",
        "description": "Suculenta roseta originaria de México. Muy resistente a sequía. Requiere sol directo para colores vibrantes.",
        "image_url": None,
    },
    {
        "common_name": "Helecho de Boston",
        "scientific_name": "Nephrolepis exaltata",
        "family": "Lomariopsidaceae",
        "light_requirement": "full_shade",
        "par_min_umol": 20.0,
        "par_optimal_umol": 100.0,
        "par_max_umol": 250.0,
        "dli_min": 2.0,
        "dli_optimal": 7.0,
        "photoperiod_type": "day_neutral",
        "key_wavelengths_json": json.dumps({"red_660": 0.7, "blue_450": 0.6, "green_550": 0.9}),
        "physiological_notes": "Muy sensible a sol directo (quema de frondas). Fotosíntesis eficiente a bajas irradiancias con verde y rojo.",
        "description": "Helecho exuberante ideal para interiores húmedos. Requiere sombra y alta humedad ambiental.",
        "image_url": None,
    },
    {
        "common_name": "Cannabis / Cáñamo",
        "scientific_name": "Cannabis sativa",
        "family": "Cannabaceae",
        "light_requirement": "full_sun",
        "par_min_umol": 400.0,
        "par_optimal_umol": 1000.0,
        "par_max_umol": 2500.0,
        "dli_min": 25.0,
        "dli_optimal": 40.0,
        "photoperiod_type": "short_day",
        "key_wavelengths_json": json.dumps({"red_660": 0.9, "blue_450": 0.8, "far_red_730": 0.9, "uv_a_380": 0.7}),
        "physiological_notes": "Floración estricta por días cortos (< 12 h). Rojo y rojo lejano críticos para señal fotoperiódica. UV-A aumenta potencia de cannabinoides.",
        "description": "Planta anual dioica de alta demanda lumínica. Floración controlada por fotoperiodo.",
        "image_url": None,
    },
    {
        "common_name": "Menta",
        "scientific_name": "Mentha × piperita",
        "family": "Lamiaceae",
        "light_requirement": "partial_shade",
        "par_min_umol": 100.0,
        "par_optimal_umol": 400.0,
        "par_max_umol": 1000.0,
        "dli_min": 8.0,
        "dli_optimal": 18.0,
        "photoperiod_type": "long_day",
        "key_wavelengths_json": json.dumps({"red_660": 0.8, "blue_450": 0.8, "uv_a_380": 0.6}),
        "physiological_notes": "UV-A y azul favorecen aceites esenciales. Días largos inducen floración (reduce calidad aromática).",
        "description": "Hierba perenne aromática muy versátil. Crece bien en sombra parcial. Invasiva si no se controla.",
        "image_url": None,
    },
    {
        "common_name": "Petunia",
        "scientific_name": "Petunia × hybrida",
        "family": "Solanaceae",
        "light_requirement": "full_sun",
        "par_min_umol": 200.0,
        "par_optimal_umol": 700.0,
        "par_max_umol": 1800.0,
        "dli_min": 12.0,
        "dli_optimal": 24.0,
        "photoperiod_type": "long_day",
        "key_wavelengths_json": json.dumps({"red_660": 0.8, "blue_450": 0.7, "far_red_730": 0.6}),
        "physiological_notes": "Floración favorecida por días largos y alta irradiancia. Azul y rojo son clave para la síntesis de antocianinas (color floral).",
        "description": "Planta ornamental anual muy popular para macetas y canteros. Floración prolífica con sol pleno.",
        "image_url": None,
    },
    {
        "common_name": "Espinaca",
        "scientific_name": "Spinacia oleracea",
        "family": "Amaranthaceae",
        "light_requirement": "partial_shade",
        "par_min_umol": 80.0,
        "par_optimal_umol": 350.0,
        "par_max_umol": 900.0,
        "dli_min": 7.0,
        "dli_optimal": 16.0,
        "photoperiod_type": "long_day",
        "key_wavelengths_json": json.dumps({"red_660": 0.8, "blue_450": 0.9, "far_red_730": 0.5}),
        "physiological_notes": "Muy sensible al fotoperiodo: días largos (> 14 h) inducen floración rápida. Azul favorece hojas grandes y oscuras ricas en clorofila.",
        "description": "Hortícola de hoja muy nutritiva. Crece bien en primavera y otoño. Florece con los días largos del verano.",
        "image_url": None,
    },
    {
        "common_name": "Zanahoria",
        "scientific_name": "Daucus carota subsp. sativus",
        "family": "Apiaceae",
        "light_requirement": "full_sun",
        "par_min_umol": 150.0,
        "par_optimal_umol": 500.0,
        "par_max_umol": 1500.0,
        "dli_min": 12.0,
        "dli_optimal": 22.0,
        "photoperiod_type": "long_day",
        "key_wavelengths_json": json.dumps({"red_660": 0.9, "blue_450": 0.6, "far_red_730": 0.4}),
        "physiological_notes": "La raíz se desarrolla mejor con alta irradiancia de rojo. El caroteno (color naranja) aumenta con mayor exposición solar.",
        "description": "Hortícola de raíz bianual cultivada como anual. Requiere suelo profundo y sol directo para raíces bien desarrolladas.",
        "image_url": None,
    },
    {
        "common_name": "Cactus (Cereus)",
        "scientific_name": "Cereus repandus",
        "family": "Cactaceae",
        "light_requirement": "full_sun",
        "par_min_umol": 200.0,
        "par_optimal_umol": 800.0,
        "par_max_umol": 3000.0,
        "dli_min": 15.0,
        "dli_optimal": 35.0,
        "photoperiod_type": "day_neutral",
        "key_wavelengths_json": json.dumps({"red_660": 0.7, "blue_450": 0.8, "uv_a_380": 0.9}),
        "physiological_notes": "Fotosíntesis CAM altamente eficiente. UV-A estimula producción de pigmentos protectores y cera cuticular. Tolerancia a irradiancias extremas.",
        "description": "Cactus columnar de gran porte. Extremadamente resistente a sol pleno y sequía. Ideal para exteriores.",
        "image_url": None,
    },
]


def create_db(conn: sqlite3.Connection) -> None:
    conn.execute(CREATE_SPECIES)
    conn.execute(CREATE_FTS)
    conn.execute(TRIGGER_INSERT)
    conn.execute(TRIGGER_DELETE)
    conn.execute(TRIGGER_UPDATE)
    conn.commit()


def seed_db(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM species")
    conn.commit()

    for sp in SPECIES_DATA:
        conn.execute(
            """
            INSERT INTO species (
                common_name, scientific_name, family, light_requirement,
                par_min_umol, par_optimal_umol, par_max_umol,
                dli_min, dli_optimal, photoperiod_type,
                key_wavelengths_json, physiological_notes, description, image_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sp["common_name"], sp["scientific_name"], sp["family"],
                sp["light_requirement"], sp["par_min_umol"], sp["par_optimal_umol"],
                sp["par_max_umol"], sp["dli_min"], sp["dli_optimal"],
                sp["photoperiod_type"], sp["key_wavelengths_json"],
                sp["physiological_notes"], sp["description"], sp["image_url"],
            ),
        )
    conn.commit()
    print(f"OK: {len(SPECIES_DATA)} especies insertadas en {DB_PATH}")


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    create_db(conn)
    seed_db(conn)
    conn.close()


if __name__ == "__main__":
    main()
