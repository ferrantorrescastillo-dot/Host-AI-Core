"""Servicio de detección de anomalías de compras para Host AI RC1.

Este módulo pertenece al bloque 3.0.4 Inteligencia de Compras.
La revisión RC2 mantiene la funcionalidad existente y documenta el contrato
público del servicio para facilitar mantenimiento antes del piloto.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Iterable, Tuple
import json
from statistics import mean, pstdev

from MODELOS.anomalias_compras import AnomaliaCompra, InformeAnomaliasCompras


__all__ = ["DetectorAnomaliasCompras"]


class DetectorAnomaliasCompras:
    """
    Host AI 3.0.4.3 - Detector Inteligente de Anomalías de Compras.

    Detecta desviaciones de precio, duplicados, artículos desconocidos,
    cantidades anormales, errores OCR y comportamientos extraños de proveedor.
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def detectar_anomalias(self) -> Dict[str, Any]:
        anomalias: List[Dict[str, Any]] = []
        anomalias.extend(self._detectar_anomalias_precios())
        anomalias.extend(self._detectar_anomalias_auditoria())
        anomalias.extend(self._detectar_anomalias_stock())
        anomalias.extend(self._detectar_comportamiento_proveedores())

        resumen_tipo: Dict[str, int] = {}
        resumen_proveedor: Dict[str, int] = {}
        for a in anomalias:
            resumen_tipo[a["tipo"]] = resumen_tipo.get(a["tipo"], 0) + 1
            proveedor = a.get("proveedor_nombre") or a.get("proveedor_id") or "SIN-PROVEEDOR"
            resumen_proveedor[proveedor] = resumen_proveedor.get(proveedor, 0) + 1

        criticas = sum(1 for a in anomalias if a.get("gravedad") == "critica")
        avisos = sum(1 for a in anomalias if a.get("gravedad") == "aviso")
        informativas = sum(1 for a in anomalias if a.get("gravedad") == "informativa")
        lectura = f"Anomalías compras: {len(anomalias)} detectadas ({criticas} críticas, {avisos} avisos, {informativas} informativas)."

        informe = InformeAnomaliasCompras(
            total_anomalias=len(anomalias),
            criticas=criticas,
            avisos=avisos,
            informativas=informativas,
            anomalias=anomalias,
            resumen_por_tipo=resumen_tipo,
            resumen_por_proveedor=resumen_proveedor,
            lectura_host_ai=lectura,
        )
        return informe.to_dict()

    def exportar_informe(self, informe: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "anomalias_compras.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Informe de anomalías exportado: {destino.name}."}

    def _detectar_anomalias_precios(self) -> List[Dict[str, Any]]:
        historico = getattr(self.core, "historico_inteligente_precios", None)
        registros = list(getattr(historico, "registros", []) or []) if historico else []
        agrupados: Dict[str, List[Any]] = {}
        for r in registros:
            agrupados.setdefault(getattr(r, "articulo_id", "") or "SIN-ARTICULO", []).append(r)

        salida: List[Dict[str, Any]] = []
        for articulo_id, regs in agrupados.items():
            anteriores: List[float] = []
            for r in regs:
                precio = float(getattr(r, "precio", 0) or 0)
                if precio <= 0:
                    salida.append(self._anomalia(
                        "precio_no_valido", "critica", "Precio histórico no válido o igual a cero.", "historico_precios", r,
                        datos={"precio": precio}, accion="Revisar factura y precio aplicado."
                    ))
                    continue
                if len(anteriores) >= 2:
                    media = mean(anteriores)
                    variacion = ((precio - media) / media) * 100 if media else 0.0
                    desviacion = pstdev(anteriores) if len(anteriores) >= 3 else 0.0
                    limite_alto = media * 1.25
                    limite_bajo = media * 0.75
                    if precio > limite_alto and variacion >= 25:
                        salida.append(self._anomalia(
                            "subida_anormal_precio", "critica" if variacion >= 50 else "aviso",
                            f"Subida anormal de precio en {getattr(r, 'nombre_articulo', articulo_id)}: {round(variacion, 2)}% sobre la media.",
                            "historico_precios", r,
                            datos={"precio": precio, "media_anterior": round(media, 4), "variacion_porcentual": round(variacion, 2), "desviacion": round(desviacion, 4)},
                            accion="Validar factura, unidad, proveedor y posible cambio de formato."
                        ))
                    if precio < limite_bajo and variacion <= -25:
                        salida.append(self._anomalia(
                            "bajada_sospechosa_precio", "aviso",
                            f"Bajada sospechosa de precio en {getattr(r, 'nombre_articulo', articulo_id)}: {round(variacion, 2)}% bajo la media.",
                            "historico_precios", r,
                            datos={"precio": precio, "media_anterior": round(media, 4), "variacion_porcentual": round(variacion, 2)},
                            accion="Comprobar si la unidad, formato o cantidad coinciden con compras anteriores."
                        ))
                anteriores.append(precio)
        return salida

    def _detectar_anomalias_auditoria(self) -> List[Dict[str, Any]]:
        auditoria = getattr(self.core, "auditoria_importaciones_universales", None)
        registros = list(getattr(auditoria, "registros", []) or []) if auditoria else []
        salida: List[Dict[str, Any]] = []
        vistos: Dict[Tuple[str, str, int], Any] = {}
        for r in registros:
            archivo = getattr(r, "archivo", "")
            proveedor = getattr(r, "proveedor_id", "") or getattr(r, "proveedor_nombre", "")
            total_lineas = int(getattr(r, "total_lineas", 0) or 0)
            clave = (archivo.lower().strip(), proveedor.lower().strip(), total_lineas)
            if archivo and clave in vistos:
                salida.append(self._anomalia(
                    "factura_duplicada", "critica", f"Posible factura duplicada detectada: {archivo}.", "auditoria_importaciones", r,
                    datos={"archivo": archivo, "proveedor": proveedor, "total_lineas": total_lineas},
                    accion="Bloquear doble importación y revisar auditoría antes de aplicar stock/precios."
                ))
            vistos[clave] = r

            errores = list(getattr(r, "errores", []) or [])
            avisos = list(getattr(r, "avisos", []) or [])
            texto_errores = " ".join(str(x).lower() for x in errores + avisos)
            if errores or "ocr" in texto_errores or "ilegible" in texto_errores:
                salida.append(self._anomalia(
                    "error_ocr_detectable", "critica" if errores else "aviso",
                    "La importación contiene errores o avisos compatibles con OCR/revisión manual.", "auditoria_importaciones", r,
                    datos={"errores": errores, "avisos": avisos}, accion="Revisar lectura OCR y líneas antes de confirmar importación."
                ))
            if getattr(r, "requiere_revision", False):
                salida.append(self._anomalia(
                    "requiere_revision_manual", "aviso", "La auditoría marca esta importación como pendiente de revisión.", "auditoria_importaciones", r,
                    datos={"estado": getattr(r, "estado", "")}, accion="Validar proveedor, líneas, relaciones y totales."
                ))
            if total_lineas == 0 and getattr(r, "estado", "") in {"aplicado", "preparado"}:
                salida.append(self._anomalia(
                    "factura_sin_lineas", "critica", "Factura preparada/aplicada sin líneas detectadas.", "auditoria_importaciones", r,
                    datos={"estado": getattr(r, "estado", "")}, accion="Revisar OCR/parser: una factura sin líneas no debería aplicarse."
                ))

            datos = getattr(r, "datos", {}) or {}
            salida.extend(self._detectar_articulos_desconocidos_en_datos(datos, r))
        return salida

    def _detectar_articulos_desconocidos_en_datos(self, datos: Dict[str, Any], registro_auditoria: Any) -> List[Dict[str, Any]]:
        salida: List[Dict[str, Any]] = []
        def recorrer(obj: Any) -> Iterable[Dict[str, Any]]:
            if isinstance(obj, dict):
                yield obj
                for v in obj.values():
                    yield from recorrer(v)
            elif isinstance(obj, list):
                for item in obj:
                    yield from recorrer(item)
        for item in recorrer(datos):
            posible_id = str(item.get("articulo_id", "") or item.get("articulo_host_ai_id", "") or "").strip().upper()
            nombre = str(item.get("nombre_articulo", "") or item.get("descripcion", "") or item.get("articulo", "") or "")
            confianza = float(item.get("confianza", item.get("score", 1)) or 0)
            if posible_id in {"", "DESCONOCIDO", "SIN-ARTICULO", "NO-RELACIONADO"} or item.get("desconocido") is True or confianza < 0.45:
                salida.append(self._anomalia(
                    "articulo_desconocido", "aviso", f"Artículo no relacionado o con baja confianza: {nombre or posible_id or 'sin nombre'}.",
                    "relacion_articulos", registro_auditoria,
                    datos={"articulo_id": posible_id, "nombre": nombre, "confianza": confianza},
                    accion="Relacionar manualmente el artículo o aprender relación proveedor-artículo."
                ))
        return salida

    def _detectar_anomalias_stock(self) -> List[Dict[str, Any]]:
        historico = getattr(self.core, "historico_inteligente_stock", None)
        registros = list(getattr(historico, "registros", []) or []) if historico else []
        agrupados: Dict[str, List[float]] = {}
        salida: List[Dict[str, Any]] = []
        for r in registros:
            cantidad = float(getattr(r, "cantidad", 0) or 0)
            articulo_id = getattr(r, "articulo_id", "") or "SIN-ARTICULO"
            if cantidad <= 0:
                salida.append(self._anomalia(
                    "cantidad_no_valida", "critica", "Movimiento de stock con cantidad no válida.", "historico_stock", r,
                    datos={"cantidad": cantidad}, accion="Revisar unidad/cantidad leída en factura."
                ))
            anteriores = agrupados.setdefault(articulo_id, [])
            if len(anteriores) >= 2:
                media = mean(anteriores)
                if media > 0 and cantidad > media * 4:
                    salida.append(self._anomalia(
                        "cantidad_fuera_de_rango", "aviso", f"Cantidad fuera de rango para {getattr(r, 'nombre_articulo', articulo_id)}.",
                        "historico_stock", r,
                        datos={"cantidad": cantidad, "media_anterior": round(media, 4)},
                        accion="Comprobar si se leyó una caja, kg, unidad o decimal incorrectamente."
                    ))
            if cantidad > 0:
                anteriores.append(cantidad)
        return salida

    def _detectar_comportamiento_proveedores(self) -> List[Dict[str, Any]]:
        auditoria = getattr(self.core, "auditoria_importaciones_universales", None)
        registros = list(getattr(auditoria, "registros", []) or []) if auditoria else []
        por_proveedor: Dict[str, Dict[str, int]] = {}
        muestra = {}
        for r in registros:
            prov = getattr(r, "proveedor_id", "") or getattr(r, "proveedor_nombre", "") or "SIN-PROVEEDOR"
            muestra[prov] = r
            item = por_proveedor.setdefault(prov, {"total": 0, "errores": 0, "revision": 0})
            item["total"] += 1
            if getattr(r, "errores", []) or getattr(r, "estado", "") in {"bloqueado", "error"}:
                item["errores"] += 1
            if getattr(r, "requiere_revision", False):
                item["revision"] += 1
        salida: List[Dict[str, Any]] = []
        for prov, datos in por_proveedor.items():
            total = datos["total"]
            problemas = datos["errores"] + datos["revision"]
            if total >= 2 and problemas / total >= 0.5:
                salida.append(self._anomalia(
                    "proveedor_comportamiento_extrano", "aviso", f"Proveedor con alta proporción de incidencias: {prov}.",
                    "auditoria_importaciones", muestra[prov],
                    datos={"proveedor": prov, "total_importaciones": total, "incidencias": problemas},
                    accion="Revisar plantillas, OCR, relaciones aprendidas y formato de factura de este proveedor."
                ))
        return salida

    def _anomalia(self, tipo: str, gravedad: str, mensaje: str, origen: str, registro: Any, datos: Dict[str, Any], accion: str) -> Dict[str, Any]:
        return AnomaliaCompra(
            tipo=tipo,
            gravedad=gravedad,
            mensaje=mensaje,
            origen=origen,
            articulo_id=getattr(registro, "articulo_id", ""),
            nombre_articulo=getattr(registro, "nombre_articulo", ""),
            proveedor_id=getattr(registro, "proveedor_id", ""),
            proveedor_nombre=getattr(registro, "proveedor_nombre", ""),
            numero_factura=getattr(registro, "numero_factura", ""),
            datos=datos,
            accion_recomendada=accion,
        ).to_dict()
