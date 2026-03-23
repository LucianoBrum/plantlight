"""
Tests de la base de datos de especies.

Usa las funciones síncronas del servicio para verificar
que la DB está correctamente poblada y que las búsquedas funcionan.
"""

import pytest
from app.services.species_db import get_species_by_id_sync, search_species_sync


class TestGetSpeciesById:
    def test_existing_id_returns_species(self):
        sp = get_species_by_id_sync(1)
        assert sp is not None
        assert "common_name" in sp
        assert "scientific_name" in sp

    def test_nonexistent_id_returns_none(self):
        sp = get_species_by_id_sync(99999)
        assert sp is None

    def test_species_has_required_fields(self):
        sp = get_species_by_id_sync(1)
        for field in ["id", "common_name", "scientific_name", "family",
                      "light_requirement", "par_min_umol", "par_optimal_umol",
                      "par_max_umol", "dli_min", "dli_optimal"]:
            assert field in sp

    def test_par_values_are_positive(self):
        sp = get_species_by_id_sync(1)
        assert sp["par_min_umol"] > 0
        assert sp["par_optimal_umol"] > sp["par_min_umol"]

    def test_key_wavelengths_parsed(self):
        """key_wavelengths debe ser un dict parseado del JSON."""
        sp = get_species_by_id_sync(1)
        assert isinstance(sp["key_wavelengths"], dict)
        assert len(sp["key_wavelengths"]) > 0

    def test_light_requirement_valid(self):
        sp = get_species_by_id_sync(1)
        assert sp["light_requirement"] in ("full_sun", "partial_shade", "full_shade", "variable")


class TestSearchSpecies:
    def test_empty_query_returns_all(self):
        results = search_species_sync("", limit=100)
        assert len(results) >= 20

    def test_search_tomate(self):
        results = search_species_sync("tomate")
        assert any("tomate" in r["common_name"].lower() for r in results)

    def test_search_scientific_name(self):
        results = search_species_sync("lactuca")
        assert any("Lactuca" in r["scientific_name"] for r in results)

    def test_search_family(self):
        results = search_species_sync("solanaceae")
        assert len(results) > 0

    def test_search_nonexistent_returns_empty(self):
        results = search_species_sync("xyzxyzxyz_no_existe")
        assert results == []

    def test_limit_respected(self):
        results = search_species_sync("", limit=3)
        assert len(results) <= 3

    def test_results_are_dicts(self):
        results = search_species_sync("rosa")
        for r in results:
            assert isinstance(r, dict)


class TestDbConsistency:
    def test_all_species_have_par_range_ordered(self):
        """par_min <= par_optimal <= par_max para todas las especies."""
        results = search_species_sync("", limit=100)
        for sp in results:
            if sp["par_min_umol"] and sp["par_optimal_umol"] and sp["par_max_umol"]:
                assert sp["par_min_umol"] <= sp["par_optimal_umol"], \
                    f"{sp['common_name']}: par_min > par_optimal"
                assert sp["par_optimal_umol"] <= sp["par_max_umol"], \
                    f"{sp['common_name']}: par_optimal > par_max"

    def test_all_species_have_dli_range_ordered(self):
        """dli_min <= dli_optimal para todas las especies."""
        results = search_species_sync("", limit=100)
        for sp in results:
            if sp["dli_min"] and sp["dli_optimal"]:
                assert sp["dli_min"] <= sp["dli_optimal"], \
                    f"{sp['common_name']}: dli_min > dli_optimal"

    def test_photoperiod_type_valid(self):
        valid = {"short_day", "long_day", "day_neutral", None}
        results = search_species_sync("", limit=100)
        for sp in results:
            assert sp["photoperiod_type"] in valid, \
                f"{sp['common_name']}: photoperiod inválido: {sp['photoperiod_type']}"

    def test_at_least_one_full_sun(self):
        results = search_species_sync("", limit=100)
        assert any(r["light_requirement"] == "full_sun" for r in results)

    def test_at_least_one_shade(self):
        results = search_species_sync("", limit=100)
        assert any(r["light_requirement"] in ("full_shade", "partial_shade") for r in results)
