from __future__ import annotations

import json
from pathlib import Path

from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601


def test_fichas_tecnicas_601_promueve_receta_a_entidad_central(tmp_path: Path) -> None:
    repo = RepositorioBibliotecaRecetas601(tmp_path)

    creado = repo.crear_ficha_tecnica(
        {
            "codigo": "FT-601-001",
            "nombre": "Carrillera prensada",
            "familia": "CARNES",
            "categoria": "Principal",
            "tipo": "PLATO",
            "descripcion": "Carrillera cocinada y prensada para servicio.",
            "numero_raciones": 12,
            "ingredientes": ["Carrillera", "Vino tinto"],
            "cantidades": ["3 kg", "1 l"],
            "elaboracion": "Cocinar, prensar y enfriar.",
            "tecnicas_culinarias": ["Braise", "Prensado"],
            "tiempo_activo": "45 min",
            "produccion_maxima": "24 raciones",
            "personal_recomendado": "2 cocineros",
            "regeneracion": "12 min horno mixto",
            "vida_util_congelado": "90 dias",
        }
    )

    assert creado.get("ok") is True
    ficha = creado.get("receta") or {}
    assert ficha.get("categoria") == "Principal"
    assert (ficha.get("ficha_tecnica") or {}).get("informacion_general", {}).get("nombre") == "Carrillera prensada"
    assert (ficha.get("ficha_tecnica") or {}).get("receta", {}).get("ingredientes") == ["Carrillera", "Vino tinto"]
    assert (ficha.get("ficha_tecnica") or {}).get("produccion", {}).get("produccion_maxima") == "24 raciones"

    completitud = dict(ficha.get("completitud") or {})
    pendientes = list(completitud.get("campos_obligatorios_pendientes") or [])
    assert "Tiempo de regeneración" not in pendientes
    assert "Vida útil congelada" not in pendientes
    assert "Producción máxima por tanda" not in pendientes
    assert "Categoría" not in pendientes
    assert "Descripción" not in pendientes or isinstance(pendientes, list)

    obtenido = repo.obtener("FT-601-001") or {}
    assert obtenido.get("nombre") == "Carrillera prensada"
    assert obtenido.get("ingredientes") == ["Carrillera", "Vino tinto"]
    assert (obtenido.get("ficha_tecnica") or {}).get("conservacion", {}).get("vida_util_congelado") == "90 dias"

    payload = json.loads((tmp_path / "DATOS" / "db" / "biblioteca_recetas_601.json").read_text(encoding="utf-8"))
    assert isinstance(payload.get("recetas"), list)
    assert isinstance(payload.get("fichas_tecnicas"), list)
    assert payload.get("fichas_tecnicas") == payload.get("recetas")


def test_fichas_tecnicas_601_detecta_pendientes_operativos(tmp_path: Path) -> None:
    repo = RepositorioBibliotecaRecetas601(tmp_path)

    res = repo.crear_ficha_tecnica(
        {
            "codigo": "FT-601-002",
            "nombre": "Pure base",
            "familia": "BASES",
            "tipo": "SUBELABORACION",
            "numero_raciones": 6,
            "ingredientes": ["Patata"],
            "cantidades": ["2 kg"],
            "elaboracion": "Cocer y triturar.",
        }
    )
    assert res.get("ok") is True

    pendientes = repo.pendientes_fichas_tecnicas()
    assert len(pendientes) == 1
    faltantes = list(((pendientes[0].get("completitud") or {}).get("campos_obligatorios_pendientes") or []))
    assert "Categoría" in faltantes
    assert "Tiempo activo" in faltantes
    assert "Producción máxima por tanda" in faltantes