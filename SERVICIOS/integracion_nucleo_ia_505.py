from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import json
import re

from SERVICIOS.clasificador_intenciones_503 import ClasificadorIntenciones503


def _to_dict(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if isinstance(obj, dict):
        return obj
    return obj


class ChatHostAIIntegrado505:
    """
    Host AI 5.0.5 - Confirmación y aplicación segura de recepción.

    Mantiene el chat integrado 5.0.4 y añade:
    - memoria del último borrador de recepción;
    - confirmación explícita del usuario;
    - aplicación usando el motor 4.4.3;
    - limpieza básica de texto para proveedor/producto en frases reales.
    """

    VERSION = "5.0.5"
    CONFIRMACIONES = {"s", "si", "sí", "ok", "vale", "confirmar", "aplicar", "aplica", "registrar", "registra"}
    CANCELACIONES = {"n", "no", "cancelar", "cancela", "descartar", "descarta"}

    PROVEEDORES_CONOCIDOS = [
        "Makro", "Guzman", "Guzmán", "Disbesa", "Asia Food", "Comercial CBG", "La Sirena",
        "Bon Area", "BonÀrea", "Mercabarna", "Sosa", "Bidfood", "Transgourmet", "Frutas Plana",
    ]

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self.clasificador = ClasificadorIntenciones503()
        self.contexto: Dict[str, Any] = {}
        self.historial: list[Dict[str, Any]] = []

    def responder(self, texto: str) -> Dict[str, Any]:
        texto = (texto or "").strip()
        if not texto:
            return self._respuesta(False, "Escríbeme qué necesitas hacer.", "vacio", {})

        if self._hay_borrador_pendiente():
            decision = self._interpretar_confirmacion(texto)
            if decision == "confirmar":
                resultado = self._aplicar_recepcion_pendiente()
                self.historial.append({"texto": texto, "resultado": resultado})
                return resultado
            if decision == "cancelar":
                self.contexto.pop("borrador_recepcion", None)
                resultado = self._respuesta(True, "Recepción descartada. No he modificado stock.", "recepcion_mercancia", {"stock_modificado": False})
                self.historial.append({"texto": texto, "resultado": resultado})
                return resultado

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

            texto_preparado, proveedor_detectado = self._preparar_texto_recepcion(texto)
            interpretacion = InterpreteRecepcionTexto441().interpretar(texto_preparado)

            # Correcciones ligeras para lenguaje natural real.
            if proveedor_detectado and not interpretacion.proveedor_general:
                interpretacion.proveedor_general = proveedor_detectado
            for linea in interpretacion.lineas:
                linea.producto = self._limpiar_producto_chat(linea.producto, proveedor_detectado)
                if proveedor_detectado and not linea.proveedor:
                    linea.proveedor = proveedor_detectado

            ruta_articulos = self.base_dir / "DATOS" / "db" / "articulos.json"
            validador = ValidadorRecepcionMercancia442(str(ruta_articulos))
            borrador = validador.validar_lineas(
                texto_original=texto,
                proveedor_general=interpretacion.proveedor_general,
                lineas=interpretacion.lineas,
                mensajes_generales=list(getattr(interpretacion, "errores", [])),
            )

            ruta_borrador = self.base_dir / "DATOS" / "db" / "recepcion_borrador_4_4_2.json"
            ruta_borrador.parent.mkdir(parents=True, exist_ok=True)
            ruta_borrador.write_text(json.dumps(asdict(borrador), ensure_ascii=False, indent=2), encoding="utf-8")

            interpretacion_d = _to_dict(interpretacion)
            borrador_d = _to_dict(borrador)
            lineas = borrador_d.get("lineas_validadas") or []
            proveedor = interpretacion_d.get("proveedor_general") or proveedor_detectado or "proveedor no confirmado"

            resumen_lineas = []
            aplicables = 0
            revisar = 0
            pendientes = 0
            for item in lineas[:8]:
                cantidad = item.get("cantidad", "?")
                unidad = item.get("unidad", "")
                producto = item.get("producto_texto") or item.get("articulo_encontrado") or "artículo"
                accion = item.get("accion_sugerida") or "revisar"
                if accion == "entrada_stock":
                    aplicables += 1
                elif accion == "revisar_coincidencia":
                    revisar += 1
                elif accion == "crear_articulo_pendiente":
                    pendientes += 1
                resumen_lineas.append(f"- {cantidad} {unidad} de {producto} → {accion}")

            self.contexto["borrador_recepcion"] = {
                "ruta_borrador": str(ruta_borrador),
                "proveedor": proveedor,
                "lineas": lineas,
                "aplicables": aplicables,
                "revisar": revisar,
                "pendientes": pendientes,
            }

            if not resumen_lineas:
                mensaje = "He detectado una recepción, pero necesito artículo, cantidad y unidad para crear el borrador."
            else:
                mensaje = (
                    "He detectado una recepción de mercancía y he creado un borrador seguro.\n"
                    f"Proveedor: {proveedor}\n"
                    + "\n".join(resumen_lineas)
                    + "\n\nNo he modificado stock todavía."
                )
                if aplicables:
                    mensaje += "\n¿Quieres aplicar ahora las líneas seguras al stock? (S/N)"
                else:
                    mensaje += "\nNo hay líneas 100% seguras para aplicar. Revisa coincidencias o crea artículos pendientes antes de modificar stock."

            return self._respuesta(
                True,
                mensaje,
                "recepcion_mercancia",
                {
                    "clasificacion": clasificacion,
                    "interpretacion": interpretacion_d,
                    "borrador": borrador_d,
                    "requiere_confirmacion": bool(aplicables),
                    "stock_modificado": False,
                    "aplicables": aplicables,
                    "revisar": revisar,
                    "pendientes": pendientes,
                },
            )
        except Exception as exc:
            return self._respuesta(
                False,
                f"He detectado una recepción de mercancía, pero no he podido crear el borrador: {exc}",
                "recepcion_mercancia",
                {"clasificacion": clasificacion, "error": repr(exc)},
            )

    def _aplicar_recepcion_pendiente(self) -> Dict[str, Any]:
        pendiente = self.contexto.get("borrador_recepcion") or {}
        if not pendiente:
            return self._respuesta(False, "No tengo ninguna recepción pendiente de confirmar.", "recepcion_mercancia", {})

        try:
            from SERVICIOS.aplicador_recepcion_mercancia_443 import AplicadorRecepcionMercancia443

            aplicador = AplicadorRecepcionMercancia443(
                ruta_borrador=str(self.base_dir / "DATOS" / "db" / "recepcion_borrador_4_4_2.json"),
                ruta_stock=str(self.base_dir / "DATOS" / "db" / "stock_inicial.json"),
                ruta_movimientos=str(self.base_dir / "DATOS" / "db" / "stock_movimientos.json"),
                ruta_articulos=str(self.base_dir / "DATOS" / "db" / "articulos.json"),
            )
            resultado = aplicador.aplicar_y_exportar(
                ruta_json=str(self.base_dir / "DATOS" / "db" / "recepcion_aplicada_4_4_3.json"),
                ruta_txt=str(self.base_dir / "DATOS" / "db" / "recepcion_aplicada_4_4_3.txt"),
            )
            resultado_d = _to_dict(resultado)
            self.contexto.pop("borrador_recepcion", None)

            lineas_msg = []
            for linea in resultado_d.get("lineas", [])[:8]:
                estado = "OK" if linea.get("aplicada_stock") else "PENDIENTE"
                prod = linea.get("articulo") or linea.get("producto_texto") or "artículo"
                cant = linea.get("cantidad", "?")
                unidad = linea.get("unidad", "")
                linea_msg = f"- [{estado}] {prod}: {cant} {unidad}"
                if linea.get("precio_actualizado"):
                    linea_msg += " | precio actualizado"
                lineas_msg.append(linea_msg)

            mensaje = (
                "Recepción procesada.\n"
                f"Entradas de stock OK: {resultado_d.get('entradas_stock_ok', 0)}\n"
                f"Precios actualizados: {resultado_d.get('precios_actualizados', 0)}\n"
                f"Pendientes artículo nuevo: {resultado_d.get('pendientes_articulo_nuevo', 0)}\n"
                f"Omitidas por revisión: {resultado_d.get('omitidas_revision', 0)}\n"
                f"Errores: {resultado_d.get('errores', 0)}\n"
                + ("\n" + "\n".join(lineas_msg) if lineas_msg else "")
            )
            if resultado_d.get("entradas_stock_ok", 0) == 0:
                mensaje += "\n\nNo he sumado stock porque no había ninguna coincidencia segura."
            return self._respuesta(
                True,
                mensaje,
                "recepcion_mercancia",
                {"resultado_aplicacion": resultado_d, "stock_modificado": resultado_d.get("entradas_stock_ok", 0) > 0},
            )
        except Exception as exc:
            return self._respuesta(False, f"No he podido aplicar la recepción: {exc}", "recepcion_mercancia", {"error": repr(exc), "stock_modificado": False})

    def _hay_borrador_pendiente(self) -> bool:
        return bool(self.contexto.get("borrador_recepcion"))

    def _interpretar_confirmacion(self, texto: str) -> Optional[str]:
        limpio = self._normalizar_simple(texto)
        if limpio in self.CONFIRMACIONES:
            return "confirmar"
        if limpio in self.CANCELACIONES:
            return "cancelar"
        return None

    def _preparar_texto_recepcion(self, texto: str) -> Tuple[str, Optional[str]]:
        proveedor = self._detectar_proveedor_conocido(texto)
        preparado = texto
        # "25 kg de arroz" -> "25 kg arroz" para evitar producto "de arroz".
        preparado = re.sub(
            r"(\d+(?:[,.]\d+)?\s*(?:kg|kilos?|kilogramos?|g|gr|gramos?|l|lt|litros?|ml|uds?|unidades?|cajas?|bolsas?|botes?|paquetes?))\s+de\s+",
            r"\1 ",
            preparado,
            flags=re.IGNORECASE,
        )
        return preparado, proveedor

    def _detectar_proveedor_conocido(self, texto: str) -> Optional[str]:
        t = texto or ""
        for proveedor in self.PROVEEDORES_CONOCIDOS:
            if re.search(rf"\b{re.escape(proveedor)}\b", t, re.IGNORECASE):
                return proveedor
        m = re.search(r"\bde\s+([A-ZÁÉÍÓÚÜÑ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 ._-]{2,30})\b", t)
        if m:
            posible = m.group(1).strip(" .,")
            posible = re.sub(r"\s+a\s+\d.*$", "", posible, flags=re.IGNORECASE).strip()
            if posible.lower() not in {"arroz", "aceite", "tomate", "harina"}:
                return posible
        return None

    def _limpiar_producto_chat(self, producto: str, proveedor: Optional[str]) -> str:
        limpio = (producto or "").strip(" .,")
        limpio = re.sub(r"^de\s+", "", limpio, flags=re.IGNORECASE).strip()
        if proveedor:
            limpio = re.sub(rf"\s+de\s+{re.escape(proveedor)}\b.*$", "", limpio, flags=re.IGNORECASE).strip()
        limpio = re.sub(r"\s+a\s+\d+(?:[,.]\d+)?\s*(?:€|eur|euros)?.*$", "", limpio, flags=re.IGNORECASE).strip()
        return limpio

    def _normalizar_simple(self, texto: str) -> str:
        return " ".join((texto or "").strip().lower().split())

    def _respuesta_evento(self, texto: str, clasificacion: Dict[str, Any]) -> Dict[str, Any]:
        return self._respuesta(True, "He detectado que hablas de un evento. El siguiente paso será conectarlo con eventos, producción y compras.", "evento", {"clasificacion": clasificacion})

    def _respuesta_compras(self, texto: str, clasificacion: Dict[str, Any]) -> Dict[str, Any]:
        return self._respuesta(True, "He detectado una consulta de compras. El siguiente paso será conectarla con stock, eventos y producción.", "compras", {"clasificacion": clasificacion})

    def _respuesta_rentabilidad(self, texto: str, clasificacion: Dict[str, Any]) -> Dict[str, Any]:
        return self._respuesta(True, "He detectado una consulta de rentabilidad. El siguiente paso será conectarla con los motores 4.8.", "rentabilidad", {"clasificacion": clasificacion})

    def _respuesta_produccion(self, texto: str, clasificacion: Dict[str, Any]) -> Dict[str, Any]:
        return self._respuesta(True, "He detectado una petición de producción. El siguiente paso será conectarla con planificación 4.6 y eventos 4.7.", "produccion", {"clasificacion": clasificacion})

    def _respuesta(self, ok: bool, mensaje: str, intencion: str, datos: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": ok, "version": self.VERSION, "intencion": intencion, "mensaje": mensaje, "datos": datos}


__all__ = ["ChatHostAIIntegrado505"]
