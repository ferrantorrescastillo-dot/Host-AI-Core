from __future__ import annotations

"""
Host AI 4.4.14 - Configuración centralizada.

Servicio responsable de leer, crear, validar y actualizar la configuración base
sin depender de scripts sueltos. Mantiene la configuración en DATOS/configuracion/host_ai_config.json.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List
import json


@dataclass
class ConfiguracionHostAI4414:
    restaurante: str = "Restaurante Demo"
    iva_default: float = 10.0
    moneda: str = "EUR"
    idioma: str = "es"
    ruta_datos: str = "DATOS"
    ruta_documentos: str = "Documentos"
    ruta_logs: str = "LOGS"
    ocr_activo: bool = False
    ia_activa: bool = False
    proveedor_default: str = ""
    modo_entorno: str = "desarrollo"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GestorConfiguracionCentral4414:
    """Gestiona una configuración única y reutilizable para todo Host AI."""

    CAMPOS_OBLIGATORIOS = {
        "restaurante",
        "iva_default",
        "moneda",
        "idioma",
        "ruta_datos",
        "ruta_documentos",
        "ruta_logs",
        "ocr_activo",
        "ia_activa",
        "modo_entorno",
    }

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self.config_dir = self.base_dir / "DATOS" / "configuracion"
        self.config_path = self.config_dir / "host_ai_config.json"

    def configuracion_por_defecto(self) -> Dict[str, Any]:
        return ConfiguracionHostAI4414().to_dict()

    def existe_configuracion(self) -> bool:
        return self.config_path.exists()

    def crear_si_no_existe(self) -> Dict[str, Any]:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            self.guardar_configuracion(self.configuracion_por_defecto())
        return self.cargar_configuracion()

    def cargar_configuracion(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return self.crear_si_no_existe()
        try:
            datos = json.loads(self.config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            datos = {}
        base = self.configuracion_por_defecto()
        base.update(datos if isinstance(datos, dict) else {})
        return base

    def guardar_configuracion(self, configuracion: Dict[str, Any]) -> Dict[str, Any]:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        normalizada = self._normalizar_configuracion(configuracion)
        self.config_path.write_text(json.dumps(normalizada, ensure_ascii=False, indent=2), encoding="utf-8")
        return normalizada

    def actualizar_configuracion(self, cambios: Dict[str, Any]) -> Dict[str, Any]:
        actual = self.cargar_configuracion()
        actual.update(cambios or {})
        return self.guardar_configuracion(actual)

    def validar_configuracion(self, configuracion: Dict[str, Any] | None = None) -> Dict[str, Any]:
        datos = configuracion or self.cargar_configuracion()
        errores: List[str] = []
        avisos: List[str] = []

        faltantes = sorted(self.CAMPOS_OBLIGATORIOS - set(datos.keys()))
        for campo in faltantes:
            errores.append(f"Falta campo obligatorio: {campo}")

        try:
            iva = float(datos.get("iva_default", 0))
            if iva < 0 or iva > 100:
                errores.append("iva_default debe estar entre 0 y 100")
        except (TypeError, ValueError):
            errores.append("iva_default debe ser numérico")

        if str(datos.get("moneda", "")).upper() not in {"EUR", "USD", "GBP"}:
            avisos.append("Moneda no habitual. Revisa si es correcta.")

        if str(datos.get("idioma", "")).lower() not in {"es", "ca", "en"}:
            avisos.append("Idioma no habitual. Valores recomendados: es, ca, en.")

        for ruta in ["ruta_datos", "ruta_documentos", "ruta_logs"]:
            valor = str(datos.get(ruta, "")).strip()
            if not valor:
                errores.append(f"{ruta} no puede estar vacío")

        return {
            "ok": len(errores) == 0,
            "errores": errores,
            "avisos": avisos,
            "configuracion": datos,
            "archivo": str(self.config_path),
            "lectura_host_ai": "Configuración validada correctamente." if not errores else "Configuración con errores pendientes.",
        }

    def resumen_configuracion(self) -> Dict[str, Any]:
        datos = self.cargar_configuracion()
        validacion = self.validar_configuracion(datos)
        return {
            "restaurante": datos.get("restaurante"),
            "moneda": datos.get("moneda"),
            "idioma": datos.get("idioma"),
            "ocr_activo": bool(datos.get("ocr_activo")),
            "ia_activa": bool(datos.get("ia_activa")),
            "modo_entorno": datos.get("modo_entorno"),
            "ok": validacion["ok"],
            "avisos": validacion["avisos"],
            "errores": validacion["errores"],
            "lectura_host_ai": f"Configuración Host AI cargada para {datos.get('restaurante')}.",
        }

    def asegurar_rutas_configuradas(self) -> Dict[str, Any]:
        datos = self.cargar_configuracion()
        creadas: List[str] = []
        for clave in ["ruta_datos", "ruta_documentos", "ruta_logs"]:
            ruta = self.base_dir / str(datos.get(clave, ""))
            ruta.mkdir(parents=True, exist_ok=True)
            creadas.append(str(ruta))
        return {
            "ok": True,
            "rutas_creadas": creadas,
            "lectura_host_ai": f"Rutas configuradas verificadas: {len(creadas)}.",
        }

    def _normalizar_configuracion(self, configuracion: Dict[str, Any]) -> Dict[str, Any]:
        base = self.configuracion_por_defecto()
        base.update(configuracion or {})
        base["restaurante"] = str(base.get("restaurante") or "Restaurante Demo").strip()
        base["moneda"] = str(base.get("moneda") or "EUR").upper().strip()
        base["idioma"] = str(base.get("idioma") or "es").lower().strip()
        base["modo_entorno"] = str(base.get("modo_entorno") or "desarrollo").lower().strip()
        base["iva_default"] = float(base.get("iva_default", 10) or 0)
        base["ocr_activo"] = bool(base.get("ocr_activo"))
        base["ia_activa"] = bool(base.get("ia_activa"))
        return base
