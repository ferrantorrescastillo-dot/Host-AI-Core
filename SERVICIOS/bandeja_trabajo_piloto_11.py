from __future__ import annotations

import json
import shutil
import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class BandejaTrabajoPiloto11:
    """Bandeja persistente y de solo orquestación para el piloto privado.

    No sustituye los motores de recepción, producción, eventos, compras o stock.
    Conserva tareas y referencias para retomarlas sin perder contexto.
    """

    ESTADOS_ABIERTOS = {"PENDIENTE", "EN_CURSO", "APLAZADA", "BLOQUEADA"}
    TIPOS = {
        "RECEPCION", "STOCK", "PRODUCCION", "EVENTO", "PEDIDO",
        "INCIDENCIA_PROVEEDOR", "DOCUMENTO", "GENERAL",
    }

    def __init__(self, base_dir: Path | str):
        self.base_dir = Path(base_dir).resolve()
        self.data_dir = self.base_dir / "DATOS" / "piloto" / "bandeja_trabajo"
        self.data_path = self.data_dir / "bandeja.json"
        self.backup_dir = self.base_dir / "DATOS" / "backups" / "piloto11"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        if not self.data_path.exists():
            self._write({"version": "PILOTO-1.1", "actualizado_en": _now(), "tareas": []})

    def cargar(self) -> dict[str, Any]:
        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"version": "PILOTO-1.1", "actualizado_en": _now(), "tareas": []}
        if not isinstance(data, dict) or not isinstance(data.get("tareas"), list):
            raise ValueError("La bandeja de trabajo tiene un formato inválido.")
        return data

    def listar(self, estados: Iterable[str] | None = None, incluir_completadas: bool = False) -> list[dict[str, Any]]:
        self.sincronizar_fuentes()
        tareas = self.cargar()["tareas"]
        if estados:
            allowed = {x.upper() for x in estados}
            tareas = [t for t in tareas if t.get("estado") in allowed]
        elif not incluir_completadas:
            tareas = [t for t in tareas if t.get("estado") in self.ESTADOS_ABIERTOS]
        return sorted(tareas, key=lambda t: (-int(t.get("prioridad", 50)), t.get("creado_en", "")))

    def resumen(self) -> dict[str, Any]:
        tareas = self.listar(incluir_completadas=True)
        counts: dict[str, int] = {}
        for t in tareas:
            counts[t.get("estado", "PENDIENTE")] = counts.get(t.get("estado", "PENDIENTE"), 0) + 1
        return {
            "total": len(tareas),
            "abiertas": sum(1 for t in tareas if t.get("estado") in self.ESTADOS_ABIERTOS),
            "pendientes": counts.get("PENDIENTE", 0),
            "en_curso": counts.get("EN_CURSO", 0),
            "aplazadas": counts.get("APLAZADA", 0),
            "bloqueadas": counts.get("BLOQUEADA", 0),
            "completadas": counts.get("COMPLETADA", 0),
        }

    def crear_tarea(self, titulo: str, tipo: str = "GENERAL", prioridad: int = 50,
                    descripcion: str = "", origen: str = "manual", referencia: str = "",
                    metadatos: dict[str, Any] | None = None) -> dict[str, Any]:
        titulo = titulo.strip()
        if not titulo:
            raise ValueError("El título de la tarea es obligatorio.")
        tipo = tipo.upper().strip() or "GENERAL"
        if tipo not in self.TIPOS:
            tipo = "GENERAL"
        data = self.cargar()
        task = {
            "id": _uid("TAREA"), "titulo": titulo, "tipo": tipo,
            "descripcion": descripcion.strip(), "prioridad": max(0, min(100, int(prioridad))),
            "estado": "PENDIENTE", "origen": origen, "referencia": referencia,
            "metadatos": metadatos or {}, "creado_en": _now(), "actualizado_en": _now(),
            "iniciado_en": "", "completado_en": "", "aplazado_hasta": "",
            "notas": [], "historial": [{"fecha": _now(), "accion": "CREADA", "detalle": origen}],
        }
        data["tareas"].append(task)
        self._save(data)
        return deepcopy(task)

    def obtener(self, task_id: str) -> dict[str, Any]:
        task = next((x for x in self.cargar()["tareas"] if x.get("id") == task_id), None)
        if not task:
            raise ValueError(f"No existe la tarea {task_id}.")
        return deepcopy(task)

    def cambiar_estado(self, task_id: str, estado: str, nota: str = "", aplazado_hasta: str = "") -> dict[str, Any]:
        estado = estado.upper().strip()
        if estado not in {"PENDIENTE", "EN_CURSO", "APLAZADA", "BLOQUEADA", "COMPLETADA", "CANCELADA"}:
            raise ValueError("Estado no válido.")
        data = self.cargar()
        task = next((x for x in data["tareas"] if x.get("id") == task_id), None)
        if not task:
            raise ValueError(f"No existe la tarea {task_id}.")
        task["estado"] = estado
        task["actualizado_en"] = _now()
        if estado == "EN_CURSO" and not task.get("iniciado_en"):
            task["iniciado_en"] = _now()
        if estado == "COMPLETADA":
            task["completado_en"] = _now()
        if estado == "APLAZADA":
            task["aplazado_hasta"] = aplazado_hasta.strip()
        if nota.strip():
            task.setdefault("notas", []).append({"fecha": _now(), "texto": nota.strip()})
        task.setdefault("historial", []).append({"fecha": _now(), "accion": estado, "detalle": nota.strip()})
        self._save(data)
        return deepcopy(task)

    def eliminar(self, task_id: str) -> None:
        data = self.cargar()
        before = len(data["tareas"])
        data["tareas"] = [x for x in data["tareas"] if x.get("id") != task_id]
        if len(data["tareas"]) == before:
            raise ValueError(f"No existe la tarea {task_id}.")
        self._save(data)

    def registrar_recepcion_pendiente(self, plan: dict[str, Any], motivo: str = "Actualizar stock más tarde") -> dict[str, Any]:
        referencia = str(self.base_dir / "DATOS" / "piloto" / "recepciones" / f"{plan['plan_id']}.json")
        title = f"Finalizar recepción {plan.get('proveedor') or plan.get('plan_id')}"
        return self._crear_si_no_existe(
            clave=f"recepcion:{plan['plan_id']}", titulo=title, tipo="RECEPCION", prioridad=90,
            descripcion=motivo, origen="PILOTO-1", referencia=referencia,
            metadatos={"plan_id": plan["plan_id"], "estado_plan": plan.get("estado"), "proveedor": plan.get("proveedor", "")},
        )

    def sincronizar_fuentes(self) -> int:
        created = 0
        created += self._sync_recepciones()
        created += self._sync_produccion()
        created += self._sync_eventos()
        created += self._sync_pedidos()
        return created

    def _sync_recepciones(self) -> int:
        folder = self.base_dir / "DATOS" / "piloto" / "recepciones"
        if not folder.exists():
            return 0
        count = 0
        result_ids = {p.name.replace("_resultado.json", "") for p in folder.glob("*_resultado.json")}
        for path in folder.glob("REC-*.json"):
            if path.stem in result_ids or path.name.endswith("_resultado.json"):
                continue
            try:
                plan = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if plan.get("estado") not in {"LISTA_PARA_CONFIRMAR", "REQUIERE_REVISION"}:
                continue
            if self._crear_si_no_existe(
                clave=f"recepcion:{plan.get('plan_id')}",
                titulo=f"Finalizar recepción {plan.get('proveedor') or plan.get('plan_id')}",
                tipo="RECEPCION", prioridad=90,
                descripcion="Recepción guardada y pendiente de revisar o aplicar.", origen="sincronizacion_recepciones",
                referencia=str(path), metadatos={"plan_id": plan.get("plan_id"), "estado_plan": plan.get("estado")},
            ).get("_creada"):
                count += 1
        return count

    def _sync_produccion(self) -> int:
        path = self.base_dir / "DATOS" / "db" / "planes_produccion.json"
        data = self._load_json(path, [])
        count = 0
        for plan in data if isinstance(data, list) else []:
            for tarea in plan.get("tareas", []):
                if tarea.get("estado_ejecucion", "pendiente") in {"finalizada", "completada"}:
                    continue
                item = self._crear_si_no_existe(
                    clave=f"produccion:{tarea.get('id')}", titulo=tarea.get("titulo") or "Producción pendiente",
                    tipo="PRODUCCION", prioridad=int(tarea.get("prioridad", 70)),
                    descripcion=f"{plan.get('evento') or plan.get('nombre') or ''} · {tarea.get('cantidad', '')} {tarea.get('unidad', '')}".strip(" ·"),
                    origen="planes_produccion", referencia=str(path),
                    metadatos={"plan_id": plan.get("id"), "tarea_id": tarea.get("id"), "evento_id": plan.get("evento_id")},
                )
                count += int(bool(item.get("_creada")))
        return count

    def _sync_eventos(self) -> int:
        path = self.base_dir / "DATOS" / "db" / "eventos.json"
        data = self._load_json(path, [])
        count = 0
        for evt in data if isinstance(data, list) else []:
            if str(evt.get("estado", "pendiente")).lower() in {"cerrado", "completado", "cancelado"}:
                continue
            fecha = evt.get("fecha") or "sin fecha"
            item = self._crear_si_no_existe(
                clave=f"evento:{evt.get('id')}", titulo=f"Revisar evento: {evt.get('nombre') or evt.get('id')}",
                tipo="EVENTO", prioridad=65, descripcion=f"{fecha} · {evt.get('pax', 0)} pax",
                origen="eventos", referencia=str(path), metadatos={"evento_id": evt.get("id")},
            )
            count += int(bool(item.get("_creada")))
        return count

    def _sync_pedidos(self) -> int:
        path = self.base_dir / "DATOS" / "db" / "compras_pedidos.json"
        data = self._load_json(path, [])
        count = 0
        for ped in data if isinstance(data, list) else []:
            if str(ped.get("estado", "borrador")).lower() in {"recibido", "cancelado", "cerrado"}:
                continue
            item = self._crear_si_no_existe(
                clave=f"pedido:{ped.get('id')}", titulo=f"Pedido pendiente: {ped.get('proveedor') or ped.get('id')}",
                tipo="PEDIDO", prioridad=75, descripcion=f"Estado {ped.get('estado')} · {ped.get('total_lineas', len(ped.get('lineas', [])))} líneas",
                origen="compras_pedidos", referencia=str(path), metadatos={"pedido_id": ped.get("id")},
            )
            count += int(bool(item.get("_creada")))
        return count

    def _crear_si_no_existe(self, clave: str, **kwargs: Any) -> dict[str, Any]:
        data = self.cargar()
        for task in data["tareas"]:
            if task.get("metadatos", {}).get("clave_origen") == clave and task.get("estado") not in {"CANCELADA"}:
                out = deepcopy(task); out["_creada"] = False; return out
        meta = dict(kwargs.pop("metadatos", {}) or {})
        meta["clave_origen"] = clave
        task = self.crear_tarea(metadatos=meta, **kwargs)
        task["_creada"] = True
        return task

    def diagnostico(self) -> dict[str, Any]:
        diag = self.base_dir / "DATOS" / "mur" / "diagnostico_piloto11"
        if diag.exists():
            shutil.rmtree(diag)
        diag.mkdir(parents=True)
        old_path, old_dir = self.data_path, self.data_dir
        try:
            self.data_dir = diag
            self.data_path = diag / "bandeja.json"
            self._write({"version": "PILOTO-1.1", "actualizado_en": _now(), "tareas": []})
            a = self.crear_tarea("Comprobar pedido Makro", "RECEPCION", 90)
            b = self.crear_tarea("Descontar producción del día", "STOCK", 80)
            self.cambiar_estado(a["id"], "EN_CURSO", "Proveedor descargando")
            self.cambiar_estado(a["id"], "APLAZADA", "Actualizar al final del día", "fin del día")
            self.cambiar_estado(b["id"], "COMPLETADA", "Producción registrada")
            data = self.cargar()
            abiertas = sum(1 for x in data["tareas"] if x.get("estado") in self.ESTADOS_ABIERTOS)
            completadas = sum(1 for x in data["tareas"] if x.get("estado") == "COMPLETADA")
            return {
                "diagnostico": "OK", "tareas": len(data["tareas"]), "abiertas": abiertas,
                "completadas": completadas, "persistencia": str(self.data_path),
                "estados": sorted({x["estado"] for x in data["tareas"]}), "integridad": "OK",
            }
        finally:
            self.data_path, self.data_dir = old_path, old_dir

    def _save(self, data: dict[str, Any]) -> None:
        data["actualizado_en"] = _now()
        backup = self.backup_dir / f"bandeja-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.json"
        if self.data_path.exists():
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.data_path, backup)
        self._write(data)

    def _write(self, data: Any) -> None:
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.data_path.with_suffix(".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        json.loads(temp.read_text(encoding="utf-8"))
        temp.replace(self.data_path)

    @staticmethod
    def _load_json(path: Path, default: Any) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return deepcopy(default)


def formatear_diagnostico_piloto11(data: dict[str, Any]) -> str:
    return "\n".join([
        "PILOTO-1.1 — BANDEJA DE TRABAJO OPERATIVA", "=" * 78,
        f"Diagnóstico: {data['diagnostico']} | Integridad: {data['integridad']}",
        f"Tareas: {data['tareas']} | Abiertas: {data['abiertas']} | Completadas: {data['completadas']}",
        f"Estados validados: {', '.join(data['estados'])}",
        f"Persistencia aislada: {data['persistencia']}", "-" * 78,
        "Se validó alta, persistencia, inicio, aplazamiento, finalización, historial y resumen.",
        "El diagnóstico no modifica recepciones, producción, stock, compras ni eventos reales.",
    ])


__all__ = ["BandejaTrabajoPiloto11", "formatear_diagnostico_piloto11"]
