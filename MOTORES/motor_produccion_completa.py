from __future__ import annotations

from typing import Dict, List, Any
from MODELOS.produccion_completa import NecesidadProduccion, InformeProduccionCompleta


class MotorProduccionCompleta:
    def __init__(self, core):
        self.core = core
        self.informes: Dict[str, InformeProduccionCompleta] = {}

    def analizar_evento(self, evento_id: str, hora_inicio_produccion: str = "08:00", margen_seguridad_min: int = 60, generar_compras: bool = True) -> Dict[str, Any]:
        evento = self.core.eventos.obtener(evento_id).to_dict()

        necesidades = self._extraer_necesidades_evento(evento)
        predicciones = []
        compras_generadas = []
        avisos = []

        for necesidad in necesidades:
            pred = self.core.stock.predecir_necesidad(
                nombre=necesidad["nombre"],
                cantidad_necesaria=necesidad["cantidad"],
                unidad=necesidad["unidad"],
                articulo_id=necesidad.get("articulo_id", "") or necesidad.get("receta_id", ""),
            )
            predicciones.append(pred)
            if pred["estado"] != "ok":
                avisos.append(pred["lectura_host_ai"])
                if generar_compras:
                    compra = self.core.compras.registrar_necesidad(
                        nombre=necesidad["nombre"],
                        cantidad=pred["cantidad_faltante"],
                        unidad=necesidad["unidad"],
                        familia=necesidad.get("familia", "produccion_evento"),
                        proveedor_preferente=necesidad.get("proveedor_preferente", "Sin proveedor asignado"),
                        motivo=f"Faltante para evento {evento.get('nombre')}",
                        prioridad=necesidad.get("prioridad", 85),
                        articulo_id=necesidad.get("articulo_id", "") or necesidad.get("receta_id", ""),
                    )
                    compras_generadas.append(compra.to_dict())

        simulacion = self.core.simulador_produccion_evento.simular_evento(evento, hora_inicio_produccion, int(margen_seguridad_min))
        avisos.extend(simulacion.get("avisos", []))

        informe = InformeProduccionCompleta(
            evento_id=evento_id,
            evento=evento.get("nombre", ""),
            necesidades=necesidades,
            predicciones_stock=predicciones,
            compras_generadas=compras_generadas,
            simulacion=simulacion,
            estado="revisar" if avisos else "ok",
            avisos=avisos,
        )
        self.informes[informe.id] = informe
        return {**informe.to_dict(), "lectura_host_ai": self._lectura(informe)}

    def generar_pedidos_desde_evento(self, evento_id: str) -> Dict[str, Any]:
        if not any(i.evento_id == evento_id for i in self.informes.values()):
            self.analizar_evento(evento_id, generar_compras=True)
        return self.core.compras.generar_pedidos_sugeridos()

    def listar_informes(self) -> List[Dict[str, Any]]:
        return [i.to_dict() for i in self.informes.values()]

    def _extraer_necesidades_evento(self, evento: Dict[str, Any]) -> List[Dict[str, Any]]:
        if hasattr(self.core, "escandallos_inteligente"):
            calculo = self.core.escandallos_inteligente.calcular_necesidades_evento(evento)
            if calculo.get("necesidades_agregadas"):
                salida = []
                for item in calculo["necesidades_agregadas"]:
                    salida.append({
                        "receta_id": item.get("receta_id", item.get("articulo_id", "")),
                        "nombre": item["nombre"],
                        "cantidad": item["cantidad_bruta"],
                        "unidad": item["unidad"],
                        "origen": "escandallo_evento",
                        "pase": "",
                        "prioridad": 90,
                        "articulo_id": item.get("articulo_id", ""),
                        "familia": item.get("familia", "produccion_evento"),
                        "proveedor_preferente": item.get("proveedor_preferente", "Sin proveedor asignado"),
                        "coste_estimado": item.get("coste_estimado", 0.0),
                    })
                return salida

        # Fallback antiguo si no hay escandallos.
        necesidades = []
        pax = int(evento.get("pax", 0) or 0)
        factor = max(1.0, pax / 10.0)
        for servicio in evento.get("servicios", []):
            for pase in servicio.get("pases", []):
                for receta_id in pase.get("recetas", []):
                    nombre = self._nombre_desde_receta_id(receta_id)
                    necesidades.append(NecesidadProduccion(
                        receta_id=receta_id,
                        nombre=nombre,
                        cantidad=round(factor, 2),
                        unidad="ud",
                        origen="evento",
                        pase=pase.get("nombre", ""),
                        prioridad=85,
                    ).to_dict())
        return necesidades

    def _nombre_desde_receta_id(self, receta_id: str) -> str:
        limpio = receta_id.replace("REC-", "").replace("_", " ").replace("-", " ").strip()
        return limpio.title() if limpio else receta_id

    def _lectura(self, informe: InformeProduccionCompleta) -> str:
        if informe.avisos:
            return f"Producción completa analizada para '{informe.evento}' con {len(informe.avisos)} avisos y {len(informe.compras_generadas)} compras generadas."
        return f"Producción completa analizada para '{informe.evento}' sin avisos críticos."
