from __future__ import annotations

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import unicodedata
from MODELOS.compras import (
    NecesidadCompra,
    PedidoSugerido,
    LineaPedido,
    ProveedorCompra,
    PropuestaCompraInteligente,
    CompraRegistrada,
)


class MotorCompras:
    """Gestión manual de necesidades, pedidos y recepción de compras."""

    def __init__(self, db=None):
        self.db = db
        self.necesidades: Dict[str, NecesidadCompra] = {}
        self.pedidos_sugeridos: Dict[str, PedidoSugerido] = {}
        self.proveedores: Dict[str, ProveedorCompra] = {}
        self.propuestas_compra: Dict[str, PropuestaCompraInteligente] = {}
        self.compras_registradas: Dict[str, CompraRegistrada] = {}
        self._cargar()

    def _cargar(self) -> None:
        if not self.db:
            return
        for datos in self.db.cargar("compras_necesidades"):
            try:
                necesidad = NecesidadCompra.from_dict(datos)
                self.necesidades[necesidad.id] = necesidad
            except Exception:
                continue
        for datos in self.db.cargar("compras_pedidos"):
            try:
                pedido = PedidoSugerido.from_dict(datos)
                self.pedidos_sugeridos[pedido.id] = pedido
            except Exception:
                continue
        for datos in self.db.cargar("compras_proveedores"):
            try:
                proveedor = ProveedorCompra.from_dict(datos)
                self.proveedores[proveedor.id] = proveedor
            except Exception:
                continue
        for datos in self.db.cargar("compras_propuestas"):
            try:
                propuesta = PropuestaCompraInteligente.from_dict(datos)
                self.propuestas_compra[propuesta.id] = propuesta
            except Exception:
                continue
        for datos in self.db.cargar("compras_registros"):
            try:
                compra = CompraRegistrada.from_dict(datos)
                self.compras_registradas[compra.id] = compra
            except Exception:
                continue
        self._migrar_proveedores_legacy_si_aplica()

    def _guardar(self) -> None:
        if not self.db:
            return
        self.db.guardar("compras_necesidades", [n.to_dict() for n in self.necesidades.values()])
        self.db.guardar("compras_pedidos", [p.to_dict() for p in self.pedidos_sugeridos.values()])
        self.db.guardar("compras_proveedores", [x.to_dict() for x in self.proveedores.values()])
        self.db.guardar("compras_propuestas", [x.to_dict() for x in self.propuestas_compra.values()])
        self.db.guardar("compras_registros", [x.to_dict() for x in self.compras_registradas.values()])

    def _migrar_proveedores_legacy_si_aplica(self) -> None:
        if not self.db or self.proveedores:
            return
        try:
            ruta = self.db.db_dir / "proveedores.json"
            if not ruta.exists():
                return
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            if not isinstance(datos, list):
                return
            for item in datos:
                if not isinstance(item, dict):
                    continue
                nombre = str(item.get("nombre") or "").strip()
                if not nombre:
                    continue
                estado = str(item.get("estado") or "activo").strip().lower()
                observaciones = str(item.get("observaciones") or "").strip()
                prov = ProveedorCompra(
                    nombre=nombre,
                    observaciones=observaciones,
                    estado="activo" if estado == "activo" else "inactivo",
                )
                self.proveedores[prov.id] = prov
            if self.proveedores:
                self.db.guardar("compras_proveedores", [x.to_dict() for x in self.proveedores.values()])
        except Exception:
            return

    # ------------------------------------------------------------------
    # NECESIDADES (C1)
    # ------------------------------------------------------------------
    def registrar_necesidad(self, nombre: str, cantidad: float, unidad: str, familia: str = "", proveedor_preferente: str = "", motivo: str = "", prioridad: int = 50, articulo_id: str = "", fecha_necesaria: str = "") -> NecesidadCompra:
        necesidad = NecesidadCompra(
            nombre=nombre,
            cantidad=float(cantidad),
            unidad=unidad,
            familia=familia,
            proveedor_preferente=proveedor_preferente or "Sin proveedor asignado",
            motivo=motivo,
            prioridad=int(prioridad),
            articulo_id=articulo_id,
            fecha_necesaria=fecha_necesaria,
        )
        self.necesidades[necesidad.id] = necesidad
        self._guardar()
        return necesidad

    def obtener(self, necesidad_id: str) -> Optional[NecesidadCompra]:
        return self.necesidades.get(necesidad_id)

    def listar_necesidades(self, solo_pendientes: bool = True, estado: str = "") -> List[Dict[str, Any]]:
        necesidades = list(self.necesidades.values())
        if estado:
            necesidades = [n for n in necesidades if n.estado == estado]
        elif solo_pendientes:
            necesidades = [n for n in necesidades if n.estado == "pendiente"]
        necesidades.sort(key=lambda n: (-n.prioridad, n.fecha_necesaria or "9999-99-99", n.nombre.lower()))
        return [n.to_dict() for n in necesidades]

    def buscar_necesidades(self, texto: str = "", estado: str = "") -> List[Dict[str, Any]]:
        texto = (texto or "").strip().lower()
        resultados = []
        for n in self.necesidades.values():
            if estado and n.estado != estado:
                continue
            hay = " ".join([n.id, n.nombre, n.articulo_id, n.proveedor_preferente, n.motivo, n.familia]).lower()
            if not texto or texto in hay:
                resultados.append(n)
        resultados.sort(key=lambda n: (-n.prioridad, n.nombre.lower()))
        return [n.to_dict() for n in resultados]

    def editar_necesidad(self, necesidad_id: str, **cambios) -> NecesidadCompra:
        necesidad = self.necesidades.get(necesidad_id)
        if not necesidad:
            raise KeyError(f"Necesidad no encontrada: {necesidad_id}")
        campos = {"nombre", "cantidad", "unidad", "familia", "proveedor_preferente", "motivo", "prioridad", "articulo_id", "fecha_necesaria"}
        for campo, valor in cambios.items():
            if campo not in campos or valor is None:
                continue
            if campo == "cantidad":
                valor = float(valor)
            elif campo == "prioridad":
                valor = int(valor)
            setattr(necesidad, campo, valor)
        necesidad.tocar()
        sincronizados = self._sincronizar_necesidad_en_pedidos(necesidad)
        self._guardar()
        necesidad._pedidos_sincronizados = sincronizados
        return necesidad

    def _sincronizar_necesidad_en_pedidos(self, necesidad: NecesidadCompra) -> List[str]:
        """Actualiza las líneas vinculadas en pedidos todavía editables.

        Una necesidad es la fuente de verdad mientras el pedido siga en borrador o
        preparado. Los pedidos enviados/recibidos no se alteran automáticamente.
        """
        pedidos = []
        for pedido in self.pedidos_sugeridos.values():
            if pedido.estado not in {"borrador", "preparado"}:
                continue
            tocado = False
            for linea in pedido.lineas:
                if linea.necesidad_id != necesidad.id:
                    continue
                linea.nombre = necesidad.nombre
                linea.cantidad = float(necesidad.cantidad)
                linea.unidad = necesidad.unidad
                linea.articulo_id = necesidad.articulo_id
                linea.familia = necesidad.familia
                tocado = True
            if tocado:
                if necesidad.proveedor_preferente and pedido.proveedor != necesidad.proveedor_preferente:
                    pedido.proveedor = necesidad.proveedor_preferente
                pedido.tocar("necesidad_sincronizada", f"Necesidad actualizada: {necesidad.nombre}.")
                pedidos.append(pedido.id)
        return pedidos

    def cambiar_estado(self, necesidad_id: str, estado: str) -> NecesidadCompra:
        estado = (estado or "").strip().lower()
        if estado not in NecesidadCompra.ESTADOS_VALIDOS:
            raise ValueError(f"Estado no válido: {estado}")
        necesidad = self.necesidades.get(necesidad_id)
        if not necesidad:
            raise KeyError(f"Necesidad no encontrada: {necesidad_id}")
        necesidad.estado = estado
        necesidad.tocar()
        afectados = []
        if estado in {"comprada", "cancelada"}:
            for pedido in self.pedidos_sugeridos.values():
                if pedido.estado not in {"borrador", "preparado"}:
                    continue
                antes = len(pedido.lineas)
                pedido.lineas = [l for l in pedido.lineas if l.necesidad_id != necesidad_id]
                if len(pedido.lineas) != antes:
                    pedido.tocar("necesidad_retirada", f"Necesidad {estado}: {necesidad.nombre}.")
                    afectados.append(pedido.id)
        self._guardar()
        necesidad._pedidos_afectados = afectados
        return necesidad

    def eliminar_necesidad(self, necesidad_id: str) -> bool:
        if necesidad_id not in self.necesidades:
            return False
        del self.necesidades[necesidad_id]
        self._guardar()
        return True


    def resumen_necesidades(self) -> Dict[str, int]:
        """Resume necesidades sin confundir pendientes libres con vinculadas."""
        asignadas = self._necesidades_ya_asignadas()
        pendientes = [n for n in self.necesidades.values() if n.estado == "pendiente"]
        return {
            "pendientes_sin_pedido": sum(n.id not in asignadas for n in pendientes),
            "vinculadas_a_pedido": sum(n.id in asignadas for n in pendientes),
            "compradas": sum(n.estado == "comprada" for n in self.necesidades.values()),
            "canceladas": sum(n.estado == "cancelada" for n in self.necesidades.values()),
            "total_pendientes": len(pendientes),
        }

    # ------------------------------------------------------------------
    # PEDIDOS OPERATIVOS (C2)
    # ------------------------------------------------------------------
    def _necesidades_ya_asignadas(self) -> set[str]:
        asignadas = set()
        for pedido in self.pedidos_sugeridos.values():
            if pedido.estado in {"cancelado", "recibido"}:
                continue
            asignadas.update(l.necesidad_id for l in pedido.lineas if l.necesidad_id)
        return asignadas

    def generar_pedidos_sugeridos(self) -> Dict[str, Any]:
        grupos: Dict[str, List[NecesidadCompra]] = {}
        asignadas = self._necesidades_ya_asignadas()
        pendientes = [n for n in self.necesidades.values() if n.estado == "pendiente" and n.id not in asignadas]
        for necesidad in pendientes:
            proveedor = necesidad.proveedor_preferente or "Sin proveedor asignado"
            grupos.setdefault(proveedor, []).append(necesidad)

        pedidos = []
        for proveedor, necesidades in grupos.items():
            lineas = [
                LineaPedido(
                    nombre=n.nombre,
                    cantidad=n.cantidad,
                    unidad=n.unidad,
                    articulo_id=n.articulo_id,
                    familia=n.familia,
                    necesidad_id=n.id,
                )
                for n in sorted(necesidades, key=lambda n: n.prioridad, reverse=True)
            ]
            pedido = PedidoSugerido(proveedor=proveedor, lineas=lineas)
            self.pedidos_sugeridos[pedido.id] = pedido
            pedidos.append(pedido.to_dict())
        self._guardar()
        vinculadas = [n for n in self.necesidades.values() if n.estado == "pendiente" and n.id in asignadas]
        return {
            "pedidos_sugeridos": pedidos,
            "total_pedidos": len(pedidos),
            "total_necesidades": len(pendientes),
            "pendientes_ya_vinculadas": len(vinculadas),
            "pedidos_abiertos": len([p for p in self.pedidos_sugeridos.values() if p.estado not in {"cancelado", "recibido"}]),
            "lectura_host_ai": self._lectura_pedidos(pedidos),
        }

    def obtener_pedido(self, pedido_id: str) -> Optional[PedidoSugerido]:
        return self.pedidos_sugeridos.get(pedido_id)

    def listar_pedidos(self, estado: str = "", texto: str = "") -> List[Dict[str, Any]]:
        estado = (estado or "").strip().lower()
        texto = (texto or "").strip().lower()
        pedidos = []
        for p in self.pedidos_sugeridos.values():
            if estado and p.estado != estado:
                continue
            hay = " ".join([p.id, p.proveedor, p.estado, p.observaciones] + [l.nombre for l in p.lineas]).lower()
            if texto and texto not in hay:
                continue
            pedidos.append(p)
        pedidos.sort(key=lambda p: (p.actualizado_en, p.id), reverse=True)
        return [p.to_dict() for p in pedidos]

    def editar_pedido(self, pedido_id: str, proveedor: Optional[str] = None, observaciones: Optional[str] = None) -> PedidoSugerido:
        pedido = self._pedido_editable(pedido_id)
        if proveedor is not None and proveedor.strip():
            pedido.proveedor = proveedor.strip()
        if observaciones is not None:
            pedido.observaciones = observaciones.strip()
        pedido.tocar("pedido_editado", "Cabecera del pedido actualizada.")
        self._guardar()
        return pedido

    def agregar_linea_pedido(self, pedido_id: str, nombre: str, cantidad: float, unidad: str, articulo_id: str = "", familia: str = "", necesidad_id: str = "", precio_unitario: float = 0.0, observaciones: str = "") -> LineaPedido:
        pedido = self._pedido_editable(pedido_id)
        if float(cantidad) <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")
        linea = LineaPedido(nombre=nombre, cantidad=cantidad, unidad=unidad, articulo_id=articulo_id, familia=familia, necesidad_id=necesidad_id, precio_unitario=precio_unitario, observaciones=observaciones)
        pedido.lineas.append(linea)
        pedido.tocar("linea_agregada", f"Añadido {nombre}: {cantidad} {unidad}.")
        self._guardar()
        return linea

    def editar_linea_pedido(self, pedido_id: str, linea_id: str, **cambios) -> LineaPedido:
        pedido = self._pedido_editable(pedido_id)
        linea = self._obtener_linea(pedido, linea_id)
        campos = {"nombre", "cantidad", "unidad", "articulo_id", "familia", "precio_unitario", "observaciones"}
        for campo, valor in cambios.items():
            if campo not in campos or valor is None:
                continue
            if campo in {"cantidad", "precio_unitario"}:
                valor = float(valor)
                if campo == "cantidad" and valor <= 0:
                    raise ValueError("La cantidad debe ser mayor que cero.")
            setattr(linea, campo, valor)
        pedido.tocar("linea_editada", f"Línea actualizada: {linea.nombre}.")
        self._guardar()
        return linea

    def eliminar_linea_pedido(self, pedido_id: str, linea_id: str) -> bool:
        pedido = self._pedido_editable(pedido_id)
        antes = len(pedido.lineas)
        pedido.lineas = [l for l in pedido.lineas if l.id != linea_id]
        if len(pedido.lineas) == antes:
            return False
        pedido.tocar("linea_eliminada", f"Línea eliminada: {linea_id}.")
        self._guardar()
        return True

    def cambiar_estado_pedido(self, pedido_id: str, estado: str) -> PedidoSugerido:
        pedido = self.pedidos_sugeridos.get(pedido_id)
        if not pedido:
            raise KeyError(f"Pedido no encontrado: {pedido_id}")
        estado = (estado or "").strip().lower()
        if estado not in PedidoSugerido.ESTADOS_VALIDOS:
            raise ValueError(f"Estado no válido: {estado}")
        if pedido.estado == "recibido":
            raise ValueError("Un pedido recibido no puede cambiar de estado.")
        if estado in {"preparado", "enviado"} and not pedido.lineas:
            raise ValueError("No se puede preparar o enviar un pedido sin líneas.")
        pedido.estado = estado
        if estado == "enviado":
            pedido.enviado_en = datetime.now().isoformat(timespec="seconds")
        pedido.tocar("estado_cambiado", f"Pedido marcado como {estado}.")
        self._guardar()
        return pedido

    def recibir_pedido(self, pedido_id: str, motor_stock, ubicacion: str = "", caducidades: Optional[Dict[str, str]] = None, costes: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        pedido = self.pedidos_sugeridos.get(pedido_id)
        if not pedido:
            raise KeyError(f"Pedido no encontrado: {pedido_id}")
        if pedido.estado == "recibido":
            raise ValueError("Este pedido ya fue recibido. No se duplicará la entrada de stock.")
        if pedido.estado == "cancelado":
            raise ValueError("No se puede recibir un pedido cancelado.")
        if not pedido.lineas:
            raise ValueError("El pedido no tiene líneas para recibir.")
        caducidades = caducidades or {}
        costes = costes or {}
        entradas = []
        for linea in pedido.lineas:
            coste = float(costes.get(linea.id, linea.precio_unitario or 0))
            resultado = motor_stock.registrar_entrada(
                nombre=linea.nombre,
                cantidad=linea.cantidad,
                unidad=linea.unidad,
                familia=linea.familia,
                ubicacion=ubicacion,
                proveedor=pedido.proveedor,
                articulo_id=linea.articulo_id,
                caducidad=caducidades.get(linea.id, ""),
                coste_unitario=coste,
                motivo=f"recepción pedido {pedido.id}",
            )
            linea.precio_unitario = coste
            lote = dict(resultado.get("lote") or {})
            movimiento = dict(resultado.get("movimiento") or {})
            entradas.append({
                "nombre": lote.get("nombre") or linea.nombre,
                "articulo_id": lote.get("articulo_id") or linea.articulo_id,
                "cantidad": float(lote.get("cantidad", linea.cantidad) or 0),
                "unidad": lote.get("unidad") or linea.unidad,
                "ubicacion": lote.get("ubicacion") or ubicacion,
                "caducidad": lote.get("caducidad") or caducidades.get(linea.id, ""),
                "coste_unitario": float(lote.get("coste_unitario", coste) or 0),
                "importe": round(float(lote.get("cantidad", linea.cantidad) or 0) * float(lote.get("coste_unitario", coste) or 0), 4),
                "lote_id": lote.get("id", ""),
                "movimiento_id": movimiento.get("id", ""),
                "lote": lote,
                "movimiento": movimiento,
            })
            if linea.necesidad_id and linea.necesidad_id in self.necesidades:
                self.necesidades[linea.necesidad_id].estado = "comprada"
                self.necesidades[linea.necesidad_id].tocar()
        pedido.estado = "recibido"
        pedido.recibido_en = datetime.now().isoformat(timespec="seconds")
        pedido.tocar("pedido_recibido", f"Recepción completada con {len(entradas)} línea(s).")
        self._guardar()
        return {
            "pedido": pedido.to_dict(),
            "entradas_stock": entradas,
            "total_lineas": len(entradas),
            "lectura_host_ai": f"Pedido {pedido.id} recibido. Se actualizaron {len(entradas)} líneas de stock.",
        }

    def historial_pedido(self, pedido_id: str) -> List[Dict[str, str]]:
        pedido = self.pedidos_sugeridos.get(pedido_id)
        if not pedido:
            raise KeyError(f"Pedido no encontrado: {pedido_id}")
        return list(pedido.historial)

    def diagnosticar_compras(self) -> Dict[str, Any]:
        pendientes = [n for n in self.necesidades.values() if n.estado == "pendiente"]
        avisos = []
        if not pendientes:
            avisos.append("No hay necesidades de compra pendientes.")
        sin_proveedor = [n for n in pendientes if not n.proveedor_preferente or n.proveedor_preferente == "Sin proveedor asignado"]
        if sin_proveedor:
            avisos.append(f"Hay {len(sin_proveedor)} necesidades sin proveedor asignado.")
        urgentes = [n for n in pendientes if n.prioridad >= 85]
        if urgentes:
            avisos.append(f"Hay {len(urgentes)} necesidades urgentes.")
        pedidos_abiertos = [p for p in self.pedidos_sugeridos.values() if p.estado not in {"recibido", "cancelado"}]
        return {
            "total_necesidades": len(self.necesidades),
            "pendientes": len(pendientes),
            "compradas": sum(n.estado == "comprada" for n in self.necesidades.values()),
            "canceladas": sum(n.estado == "cancelada" for n in self.necesidades.values()),
            "sin_proveedor": len(sin_proveedor),
            "urgentes": len(urgentes),
            "pedidos_abiertos": len(pedidos_abiertos),
            "pedidos_recibidos": sum(p.estado == "recibido" for p in self.pedidos_sugeridos.values()),
            "avisos": avisos,
            "estado": "revisar" if sin_proveedor or urgentes else "ok",
            "lectura_host_ai": "Compras listas para pedido operativo." if (pendientes or pedidos_abiertos) and not sin_proveedor else f"Compras con {len(avisos)} avisos.",
        }

    def _pedido_editable(self, pedido_id: str) -> PedidoSugerido:
        pedido = self.pedidos_sugeridos.get(pedido_id)
        if not pedido:
            raise KeyError(f"Pedido no encontrado: {pedido_id}")
        if pedido.estado not in {"borrador", "preparado"}:
            raise ValueError(f"El pedido no se puede editar en estado {pedido.estado}.")
        return pedido

    @staticmethod
    def _obtener_linea(pedido: PedidoSugerido, linea_id: str) -> LineaPedido:
        for linea in pedido.lineas:
            if linea.id == linea_id:
                return linea
        raise KeyError(f"Línea no encontrada: {linea_id}")

    @staticmethod
    def _lectura_pedidos(pedidos: List[Dict[str, Any]]) -> str:
        if not pedidos:
            return "No hay necesidades pendientes nuevas para generar pedidos."
        lineas = sum(p.get("total_lineas", 0) for p in pedidos)
        return f"Generados {len(pedidos)} pedidos en borrador con {lineas} líneas de compra."

    # ------------------------------------------------------------------
    # R4.1 - PROVEEDORES / PROPUESTAS / COMPRAS REGISTRADAS
    # ------------------------------------------------------------------
    @staticmethod
    def _normalizar_texto(valor: Any) -> str:
        texto = str(valor or "").strip().lower()
        texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
        return " ".join(texto.split())

    @staticmethod
    def _normalizar_clave_producto(nombre: str, unidad: str, articulo_id: str = "") -> str:
        aid = str(articulo_id or "").strip().upper()
        if aid:
            return f"ART:{aid}"
        return f"NOM:{MotorCompras._normalizar_texto(nombre)}|UNI:{MotorCompras._normalizar_texto(unidad)}"

    @classmethod
    def _normalizar_origenes(cls, origenes: Any) -> List[str]:
        if isinstance(origenes, str):
            bruto = [parte.strip() for parte in origenes.split(";")]
        else:
            bruto = [str(parte or "").strip() for parte in list(origenes or [])]
        unicos: Dict[str, str] = {}
        for origen in bruto:
            if not origen:
                continue
            clave = cls._normalizar_texto(origen)
            if clave and clave not in unicos:
                unicos[clave] = " ".join(origen.split())
        return [unicos[clave] for clave in sorted(unicos.keys())]

    @classmethod
    def _origenes_a_texto(cls, origenes: Any) -> str:
        lista = cls._normalizar_origenes(origenes)
        return "; ".join(lista) if lista else "Host AI"

    @classmethod
    def _clave_propuesta(cls, producto: str, unidad: str, articulo_id: str = "", origenes: Any = None) -> str:
        producto_clave = cls._normalizar_clave_producto(producto, unidad, articulo_id)
        origen_clave = "|".join(cls._normalizar_texto(x) for x in cls._normalizar_origenes(origenes)) or "host ai"
        return f"{producto_clave}|ORI:{origen_clave}"

    @staticmethod
    def _float_igual(a: float, b: float, tolerancia: float = 0.0001) -> bool:
        return abs(float(a or 0) - float(b or 0)) <= tolerancia

    def _consolidar_propuestas_pendientes_duplicadas(self) -> Dict[str, PropuestaCompraInteligente]:
        agrupadas: Dict[str, List[PropuestaCompraInteligente]] = {}
        for propuesta in self.propuestas_compra.values():
            if propuesta.estado != "pendiente":
                continue
            clave = self._clave_propuesta(propuesta.producto, propuesta.unidad, propuesta.articulo_id, propuesta.origen)
            agrupadas.setdefault(clave, []).append(propuesta)

        canonicas: Dict[str, PropuestaCompraInteligente] = {}
        for clave, grupo in agrupadas.items():
            grupo.sort(key=lambda x: (x.creado_en or "", x.id))
            canonica = grupo[0]
            canonicas[clave] = canonica
            for duplicada in grupo[1:]:
                duplicada.estado = "cancelada"
                duplicada.tocar()
        return canonicas

    def _cobertura_compras_registradas(self) -> Dict[str, Dict[str, float]]:
        por_propuesta: Dict[str, float] = {}
        por_producto: Dict[str, float] = {}
        for compra in self.compras_registradas.values():
            if compra.estado == "cancelada":
                continue
            cantidad = max(0.0, round(float(compra.cantidad or 0), 4))
            if cantidad <= 0:
                continue
            clave_producto = self._normalizar_clave_producto(compra.producto, compra.unidad, compra.articulo_id)
            clave_propuesta = ""
            if compra.propuesta_id and compra.propuesta_id in self.propuestas_compra:
                propuesta = self.propuestas_compra[compra.propuesta_id]
                clave_propuesta = self._clave_propuesta(propuesta.producto, propuesta.unidad, propuesta.articulo_id, propuesta.origen)
            elif str(compra.origen_tipo or "").strip().lower() == "inteligente":
                clave_propuesta = self._clave_propuesta(compra.producto, compra.unidad, compra.articulo_id, compra.origen)

            if clave_propuesta:
                por_propuesta[clave_propuesta] = round(por_propuesta.get(clave_propuesta, 0.0) + cantidad, 4)
            else:
                por_producto[clave_producto] = round(por_producto.get(clave_producto, 0.0) + cantidad, 4)
        return {"por_propuesta": por_propuesta, "por_producto": por_producto}

    def _actualizar_propuesta_existente(
        self,
        propuesta: PropuestaCompraInteligente,
        necesario: float,
        disponible: float,
        comprar: float,
        prioridad: str,
        proveedor_sugerido: str,
        origen_texto: str,
    ) -> bool:
        cambios = False
        if not self._float_igual(propuesta.necesario, necesario):
            propuesta.necesario = necesario
            cambios = True
        if not self._float_igual(propuesta.disponible, disponible):
            propuesta.disponible = disponible
            cambios = True
        if not self._float_igual(propuesta.comprar, comprar):
            propuesta.comprar = comprar
            cambios = True
        if str(propuesta.prioridad or "") != str(prioridad or ""):
            propuesta.prioridad = prioridad
            cambios = True
        if str(propuesta.proveedor_sugerido or "") != str(proveedor_sugerido or ""):
            propuesta.proveedor_sugerido = proveedor_sugerido
            cambios = True
        if self._origenes_a_texto(propuesta.origen) != origen_texto:
            propuesta.origen = origen_texto
            cambios = True
        if cambios:
            propuesta.tocar()
        return cambios

    def listar_proveedores(self, incluir_inactivos: bool = True, texto: str = "") -> List[Dict[str, Any]]:
        q = self._normalizar_texto(texto)
        salida = []
        for prov in self.proveedores.values():
            if not incluir_inactivos and prov.estado != "activo":
                continue
            hay = " ".join(
                [
                    prov.id,
                    prov.nombre,
                    prov.cif,
                    prov.telefono,
                    prov.email,
                    prov.direccion,
                    prov.comercial,
                    prov.observaciones,
                ]
            )
            if q and q not in self._normalizar_texto(hay):
                continue
            salida.append(prov)
        salida.sort(key=lambda x: (0 if x.estado == "activo" else 1, x.nombre.lower()))
        return [x.to_dict() for x in salida]

    def crear_proveedor_manual(
        self,
        nombre: str,
        cif: str = "",
        telefono: str = "",
        email: str = "",
        direccion: str = "",
        comercial: str = "",
        observaciones: str = "",
    ) -> ProveedorCompra:
        nombre = str(nombre or "").strip()
        if not nombre:
            raise ValueError("El nombre del proveedor es obligatorio")
        nombre_norm = self._normalizar_texto(nombre)
        for prov in self.proveedores.values():
            if self._normalizar_texto(prov.nombre) == nombre_norm:
                raise ValueError("Ya existe un proveedor con ese nombre")
        nuevo = ProveedorCompra(
            nombre=nombre,
            cif=cif,
            telefono=telefono,
            email=email,
            direccion=direccion,
            comercial=comercial,
            observaciones=observaciones,
            estado="activo",
        )
        self.proveedores[nuevo.id] = nuevo
        self._guardar()
        return nuevo

    def editar_proveedor(self, proveedor_id: str, **cambios) -> ProveedorCompra:
        prov = self.proveedores.get(str(proveedor_id or ""))
        if not prov:
            raise KeyError(f"Proveedor no encontrado: {proveedor_id}")
        for campo in ("nombre", "cif", "telefono", "email", "direccion", "comercial", "observaciones"):
            if campo in cambios and cambios[campo] is not None:
                valor = str(cambios[campo]).strip()
                if campo == "nombre" and not valor:
                    raise ValueError("El nombre del proveedor es obligatorio")
                setattr(prov, campo, valor)
        if "estado" in cambios and cambios["estado"] is not None:
            estado = str(cambios["estado"]).strip().lower()
            if estado in ProveedorCompra.ESTADOS_VALIDOS:
                prov.estado = estado
        prov.tocar()
        self._guardar()
        return prov

    def desactivar_proveedor(self, proveedor_id: str) -> ProveedorCompra:
        prov = self.proveedores.get(str(proveedor_id or ""))
        if not prov:
            raise KeyError(f"Proveedor no encontrado: {proveedor_id}")
        prov.estado = "inactivo"
        prov.tocar()
        self._guardar()
        return prov

    def asociar_producto_proveedor(self, proveedor_id: str, producto: str) -> ProveedorCompra:
        prov = self.proveedores.get(str(proveedor_id or ""))
        if not prov:
            raise KeyError(f"Proveedor no encontrado: {proveedor_id}")
        nombre_producto = str(producto or "").strip()
        if not nombre_producto:
            raise ValueError("El producto es obligatorio")
        existentes_norm = {self._normalizar_texto(x): x for x in prov.productos_habituales}
        if self._normalizar_texto(nombre_producto) not in existentes_norm:
            prov.productos_habituales.append(nombre_producto)
        prov.tocar()
        self._guardar()
        return prov

    def registrar_compra_manual(
        self,
        producto: str,
        cantidad: float,
        unidad: str,
        proveedor: str,
        observaciones: str = "",
        prioridad: str = "Normal",
        articulo_id: str = "",
    ) -> CompraRegistrada:
        if float(cantidad or 0) <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")
        compra = CompraRegistrada(
            producto=producto,
            cantidad=float(cantidad),
            unidad=unidad,
            proveedor=proveedor,
            observaciones=observaciones,
            origen="Manual",
            origen_tipo="manual",
            prioridad=prioridad,
            articulo_id=articulo_id,
        )
        self.compras_registradas[compra.id] = compra
        self._guardar()
        return compra

    def listar_historial_compras(self, texto: str = "") -> List[Dict[str, Any]]:
        q = self._normalizar_texto(texto)
        salida = []
        for compra in self.compras_registradas.values():
            hay = " ".join([compra.id, compra.producto, compra.proveedor, compra.origen, compra.observaciones])
            if q and q not in self._normalizar_texto(hay):
                continue
            salida.append(compra)
        salida.sort(key=lambda x: (x.creado_en, x.id), reverse=True)
        return [x.to_dict() for x in salida]

    def listar_propuestas_compra(self, solo_pendientes: bool = True) -> List[Dict[str, Any]]:
        propuestas = list(self.propuestas_compra.values())
        if solo_pendientes:
            propuestas = [p for p in propuestas if p.estado == "pendiente"]
        propuestas.sort(key=lambda x: (x.creado_en, x.id), reverse=True)
        return [x.to_dict() for x in propuestas]

    @staticmethod
    def _prioridad_desde_ratio(necesario: float, disponible: float, comprar: float) -> str:
        if comprar <= 0:
            return "Baja"
        if necesario <= 0:
            return "Normal"
        ratio = (disponible / necesario) if necesario else 0
        if ratio < 0.35:
            return "Crítica"
        if ratio < 0.7:
            return "Alta"
        return "Normal"

    def generar_propuesta_compra_inteligente(self, core, plan_id: str = "") -> Dict[str, Any]:
        planes = list(core.produccion_real.listar_planes())
        planes_validos = []
        for p in planes:
            estado = str(p.get("estado") or "").lower()
            if estado in {"finalizado", "cancelado"}:
                continue
            if plan_id and str(p.get("id") or "") != str(plan_id):
                continue
            if list(p.get("tareas") or []):
                planes_validos.append(p)

        stock_actual = core.stock.stock_actual()
        stock_idx: Dict[str, float] = {}
        for item in list(stock_actual.get("items") or []):
            clave = self._normalizar_clave_producto(item.get("nombre", ""), item.get("unidad", "u"), item.get("articulo_id", ""))
            stock_idx[clave] = float(item.get("cantidad") or 0)

        agregadas: Dict[str, Dict[str, Any]] = {}
        for plan in planes_validos:
            plan_nombre = str(plan.get("nombre") or plan.get("evento") or plan.get("id") or "Plan")
            for tarea in list(plan.get("tareas") or []):
                receta_id = str(tarea.get("receta_id") or "").strip().upper()
                if not receta_id:
                    continue
                try:
                    raciones = int(float(tarea.get("cantidad") or 0) or 0)
                except (TypeError, ValueError):
                    raciones = 0
                if raciones <= 0:
                    raciones = 1
                try:
                    calculo = core.escandallos_inteligente.calcular_necesidades_receta(
                        receta_id,
                        raciones,
                        origen=f"{plan_nombre} / {tarea.get('titulo') or receta_id}",
                    )
                except Exception:
                    continue

                for nec in list(calculo.get("necesidades") or []):
                    producto = str(nec.get("nombre") or "").strip()
                    unidad = str(nec.get("unidad") or "u").strip() or "u"
                    articulo_id = str(nec.get("articulo_id") or "").strip()
                    necesario = float(nec.get("cantidad_bruta") or nec.get("cantidad_neta") or 0)
                    if necesario <= 0:
                        continue
                    clave = self._normalizar_clave_producto(producto, unidad, articulo_id)
                    item = agregadas.setdefault(
                        clave,
                        {
                            "producto": producto,
                            "unidad": unidad,
                            "articulo_id": articulo_id,
                            "necesario": 0.0,
                            "origenes": [],
                            "proveedor_sugerido": str(nec.get("proveedor_preferente") or "").strip(),
                        },
                    )
                    item["necesario"] += necesario
                    origen = str(nec.get("origen") or plan_nombre).strip() or plan_nombre
                    if origen:
                        item["origenes"].append(origen)

        pendientes_canonicas = self._consolidar_propuestas_pendientes_duplicadas()
        cobertura = self._cobertura_compras_registradas()
        cobertura_por_propuesta = cobertura["por_propuesta"]
        cobertura_por_producto = cobertura["por_producto"]
        claves_activas = set()
        creadas = []
        resumen = {
            "propuestas_nuevas": 0,
            "propuestas_actualizadas": 0,
            "propuestas_existentes": 0,
            "necesidades_cubiertas_por_compras": 0,
            "necesidades_sin_faltante": 0,
            "propuestas_cerradas": 0,
            "duplicados_consolidados": 0,
        }

        duplicados_cancelados = 0
        for propuesta in self.propuestas_compra.values():
            if propuesta.estado == "cancelada":
                pass
        for clave, propuesta in pendientes_canonicas.items():
            grupo = [p for p in self.propuestas_compra.values() if p.estado == "cancelada" and self._clave_propuesta(p.producto, p.unidad, p.articulo_id, p.origen) == clave]
            duplicados_cancelados += len(grupo)
        resumen["duplicados_consolidados"] = duplicados_cancelados

        agregadas_por_propuesta: Dict[str, Dict[str, Any]] = {}
        for item in agregadas.values():
            origenes = self._normalizar_origenes(item["origenes"])
            clave = self._clave_propuesta(item["producto"], item["unidad"], item["articulo_id"], origenes)
            destino = agregadas_por_propuesta.setdefault(
                clave,
                {
                    "producto": item["producto"],
                    "unidad": item["unidad"],
                    "articulo_id": item["articulo_id"],
                    "origenes": origenes,
                    "necesario": 0.0,
                    "proveedor_sugerido": item["proveedor_sugerido"],
                },
            )
            destino["necesario"] = round(float(destino["necesario"]) + float(item["necesario"]), 4)
            if not destino["proveedor_sugerido"]:
                destino["proveedor_sugerido"] = item["proveedor_sugerido"]

        for clave, item in agregadas_por_propuesta.items():
            claves_activas.add(clave)
            producto_clave = self._normalizar_clave_producto(item["producto"], item["unidad"], item["articulo_id"])
            necesario = round(float(item["necesario"]), 4)
            disponible = round(float(stock_idx.get(producto_clave, 0.0)), 4)
            cubierto_por_compras = round(float(cobertura_por_propuesta.get(clave, 0.0)) + float(cobertura_por_producto.get(producto_clave, 0.0)), 4)
            comprar = round(max(0.0, necesario - disponible - cubierto_por_compras), 4)
            prioridad = self._prioridad_desde_ratio(necesario, disponible, comprar)
            origen_texto = self._origenes_a_texto(item["origenes"])
            propuesta_existente = pendientes_canonicas.get(clave)

            if comprar <= 0:
                if propuesta_existente:
                    propuesta_existente.estado = "cancelada"
                    propuesta_existente.tocar()
                    resumen["propuestas_cerradas"] += 1
                if cubierto_por_compras > 0:
                    resumen["necesidades_cubiertas_por_compras"] += 1
                else:
                    resumen["necesidades_sin_faltante"] += 1
                continue

            if propuesta_existente:
                cambios = self._actualizar_propuesta_existente(
                    propuesta_existente,
                    necesario=necesario,
                    disponible=disponible,
                    comprar=comprar,
                    prioridad=prioridad,
                    proveedor_sugerido=item["proveedor_sugerido"],
                    origen_texto=origen_texto,
                )
                if cambios:
                    resumen["propuestas_actualizadas"] += 1
                else:
                    resumen["propuestas_existentes"] += 1
                continue

            propuesta = PropuestaCompraInteligente(
                producto=item["producto"],
                necesario=necesario,
                disponible=disponible,
                comprar=comprar,
                unidad=item["unidad"],
                origen=origen_texto,
                prioridad=prioridad,
                articulo_id=item["articulo_id"],
                proveedor_sugerido=item["proveedor_sugerido"],
                estado="pendiente",
            )
            self.propuestas_compra[propuesta.id] = propuesta
            creadas.append(propuesta.to_dict())
            resumen["propuestas_nuevas"] += 1

        for clave, propuesta in pendientes_canonicas.items():
            if clave in claves_activas:
                continue
            if propuesta.estado == "pendiente":
                propuesta.estado = "cancelada"
                propuesta.tocar()
                resumen["propuestas_cerradas"] += 1

        self._guardar()

        lineas = [
            "GENERACION COMPLETADA",
            "",
            f"- Propuestas nuevas: {resumen['propuestas_nuevas']}",
            f"- Propuestas actualizadas: {resumen['propuestas_actualizadas']}",
            f"- Propuestas ya existentes: {resumen['propuestas_existentes']}",
        ]
        if resumen["necesidades_cubiertas_por_compras"]:
            lineas.append(f"- Necesidades cubiertas por compras: {resumen['necesidades_cubiertas_por_compras']}")
        if resumen["necesidades_sin_faltante"]:
            lineas.append(f"- Necesidades sin faltante: {resumen['necesidades_sin_faltante']}")
        if resumen["propuestas_cerradas"]:
            lineas.append(f"- Propuestas cerradas: {resumen['propuestas_cerradas']}")
        if resumen["duplicados_consolidados"]:
            lineas.append(f"- Duplicados consolidados: {resumen['duplicados_consolidados']}")
        lineas.append("")
        if resumen["propuestas_nuevas"] == 0 and resumen["propuestas_actualizadas"] == 0:
            lineas.append("No se han creado duplicados.")
        lineas.append("Ningun pedido se ha creado automaticamente.")
        return {
            "total_propuestas": resumen["propuestas_nuevas"],
            "propuestas": creadas,
            "resumen": resumen,
            "lectura_host_ai": "\n".join(lineas),
        }

    def confirmar_propuesta_compra(self, propuesta_id: str, proveedor: str = "", observaciones: str = "") -> CompraRegistrada:
        propuesta = self.propuestas_compra.get(str(propuesta_id or ""))
        if not propuesta:
            raise KeyError(f"Propuesta no encontrada: {propuesta_id}")
        if propuesta.estado != "pendiente":
            raise ValueError("La propuesta ya no está pendiente")

        compra = CompraRegistrada(
            producto=propuesta.producto,
            cantidad=propuesta.comprar,
            unidad=propuesta.unidad,
            proveedor=str(proveedor or propuesta.proveedor_sugerido or "Sin proveedor"),
            observaciones=observaciones,
            origen=propuesta.origen,
            origen_tipo="inteligente",
            prioridad=propuesta.prioridad,
            articulo_id=propuesta.articulo_id,
            propuesta_id=propuesta.id,
        )
        propuesta.estado = "confirmada"
        propuesta.tocar()
        self.compras_registradas[compra.id] = compra
        self._guardar()
        return compra

    def cancelar_propuesta_compra(self, propuesta_id: str) -> PropuestaCompraInteligente:
        propuesta = self.propuestas_compra.get(str(propuesta_id or ""))
        if not propuesta:
            raise KeyError(f"Propuesta no encontrada: {propuesta_id}")
        if propuesta.estado != "pendiente":
            raise ValueError("La propuesta ya no está pendiente")
        propuesta.estado = "cancelada"
        propuesta.tocar()
        self._guardar()
        return propuesta

    def preparar_onboarding_proveedor_detectado(self, nombre_detectado: str, datos_detectados: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Preparación de arquitectura OCR (sin OCR real): siempre con alternativa manual."""
        nombre = str(nombre_detectado or "").strip()
        encontrado = next((p for p in self.proveedores.values() if self._normalizar_texto(p.nombre) == self._normalizar_texto(nombre)), None)
        return {
            "ocr_implementado": False,
            "nombre_detectado": nombre,
            "proveedor_existente": encontrado.to_dict() if encontrado else None,
            "sugerencia": "crear_manual" if not encontrado else "usar_existente",
            "faltantes_detectados": [k for k, v in dict(datos_detectados or {}).items() if not str(v or "").strip()],
            "alternativas_manuales": {
                "crear_proveedor_manual": True,
                "editar_proveedor_manual": True,
                "dejar_campos_vacios": True,
            },
            "mensaje": "No se bloquea la operación: puedes crear o completar la ficha manualmente.",
        }
