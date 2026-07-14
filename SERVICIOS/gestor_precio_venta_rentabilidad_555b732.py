from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from SERVICIOS.lector_modelo_canonico_555b72 import LectorModeloCanonico555B72
from SERVICIOS.enriquecedor_precios_articulos_555b731 import EnriquecedorPreciosArticulos555B731
from SERVICIOS.calculador_rentabilidad_escandallos_555b73 import calcular_resumen_economico_555b73


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _numero(texto: str) -> Optional[float]:
    match = re.search(r"(\d+(?:[.,]\d+)?)", texto or "")
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def _leer_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _escribir_atomico(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.stem}_", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _lista_registros(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("escandallos", "recetas", "items", "registros"):
            if isinstance(payload.get(key), list):
                return [x for x in payload[key] if isinstance(x, dict)]
    return []


def _receta_de_registro(registro: Dict[str, Any]) -> Dict[str, Any]:
    receta = registro.get("receta")
    return receta if isinstance(receta, dict) else registro


def _nombre_registro(registro: Dict[str, Any]) -> str:
    receta = _receta_de_registro(registro)
    return str(receta.get("nombre") or registro.get("nombre") or receta.get("receta") or "").strip()


class GestorPrecioVentaRentabilidad555B732:
    """Gestiona PVP opcional y rentabilidad con confirmación segura.

    El primer mensaje crea una propuesta pendiente. Solo un segundo mensaje
    explícito de confirmación escribe el PVP en la base canónica. La escritura
    es atómica y genera una copia de seguridad previa.
    """

    VERSION = "5.5.5B.7.3.2"

    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.ruta_canonica = self.base_dir / "DATOS" / "db" / "escandallos_canonicos.json"
        self.ruta_pendiente = self.base_dir / "DATOS" / "pendientes" / "precio_venta_555b732.json"
        self.dir_backups = self.base_dir / "DATOS" / "db" / "backups"

    @staticmethod
    def es_comando_precio(texto: str) -> bool:
        t = _norm(texto)
        return (
            "precio de venta" in t
            and any(x in t for x in ("pon", "poner", "define", "definir", "establece", "guardar", "asigna"))
        )

    @staticmethod
    def es_confirmacion_precio(texto: str) -> bool:
        t = _norm(texto)
        return (
            "precio de venta" in t
            and any(x in t for x in ("confirma", "confirmar", "aplica", "guardar", "si confirma"))
        ) or t in {"confirmar precio", "confirma precio", "aplicar precio"}

    @staticmethod
    def es_cancelacion_precio(texto: str) -> bool:
        t = _norm(texto)
        return "precio de venta" in t and any(x in t for x in ("cancela", "cancelar", "no aplicar"))

    @staticmethod
    def es_consulta_rentabilidad(texto: str) -> bool:
        t = _norm(texto)
        return any(x in t for x in ("rentabilidad de", "margen de", "food cost de", "beneficio de"))

    def _buscar_registro(self, termino: str, payload: Any) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        q = _norm(termino)
        candidatos: List[Tuple[int, Dict[str, Any]]] = []
        for registro in _lista_registros(payload):
            nombre = _nombre_registro(registro)
            n = _norm(nombre)
            if not q or not n:
                continue
            if q == n:
                candidatos.append((100, registro))
            elif q in n or n in q:
                candidatos.append((90, registro))
        candidatos.sort(key=lambda x: (-x[0], _nombre_registro(x[1]).lower()))
        nombres = [_nombre_registro(x[1]) for x in candidatos]
        if not candidatos:
            return None, []
        if len(candidatos) > 1 and candidatos[0][0] == candidatos[1][0]:
            return None, nombres
        return candidatos[0][1], nombres

    @staticmethod
    def _extraer_propuesta(texto: str) -> Dict[str, Any]:
        normal = _norm(texto)
        precio = None
        patron_precio = re.search(r"precio de venta(?: de)?\s+(\d+(?:[.,]\d+)?)", texto, re.I)
        if patron_precio:
            precio = float(patron_precio.group(1).replace(",", "."))
        if precio is None:
            precio = _numero(texto)

        iva = None
        patron_iva = re.search(r"iva(?: del| de)?\s*(\d+(?:[.,]\d+)?)\s*%?", texto, re.I)
        if patron_iva:
            iva = float(patron_iva.group(1).replace(",", "."))

        termino = ""
        patrones = (
            r"(?:para|a la receta|al escandallo de)\s+(.+?)(?:\s+con iva|\s*$)",
            r"precio de venta(?: de)?\s+\d+(?:[.,]\d+)?\s*(?:€|euros?)?(?:\s+por\s+\w+)?\s+(?:para|a)\s+(.+?)(?:\s+con iva|\s*$)",
        )
        for patron in patrones:
            m = re.search(patron, texto, re.I)
            if m:
                termino = m.group(1).strip(" .")
                break
        if not termino:
            # Limpieza conservadora de la frase completa.
            termino = re.sub(r".*?precio de venta(?: de)?\s+\d+(?:[.,]\d+)?\s*(?:€|euros?)?", "", texto, flags=re.I)
            termino = re.sub(r"\b(?:por unidad|por racion|por pax|para|a)\b", " ", termino, flags=re.I)
            termino = re.sub(r"\bcon iva.*$", "", termino, flags=re.I).strip(" .")
        return {"precio": precio, "iva": iva, "termino": termino, "normal": normal}

    @staticmethod
    def _extraer_termino_rentabilidad(texto: str) -> str:
        t = str(texto or "").strip().rstrip("?.")
        for patron in (
            r"rentabilidad de (.+)$",
            r"margen de (.+)$",
            r"food cost de (.+)$",
            r"beneficio de (.+)$",
        ):
            m = re.search(patron, t, re.I)
            if m:
                return m.group(1).strip(" .")
        return ""

    def _economia(self, registro: Dict[str, Any]) -> Dict[str, Any]:
        receta = _receta_de_registro(registro)
        ingredientes_raw = receta.get("ingredientes") if isinstance(receta.get("ingredientes"), list) else []
        lineas = []
        for ing in ingredientes_raw:
            if not isinstance(ing, dict):
                continue
            lineas.append({
                "nombre": ing.get("nombre") or ing.get("ingrediente") or ing.get("articulo"),
                "articulo_id": ing.get("articulo_id") or ing.get("codigo"),
                "cantidad": ing.get("cantidad") or 0,
                "unidad": ing.get("unidad") or "u",
                "coste_unitario": ing.get("coste_unitario") or ing.get("precio") or 0,
                "proveedor": ing.get("proveedor"),
            })
        enriquecimiento = EnriquecedorPreciosArticulos555B731(self.base_dir).enriquecer(lineas)
        rendimiento = receta.get("rendimiento") or registro.get("rendimiento") or 1
        try:
            rendimiento_num = max(float(rendimiento), 1e-9)
        except (TypeError, ValueError):
            rendimiento_num = 1.0
        resumen = calcular_resumen_economico_555b73(
            registro,
            coste_calculado=float(enriquecimiento.get("coste_total") or 0),
            rendimiento_calculo=rendimiento_num,
            ingredientes=enriquecimiento.get("lineas") or [],
        )
        resumen.update({
            "ingredientes_valorados": enriquecimiento.get("valoradas", 0),
            "ingredientes_totales": enriquecimiento.get("total", 0),
            "fuente_precios": enriquecimiento.get("fuente"),
        })
        return resumen

    def proponer(self, texto: str) -> Dict[str, Any]:
        datos = self._extraer_propuesta(texto)
        precio = datos.get("precio")
        termino = str(datos.get("termino") or "").strip()
        if precio is None or precio <= 0:
            return {"ok": False, "estado": "PRECIO_INVALIDO", "mensaje": "Necesito un precio de venta mayor que 0."}
        if not termino:
            return {"ok": False, "estado": "RECETA_NO_INDICADA", "mensaje": "Indica para qué receta o escandallo quieres definir el precio."}

        payload = _leer_json(self.ruta_canonica)
        registro, candidatos = self._buscar_registro(termino, payload)
        if registro is None:
            if candidatos:
                return {
                    "ok": False,
                    "estado": "RECETA_AMBIGUA",
                    "mensaje": "He encontrado varias recetas posibles: " + ", ".join(candidatos[:10]),
                }
            return {"ok": False, "estado": "RECETA_NO_ENCONTRADA", "mensaje": f"No he encontrado una receta llamada '{termino}'."}

        nombre = _nombre_registro(registro)
        propuesta = {
            "version": self.VERSION,
            "creado_en": datetime.now(timezone.utc).isoformat(),
            "receta_id": _receta_de_registro(registro).get("codigo") or registro.get("id") or registro.get("receta_id"),
            "nombre": nombre,
            "precio_venta_unitario": round(float(precio), 6),
            "iva_pct": round(float(datos["iva"]), 4) if datos.get("iva") is not None else None,
            "ruta_destino": str(self.ruta_canonica.relative_to(self.base_dir)),
        }
        self.ruta_pendiente.parent.mkdir(parents=True, exist_ok=True)
        _escribir_atomico(self.ruta_pendiente, propuesta)

        previo = dict(registro)
        previo["precio_venta_unitario"] = propuesta["precio_venta_unitario"]
        if propuesta["iva_pct"] is not None:
            previo["iva_pct"] = propuesta["iva_pct"]
        economia = self._economia(previo)
        return {
            "ok": True,
            "estado": "PENDIENTE_CONFIRMACION",
            "propuesta": propuesta,
            "economia": economia,
            "mensaje": self._formatear_propuesta(propuesta, economia),
        }

    def confirmar(self) -> Dict[str, Any]:
        pendiente = _leer_json(self.ruta_pendiente)
        if not isinstance(pendiente, dict):
            return {"ok": False, "estado": "SIN_PROPUESTA", "mensaje": "No hay ningún precio de venta pendiente de confirmación."}
        payload = _leer_json(self.ruta_canonica)
        if payload is None:
            return {"ok": False, "estado": "BASE_NO_DISPONIBLE", "mensaje": "No se puede abrir la base canónica de escandallos."}

        objetivo = str(pendiente.get("receta_id") or "")
        nombre_objetivo = _norm(pendiente.get("nombre"))
        registro_objetivo = None
        for registro in _lista_registros(payload):
            receta = _receta_de_registro(registro)
            rid = str(receta.get("codigo") or registro.get("id") or registro.get("receta_id") or "")
            if (objetivo and rid == objetivo) or _norm(_nombre_registro(registro)) == nombre_objetivo:
                registro_objetivo = registro
                break
        if registro_objetivo is None:
            return {"ok": False, "estado": "RECETA_NO_ENCONTRADA", "mensaje": "La receta pendiente ya no existe en la base canónica."}

        anterior = registro_objetivo.get("precio_venta_unitario")
        registro_objetivo["precio_venta_unitario"] = float(pendiente["precio_venta_unitario"])
        if pendiente.get("iva_pct") is not None:
            registro_objetivo["iva_pct"] = float(pendiente["iva_pct"])
        registro_objetivo["precio_venta_actualizado_en"] = datetime.now(timezone.utc).isoformat()
        registro_objetivo["precio_venta_origen"] = "HOST_AI_5.5.5B.7.3.2"

        self.dir_backups.mkdir(parents=True, exist_ok=True)
        marca = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = self.dir_backups / f"escandallos_canonicos_precio_{marca}.json.bak"
        shutil.copy2(self.ruta_canonica, backup)
        _escribir_atomico(self.ruta_canonica, payload)
        try:
            self.ruta_pendiente.unlink()
        except OSError:
            pass

        economia = self._economia(registro_objetivo)
        return {
            "ok": True,
            "estado": "PRECIO_APLICADO",
            "nombre": _nombre_registro(registro_objetivo),
            "precio_anterior": anterior,
            "precio_nuevo": registro_objetivo["precio_venta_unitario"],
            "backup": str(backup.relative_to(self.base_dir)),
            "economia": economia,
            "mensaje": self._formatear_confirmacion(registro_objetivo, anterior, backup, economia),
        }

    def cancelar(self) -> Dict[str, Any]:
        if self.ruta_pendiente.exists():
            self.ruta_pendiente.unlink()
            return {"ok": True, "estado": "PROPUESTA_CANCELADA", "mensaje": "Propuesta de precio de venta cancelada. No se han modificado datos reales."}
        return {"ok": True, "estado": "SIN_PROPUESTA", "mensaje": "No había ningún precio de venta pendiente."}

    def consultar_rentabilidad(self, texto: str) -> Dict[str, Any]:
        termino = self._extraer_termino_rentabilidad(texto)
        payload = _leer_json(self.ruta_canonica)
        registro, candidatos = self._buscar_registro(termino, payload)
        if registro is None:
            mensaje = "No he encontrado la receta indicada."
            if candidatos:
                mensaje = "He encontrado varias recetas posibles: " + ", ".join(candidatos[:10])
            return {"ok": False, "estado": "RECETA_NO_ENCONTRADA", "mensaje": mensaje}
        economia = self._economia(registro)
        return {
            "ok": True,
            "estado": "RENTABILIDAD_CONSULTADA",
            "nombre": _nombre_registro(registro),
            "economia": economia,
            "mensaje": self._formatear_rentabilidad(_nombre_registro(registro), economia),
        }

    @staticmethod
    def _formatear_propuesta(propuesta: Dict[str, Any], economia: Dict[str, Any]) -> str:
        lines = [
            "PROPUESTA DE PRECIO DE VENTA",
            f"- Receta: {propuesta['nombre']}",
            f"- Precio propuesto: {float(propuesta['precio_venta_unitario']):.2f} € por unidad de rendimiento",
        ]
        if propuesta.get("iva_pct") is not None:
            lines.append(f"- IVA propuesto: {float(propuesta['iva_pct']):.2f}%")
        lines.extend([
            f"- Coste unitario actual: {float(economia.get('coste_unitario') or 0):.2f} €",
            f"- Beneficio bruto unitario: {float(economia.get('beneficio_bruto_unitario') or 0):.2f} €",
            f"- Food cost: {float(economia.get('food_cost_pct') or 0):.2f}%",
            f"- Margen bruto sobre venta: {float(economia.get('margen_bruto_pct') or 0):.2f}%",
            "",
            "CONFIRMACIÓN NECESARIA",
            "- No se ha modificado ningún dato real.",
            "- Para aplicarlo escribe: confirma el precio de venta.",
            "- Para descartarlo escribe: cancela el precio de venta.",
        ])
        return "\n".join(lines)

    @staticmethod
    def _formatear_confirmacion(registro: Dict[str, Any], anterior: Any, backup: Path, economia: Dict[str, Any]) -> str:
        lines = [
            "PRECIO DE VENTA APLICADO",
            f"- Receta: {_nombre_registro(registro)}",
            f"- Precio anterior: {float(anterior):.2f} €" if anterior not in (None, "") else "- Precio anterior: NO DEFINIDO",
            f"- Precio nuevo: {float(registro.get('precio_venta_unitario') or 0):.2f} €",
            f"- Coste unitario: {float(economia.get('coste_unitario') or 0):.2f} €",
            f"- Beneficio bruto unitario: {float(economia.get('beneficio_bruto_unitario') or 0):.2f} €",
            f"- Food cost: {float(economia.get('food_cost_pct') or 0):.2f}%",
            f"- Margen bruto: {float(economia.get('margen_bruto_pct') or 0):.2f}%",
            "",
            "SEGURIDAD",
            f"- Copia de seguridad: {backup}",
            "- Datos reales modificados: SÍ, con confirmación explícita.",
        ]
        return "\n".join(lines)

    @staticmethod
    def _formatear_rentabilidad(nombre: str, economia: Dict[str, Any]) -> str:
        lines = [
            f"RENTABILIDAD: {nombre}",
            f"- Coste total de la receta: {float(economia.get('coste_total') or 0):.2f} €",
            f"- Coste unitario: {float(economia.get('coste_unitario') or 0):.2f} €",
        ]
        pvp = economia.get("precio_venta_unitario")
        if pvp is None:
            lines.extend([
                "- Precio de venta: NO DEFINIDO",
                "- Beneficio, food cost y margen: pendientes de precio de venta.",
            ])
        else:
            lines.extend([
                f"- Precio de venta: {float(pvp):.2f} €",
                f"- Beneficio bruto unitario: {float(economia.get('beneficio_bruto_unitario') or 0):.2f} €",
                f"- Beneficio sobre coste: {float(economia.get('beneficio_sobre_coste_pct') or 0):.2f}%",
                f"- Food cost: {float(economia.get('food_cost_pct') or 0):.2f}%",
                f"- Margen bruto sobre venta: {float(economia.get('margen_bruto_pct') or 0):.2f}%",
            ])
        iva = economia.get("iva_pct")
        lines.append(f"- IVA: {float(iva):.2f}%" if iva is not None else "- IVA: NO DEFINIDO")
        lines.extend([
            f"- Estado económico: {economia.get('estado', 'SIN_CALCULAR')}",
            "",
            "FUENTE",
            "- Costes: DATOS/db/articulos.json",
            "- Precio de venta: DATOS/db/escandallos_canonicos.json",
        ])
        return "\n".join(lines)

    def procesar(self, texto: str) -> Dict[str, Any]:
        if self.es_cancelacion_precio(texto):
            return {"gestionado": True, **self.cancelar()}
        if self.es_confirmacion_precio(texto):
            return {"gestionado": True, **self.confirmar()}
        if self.es_comando_precio(texto):
            return {"gestionado": True, **self.proponer(texto)}
        if self.es_consulta_rentabilidad(texto):
            return {"gestionado": True, **self.consultar_rentabilidad(texto)}
        return {"gestionado": False}


__all__ = ["GestorPrecioVentaRentabilidad555B732"]
