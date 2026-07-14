from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from SERVICIOS.bandeja_correccion_postimportacion_i13441 import BandejaCorreccionPostimportacionI13441


class DiagnosticoBandejaCorreccionI13441:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir).resolve()

    def ejecutar(self) -> dict[str, Any]:
        root = self.base_dir / "DATOS" / "mur" / "diagnostico_i13441"
        root.mkdir(parents=True, exist_ok=True)
        menus = [{
            "menu_id": "M1", "nombre": "Menu demo", "secciones": [{"seccion_id": "S1", "nombre": "Principal"}],
            "platos": [{"plato_id": "P1", "nombre": "Plato demo", "seccion": "Postre", "componentes": []}],
            "articulos_directos": [{"nombre": "Pan inexistente"}], "bebidas": [], "complementos": [], "servicios": [],
            "economico": {"precio_venta": 10, "coste_total": 3, "food_cost_pct": 99, "beneficio": None},
            "resumen": {"secciones": 1, "platos": 1, "componentes": 0, "articulos_directos": 1, "bebidas": 0, "complementos": 0},
        }]
        recetas = [{"receta_id": "R1", "nombre": "Receta demo"}]
        articulos = [{"codigo": "A1", "nombre": "Pan"}]
        for name, data in [("menus.json", menus), ("recetas.json", recetas), ("articulos.json", articulos)]:
            (root / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        b = BandejaCorreccionPostimportacionI13441(self.base_dir,
            "DATOS/mur/diagnostico_i13441/menus.json",
            "DATOS/mur/diagnostico_i13441/recetas.json",
            "DATOS/mur/diagnostico_i13441/articulos.json")
        inicial = b.resumen()
        # Crear/vincular receta principal, corregir sección y economía, vincular artículo.
        idx_plato = next(i for i,x in enumerate(b.incidencias(),1) if x["codigo"]=="PLATO_SIN_RECETA_PRINCIPAL")
        b.vincular_receta(idx_plato, recetas[0])
        idx_sec = next(i for i,x in enumerate(b.incidencias(),1) if x["codigo"]=="SECCION_REFERENCIA_INEXISTENTE")
        b.cambiar_seccion([idx_sec], "Principal")
        idx_art = next(i for i,x in enumerate(b.incidencias(),1) if x["codigo"]=="ARTICULO_REFERENCIA_INEXISTENTE")
        b.vincular_articulo(idx_art, articulos[0])
        b.recalcular_economia()
        resultado = b.guardar(confirmar=True)
        final = resultado["auditoria"]
        return {
            "diagnostico": "OK" if final["resumen"]["errores"]==0 else "ERROR",
            "inicial": inicial,
            "final": final["resumen"],
            "estado_final": final["estado"],
            "transaccion": resultado["transaccion"],
            "archivo_aislado": str(root / "menus.json"),
        }


def formatear_diagnostico_i13441(r: dict[str, Any]) -> str:
    return "\n".join([
        "I1.3.4.4.1 — BANDEJA DE CORRECCIÓN POSTIMPORTACIÓN",
        "="*78,
        f"Diagnóstico: {r['diagnostico']} | Estado final: {r['estado_final']}",
        f"Incidencias iniciales: {r['inicial']['total']} | Errores iniciales: {r['inicial']['errores']} | Avisos iniciales: {r['inicial']['avisos']}",
        f"Errores finales: {r['final']['errores']} | Avisos finales: {r['final']['avisos']}",
        f"Transacción: {r['transaccion']['estado']} | Backup: {r['transaccion']['backup_dir']} | Integridad: {'OK' if r['transaccion']['integridad_ok'] else 'ERROR'}",
        f"Archivo aislado: {r['archivo_aislado']}",
        "-"*78,
        "Se validó vinculación, cambio de sección, economía, artículo, commit, backup y reauditoría.",
        "El diagnóstico no modifica DATOS/db/menus.json.",
    ])
