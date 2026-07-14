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

        escandallo = self._buscar_escandallo(tarea.receta_id, tarea.receta or tarea.titulo)
        if not escandallo:
            return {"ok": False, "estado": "SIN_ESCANDALLO", "mensaje": "No se ha localizado un escandallo para calcular los consumos."}

        base = float(escandallo.get("raciones_base", 1) or 1)
        cantidad = float(tarea.cantidad or base)
        factor = cantidad / base if base else 1.0
        consumos, faltantes = [], []
        for linea in escandallo.get("lineas", []) or []:
            requerido = round(float(linea.get("cantidad_bruta", linea.get("cantidad", 0)) or 0) * factor, 6)
            if requerido <= 0:
                continue
            articulo_id = str(linea.get("articulo_id") or linea.get("elaboracion_id") or "")
            nombre = str(linea.get("nombre") or articulo_id or "Ingrediente")
            unidad = str(linea.get("unidad") or "u")
            disponible = self._disponible(nombre, articulo_id, unidad)
            fila = {"nombre": nombre, "articulo_id": articulo_id, "cantidad": requerido, "unidad": unidad, "disponible": round(disponible, 6), "tipo": linea.get("tipo", "articulo")}
            consumos.append(fila)
            if disponible + 1e-9 < requerido:
                faltantes.append({**fila, "faltante": round(requerido - disponible, 6)})

        salida = {
            "nombre": tarea.receta or tarea.titulo,
            "receta_id": tarea.receta_id or escandallo.get("receta_id", ""),
            "cantidad": cantidad,
            "unidad": tarea.unidad or "u",
            "articulo_id": tarea.receta_id or escandallo.get("receta_id", ""),
        }
        return {
            "ok": not faltantes,
            "estado": "LISTO" if not faltantes else "STOCK_INSUFICIENTE",
            "plan_id": plan_id, "tarea_id": tarea_id,
            "plan": plan.nombre, "tarea": tarea.titulo,
            "operario": plan.responsable or "cocina",
            "consumos": consumos, "faltantes": faltantes, "produccion_generada": salida,
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
            for linea in vista["consumos"]:
                resultado = self.stock.consumir(linea["nombre"], linea["cantidad"], linea["unidad"], motivo=motivo, articulo_id=linea["articulo_id"])
                if not resultado.get("ok", False):
                    raise RuntimeError(resultado.get("lectura_host_ai") or "No se pudo consumir stock.")
                movimientos.append(resultado.get("movimiento", {}))

            salida = vista["produccion_generada"]
            entrada = self.stock.registrar_entrada(
                salida["nombre"], salida["cantidad"], salida["unidad"],
                familia="elaboraciones", ubicacion="producción", articulo_id=salida["articulo_id"],
                motivo=f"Producción terminada {vista['tarea']}" + (f" | lote {lote}" if lote else ""),
            )
            movimientos.append(entrada.get("movimiento", {}))
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
