from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from SERVICIOS.detector_limpio_menus_i131 import DetectorLimpioMenusI131
from SERVICIOS.motor_aprendizaje_culinario_i1324 import MotorAprendizajeCulinarioI1324


class PreimportadorDefinitivoMenusI133:
    """I1.3.3 — construye el contrato final de importación sin escribir datos."""

    VERSION = "I1.3.3"

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir).resolve()
        self.aprendizaje = MotorAprendizajeCulinarioI1324(self.base_dir)

    @staticmethod
    def _componentes(arbol: dict[str, Any]) -> list[dict[str, Any]]:
        salida: list[dict[str, Any]] = []
        principal = arbol.get("receta_principal")
        if principal:
            salida.append({**deepcopy(principal), "grupo": "RECETA_PRINCIPAL"})
        for campo, grupo in (
            ("elaboraciones", "ELABORACION"),
            ("guarniciones", "GUARNICION"),
            ("salsas", "SALSA"),
            ("articulos_directos", "ARTICULO_DIRECTO"),
            ("componentes_pendientes", "COMPONENTE_PENDIENTE"),
        ):
            for item in arbol.get(campo, []):
                salida.append({**deepcopy(item), "grupo": grupo})
        return salida

    @staticmethod
    def _bloqueo_componente(menu: str, plato: str, componente: dict[str, Any]) -> dict[str, Any] | None:
        accion = componente.get("resolucion")
        if componente.get("catalogado"):
            return None
        if accion == "PROPONER_NUEVA_RECETA" or componente.get("estado") == "PROPUESTA_NUEVA_RECETA":
            return {
                "codigo": "RECETA_PROPUESTA_NO_CREADA",
                "nivel": "BLOQUEO",
                "menu": menu,
                "plato": plato,
                "componente": componente.get("nombre"),
                "rol": componente.get("rol"),
                "mensaje": "Existe una propuesta de nueva receta que todavía no forma parte del catálogo.",
                "acciones": [
                    "Crear y completar la receta",
                    "Vincularla con una receta existente",
                    "Mantenerla pendiente solo si una política futura lo permite",
                ],
            }
        return {
            "codigo": "COMPONENTE_NO_RESUELTO",
            "nivel": "BLOQUEO",
            "menu": menu,
            "plato": plato,
            "componente": componente.get("nombre"),
            "rol": componente.get("rol"),
            "mensaje": "Existe un componente sin vínculo definitivo.",
            "acciones": ["Vincular con receta", "Vincular con artículo", "Crear receta y completar ficha"],
        }

    def preparar(self, ruta_excel: str | Path, hojas: list[str] | None = None) -> dict[str, Any]:
        sem = self.aprendizaje.preparar_desde_excel(ruta_excel, hojas=hojas)
        limpia = DetectorLimpioMenusI131().preparar(ruta_excel, hojas=hojas)
        limpia_por_hoja = {m.get("hoja"): m for m in limpia.get("menus", [])}

        menus_finales = []
        bloqueos = []
        total_platos = total_componentes = 0
        for menu in sem.get("menus", []):
            origen = limpia_por_hoja.get(menu.get("hoja"), {})
            platos = []
            for plato in menu.get("platos", []):
                arbol = plato.get("semantica", {}).get("arbol", {})
                componentes = self._componentes(arbol)
                total_componentes += len(componentes)
                total_platos += 1
                for componente in componentes:
                    bloqueo = self._bloqueo_componente(menu.get("nombre"), plato.get("nombre"), componente)
                    if bloqueo:
                        bloqueos.append(bloqueo)
                platos.append({
                    "nombre_original": plato.get("nombre"),
                    "seccion": plato.get("seccion"),
                    "fila": plato.get("fila"),
                    "cantidad": plato.get("cantidad"),
                    "coste_racion": plato.get("coste_racion"),
                    "estado_semantico": plato.get("semantica", {}).get("estado_semantico"),
                    "componentes": componentes,
                })
            menus_finales.append({
                "nombre": menu.get("nombre"),
                "hoja": menu.get("hoja"),
                "secciones": origen.get("secciones", []),
                "platos": platos,
                "articulos_directos": deepcopy(menu.get("articulos_directos", [])),
                "complementos": deepcopy(menu.get("complementos", [])),
                "economico": deepcopy(origen.get("economico", {})),
                "avisos_detector": deepcopy(origen.get("avisos", [])),
            })

        importable = len(bloqueos) == 0 and bool(menus_finales)
        return {
            "version": self.VERSION,
            "menus": menus_finales,
            "resumen": {
                "menus": len(menus_finales),
                "platos": total_platos,
                "componentes": total_componentes,
                "articulos_directos": sum(len(m["articulos_directos"]) for m in menus_finales),
                "complementos": sum(len(m["complementos"]) for m in menus_finales),
                "bloqueos": len(bloqueos),
                "aprendizajes_aplicados": sem.get("resumen_aprendizaje", {}).get("aprendizajes_aplicados", 0),
            },
            "bloqueos": bloqueos,
            "estado_preimportacion": "LISTA" if importable else "BLOQUEADA",
            "importacion_disponible": False,
            "solo_preimportacion": True,
            "datos_modificados": False,
        }


def _fmt_num(valor: Any, decimales: int = 4) -> str:
    if valor is None:
        return "-"
    try:
        return f"{float(valor):.{decimales}f}"
    except (TypeError, ValueError):
        return str(valor)


def formatear_preimportacion_i133(resultado: dict[str, Any]) -> str:
    r = resultado.get("resumen", {})
    lineas = [
        "I1.3.3 — PREIMPORTACIÓN DEFINITIVA DE MENÚS",
        "=" * 78,
        f"Menús: {r.get('menus',0)} | Platos: {r.get('platos',0)} | Componentes: {r.get('componentes',0)} | "
        f"Artículos directos: {r.get('articulos_directos',0)} | Complementos: {r.get('complementos',0)}",
        f"Aprendizajes aplicados: {r.get('aprendizajes_aplicados',0)} | Bloqueos: {r.get('bloqueos',0)} | Estado: {resultado.get('estado_preimportacion')}",
    ]
    for menu in resultado.get("menus", []):
        lineas.append(f"\n{menu.get('nombre')} | Hoja: {menu.get('hoja')}")
        for plato in menu.get("platos", []):
            lineas.append(f"- [{plato.get('seccion')}] {plato.get('nombre_original')} | coste/ración {_fmt_num(plato.get('coste_racion'))} €")
            for c in plato.get("componentes", []):
                icono = "✔" if c.get("catalogado") else "?"
                estado = "catalogado" if c.get("catalogado") else (c.get("estado") or "pendiente")
                lineas.append(f"    {icono} {c.get('grupo')}: {c.get('nombre')} [{estado}]")
        for comp in menu.get("complementos", []):
            lineas.append(f"  [COMPLEMENTO] {comp.get('nombre')}")
        for art in menu.get("articulos_directos", []):
            lineas.append(f"  [ARTÍCULO DIRECTO] {art.get('nombre')} | coste/ración {_fmt_num(art.get('coste_racion'))} €")
        eco = menu.get("economico", {})
        lineas.append(
            "  Económico: venta={} € | neto={} € | coste={} € | food cost={}% | beneficio={} €".format(
                _fmt_num(eco.get("precio_venta"),2), _fmt_num(eco.get("venta_neta"),2),
                _fmt_num(eco.get("coste_total"),4), _fmt_num(eco.get("food_cost_pct"),4),
                _fmt_num(eco.get("beneficio"),4),
            )
        )
    lineas.append("=" * 78)
    if resultado.get("bloqueos"):
        lineas.append("IMPORTACIÓN BLOQUEADA")
        for i, b in enumerate(resultado["bloqueos"], 1):
            lineas.append(f"{i}. {b.get('componente')} | {b.get('rol')} | Plato: {b.get('plato')}")
            lineas.append(f"   Motivo: {b.get('mensaje')}")
            for j, accion in enumerate(b.get("acciones", []), 1):
                lineas.append(f"   {j}. {accion}")
    else:
        lineas.append("PREIMPORTACIÓN LISTA: no existen bloqueos técnicos.")
    lineas.extend([
        "SOLO PREIMPORTACIÓN: I1.3.3 no escribe menús, recetas, artículos ni relaciones.",
        "La importación definitiva seguirá deshabilitada hasta un sprint posterior.",
    ])
    return "\n".join(lineas)
