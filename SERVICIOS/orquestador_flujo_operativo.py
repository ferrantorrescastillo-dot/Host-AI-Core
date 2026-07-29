from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

from SERVICIOS.confirmaciones_inteligentes_5412 import interpretar_confirmacion_contextual_5412, registrar_confirmacion_accion_5412
from SERVICIOS.continuador_flujo_5411 import acciones_seleccionables, interpretar_seleccion, seleccionar_accion_en_flujo_5411
from SERVICIOS.ejecutor_flujo_operativo_532 import ejecutar_flujo_operativo
from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento
from SERVICIOS.modelo_flujo_operativo import cancelar_flujo
from SERVICIOS.repositorio_flujos_json import RepositorioFlujosJSON


class OrquestadorFlujoOperativo:
    """Coordinador incremental del workflow operativo 5.3.1 -> 5.4.11 -> 5.4.12 -> 5.3.2."""

    VERSION = "1.0"

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self.repo = RepositorioFlujosJSON(self.base_dir)

    def iniciar_flujo_operativo(self, datos_evento: Dict[str, Any]) -> Dict[str, Any]:
        generado = generar_flujo_operativo_evento(datos_evento)
        if not generado.get("ok"):
            return {
                "ok": False,
                "estado": generado.get("estado", "flujo_no_generado"),
                "mensaje": generado.get("mensaje", "No se pudo generar flujo."),
                "flujo": generado.get("flujo"),
                "pasos": generado.get("pasos", []),
                "datos": generado.get("datos", {}),
            }
        return {
            "ok": True,
            "estado": "flujo_iniciado",
            "mensaje": "Flujo operativo iniciado en modo seguro.",
            "flujo": deepcopy(generado.get("flujo")),
            "pasos": deepcopy(generado.get("pasos") or []),
            "datos": deepcopy(generado.get("datos") or {}),
        }

    def seleccionar_accion_en_flujo(self, texto: str, flujo: Dict[str, Any]) -> Dict[str, Any]:
        return seleccionar_accion_en_flujo_5411(texto, flujo)

    def confirmar_accion_en_flujo(self, texto: str, flujo: Dict[str, Any]) -> Dict[str, Any]:
        estado_ctx = str(flujo.get("estado") or "")
        if estado_ctx == "esperando_confirmacion":
            estado_ctx = "esperando_confirmacion_especifica"
        contexto = {
            "estado_conversacion": estado_ctx,
            "confirmaciones": {"acciones_con_confirmacion": acciones_seleccionables({"flujo": flujo})},
            "accion_seleccionada": deepcopy(flujo.get("accion_seleccionada")),
            "flujo": deepcopy(flujo),
        }
        interpretada = interpretar_confirmacion_contextual_5412(texto, contexto)
        if not interpretada.get("gestionado"):
            return {
                "ok": False,
                "estado": "confirmacion_no_entendida",
                "mensaje": "No se pudo interpretar la confirmación en el flujo activo.",
                "flujo": deepcopy(flujo),
                "interpretacion": interpretada,
            }

        tipo = str(interpretada.get("tipo") or "")
        if tipo in {"confirmar_accion", "seleccionar_y_confirmar"}:
            accion = interpretada.get("accion") or flujo.get("accion_seleccionada")
            if not accion:
                return {
                    "ok": False,
                    "estado": "sin_accion_seleccionada",
                    "mensaje": "No hay acción seleccionada para confirmar.",
                    "flujo": deepcopy(flujo),
                }
            resultado = registrar_confirmacion_accion_5412({"flujo": flujo}, accion, True)
            return {
                "ok": bool(resultado.get("ok")),
                "estado": "confirmacion_aplicada" if resultado.get("ok") else resultado.get("estado", "confirmacion_error"),
                "mensaje": "Confirmación registrada en el flujo." if resultado.get("ok") else resultado.get("mensaje", "No se pudo registrar la confirmación."),
                "flujo": deepcopy(resultado.get("flujo") or flujo),
                "paso": deepcopy(resultado.get("paso")),
                "interpretacion": interpretada,
            }

        if tipo in {"rechazar_accion", "cancelar_accion"}:
            accion = interpretada.get("accion") or flujo.get("accion_seleccionada")
            if not accion:
                return {
                    "ok": False,
                    "estado": "sin_accion_seleccionada",
                    "mensaje": "No hay acción seleccionada para rechazar.",
                    "flujo": deepcopy(flujo),
                }
            resultado = registrar_confirmacion_accion_5412({"flujo": flujo}, accion, False)
            return {
                "ok": bool(resultado.get("ok")),
                "estado": "rechazo_aplicado" if resultado.get("ok") else resultado.get("estado", "rechazo_error"),
                "mensaje": "Rechazo registrado en el flujo." if resultado.get("ok") else resultado.get("mensaje", "No se pudo registrar el rechazo."),
                "flujo": deepcopy(resultado.get("flujo") or flujo),
                "paso": deepcopy(resultado.get("paso")),
                "interpretacion": interpretada,
            }

        if tipo == "cancelar_flujo":
            cancelado = cancelar_flujo(flujo, motivo="cancelado_por_confirmacion")
            return {
                "ok": bool(cancelado.get("ok")),
                "estado": cancelado.get("estado", "flujo_cancelado"),
                "mensaje": "Flujo cancelado por el usuario.",
                "flujo": deepcopy(cancelado.get("flujo") or flujo),
                "interpretacion": interpretada,
            }

        if tipo in {"abrir_seleccion", "volver_seleccion"}:
            copia = deepcopy(flujo)
            copia["estado"] = "esperando_seleccion"
            return {
                "ok": True,
                "estado": "esperando_seleccion",
                "mensaje": "Puedes seleccionar una acción del flujo activo.",
                "flujo": copia,
                "interpretacion": interpretada,
            }

        return {
            "ok": False,
            "estado": "confirmacion_no_aplicable",
            "mensaje": "La confirmación interpretada no aplica sobre el flujo activo.",
            "flujo": deepcopy(flujo),
            "interpretacion": interpretada,
        }

    def ejecutar_paso_seguro(self, flujo: Dict[str, Any], codigo_paso: Optional[str] = None) -> Dict[str, Any]:
        resultado = ejecutar_flujo_operativo(
            flujo,
            confirmar=True,
            codigo_paso=codigo_paso,
            contexto={"base_dir": str(self.base_dir)},
        )
        return {
            "ok": bool(resultado.get("ok")),
            "estado": resultado.get("estado", "ejecucion_finalizada"),
            "mensaje": resultado.get("mensaje", ""),
            "flujo": deepcopy(resultado.get("flujo") or flujo),
            "paso": deepcopy(resultado.get("paso")),
            "resultados": deepcopy(resultado.get("resultados") or []),
        }

    def ejecutar_flujo_seguro(self, flujo: Dict[str, Any], confirmar: bool = False, codigo_paso: Optional[str] = None) -> Dict[str, Any]:
        """Wrapper canónico de ejecución 5.3.2 en modo seguro."""
        resultado = ejecutar_flujo_operativo(
            flujo,
            confirmar=confirmar,
            codigo_paso=codigo_paso,
            contexto={"base_dir": str(self.base_dir)},
        )
        return {
            "ok": bool(resultado.get("ok")),
            "estado": resultado.get("estado", "ejecucion_finalizada"),
            "mensaje": resultado.get("mensaje", ""),
            "confirmado": bool(resultado.get("confirmado", confirmar)),
            "flujo": deepcopy(resultado.get("flujo") or flujo),
            "paso": deepcopy(resultado.get("paso")),
            "resultados": deepcopy(resultado.get("resultados") or []),
            "pendientes_confirmacion": deepcopy(resultado.get("pendientes_confirmacion") or []),
            "modifico_datos_reales": bool(resultado.get("modifico_datos_reales", False)),
        }

    def cancelar_flujo_operativo(self, flujo: Dict[str, Any], motivo: str = "cancelado_por_usuario") -> Dict[str, Any]:
        """Cancelación canónica del flujo activo."""
        cancelado = cancelar_flujo(flujo, motivo=motivo, origen="orquestador_flujo_operativo")
        return {
            "ok": bool(cancelado.get("ok")),
            "estado": cancelado.get("estado", "flujo_cancelado"),
            "mensaje": cancelado.get("mensaje", "Flujo cancelado."),
            "flujo": deepcopy(cancelado.get("flujo") or flujo),
        }

    def guardar_flujo(self, flujo: Dict[str, Any], ruta: Optional[Path] = None, overwrite: bool = False) -> Dict[str, Any]:
        """Persistencia canónica del flujo para continuidad/reanudación."""
        guardado = self.repo.guardar(flujo, ruta=ruta, overwrite=overwrite)
        return {
            "ok": bool(guardado.get("ok")),
            "estado": guardado.get("estado", "guardado_error"),
            "mensaje": guardado.get("mensaje", ""),
            "ruta": guardado.get("ruta"),
            "flujo": deepcopy(guardado.get("flujo") or flujo),
        }

    def procesar_texto_en_flujo(self, texto: str, flujo: Dict[str, Any], base_dir: Optional[Path] = None) -> Dict[str, Any]:
        _ = base_dir  # compatibilidad de firma
        seleccion = self.seleccionar_accion_en_flujo(texto, flujo)
        if seleccion.get("ok"):
            return seleccion

        confirmado = self.confirmar_accion_en_flujo(texto, flujo)
        if confirmado.get("ok"):
            return confirmado

        return {
            "ok": False,
            "estado": "texto_no_gestionado_en_flujo",
            "mensaje": "No se pudo interpretar el texto en el contexto del flujo activo.",
            "flujo": deepcopy(flujo),
        }

    def reanudar_flujo_desde_archivo(self, ruta: Optional[Path] = None, id_flujo: Optional[str] = None) -> Dict[str, Any]:
        cargado = self.repo.cargar(ruta=ruta, id_flujo=id_flujo)
        return {
            "ok": bool(cargado.get("ok")),
            "estado": cargado.get("estado", "carga_error"),
            "mensaje": cargado.get("mensaje", "Flujo cargado." if cargado.get("ok") else "No se pudo cargar el flujo."),
            "flujo": deepcopy(cargado.get("flujo")),
            "ruta": cargado.get("ruta"),
        }


__all__ = ["OrquestadorFlujoOperativo"]
