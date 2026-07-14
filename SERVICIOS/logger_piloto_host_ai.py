"""
Host AI - RC3.3 Logs para Piloto

Servicio ligero para registrar eventos importantes durante pruebas reales.
No sustituye a logging avanzado, pero crea una base clara para piloto.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json


@dataclass
class EventoLogPiloto:
    fecha_hora: str
    nivel: str
    modulo: str
    accion: str
    mensaje: str
    datos: Optional[Dict] = None


class LoggerPilotoHostAI:
    """
    Logger simple para piloto.

    Registra:
    - acciones importantes
    - errores controlados
    - avisos
    - eventos de uso real
    """

    NIVELES_VALIDOS = {"INFO", "AVISO", "ERROR", "CRITICO"}

    def __init__(self, ruta_log: str = "LOGS/host_ai_piloto.log") -> None:
        self.ruta_log = Path(ruta_log)
        self.ruta_log.parent.mkdir(parents=True, exist_ok=True)

    def registrar(
        self,
        nivel: str,
        modulo: str,
        accion: str,
        mensaje: str,
        datos: Optional[Dict] = None,
    ) -> EventoLogPiloto:
        nivel_normalizado = self._normalizar_nivel(nivel)

        evento = EventoLogPiloto(
            fecha_hora=datetime.now().isoformat(timespec="seconds"),
            nivel=nivel_normalizado,
            modulo=(modulo or "desconocido").strip(),
            accion=(accion or "sin_accion").strip(),
            mensaje=(mensaje or "").strip(),
            datos=datos or {},
        )

        self._escribir_evento(evento)
        return evento

    def info(self, modulo: str, accion: str, mensaje: str, datos: Optional[Dict] = None) -> EventoLogPiloto:
        return self.registrar("INFO", modulo, accion, mensaje, datos)

    def aviso(self, modulo: str, accion: str, mensaje: str, datos: Optional[Dict] = None) -> EventoLogPiloto:
        return self.registrar("AVISO", modulo, accion, mensaje, datos)

    def error(self, modulo: str, accion: str, mensaje: str, datos: Optional[Dict] = None) -> EventoLogPiloto:
        return self.registrar("ERROR", modulo, accion, mensaje, datos)

    def critico(self, modulo: str, accion: str, mensaje: str, datos: Optional[Dict] = None) -> EventoLogPiloto:
        return self.registrar("CRITICO", modulo, accion, mensaje, datos)

    def leer_eventos(self) -> List[Dict]:
        if not self.ruta_log.exists():
            return []

        eventos: List[Dict] = []
        for linea in self.ruta_log.read_text(encoding="utf-8").splitlines():
            if not linea.strip():
                continue
            try:
                eventos.append(json.loads(linea))
            except json.JSONDecodeError:
                eventos.append({"nivel": "ERROR", "mensaje": "Línea de log no válida", "linea": linea})
        return eventos

    def resumen(self) -> Dict[str, int]:
        resumen: Dict[str, int] = {}
        for evento in self.leer_eventos():
            nivel = evento.get("nivel", "DESCONOCIDO")
            resumen[nivel] = resumen.get(nivel, 0) + 1
        return resumen

    def _normalizar_nivel(self, nivel: str) -> str:
        nivel_normalizado = (nivel or "INFO").strip().upper()
        if nivel_normalizado not in self.NIVELES_VALIDOS:
            return "INFO"
        return nivel_normalizado

    def _escribir_evento(self, evento: EventoLogPiloto) -> None:
        with self.ruta_log.open("a", encoding="utf-8") as archivo:
            archivo.write(json.dumps(asdict(evento), ensure_ascii=False) + "\n")


__all__ = [
    "EventoLogPiloto",
    "LoggerPilotoHostAI",
]
