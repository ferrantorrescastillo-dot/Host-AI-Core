from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any
import json

from MODELOS.relacion_articulos_factura import (
    CandidatoArticuloFactura,
    RelacionLineaArticulo,
    InformeRelacionArticulosFactura,
)


class RelacionadorAutomaticoArticulosFactura:
    """
    Host AI 3.0.3.4.3

    Relaciona automáticamente cada línea de factura con el artículo interno
    más probable usando el buscador de artículos parecidos.

    Umbrales:
    - >= 85: relación automática
    - 60-84.99: sugerencia con revisión
    - < 60: sin relación
    """

    UMBRAL_AUTO = 85.0
    UMBRAL_REVISION = 60.0

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def relacionar_bloque(self, bloque: Dict[str, Any], limite_candidatos: int = 5) -> Dict[str, Any]:
        proveedor_id = bloque.get("proveedor_id", "") or bloque.get("deteccion_proveedor", {}).get("proveedor_id", "")
        proveedor_nombre = bloque.get("proveedor_nombre", "") or bloque.get("deteccion_proveedor", {}).get("nombre", "")

        relaciones: List[RelacionLineaArticulo] = []
        avisos_generales = []

        for linea in bloque.get("lineas", []):
            relacion = self.relacionar_linea(linea, proveedor_id=proveedor_id, limite_candidatos=limite_candidatos)
            relaciones.append(self._relacion_desde_dict(relacion))

        if not relaciones:
            avisos_generales.append("No hay líneas para relacionar.")

        informe = InformeRelacionArticulosFactura(
            archivo=str(bloque.get("archivo", "") or ""),
            proveedor_id=proveedor_id,
            proveedor_nombre=proveedor_nombre,
            numero_factura=bloque.get("numero_factura", ""),
            fecha_factura=bloque.get("fecha_factura", ""),
            relaciones=relaciones,
            avisos_generales=avisos_generales,
        )
        datos = informe.to_dict()
        datos["lectura_host_ai"] = (
            f"Relación automática: {datos['relacionadas_auto']} automáticas, "
            f"{datos['requieren_revision']} para revisar, {datos['sin_relacion']} sin relación."
        )
        return datos

    def relacionar_linea(self, linea: Dict[str, Any], proveedor_id: str = "", limite_candidatos: int = 5) -> Dict[str, Any]:
        descripcion = str(linea.get("descripcion", "") or "").strip()

        aprendizaje = getattr(self.core, "aprendizaje_relacion_proveedor", None)
        if aprendizaje is not None and proveedor_id:
            aprendido = aprendizaje.buscar_aprendizaje(proveedor_id, descripcion)
            if aprendido.get("encontrado"):
                apr = aprendido["aprendizaje"]
                relacion = RelacionLineaArticulo(
                    descripcion_factura=descripcion,
                    cantidad=float(linea.get("cantidad", 0) or 0),
                    unidad=str(linea.get("unidad", "") or ""),
                    precio_unitario=float(linea.get("precio_unitario", 0) or 0),
                    importe=float(linea.get("importe", 0) or 0),
                    proveedor_id=proveedor_id,
                    articulo_id=apr["articulo_id"],
                    nombre_articulo=apr["nombre_articulo"],
                    confianza=float(apr.get("confianza", 100) or 100),
                    metodo="aprendizaje_proveedor",
                    requiere_revision=False,
                    candidatos=[],
                    avisos=[],
                    origen_linea=linea,
                )
                datos = relacion.to_dict()
                datos["busqueda"] = {"aprendizaje": aprendido}
                datos["lectura_host_ai"] = f"Relacionado por aprendizaje con {apr['nombre_articulo']}."
                return datos

        busqueda = self.core.buscador_articulos_parecidos.buscar(
            descripcion=descripcion,
            limite=limite_candidatos,
            proveedor_id=proveedor_id,
        )

        candidatos = []
        for c in busqueda.get("candidatos", []):
            candidatos.append(CandidatoArticuloFactura(
                articulo_id=c.get("articulo_id", ""),
                nombre_articulo=c.get("nombre_articulo", ""),
                confianza=float(c.get("confianza", 0) or 0),
                metodo=c.get("metodo", ""),
                motivos=c.get("motivos", []),
                proveedor_id=c.get("proveedor_id", proveedor_id),
                unidad=c.get("unidad", ""),
                familia=c.get("familia", ""),
            ))

        mejor = candidatos[0] if candidatos else None
        avisos = []
        articulo_id = ""
        nombre_articulo = ""
        confianza = 0.0
        metodo = "sin_relacion"
        requiere_revision = True

        if mejor:
            articulo_id = mejor.articulo_id
            nombre_articulo = mejor.nombre_articulo
            confianza = mejor.confianza
            metodo = mejor.metodo
            if confianza >= self.UMBRAL_AUTO:
                requiere_revision = False
            elif confianza >= self.UMBRAL_REVISION:
                requiere_revision = True
                avisos.append("Confianza media. Requiere revisión.")
            else:
                articulo_id = ""
                nombre_articulo = ""
                metodo = "sin_relacion"
                requiere_revision = True
                avisos.append("Confianza insuficiente para relacionar.")
        else:
            avisos.append("No hay candidatos para esta línea.")

        relacion = RelacionLineaArticulo(
            descripcion_factura=descripcion,
            cantidad=float(linea.get("cantidad", 0) or 0),
            unidad=str(linea.get("unidad", "") or ""),
            precio_unitario=float(linea.get("precio_unitario", 0) or 0),
            importe=float(linea.get("importe", 0) or 0),
            proveedor_id=proveedor_id,
            articulo_id=articulo_id,
            nombre_articulo=nombre_articulo,
            confianza=confianza,
            metodo=metodo,
            requiere_revision=requiere_revision,
            candidatos=candidatos,
            avisos=avisos,
            origen_linea=linea,
        )
        datos = relacion.to_dict()
        datos["busqueda"] = busqueda
        datos["lectura_host_ai"] = (
            f"Relacionado con {nombre_articulo} ({confianza}%)."
            if articulo_id else "Línea sin relación automática."
        )
        return datos

    def relacionar_factura_texto(
        self,
        texto: str,
        proveedor_sugerido: str = "",
        cif_sugerido: str = "",
        numero_factura: str = "",
        fecha_factura: str = "",
        total_factura_detectado: float = 0.0,
    ) -> Dict[str, Any]:
        bloque = self.core.lector_completo_lineas_factura.leer_factura_texto_completa(
            texto=texto,
            proveedor_sugerido=proveedor_sugerido,
            cif_sugerido=cif_sugerido,
            numero_factura=numero_factura,
            fecha_factura=fecha_factura,
            total_factura_detectado=total_factura_detectado,
        )
        return self.relacionar_bloque(bloque)

    def relacionar_factura_pdf(self, ruta_archivo: str) -> Dict[str, Any]:
        bloque = self.core.lector_completo_lineas_factura.leer_factura_pdf_completa(
            ruta_archivo=ruta_archivo,
            exportar_json=True,
        )
        return self.relacionar_bloque(bloque)

    def exportar_informe(self, informe: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "relacion_automatica_articulos_factura.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "archivo": str(destino),
            "lectura_host_ai": f"Informe de relación automática exportado: {destino.name}.",
        }

    def _relacion_desde_dict(self, datos: Dict[str, Any]) -> RelacionLineaArticulo:
        candidatos = [
            CandidatoArticuloFactura(
                articulo_id=c.get("articulo_id", ""),
                nombre_articulo=c.get("nombre_articulo", ""),
                confianza=float(c.get("confianza", 0) or 0),
                metodo=c.get("metodo", ""),
                motivos=c.get("motivos", []),
                proveedor_id=c.get("proveedor_id", ""),
                unidad=c.get("unidad", ""),
                familia=c.get("familia", ""),
            )
            for c in datos.get("candidatos", [])
        ]
        return RelacionLineaArticulo(
            descripcion_factura=datos.get("descripcion_factura", ""),
            cantidad=float(datos.get("cantidad", 0) or 0),
            unidad=datos.get("unidad", ""),
            precio_unitario=float(datos.get("precio_unitario", 0) or 0),
            importe=float(datos.get("importe", 0) or 0),
            proveedor_id=datos.get("proveedor_id", ""),
            articulo_id=datos.get("articulo_id", ""),
            nombre_articulo=datos.get("nombre_articulo", ""),
            confianza=float(datos.get("confianza", 0) or 0),
            metodo=datos.get("metodo", ""),
            requiere_revision=bool(datos.get("requiere_revision", True)),
            candidatos=candidatos,
            avisos=datos.get("avisos", []),
            origen_linea=datos.get("origen_linea", {}),
        )
