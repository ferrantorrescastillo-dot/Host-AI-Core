from __future__ import annotations
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from MODELOS.stock import LoteStock, MovimientoStock
from SERVICIOS.base_datos_local import BaseDatosLocal


class MotorStock:
    def __init__(self, db: Optional[BaseDatosLocal] = None):
        self.db = db
        self.lotes: Dict[str, LoteStock] = {}
        self.movimientos: Dict[str, MovimientoStock] = {}
        self.stock_minimos: Dict[str, float] = {}
        self._cargar_desde_db()

    def _cargar_desde_db(self) -> None:
        if not self.db:
            return
        for fila in self.db.cargar("stock_lotes"):
            try:
                lote = LoteStock(**fila)
                self.lotes[lote.id] = lote
            except Exception:
                continue
        for fila in self.db.cargar("stock_movimientos"):
            try:
                mov = MovimientoStock(**fila)
                self.movimientos[mov.id] = mov
            except Exception:
                continue

    def _guardar_automatico(self) -> None:
        if not self.db:
            return
        self.db.guardar("stock_lotes", [l.to_dict() for l in self.lotes.values()])
        self.db.guardar("stock_movimientos", [m.to_dict() for m in self.movimientos.values()])

    def registrar_entrada(self, nombre: str, cantidad: float, unidad: str, familia: str = "", ubicacion: str = "", proveedor: str = "", articulo_id: str = "", caducidad: str = "", coste_unitario: float = 0.0, motivo: str = "entrada mercancía") -> Dict[str, Any]:
        lote = LoteStock(nombre=nombre, cantidad=float(cantidad), unidad=unidad, familia=familia, ubicacion=ubicacion, proveedor=proveedor, articulo_id=articulo_id, caducidad=caducidad, coste_unitario=float(coste_unitario or 0))
        self.lotes[lote.id] = lote
        mov = MovimientoStock(tipo="entrada", nombre=nombre, cantidad=float(cantidad), unidad=unidad, motivo=motivo, lote_id=lote.id, articulo_id=articulo_id)
        self.movimientos[mov.id] = mov
        self._guardar_automatico()
        return {"lote": lote.to_dict(), "movimiento": mov.to_dict()}

    def consumir(self, nombre: str, cantidad: float, unidad: str, motivo: str = "consumo producción", articulo_id: str = "") -> Dict[str, Any]:
        return self._descontar_stock(nombre, cantidad, unidad, motivo, articulo_id, "salida")

    def registrar_merma(self, nombre: str, cantidad: float, unidad: str, motivo: str = "merma", articulo_id: str = "") -> Dict[str, Any]:
        return self._descontar_stock(nombre, cantidad, unidad, motivo, articulo_id, "merma")

    def ajustar_inventario(self, nombre: str, cantidad_objetivo: float, unidad: str, articulo_id: str = "", familia: str = "", ubicacion: str = "", motivo: str = "ajuste inventario") -> Dict[str, Any]:
        actual = self._cantidad_disponible(nombre, articulo_id, unidad)
        diferencia = round(float(cantidad_objetivo) - actual, 6)
        if abs(diferencia) < 1e-9:
            return {"ok": True, "tipo": "sin_cambios", "cantidad_anterior": actual, "cantidad_objetivo": float(cantidad_objetivo), "diferencia": 0.0, "lectura_host_ai": "El inventario ya coincide con el stock teórico."}
        if diferencia > 0:
            resultado = self.registrar_entrada(nombre, diferencia, unidad, familia=familia, ubicacion=ubicacion, articulo_id=articulo_id, motivo=motivo)
            mov_id = resultado["movimiento"]["id"]
            self.movimientos[mov_id].tipo = "ajuste_positivo"
            self._guardar_automatico()
            return {"ok": True, "tipo": "ajuste_positivo", "cantidad_anterior": actual, "cantidad_objetivo": float(cantidad_objetivo), "diferencia": diferencia, "resultado": resultado, "lectura_host_ai": f"Ajuste positivo registrado: +{diferencia} {unidad}."}
        resultado = self._descontar_stock(nombre, abs(diferencia), unidad, motivo, articulo_id, "ajuste_negativo")
        resultado.update({"tipo": "ajuste_negativo", "cantidad_anterior": actual, "cantidad_objetivo": float(cantidad_objetivo), "diferencia": diferencia})
        return resultado

    def actualizar_lote(self, lote_id: str, ubicacion: Optional[str] = None, caducidad: Optional[str] = None) -> Dict[str, Any]:
        lote = self.lotes.get(lote_id)
        if not lote:
            return {"ok": False, "mensaje": "Lote no encontrado."}
        antes = lote.to_dict()
        if ubicacion is not None:
            lote.ubicacion = ubicacion.strip()
        if caducidad is not None:
            lote.caducidad = caducidad.strip()
        self._guardar_automatico()
        return {"ok": True, "mensaje": f"Lote actualizado: {lote.nombre}.", "antes": antes, "lote": lote.to_dict()}

    def ajustar_minimo(self, nombre: str, cantidad_minima: float, articulo_id: str = "") -> Dict[str, Any]:
        clave = articulo_id or nombre.lower().strip()
        self.stock_minimos[clave] = float(cantidad_minima)
        return {"clave": clave, "stock_minimo": float(cantidad_minima)}

    def stock_actual(self) -> Dict[str, Any]:
        agregado: Dict[str, Dict[str, Any]] = {}
        for lote in self.lotes.values():
            clave = lote.articulo_id or lote.nombre.lower().strip()
            if clave not in agregado:
                agregado[clave] = {"clave": clave, "nombre": lote.nombre, "articulo_id": lote.articulo_id, "familia": lote.familia, "unidad": lote.unidad, "cantidad": 0.0, "lotes": []}
            agregado[clave]["cantidad"] += float(lote.cantidad)
            agregado[clave]["lotes"].append(lote.to_dict())
        return {"items": list(agregado.values()), "total_items": len(agregado), "total_lotes": len(self.lotes), "lectura_host_ai": f"Stock actual: {len(agregado)} artículos agrupados en {len(self.lotes)} lotes."}

    def lotes_listado(self, texto: str = "", ubicacion: str = "", familia: str = "", solo_con_stock: bool = True) -> List[Dict[str, Any]]:
        texto = (texto or "").strip().lower()
        ubicacion = (ubicacion or "").strip().lower()
        familia = (familia or "").strip().lower()
        salida = []
        for lote in self.lotes.values():
            if solo_con_stock and lote.cantidad <= 0:
                continue
            if texto and texto not in lote.nombre.lower() and texto not in lote.articulo_id.lower() and texto not in lote.id.lower():
                continue
            if ubicacion and ubicacion not in (lote.ubicacion or "").lower():
                continue
            if familia and familia not in (lote.familia or "").lower():
                continue
            salida.append(lote.to_dict())
        # FIFO real: primero la entrada más antigua; la caducidad desempata.
        salida.sort(key=lambda x: (x.get("fecha_entrada") or x.get("creado_en", "")[:10], x.get("caducidad") or "9999-12-31", x.get("nombre", "").lower()))
        return salida

    def movimientos_articulo(self, texto: str = "") -> List[Dict[str, Any]]:
        texto = (texto or "").strip().lower()
        salida = []
        for mov in self.movimientos.values():
            if texto and texto not in mov.nombre.lower() and texto not in mov.articulo_id.lower() and texto not in mov.tipo.lower():
                continue
            salida.append(mov.to_dict())
        salida.sort(key=lambda x: (x.get("creado_en", ""), x.get("id", "")), reverse=True)
        return salida

    def diagnosticar_stock(self, dias_caducidad_alerta: int = 3) -> Dict[str, Any]:
        avisos = []
        for item in self.stock_actual()["items"]:
            clave = item["articulo_id"] or item["nombre"].lower().strip()
            minimo = self.stock_minimos.get(clave)
            if minimo is not None and item["cantidad"] < minimo:
                avisos.append({"tipo": "bajo_stock", "nivel": "alto", "mensaje": f"{item['nombre']} está bajo mínimo: {item['cantidad']} {item['unidad']} < {minimo} {item['unidad']}.", "item": item})
        hoy = date.today()
        for lote in self.lotes.values():
            if lote.cantidad <= 0:
                continue
            if not lote.ubicacion:
                avisos.append({"tipo": "sin_ubicacion", "nivel": "bajo", "mensaje": f"{lote.nombre} tiene un lote sin ubicación.", "lote": lote.to_dict()})
            if lote.caducidad:
                try:
                    cad = datetime.fromisoformat(lote.caducidad).date()
                    dias = (cad - hoy).days
                    if dias < 0:
                        avisos.append({"tipo": "caducado", "nivel": "alto", "mensaje": f"{lote.nombre} caducó hace {abs(dias)} días.", "lote": lote.to_dict()})
                    elif dias <= dias_caducidad_alerta:
                        avisos.append({"tipo": "caducidad_cercana", "nivel": "medio", "mensaje": f"{lote.nombre} caduca en {dias} días.", "lote": lote.to_dict()})
                except Exception:
                    avisos.append({"tipo": "caducidad_invalida", "nivel": "medio", "mensaje": f"{lote.nombre} tiene fecha de caducidad inválida.", "lote": lote.to_dict()})
        return {"avisos": avisos, "total_avisos": len(avisos), "estado": "revisar" if avisos else "ok", "lectura_host_ai": "Stock sin avisos críticos." if not avisos else f"Stock con {len(avisos)} avisos."}

    def resumen_operativo(self, dias_caducidad_alerta: int = 3) -> Dict[str, Any]:
        actual = self.stock_actual()
        diagnostico = self.diagnosticar_stock(dias_caducidad_alerta)
        por_ubicacion: Dict[str, Dict[str, Any]] = {}
        valor_total = 0.0
        lotes_caducados = 0
        lotes_caducan_pronto = 0
        hoy = date.today()
        for lote in self.lotes.values():
            if lote.cantidad <= 0:
                continue
            ubic = lote.ubicacion or "sin ubicación"
            info = por_ubicacion.setdefault(ubic, {"lotes": 0, "articulos": set(), "valor": 0.0})
            info["lotes"] += 1
            info["articulos"].add(lote.articulo_id or lote.nombre.lower().strip())
            valor = float(lote.cantidad) * float(lote.coste_unitario or 0)
            info["valor"] += valor
            valor_total += valor
            if lote.caducidad:
                try:
                    dias = (datetime.fromisoformat(lote.caducidad).date() - hoy).days
                    if dias < 0:
                        lotes_caducados += 1
                    elif dias <= dias_caducidad_alerta:
                        lotes_caducan_pronto += 1
                except Exception:
                    pass
        ubicaciones = []
        for nombre, info in sorted(por_ubicacion.items()):
            ubicaciones.append({"ubicacion": nombre, "lotes": info["lotes"], "articulos": len(info["articulos"]), "valor": round(info["valor"], 2)})
        lotes_positivos = [l for l in self.lotes.values() if l.cantidad > 0]
        lotes_sin_precio = sum(1 for l in lotes_positivos if float(l.coste_unitario or 0) <= 0)
        lotes_sin_ubicacion = sum(1 for l in lotes_positivos if not (l.ubicacion or "").strip())
        articulos_bajo_minimo = sum(1 for a in diagnostico["avisos"] if a.get("tipo") == "bajo_stock")
        return {
            "total_articulos": actual["total_items"],
            "total_lotes": actual["total_lotes"],
            "valor_total": round(valor_total, 2),
            "ubicaciones": ubicaciones,
            "avisos": diagnostico["avisos"],
            "total_avisos": diagnostico["total_avisos"],
            "lotes_caducados": lotes_caducados,
            "lotes_caducan_pronto": lotes_caducan_pronto,
            "lotes_sin_precio": lotes_sin_precio,
            "lotes_sin_ubicacion": lotes_sin_ubicacion,
            "articulos_bajo_minimo": articulos_bajo_minimo,
            "lectura_host_ai": f"Stock operativo: {actual['total_items']} artículos, {actual['total_lotes']} lotes y {diagnostico['total_avisos']} avisos.",
        }


    def ultimo_coste_conocido(self, nombre: str = "", articulo_id: str = "", proveedor: str = "") -> float:
        """Devuelve el coste positivo más reciente compatible con el artículo.

        Prioriza el ID de artículo, después el nombre y opcionalmente el proveedor.
        Los lotes sin coste no sustituyen un coste válido anterior.
        """
        nombre_n = (nombre or "").strip().lower()
        proveedor_n = (proveedor or "").strip().lower()
        candidatos = []
        for lote in self.lotes.values():
            if float(lote.coste_unitario or 0) <= 0:
                continue
            mismo_id = bool(articulo_id) and lote.articulo_id == articulo_id
            mismo_nombre = bool(nombre_n) and lote.nombre.strip().lower() == nombre_n
            if not (mismo_id or mismo_nombre):
                continue
            if proveedor_n and (lote.proveedor or "").strip().lower() != proveedor_n:
                continue
            candidatos.append(lote)
        if not candidatos and proveedor_n:
            return self.ultimo_coste_conocido(nombre=nombre, articulo_id=articulo_id)
        if not candidatos:
            return 0.0
        ultimo = sorted(candidatos, key=lambda l: (l.creado_en, l.id))[-1]
        return float(ultimo.coste_unitario or 0)

    def predecir_necesidad(self, nombre: str, cantidad_necesaria: float, unidad: str, articulo_id: str = "") -> Dict[str, Any]:
        disponible = self._cantidad_disponible(nombre, articulo_id, unidad)
        falta = max(0.0, float(cantidad_necesaria) - disponible)
        return {"nombre": nombre, "articulo_id": articulo_id, "cantidad_necesaria": float(cantidad_necesaria), "cantidad_disponible": disponible, "cantidad_faltante": falta, "unidad": unidad, "estado": "ok" if falta <= 0 else "falta_stock", "lectura_host_ai": f"Hay stock suficiente de {nombre}." if falta <= 0 else f"Faltan {falta} {unidad} de {nombre}."}

    def corregir_ultima_entrada(self) -> Dict[str, Any]:
        entradas = [m for m in self.movimientos.values() if m.tipo in {"entrada", "ajuste_positivo"}]
        if not entradas:
            return {"ok": False, "mensaje": "No hay entradas de stock para corregir."}
        ultimo = sorted(entradas, key=lambda m: (m.creado_en, list(self.movimientos).index(m.id)))[-1]
        lote = self.lotes.get(ultimo.lote_id)
        if lote is None:
            return {"ok": False, "mensaje": "La última entrada no tiene un lote asociado válido."}
        self.movimientos.pop(ultimo.id, None)
        self.lotes.pop(lote.id, None)
        self._guardar_automatico()
        return {"ok": True, "mensaje": f"Entrada corregida: {lote.nombre}, {lote.cantidad} {lote.unidad}.", "lote": lote.to_dict(), "movimiento": ultimo.to_dict()}

    def ultima_entrada(self) -> Optional[Dict[str, Any]]:
        entradas = [m for m in self.movimientos.values() if m.tipo in {"entrada", "ajuste_positivo"}]
        if not entradas:
            return None
        ultimo = sorted(entradas, key=lambda m: (m.creado_en, list(self.movimientos).index(m.id)))[-1]
        lote = self.lotes.get(ultimo.lote_id)
        return {"movimiento": ultimo.to_dict(), "lote": lote.to_dict() if lote else None}

    def movimientos_listado(self) -> List[Dict[str, Any]]:
        return self.movimientos_articulo("")

    def _descontar_stock(self, nombre: str, cantidad: float, unidad: str, motivo: str, articulo_id: str, tipo_movimiento: str) -> Dict[str, Any]:
        cantidad_pendiente = float(cantidad)
        consumos = []
        lotes = sorted(self._lotes_compatibles(nombre, articulo_id, unidad), key=lambda l: (self._fecha_sort(l.caducidad), self._fecha_sort(l.fecha_entrada), l.creado_en, l.id))
        for lote in lotes:
            if cantidad_pendiente <= 0:
                break
            usar = min(lote.cantidad, cantidad_pendiente)
            lote.cantidad -= usar
            cantidad_pendiente -= usar
            consumos.append({"lote_id": lote.id, "cantidad": usar, "unidad": unidad, "ubicacion": lote.ubicacion})
        aplicado = float(cantidad) - cantidad_pendiente
        mov = MovimientoStock(tipo=tipo_movimiento, nombre=nombre, cantidad=aplicado, unidad=unidad, motivo=motivo, articulo_id=articulo_id)
        self.movimientos[mov.id] = mov
        self._guardar_automatico()
        ok = cantidad_pendiente <= 0
        return {"movimiento": mov.to_dict(), "consumos_lotes": consumos, "cantidad_solicitada": float(cantidad), "cantidad_consumida": aplicado, "cantidad_faltante": max(0.0, cantidad_pendiente), "ok": ok, "lectura_host_ai": f"{tipo_movimiento.replace('_', ' ').capitalize()} registrado correctamente." if ok else f"No hay stock suficiente. Faltan {cantidad_pendiente} {unidad} de {nombre}."}

    def _lotes_compatibles(self, nombre: str, articulo_id: str, unidad: str):
        salida = []
        for lote in self.lotes.values():
            mismo_articulo = bool(articulo_id) and lote.articulo_id == articulo_id
            mismo_nombre = lote.nombre.lower().strip() == nombre.lower().strip()
            if (mismo_articulo or mismo_nombre) and lote.unidad.lower() == unidad.lower() and lote.cantidad > 0:
                salida.append(lote)
        return salida

    def _cantidad_disponible(self, nombre: str, articulo_id: str, unidad: str) -> float:
        return sum(l.cantidad for l in self._lotes_compatibles(nombre, articulo_id, unidad))

    def _fecha_sort(self, fecha_txt: str):
        return fecha_txt or "9999-12-31"
