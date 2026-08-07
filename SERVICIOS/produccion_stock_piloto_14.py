from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


class ProduccionStockPiloto14:
    """Coordina Producción Real y Stock sin duplicar sus reglas.

    El servicio calcula una vista previa desde el escandallo, valida existencias,
    delega consumos/entradas a ``core.stock`` y solo después cierra la tarea en
    ``core.produccion_real``. Registra una trazabilidad idempotente del piloto.
    """

    VERSION = "PILOTO-1.4"

    def __init__(self, core: Any):
        self.core = core
        self.produccion = core.produccion_real
        self.stock = core.stock
        base_dir = Path(getattr(core, "base_dir", Path.cwd()))
        self.ruta_trazabilidad = base_dir / "DATOS" / "piloto" / "produccion_stock_registros.json"

    def preparar_cierre(self, plan_id: str, tarea_id: str) -> dict[str, Any]:
        plan = self.produccion.obtener_plan(plan_id)
        tarea = next((t for t in plan.tareas if str(t.id) == str(tarea_id)), None)
        if tarea is None:
            raise ValueError("No existe la tarea seleccionada.")
        clave = self._clave(plan_id, tarea_id)
        previo = self._registro_por_clave(clave)
        if previo:
            return {"ok": False, "estado": "YA_REGISTRADA", "mensaje": "Esta producción ya actualizó el stock.", "registro": previo}
        if tarea.estado_ejecucion == "finalizada":
            return {"ok": False, "estado": "FINALIZADA_SIN_REGISTRO", "mensaje": "La tarea ya estaba finalizada antes de PILOTO-1.4. Revísala manualmente antes de tocar stock."}
        if float(tarea.cantidad or 0) <= 0:
            return {"ok": False, "estado": "CANTIDAD_INVALIDA", "mensaje": "La tarea tiene una cantidad no válida para cerrar producción."}

        ingredientes_plan = list((getattr(tarea, "requisitos_recursos", {}) or {}).get("ingredientes") or [])
        escandallo = self._buscar_escandallo(tarea.receta_id, tarea.receta or tarea.titulo)
        if ingredientes_plan:
            escandallo = {"receta_id": tarea.receta_id, "nombre": tarea.receta or tarea.titulo,
                          "raciones_base": float(tarea.cantidad or 1), "lineas": ingredientes_plan}
        if not escandallo:
            return {"ok": False, "estado": "SIN_ESCANDALLO", "mensaje": "No se ha localizado un escandallo para calcular los consumos."}

        base = float(escandallo.get("raciones_base", 1) or 1)
        cantidad = float(tarea.cantidad or base)
        factor = cantidad / base if base else 1.0
        consumos, faltantes, incompletas, incompatibles = [], [], [], []
        for linea in escandallo.get("lineas", []) or []:
            requerido = round(float(linea.get("cantidad_bruta", linea.get("cantidad", 0)) or 0) * factor, 6)
            if requerido <= 0:
                incompletas.append({"linea": linea, "motivo": "Cantidad de línea no válida."})
                continue
            articulo_id = str(linea.get("articulo_id") or linea.get("elaboracion_id") or "")
            nombre = str(linea.get("nombre") or articulo_id or "Ingrediente")
            unidad = str(linea.get("unidad") or "u")
            if not nombre.strip() or not unidad.strip():
                incompletas.append({"linea": linea, "motivo": "Línea sin nombre o unidad."})
                continue
            tipo_linea = str(linea.get("tipo") or "articulo").strip().lower()
            nombre_norm = nombre.strip().lower()
            articulo_norm = articulo_id.strip().lower()
            if tipo_linea == "articulo" and (nombre_norm.startswith("a.p") or articulo_norm.startswith("a.p")):
                return {
                    "ok": False,
                    "estado": "AP_COMO_MP_NO_PERMITIDO",
                    "mensaje": "No se permite usar A.P como materia prima directa en este cierre.",
                    "linea": {"nombre": nombre, "articulo_id": articulo_id, "unidad": unidad},
                }
            disponible = self._disponible(nombre, articulo_id, unidad)
            fila = {"nombre": nombre, "articulo_id": articulo_id, "cantidad": requerido, "unidad": unidad, "disponible": round(disponible, 6), "tipo": linea.get("tipo", "articulo")}
            consumos.append(fila)
            if disponible + 1e-9 < requerido:
                faltantes.append({**fila, "faltante": round(requerido - disponible, 6)})
                if self._hay_unidad_incompatible(nombre, articulo_id, unidad):
                    incompatibles.append({**fila, "motivo": "Existe stock del artículo en una unidad distinta."})

        if incompletas:
            return {
                "ok": False,
                "estado": "RECETA_INCOMPLETA",
                "mensaje": "El escandallo tiene líneas incompletas o inválidas.",
                "lineas_invalidas": incompletas,
            }
        if incompatibles:
            return {
                "ok": False,
                "estado": "UNIDAD_INCOMPATIBLE",
                "mensaje": "Hay artículos con stock en unidades incompatibles para este cierre.",
                "incompatibilidades": incompatibles,
            }

        salida = {
            "nombre": tarea.receta or tarea.titulo,
            "receta_id": tarea.receta_id or escandallo.get("receta_id", ""),
            "cantidad": cantidad,
            "unidad": tarea.unidad or "u",
            "articulo_id": tarea.receta_id or escandallo.get("receta_id", ""),
        }
        traza = self._trazabilidad_base(plan, tarea, salida)
        return {
            "ok": not faltantes,
            "estado": "LISTO" if not faltantes else "STOCK_INSUFICIENTE",
            "plan_id": plan_id, "tarea_id": tarea_id,
            "plan": plan.nombre, "tarea": tarea.titulo,
            "operario": plan.responsable or "cocina",
            "consumos": consumos, "faltantes": faltantes, "produccion_generada": salida,
            "trazabilidad_base": traza,
            "mensaje": "Stock suficiente para registrar la producción." if not faltantes else "No hay stock suficiente para cerrar normalmente.",
        }

    def cerrar_y_actualizar_stock(self, plan_id: str, tarea_id: str, operario: str = "", lote: str = "") -> dict[str, Any]:
        vista = self.preparar_cierre(plan_id, tarea_id)
        if not vista.get("ok"):
            return vista

        # Snapshot en memoria para rollback si cualquier escritura posterior falla.
        lotes_antes = deepcopy(self.stock.lotes)
        movimientos_antes = deepcopy(self.stock.movimientos)
        planes_antes = deepcopy(self.produccion.planes)
        try:
            movimientos = []
            motivo = f"Producción {vista['tarea']} ({plan_id}/{tarea_id})"
            traza_base = dict(vista.get("trazabilidad_base") or {})
            movimientos_salida_ids = []
            lotes_origen = []
            for linea in vista["consumos"]:
                traza_salida = {
                    **traza_base,
                    "elaboracion": vista["produccion_generada"].get("nombre"),
                    "cantidad": float(linea.get("cantidad") or 0),
                    "unidad": linea.get("unidad"),
                    "lote_origen": [],
                    "lote_generado": "",
                }
                resultado = self.stock.consumir(linea["nombre"], linea["cantidad"], linea["unidad"], motivo=motivo, articulo_id=linea["articulo_id"], trazabilidad=traza_salida)
                if not resultado.get("ok", False):
                    raise RuntimeError(resultado.get("lectura_host_ai") or "No se pudo consumir stock.")
                mov = dict(resultado.get("movimiento", {}))
                mov_id = str(mov.get("id") or "")
                consumos_lotes = list(resultado.get("consumos_lotes") or [])
                for c in consumos_lotes:
                    if c.get("lote_id"):
                        lotes_origen.append(c.get("lote_id"))
                if mov_id and mov_id in self.stock.movimientos:
                    traza_actual = dict(self.stock.movimientos[mov_id].trazabilidad or {})
                    traza_actual["lote_origen"] = [x for x in lotes_origen if x]
                    self.stock.movimientos[mov_id].trazabilidad = traza_actual
                    mov = self.stock.movimientos[mov_id].to_dict()
                    movimientos_salida_ids.append(mov_id)
                movimientos.append(mov)

            salida = vista["produccion_generada"]
            traza_entrada = {
                **traza_base,
                "elaboracion": salida.get("nombre"),
                "cantidad": float(salida.get("cantidad") or 0),
                "unidad": salida.get("unidad"),
                "lote_origen": [x for x in lotes_origen if x],
                "lote_generado": "",
            }
            entrada = self.stock.registrar_entrada(
                salida["nombre"], salida["cantidad"], salida["unidad"],
                familia="elaboraciones", ubicacion="producción", articulo_id=salida["articulo_id"],
                motivo=f"Producción terminada {vista['tarea']}" + (f" | lote {lote}" if lote else ""),
                trazabilidad=traza_entrada,
            )
            movimiento_entrada = dict(entrada.get("movimiento", {}))
            lote_generado_id = str((entrada.get("lote") or {}).get("id") or "")
            mov_ent_id = str(movimiento_entrada.get("id") or "")
            if mov_ent_id and mov_ent_id in self.stock.movimientos:
                traza_actual = dict(self.stock.movimientos[mov_ent_id].trazabilidad or {})
                traza_actual["lote_generado"] = lote_generado_id
                self.stock.movimientos[mov_ent_id].trazabilidad = traza_actual
                movimiento_entrada = self.stock.movimientos[mov_ent_id].to_dict()
            movimientos.append(movimiento_entrada)

            transformacion = self.stock.registrar_transformacion(
                salida["nombre"], salida["cantidad"], salida["unidad"],
                motivo=f"Transformación producción {vista['tarea']} ({plan_id}/{tarea_id})",
                articulo_id=salida["articulo_id"],
                trazabilidad={
                    **traza_base,
                    "elaboracion": salida.get("nombre"),
                    "cantidad": float(salida.get("cantidad") or 0),
                    "unidad": salida.get("unidad"),
                    "lote_origen": [x for x in lotes_origen if x],
                    "lote_generado": lote_generado_id,
                    "movimientos_salida": movimientos_salida_ids,
                    "movimiento_entrada": mov_ent_id,
                },
            )
            movimientos.append(dict(transformacion.get("movimiento", {})))
            self.stock._guardar_automatico()
            estado_tarea = self.produccion.finalizar_tarea(plan_id, tarea_id)
            registro = {
                "id": f"PST-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                "clave": self._clave(plan_id, tarea_id), "version": self.VERSION,
                "fecha_hora": datetime.now().isoformat(timespec="seconds"),
                "plan_id": plan_id, "plan": vista["plan"], "tarea_id": tarea_id, "tarea": vista["tarea"],
                "receta_id": vista["produccion_generada"]["receta_id"], "operario": operario or vista["operario"] or "cocina", "lote": lote,
                "consumos": vista["consumos"], "produccion_generada": salida,
                "movimientos_stock": movimientos, "estado": "REGISTRADA",
            }
            self._guardar_registro(registro)
            return {"ok": True, "estado": "REGISTRADA", "mensaje": "Producción terminada y stock actualizado correctamente.", "registro": registro, "tarea": estado_tarea}
        except Exception as exc:
            self.stock.lotes = lotes_antes
            self.stock.movimientos = movimientos_antes
            self.produccion.planes = planes_antes
            self.stock._guardar_automatico()
            self.produccion._persistir()
            return {"ok": False, "estado": "ERROR_REVERTIDO", "mensaje": f"No se aplicó ningún cambio: {exc}"}

    def registrar_incidencia_stock(self, plan_id: str, tarea_id: str, descripcion: str) -> dict[str, Any]:
        texto = (descripcion or "Stock insuficiente al cerrar producción").strip()
        incidencia = self.produccion.registrar_incidencia_tarea(plan_id, tarea_id, "bloqueo", texto, 0)
        return {"ok": True, "estado": "INCIDENCIA_REGISTRADA", "incidencia": incidencia}

    def historial(self) -> list[dict[str, Any]]:
        try:
            datos = json.loads(self.ruta_trazabilidad.read_text(encoding="utf-8"))
            return datos if isinstance(datos, list) else []
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []

    def _buscar_escandallo(self, receta_id: str, nombre: str) -> dict[str, Any] | None:
        escandallos = self.core.db.cargar("escandallos")
        rid = str(receta_id or "").strip().lower()
        nom = str(nombre or "").strip().lower()
        return next((e for e in escandallos if rid and str(e.get("receta_id") or e.get("id") or "").lower() == rid), None) or next((e for e in escandallos if nom and str(e.get("nombre") or "").strip().lower() == nom), None)

    def _disponible(self, nombre: str, articulo_id: str, unidad: str) -> float:
        return float(self.stock._cantidad_disponible(nombre, articulo_id, unidad))

    def _hay_unidad_incompatible(self, nombre: str, articulo_id: str, unidad: str) -> bool:
        objetivo = str(unidad or "").strip().lower()
        nombre_n = str(nombre or "").strip().lower()
        art_n = str(articulo_id or "").strip()
        for lote in self.stock.lotes.values():
            if float(lote.cantidad or 0) <= 0:
                continue
            mismo_articulo = bool(art_n) and str(lote.articulo_id or "").strip() == art_n
            mismo_nombre = str(lote.nombre or "").strip().lower() == nombre_n
            if not (mismo_articulo or mismo_nombre):
                continue
            if str(lote.unidad or "").strip().lower() != objetivo:
                return True
        return False

    @staticmethod
    def _trazabilidad_base(plan: Any, tarea: Any, salida: dict[str, Any]) -> dict[str, Any]:
        hora = datetime.now()
        return {
            "evento": str(getattr(plan, "evento", "") or ""),
            "evento_id": str(getattr(plan, "evento_id", "") or ""),
            "menu_id": str((getattr(plan, "configuracion_planificacion", {}) or {}).get("menu_id") or ""),
            "servicio": str(getattr(tarea, "origen", "") or ""),
            "pase": str(getattr(tarea, "origen", "") or ""),
            "receta": str(getattr(tarea, "receta", "") or salida.get("nombre") or ""),
            "receta_id": str(getattr(tarea, "receta_id", "") or salida.get("receta_id") or ""),
            "usuario": str(getattr(plan, "responsable", "") or "cocina"),
            "fecha": hora.date().isoformat(),
            "hora": hora.time().isoformat(timespec="seconds"),
        }

    @staticmethod
    def _clave(plan_id: str, tarea_id: str) -> str:
        return f"{plan_id}::{tarea_id}"

    def _registro_por_clave(self, clave: str) -> dict[str, Any] | None:
        return next((r for r in self.historial() if r.get("clave") == clave and r.get("estado") == "REGISTRADA"), None)

    def _guardar_registro(self, registro: dict[str, Any]) -> None:
        datos = self.historial()
        datos.append(registro)
        self.ruta_trazabilidad.parent.mkdir(parents=True, exist_ok=True)
        self.ruta_trazabilidad.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def formatear_diagnostico_piloto14(d: dict[str, Any]) -> str:
    return "\n".join([
        "PILOTO-1.4 — PRODUCCIÓN → STOCK", "=" * 78,
        f"Diagnóstico: {d.get('diagnostico')} | Consumos: {d.get('consumos')} | Entradas: {d.get('entradas')}",
        f"Trazabilidad: {d.get('trazabilidad')} | Protección duplicados: {d.get('duplicados')} | Rollback: {d.get('rollback')}",
        "-" * 78,
        "Se validó el cierre transaccional de producción, stock y trazabilidad.",
    ])


__all__ = ["ProduccionStockPiloto14", "formatear_diagnostico_piloto14"]
