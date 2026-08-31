from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List

from SERVICIOS.lector_modelo_canonico_555b72 import LectorModeloCanonico555B72
from SERVICIOS.calculador_rentabilidad_escandallos_555b73 import calcular_resumen_economico_555b73
from SERVICIOS.enriquecedor_precios_articulos_555b731 import EnriquecedorPreciosArticulos555B731
from SERVICIOS.gestor_precio_venta_rentabilidad_555b732 import GestorPrecioVentaRentabilidad555B732


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


def _decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    text = str(value).strip().replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", ".")
    try:
        parsed = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def es_consulta_escandallo_real_555(texto: str) -> bool:
    t = _norm(texto)
    patrones = (
        "en que recetas", "en que platos", "que recetas llevan", "que platos llevan",
        "escandallo de", "receta de", "ingredientes de", "coste de la receta",
        "coste del escandallo", "busca el escandallo", "busca una receta",
        "muestrame el escandallo", "mostrar escandallo",
        "rentabilidad de", "margen de", "food cost de", "beneficio de",
        "precio de venta",
    )
    return any(p in t for p in patrones)


def extraer_termino_escandallo_555(texto: str) -> str:
    t = _norm(texto).replace("?", "").strip()
    patrones = (
        r"en que (?:recetas|platos) (?:utilizo|uso|aparece|esta) (.+)$",
        r"que (?:recetas|platos) llevan (.+)$",
        r"(?:muestrame|mostrar) (?:el )?escandallo de (.+)$",
        r"(?:escandallo|receta|ingredientes) de (.+)$",
        r"coste (?:de la receta|del escandallo) (.+)$",
        r"busca (?:el )?(?:escandallo|una receta) (?:que contenga |de |llamad[oa] )?(.+)$",
    )
    for patron in patrones:
        match = re.search(patron, t)
        if match:
            return match.group(1).strip(" .\"'")
    return ""


class ConectorEscandallosReal555:
    """Consulta recetas/escandallos priorizando el modelo canónico 5.5.5B.

    Es estrictamente de solo lectura. Usa ``escandallos_canonicos.json`` y solo
    recurre al archivo legacy si la base canónica no contiene datos.
    """

    VERSION = "5.5.5B.7.3.2"
    UNIDADES_DERIVACION = frozenset({"u", "unidad", "unidades", "racion", "raciones", "pax"})

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.catalogo = LectorModeloCanonico555B72(self.base_dir).cargar()
        self.escandallos: List[Dict[str, Any]] = self.catalogo.get("escandallos", [])
        self.fuente = self.catalogo.get("fuente", "DATOS/db/escandallos_canonicos.json")
        self.modelo = self.catalogo.get("modelo", "SIN_DATOS")
        self.enriquecedor_precios = EnriquecedorPreciosArticulos555B731(self.base_dir)

    def consultar(self, termino: str, personas: int | None = None) -> Dict[str, Any]:
        termino_n = _norm(termino)
        resultados: List[Dict[str, Any]] = []

        for esc in self.escandallos:
            nombre = str(esc.get("nombre") or esc.get("receta") or "Sin nombre").strip()
            ingredientes_raw = esc.get("ingredientes") if isinstance(esc.get("ingredientes"), list) else []
            coincide_nombre = bool(termino_n and termino_n in _norm(nombre))
            coincide_ingrediente = any(
                termino_n in _norm(
                    ing.get("nombre") or ing.get("ingrediente") or ing.get("articulo") or ing.get("articulo_id")
                )
                for ing in ingredientes_raw
                if isinstance(ing, dict)
            )
            if not (coincide_nombre or coincide_ingrediente):
                continue

            incidencias: List[Dict[str, Any]] = []
            unidad_rendimiento = str(esc.get("unidad_rendimiento") or "u")
            raciones_base_dec = _decimal(esc.get("rendimiento") or esc.get("raciones_base"))
            if raciones_base_dec is None or raciones_base_dec <= 0:
                raciones_base_dec = None
                incidencias.append({
                    "tipo": "RENDIMIENTO_INVALIDO",
                    "detalle": f"Rendimiento no válido en '{nombre}'.",
                })

            objetivo_dec = _decimal(personas) if personas is not None else None
            if personas is not None and (objetivo_dec is None or objetivo_dec <= 0):
                objetivo_dec = None
                incidencias.append({
                    "tipo": "OBJETIVO_INVALIDO",
                    "detalle": "Objetivo de personas inválido para escalado.",
                })

            factor_dec = Decimal("1")
            if objetivo_dec is not None:
                if raciones_base_dec is None:
                    factor_dec = None
                else:
                    factor_dec = objetivo_dec / raciones_base_dec

            ingredientes: List[Dict[str, Any]] = []
            coste_total = Decimal("0")
            for linea in ingredientes_raw:
                if not isinstance(linea, dict):
                    continue
                nombre_linea = str(
                    linea.get("nombre") or linea.get("ingrediente") or linea.get("articulo") or "Ingrediente"
                ).strip()
                cantidad_base_dec = _decimal(linea.get("cantidad"))
                cantidad_dec = (
                    (cantidad_base_dec * factor_dec)
                    if cantidad_base_dec is not None and factor_dec is not None
                    else None
                )
                coste_unitario_dec = _decimal(linea.get("coste_unitario") or linea.get("precio")) or Decimal("0")
                coste_dec = (
                    cantidad_dec * coste_unitario_dec
                    if cantidad_dec is not None and coste_unitario_dec > 0
                    else None
                )
                if coste_dec is not None:
                    coste_total += coste_dec

                unidad_linea = str(linea.get("unidad") or "u")
                unidad_r_norm = _norm(unidad_rendimiento)
                derivable = (
                    cantidad_base_dec is not None
                    and raciones_base_dec is not None
                    and unidad_r_norm in self.UNIDADES_DERIVACION
                    and raciones_base_dec > 0
                )
                cantidad_por_unidad = (cantidad_base_dec / raciones_base_dec) if derivable else None
                ingredientes.append({
                    "nombre": nombre_linea,
                    "articulo_id": linea.get("articulo_id") or linea.get("codigo"),
                    "cantidad_base": float(cantidad_base_dec) if cantidad_base_dec is not None else None,
                    "cantidad": float(cantidad_dec) if cantidad_dec is not None else None,
                    "unidad": unidad_linea,
                    "ambito_cantidad": "LOTE_COMPLETO",
                    "cantidad_por_unidad_rendimiento": float(cantidad_por_unidad) if cantidad_por_unidad is not None else None,
                    "unidad_cantidad_por_rendimiento": (
                        f"{unidad_linea}/{unidad_rendimiento}" if cantidad_por_unidad is not None else None
                    ),
                    "coste_unitario": float(coste_unitario_dec),
                    "coste": float(coste_dec) if coste_dec is not None else None,
                    "proveedor": linea.get("proveedor_preferente") or linea.get("proveedor"),
                })

            enriquecimiento = self.enriquecedor_precios.enriquecer(ingredientes)
            ingredientes = enriquecimiento["lineas"]
            coste_total = enriquecimiento["coste_total"]
            rendimiento_calculo = float(objetivo_dec) if objetivo_dec is not None else (float(raciones_base_dec) if raciones_base_dec is not None else None)
            resumen_economico = calcular_resumen_economico_555b73(
                esc,
                coste_calculado=coste_total,
                rendimiento_calculo=rendimiento_calculo,
                ingredientes=ingredientes,
            )
            resumen_economico["ingredientes_valorados"] = enriquecimiento["valoradas"]
            resumen_economico["ingredientes_totales"] = enriquecimiento["total"]
            resumen_economico["ingredientes_ambiguos"] = enriquecimiento["ambiguas"]
            resumen_economico["nombres_sin_precio"] = enriquecimiento["nombres_sin_precio"]
            resumen_economico["fuente_precios"] = enriquecimiento["fuente"]
            resultados.append({
                "receta_id": esc.get("codigo") or esc.get("receta_id") or esc.get("id"),
                "nombre": nombre,
                "raciones_base": float(raciones_base_dec) if raciones_base_dec is not None else None,
                "unidad_rendimiento": unidad_rendimiento,
                "personas_calculo": personas,
                "factor": float(factor_dec) if factor_dec is not None else None,
                "ingredientes": ingredientes,
                "coste_total": resumen_economico["coste_total"],
                "economia": resumen_economico,
                "coincide_por": "nombre" if coincide_nombre else "ingrediente",
                "estado_escalado": "CALCULABLE" if factor_dec is not None else "NO_CALCULABLE",
                "incidencias": incidencias,
            })

        return {
            "ok": True,
            "encontrado": bool(resultados),
            "termino": termino,
            "personas": personas,
            "coincidencias": resultados,
            "total_escandallos": len(self.escandallos),
            "fuente": self.fuente,
            "modelo": self.modelo,
            "solo_lectura": True,
        }


def formatear_escandallos_real_555(resultado: Dict[str, Any]) -> str:
    termino = resultado.get("termino", "")
    fuente = resultado.get("fuente", "DATOS/db/escandallos_canonicos.json")
    if not resultado.get("encontrado"):
        return (
            f"ESCANDALLOS/RECETAS REALES: {termino}\n"
            f"- No he localizado coincidencias en {fuente}.\n"
            f"- Escandallos cargados actualmente: {resultado.get('total_escandallos', 0)}.\n\n"
            "SIGUIENTE PASO PROFESIONAL\n"
            "- Revisa el nombre o busca por un ingrediente relacionado.\n"
            "- No inventaré ingredientes ni rendimientos.\n\n"
            "SEGURIDAD\n- Consulta en modo solo lectura.\n- Datos reales modificados: NO."
        )

    lines = [
        f"ESCANDALLOS/RECETAS REALES: {termino}",
        f"Coincidencias: {len(resultado.get('coincidencias', []))}",
        "",
    ]
    for esc in resultado.get("coincidencias", []):
        lines.append(str(esc.get("nombre")))
        lines.append(f"- Coincidencia por: {esc.get('coincide_por')}")
        rbase = esc.get("raciones_base")
        if rbase is None:
            lines.append(f"- Rendimiento base: NO DISPONIBLE ({esc.get('unidad_rendimiento', 'u')})")
        else:
            lines.append(f"- Rendimiento base: {float(rbase):g} {esc.get('unidad_rendimiento', 'u')}")
        if esc.get("personas_calculo"):
            lines.append(f"- Cálculo escalado para: {esc.get('personas_calculo')} personas")
        lines.append(f"- Ingredientes: {len(esc.get('ingredientes', []))}")
        for ing in esc.get("ingredientes", [])[:20]:
            cantidad = ing.get("cantidad")
            cantidad_txt = f"{float(cantidad):g}" if isinstance(cantidad, (int, float)) else "NO CALCULABLE"
            lines.append(f"  · {ing.get('nombre')}: {cantidad_txt} {ing.get('unidad')}")
        economia = esc.get("economia") if isinstance(esc.get("economia"), dict) else {}
        lines.append("")
        lines.append("RESUMEN ECONÓMICO")
        lines.append(f"- Coste total de la receta: {float(economia.get('coste_total') or 0):.2f} €")
        if economia.get("coste_unitario") is None:
            lines.append(f"- Coste por {esc.get('unidad_rendimiento', 'u')}: NO DISPONIBLE")
        else:
            lines.append(f"- Coste por {esc.get('unidad_rendimiento', 'u')}: {float(economia.get('coste_unitario') or 0):.2f} €")
        pvp = economia.get("precio_venta_unitario")
        if pvp is None:
            lines.append("- Precio de venta: NO DEFINIDO (opcional)")
            lines.append("- Beneficio bruto: pendiente de precio de venta")
            lines.append("- Food cost y margen: pendientes de precio de venta")
        else:
            lines.append(f"- Precio de venta: {float(pvp):.2f} €")
            lines.append(f"- Beneficio bruto por {esc.get('unidad_rendimiento', 'u')}: {float(economia.get('beneficio_bruto_unitario') or 0):.2f} €")
            lines.append(f"- Beneficio sobre coste: {float(economia.get('beneficio_sobre_coste_pct') or 0):.2f}%")
            lines.append(f"- Margen bruto sobre venta: {float(economia.get('margen_bruto_pct') or 0):.2f}%")
            lines.append(f"- Food cost: {float(economia.get('food_cost_pct') or 0):.2f}%")
        iva = economia.get("iva_pct")
        lines.append(f"- IVA: {float(iva):.2f}%" if iva is not None else "- IVA: NO DEFINIDO")
        valorados = int(economia.get("ingredientes_valorados") or 0)
        totales = int(economia.get("ingredientes_totales") or len(esc.get("ingredientes", [])))
        lines.append(f"- Ingredientes valorados: {valorados}/{totales}")
        if economia.get("fuente_precios"):
            lines.append(f"- Fuente de precios: {economia.get('fuente_precios')}")
        if int(economia.get("ingredientes_sin_precio") or 0):
            lines.append(f"- Aviso: {int(economia.get('ingredientes_sin_precio') or 0)} ingredientes sin precio; el coste puede ser parcial.")
            for nombre_sin_precio in (economia.get("nombres_sin_precio") or [])[:10]:
                lines.append(f"  · Sin precio: {nombre_sin_precio}")
        if int(economia.get("ingredientes_ambiguos") or 0):
            lines.append(f"- Aviso: {int(economia.get('ingredientes_ambiguos') or 0)} enlaces ambiguos requieren revisión.")
        lines.append(f"- Estado económico: {economia.get('estado', 'SIN_CALCULAR')}")
        for inc in esc.get("incidencias", [])[:5]:
            lines.append(f"- Incidencia de escalado: {inc.get('tipo')} ({inc.get('detalle')})")
        lines.append("")
    lines.extend([
        "FUENTE DE DATOS",
        f"- {fuente}",
        "",
        "SEGURIDAD",
        "- Consulta en modo solo lectura.",
        "- Datos reales modificados: NO.",
    ])
    return "\n".join(lines)


def procesar_consulta_escandallos_real_555(texto: str, base_dir: Path) -> Dict[str, Any]:
    gestion_precio = GestorPrecioVentaRentabilidad555B732(base_dir).procesar(texto)
    if gestion_precio.get("gestionado"):
        return {
            "gestionado": True,
            "ok": bool(gestion_precio.get("ok", True)),
            "version": GestorPrecioVentaRentabilidad555B732.VERSION,
            "intencion": "gestionar_precio_venta_rentabilidad",
            "estado": gestion_precio.get("estado"),
            "mensaje": gestion_precio.get("mensaje", ""),
            "datos": gestion_precio,
            "pasos": [],
        }
    if not es_consulta_escandallo_real_555(texto):
        return {"gestionado": False}
    termino = extraer_termino_escandallo_555(texto)
    match_pax = re.search(r"(?:para|de)\s+(\d{1,5})\s+personas", _norm(texto))
    personas = int(match_pax.group(1)) if match_pax else None
    termino = re.sub(r"\s+(?:para|de)\s+\d{1,5}\s+personas$", "", termino).strip()
    datos = ConectorEscandallosReal555(base_dir).consultar(termino, personas)
    return {
        "gestionado": True,
        "ok": True,
        "version": ConectorEscandallosReal555.VERSION,
        "intencion": "consultar_escandallos_reales",
        "estado": "escandallos_reales_consultados",
        "mensaje": formatear_escandallos_real_555(datos),
        "datos": datos,
        "pasos": [],
    }


__all__ = [
    "ConectorEscandallosReal555", "es_consulta_escandallo_real_555",
    "extraer_termino_escandallo_555", "formatear_escandallos_real_555",
    "procesar_consulta_escandallos_real_555",
]
