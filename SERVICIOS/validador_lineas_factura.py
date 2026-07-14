from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any
import json
import re

from MODELOS.validacion_lineas_factura import ValidacionLineaFactura, InformeValidacionFactura


class ValidadorLineasFactura:
    """
    Host AI 3.0.3.3.5 - Validador Inteligente de Líneas de Factura.

    Valida:
    - cantidad
    - unidad
    - precio
    - importe
    - cantidad x precio = importe
    - descripción
    - duplicados
    - confianza mínima
    """

    UNIDADES_VALIDAS = {"kg", "g", "L", "l", "ml", "ud", "caja", "paq", "pack", "bote"}

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def validar_linea(self, linea: Dict[str, Any]) -> Dict[str, Any]:
        descripcion = str(linea.get("descripcion", "") or "").strip()
        cantidad = self._float(linea.get("cantidad"))
        unidad = str(linea.get("unidad", "") or "").strip()
        precio = self._float(linea.get("precio_unitario"))
        importe = self._float(linea.get("importe"))
        confianza_original = self._float(linea.get("confianza"))

        errores = []
        avisos = []
        confianza = 100.0

        if not descripcion:
            errores.append("Falta descripción.")
            confianza -= 35
        elif len(descripcion) < 2:
            errores.append("Descripción demasiado corta.")
            confianza -= 25

        if self._tiene_caracteres_raros(descripcion):
            avisos.append("La descripción contiene caracteres extraños.")
            confianza -= 10

        if cantidad <= 0:
            errores.append("Cantidad inválida.")
            confianza -= 30

        if not unidad:
            errores.append("Falta unidad.")
            confianza -= 25
        elif unidad not in self.UNIDADES_VALIDAS:
            avisos.append(f"Unidad no habitual: {unidad}.")
            confianza -= 10

        if precio <= 0:
            errores.append("Precio unitario inválido.")
            confianza -= 25

        if importe <= 0:
            errores.append("Importe inválido.")
            confianza -= 25

        importe_calculado = round(cantidad * precio, 2) if cantidad and precio else 0.0
        diferencia = round(importe - importe_calculado, 2)
        if cantidad > 0 and precio > 0 and importe > 0 and abs(diferencia) > 0.05:
            errores.append("El importe no coincide con cantidad x precio.")
            confianza -= 30

        if confianza_original and confianza_original < 70:
            avisos.append(f"Confianza de lectura baja: {confianza_original}.")
            confianza -= 10

        valida = len(errores) == 0
        val = ValidacionLineaFactura(
            descripcion=descripcion,
            valida=valida,
            errores=errores,
            avisos=avisos,
            confianza_original=confianza_original,
            confianza_validacion=max(0.0, confianza),
            cantidad=cantidad,
            unidad=unidad,
            precio_unitario=precio,
            importe=importe,
            importe_calculado=importe_calculado,
            diferencia=diferencia,
            origen_texto=str(linea.get("origen_texto", "") or ""),
        )
        datos = val.to_dict()
        datos["lectura_host_ai"] = "Línea válida." if valida else f"Línea inválida: {', '.join(errores)}"
        return datos

    def validar_factura_completa(self, bloque: Dict[str, Any]) -> Dict[str, Any]:
        validaciones = []
        for linea in bloque.get("lineas", []):
            datos = self.validar_linea(linea)
            validaciones.append(ValidacionLineaFactura(
                descripcion=datos["descripcion"],
                valida=datos["valida"],
                errores=datos["errores"],
                avisos=datos["avisos"],
                confianza_original=datos["confianza_original"],
                confianza_validacion=datos["confianza_validacion"],
                cantidad=datos["cantidad"],
                unidad=datos["unidad"],
                precio_unitario=datos["precio_unitario"],
                importe=datos["importe"],
                importe_calculado=datos["importe_calculado"],
                diferencia=datos["diferencia"],
                origen_texto=datos["origen_texto"],
            ))

        duplicados = self._detectar_duplicados(bloque.get("lineas", []))
        avisos_generales = []
        errores_generales = []

        total_factura = self._float(bloque.get("total_factura_detectado"))
        importe_lineas = round(sum(self._float(l.get("importe")) for l in bloque.get("lineas", [])), 2)
        diferencia_total = round(total_factura - importe_lineas, 2) if total_factura else 0.0

        # La diferencia puede ser IVA/portes/descuentos. Aviso, no error.
        if total_factura and abs(diferencia_total) > 0.10:
            avisos_generales.append(
                f"La suma de líneas ({importe_lineas}) no coincide con el total factura ({total_factura}). Diferencia: {diferencia_total}."
            )

        if duplicados:
            avisos_generales.append(f"Se han detectado {len(duplicados)} posibles líneas duplicadas.")

        informe = InformeValidacionFactura(
            archivo=str(bloque.get("archivo", "") or ""),
            total_factura_detectado=total_factura,
            validaciones=validaciones,
            duplicados=duplicados,
            avisos_generales=avisos_generales,
            errores_generales=errores_generales,
        )
        datos = informe.to_dict()
        datos["lectura_host_ai"] = (
            f"Validación factura: {datos['lineas_validas']} válidas, "
            f"{datos['lineas_con_avisos']} con avisos, {datos['lineas_invalidas']} inválidas."
        )
        return datos

    def validar_factura_desde_texto(self, texto: str, **kwargs) -> Dict[str, Any]:
        bloque = self.core.lector_completo_lineas_factura.leer_factura_texto_completa(
            texto=texto,
            proveedor_sugerido=kwargs.get("proveedor_sugerido", ""),
            cif_sugerido=kwargs.get("cif_sugerido", ""),
            numero_factura=kwargs.get("numero_factura", ""),
            fecha_factura=kwargs.get("fecha_factura", ""),
            total_factura_detectado=kwargs.get("total_factura_detectado", 0.0),
        )
        return self.validar_factura_completa(bloque)

    def validar_factura_desde_pdf(self, ruta_archivo: str) -> Dict[str, Any]:
        bloque = self.core.lector_completo_lineas_factura.leer_factura_pdf_completa(
            ruta_archivo=ruta_archivo,
            exportar_json=True,
        )
        return self.validar_factura_completa(bloque)

    def exportar_validacion(self, informe: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "validacion_lineas_factura.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "archivo": str(destino),
            "lectura_host_ai": f"Validación de factura exportada: {destino.name}.",
        }

    def _detectar_duplicados(self, lineas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        vistos = {}
        duplicados = []
        for idx, linea in enumerate(lineas, start=1):
            clave = (
                str(linea.get("descripcion", "")).lower().strip(),
                round(self._float(linea.get("cantidad")), 4),
                str(linea.get("unidad", "")).strip(),
                round(self._float(linea.get("importe")), 2),
            )
            if clave in vistos:
                duplicados.append({
                    "linea_actual": idx,
                    "linea_anterior": vistos[clave],
                    "descripcion": linea.get("descripcion", ""),
                    "cantidad": linea.get("cantidad", 0),
                    "unidad": linea.get("unidad", ""),
                    "importe": linea.get("importe", 0),
                })
            else:
                vistos[clave] = idx
        return duplicados

    def _float(self, valor) -> float:
        if valor in [None, ""]:
            return 0.0
        if isinstance(valor, (int, float)):
            return float(valor)
        try:
            return float(str(valor).replace(",", ".").replace("€", "").strip())
        except Exception:
            return 0.0

    def _tiene_caracteres_raros(self, texto: str) -> bool:
        # Permite letras, números, espacios y caracteres gastronómicos normales.
        return bool(re.search(r"[^A-Za-zÀ-ÿ0-9\s\-\.,/%ºª()]", texto or ""))
