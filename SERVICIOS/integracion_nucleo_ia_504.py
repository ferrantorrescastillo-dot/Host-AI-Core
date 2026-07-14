from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from SERVICIOS.clasificador_intenciones_503 import ClasificadorIntenciones503


def _to_dict(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if isinstance(obj, dict):
        return obj
    return obj


class ChatHostAIIntegrado504:
    """
    Host AI 5.0.4 - Integración real del Núcleo IA en conversación.

    Objetivo:
    - Usar el clasificador 5.0.3 desde una conversación real.
    - Enrutar recepción de mercancía hacia los motores 4.4.1 y 4.4.2.
    - Mantener el modo seguro: crea borrador, no modifica stock todavía.
    """

    VERSION = "5.0.4"

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self.clasificador = ClasificadorIntenciones503()
        self.contexto: Dict[str, Any] = {}
        self.historial: list[Dict[str, Any]] = []

    def responder(self, texto: str) -> Dict[str, Any]:
        texto = (texto or "").strip()
        if not texto:
            return self._respuesta(False, "Escríbeme qué necesitas hacer.", "vacio", {})

        clasificacion = self.clasificador.clasificar(texto, self.contexto)
        ganadora = clasificacion.get("intencion_ganadora", {})
        intencion = ganadora.get("intencion", "desconocida")
        confianza = float(ganadora.get("confianza", 0.0) or 0.0)

        if intencion == "recepcion_mercancia" and confianza >= 0.55:
            resultado = self._crear_borrador_recepcion(texto, clasificacion)
        elif intencion == "evento" and confianza >= 0.55:
            resultado = self._respuesta_evento(texto, clasificacion)
        elif intencion == "compras" and confianza >= 0.55:
            resultado = self._respuesta_compras(texto, clasificacion)
        elif intencion == "rentabilidad" and confianza >= 0.55:
            resultado = self._respuesta_rentabilidad(texto, clasificacion)
        elif intencion == "produccion" and confianza >= 0.55:
            resultado = self._respuesta_produccion(texto, clasificacion)
        else:
            resultado = self._respuesta(
                False,
                "Necesito un dato más o una petición más concreta. Puedo ayudarte con recepción, eventos, compras, producción, stock y rentabilidad.",
                intencion,
                {"clasificacion": clasificacion},
            )

        self.historial.append({"texto": texto, "resultado": resultado})
        return resultado

    def _crear_borrador_recepcion(self, texto: str, clasificacion: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from SERVICIOS.interprete_recepcion_texto_441 import InterpreteRecepcionTexto441
            from SERVICIOS.validador_recepcion_mercancia_442 import ValidadorRecepcionMercancia442

            interpretacion = InterpreteRecepcionTexto441().interpretar(texto)
            borrador = ValidadorRecepcionMercancia442().validar_lineas(
                texto_original=interpretacion.texto_original,
                proveedor_general=interpretacion.proveedor_general,
                lineas=interpretacion.lineas,
                mensajes_generales=list(getattr(interpretacion, "errores", [])),
            )

            interpretacion_d = _to_dict(interpretacion)
            borrador_d = _to_dict(borrador)
            lineas = borrador_d.get("lineas_validadas") or borrador_d.get("lineas") or []
            proveedor = interpretacion_d.get("proveedor_general") or "proveedor no confirmado"

            resumen_lineas = []
            for item in lineas[:5]:
                cantidad = item.get("cantidad", "?")
                unidad = item.get("unidad", "")
                producto = item.get("producto_texto") or item.get("nombre") or item.get("articulo") or "artículo"
                accion = item.get("accion_sugerida") or item.get("accion") or "revisar"
                resumen_lineas.append(f"- {cantidad} {unidad} de {producto} → {accion}")

            if not resumen_lineas:
                mensaje = (
                    "He detectado una recepción de mercancía, pero necesito artículo, cantidad y unidad para crear el borrador."
                )
            else:
                mensaje = (
                    "He detectado una recepción de mercancía y he creado un borrador seguro.\n"
                    f"Proveedor: {proveedor}\n"
                    + "\n".join(resumen_lineas)
                    + "\n\nNo he modificado stock todavía. El siguiente paso será confirmar y aplicar la recepción."
                )

            return self._respuesta(
                True,
                mensaje,
                "recepcion_mercancia",
                {
                    "clasificacion": clasificacion,
                    "interpretacion": interpretacion_d,
                    "borrador": borrador_d,
                    "requiere_confirmacion": True,
                    "stock_modificado": False,
                },
            )
        except Exception as exc:
            return self._respuesta(
                False,
                f"He detectado una recepción de mercancía, pero no he podido crear el borrador: {exc}",
                "recepcion_mercancia",
                {"clasificacion": clasificacion, "error": repr(exc)},
            )

    def _respuesta_evento(self, texto: str, clasificacion: Dict[str, Any]) -> Dict[str, Any]:
        return self._respuesta(
            True,
            "He detectado que hablas de un evento. Todavía mantengo este flujo en modo seguro: puedo crear/organizar el evento cuando conectemos el selector de motores 5.0.5.",
            "evento",
            {"clasificacion": clasificacion},
        )

    def _respuesta_compras(self, texto: str, clasificacion: Dict[str, Any]) -> Dict[str, Any]:
        return self._respuesta(
            True,
            "He detectado una consulta de compras. El siguiente paso será conectarla con stock, eventos y producción para decirte qué falta comprar.",
            "compras",
            {"clasificacion": clasificacion},
        )

    def _respuesta_rentabilidad(self, texto: str, clasificacion: Dict[str, Any]) -> Dict[str, Any]:
        return self._respuesta(
            True,
            "He detectado una consulta de rentabilidad. El siguiente paso será conectarla con los motores 4.8 para calcular márgenes reales.",
            "rentabilidad",
            {"clasificacion": clasificacion},
        )

    def _respuesta_produccion(self, texto: str, clasificacion: Dict[str, Any]) -> Dict[str, Any]:
        return self._respuesta(
            True,
            "He detectado una petición de producción. El siguiente paso será conectarla con planificación 4.6 y eventos 4.7.",
            "produccion",
            {"clasificacion": clasificacion},
        )

    def _respuesta(self, ok: bool, mensaje: str, intencion: str, datos: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ok": ok,
            "version": self.VERSION,
            "intencion": intencion,
            "mensaje": mensaje,
            "datos": datos,
        }


__all__ = ["ChatHostAIIntegrado504"]
