"""
Servicio de consultas a la base de datos de especies.

Usa aiosqlite para operaciones async compatibles con FastAPI.
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional

import aiosqlite

DB_PATH = Path(__file__).parent.parent / "data" / "species.db"


def _row_to_dict(row: aiosqlite.Row) -> dict:
    d = dict(row)
    if d.get("key_wavelengths_json"):
        try:
            d["key_wavelengths"] = json.loads(d["key_wavelengths_json"])
        except (json.JSONDecodeError, TypeError):
            d["key_wavelengths"] = {}
    else:
        d["key_wavelengths"] = {}
    return d


async def get_species_by_id(species_id: int) -> Optional[dict]:
    """Obtiene una especie por su ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM species WHERE id = ?", (species_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return _row_to_dict(row) if row else None


async def search_species(query: str, limit: int = 20) -> list[dict]:
    """
    Busca especies usando full-text search (FTS5).

    Si la query está vacía, devuelve las primeras `limit` especies.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if not query.strip():
            async with db.execute(
                "SELECT * FROM species ORDER BY common_name LIMIT ?", (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [_row_to_dict(r) for r in rows]

        # FTS5: busca en common_name, scientific_name, family
        fts_query = " OR ".join(f'"{term}"' for term in query.strip().split())
        async with db.execute(
            """
            SELECT s.* FROM species s
            JOIN species_fts fts ON s.id = fts.rowid
            WHERE species_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (fts_query, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [_row_to_dict(r) for r in rows]


async def get_all_species(limit: int = 100) -> list[dict]:
    """Devuelve todas las especies ordenadas por nombre común."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM species ORDER BY common_name LIMIT ?", (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [_row_to_dict(r) for r in rows]


def get_species_by_id_sync(species_id: int) -> Optional[dict]:
    """Versión síncrona de get_species_by_id (para tests y scripts)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM species WHERE id = ?", (species_id,)
        ).fetchone()
        if row is None:
            return None
        d = dict(row)
        if d.get("key_wavelengths_json"):
            try:
                d["key_wavelengths"] = json.loads(d["key_wavelengths_json"])
            except (json.JSONDecodeError, TypeError):
                d["key_wavelengths"] = {}
        else:
            d["key_wavelengths"] = {}
        return d


def search_species_sync(query: str, limit: int = 20) -> list[dict]:
    """Versión síncrona de search_species (para tests y scripts)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        if not query.strip():
            rows = conn.execute(
                "SELECT * FROM species ORDER BY common_name LIMIT ?", (limit,)
            ).fetchall()
        else:
            fts_query = " OR ".join(f'"{term}"' for term in query.strip().split())
            rows = conn.execute(
                """
                SELECT s.* FROM species s
                JOIN species_fts fts ON s.id = fts.rowid
                WHERE species_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (fts_query, limit),
            ).fetchall()

        result = []
        for row in rows:
            d = dict(row)
            if d.get("key_wavelengths_json"):
                try:
                    d["key_wavelengths"] = json.loads(d["key_wavelengths_json"])
                except (json.JSONDecodeError, TypeError):
                    d["key_wavelengths"] = {}
            else:
                d["key_wavelengths"] = {}
            result.append(d)
        return result
