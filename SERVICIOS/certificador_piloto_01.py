from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
import hashlib
import json

from SERVICIOS.auditor_arranque_piloto_01 import AuditorArranquePiloto01
from SERVICIOS.configuracion_piloto_01 import ConfiguracionPiloto01
from SERVICIOS.inventario_modulos_piloto_01 import InventarioModulosPiloto01


class CertificadorPiloto01:
    ARCHIVOS_NEGOCIO = (
        "DATOS/db/articulos.json",
        "DATOS/db/escandallos.json",
        "DATOS/db/menus.json",
    )

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self.config = ConfiguracionPiloto01(self.base_dir)

    def ejecutar(self, guardar_informe: bool = True) -> dict[str, Any]:
        antes = self._huellas_negocio()
        auditoria = AuditorArranquePiloto01(self.base_dir).ejecutar(importar_modulos=True)
        inventario = InventarioModulosPiloto01(self.base_dir).generar()
        despues = self._huellas_negocio()
        negocio_intacto = antes == despues
        estado = "CERTIFICADO" if auditoria["ok"] and negocio_intacto else "NO_CERTIFICADO"
        marca = datetime.now().strftime("%Y%m%d-%H%M%S")
        certificado = {
            "sprint": "PILOTO-0.1",
            "estado": estado,
            "solo_lectura": negocio_intacto,
            "auditoria": auditoria,
            "inventario_resumen": inventario["resumen"],
            "total_python": inventario["total_python"],
            "archivos_negocio_modificados": 0 if negocio_intacto else 1,
            "fecha": marca,
        }
        if guardar_informe:
            rutas = self.config.rutas()
            destino = Path(rutas.certificaciones)
            destino.mkdir(parents=True, exist_ok=True)
            json_path = destino / f"CERT-PILOTO01-{marca}.json"
            txt_path = destino / f"CERT-PILOTO01-{marca}.txt"
            json_path.write_text(json.dumps(certificado, ensure_ascii=False, indent=2), encoding="utf-8")
            txt_path.write_text(self.formatear(certificado), encoding="utf-8")
            certificado["informe_json"] = str(json_path)
            certificado["informe_txt"] = str(txt_path)
        return certificado

    @staticmethod
    def formatear(certificado: dict[str, Any]) -> str:
        audit = certificado["auditoria"]
        resumen = certificado["inventario_resumen"]
        lineas = [
            "PILOTO-0.1 — ESTABILIZACIÓN DE LA LÍNEA BASE",
            "=" * 78,
            f"Estado: {certificado['estado']} | Solo lectura: {'SÍ' if certificado['solo_lectura'] else 'NO'}",
            f"Arranque: {audit['estado']} | Errores: {audit['errores']} | Avisos: {audit['avisos']}",
            f"Módulos Python inventariados: {certificado['total_python']}",
            "Clasificación: " + ", ".join(f"{k}={v}" for k, v in resumen.items()),
            f"Archivos de negocio modificados: {certificado['archivos_negocio_modificados']}",
            "-" * 78,
        ]
        for item in audit["comprobaciones"]:
            simbolo = "OK" if item["ok"] else "REVISAR"
            lineas.append(f"[{simbolo}] {item['codigo']}: {item['detalle']}")
        return "\n".join(lineas) + "\n"

    def _huellas_negocio(self) -> dict[str, str | None]:
        resultado: dict[str, str | None] = {}
        for relativa in self.ARCHIVOS_NEGOCIO:
            ruta = self.base_dir / relativa
            resultado[relativa] = self._sha256(ruta) if ruta.exists() else None
        return resultado

    @staticmethod
    def _sha256(ruta: Path) -> str:
        digest = hashlib.sha256()
        with ruta.open("rb") as fh:
            for bloque in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(bloque)
        return digest.hexdigest()


__all__ = ["CertificadorPiloto01"]
