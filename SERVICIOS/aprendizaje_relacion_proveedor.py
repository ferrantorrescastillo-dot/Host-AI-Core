from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any
import json
import unicodedata
import re
from datetime import datetime

from MODELOS.relacion_articulos_factura import AprendizajeRelacionProveedor as ModeloAprendizajeRelacionProveedor


class AprendizajeRelacionProveedorArticulos:
    """
    Host AI 3.0.3.4.4

    Aprende relaciones específicas por proveedor:
    - Makro escribe "CARR TERN" -> ART-CARRILLERA
    - BonÀrea escribe "CEB KG" -> ART-CEBOLLA

    El aprendizaje se guarda en:
    DATOS/diccionarios/diccionario_relaciones_proveedor.json
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.diccionario_path = self.base_dir / "DATOS" / "diccionarios" / "diccionario_relaciones_proveedor.json"
        self.diccionario_path.parent.mkdir(parents=True, exist_ok=True)
        self.aprendizajes: Dict[str, ModeloAprendizajeRelacionProveedor] = self._cargar()

    def aprender(
        self,
        proveedor_id: str,
        texto_proveedor: str,
        articulo_id: str,
        nombre_articulo: str,
        confianza: float = 100.0,
    ) -> Dict[str, Any]:
        clave = self._clave(proveedor_id, texto_proveedor)
        ahora = datetime.now().isoformat(timespec="seconds")

        if clave in self.aprendizajes:
            apr = self.aprendizajes[clave]
            apr.articulo_id = articulo_id
            apr.nombre_articulo = nombre_articulo
            apr.confianza = confianza
            apr.usos += 1
            apr.actualizado_en = ahora
        else:
            apr = ModeloAprendizajeRelacionProveedor(
                proveedor_id=proveedor_id,
                texto_proveedor=texto_proveedor,
                articulo_id=articulo_id,
                nombre_articulo=nombre_articulo,
                confianza=confianza,
                usos=1,
            )
            self.aprendizajes[clave] = apr

        self._guardar()
        return {
            "aprendizaje": apr.to_dict(),
            "lectura_host_ai": f"Relación aprendida: {proveedor_id} / {texto_proveedor} -> {nombre_articulo}.",
        }

    def buscar_aprendizaje(self, proveedor_id: str, texto_proveedor: str) -> Dict[str, Any]:
        clave = self._clave(proveedor_id, texto_proveedor)
        apr = self.aprendizajes.get(clave)
        if not apr:
            return {
                "encontrado": False,
                "lectura_host_ai": "No hay aprendizaje para esta línea/proveedor.",
            }
        return {
            "encontrado": True,
            "aprendizaje": apr.to_dict(),
            "lectura_host_ai": f"Aprendizaje encontrado: {apr.texto_proveedor} -> {apr.nombre_articulo}.",
        }

    def aplicar_a_linea(self, linea: Dict[str, Any], proveedor_id: str = "") -> Dict[str, Any]:
        descripcion = linea.get("descripcion", "") or linea.get("descripcion_factura", "")
        encontrado = self.buscar_aprendizaje(proveedor_id, descripcion)
        if not encontrado.get("encontrado"):
            return {
                "aplicado": False,
                "linea": linea,
                "lectura_host_ai": "No se aplicó aprendizaje.",
            }

        apr = encontrado["aprendizaje"]
        nueva = dict(linea)
        nueva["articulo_id"] = apr["articulo_id"]
        nueva["nombre_articulo"] = apr["nombre_articulo"]
        nueva["confianza"] = apr["confianza"]
        nueva["metodo"] = "aprendizaje_proveedor"
        nueva["requiere_revision"] = False
        return {
            "aplicado": True,
            "linea": nueva,
            "aprendizaje": apr,
            "lectura_host_ai": f"Aprendizaje aplicado: {descripcion} -> {apr['nombre_articulo']}.",
        }

    def aplicar_a_bloque(self, bloque: Dict[str, Any], proveedor_id: str = "") -> Dict[str, Any]:
        proveedor_id = proveedor_id or bloque.get("proveedor_id", "")
        relaciones = []
        aplicados = 0
        for rel in bloque.get("relaciones", []):
            r = self.aplicar_a_linea(rel, proveedor_id=proveedor_id)
            if r.get("aplicado"):
                aplicados += 1
                relaciones.append(r["linea"])
            else:
                relaciones.append(rel)

        nuevo = dict(bloque)
        nuevo["relaciones"] = relaciones
        nuevo["aprendizajes_aplicados"] = aplicados
        nuevo["lectura_host_ai"] = f"Aprendizajes aplicados: {aplicados}."
        return nuevo

    def listar(self) -> Dict[str, Any]:
        datos = [a.to_dict() for a in self.aprendizajes.values()]
        return {
            "aprendizajes": datos,
            "total": len(datos),
            "lectura_host_ai": f"Aprendizajes proveedor-artículo: {len(datos)}.",
        }

    def exportar(self) -> Dict[str, Any]:
        self._guardar()
        return {
            "archivo": str(self.diccionario_path),
            "lectura_host_ai": "Diccionario de relaciones proveedor-artículo exportado.",
        }

    def _cargar(self) -> Dict[str, ModeloAprendizajeRelacionProveedor]:
        if self.diccionario_path.exists():
            try:
                raw = json.loads(self.diccionario_path.read_text(encoding="utf-8"))
                out = {}
                for item in raw.get("aprendizajes", []):
                    apr = ModeloAprendizajeRelacionProveedor(**item)
                    out[self._clave(apr.proveedor_id, apr.texto_proveedor)] = apr
                return out
            except Exception:
                pass
        return {}

    def _guardar(self):
        data = {
            "version": "3.0.3.4.4",
            "aprendizajes": [a.to_dict() for a in self.aprendizajes.values()],
        }
        self.diccionario_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _clave(self, proveedor_id: str, texto: str) -> str:
        return f"{proveedor_id}::{self._normalizar(texto)}"

    def _normalizar(self, texto: str) -> str:
        texto = str(texto or "").strip().lower()
        texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
        texto = re.sub(r"[^a-z0-9\s]", " ", texto)
        return " ".join(texto.split())
