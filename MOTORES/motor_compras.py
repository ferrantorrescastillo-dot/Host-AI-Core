from __future__ import annotations

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import unicodedata
from MODELOS.compras import (
    NecesidadCompra,
    PedidoSugerido,
    LineaPedido,
    ProveedorCompra,
    PropuestaCompraInteligente,
    CompraRegistrada,
    AsociacionProductoProveedor,
    RecepcionCompra,
    IncidenciaCompra,
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
        self.recepciones_compra: Dict[str, RecepcionCompra] = {}
        self.incidencias_compra: Dict[str, IncidenciaCompra] = {}
        self.asociaciones_producto_proveedor: Dict[str, AsociacionProductoProveedor] = {}
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
        for datos in self.db.cargar("compras_recepciones"):
            try:
                recepcion = RecepcionCompra.from_dict(datos)
                self.recepciones_compra[recepcion.id] = recepcion
            except Exception:
                continue
        for datos in self.db.cargar("compras_incidencias"):
            try:
                incidencia = IncidenciaCompra.from_dict(datos)
                self.incidencias_compra[incidencia.id] = incidencia
            except Exception:
                continue
        for datos in self.db.cargar("compras_producto_proveedor"):
            try:
                asociacion = AsociacionProductoProveedor.from_dict(datos)
                self.asociaciones_producto_proveedor[asociacion.id] = asociacion
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
        self.db.guardar("compras_recepciones", [x.to_dict() for x in self.recepciones_compra.values()])
        self.db.guardar("compras_incidencias", [x.to_dict() for x in self.incidencias_compra.values()])
        self.db.guardar("compras_producto_proveedor", [x.to_dict() for x in self.asociaciones_producto_proveedor.values()])

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

    def crear_pedidos_borrador_transaccional(self, grupos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Crea borradores ya revisados con una sola persistencia, o ninguno."""
        preparados: List[PedidoSugerido] = []
        for grupo in grupos:
            proveedor = str(grupo.get("proveedor") or "").strip()
            if not proveedor:
                raise ValueError("Cada borrador necesita un proveedor.")
            lineas_raw = list(grupo.get("lineas") or [])
            if not lineas_raw:
                raise ValueError(f"El borrador de {proveedor} no puede estar vacío.")
            lineas: List[LineaPedido] = []
            for raw in lineas_raw:
                cantidad = float(raw.get("cantidad") or 0)
                if cantidad <= 0:
                    raise ValueError("Cada línea incluida necesita una cantidad mayor que cero.")
                nombre = str(raw.get("nombre") or "").strip()
                articulo_id = str(raw.get("articulo_id") or "").strip()
                if not nombre or not articulo_id:
                    raise ValueError("Cada línea incluida necesita un artículo relacionado.")
                lineas.append(LineaPedido(
                    nombre=nombre, cantidad=cantidad, unidad=str(raw.get("unidad") or "u"),
                    articulo_id=articulo_id, propuesta_id=str(raw.get("propuesta_id") or ""),
                    precio_unitario=float(raw.get("precio_unitario") or 0),
                    observaciones=str(raw.get("observaciones") or ""),
                ))
            preparados.append(PedidoSugerido(
                proveedor=proveedor, lineas=lineas, estado="borrador",
                observaciones=str(grupo.get("observaciones") or ""),
                origen_tipo=str(grupo.get("origen_tipo") or ""),
                origen_id=str(grupo.get("origen_id") or ""),
                origen_version=int(grupo.get("origen_version") or 0),
                propuesta_id=str(grupo.get("propuesta_id") or ""),
            ))

        anteriores = dict(self.pedidos_sugeridos)
        try:
            for pedido in preparados:
                self.pedidos_sugeridos[pedido.id] = pedido
            if self.db:
                self.db.guardar("compras_pedidos", [p.to_dict() for p in self.pedidos_sugeridos.values()])
        except Exception:
            self.pedidos_sugeridos = anteriores
            if self.db:
                self.db.guardar("compras_pedidos", [p.to_dict() for p in anteriores.values()])
            raise
        return [pedido.to_dict() for pedido in preparados]

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

    def actualizar_borrador_completo(self, pedido_id: str, datos: Dict[str, Any]) -> PedidoSugerido:
        """Reemplaza cabecera y lineas de un borrador con una unica persistencia."""
        pedido = self.pedidos_sugeridos.get(pedido_id)
        if not pedido:
            raise KeyError(f"Pedido no encontrado: {pedido_id}")
        if pedido.estado != "borrador":
            raise ValueError("Solo se pueden editar pedidos en estado borrador.")
        proveedor = str(datos.get("proveedor") or "").strip()
        if not proveedor:
            raise ValueError("El borrador necesita un proveedor.")
        nuevas_lineas: List[LineaPedido] = []
        for raw in list(datos.get("lineas") or []):
            nombre = str(raw.get("nombre") or "").strip()
            unidad = str(raw.get("unidad") or "").strip()
            cantidad = float(raw.get("cantidad") or 0)
            precio = float(raw.get("precio_unitario") or 0)
            if not nombre or not unidad:
                raise ValueError("Cada linea necesita nombre y unidad.")
            if cantidad <= 0:
                raise ValueError("La cantidad debe ser mayor que cero.")
            if precio < 0:
                raise ValueError("El precio unitario no puede ser negativo.")
            nuevas_lineas.append(LineaPedido.from_dict({**dict(raw), "nombre": nombre, "unidad": unidad, "cantidad": cantidad, "precio_unitario": precio}))
        anterior = PedidoSugerido.from_dict(pedido.to_dict())
        try:
            pedido.proveedor = proveedor
            pedido.observaciones = str(datos.get("observaciones") or "").strip()
            pedido.lineas = nuevas_lineas
            pedido.tocar("borrador_editado", "Borrador actualizado desde Compras.")
            if self.db:
                self.db.guardar("compras_pedidos", [p.to_dict() for p in self.pedidos_sugeridos.values()])
        except Exception:
            self.pedidos_sugeridos[pedido_id] = anterior
            raise
        return pedido

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
        if estado in {"preparado", "enviado"} and not pedido.confirmado_en:
            pedido.confirmado_en = datetime.now().isoformat(timespec="seconds")
        if estado == "enviado":
            pedido.enviado_en = datetime.now().isoformat(timespec="seconds")
        pedido.tocar("estado_cambiado", f"Pedido marcado como {estado}.")
        self._guardar()
        return pedido

    def confirmar_borrador_pedido(self, pedido_id: str, *, usuario: str, actualizado_en: str = "") -> tuple[PedidoSugerido, bool]:
        """Convierte el pedido-borrador canónico en preparado, sin enviarlo ni recibirlo."""
        pedido = self.pedidos_sugeridos.get(pedido_id)
        if not pedido:
            raise KeyError(f"Pedido no encontrado: {pedido_id}")
        if pedido.estado == "preparado" and pedido.borrador_origen_id == pedido.id:
            return pedido, True
        if pedido.estado != "borrador":
            raise ValueError(f"El pedido no se puede confirmar en estado {pedido.estado}.")
        if actualizado_en and actualizado_en != pedido.actualizado_en:
            raise RuntimeError("El borrador cambió desde la última revisión.")
        if not pedido.lineas:
            raise ValueError("No se puede confirmar un borrador sin líneas.")

        anterior = PedidoSugerido.from_dict(pedido.to_dict())
        try:
            pedido.estado = "preparado"
            pedido.confirmado_en = datetime.now().isoformat(timespec="seconds")
            pedido.confirmado_por = str(usuario or "").strip()
            pedido.borrador_origen_id = pedido.id
            pedido.tocar(
                "pedido_confirmado",
                f"Borrador {pedido.id} confirmado por {pedido.confirmado_por}; {len(pedido.lineas)} líneas; proveedor {pedido.proveedor}; total {pedido.importe_estimado():.2f}.",
            )
            if self.db:
                self.db.guardar("compras_pedidos", [p.to_dict() for p in self.pedidos_sugeridos.values()])
        except Exception:
            self.pedidos_sugeridos[pedido_id] = anterior
            raise
        return pedido, False

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
        incidencias = []
        for linea in pedido.lineas:
            coste = float(costes.get(linea.id, linea.precio_unitario or 0))
            if linea.cantidad <= 0:
                incidencia = IncidenciaCompra(
                    pedido_id=pedido.id,
                    recepcion_id="",
                    tipo="cantidad_invalida",
                    descripcion=f"La línea {linea.nombre} tiene una cantidad no válida.",
                    severidad="alta",
                    linea_id=linea.id,
                    proveedor=pedido.proveedor,
                )
                self.incidencias_compra[incidencia.id] = incidencia
                incidencias.append(incidencia.to_dict())
                continue
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
        recepcion = RecepcionCompra(
            pedido_id=pedido.id,
            proveedor=pedido.proveedor,
            estado="completa" if not incidencias else "parcial",
            lineas=entradas,
            incidencias=incidencias,
            observaciones=f"Recepción registrada para pedido {pedido.id}.",
            trazabilidad={"ubicacion": ubicacion, "total_lineas": len(pedido.lineas), "lineas_recibidas": len(entradas)},
            stock_aplicado=True,
            stock_aplicado_en=datetime.now().isoformat(timespec="seconds"),
            confirmado_en=pedido.recibido_en,
        )
        for incidencia in incidencias:
            incidencia["recepcion_id"] = recepcion.id
            incidencia_obj = self.incidencias_compra.get(incidencia.get("id", ""))
            if incidencia_obj:
                incidencia_obj.recepcion_id = recepcion.id
                incidencia_obj.tocar()
        self.recepciones_compra[recepcion.id] = recepcion
        pedido.recepciones.append({"id": recepcion.id, "creado_en": recepcion.creado_en, "estado": recepcion.estado, "lineas": len(entradas)})
        pedido.incidencias.extend(incidencias)
        self._guardar()
        return {
            "pedido": pedido.to_dict(),
            "recepcion": recepcion.to_dict(),
            "entradas_stock": entradas,
            "incidencias": incidencias,
            "total_lineas": len(entradas),
            "lectura_host_ai": f"Pedido {pedido.id} recibido. Se actualizaron {len(entradas)} líneas de stock.",
        }

    def registrar_incidencia_compra(self, pedido_id: str, recepcion_id: str, tipo: str, descripcion: str, severidad: str = "media", linea_id: str = "", proveedor: str = "", solucion: str = "") -> IncidenciaCompra:
        incidencia = IncidenciaCompra(
            pedido_id=pedido_id,
            recepcion_id=recepcion_id,
            tipo=tipo,
            descripcion=descripcion,
            severidad=severidad,
            linea_id=linea_id,
            proveedor=proveedor,
            solucion=solucion,
        )
        self.incidencias_compra[incidencia.id] = incidencia
        pedido = self.pedidos_sugeridos.get(str(pedido_id or ""))
        if pedido:
            pedido.incidencias.append(incidencia.to_dict())
            pedido.tocar("incidencia_registrada", incidencia.descripcion)
        self._guardar()
        return incidencia

    def listar_recepciones(self, pedido_id: str = "") -> List[Dict[str, Any]]:
        pedido_id = str(pedido_id or "").strip()
        recepciones = list(self.recepciones_compra.values())
        if pedido_id:
            recepciones = [r for r in recepciones if r.pedido_id == pedido_id]
        recepciones.sort(key=lambda r: (r.creado_en, r.id), reverse=True)
        return [r.to_dict() for r in recepciones]

    def listar_incidencias(self, pedido_id: str = "", recepcion_id: str = "") -> List[Dict[str, Any]]:
        pedido_id = str(pedido_id or "").strip()
        recepcion_id = str(recepcion_id or "").strip()
        incidencias = list(self.incidencias_compra.values())
        if pedido_id:
            incidencias = [i for i in incidencias if i.pedido_id == pedido_id]
        if recepcion_id:
            incidencias = [i for i in incidencias if i.recepcion_id == recepcion_id]
        incidencias.sort(key=lambda i: (i.creado_en, i.id), reverse=True)
        return [i.to_dict() for i in incidencias]

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
    def _float_no_negativo(valor: Any, campo: str, permitir_none: bool = True) -> Optional[float]:
        if valor in (None, ""):
            return None if permitir_none else 0.0
        numero = float(valor)
        if numero < 0:
            raise ValueError(f"{campo} no puede ser negativo")
        return numero

    @staticmethod
    def _int_no_negativo(valor: Any, campo: str, permitir_none: bool = True) -> Optional[int]:
        if valor in (None, ""):
            return None if permitir_none else 0
        numero = int(valor)
        if numero < 0:
            raise ValueError(f"{campo} no puede ser negativo")
        return numero

    @staticmethod
    def _parse_fecha_iso(valor: str) -> Optional[datetime]:
        txt = str(valor or "").strip()
        if not txt:
            return None
        for candidato in (txt, txt[:10]):
            try:
                if len(candidato) == 10:
                    return datetime.strptime(candidato, "%Y-%m-%d")
                return datetime.fromisoformat(candidato)
            except ValueError:
                continue
        return None

    @classmethod
    def _unidad_compatible(cls, unidad_a: str, unidad_b: str) -> bool:
        return cls._normalizar_texto(unidad_a) == cls._normalizar_texto(unidad_b)

    @classmethod
    def normalizar_producto(cls, nombre: str) -> str:
        texto = str(nombre or "").strip().lower()
        texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
        texto = texto.replace("-", " ")
        return " ".join(texto.split())

    def _proveedor_activo(self, proveedor_id: str = "", proveedor_nombre: str = "") -> Optional[ProveedorCompra]:
        pid = str(proveedor_id or "").strip()
        if pid and pid in self.proveedores and self.proveedores[pid].estado == "activo":
            return self.proveedores[pid]
        nombre_norm = self._normalizar_texto(proveedor_nombre)
        if not nombre_norm:
            return None
        for prov in self.proveedores.values():
            if prov.estado != "activo":
                continue
            if self._normalizar_texto(prov.nombre) == nombre_norm:
                return prov
        return None

    def _buscar_asociacion_activa(self, producto_normalizado: str, proveedor_id: str) -> Optional[AsociacionProductoProveedor]:
        for aso in self.asociaciones_producto_proveedor.values():
            if not aso.activo:
                continue
            if aso.producto_normalizado == producto_normalizado and aso.proveedor_id == proveedor_id:
                return aso
        return None

    def listar_proveedores_producto(self, producto: str, solo_activos: bool = True) -> List[Dict[str, Any]]:
        producto_norm = self.normalizar_producto(producto)
        salida = []
        for aso in self.asociaciones_producto_proveedor.values():
            if aso.producto_normalizado != producto_norm:
                continue
            if solo_activos and not aso.activo:
                continue
            proveedor = self._proveedor_activo(aso.proveedor_id, aso.proveedor_nombre)
            if not proveedor:
                continue
            datos = aso.to_dict()
            datos["proveedor_nombre"] = proveedor.nombre
            salida.append(datos)
        salida.sort(key=lambda x: (0 if x.get("preferente") else 1, -int(x.get("veces_usado", 0)), x.get("proveedor_nombre", "").lower(), x.get("proveedor_id", "")))
        return salida

    def listar_productos_habituales_proveedor(self, proveedor_id: str) -> List[Dict[str, Any]]:
        pid = str(proveedor_id or "").strip()
        salida = []
        for aso in self.asociaciones_producto_proveedor.values():
            if aso.proveedor_id != pid:
                continue
            salida.append(aso.to_dict())
        salida.sort(key=lambda x: (x.get("producto_normalizado", ""), -int(x.get("veces_usado", 0))))
        return salida

    def asociar_producto_proveedor_detallado(
        self,
        producto: str,
        proveedor_id: str,
        preferente: bool = False,
        activo: bool = True,
        precio_habitual: Any = None,
        unidad_precio: str = "",
        cantidad_minima_producto: Any = None,
        plazo_entrega_dias: Any = None,
        observaciones: str = "",
    ) -> AsociacionProductoProveedor:
        producto_txt = str(producto or "").strip()
        if not producto_txt:
            raise ValueError("El producto es obligatorio")
        pid = str(proveedor_id or "").strip()
        proveedor = self.proveedores.get(pid)
        if not proveedor:
            raise ValueError("El proveedor no existe")
        if proveedor.estado != "activo":
            raise ValueError("No se puede asociar un proveedor inactivo")

        producto_norm = self.normalizar_producto(producto_txt)
        existente = self._buscar_asociacion_activa(producto_norm, pid)
        if existente:
            existente.producto = producto_txt
            existente.proveedor_nombre = proveedor.nombre
            existente.activo = bool(activo)
            if precio_habitual is not None:
                existente.precio_habitual = self._float_no_negativo(precio_habitual, "precio_habitual", permitir_none=True)
                existente.ultima_actualizacion_precio = datetime.now().isoformat(timespec="seconds")
            if unidad_precio is not None:
                existente.unidad_precio = str(unidad_precio or "").strip()
            if cantidad_minima_producto is not None:
                existente.cantidad_minima_producto = self._float_no_negativo(cantidad_minima_producto, "cantidad_minima_producto", permitir_none=True)
            if plazo_entrega_dias is not None:
                existente.plazo_entrega_dias = self._int_no_negativo(plazo_entrega_dias, "plazo_entrega_dias", permitir_none=True)
            if observaciones is not None:
                existente.observaciones = str(observaciones or "").strip()
            if preferente:
                self._desmarcar_preferente_producto(producto_norm)
                existente.preferente = True
            existente.tocar()
            self._guardar()
            return existente

        asociacion = AsociacionProductoProveedor(
            producto=producto_txt,
            producto_normalizado=producto_norm,
            proveedor_id=pid,
            proveedor_nombre=proveedor.nombre,
            preferente=bool(preferente),
            activo=bool(activo),
            precio_habitual=self._float_no_negativo(precio_habitual, "precio_habitual", permitir_none=True),
            unidad_precio=str(unidad_precio or "").strip(),
            cantidad_minima_producto=self._float_no_negativo(cantidad_minima_producto, "cantidad_minima_producto", permitir_none=True),
            plazo_entrega_dias=self._int_no_negativo(plazo_entrega_dias, "plazo_entrega_dias", permitir_none=True),
            observaciones=str(observaciones or "").strip(),
        )
        if asociacion.precio_habitual is not None:
            asociacion.ultima_actualizacion_precio = datetime.now().isoformat(timespec="seconds")
        if asociacion.preferente:
            self._desmarcar_preferente_producto(producto_norm)
        self.asociaciones_producto_proveedor[asociacion.id] = asociacion
        self._guardar()
        return asociacion

    def _desmarcar_preferente_producto(self, producto_normalizado: str) -> None:
        for aso in self.asociaciones_producto_proveedor.values():
            if aso.producto_normalizado != producto_normalizado:
                continue
            if aso.preferente:
                aso.preferente = False
                aso.tocar()

    def marcar_proveedor_preferente_producto(self, producto: str, proveedor_id: str) -> AsociacionProductoProveedor:
        producto_norm = self.normalizar_producto(producto)
        asociacion = self._buscar_asociacion_activa(producto_norm, str(proveedor_id or "").strip())
        if not asociacion:
            asociacion = self.asociar_producto_proveedor_detallado(producto, proveedor_id, preferente=True, activo=True)
            return asociacion
        proveedor = self._proveedor_activo(asociacion.proveedor_id, asociacion.proveedor_nombre)
        if not proveedor:
            raise ValueError("No se puede marcar como preferente un proveedor inactivo")
        self._desmarcar_preferente_producto(producto_norm)
        asociacion.preferente = True
        asociacion.tocar()
        self._guardar()
        return asociacion

    def desactivar_asociacion_producto_proveedor(self, asociacion_id: str) -> AsociacionProductoProveedor:
        aso = self.asociaciones_producto_proveedor.get(str(asociacion_id or ""))
        if not aso:
            raise KeyError(f"Asociación no encontrada: {asociacion_id}")
        aso.activo = False
        aso.preferente = False
        aso.tocar()
        self._guardar()
        return aso

    def editar_asociacion_producto_proveedor(
        self,
        asociacion_id: str,
        preferente: Optional[bool] = None,
        activo: Optional[bool] = None,
        precio_habitual: Any = None,
        unidad_precio: Optional[str] = None,
        cantidad_minima_producto: Any = None,
        plazo_entrega_dias: Any = None,
        observaciones: Optional[str] = None,
    ) -> AsociacionProductoProveedor:
        aso = self.asociaciones_producto_proveedor.get(str(asociacion_id or ""))
        if not aso:
            raise KeyError(f"Asociación no encontrada: {asociacion_id}")
        if activo is not None:
            aso.activo = bool(activo)
            if not aso.activo:
                aso.preferente = False
        if preferente is not None:
            if bool(preferente):
                prov = self._proveedor_activo(aso.proveedor_id, aso.proveedor_nombre)
                if not prov:
                    raise ValueError("No se puede marcar preferente con proveedor inactivo")
                self._desmarcar_preferente_producto(aso.producto_normalizado)
                aso.preferente = True
                aso.activo = True
            else:
                aso.preferente = False
        if precio_habitual is not None:
            aso.precio_habitual = self._float_no_negativo(precio_habitual, "precio_habitual", permitir_none=True)
            aso.ultima_actualizacion_precio = datetime.now().isoformat(timespec="seconds") if aso.precio_habitual is not None else aso.ultima_actualizacion_precio
        if unidad_precio is not None:
            aso.unidad_precio = str(unidad_precio or "").strip()
        if cantidad_minima_producto is not None:
            aso.cantidad_minima_producto = self._float_no_negativo(cantidad_minima_producto, "cantidad_minima_producto", permitir_none=True)
        if plazo_entrega_dias is not None:
            aso.plazo_entrega_dias = self._int_no_negativo(plazo_entrega_dias, "plazo_entrega_dias", permitir_none=True)
        if observaciones is not None:
            aso.observaciones = str(observaciones or "").strip()
        aso.tocar()
        self._guardar()
        return aso

    def editar_condiciones_proveedor(
        self,
        proveedor_id: str,
        pedido_minimo_importe: Any = None,
        portes: Any = None,
        portes_gratis_desde: Any = None,
        plazo_entrega_general_dias: Any = None,
        dias_reparto: Optional[List[str]] = None,
        observaciones_comerciales: Optional[str] = None,
    ) -> ProveedorCompra:
        prov = self.proveedores.get(str(proveedor_id or "").strip())
        if not prov:
            raise KeyError(f"Proveedor no encontrado: {proveedor_id}")
        if pedido_minimo_importe is not None:
            prov.pedido_minimo_importe = self._float_no_negativo(pedido_minimo_importe, "pedido_minimo_importe", permitir_none=True)
        if portes is not None:
            prov.portes = self._float_no_negativo(portes, "portes", permitir_none=True)
        if portes_gratis_desde is not None:
            prov.portes_gratis_desde = self._float_no_negativo(portes_gratis_desde, "portes_gratis_desde", permitir_none=True)
        if plazo_entrega_general_dias is not None:
            prov.plazo_entrega_general_dias = self._int_no_negativo(plazo_entrega_general_dias, "plazo_entrega_general_dias", permitir_none=True)
        if dias_reparto is not None:
            prov.dias_reparto = [str(x or "").strip() for x in list(dias_reparto or []) if str(x or "").strip()]
        if observaciones_comerciales is not None:
            prov.observaciones_comerciales = str(observaciones_comerciales or "").strip()
        prov.tocar()
        self._guardar()
        return prov

    @staticmethod
    def _timestamp_sort(fecha: str) -> str:
        return str(fecha or "")

    def _calcular_portes(self, proveedor: ProveedorCompra, subtotal: Optional[float]) -> Optional[float]:
        if subtotal is None:
            if proveedor.portes in (None, ""):
                return None
            if proveedor.portes_gratis_desde in (None, ""):
                return float(proveedor.portes or 0)
            return float(proveedor.portes or 0)
        if proveedor.portes_gratis_desde not in (None, "") and subtotal >= float(proveedor.portes_gratis_desde or 0):
            return 0.0
        if proveedor.portes in (None, ""):
            return None
        return float(proveedor.portes or 0)

    def _coste_producto_estimado(self, cantidad: float, unidad: str, asociacion: AsociacionProductoProveedor) -> Optional[float]:
        if asociacion.precio_habitual is None:
            return None
        if not self._unidad_compatible(unidad, asociacion.unidad_precio or unidad):
            return None
        return round(float(cantidad or 0) * float(asociacion.precio_habitual), 4)

    def _dias_entrega(self, proveedor: ProveedorCompra, asociacion: AsociacionProductoProveedor) -> Optional[int]:
        if asociacion.plazo_entrega_dias is not None:
            return int(asociacion.plazo_entrega_dias)
        if proveedor.plazo_entrega_general_dias is not None:
            return int(proveedor.plazo_entrega_general_dias)
        return None

    def _cumple_plazo(self, dias_entrega: Optional[int], fecha_necesaria: str) -> Optional[bool]:
        requerida = self._parse_fecha_iso(fecha_necesaria)
        if not requerida:
            return None
        if dias_entrega is None:
            return False
        entrega = datetime.now() + timedelta(days=int(dias_entrega))
        return entrega.date() <= requerida.date()

    def evaluar_proveedores_producto(
        self,
        producto: str,
        cantidad: float,
        unidad: str,
        prioridad: str = "Normal",
        fecha_necesaria: str = "",
        proveedor_sugerido: str = "",
        familia: str = "",
        contexto_subtotales: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        producto_norm = self.normalizar_producto(producto)
        contexto_subtotales = dict(contexto_subtotales or {})
        candidatos: List[Dict[str, Any]] = []

        asociaciones = [
            aso for aso in self.asociaciones_producto_proveedor.values()
            if aso.producto_normalizado == producto_norm
        ]

        for aso in asociaciones:
            proveedor = self.proveedores.get(aso.proveedor_id)
            if not proveedor:
                continue
            if proveedor.estado != "activo":
                continue
            if not aso.activo:
                continue

            coste_producto = self._coste_producto_estimado(float(cantidad or 0), unidad, aso)
            subtotal_contexto = contexto_subtotales.get(proveedor.id, 0.0)
            subtotal_efectivo = None if coste_producto is None else round(subtotal_contexto + coste_producto, 4)
            portes = self._calcular_portes(proveedor, subtotal_efectivo)
            total = None if subtotal_efectivo is None else round(subtotal_efectivo + float(portes or 0), 4)

            cumple_min_producto = True
            if aso.cantidad_minima_producto is not None:
                cumple_min_producto = float(cantidad or 0) >= float(aso.cantidad_minima_producto)

            cumple_min_pedido = True
            faltante_min_pedido = 0.0
            if proveedor.pedido_minimo_importe is not None:
                if subtotal_efectivo is None:
                    cumple_min_pedido = False
                else:
                    cumple_min_pedido = subtotal_efectivo >= float(proveedor.pedido_minimo_importe)
                    faltante_min_pedido = round(max(0.0, float(proveedor.pedido_minimo_importe) - subtotal_efectivo), 4)

            dias_entrega = self._dias_entrega(proveedor, aso)
            cumple_plazo = self._cumple_plazo(dias_entrega, fecha_necesaria)

            datos_incompletos = []
            if aso.precio_habitual is None:
                datos_incompletos.append("precio")
            if dias_entrega is None:
                datos_incompletos.append("plazo")

            candidatos.append(
                {
                    "proveedor_id": proveedor.id,
                    "proveedor_nombre": proveedor.nombre,
                    "asociacion_id": aso.id,
                    "preferente": bool(aso.preferente),
                    "veces_usado": int(aso.veces_usado or 0),
                    "numero_compras": int(aso.numero_compras or aso.veces_usado or 0),
                    "ultima_compra_en": aso.ultima_compra_en or aso.ultima_compra,
                    "coste_producto_estimado": coste_producto,
                    "portes_estimados": portes,
                    "coste_total_estimado": total,
                    "cumple_cantidad_minima_producto": bool(cumple_min_producto),
                    "cumple_pedido_minimo": bool(cumple_min_pedido),
                    "faltante_pedido_minimo": faltante_min_pedido,
                    "cumple_plazo": cumple_plazo,
                    "dias_entrega_estimados": dias_entrega,
                    "elegible": True,
                    "ventajas": [],
                    "advertencias": [],
                    "motivos_descarte": [],
                    "datos_incompletos": datos_incompletos,
                    "puntuacion": 0,
                }
            )

        if not candidatos and proveedor_sugerido:
            prov = self._proveedor_activo("", proveedor_sugerido)
            if prov:
                candidatos.append(
                    {
                        "proveedor_id": prov.id,
                        "proveedor_nombre": prov.nombre,
                        "asociacion_id": "",
                        "preferente": False,
                        "veces_usado": 0,
                        "numero_compras": 0,
                        "ultima_compra_en": "",
                        "coste_producto_estimado": None,
                        "portes_estimados": self._calcular_portes(prov, None),
                        "coste_total_estimado": None,
                        "cumple_cantidad_minima_producto": True,
                        "cumple_pedido_minimo": prov.pedido_minimo_importe in (None, ""),
                        "faltante_pedido_minimo": 0.0,
                        "cumple_plazo": self._cumple_plazo(prov.plazo_entrega_general_dias, fecha_necesaria),
                        "dias_entrega_estimados": prov.plazo_entrega_general_dias,
                        "elegible": True,
                        "ventajas": ["Sugerido por la necesidad."],
                        "advertencias": ["Sin información suficiente de precio."],
                        "motivos_descarte": [],
                        "datos_incompletos": ["precio"],
                        "puntuacion": 0,
                    }
                )

        costos_conocidos = [c for c in candidatos if c.get("coste_total_estimado") is not None]
        min_coste = min((c["coste_total_estimado"] for c in costos_conocidos), default=None)
        max_usos = max((int(c.get("veces_usado", 0)) for c in candidatos), default=0)

        for c in candidatos:
            score = 0
            if c["preferente"]:
                score += 30
                c["ventajas"].append("Proveedor preferente del producto.")
            if c["cumple_plazo"] is True:
                score += 20
                c["ventajas"].append("Cumple el plazo requerido.")
            elif c["cumple_plazo"] is False:
                score -= 40
                c["advertencias"].append("No cumple el plazo requerido.")
            else:
                c["advertencias"].append("Plazo de entrega desconocido.")
            if min_coste is not None and c.get("coste_total_estimado") is not None and abs(c["coste_total_estimado"] - min_coste) <= 0.0001:
                score += 15
                c["ventajas"].append("Mejor precio conocido.")
            if c["cumple_pedido_minimo"]:
                score += 10
                c["ventajas"].append("Pedido mínimo alcanzado.")
            else:
                score -= 20
                c["advertencias"].append(
                    "No se alcanza el pedido mínimo." + (f" Faltan {c.get('faltante_pedido_minimo', 0):.2f} €." if c.get("faltante_pedido_minimo", 0) > 0 else "")
                )
            if c.get("veces_usado", 0) > 0:
                score += 8
                c["ventajas"].append("Proveedor habitual del producto.")
            if max_usos > 0 and int(c.get("veces_usado", 0)) == max_usos:
                score += 5
                c["ventajas"].append("Proveedor más utilizado para el producto.")
            if c.get("portes_estimados") == 0:
                score += 3
                c["ventajas"].append("Sin portes.")
            if not c["cumple_cantidad_minima_producto"]:
                score -= 10
                c["advertencias"].append("Cantidad mínima del producto no alcanzada.")
            if c.get("datos_incompletos"):
                score -= 5
                if "precio" in c["datos_incompletos"]:
                    c["advertencias"].append("Sin información suficiente de precio.")

            c["puntuacion"] = int(score)

        candidatos.sort(
            key=lambda x: (
                int(x.get("puntuacion", 0)),
                1 if x.get("cumple_plazo") is True else 0,
                -float(x.get("coste_total_estimado") if x.get("coste_total_estimado") is not None else 10**12),
                1 if x.get("preferente") else 0,
                int(x.get("numero_compras", 0)),
                self._normalizar_texto(x.get("proveedor_nombre", "")),
                x.get("proveedor_id", ""),
            ),
            reverse=True,
        )
        return candidatos

    def recomendar_proveedor(self, producto: str, proveedor_sugerido: str = "", familia: str = "") -> Dict[str, Any]:
        evaluados = self.evaluar_proveedores_producto(
            producto=producto,
            cantidad=1,
            unidad="u",
            prioridad="Normal",
            fecha_necesaria="",
            proveedor_sugerido=proveedor_sugerido,
            familia=familia,
        )
        if not evaluados:
            return {
                "proveedor_id": "",
                "proveedor_nombre": "",
                "motivo": "Sin historial suficiente.",
                "fuente": "sin_recomendacion",
                "puntuacion": 0,
                "advertencias": ["Sin proveedores disponibles."],
            }
        mejor = evaluados[0]
        motivo = mejor["ventajas"][0] if mejor.get("ventajas") else "Sin historial suficiente."
        fuente = "evaluacion_r43"
        if mejor.get("preferente"):
            fuente = "preferente"
        elif mejor.get("veces_usado", 0):
            fuente = "frecuencia"
        elif proveedor_sugerido and self._normalizar_texto(mejor.get("proveedor_nombre", "")) == self._normalizar_texto(proveedor_sugerido):
            fuente = "sugerido_necesidad"
        return {
            "proveedor_id": mejor.get("proveedor_id", ""),
            "proveedor_nombre": mejor.get("proveedor_nombre", ""),
            "motivo": motivo,
            "fuente": fuente,
            "puntuacion": mejor.get("puntuacion", 0),
            "advertencias": list(mejor.get("advertencias", [])),
            "comparativa": evaluados,
        }

    def registrar_uso_proveedor(self, producto: str, proveedor: str = "", proveedor_id: str = "", fecha: str = "") -> Optional[AsociacionProductoProveedor]:
        prov = self._proveedor_activo(proveedor_id, proveedor)
        if not prov:
            return None
        producto_txt = str(producto or "").strip()
        if not producto_txt:
            return None
        producto_norm = self.normalizar_producto(producto_txt)
        asociacion = self._buscar_asociacion_activa(producto_norm, prov.id)
        if not asociacion:
            asociacion = AsociacionProductoProveedor(
                producto=producto_txt,
                producto_normalizado=producto_norm,
                proveedor_id=prov.id,
                proveedor_nombre=prov.nombre,
                preferente=False,
                activo=True,
            )
            self.asociaciones_producto_proveedor[asociacion.id] = asociacion
        asociacion.producto = producto_txt
        asociacion.proveedor_nombre = prov.nombre
        asociacion.activo = True
        asociacion.incrementar_uso(fecha)
        prod_norm = self.normalizar_producto(producto_txt)
        prod_set = {self.normalizar_producto(x) for x in list(prov.productos_habituales or [])}
        if prod_norm not in prod_set:
            prov.productos_habituales.append(producto_txt)
            prov.tocar()
        self._guardar()
        return asociacion

    def recomendar_proveedor_para_propuesta(self, propuesta_id: str) -> Dict[str, Any]:
        propuesta = self.propuestas_compra.get(str(propuesta_id or ""))
        if not propuesta:
            raise KeyError(f"Propuesta no encontrada: {propuesta_id}")
        evaluados = self.evaluar_proveedores_producto(
            producto=propuesta.producto,
            cantidad=propuesta.comprar,
            unidad=propuesta.unidad,
            prioridad=propuesta.prioridad,
            fecha_necesaria="",
            proveedor_sugerido=propuesta.proveedor_sugerido,
            familia="",
        )
        if evaluados:
            mejor = evaluados[0]
            proveedor_nombre = mejor.get("proveedor_nombre", "")
            motivo = mejor["ventajas"][0] if mejor.get("ventajas") else "Sin historial suficiente."
        else:
            proveedor_nombre = ""
            motivo = "Sin historial suficiente."
        return {
            "propuesta_id": propuesta.id,
            "producto": propuesta.producto,
            "proveedor_recomendado": proveedor_nombre or "Sin recomendación",
            "motivo": motivo,
            "fuente": "evaluacion_r43" if evaluados else "sin_recomendacion",
            "comparativa": evaluados,
        }

    def agrupar_propuestas_por_proveedor_recomendado(self) -> Dict[str, Any]:
        propuestas_pendientes = [p for p in self.propuestas_compra.values() if p.estado == "pendiente"]
        recomendadas_base: Dict[str, Dict[str, Any]] = {}
        for propuesta in propuestas_pendientes:
            evaluados = self.evaluar_proveedores_producto(
                producto=propuesta.producto,
                cantidad=propuesta.comprar,
                unidad=propuesta.unidad,
                prioridad=propuesta.prioridad,
                fecha_necesaria="",
                proveedor_sugerido=propuesta.proveedor_sugerido,
            )
            recomendadas_base[propuesta.id] = evaluados[0] if evaluados else {
                "proveedor_id": "",
                "proveedor_nombre": "",
                "coste_producto_estimado": None,
                "portes_estimados": None,
                "coste_total_estimado": None,
                "cumple_pedido_minimo": False,
                "cumple_plazo": None,
                "dias_entrega_estimados": None,
                "advertencias": ["Sin proveedores disponibles."],
                "ventajas": [],
                "puntuacion": 0,
                "faltante_pedido_minimo": 0.0,
            }

        subtotales_base: Dict[str, float] = {}
        for propuesta in propuestas_pendientes:
            rec = recomendadas_base.get(propuesta.id, {})
            pid = rec.get("proveedor_id", "")
            subtotal = rec.get("coste_producto_estimado")
            if pid and subtotal is not None:
                subtotales_base[pid] = round(subtotales_base.get(pid, 0.0) + float(subtotal), 4)

        grupos: Dict[str, Dict[str, Any]] = {}
        for propuesta in self.propuestas_compra.values():
            if propuesta.estado != "pendiente":
                continue
            evaluados = self.evaluar_proveedores_producto(
                producto=propuesta.producto,
                cantidad=propuesta.comprar,
                unidad=propuesta.unidad,
                prioridad=propuesta.prioridad,
                fecha_necesaria="",
                proveedor_sugerido=propuesta.proveedor_sugerido,
                contexto_subtotales=subtotales_base,
            )
            mejor = evaluados[0] if evaluados else recomendadas_base.get(propuesta.id, {})
            base = recomendadas_base.get(propuesta.id, {})
            ajustada = bool(base.get("proveedor_id")) and base.get("proveedor_id") != mejor.get("proveedor_id")
            proveedor_nombre = mejor.get("proveedor_nombre") or "Sin proveedor recomendado"

            grupo = grupos.setdefault(
                proveedor_nombre,
                {
                    "proveedor": proveedor_nombre,
                    "proveedor_id": mejor.get("proveedor_id", ""),
                    "propuestas": [],
                    "subtotal_estimado": 0.0,
                    "portes_estimados": None,
                    "total_estimado": None,
                    "pedido_minimo": None,
                    "pedido_minimo_alcanzado": None,
                    "faltante_pedido_minimo": 0.0,
                    "plazo_entrega_estimado_dias": None,
                    "advertencias": [],
                },
            )
            grupo["propuestas"].append(
                {
                    "id": propuesta.id,
                    "producto": propuesta.producto,
                    "cantidad": propuesta.comprar,
                    "unidad": propuesta.unidad,
                    "prioridad": propuesta.prioridad,
                    "coste_producto_estimado": mejor.get("coste_producto_estimado"),
                    "dias_entrega_estimados": mejor.get("dias_entrega_estimados"),
                    "motivo_recomendacion": (mejor.get("ventajas") or ["Sin historial suficiente."])[0],
                    "advertencias": list(mejor.get("advertencias", [])),
                    "recomendacion_ajustada_por_consolidacion": ajustada,
                }
            )

        salida = []
        for _, grupo in sorted(grupos.items(), key=lambda x: x[0].lower()):
            grupo["propuestas"].sort(key=lambda x: (x["producto"].lower(), x["id"]))
            subtotal = sum(float(x.get("coste_producto_estimado") or 0) for x in grupo["propuestas"] if x.get("coste_producto_estimado") is not None)
            hay_coste = any(x.get("coste_producto_estimado") is not None for x in grupo["propuestas"])
            grupo["subtotal_estimado"] = round(subtotal, 4) if hay_coste else None
            prov = self.proveedores.get(str(grupo.get("proveedor_id") or "")) if grupo.get("proveedor_id") else None
            if prov:
                grupo["pedido_minimo"] = prov.pedido_minimo_importe
                portes = self._calcular_portes(prov, grupo["subtotal_estimado"])
                grupo["portes_estimados"] = portes
                if grupo["subtotal_estimado"] is None:
                    grupo["total_estimado"] = None
                    if prov.pedido_minimo_importe is not None:
                        grupo["pedido_minimo_alcanzado"] = False
                        grupo["advertencias"].append("Pedido mínimo no evaluable por coste desconocido.")
                else:
                    grupo["total_estimado"] = round(float(grupo["subtotal_estimado"] or 0) + float(portes or 0), 4)
                    if prov.pedido_minimo_importe is not None:
                        cumple = float(grupo["subtotal_estimado"]) >= float(prov.pedido_minimo_importe)
                        grupo["pedido_minimo_alcanzado"] = cumple
                        grupo["faltante_pedido_minimo"] = round(max(0.0, float(prov.pedido_minimo_importe) - float(grupo["subtotal_estimado"])), 4)
                        if not cumple:
                            grupo["advertencias"].append(f"Faltan {grupo['faltante_pedido_minimo']:.2f} € para el pedido mínimo.")
                plazos = [int(x["dias_entrega_estimados"]) for x in grupo["propuestas"] if x.get("dias_entrega_estimados") is not None]
                grupo["plazo_entrega_estimado_dias"] = max(plazos) if plazos else prov.plazo_entrega_general_dias
                if grupo["portes_estimados"] is None:
                    grupo["advertencias"].append("Portes desconocidos para este proveedor.")
            for item in grupo["propuestas"]:
                for aviso in item.get("advertencias", []):
                    if aviso not in grupo["advertencias"]:
                        grupo["advertencias"].append(aviso)
            salida.append(grupo)
        return {
            "grupos": salida,
            "total_grupos": len(salida),
            "total_propuestas": sum(len(x["propuestas"]) for x in salida),
        }

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
        if "pedido_minimo_importe" in cambios and cambios["pedido_minimo_importe"] is not None:
            prov.pedido_minimo_importe = self._float_no_negativo(cambios["pedido_minimo_importe"], "pedido_minimo_importe", permitir_none=True)
        if "portes" in cambios and cambios["portes"] is not None:
            prov.portes = self._float_no_negativo(cambios["portes"], "portes", permitir_none=True)
        if "portes_gratis_desde" in cambios and cambios["portes_gratis_desde"] is not None:
            prov.portes_gratis_desde = self._float_no_negativo(cambios["portes_gratis_desde"], "portes_gratis_desde", permitir_none=True)
        if "plazo_entrega_general_dias" in cambios and cambios["plazo_entrega_general_dias"] is not None:
            prov.plazo_entrega_general_dias = self._int_no_negativo(cambios["plazo_entrega_general_dias"], "plazo_entrega_general_dias", permitir_none=True)
        if "dias_reparto" in cambios and cambios["dias_reparto"] is not None:
            prov.dias_reparto = [str(x or "").strip() for x in list(cambios["dias_reparto"] or []) if str(x or "").strip()]
        if "observaciones_comerciales" in cambios and cambios["observaciones_comerciales"] is not None:
            prov.observaciones_comerciales = str(cambios["observaciones_comerciales"] or "").strip()
        prov.tocar()
        self._guardar()
        return prov

    def desactivar_proveedor(self, proveedor_id: str) -> ProveedorCompra:
        prov = self.proveedores.get(str(proveedor_id or ""))
        if not prov:
            raise KeyError(f"Proveedor no encontrado: {proveedor_id}")
        prov.estado = "inactivo"
        prov.tocar()
        for aso in self.asociaciones_producto_proveedor.values():
            if aso.proveedor_id != prov.id:
                continue
            aso.activo = False
            aso.preferente = False
            aso.tocar()
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
        self.asociar_producto_proveedor_detallado(nombre_producto, prov.id, preferente=False, activo=True)
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
        self.registrar_uso_proveedor(producto=compra.producto, proveedor=compra.proveedor, fecha=compra.creado_en)
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
        salida = []
        for p in propuestas:
            evaluados = self.evaluar_proveedores_producto(
                producto=p.producto,
                cantidad=p.comprar,
                unidad=p.unidad,
                prioridad=p.prioridad,
                fecha_necesaria="",
                proveedor_sugerido=p.proveedor_sugerido,
            )
            datos = p.to_dict()
            if evaluados:
                mejor = evaluados[0]
                datos["proveedor_sugerido"] = mejor.get("proveedor_nombre", "")
                datos["motivo_proveedor_sugerido"] = (mejor.get("ventajas") or ["Sin historial suficiente."])[0]
            else:
                datos["proveedor_sugerido"] = ""
                datos["motivo_proveedor_sugerido"] = "Sin historial suficiente."
            salida.append(datos)
        return salida

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
            evaluados = self.evaluar_proveedores_producto(
                producto=item["producto"],
                cantidad=comprar,
                unidad=item["unidad"],
                prioridad=prioridad,
                fecha_necesaria="",
                proveedor_sugerido=item["proveedor_sugerido"],
                familia="",
            )
            mejor = evaluados[0] if evaluados else {}
            proveedor_recomendado = mejor.get("proveedor_nombre", "")
            motivo_recomendado = (mejor.get("ventajas") or ["Sin historial suficiente."])[0] if mejor else "Sin historial suficiente."

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
                    proveedor_sugerido=proveedor_recomendado,
                    origen_texto=origen_texto,
                )
                if propuesta_existente.motivo_proveedor_sugerido != motivo_recomendado:
                    propuesta_existente.motivo_proveedor_sugerido = motivo_recomendado
                    propuesta_existente.tocar()
                    cambios = True
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
                proveedor_sugerido=proveedor_recomendado,
                motivo_proveedor_sugerido=motivo_recomendado,
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

        proveedor_final = str(proveedor or propuesta.proveedor_sugerido or "").strip()
        proveedor_obj = self._proveedor_activo("", proveedor_final)
        if proveedor_obj:
            proveedor_final = proveedor_obj.nombre
        if not proveedor_final:
            proveedor_final = "Sin proveedor"

        compra = CompraRegistrada(
            producto=propuesta.producto,
            cantidad=propuesta.comprar,
            unidad=propuesta.unidad,
            proveedor=proveedor_final,
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
        self.registrar_uso_proveedor(producto=compra.producto, proveedor=compra.proveedor, fecha=compra.creado_en)
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
