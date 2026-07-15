from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import json
import uuid

from SERVICIOS.editor_articulos_417 import EditorArticulos417


def _rid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class RecepcionOperativaRP3:
    """Recepcion operativa guiada por pedido esperado (RP-3).

    Reutiliza componentes existentes:
    - `core.compras` para pedido esperado y estados.
    - `core.stock` para entradas, lotes y movimientos.
    - `EditorArticulos417` para actualizar precio de articulo.

    Principios:
    - sin sistemas paralelos de stock/movimientos/lotes;
    - recepcion con vista previa y diferencias trazables;
    - commit atomico con rollback sobre stock+pedido+registro.
    """

    VERSION = "RP-3"

    def __init__(self, core: Any):
        self.core = core
        base_dir = Path(getattr(core, "base_dir", Path.cwd()))
        self.base_dir = base_dir
        self.dir_recepciones = base_dir / "DATOS" / "piloto" / "recepciones_rp3"
        self.dir_recepciones.mkdir(parents=True, exist_ok=True)
        self.path_sesiones = self.dir_recepciones / "sesiones.json"
        self.path_registros = self.dir_recepciones / "registros.json"
        self.editor_articulos = EditorArticulos417(str(base_dir / "DATOS" / "db" / "articulos.json"))

    # ------------------------------------------------------------------
    # Sesiones
    # ------------------------------------------------------------------
    def iniciar_recepcion(self, pedido_id: str, proveedor_llegada: str = "") -> dict[str, Any]:
        pedido = self.core.compras.obtener_pedido(pedido_id)
        if not pedido:
            raise ValueError(f"Pedido no encontrado: {pedido_id}")
        if pedido.estado in {"recibido", "cancelado"}:
            raise ValueError(f"El pedido no se puede recepcionar en estado {pedido.estado}.")

        esperado = []
        for linea in pedido.lineas:
            esperado.append({
                "linea_id": linea.id,
                "articulo_id": linea.articulo_id,
                "nombre": linea.nombre,
                "cantidad_esperada": float(linea.cantidad),
                "cantidad_recibida": 0.0,
                "unidad_esperada": linea.unidad,
                "unidad_recibida": linea.unidad,
                "precio_esperado": float(linea.precio_unitario or 0),
                "precio_recibido": float(linea.precio_unitario or 0),
                "caducidad": "",
                "lote": "",
                "estado_linea": "pendiente",  # pendiente|aceptada|parcial|no_recibida|rechazada|sustitucion
                "motivo": "",
                "incidencias": [],
            })

        sesion = {
            "id": _rid("RECRP3"),
            "version": self.VERSION,
            "creado_en": datetime.now().isoformat(timespec="seconds"),
            "estado": "borrador",
            "pedido_id": pedido.id,
            "proveedor_esperado": pedido.proveedor,
            "proveedor_llegada": proveedor_llegada.strip() or pedido.proveedor,
            "lineas_esperadas": esperado,
            "lineas_adicionales": [],
            "incidencias": [],
            "resumen": {
                "esperadas": len(esperado),
                "aceptadas": 0,
                "parciales": 0,
                "rechazadas": 0,
                "no_recibidas": 0,
                "adicionales": 0,
                "incidencias": 0,
            },
            "solo_vista_previa": True,
        }
        sesiones = self._leer_lista(self.path_sesiones)
        sesiones.append(sesion)
        self._escribir_lista(self.path_sesiones, sesiones)
        return self._enriquecer_resumen(sesion)

    def obtener_sesion(self, sesion_id: str) -> dict[str, Any]:
        sesiones = self._leer_lista(self.path_sesiones)
        sesion = next((s for s in sesiones if str(s.get("id")) == str(sesion_id)), None)
        if not sesion:
            raise ValueError("Sesion de recepcion no encontrada.")
        return self._enriquecer_resumen(sesion)

    def listar_sesiones_abiertas(self) -> list[dict[str, Any]]:
        sesiones = self._leer_lista(self.path_sesiones)
        abiertas = [s for s in sesiones if str(s.get("estado")) in {"borrador", "preparada"}]
        abiertas.sort(key=lambda x: str(x.get("creado_en") or ""), reverse=True)
        return [self._enriquecer_resumen(s) for s in abiertas]

    def actualizar_linea_esperada(
        self,
        sesion_id: str,
        linea_id: str,
        *,
        cantidad_recibida: float,
        unidad_recibida: str,
        precio_recibido: float | None = None,
        lote: str = "",
        caducidad: str = "",
        estado_linea: str = "aceptada",
        motivo: str = "",
        articulo_id_recibido: str = "",
        nombre_recibido: str = "",
    ) -> dict[str, Any]:
        sesion, sesiones = self._mut_sesion(sesion_id)
        linea = next((x for x in sesion["lineas_esperadas"] if str(x.get("linea_id")) == str(linea_id)), None)
        if not linea:
            raise ValueError("Linea esperada no encontrada en la sesion.")

        estado = (estado_linea or "aceptada").strip().lower()
        if estado not in {"aceptada", "parcial", "no_recibida", "rechazada", "sustitucion"}:
            raise ValueError("Estado de linea no soportado.")

        cantidad = _to_float(cantidad_recibida)
        if cantidad < 0:
            raise ValueError("No se aceptan cantidades negativas.")

        unidad = (unidad_recibida or "").strip() or str(linea.get("unidad_esperada") or "")
        if not unidad:
            raise ValueError("La unidad recibida es obligatoria.")

        esperada = _to_float(linea.get("cantidad_esperada"), 0.0)
        if estado in {"aceptada", "parcial", "sustitucion"} and cantidad <= 0:
            raise ValueError("La linea aceptada/parcial/sustitucion requiere cantidad recibida mayor que cero.")

        precio = linea.get("precio_esperado") if precio_recibido is None else _to_float(precio_recibido)
        if _to_float(precio, 0.0) < 0:
            raise ValueError("No se aceptan precios negativos.")

        linea["cantidad_recibida"] = cantidad
        linea["unidad_recibida"] = unidad
        linea["precio_recibido"] = _to_float(precio, 0.0)
        linea["lote"] = (lote or "").strip()
        linea["caducidad"] = (caducidad or "").strip()
        linea["estado_linea"] = estado
        linea["motivo"] = (motivo or "").strip()

        if estado == "sustitucion":
            if not (articulo_id_recibido or nombre_recibido):
                raise ValueError("La sustitucion requiere articulo o nombre recibido.")
            linea["articulo_id_recibido"] = (articulo_id_recibido or "").strip()
            linea["nombre_recibido"] = (nombre_recibido or linea.get("nombre") or "").strip()

        incidencias = []
        if estado == "parcial" and cantidad < esperada:
            incidencias.append(self._inc("cantidad_incorrecta", f"Parcial: esperado {esperada:g}, recibido {cantidad:g}"))
        if estado == "no_recibida":
            incidencias.append(self._inc("no_recibido", "Producto esperado no recibido."))
        if estado == "rechazada":
            incidencias.append(self._inc("producto_rechazado", "Producto rechazado en recepcion."))
        if estado == "sustitucion":
            incidencias.append(self._inc("sustitucion", "Producto recibido como sustitucion del esperado."))
        if unidad.lower() != str(linea.get("unidad_esperada") or "").lower():
            incidencias.append(self._inc("unidad_diferente", f"Unidad esperada {linea.get('unidad_esperada')} vs recibida {unidad}."))
        if _to_float(linea.get("precio_esperado"), 0.0) != _to_float(linea.get("precio_recibido"), 0.0):
            incidencias.append(self._inc("precio_incorrecto", f"Precio esperado {linea.get('precio_esperado')} vs recibido {linea.get('precio_recibido')}"))
        if linea.get("caducidad"):
            incidencias.append(self._inc("caducidad", f"Caducidad informada: {linea.get('caducidad')}"))
        if linea.get("lote"):
            incidencias.append(self._inc("lote", f"Lote recibido: {linea.get('lote')}"))

        linea["incidencias"] = incidencias
        self._recalcular_sesion(sesion)
        self._guardar_sesiones(sesiones)
        return self._enriquecer_resumen(sesion)

    def registrar_adicional(
        self,
        sesion_id: str,
        *,
        nombre: str,
        cantidad: float,
        unidad: str,
        precio_unitario: float = 0.0,
        articulo_id: str = "",
        lote: str = "",
        caducidad: str = "",
        motivo: str = "",
    ) -> dict[str, Any]:
        sesion, sesiones = self._mut_sesion(sesion_id)
        nombre = (nombre or "").strip()
        if not nombre:
            raise ValueError("El producto adicional requiere nombre.")
        cantidad = _to_float(cantidad)
        if cantidad <= 0:
            raise ValueError("El producto adicional requiere cantidad mayor que cero.")
        unidad = (unidad or "").strip()
        if not unidad:
            raise ValueError("El producto adicional requiere unidad.")
        precio = _to_float(precio_unitario)
        if precio < 0:
            raise ValueError("No se aceptan precios negativos.")

        sesion["lineas_adicionales"].append({
            "id": _rid("ADIC"),
            "nombre": nombre,
            "articulo_id": (articulo_id or "").strip(),
            "cantidad": cantidad,
            "unidad": unidad,
            "precio_unitario": precio,
            "lote": (lote or "").strip(),
            "caducidad": (caducidad or "").strip(),
            "motivo": (motivo or "Producto adicional").strip(),
            "incidencias": [self._inc("producto_adicional", "Producto no esperado recibido en proveedor.")],
        })
        self._recalcular_sesion(sesion)
        self._guardar_sesiones(sesiones)
        return self._enriquecer_resumen(sesion)

    def preparar_validacion(self, sesion_id: str) -> dict[str, Any]:
        sesion = self.obtener_sesion(sesion_id)
        pedido = self.core.compras.obtener_pedido(sesion["pedido_id"])
        if not pedido:
            raise ValueError("Pedido original no encontrado.")

        diferencias = []
        for linea in sesion["lineas_esperadas"]:
            diferencias.extend(linea.get("incidencias") or [])
        for linea in sesion["lineas_adicionales"]:
            diferencias.extend(linea.get("incidencias") or [])

        return {
            "ok": True,
            "sesion_id": sesion_id,
            "pedido_id": pedido.id,
            "proveedor_esperado": sesion.get("proveedor_esperado"),
            "proveedor_llegada": sesion.get("proveedor_llegada"),
            "lineas_esperadas": sesion.get("lineas_esperadas", []),
            "lineas_adicionales": sesion.get("lineas_adicionales", []),
            "diferencias": diferencias,
            "resumen": sesion.get("resumen", {}),
            "stock_antes": self.core.stock.stock_actual(),
            "solo_vista_previa": True,
        }

    # ------------------------------------------------------------------
    # Commit/rollback
    # ------------------------------------------------------------------
    def finalizar_recepcion(self, sesion_id: str, confirmacion: str = "") -> dict[str, Any]:
        if (confirmacion or "").strip().upper() != "RECEPCIONAR":
            raise ValueError("Confirmacion incorrecta. Debes escribir RECEPCIONAR.")

        sesion, sesiones = self._mut_sesion(sesion_id)
        pedido = self.core.compras.obtener_pedido(sesion["pedido_id"])
        if not pedido:
            raise ValueError("Pedido no encontrado para finalizar recepcion.")
        if pedido.estado in {"recibido", "cancelado"}:
            raise ValueError("El pedido no admite recepcion en su estado actual.")

        # Validaciones finales
        for linea in sesion["lineas_esperadas"]:
            estado = str(linea.get("estado_linea") or "pendiente")
            if estado == "pendiente":
                raise ValueError("Todas las lineas esperadas deben registrarse antes de finalizar.")
            if _to_float(linea.get("cantidad_recibida"), 0.0) < 0:
                raise ValueError("No se aceptan cantidades negativas.")
            if _to_float(linea.get("precio_recibido"), 0.0) < 0:
                raise ValueError("No se aceptan precios negativos.")

        lotes_antes = deepcopy(self.core.stock.lotes)
        movimientos_antes = deepcopy(self.core.stock.movimientos)
        pedido_antes = deepcopy(pedido.to_dict())

        try:
            entradas_stock = []
            incidencias = []

            # Aplicar lineas esperadas
            for linea in sesion["lineas_esperadas"]:
                estado = str(linea.get("estado_linea") or "pendiente")
                incidencias.extend(linea.get("incidencias") or [])
                if estado in {"aceptada", "parcial", "sustitucion"}:
                    cantidad = _to_float(linea.get("cantidad_recibida"), 0.0)
                    if cantidad <= 0:
                        continue
                    articulo_id = str(linea.get("articulo_id_recibido") or linea.get("articulo_id") or "")
                    nombre = str(linea.get("nombre_recibido") or linea.get("nombre") or "")
                    unidad = str(linea.get("unidad_recibida") or linea.get("unidad_esperada") or "")

                    # Bloqueo de unidad incompatible para linea esperada (solo en sustitucion permitimos diferente articulo).
                    if estado != "sustitucion" and unidad.lower() != str(linea.get("unidad_esperada") or "").lower():
                        raise ValueError(f"Unidad incompatible para {nombre}: esperada {linea.get('unidad_esperada')} y recibida {unidad}.")

                    precio = _to_float(linea.get("precio_recibido"), _to_float(linea.get("precio_esperado"), 0.0))
                    traza = {
                        "rp": self.VERSION,
                        "sesion_id": sesion_id,
                        "pedido_id": pedido.id,
                        "linea_id": linea.get("linea_id"),
                        "proveedor_esperado": sesion.get("proveedor_esperado"),
                        "proveedor_llegada": sesion.get("proveedor_llegada"),
                        "estado_linea": estado,
                        "lote_externo": linea.get("lote") or "",
                        "caducidad": linea.get("caducidad") or "",
                        "incidencias": list(linea.get("incidencias") or []),
                    }
                    res = self.core.stock.registrar_entrada(
                        nombre=nombre,
                        cantidad=cantidad,
                        unidad=unidad,
                        ubicacion="recepcion",
                        proveedor=sesion.get("proveedor_llegada") or sesion.get("proveedor_esperado") or "",
                        articulo_id=articulo_id,
                        caducidad=str(linea.get("caducidad") or ""),
                        coste_unitario=precio,
                        motivo=f"recepcion rp3 {pedido.id}",
                        trazabilidad=traza,
                    )
                    lote = dict(res.get("lote") or {})
                    movimiento = dict(res.get("movimiento") or {})
                    entradas_stock.append({
                        "nombre": lote.get("nombre") or nombre,
                        "articulo_id": lote.get("articulo_id") or articulo_id,
                        "cantidad": _to_float(lote.get("cantidad"), cantidad),
                        "unidad": lote.get("unidad") or unidad,
                        "caducidad": lote.get("caducidad") or "",
                        "lote_id": lote.get("id") or "",
                        "movimiento_id": movimiento.get("id") or "",
                        "coste_unitario": _to_float(lote.get("coste_unitario"), precio),
                    })

                    # Actualizar precio de la linea del pedido y articulo catalogo.
                    pedido_linea = next((x for x in pedido.lineas if x.id == str(linea.get("linea_id"))), None)
                    if pedido_linea:
                        pedido_linea.precio_unitario = precio
                    if articulo_id:
                        self.editor_articulos.editar_por_codigo(
                            articulo_id,
                            precio=precio,
                            proveedor=sesion.get("proveedor_llegada") or sesion.get("proveedor_esperado") or "",
                        )

            # Aplicar lineas adicionales
            for ad in sesion.get("lineas_adicionales", []):
                incidencias.extend(ad.get("incidencias") or [])
                res = self.core.stock.registrar_entrada(
                    nombre=str(ad.get("nombre") or ""),
                    cantidad=_to_float(ad.get("cantidad"), 0.0),
                    unidad=str(ad.get("unidad") or ""),
                    ubicacion="recepcion",
                    proveedor=sesion.get("proveedor_llegada") or sesion.get("proveedor_esperado") or "",
                    articulo_id=str(ad.get("articulo_id") or ""),
                    caducidad=str(ad.get("caducidad") or ""),
                    coste_unitario=_to_float(ad.get("precio_unitario"), 0.0),
                    motivo=f"recepcion rp3 adicional {pedido.id}",
                    trazabilidad={
                        "rp": self.VERSION,
                        "sesion_id": sesion_id,
                        "pedido_id": pedido.id,
                        "adicional_id": ad.get("id"),
                        "motivo": ad.get("motivo") or "",
                    },
                )
                lote = dict(res.get("lote") or {})
                movimiento = dict(res.get("movimiento") or {})
                entradas_stock.append({
                    "nombre": lote.get("nombre") or ad.get("nombre"),
                    "articulo_id": lote.get("articulo_id") or ad.get("articulo_id") or "",
                    "cantidad": _to_float(lote.get("cantidad"), _to_float(ad.get("cantidad"), 0.0)),
                    "unidad": lote.get("unidad") or ad.get("unidad"),
                    "caducidad": lote.get("caducidad") or "",
                    "lote_id": lote.get("id") or "",
                    "movimiento_id": movimiento.get("id") or "",
                    "coste_unitario": _to_float(lote.get("coste_unitario"), _to_float(ad.get("precio_unitario"), 0.0)),
                })

            # Cerrar o dejar pendiente el pedido segun diferencias.
            hay_diferencias_abiertas = any(
                str(x.get("estado_linea") or "") in {"parcial", "no_recibida", "rechazada", "sustitucion"}
                for x in sesion.get("lineas_esperadas", [])
            )
            if not hay_diferencias_abiertas and not sesion.get("lineas_adicionales"):
                pedido.estado = "recibido"
                pedido.recibido_en = datetime.now().isoformat(timespec="seconds")
                pedido.tocar("pedido_recibido_rp3", "Recepcion completa sin diferencias.")
                for linea in pedido.lineas:
                    if linea.necesidad_id and linea.necesidad_id in self.core.compras.necesidades:
                        necesidad = self.core.compras.necesidades[linea.necesidad_id]
                        necesidad.estado = "comprada"
                        necesidad.tocar()
            else:
                pedido.tocar("recepcion_parcial_rp3", "Recepcion con diferencias/incidencias. Pedido pendiente de cierre.")
                obs = str(pedido.observaciones or "").strip()
                marca = f"RP3:{sesion_id} diferencias:{len(incidencias)}"
                pedido.observaciones = f"{obs} | {marca}".strip(" |")

            self.core.compras._guardar()

            sesion["estado"] = "aplicada"
            sesion["solo_vista_previa"] = False
            sesion["aplicada_en"] = datetime.now().isoformat(timespec="seconds")
            sesion["incidencias"] = incidencias
            self._recalcular_sesion(sesion)
            self._guardar_sesiones(sesiones)

            registro = {
                "id": _rid("RPR3"),
                "sesion_id": sesion_id,
                "pedido_id": pedido.id,
                "proveedor_esperado": sesion.get("proveedor_esperado"),
                "proveedor_llegada": sesion.get("proveedor_llegada"),
                "creado_en": datetime.now().isoformat(timespec="seconds"),
                "estado": "APLICADA",
                "resumen": dict(sesion.get("resumen") or {}),
                "incidencias": incidencias,
                "entradas_stock": entradas_stock,
            }
            registros = self._leer_lista(self.path_registros)
            registros.append(registro)
            self._escribir_lista(self.path_registros, registros)

            return {
                "ok": True,
                "estado": "APLICADA",
                "sesion_id": sesion_id,
                "pedido_id": pedido.id,
                "registro": registro,
                "stock_despues": self.core.stock.stock_actual(),
                "mensaje": "Recepcion aplicada con trazabilidad completa.",
            }
        except Exception as exc:
            # rollback completo
            self.core.stock.lotes = lotes_antes
            self.core.stock.movimientos = movimientos_antes
            self.core.stock._guardar_automatico()
            restaurado = self.core.compras.pedidos_sugeridos.get(pedido.id)
            if restaurado:
                restaurado_rest = type(restaurado).from_dict(pedido_antes)
                self.core.compras.pedidos_sugeridos[pedido.id] = restaurado_rest
            self.core.compras._guardar()
            return {
                "ok": False,
                "estado": "ERROR_REVERTIDO",
                "sesion_id": sesion_id,
                "pedido_id": pedido.id,
                "mensaje": f"No se aplico ningun cambio: {exc}",
            }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _inc(tipo: str, detalle: str) -> dict[str, Any]:
        return {
            "id": _rid("INCRP3"),
            "tipo": tipo,
            "detalle": detalle,
            "fecha": datetime.now().isoformat(timespec="seconds"),
        }

    def _mut_sesion(self, sesion_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        sesiones = self._leer_lista(self.path_sesiones)
        idx = next((i for i, s in enumerate(sesiones) if str(s.get("id")) == str(sesion_id)), None)
        if idx is None:
            raise ValueError("Sesion de recepcion no encontrada.")
        return sesiones[idx], sesiones

    def _guardar_sesiones(self, sesiones: list[dict[str, Any]]) -> None:
        self._escribir_lista(self.path_sesiones, sesiones)

    def _recalcular_sesion(self, sesion: dict[str, Any]) -> None:
        esperadas = sesion.get("lineas_esperadas", [])
        adicionales = sesion.get("lineas_adicionales", [])
        resumen = {
            "esperadas": len(esperadas),
            "aceptadas": sum(1 for x in esperadas if x.get("estado_linea") == "aceptada"),
            "parciales": sum(1 for x in esperadas if x.get("estado_linea") == "parcial"),
            "rechazadas": sum(1 for x in esperadas if x.get("estado_linea") == "rechazada"),
            "no_recibidas": sum(1 for x in esperadas if x.get("estado_linea") == "no_recibida"),
            "adicionales": len(adicionales),
            "incidencias": sum(len(x.get("incidencias") or []) for x in esperadas) + sum(len(x.get("incidencias") or []) for x in adicionales),
        }
        sesion["resumen"] = resumen
        sesion["estado"] = "preparada" if all(str(x.get("estado_linea") or "") != "pendiente" for x in esperadas) else "borrador"

    @staticmethod
    def _enriquecer_resumen(sesion: dict[str, Any]) -> dict[str, Any]:
        out = deepcopy(sesion)
        out["diferencias"] = []
        for linea in out.get("lineas_esperadas", []):
            out["diferencias"].extend(linea.get("incidencias") or [])
        for linea in out.get("lineas_adicionales", []):
            out["diferencias"].extend(linea.get("incidencias") or [])
        return out

    @staticmethod
    def _leer_lista(path: Path) -> list[dict[str, Any]]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []

    @staticmethod
    def _escribir_lista(path: Path, data: list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        json.loads(tmp.read_text(encoding="utf-8"))
        tmp.replace(path)


__all__ = ["RecepcionOperativaRP3"]
