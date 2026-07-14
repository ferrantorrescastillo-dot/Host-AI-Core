from __future__ import annotations
from typing import Dict, Any
from SERVICIOS.base_datos_local import BaseDatosLocal

class MotorPersistencia:
    def __init__(self, core, db: BaseDatosLocal):
        self.core = core
        self.db = db

    def guardar_todo(self) -> Dict[str, Any]:
        r = []
        if hasattr(self.core, "eventos"):
            r.append(self.db.guardar("eventos", [e.to_dict() for e in self.core.eventos.eventos.values()]))
        if hasattr(self.core, "stock"):
            r.append(self.db.guardar("stock_lotes", [l.to_dict() for l in self.core.stock.lotes.values()]))
            r.append(self.db.guardar("stock_movimientos", [m.to_dict() for m in self.core.stock.movimientos.values()]))
        if hasattr(self.core, "compras"):
            r.append(self.db.guardar("compras_necesidades", [n.to_dict() for n in self.core.compras.necesidades.values()]))
            r.append(self.db.guardar("compras_pedidos", [p.to_dict() for p in self.core.compras.pedidos_sugeridos.values()]))
        if hasattr(self.core, "escandallos_inteligente"):
            r.append(self.db.guardar("escandallos", [e.to_dict() for e in self.core.escandallos_inteligente.escandallos.values()]))
        if hasattr(self.core, "costes_inteligente"):
            r.append(self.db.guardar("precios", [p.to_dict() for p in self.core.costes_inteligente.precios.values()]))
        if hasattr(self.core, "produccion_real"):
            r.append(self.db.guardar("planes_produccion", [p.to_dict() for p in self.core.produccion_real.planes.values()]))
        if hasattr(self.core, "ia_culinaria"):
            r.append(self.db.guardar("ideas_culinarias", [i.to_dict() for i in self.core.ia_culinaria.ideas.values()]))
        if hasattr(self.core, "asistente_conversacional"):
            r.append(self.db.guardar("historial_chat", [h.to_dict() for h in self.core.asistente_conversacional.historial]))
        return {"ok": True, "resultados": r, "lectura_host_ai": "Datos guardados en base de datos local."}

    def resumen(self): return self.db.resumen()
    def snapshot(self, nombre: str = ""): return self.db.snapshot(nombre)
    def limpiar(self): return self.db.borrar_todo()
