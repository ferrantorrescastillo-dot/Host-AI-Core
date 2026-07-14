from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
import json
from datetime import datetime


class ActualizadorInteligentePreciosFactura:
    """
    Host AI 3.0.3.5.2

    Aplica cambios de precios preparados desde facturas.
    - Actualiza automáticamente cambios normales.
    - Bloquea/revisa cambios fuertes.
    - Guarda log de aplicación.
    - Usa motor costes_inteligente si existe.
    """

    UMBRAL_REVISION = 20.0

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.facturas_dir / "log_actualizaciones_precios.json"
        self.log = self._cargar_log()

    def aplicar_cambio(self, cambio: Dict[str, Any], forzar: bool = False) -> Dict[str, Any]:
        articulo_id = cambio.get("articulo_id", "")
        nombre = cambio.get("nombre_articulo", "")
        precio_nuevo = float(cambio.get("precio_nuevo", 0) or 0)
        precio_anterior = float(cambio.get("precio_anterior", 0) or 0)
        unidad = cambio.get("unidad", "") or "ud"
        proveedor_id = cambio.get("proveedor_id", "")
        requiere_revision = bool(cambio.get("requiere_revision", False))
        variacion = float(cambio.get("variacion_porcentaje", 0) or 0)

        errores = []
        avisos = []

        if not articulo_id:
            errores.append("No hay articulo_id.")
        if not nombre:
            errores.append("No hay nombre de artículo.")
        if precio_nuevo <= 0:
            errores.append("Precio nuevo inválido.")
        if requiere_revision and not forzar:
            errores.append("Cambio requiere revisión. Usa forzar=True para aplicarlo.")
        if abs(variacion) >= self.UMBRAL_REVISION and not forzar:
            errores.append(f"Variación fuerte ({variacion}%). Requiere revisión.")

        if errores:
            resultado = {
                "aplicado": False,
                "errores": errores,
                "avisos": avisos,
                "cambio": cambio,
                "lectura_host_ai": f"No se aplicó cambio de precio: {', '.join(errores)}",
            }
            self._registrar_log(resultado)
            return resultado

        costes = getattr(self.core, "costes_inteligente", None)
        if costes:
            try:
                costes.registrar_precio(
                    nombre=nombre,
                    precio_unitario=precio_nuevo,
                    unidad=unidad,
                    articulo_id=articulo_id,
                    proveedor=proveedor_id,
                    familia=cambio.get("familia", ""),
                )
            except TypeError:
                # compatibilidad si la firma del motor es distinta
                costes.registrar_precio(nombre, precio_nuevo, unidad, articulo_id)

        # Actualiza también el registro de artículos importados si existe.
        imp = getattr(self.core, "importador_articulos_excel", None)
        if imp and hasattr(imp, "articulos") and articulo_id in imp.articulos:
            try:
                imp.articulos[articulo_id].precio_unitario = precio_nuevo
                imp.articulos[articulo_id].proveedor = proveedor_id or getattr(imp.articulos[articulo_id], "proveedor", "")
            except Exception:
                pass

        resultado = {
            "aplicado": True,
            "articulo_id": articulo_id,
            "nombre_articulo": nombre,
            "precio_anterior": precio_anterior,
            "precio_nuevo": precio_nuevo,
            "unidad": unidad,
            "proveedor_id": proveedor_id,
            "variacion_porcentaje": variacion,
            "forzado": forzar,
            "fecha_aplicacion": datetime.now().isoformat(timespec="seconds"),
            "errores": [],
            "avisos": avisos,
            "cambio": cambio,
            "lectura_host_ai": f"Precio actualizado: {nombre} {precio_anterior} -> {precio_nuevo}.",
        }
        self._registrar_log(resultado)
        hist = getattr(self.core, "historico_inteligente_precios", None)
        if hist is not None and resultado.get("aplicado"):
            resultado["historico"] = hist.registrar_desde_aplicacion(resultado)
        return resultado

    def aplicar_informe(self, informe: Dict[str, Any], forzar: bool = False) -> Dict[str, Any]:
        resultados = []
        for cambio in informe.get("cambios", []):
            resultados.append(self.aplicar_cambio(cambio, forzar=forzar))

        aplicados = sum(1 for r in resultados if r.get("aplicado"))
        bloqueados = len(resultados) - aplicados
        datos = {
            "resultados": resultados,
            "total": len(resultados),
            "aplicados": aplicados,
            "bloqueados": bloqueados,
            "lectura_host_ai": f"Actualización precios: {aplicados} aplicados, {bloqueados} bloqueados.",
        }

        if hasattr(self.core, "persistencia"):
            try:
                self.core.persistencia.guardar_todo()
            except Exception:
                pass
        return datos

    def preparar_y_aplicar(self, informe_relaciones: Dict[str, Any], forzar: bool = False) -> Dict[str, Any]:
        informe_precios = self.core.base_actualizacion_precios_factura.preparar_informe(informe_relaciones)
        aplicacion = self.aplicar_informe(informe_precios, forzar=forzar)
        aplicacion["informe_precios"] = informe_precios
        return aplicacion

    def listar_log(self) -> Dict[str, Any]:
        return {
            "log": self.log,
            "total": len(self.log),
            "lectura_host_ai": f"Log de actualizaciones de precios: {len(self.log)} registros.",
        }

    def exportar_log(self) -> Dict[str, Any]:
        self._guardar_log()
        return {
            "archivo": str(self.log_path),
            "lectura_host_ai": "Log de actualizaciones de precios exportado.",
        }

    def _registrar_log(self, resultado: Dict[str, Any]):
        self.log.append(resultado)
        self._guardar_log()

    def _cargar_log(self) -> List[Dict[str, Any]]:
        if self.log_path.exists():
            try:
                return json.loads(self.log_path.read_text(encoding="utf-8")).get("log", [])
            except Exception:
                return []
        return []

    def _guardar_log(self):
        self.log_path.write_text(json.dumps({"version": "3.0.3.5.2", "log": self.log}, ensure_ascii=False, indent=2), encoding="utf-8")
