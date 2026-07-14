from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any
import json
from statistics import mean

from MODELOS.historico_precios import RegistroHistoricoPrecio, AnalisisHistoricoPrecio


class HistoricoInteligentePrecios:
    """
    Host AI 3.0.3.5.3

    Guarda y analiza histórico de precios por artículo.
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.facturas_dir / "historico_precios.json"
        self.registros: List[RegistroHistoricoPrecio] = self._cargar()

    def registrar_precio(self, registro: Dict[str, Any]) -> Dict[str, Any]:
        r = RegistroHistoricoPrecio(
            articulo_id=registro.get("articulo_id", ""),
            nombre_articulo=registro.get("nombre_articulo", ""),
            precio=float(registro.get("precio", registro.get("precio_nuevo", 0)) or 0),
            unidad=registro.get("unidad", ""),
            proveedor_id=registro.get("proveedor_id", ""),
            proveedor_nombre=registro.get("proveedor_nombre", ""),
            numero_factura=registro.get("numero_factura", ""),
            fecha_factura=registro.get("fecha_factura", ""),
            origen=registro.get("origen", "factura"),
        )
        if not r.articulo_id or not r.precio:
            return {"registrado": False, "errores": ["Falta articulo_id o precio."], "lectura_host_ai": "No se registró precio histórico."}
        self.registros.append(r)
        self._guardar()
        return {"registrado": True, "registro": r.to_dict(), "lectura_host_ai": f"Precio histórico registrado: {r.nombre_articulo} {r.precio}."}

    def registrar_desde_aplicacion(self, resultado_aplicacion: Dict[str, Any]) -> Dict[str, Any]:
        if not resultado_aplicacion.get("aplicado"):
            return {"registrado": False, "errores": ["La aplicación de precio no fue aplicada."], "lectura_host_ai": "No se registró histórico."}
        cambio = resultado_aplicacion.get("cambio", {})
        datos = {
            "articulo_id": resultado_aplicacion.get("articulo_id"),
            "nombre_articulo": resultado_aplicacion.get("nombre_articulo"),
            "precio": resultado_aplicacion.get("precio_nuevo"),
            "unidad": resultado_aplicacion.get("unidad"),
            "proveedor_id": resultado_aplicacion.get("proveedor_id"),
            "numero_factura": cambio.get("numero_factura", ""),
            "fecha_factura": cambio.get("fecha_factura", ""),
            "origen": "actualizacion_factura",
        }
        return self.registrar_precio(datos)

    def analizar_articulo(self, articulo_id: str) -> Dict[str, Any]:
        regs = [r for r in self.registros if r.articulo_id == articulo_id]
        if not regs:
            return {"encontrado": False, "lectura_host_ai": "No hay histórico para este artículo."}

        precios = [float(r.precio) for r in regs]
        minimo = min(regs, key=lambda r: r.precio)
        maximo = max(regs, key=lambda r: r.precio)
        primero = regs[0].precio
        ultimo = regs[-1].precio
        variacion = round(((ultimo - primero) / primero) * 100, 2) if primero else 0.0
        tendencia = "estable"
        if variacion > 5:
            tendencia = "sube"
        elif variacion < -5:
            tendencia = "baja"

        analisis = AnalisisHistoricoPrecio(
            articulo_id=articulo_id,
            nombre_articulo=regs[-1].nombre_articulo,
            total_registros=len(regs),
            precio_minimo=round(min(precios), 4),
            precio_maximo=round(max(precios), 4),
            precio_medio=round(mean(precios), 4),
            ultimo_precio=round(ultimo, 4),
            primer_precio=round(primero, 4),
            variacion_total=variacion,
            mejor_proveedor=minimo.proveedor_id,
            peor_proveedor=maximo.proveedor_id,
            tendencia=tendencia,
            registros=[r.to_dict() for r in regs],
        )
        datos = analisis.to_dict()
        datos["encontrado"] = True
        datos["lectura_host_ai"] = f"Histórico {analisis.nombre_articulo}: {analisis.total_registros} registros, tendencia {analisis.tendencia}."
        return datos

    def listar_historico(self) -> Dict[str, Any]:
        data = [r.to_dict() for r in self.registros]
        return {"registros": data, "total": len(data), "lectura_host_ai": f"Histórico de precios: {len(data)} registros."}

    def exportar(self) -> Dict[str, Any]:
        self._guardar()
        return {"archivo": str(self.path), "lectura_host_ai": "Histórico de precios exportado."}

    def _cargar(self) -> List[RegistroHistoricoPrecio]:
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                return [RegistroHistoricoPrecio(**r) for r in raw.get("registros", [])]
            except Exception:
                return []
        return []

    def _guardar(self):
        self.path.write_text(json.dumps({"version": "3.0.3.5.3", "registros": [r.to_dict() for r in self.registros]}, ensure_ascii=False, indent=2), encoding="utf-8")
