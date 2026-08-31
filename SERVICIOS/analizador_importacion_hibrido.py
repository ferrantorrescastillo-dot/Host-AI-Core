from __future__ import annotations

import base64
import tempfile
import unicodedata
from copy import deepcopy
from pathlib import Path
from typing import Any

from SERVICIOS.analizador_importacion_restaurante import RestaurantDataImportAnalyzer
from SERVICIOS.clasificador_hojas_excel_555b import ClasificadorHojasExcel555B
from SERVICIOS.lector_escandallos_excel_555b import LectorEscandallosExcel555B
from SERVICIOS.perfil_mapeo_escandallos_555b import PerfilMapeoEscandallos555B
from SERVICIOS.preimportador_escandallos_555b import PreimportadorEscandallosExcel555B


def _name_key(value: Any) -> str:
    text = "".join(c for c in unicodedata.normalize("NFKD", str(value or "").casefold())
                   if not unicodedata.combining(c))
    tokens = [token for token in "".join(c if c.isalnum() else " " for c in text).split()
              if token not in {"de", "del", "la", "el", "las", "los", "una", "un"}]
    return " ".join(tokens)


def _ingredient_keys(recipe: dict[str, Any]) -> set[str]:
    return {_name_key(item.get("nombre_original") or item.get("nombre"))
            for item in recipe.get("ingredientes_estructurados") or []
            if _name_key(item.get("nombre_original") or item.get("nombre"))}


def _overlap(left: dict[str, Any], right: dict[str, Any]) -> float:
    a, b = _ingredient_keys(left), _ingredient_keys(right)
    return len(a & b) / len(a | b) if a and b else 0.0


class HybridRestaurantImportAnalyzer:
    """Read-only orchestration: legacy evidence first, structural coverage second."""

    def __init__(self, base_dir: Path, structural: RestaurantDataImportAnalyzer) -> None:
        self.base_dir = Path(base_dir)
        self.structural = structural

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        analysis = self.structural.analyze(payload)
        historical: list[dict[str, Any]] = []
        historical_applied = False
        profiles: list[dict[str, Any]] = []
        technical: list[dict[str, Any]] = []
        for item in payload.get("archivos") or []:
            name = Path(str(item.get("nombre") or "")).name
            if Path(name).suffix.lower() != ".xlsx":
                continue
            content = self._bytes(item)
            if not content:
                continue
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as handle:
                handle.write(content)
                path = Path(handle.name)
            try:
                classification = ClasificadorHojasExcel555B().analizar(path)
                compatible = any(
                    sheet.get("tipo") == "FICHAS_TECNICAS" and sheet.get("bloques")
                    for sheet in classification.get("hojas") or []
                )
                if not compatible:
                    continue
                historical_applied = True
                reader = LectorEscandallosExcel555B().analizar(path)
                for sheet in reader.get("hojas") or []:
                    if not sheet.get("mapeo_sugerido"):
                        continue
                    profile = PerfilMapeoEscandallos555B(
                        nombre=f"AUTO-{_name_key(name)}-{_name_key(sheet.get('nombre'))}",
                        hoja=str(sheet.get("nombre") or ""),
                        fila_cabecera=int(sheet.get("fila_cabecera") or 1),
                        mapeo=dict(sheet.get("mapeo_sugerido") or {}),
                    )
                    profiles.append({
                        "nombre": profile.nombre, "hoja": profile.hoja,
                        "fila_cabecera": profile.fila_cabecera, "mapeo": profile.mapeo,
                        "version": profile.version, "persistido": False,
                    })
                preview = PreimportadorEscandallosExcel555B(
                    ruta_articulos=self.base_dir / "DATOS/db/articulos.json",
                    ruta_destino=self.base_dir / "DATOS/db/escandallos_canonicos.json",
                ).ejecutar(path, confirmar=False)
                for sheet in classification.get("hojas") or []:
                    for block in sheet.get("bloques") or []:
                        block.setdefault("archivo", name)
                historical.extend(self._recipes(preview, name))
                technical.extend({"origen": "HISTORICO", "tipo": "FICHA_OMITIDA", "detalle": f}
                                 for f in preview.get("fichas") or [] if f.get("accion") == "OMITIR")
            finally:
                path.unlink(missing_ok=True)

        structural_count = len(analysis.get("recetas") or [])
        consolidated, variants = self._consolidate(
            historical, list(analysis.get("recetas") or [])
        )
        warnings = list(analysis.get("dudas", {}).get("precio") or []) + technical
        ambiguous = list(analysis.get("regiones_ambiguas") or [])
        layout_decisions = {}
        for region in ambiguous:
            signature = self._layout_key(region)
            layout_decisions.setdefault(signature, {
                "tipo": "MAPPING_AMBIGUO", "region_id": region.get("region_id"),
                "hoja": region.get("hoja"), "regiones_equivalentes": 0,
            })["regiones_equivalentes"] += 1
        decisions = list(layout_decisions.values())
        decisions.extend(analysis.get("dudas", {}).get("relaciones") or [])
        decisions.extend(variants)
        analysis["recetas"] = consolidated
        analysis["perfiles_importacion"] = profiles
        analysis["warnings_tecnicos"] = warnings
        analysis["decisiones_usuario"] = decisions
        analysis["resultado_hibrido"] = {
            "historico_compatible": historical_applied,
            "candidatos_historicos": len(historical),
            "candidatos_estructurales": structural_count,
            "recetas_consolidadas": len(consolidated),
            "perfiles_reutilizados": len(profiles),
            "variantes": len(variants),
            "warnings_tecnicos": len(warnings),
            "decisiones_usuario": len(decisions),
        }
        analysis["resumen"].update({
            "posibles_recetas": len(consolidated),
            "warnings_tecnicos": len(warnings),
            "decisiones_usuario": len(decisions),
            "ambiguedades": len(decisions),
        })
        return analysis

    @staticmethod
    def _bytes(item: dict[str, Any]) -> bytes:
        raw = item.get("contenido_base64")
        if raw:
            try: return base64.b64decode(str(raw), validate=True)
            except (ValueError, TypeError): return b""
        return bytes(item.get("contenido") or b"")

    @staticmethod
    def _recipes(preview: dict[str, Any], filename: str) -> list[dict[str, Any]]:
        output = []
        for item in preview.get("fichas") or []:
            if item.get("accion") == "OMITIR" or item.get("estado") != "PREPARADA":
                continue
            ingredients = [{
                "nombre_original": ing.get("nombre"), "cantidad": ing.get("cantidad"),
                "cantidad_texto": str(ing.get("cantidad") or ""), "unidad": ing.get("unidad"),
                "precio_unitario": ing.get("precio_unitario"), "article_id": ing.get("articulo_id"),
                "trazabilidad": {"archivo": filename, "hoja": item.get("hoja"),
                                  "fila": (ing.get("metadata") or {}).get("fila_origen"),
                                  "origen_detector": "HISTORICO"},
            } for ing in item.get("ingredientes") or []]
            output.append({
                "id_origen": item.get("codigo"), "nombre": item.get("nombre"),
                "ingredientes_estructurados": ingredients, "rendimiento": item.get("rendimiento"),
                "numero_raciones": item.get("rendimiento"), "pasos": [],
                "bloques_origen": [{"archivo": filename, "hoja": item.get("hoja"),
                                     "fila_inicio": item.get("fila_inicio"),
                                     "fila_fin": item.get("fila_fin")}],
                "origen_detector": "HISTORICO", "origenes_detector": ["HISTORICO"],
                "confidence": float(item.get("confianza") or 0) / 100,
            })
        return output

    @staticmethod
    def _layout_key(region: dict[str, Any]) -> tuple[str, ...]:
        return tuple(str(value).strip().casefold() for value in region.get("headers") or [])

    def _consolidate(
        self, historical: list[dict[str, Any]], structural: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        remaining = [deepcopy(item) for item in structural]
        for item in remaining:
            item["origen_detector"] = "ESTRUCTURAL"
            item["origenes_detector"] = ["ESTRUCTURAL"]
        result: list[dict[str, Any]] = []
        variants: list[dict[str, Any]] = []
        for legacy in historical:
            same_name = [item for item in remaining if _name_key(item.get("nombre")) == _name_key(legacy.get("nombre"))]
            compatible = [item for item in same_name if _overlap(legacy, item) >= 0.6]
            if compatible:
                selected = max(compatible, key=lambda item: _overlap(legacy, item))
                legacy["origenes_detector"] = ["HISTORICO", "ESTRUCTURAL"]
                legacy["evidencia_complementaria"] = selected.get("bloques_origen") or []
                remaining.remove(selected)
            result.append(legacy)
        combined = result + remaining
        grouped: dict[str, list[dict[str, Any]]] = {}
        for recipe in combined:
            grouped.setdefault(_name_key(recipe.get("nombre")), []).append(recipe)
        final: list[dict[str, Any]] = []
        for key, group in grouped.items():
            unique: list[dict[str, Any]] = []
            for recipe in group:
                duplicate = next((item for item in unique if _overlap(recipe, item) >= 0.98), None)
                if duplicate:
                    duplicate["origenes_detector"] = sorted(set(
                        duplicate.get("origenes_detector", []) + recipe.get("origenes_detector", [])
                    ))
                    duplicate.setdefault("evidencia_complementaria", []).extend(
                        recipe.get("bloques_origen") or []
                    )
                else:
                    unique.append(recipe)
            if len(unique) > 1:
                for recipe in unique:
                    recipe["posible_variante"] = True
                variants.append({"tipo": "POSIBLE_VARIANTE", "nombre": unique[0].get("nombre"),
                                 "versiones": len(unique), "motivo": "Mismo nombre y estructuras distintas."})
            final.extend(unique)
        return final, variants
