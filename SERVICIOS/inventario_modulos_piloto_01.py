from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import hashlib


@dataclass(frozen=True)
class EntradaInventarioPiloto01:
    ruta: str
    categoria: str
    tamano: int
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class InventarioModulosPiloto01:
    DIRECTORIOS_ACTIVOS = {"APP", "CORE", "SERVICIOS", "MOTORES", "PIPELINES", "MODELOS"}
    DIRECTORIOS_PRUEBA = {"TESTS", "QA", "CERTIFICACION"}
    PREFIJOS_LEGACY = ("HOST_AI_", "Host_AI_", "Version")

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()

    def generar(self) -> dict[str, Any]:
        entradas: list[EntradaInventarioPiloto01] = []
        for ruta in sorted(self.base_dir.rglob("*.py")):
            if any(parte in {"__pycache__", ".pytest_cache", ".git", ".venv", "venv"} for parte in ruta.parts):
                continue
            relativo = ruta.relative_to(self.base_dir)
            categoria = self._clasificar(relativo)
            entradas.append(
                EntradaInventarioPiloto01(
                    ruta=relativo.as_posix(),
                    categoria=categoria,
                    tamano=ruta.stat().st_size,
                    sha256=self._sha256(ruta),
                )
            )
        resumen: dict[str, int] = {}
        for entrada in entradas:
            resumen[entrada.categoria] = resumen.get(entrada.categoria, 0) + 1
        return {
            "total_python": len(entradas),
            "resumen": dict(sorted(resumen.items())),
            "entradas": [entrada.to_dict() for entrada in entradas],
        }

    def _clasificar(self, relativo: Path) -> str:
        primero = relativo.parts[0] if relativo.parts else ""
        if primero in self.DIRECTORIOS_ACTIVOS:
            return "ACTIVO"
        if primero in self.DIRECTORIOS_PRUEBA or relativo.name.startswith("test_"):
            return "PRUEBA"
        if primero.startswith(self.PREFIJOS_LEGACY):
            return "LEGACY"
        if primero in {"HERRAMIENTAS", "DOCS", "Documentos"}:
            return "SOPORTE"
        return "HISTORICO_O_RAIZ"

    @staticmethod
    def _sha256(ruta: Path) -> str:
        digest = hashlib.sha256()
        with ruta.open("rb") as fh:
            for bloque in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(bloque)
        return digest.hexdigest()


__all__ = ["EntradaInventarioPiloto01", "InventarioModulosPiloto01"]
