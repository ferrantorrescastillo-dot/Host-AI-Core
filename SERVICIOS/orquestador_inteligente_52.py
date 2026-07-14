from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from SERVICIOS.gestor_datos_minimos_52 import GestorDatosMinimos52
from SERVICIOS.orquestador_inteligente_51 import OrquestadorInteligente51
from SERVICIOS.confirmacion_inteligente_534 import interpretar_confirmacion


class OrquestadorInteligente52:
    """
    Host AI 5.4.9 - Continuidad conversacional.

    Mantiene la recogida de datos mínimos del 5.2 y la orquestación 5.3,
    pero corrige el punto crítico detectado en prueba real: cuando el usuario
    responde "sí", "no" o "seleccionar" después de preparar un flujo, el sistema
    NO vuelve a clasificar desde cero como conversación general. Continúa el flujo
    activo con el contexto del evento.
    """

    VERSION = "5.5.6E.3.3"

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self.gestor_datos = GestorDatosMinimos52()
        self.orquestador_51 = OrquestadorInteligente51(self.base_dir)
        self.contexto_activo_549: Dict[str, Any] = {}
        self.contexto_ingesta_receta_556e32: Dict[str, Any] = {}
        self.contexto_post_ficha_556e33: Dict[str, Any] = {}

    def procesar(self, texto: str) -> Dict[str, Any]:
        texto = (texto or "").strip()

        # 5.5.6E.3.3: continuidad tras guardar una ficha y planificación guiada.
        gestion_post_ficha = self._procesar_post_ficha_556e33(texto)
        if gestion_post_ficha is not None:
            return gestion_post_ficha

        # 5.5.6E.3.2: ingesta conversacional de recetas/procesos reales.
        gestion_ingesta = self._procesar_ingesta_receta_556e32(texto)
        if gestion_ingesta is not None:
            return gestion_ingesta

        # 5.5.6: genera producción preliminar desde escandallos reales.
        from SERVICIOS.conector_produccion_real_556 import procesar_consulta_produccion_real_556
        consulta_produccion = procesar_consulta_produccion_real_556(texto, self.base_dir)
        if consulta_produccion.get("gestionado"):
            return consulta_produccion

        # 5.5.5: consulta escandallos y recetas reales antes de búsquedas genéricas.
        from SERVICIOS.conector_escandallos_real_555 import procesar_consulta_escandallos_real_555
        consulta_escandallo = procesar_consulta_escandallos_real_555(texto, self.base_dir)
        if consulta_escandallo.get("gestionado"):
            return consulta_escandallo

        # 5.5.4: resuelve proveedores asociados a artículos antes de la búsqueda genérica.
        from SERVICIOS.conector_proveedores_real_554 import procesar_consulta_proveedores_real_554
        consulta_proveedor = procesar_consulta_proveedores_real_554(texto, self.base_dir)
        if consulta_proveedor.get("gestionado"):
            return consulta_proveedor

        # 5.5.3: consulta stock real antes del orquestador genérico de stock.
        from SERVICIOS.conector_stock_real_553 import procesar_consulta_stock_real_553
        consulta_stock = procesar_consulta_stock_real_553(texto, self.base_dir)
        if consulta_stock.get("gestionado"):
            return consulta_stock

        # 5.5.2: las consultas de datos reales tienen prioridad sobre el fallback
        # conversacional y se resuelven en modo solo lectura.
        from SERVICIOS.consultas_datos_conversacionales_552 import procesar_consulta_datos_552
        consulta_datos = procesar_consulta_datos_552(texto, self.base_dir)
        if consulta_datos.get("gestionado"):
            return consulta_datos

        # 5.4.9: si hay un flujo pendiente de confirmación, primero interpretamos
        # la respuesta como confirmación. Evita que "sí" se clasifique como charla.
        if self._hay_flujo_pendiente_confirmacion():
            confirmacion = interpretar_confirmacion(texto)
            if confirmacion.get("tipo") != "desconocido":
                return self._procesar_confirmacion_flujo(confirmacion, texto)

        # Si es evento o hay evento pendiente, validamos datos mínimos.
        datos_evento = self.gestor_datos.procesar(texto)
        if datos_evento.get("gestionado"):
            if datos_evento.get("estado") == "datos_completos":
                return self._procesar_evento_completo(datos_evento)
            return {
                "ok": bool(datos_evento.get("ok", True)),
                "version": self.VERSION,
                "intencion": "evento",
                "estado": datos_evento.get("estado"),
                "mensaje": datos_evento.get("mensaje", ""),
                "datos": {"datos_minimos": datos_evento},
                "pasos": [],
            }

        # Para el resto de flujos, reutilizamos 5.1 sin duplicar lógica.
        respuesta = self.orquestador_51.procesar(texto)
        respuesta["version"] = self.VERSION
        return respuesta

    def _procesar_ingesta_receta_556e32(self, texto: str) -> Optional[Dict[str, Any]]:
        from SERVICIOS.ingesta_recetas_lenguaje_natural_556e32 import AnalizadorRecetasLenguajeNatural556E32

        analizador = AnalizadorRecetasLenguajeNatural556E32(self.base_dir)
        t = texto.strip().lower()

        if self.contexto_ingesta_receta_556e32.get("propuesta"):
            if t in {"confirma la ficha de produccion", "confirma la ficha de producción", "confirmar ficha", "confirmo la ficha"}:
                resultado = analizador.guardar_confirmado(self.contexto_ingesta_receta_556e32["propuesta"])
                self.contexto_ingesta_receta_556e32.clear()
                receta_guardada = str((resultado.get("ficha") or {}).get("receta") or "").strip()
                self.contexto_post_ficha_556e33 = {
                    "estado": "ESPERANDO_CONFIRMACION_PLANIFICAR",
                    "receta": receta_guardada,
                }
                mensaje = resultado.get("mensaje", "") + (
                    "\n\nSIGUIENTE DECISIÓN\n"
                    f"- ¿Quieres que planifique ahora '{receta_guardada}'?\n"
                    "- Responde 'sí' para continuar o 'no' para dejarlo guardado."
                )
                return {"ok": bool(resultado.get("datos_reales_modificados")), "version": "5.5.6E.3.3", "intencion": "ingesta_receta", "estado": "FICHA_GUARDADA_ESPERANDO_PLANIFICACION", "mensaje": mensaje, "datos": resultado, "pasos": []}
            if t in {"cancela la ficha de produccion", "cancela la ficha de producción", "cancelar ficha"}:
                self.contexto_ingesta_receta_556e32.clear()
                return {"ok": True, "version": "5.5.6E.3.2", "intencion": "ingesta_receta", "estado": "PROPUESTA_CANCELADA", "mensaje": "Ficha de producción cancelada. No se han modificado datos reales.", "datos": {}, "pasos": []}

        if self.contexto_ingesta_receta_556e32.get("capturando"):
            if t in {"fin", "terminar", "analizar"}:
                ctx = dict(self.contexto_ingesta_receta_556e32)
                texto_receta = "\n".join(ctx.get("lineas", []))
                resultado = analizador.analizar(ctx["receta"], texto_receta, ctx.get("rendimiento_base", 1), ctx.get("unidad_rendimiento", "u"))
                if resultado.get("ok"):
                    self.contexto_ingesta_receta_556e32 = {"propuesta": resultado["ficha"]}
                else:
                    self.contexto_ingesta_receta_556e32.clear()
                return {"ok": bool(resultado.get("ok")), "version": "5.5.6E.3.2", "intencion": "ingesta_receta", "estado": resultado.get("estado"), "mensaje": resultado.get("mensaje", ""), "datos": resultado, "pasos": []}
            self.contexto_ingesta_receta_556e32.setdefault("lineas", []).append(texto)
            return {"ok": True, "version": "5.5.6E.3.2", "intencion": "ingesta_receta", "estado": "CAPTURANDO_RECETA", "mensaje": "Texto añadido. Sigue pegando la receta o escribe FIN para analizarla.", "datos": {"lineas": len(self.contexto_ingesta_receta_556e32.get("lineas", []))}, "pasos": []}

        if analizador.es_inicio_ingesta(texto):
            receta = analizador.extraer_nombre_objetivo(texto)
            inline = analizador.extraer_texto_inline(texto)
            if not receta:
                return {"ok": False, "version": "5.5.6E.3.2", "intencion": "ingesta_receta", "estado": "FALTA_NOMBRE_RECETA", "mensaje": "Indica el nombre, por ejemplo: Registra esta receta para Ensaladilla de gamba", "datos": {}, "pasos": []}
            if inline:
                resultado = analizador.analizar(receta, inline)
                if resultado.get("ok"):
                    self.contexto_ingesta_receta_556e32 = {"propuesta": resultado["ficha"]}
                return {"ok": bool(resultado.get("ok")), "version": "5.5.6E.3.2", "intencion": "ingesta_receta", "estado": resultado.get("estado"), "mensaje": resultado.get("mensaje", ""), "datos": resultado, "pasos": []}
            self.contexto_ingesta_receta_556e32 = {"capturando": True, "receta": receta, "lineas": []}
            return {"ok": True, "version": "5.5.6E.3.2", "intencion": "ingesta_receta", "estado": "ESPERANDO_TEXTO_RECETA", "mensaje": f"Pega ahora la receta/proceso real de {receta}. Puedes enviarla en varias líneas. Cuando termines, escribe FIN.", "datos": {"receta": receta}, "pasos": []}

        return None

    def _procesar_post_ficha_556e33(self, texto: str) -> Optional[Dict[str, Any]]:
        """Mantiene el hilo tras guardar una ficha y recoge el objetivo de producción."""
        if not self.contexto_post_ficha_556e33:
            return None

        import re
        import unicodedata

        def norm(value: str) -> str:
            v = str(value or "").strip().lower()
            v = "".join(c for c in unicodedata.normalize("NFD", v) if unicodedata.category(c) != "Mn")
            return re.sub(r"\s+", " ", v).strip(" .")

        def extraer_objetivo(value: str):
            m = re.search(r"(\d+(?:[.,]\d+)?)\s*(personas?|pax|raciones?|unidades?|uds?|u)?", norm(value))
            if not m:
                return None
            cantidad = float(m.group(1).replace(",", "."))
            unidad_raw = m.group(2) or "personas"
            unidad = "personas" if unidad_raw in {"persona", "personas", "pax"} else ("u" if unidad_raw in {"unidad", "unidades", "ud", "uds", "u"} else "raciones")
            coc = re.search(r"(?:con\s+)?(\d+)\s*cociner", norm(value))
            return cantidad, unidad, int(coc.group(1)) if coc else 3

        t = norm(texto)
        estado = self.contexto_post_ficha_556e33.get("estado")
        receta = self.contexto_post_ficha_556e33.get("receta")
        afirmativas = {"si", "sí", "vale", "adelante", "continua", "continúa", "planifica", "hazlo"}
        negativas = {"no", "ahora no", "dejalo", "déjalo", "cancelar", "salir"}

        if estado == "ESPERANDO_CONFIRMACION_PLANIFICAR":
            objetivo = extraer_objetivo(texto)
            if t in negativas:
                self.contexto_post_ficha_556e33.clear()
                return {"ok": True, "version": "5.5.6E.3.3", "intencion": "continuidad_planificacion", "estado": "PLANIFICACION_POSPUESTA", "mensaje": f"Perfecto. La ficha de '{receta}' queda guardada y no genero planning ahora.", "datos": {"receta": receta}, "pasos": []}
            if t in afirmativas and objetivo is None:
                self.contexto_post_ficha_556e33["estado"] = "ESPERANDO_OBJETIVO_PLANIFICACION"
                return {"ok": True, "version": "5.5.6E.3.3", "intencion": "continuidad_planificacion", "estado": "ESPERANDO_OBJETIVO", "mensaje": f"Perfecto. ¿Para cuántas personas, raciones o unidades quieres planificar '{receta}'? Puedes añadir el equipo, por ejemplo: '150 personas con 3 cocineros'.", "datos": {"receta": receta}, "pasos": []}
            if objetivo is not None:
                return self._generar_plan_post_ficha_556e33(receta, *objetivo)
            return {"ok": False, "version": "5.5.6E.3.3", "intencion": "continuidad_planificacion", "estado": "RESPUESTA_NO_ENTENDIDA", "mensaje": "Responde 'sí' para planificar ahora o 'no' para dejar la ficha guardada.", "datos": {"receta": receta}, "pasos": []}

        if estado == "ESPERANDO_OBJETIVO_PLANIFICACION":
            if t in negativas:
                self.contexto_post_ficha_556e33.clear()
                return {"ok": True, "version": "5.5.6E.3.3", "intencion": "continuidad_planificacion", "estado": "PLANIFICACION_CANCELADA", "mensaje": f"De acuerdo. La ficha de '{receta}' sigue guardada y no genero planning.", "datos": {"receta": receta}, "pasos": []}
            objetivo = extraer_objetivo(texto)
            if objetivo is None:
                return {"ok": False, "version": "5.5.6E.3.3", "intencion": "continuidad_planificacion", "estado": "FALTA_OBJETIVO", "mensaje": "Indica una cantidad, por ejemplo: '150 personas con 3 cocineros'.", "datos": {"receta": receta}, "pasos": []}
            return self._generar_plan_post_ficha_556e33(receta, *objetivo)

        self.contexto_post_ficha_556e33.clear()
        return None

    def _generar_plan_post_ficha_556e33(self, receta: str, objetivo: float, unidad: str, cocineros: int) -> Dict[str, Any]:
        from SERVICIOS.motor_planificacion_recetas_reales_556e31 import (
            MotorPlanificacionRecetasReales556E31,
            formatear_plan_real_556e31,
        )
        resultado = MotorPlanificacionRecetasReales556E31(self.base_dir).planificar(
            receta, objetivo, unidad, cocineros, "08:00", "15:30"
        )
        self.contexto_post_ficha_556e33.clear()
        return {
            "ok": bool(resultado.get("puede_planificar")),
            "version": "5.5.6E.3.3",
            "intencion": "planificacion_receta_real",
            "estado": resultado.get("estado"),
            "mensaje": formatear_plan_real_556e31(resultado),
            "datos": resultado,
            "pasos": resultado.get("tareas", []),
        }

    def _hay_flujo_pendiente_confirmacion(self) -> bool:
        return bool(self.contexto_activo_549.get("flujo_pendiente_confirmacion"))

    def _normalizar_evento_para_flujo(self, evento: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "tipo": evento.get("tipo_evento") or evento.get("tipo") or "evento",
            "personas": evento.get("pax") or evento.get("personas"),
            "fecha": evento.get("fecha"),
            "hora_servicio": evento.get("hora_servicio"),
            "menu": evento.get("tipo_menu") or evento.get("menu"),
            "lugar": evento.get("lugar"),
            "restricciones": evento.get("restricciones"),
            "objetivo": evento.get("objetivo") or "flujo completo",
        }

    def _procesar_evento_completo(self, datos_evento: Dict[str, Any]) -> Dict[str, Any]:
        from SERVICIOS.generador_flujo_operativo_531 import generar_flujo_operativo_evento
        from SERVICIOS.ejecutor_flujo_operativo_532 import ejecutar_flujo_operativo
        from SERVICIOS.respuesta_ejecutiva_533 import generar_respuesta_ejecutiva_evento
        from SERVICIOS.confirmacion_inteligente_534 import analizar_confirmaciones_flujo

        evento = datos_evento.get("evento") or {}
        datos_flujo = self._normalizar_evento_para_flujo(evento)
        flujo = generar_flujo_operativo_evento(datos_flujo)
        ejecucion = ejecutar_flujo_operativo(flujo, confirmar=False)
        respuesta_ejecutiva = generar_respuesta_ejecutiva_evento(flujo, ejecucion)
        confirmaciones = analizar_confirmaciones_flujo(flujo, ejecucion)

        self.contexto_activo_549 = {
            "flujo_pendiente_confirmacion": True,
            "datos_evento": datos_evento,
            "evento": evento,
            "datos_flujo": datos_flujo,
            "flujo": flujo,
            "ejecucion_previa": ejecucion,
            "respuesta_ejecutiva": respuesta_ejecutiva,
            "confirmaciones": confirmaciones,
        }

        mensaje = "\n\n".join(
            parte for parte in [
                respuesta_ejecutiva.get("mensaje", ""),
                confirmaciones.get("mensaje", ""),
                "CONTINUIDAD 5.4.9\n- Si respondes 'sí', continuaré este mismo flujo sin reclasificar la conversación desde cero."
            ] if parte
        )

        return {
            "ok": True,
            "version": self.VERSION,
            "intencion": "evento",
            "estado": "flujo_evento_preparado_pendiente_confirmacion",
            "mensaje": mensaje,
            "datos": {
                "datos_minimos": datos_evento,
                "flujo": flujo,
                "ejecucion": ejecucion,
                "respuesta_ejecutiva": respuesta_ejecutiva,
                "confirmaciones": confirmaciones,
                "contexto_activo": True,
            },
            "pasos": flujo.get("pasos", []),
        }

    def _procesar_confirmacion_flujo(self, confirmacion: Dict[str, Any], texto_original: str) -> Dict[str, Any]:
        tipo = confirmacion.get("tipo")

        if tipo == "cancelar":
            evento = self.contexto_activo_549.get("datos_flujo", {})
            self.contexto_activo_549.clear()
            return {
                "ok": True,
                "version": self.VERSION,
                "intencion": "confirmacion_flujo",
                "estado": "flujo_cancelado",
                "mensaje": self._mensaje_cancelacion(evento),
                "datos": {"confirmacion": confirmacion},
                "pasos": [],
            }

        if tipo == "seleccionar":
            return {
                "ok": True,
                "version": self.VERSION,
                "intencion": "confirmacion_flujo",
                "estado": "seleccion_acciones_pendiente",
                "mensaje": self._mensaje_seleccionar_acciones(),
                "datos": {"confirmacion": confirmacion, "contexto_activo": self.contexto_activo_549},
                "pasos": self.contexto_activo_549.get("flujo", {}).get("pasos", []),
            }

        if tipo == "confirmar_todo":
            return self._continuar_flujo_confirmado(confirmacion)

        return {
            "ok": False,
            "version": self.VERSION,
            "intencion": "confirmacion_flujo",
            "estado": "confirmacion_no_entendida",
            "mensaje": "No he entendido la confirmación. Responde 'sí', 'no' o 'seleccionar'.",
            "datos": {"confirmacion": confirmacion, "texto": texto_original},
            "pasos": [],
        }

    def _continuar_flujo_confirmado(self, confirmacion: Dict[str, Any]) -> Dict[str, Any]:
        from SERVICIOS.ejecutor_flujo_operativo_532 import ejecutar_flujo_operativo

        flujo = self.contexto_activo_549.get("flujo") or {}
        datos_flujo = self.contexto_activo_549.get("datos_flujo") or {}
        ejecucion = ejecutar_flujo_operativo(flujo, confirmar=True)

        mensaje = self._mensaje_flujo_confirmado(datos_flujo, flujo, ejecucion)
        self.contexto_activo_549.clear()

        return {
            "ok": True,
            "version": self.VERSION,
            "intencion": "confirmacion_flujo",
            "estado": "flujo_confirmado_continuado",
            "mensaje": mensaje,
            "datos": {
                "confirmacion": confirmacion,
                "flujo": flujo,
                "ejecucion": ejecucion,
                "modifico_datos_reales": ejecucion.get("modifico_datos_reales", False),
            },
            "pasos": flujo.get("pasos", []),
        }

    def _mensaje_flujo_confirmado(self, evento: Dict[str, Any], flujo: Dict[str, Any], ejecucion: Dict[str, Any]) -> str:
        resultados = ejecucion.get("resultados", [])
        pendientes = ejecucion.get("pendientes_confirmacion", [])

        lineas = []
        lineas.append("Perfecto. Mantengo el contexto de la boda y continúo el flujo preparado.")
        lineas.append("")
        lineas.append("CONTINUIDAD CONVERSACIONAL 5.4.9")
        lineas.append("- No he vuelto a clasificar tu 'sí' como conversación general.")
        lineas.append("- He usado el evento activo y el flujo que ya estaba preparado.")
        lineas.append("- Sigo en modo seguro: no modifico datos reales sin confirmaciones específicas del jefe de cocina.")
        lineas.append("")
        lineas.append("EVENTO ACTIVO")
        lineas.append(f"- Tipo: {evento.get('tipo')}")
        lineas.append(f"- Personas: {evento.get('personas')}")
        lineas.append(f"- Fecha: {evento.get('fecha')}")
        lineas.append(f"- Hora servicio: {evento.get('hora_servicio')}")
        lineas.append(f"- Menú: {evento.get('menu')}")
        lineas.append(f"- Lugar: {evento.get('lugar')}")
        lineas.append("")
        lineas.append("EJECUCIÓN DEL FLUJO")
        lineas.append(f"- Pasos revisados: {len(resultados)}")
        lineas.append(f"- Acciones críticas todavía protegidas: {len(pendientes)}")
        lineas.append("- Datos reales modificados: NO")
        lineas.append("")
        lineas.append("SIGUIENTE PASO PROFESIONAL")
        lineas.append("- Consultar inventario activo.")
        lineas.append("- Asociar el menú real existente en escandallos/recetas.")
        lineas.append("- Preparar compras reales solo cuando stock, proveedores y precios estén verificados.")
        lineas.append("- Si quieres aplicar una acción concreta, responde 'seleccionar' y eliges qué confirmar.")
        return "\n".join(lineas)

    def _mensaje_cancelacion(self, evento: Dict[str, Any]) -> str:
        return (
            "Perfecto, cancelo la ejecución del flujo activo.\n\n"
            "No he modificado datos reales.\n"
            "Mantengo la recomendación profesional: antes de continuar, revisaría menú real, stock y compras disponibles."
        )

    def _mensaje_seleccionar_acciones(self) -> str:
        confirmaciones = self.contexto_activo_549.get("confirmaciones") or {}
        acciones = confirmaciones.get("acciones_con_confirmacion", [])
        lineas = []
        lineas.append("Perfecto. Seleccionamos acciones concretas sin aplicar todo de golpe.")
        lineas.append("")
        lineas.append("ACCIONES PENDIENTES")
        for i, accion in enumerate(acciones, 1):
            marca = "CRÍTICA" if accion.get("modifica_datos") else "confirmar"
            lineas.append(f"{i}. [{marca}] {accion.get('nombre')}")
        lineas.append("")
        lineas.append("Responde con el número de la acción que quieres confirmar o escribe 'no' para cancelar.")
        return "\n".join(lineas)


__all__ = ["OrquestadorInteligente52"]
