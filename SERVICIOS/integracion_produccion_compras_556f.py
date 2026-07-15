from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import unicodedata

from MOTORES.motor_compras import MotorCompras
from SERVICIOS.base_datos_local import BaseDatosLocal


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return " ".join(text.split())


def _traza_necesidad(evento: Dict[str, Any], articulo_id: str, articulo: str, unidad: str) -> str:
    evento_id = str(evento.get("id") or "").strip() or "SIN_EVENTO_ID"
    articulo_ref = articulo_id or _norm(articulo) or "SIN_ARTICULO"
    return f"AUTO556F|EVENTO={evento_id}|ART={articulo_ref}|UNI={_norm(unidad)}"


class IntegracionProduccionCompras556F:
    """Integra faltantes 556F en el motor de compras existente sin crear pedidos definitivos."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.db = BaseDatosLocal(self.base_dir)
        self.motor = MotorCompras(self.db)

    def integrar(
        self,
        *,
        evento: Dict[str, Any],
        plan_id: str,
        compras_propuestas: List[Dict[str, Any]],
        generar_pedidos_sugeridos: bool = False,
    ) -> Dict[str, Any]:
        creadas = 0
        actualizadas = 0
        omitidas = 0
        necesidades_ids: List[str] = []

        fecha_necesaria = str(evento.get("fecha") or "").strip()
        motivo_base = f"FALTANTE_PARA_PRODUCCION_EVENTO {plan_id}"

        for compra in compras_propuestas:
            cantidad = float(compra.get("cantidad") or 0)
            if cantidad <= 0:
                omitidas += 1
                continue

            articulo = str(compra.get("articulo") or "").strip()
            unidad = str(compra.get("unidad") or "").strip() or "u"
            articulo_id = str(compra.get("articulo_id") or "").strip()
            proveedor = str(compra.get("proveedor") or "").strip() or "Sin proveedor asignado"
            traza = _traza_necesidad(evento, articulo_id, articulo, unidad)
            motivo = f"{motivo_base} [{traza}]"

            existente = self._buscar_pendiente(traza, articulo_id, articulo, unidad)
            if existente:
                necesidad = self.motor.editar_necesidad(
                    existente["id"],
                    nombre=articulo,
                    cantidad=cantidad,
                    unidad=unidad,
                    familia="produccion_evento_556f",
                    proveedor_preferente=proveedor,
                    motivo=motivo,
                    prioridad=90,
                    articulo_id=articulo_id,
                    fecha_necesaria=fecha_necesaria,
                )
                actualizadas += 1
            else:
                necesidad = self.motor.registrar_necesidad(
                    nombre=articulo,
                    cantidad=cantidad,
                    unidad=unidad,
                    familia="produccion_evento_556f",
                    proveedor_preferente=proveedor,
                    motivo=motivo,
                    prioridad=90,
                    articulo_id=articulo_id,
                    fecha_necesaria=fecha_necesaria,
                )
                creadas += 1
            necesidades_ids.append(necesidad.id)

        pedidos = {
            "total_pedidos": 0,
            "total_necesidades": 0,
            "pedidos_sugeridos": [],
            "pedidos_abiertos": len([p for p in self.motor.pedidos_sugeridos.values() if p.estado not in {"cancelado", "recibido"}]),
        }
        if generar_pedidos_sugeridos:
            pedidos = self.motor.generar_pedidos_sugeridos()

        modificados = (creadas + actualizadas) > 0 or bool(pedidos.get("total_pedidos", 0))
        return {
            "activada": True,
            "generar_pedidos_sugeridos": bool(generar_pedidos_sugeridos),
            "necesidades_creadas": creadas,
            "necesidades_actualizadas": actualizadas,
            "lineas_omitidas": omitidas,
            "necesidades_ids": necesidades_ids,
            "pedidos_sugeridos": {
                "total_pedidos_nuevos": int(pedidos.get("total_pedidos", 0) or 0),
                "total_necesidades_enlazadas": int(pedidos.get("total_necesidades", 0) or 0),
                "pedidos_abiertos": int(pedidos.get("pedidos_abiertos", 0) or 0),
                "ids": [p.get("id") for p in (pedidos.get("pedidos_sugeridos") or []) if p.get("id")],
            },
            "datos_reales_modificados": modificados,
            "modo": "necesidades_y_pedidos_sugeridos" if generar_pedidos_sugeridos else "solo_necesidades",
        }

    def _buscar_pendiente(self, traza: str, articulo_id: str, articulo: str, unidad: str) -> Optional[Dict[str, Any]]:
        articulo_norm = _norm(articulo)
        unidad_norm = _norm(unidad)
        for n in self.motor.necesidades.values():
            if n.estado != "pendiente":
                continue
            if traza in str(n.motivo or ""):
                return n.to_dict()
            mismo_articulo = False
            if articulo_id and str(n.articulo_id or "").strip() == articulo_id:
                mismo_articulo = True
            elif _norm(n.nombre) == articulo_norm:
                mismo_articulo = True
            if not mismo_articulo:
                continue
            if _norm(n.unidad) != unidad_norm:
                continue
            if str(n.motivo or "").startswith("FALTANTE_PARA_PRODUCCION_EVENTO"):
                return n.to_dict()
        return None
