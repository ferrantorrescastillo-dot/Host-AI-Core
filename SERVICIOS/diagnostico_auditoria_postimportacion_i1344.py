from __future__ import annotations

import json
from pathlib import Path

from SERVICIOS.auditor_integridad_postimportacion_i1344 import AuditorIntegridadPostimportacionI1344, formatear_auditoria_i1344


class DiagnosticoAuditoriaPostimportacionI1344:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir).resolve()
        self.root = self.base_dir / "DATOS/mur/diagnostico_i1344"

    def ejecutar(self):
        self.root.mkdir(parents=True, exist_ok=True)
        menus = [{
            "menu_id": "MENU-DIAG-1344", "nombre": "MENÚ DIAGNÓSTICO", "estado": "ACTIVO",
            "secciones": [{"seccion_id": "SEC-1", "nombre": "PRINCIPAL"}],
            "platos": [{
                "plato_id": "PLATO-1", "nombre": "Solomillo diagnóstico", "seccion": "PRINCIPAL",
                "componentes": [{"componente_id": "COMP-1", "rol": "RECETA_PRINCIPAL", "nombre": "Solomillo de cerdo", "plato_id": "PLATO-1", "catalogado": True}],
            }],
            "articulos_directos": [{"nombre": "Pan individual", "tipo": "ARTICULO_DIRECTO", "coste_racion": 0.2}],
            "bebidas": [], "complementos": [], "servicios": [],
            "economico": {"precio_venta": 50, "coste_total": 12, "food_cost_pct": 24, "beneficio": 38},
            "resumen": {"secciones": 1, "platos": 1, "componentes": 1, "articulos_directos": 1, "bebidas": 0, "complementos": 0},
        }]
        recetas = [{"receta_id": "REC-SOLOMILLO", "nombre": "Solomillo de cerdo", "activo": True}]
        articulos = [{"codigo": "ART-PAN", "nombre": "Pan individual", "activo": True}]
        for nombre, data in (("menus.json", menus), ("recetas.json", recetas), ("articulos.json", articulos)):
            (self.root / nombre).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        auditor = AuditorIntegridadPostimportacionI1344(
            self.base_dir,
            ruta_menus="DATOS/mur/diagnostico_i1344/menus.json",
            ruta_recetas="DATOS/mur/diagnostico_i1344/recetas.json",
            ruta_articulos="DATOS/mur/diagnostico_i1344/articulos.json",
            ruta_informes="DATOS/mur/diagnostico_i1344/informes",
        )
        resultado = auditor.auditar(guardar_informe=True)
        resultado["diagnostico"] = "OK" if resultado["estado"] == "CERTIFICADA" else "ERROR"
        resultado["archivo_aislado"] = str(self.root / "menus.json")
        return resultado


def formatear_diagnostico_i1344(r):
    return "\n".join([
        formatear_auditoria_i1344(r, detalle=True),
        f"Diagnóstico: {r.get('diagnostico')} | Archivo aislado: {r.get('archivo_aislado')}",
        "Se validó estructura, referencias, duplicados, economía, informe y certificado.",
        "El diagnóstico no modificó DATOS/db/menus.json ni otros datos reales.",
    ])
