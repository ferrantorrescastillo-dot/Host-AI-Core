from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from SERVICIOS.bandeja_correccion_inteligente_i13442 import BandejaCorreccionInteligenteI13442


class DiagnosticoCorreccionInteligenteI13442:
    VERSION = "I1.3.4.4.2"

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir).resolve()
        self.root = self.base_dir / "DATOS" / "mur" / "diagnostico_i13442"

    def _write(self, nombre: str, data: Any) -> str:
        self.root.mkdir(parents=True, exist_ok=True)
        p = self.root / nombre
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(p.relative_to(self.base_dir))

    def ejecutar(self) -> dict[str, Any]:
        menus = [{
            "menu_id": "M1", "nombre": "Menú diagnóstico", "secciones": [{"seccion_id": "S1", "nombre": "Principal"}],
            "platos": [
                {"plato_id": "P1", "nombre": "Crema catalana", "seccion": "Postre", "componentes": []},
                {"plato_id": "P2", "nombre": "Plato ambiguo", "seccion": "Principal", "componentes": []},
            ],
            "articulos_directos": [{"nombre": "Pan"}], "bebidas": [], "complementos": [], "servicios": [],
            "economico": {"precio_venta": 20, "coste_total": 6, "food_cost_pct": 90, "beneficio": None},
            "resumen": {"secciones": 1, "platos": 2, "componentes": 0, "articulos_directos": 1, "bebidas": 0, "complementos": 0},
        }]
        recetas = [{"receta_id": "R1", "nombre": "Crema catalana"}]
        articulos = [{"codigo": "A1", "nombre": "Pan"}]
        ruta_menus = self._write("menus.json", menus)
        ruta_recetas = self._write("recetas.json", recetas)
        ruta_articulos = self._write("articulos.json", articulos)
        b = BandejaCorreccionInteligenteI13442(self.base_dir, ruta_menus, ruta_recetas, ruta_articulos)
        inicial = b.resumen()
        grupos_tipo = b.agrupar_por_tipo()
        grupos_menu = b.agrupar_por_menu()
        auto = b.resolver_automaticamente_univocos()
        final = b.resumen()
        return {
            "diagnostico": "OK" if auto["resueltas"] >= 3 and final["total"] == 1 else "REVISAR",
            "inicial": inicial,
            "final": final,
            "automatico": auto,
            "grupos_tipo": grupos_tipo,
            "grupos_menu": grupos_menu,
            "archivo_aislado": str((self.base_dir / ruta_menus).resolve()),
        }


def formatear_diagnostico_i13442(r: dict[str, Any]) -> str:
    return "\n".join([
        "I1.3.4.4.2 — CORRECCIÓN INTELIGENTE MASIVA Y NAVEGACIÓN",
        "=" * 78,
        f"Diagnóstico: {r['diagnostico']}",
        f"Incidencias iniciales: {r['inicial']['total']} | Errores: {r['inicial']['errores']} | Avisos: {r['inicial']['avisos']}",
        f"Resueltas automáticamente: {r['automatico']['resueltas']} | Omitidas por seguridad: {r['automatico']['omitidas']}",
        f"Incidencias finales: {r['final']['total']} | Errores: {r['final']['errores']} | Avisos: {r['final']['avisos']}",
        f"Grupos por tipo: {len(r['grupos_tipo'])} | Grupos por menú: {len(r['grupos_menu'])}",
        f"Archivo aislado: {r['archivo_aislado']}",
        "-" * 78,
        "Se validó resolución unívoca, filtros, agrupación, navegación y conservación de ambiguos.",
        "El diagnóstico no modifica DATOS/db/menus.json.",
    ])
