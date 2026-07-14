from __future__ import annotations

from typing import Dict, List, Any, Optional
from datetime import datetime
from MODELOS.compras import NecesidadCompra, PedidoSugerido, LineaPedido


class MotorCompras:
    """Gestión manual de necesidades, pedidos y recepción de compras."""

    def __init__(self, db=None):
        self.db = db
        self.necesidades: Dict[str, NecesidadCompra] = {}
        self.pedidos_sugeridos: Dict[str, PedidoSugerido] = {}
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

    def _guardar(self) -> None:
        if not self.db:
            return
        self.db.guardar("compras_necesidades", [n.to_dict() for n in self.necesidades.values()])
        self.db.guardar("compras_pedidos", [p.to_dict() for p in self.pedidos_sugeridos.values()])

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
            entradas.append(resultado)
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
