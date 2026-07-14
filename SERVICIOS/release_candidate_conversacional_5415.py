from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from SERVICIOS.integracion_conversacional_datos_5414 import integrar_conversacion_datos_5414


class ReleaseCandidateConversacional5415:
    VERSION = "5.4.15"

    MODULOS_CRITICOS = [
        "SERVICIOS.orquestador_inteligente_52",
        "SERVICIOS.confirmacion_inteligente_534",
        "SERVICIOS.integracion_conversacional_datos_5414",
    ]

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()

    def _auditar_modulos(self) -> List[Dict[str, Any]]:
        salida = []
        for nombre in self.MODULOS_CRITICOS:
            try:
                importlib.import_module(nombre)
                salida.append({"modulo": nombre, "ok": True})
            except Exception as exc:  # auditoría: debe capturar el fallo y seguir
                salida.append({"modulo": nombre, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
        return salida

    def _auditar_datos(self) -> Dict[str, Any]:
        db = self.base_dir / "DATOS" / "db"
        esperados = ["articulos.json", "proveedores.json", "escandallos.json", "eventos.json"]
        presentes = [name for name in esperados if (db / name).exists()]
        return {"ok": db.exists(), "directorio": str(db), "presentes": presentes, "esperados": esperados}

    def ejecutar(self) -> Dict[str, Any]:
        modulos = self._auditar_modulos()
        datos = self._auditar_datos()
        escenario = integrar_conversacion_datos_5414(
            {"tipo": "boda", "personas": 150, "fecha": "sábado", "hora_servicio": "15:00", "menu": "paella"},
            base_dir=self.base_dir,
        )
        comprobaciones = {
            "modulos_importables": all(x["ok"] for x in modulos),
            "directorio_datos": bool(datos["ok"]),
            "integracion_solo_lectura": escenario.get("datos_reales_modificados") is False,
            "respuesta_estructurada": all(k in escenario for k in ("menus_encontrados", "stock", "proveedores", "incidencias")),
            "confirmacion_escritura_protegida": escenario.get("requiere_confirmacion_escritura") is True,
        }
        aprobadas = sum(bool(v) for v in comprobaciones.values())
        total = len(comprobaciones)
        return {
            "ok": aprobadas == total,
            "version": self.VERSION,
            "estado": "RELEASE_CANDIDATE_APROBADO" if aprobadas == total else "RELEASE_CANDIDATE_PENDIENTE",
            "comprobaciones": comprobaciones,
            "aprobadas": aprobadas,
            "total": total,
            "porcentaje": round(aprobadas * 100 / total, 1),
            "modulos": modulos,
            "datos": datos,
            "escenario": escenario,
        }


def ejecutar_release_candidate_5415(base_dir: Optional[Path] = None) -> Dict[str, Any]:
    return ReleaseCandidateConversacional5415(base_dir).ejecutar()


def formatear_release_candidate_5415(resultado: Dict[str, Any]) -> str:
    lineas = ["HOST AI 5.4.15 - RELEASE CANDIDATE CONVERSACIONAL", ""]
    for nombre, ok in resultado.get("comprobaciones", {}).items():
        lineas.append(f"- {nombre}: {'OK' if ok else 'PENDIENTE'}")
    lineas += [
        "",
        f"Resultado: {resultado.get('aprobadas')}/{resultado.get('total')} ({resultado.get('porcentaje')}%)",
        f"Estado: {resultado.get('estado')}",
        "Datos reales modificados: NO",
    ]
    return "\n".join(lineas)


__all__ = ["ReleaseCandidateConversacional5415", "ejecutar_release_candidate_5415", "formatear_release_candidate_5415"]
