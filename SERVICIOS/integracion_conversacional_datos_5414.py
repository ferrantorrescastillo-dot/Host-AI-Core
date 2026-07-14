from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.lower().strip().split())


def _read_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return default


def _records(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("items", "registros", "datos", "articulos", "proveedores", "eventos", "escandallos", "recetas", "stock", "lotes"):
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
        # Un diccionario indexado por id/nombre también es válido.
        if all(isinstance(v, dict) for v in data.values()) and data:
            return list(data.values())
    return []


def _first(record: Dict[str, Any], *keys: str) -> Any:
    lowered = {_norm(k): v for k, v in record.items()}
    for key in keys:
        if _norm(key) in lowered:
            return lowered[_norm(key)]
    return None


@dataclass(frozen=True)
class ResultadoBusqueda:
    tipo: str
    nombre: str
    coincidencia: str
    datos: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IntegradorConversacionalDatos5414:
    """Puente de solo lectura entre la conversación y los datos reales de Host AI.

    No duplica motores de negocio ni escribe datos. Localiza entidades existentes,
    comprueba disponibilidad documental y prepara el contexto que los motores ya
    existentes necesitan para ejecutar acciones seguras.
    """

    VERSION = "5.4.14"

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self.db_dir = self.base_dir / "DATOS" / "db"

    def _load(self, filename: str) -> List[Dict[str, Any]]:
        return _records(_read_json(self.db_dir / filename, []))

    def buscar_menu(self, texto: str, limite: int = 8) -> List[Dict[str, Any]]:
        query = _norm(texto)
        fuentes = [
            ("escandallo", self._load("escandallos.json")),
            ("evento_menu", self._load("eventos.json")),
        ]
        encontrados: List[ResultadoBusqueda] = []
        vistos = set()
        for tipo, registros in fuentes:
            for registro in registros:
                nombre = _first(registro, "nombre", "receta", "plato", "menu", "tipo_menu", "titulo")
                if not nombre:
                    continue
                nombre_n = _norm(nombre)
                if query and query not in nombre_n and nombre_n not in query:
                    continue
                key = (tipo, nombre_n)
                if key in vistos:
                    continue
                vistos.add(key)
                coincidencia = "exacta" if nombre_n == query else "parcial"
                encontrados.append(ResultadoBusqueda(tipo, str(nombre), coincidencia, registro))
        encontrados.sort(key=lambda r: (r.coincidencia != "exacta", len(r.nombre)))
        return [r.to_dict() for r in encontrados[:limite]]

    def consultar_stock(self, nombres_articulos: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        filtros = [_norm(x) for x in (nombres_articulos or []) if _norm(x)]
        registros = self._load("stock_lotes.json") or self._load("stock_inicial.json")
        articulos = self._load("articulos.json")
        index_articulos = {}
        for art in articulos:
            codigo = _first(art, "codigo", "id", "articulo_id")
            nombre = _first(art, "articulo", "nombre", "descripcion")
            if codigo is not None and nombre:
                index_articulos[_norm(codigo)] = str(nombre)

        resultado = []
        for reg in registros:
            nombre = _first(reg, "articulo", "nombre", "descripcion", "producto")
            codigo = _first(reg, "codigo", "articulo_id", "id_articulo")
            if not nombre and codigo is not None:
                nombre = index_articulos.get(_norm(codigo), str(codigo))
            if not nombre:
                continue
            nombre_n = _norm(nombre)
            if filtros and not any(f in nombre_n or nombre_n in f for f in filtros):
                continue
            cantidad = _first(reg, "stock", "cantidad", "cantidad_actual", "disponible", "unidades")
            unidad = _first(reg, "unidad", "ud", "formato") or ""
            resultado.append({"nombre": str(nombre), "cantidad": cantidad, "unidad": unidad, "datos": reg})
        return {
            "fuente_disponible": bool(registros),
            "total": len(resultado),
            "articulos": resultado,
            "modo": "solo_lectura",
        }

    def buscar_proveedores(self, articulos: Optional[Iterable[str]] = None) -> List[Dict[str, Any]]:
        filtros = [_norm(x) for x in (articulos or []) if _norm(x)]
        proveedores = self._load("proveedores.json")
        articulos_db = self._load("articulos.json")
        salida: List[Dict[str, Any]] = []
        vistos = set()

        for art in articulos_db:
            nombre_art = _first(art, "articulo", "nombre", "descripcion")
            if filtros and (not nombre_art or not any(f in _norm(nombre_art) or _norm(nombre_art) in f for f in filtros)):
                continue
            proveedor = _first(art, "proveedor", "proveedor_habitual", "nombre_proveedor")
            if proveedor and _norm(proveedor) not in vistos:
                vistos.add(_norm(proveedor))
                salida.append({"proveedor": str(proveedor), "origen": "articulos", "articulo": nombre_art})

        for prov in proveedores:
            nombre = _first(prov, "proveedor", "nombre", "razon_social")
            if nombre and _norm(nombre) not in vistos and not filtros:
                vistos.add(_norm(nombre))
                salida.append({"proveedor": str(nombre), "origen": "proveedores", "datos": prov})
        return salida

    def preparar_contexto(self, evento: Dict[str, Any], accion: str = "todo") -> Dict[str, Any]:
        menu = evento.get("menu") or evento.get("tipo_menu") or ""
        menus = self.buscar_menu(str(menu)) if menu else []
        nombres = []
        for item in menus:
            ingredientes = item.get("datos", {}).get("ingredientes", [])
            if isinstance(ingredientes, list):
                for ing in ingredientes:
                    if isinstance(ing, dict):
                        nombre = _first(ing, "articulo", "nombre", "ingrediente", "producto")
                    else:
                        nombre = ing
                    if nombre:
                        nombres.append(str(nombre))
        stock = self.consultar_stock(nombres if nombres else None)
        proveedores = self.buscar_proveedores(nombres)
        incidencias = []
        if menu and not menus:
            incidencias.append({"nivel": "alto", "codigo": "MENU_NO_LOCALIZADO", "mensaje": f"No se ha localizado un menú/escandallo existente para '{menu}'."})
        if not stock["fuente_disponible"]:
            incidencias.append({"nivel": "alto", "codigo": "STOCK_NO_DISPONIBLE", "mensaje": "No hay una fuente de stock activa legible."})
        if menus and len(menus) > 1:
            incidencias.append({"nivel": "medio", "codigo": "MENU_AMBIGUO", "mensaje": "Hay varias opciones de menú y debe elegirse una antes de calcular."})

        listo = bool(menus) and stock["fuente_disponible"] and len(menus) == 1
        return {
            "ok": True,
            "version": self.VERSION,
            "modo": "solo_lectura",
            "accion_solicitada": accion,
            "evento": dict(evento),
            "menus_encontrados": menus,
            "stock": stock,
            "proveedores": proveedores,
            "incidencias": incidencias,
            "listo_para_motores": listo,
            "requiere_confirmacion_escritura": True,
            "datos_reales_modificados": False,
        }


def integrar_conversacion_datos_5414(evento: Dict[str, Any], accion: str = "todo", base_dir: Optional[Path] = None) -> Dict[str, Any]:
    return IntegradorConversacionalDatos5414(base_dir).preparar_contexto(evento, accion)


def formatear_integracion_5414(resultado: Dict[str, Any]) -> str:
    evento = resultado.get("evento", {})
    menus = resultado.get("menus_encontrados", [])
    stock = resultado.get("stock", {})
    lineas = ["HOST AI 5.4.14 - INTEGRACIÓN CONVERSACIONAL COMPLETA", "", "EVENTO ACTIVO"]
    lineas += [
        f"- Tipo: {evento.get('tipo') or evento.get('tipo_evento') or 'pendiente'}",
        f"- Personas: {evento.get('personas') or evento.get('pax') or 'pendiente'}",
        f"- Menú solicitado: {evento.get('menu') or evento.get('tipo_menu') or 'pendiente'}",
        "",
        "DATOS REALES LOCALIZADOS",
        f"- Menús/escandallos coincidentes: {len(menus)}",
        f"- Registros de stock disponibles: {stock.get('total', 0)}",
        f"- Proveedores relacionados: {len(resultado.get('proveedores', []))}",
    ]
    if menus:
        lineas.append("- Opciones: " + ", ".join(x.get("nombre", "") for x in menus))
    if resultado.get("incidencias"):
        lineas += ["", "PUNTOS PENDIENTES"]
        lineas += [f"- [{x.get('nivel', '').upper()}] {x.get('mensaje')}" for x in resultado["incidencias"]]
    lineas += ["", "SEGURIDAD", "- Consulta en modo solo lectura.", "- Datos reales modificados: NO."]
    return "\n".join(lineas)


__all__ = ["IntegradorConversacionalDatos5414", "integrar_conversacion_datos_5414", "formatear_integracion_5414"]
