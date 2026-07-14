from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from SERVICIOS.clasificador_intenciones_503 import ClasificadorIntenciones503
from SERVICIOS.integracion_nucleo_ia_505 import ChatHostAIIntegrado505


@dataclass
class PasoOrquestacion51:
    orden: int
    modulo: str
    accion: str
    estado: str = "pendiente"
    detalle: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OrquestadorInteligente51:
    """
    Host AI 5.1 - Orquestador Inteligente.

    Convierte una petición natural en un flujo de trabajo con varios motores.
    No duplica la lógica de los módulos 4.x/5.0: clasifica la intención,
    decide pasos, llama al chat 5.0.5 para recepción segura y genera una
    respuesta unificada de jefe de cocina.
    """

    VERSION = "5.1.0"

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self.clasificador = ClasificadorIntenciones503()
        self.chat_recepcion = ChatHostAIIntegrado505(self.base_dir)
        self.contexto: Dict[str, Any] = {}
        self.historial: List[Dict[str, Any]] = []

    def procesar(self, texto: str) -> Dict[str, Any]:
        texto = (texto or "").strip()
        if not texto:
            return self._respuesta(False, "Escríbeme qué necesitas hacer.", "vacio", [], {})

        # Si hay una recepción esperando confirmación, no reclasificamos: la decisión pertenece al flujo pendiente.
        if self._hay_recepcion_pendiente():
            resp = self.chat_recepcion.responder(texto)
            self._sincronizar_contexto_recepcion()
            resultado = self._respuesta(
                bool(resp.get("ok")),
                resp.get("mensaje", ""),
                "recepcion_mercancia",
                [PasoOrquestacion51(1, "4.4.3", "Aplicar recepción confirmada", "ejecutado").to_dict()],
                {"respuesta_chat": resp},
            )
            self.historial.append({"texto": texto, "resultado": resultado})
            return resultado

        clasificacion = self.clasificador.clasificar(texto, self.contexto)
        intencion = clasificacion.get("intencion_ganadora", {}).get("intencion", "conversacion_general")
        confianza = float(clasificacion.get("intencion_ganadora", {}).get("confianza", 0.0) or 0.0)

        # Multi-intención: una frase puede pedir evento + producción + compras + rentabilidad.
        intenciones = self._detectar_intenciones_compuestas(texto, intencion, clasificacion)
        pasos = self._construir_plan(texto, intenciones)

        datos: Dict[str, Any] = {"clasificacion": clasificacion, "intenciones": intenciones}

        if intencion == "recepcion_mercancia" and confianza >= 0.55:
            resp = self.chat_recepcion.responder(texto)
            self._sincronizar_contexto_recepcion()
            datos["respuesta_chat"] = resp
            mensaje = resp.get("mensaje", "")
            resultado = self._respuesta(bool(resp.get("ok")), mensaje, intencion, pasos, datos)
        else:
            mensaje = self._generar_respuesta_operativa(texto, intenciones, pasos)
            resultado = self._respuesta(True, mensaje, intenciones[0] if intenciones else intencion, pasos, datos)

        self.historial.append({"texto": texto, "resultado": resultado})
        return resultado

    def _detectar_intenciones_compuestas(self, texto: str, intencion_base: str, clasificacion: Dict[str, Any]) -> List[str]:
        t = self.clasificador.normalizar(texto)
        intenciones: List[str] = []

        def add(nombre: str) -> None:
            if nombre not in intenciones:
                intenciones.append(nombre)

        if intencion_base and intencion_base != "conversacion_general":
            add(intencion_base)

        # Reglas de orquestación multi-motor. No sustituyen al clasificador; lo complementan.
        if any(p in t for p in ["boda", "evento", "catering", "banquete", "comunion"]):
            add("evento")
        if any(p in t for p in ["produccion", "producir", "preparar", "organiza", "organizar", "plan de trabajo", "cronograma", "elaboraciones", "adelantar"]):
            add("produccion")
        if any(p in t for p in ["comprar", "compra", "pedido", "pedir", "faltan", "falta", "que tengo que comprar"]):
            add("compras")
        if any(p in t for p in ["stock", "queda", "tengo suficiente", "existencias", "rotura", "almacen"]):
            add("stock")
        if any(p in t for p in ["coste", "margen", "rentabilidad", "beneficio", "precio", "merma", "financiero"]):
            add("rentabilidad")
        if any(p in t for p in ["han llegado", "ha llegado", "me han traido", "me ha traido", "recibido", "sube al almacen"]):
            add("recepcion_mercancia")

        # Si pide organizar un evento completo, se encadenan módulos aunque no los nombre todos.
        evento_completo = any(p in t for p in ["boda", "evento", "catering", "banquete"]) and any(p in t for p in ["organiza", "organizame", "preparar", "desde hoy", "hasta el servicio", "que tengo que hacer"])
        if evento_completo:
            for nombre in ["evento", "produccion", "stock", "compras", "rentabilidad"]:
                add(nombre)

        if not intenciones:
            add("conversacion_general")
        return intenciones

    def _construir_plan(self, texto: str, intenciones: List[str]) -> List[Dict[str, Any]]:
        pasos: List[PasoOrquestacion51] = []
        orden = 1

        def paso(modulo: str, accion: str, detalle: str = "") -> None:
            nonlocal orden
            pasos.append(PasoOrquestacion51(orden, modulo, accion, "planificado", detalle))
            orden += 1

        # Orden operativo real: evento -> producción -> stock -> compras -> rentabilidad -> respuesta.
        if "recepcion_mercancia" in intenciones:
            paso("4.4.1", "Interpretar recepción por texto", "extraer proveedor, producto, cantidad, unidad y precio")
            paso("4.4.2", "Validar líneas de recepción", "buscar artículos y crear borrador seguro")
            paso("4.4.3", "Aplicar stock solo con confirmación", "no modifica stock hasta que el usuario confirme")
            return [p.to_dict() for p in pasos]

        if "evento" in intenciones:
            paso("4.7.1", "Crear o localizar evento", "fecha, pax, cliente y estado")
            paso("4.7.2", "Analizar menú del evento", "servicios, pases y coste por persona")
        if "produccion" in intenciones or "evento" in intenciones:
            paso("4.6.1-4.6.4", "Planificar producción", "prioridades, cocineros y tiempos activos/pasivos")
            paso("4.6.5-4.6.8", "Revisar recursos y checklist", "hornos, abatidor, conflictos e informe diario")
        if "stock" in intenciones or "compras" in intenciones or "evento" in intenciones:
            paso("4.3", "Consultar stock disponible", "existencias, mínimos, roturas y artículos críticos")
        if "compras" in intenciones or "evento" in intenciones:
            paso("4.5/4.8", "Calcular necesidades de compra", "faltantes, proveedores y pedido sugerido")
        if "rentabilidad" in intenciones or "evento" in intenciones:
            paso("4.8", "Analizar coste y rentabilidad", "margen, precio recomendado y alertas")
        paso("5.1", "Respuesta unificada", "resumir acciones, riesgos y siguiente confirmación")
        return [p.to_dict() for p in pasos]

    def _generar_respuesta_operativa(self, texto: str, intenciones: List[str], pasos: List[Dict[str, Any]]) -> str:
        principal = intenciones[0] if intenciones else "conversacion_general"
        lineas: List[str] = []
        lineas.append("He analizado tu petición y he preparado un flujo operativo.")
        lineas.append(f"Intención principal: {self._nombre_intencion(principal)}")
        if len(intenciones) > 1:
            lineas.append("Módulos implicados: " + ", ".join(self._nombre_intencion(i) for i in intenciones))
        lineas.append("")
        lineas.append("Plan de trabajo:")
        for p in pasos[:8]:
            lineas.append(f"{p['orden']}. {p['accion']} ({p['modulo']})")

        if "evento" in intenciones and any(i in intenciones for i in ["produccion", "compras", "stock", "rentabilidad"]):
            lineas.append("")
            lineas.append("Resumen tipo jefe de cocina:")
            lineas.append("- Primero dejaría cerrado el evento: pax, hora, menú y restricciones.")
            lineas.append("- Después generaría producción y comprobaría stock antes de comprar.")
            lineas.append("- Finalmente revisaría coste/margen y pediría confirmación antes de crear pedidos reales.")
        elif principal == "compras":
            lineas.append("\nSiguiente paso: revisar stock mínimo, necesidades de producción/evento y proponer pedidos por proveedor.")
        elif principal == "produccion":
            lineas.append("\nSiguiente paso: convertir la petición en tareas por cocinero, prioridad y tiempos activos/pasivos.")
        elif principal == "stock":
            lineas.append("\nSiguiente paso: consultar existencias reales y detectar roturas o mínimos.")
        elif principal == "rentabilidad":
            lineas.append("\nSiguiente paso: calcular costes reales, margen y recomendaciones económicas.")
        else:
            lineas.append("\nNecesito un poco más de contexto para ejecutar un flujo completo con seguridad.")

        lineas.append("\nNo he modificado datos todavía. Esto es una orquestación segura previa a ejecutar acciones reales.")
        return "\n".join(lineas)

    def _sincronizar_contexto_recepcion(self) -> None:
        if self.chat_recepcion.contexto.get("borrador_recepcion"):
            self.contexto["borrador_recepcion"] = self.chat_recepcion.contexto["borrador_recepcion"]
        else:
            self.contexto.pop("borrador_recepcion", None)

    def _hay_recepcion_pendiente(self) -> bool:
        return bool(self.chat_recepcion.contexto.get("borrador_recepcion") or self.contexto.get("borrador_recepcion"))

    def _nombre_intencion(self, intencion: str) -> str:
        nombres = {
            "recepcion_mercancia": "Recepción de mercancía",
            "evento": "Eventos",
            "produccion": "Producción",
            "stock": "Stock",
            "compras": "Compras",
            "rentabilidad": "Rentabilidad",
            "conversacion_general": "Conversación general",
        }
        return nombres.get(intencion, intencion)

    def _respuesta(self, ok: bool, mensaje: str, intencion: str, pasos: List[Dict[str, Any]], datos: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ok": ok,
            "version": self.VERSION,
            "intencion": intencion,
            "mensaje": mensaje,
            "pasos": pasos,
            "datos": datos,
        }


__all__ = ["OrquestadorInteligente51", "PasoOrquestacion51"]
