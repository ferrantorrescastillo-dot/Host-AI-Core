from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from SERVICIOS.registro_logs_proyecto_4413 import RegistroLogsProyecto4413
except Exception:  # compatibilidad si se ejecuta aislado
    RegistroLogsProyecto4413 = None  # type: ignore


@dataclass
class ResultadoTestHostAI:
    archivo: str
    ok: bool
    duracion_segundos: float
    salida: str = ""
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RunnerTests4412:
    """
    Host AI 4.4.12 - Runner inteligente de tests.

    Permite lanzar tests por bloque sin recordar nombres de archivo.
    No sustituye pytest; usa los scripts actuales de TESTS para no romper arquitectura.
    """

    VERSION = "4.4.12"

    BLOQUES: Dict[str, Dict[str, Any]] = {
        "1": {"nombre": "Catálogo", "prefijos": ["test_41", "test_412", "test_413", "test_414", "test_415", "test_416", "test_417", "test_418", "test_419"]},
        "2": {"nombre": "Proveedores", "prefijos": ["test_42"]},
        "3": {"nombre": "Stock", "prefijos": ["test_43", "test_alertas_inteligentes_stock", "test_historico_inteligente_stock", "test_stock_por_ubicaciones"]},
        "4": {"nombre": "Recepción", "prefijos": ["test_44"]},
        "5": {"nombre": "Compras", "prefijos": ["test_inteligencia_compras", "test_analizador_inteligente_compras", "test_comparador_inteligente_proveedores", "test_detector_anomalias_compras"]},
        "6": {"nombre": "Producción", "prefijos": ["test_produccion", "test_analizador_inteligente_produccion", "test_planificador_inteligente_produccion", "test_motor_produccion_real", "test_pipeline_produccion"]},
        "7": {"nombre": "IA", "prefijos": ["test_ia", "test_asistente", "test_motor_conversacional", "test_memoria_conversacional", "test_generador_inteligente_respuestas", "test_selector_inteligente_motores"]},
        "8": {"nombre": "Todos", "prefijos": ["test_"]},
    }

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir).resolve()
        self.tests_dir = self.base_dir / "TESTS"
        self.logger = RegistroLogsProyecto4413(self.base_dir) if RegistroLogsProyecto4413 else None

    def bloques_disponibles(self) -> Dict[str, str]:
        return {k: v["nombre"] for k, v in self.BLOQUES.items()}

    def descubrir_tests(self, bloque: str = "8") -> List[Path]:
        if not self.tests_dir.exists():
            return []
        config = self.BLOQUES.get(str(bloque), self.BLOQUES["8"])
        prefijos = config["prefijos"]
        archivos = []
        for path in self.tests_dir.glob("test_*.py"):
            name = path.name
            if any(name.startswith(prefijo) for prefijo in prefijos):
                archivos.append(path)
        return sorted(set(archivos), key=lambda p: p.name)

    def ejecutar_archivo(self, archivo: str | Path, timeout: int = 120) -> ResultadoTestHostAI:
        path = Path(archivo)
        if not path.is_absolute():
            path = self.base_dir / path
        inicio = time.perf_counter()
        try:
            proceso = subprocess.run(
                [sys.executable, str(path)],
                cwd=str(self.base_dir),
                text=True,
                capture_output=True,
                timeout=timeout,
            )
            duracion = time.perf_counter() - inicio
            return ResultadoTestHostAI(
                archivo=path.name,
                ok=proceso.returncode == 0,
                duracion_segundos=round(duracion, 3),
                salida=(proceso.stdout or "")[-4000:],
                error=(proceso.stderr or "")[-4000:],
            )
        except subprocess.TimeoutExpired as exc:
            duracion = time.perf_counter() - inicio
            return ResultadoTestHostAI(path.name, False, round(duracion, 3), salida=exc.stdout or "", error=f"Timeout: {timeout}s")
        except Exception as exc:
            duracion = time.perf_counter() - inicio
            return ResultadoTestHostAI(path.name, False, round(duracion, 3), error=str(exc))

    def ejecutar_bloque(self, bloque: str = "8", timeout_por_test: int = 120) -> Dict[str, Any]:
        bloque = str(bloque)
        nombre = self.BLOQUES.get(bloque, self.BLOQUES["8"])["nombre"]
        archivos = self.descubrir_tests(bloque)
        inicio = time.perf_counter()
        resultados = [self.ejecutar_archivo(path, timeout=timeout_por_test) for path in archivos]
        duracion_total = round(time.perf_counter() - inicio, 3)
        ok_count = sum(1 for r in resultados if r.ok)
        fail_count = len(resultados) - ok_count
        informe = {
            "version": self.VERSION,
            "bloque": nombre,
            "total": len(resultados),
            "ok": ok_count,
            "fail": fail_count,
            "duracion_segundos": duracion_total,
            "resultados": [r.to_dict() for r in resultados],
            "lectura_host_ai": f"Runner tests {nombre}: {ok_count}/{len(resultados)} OK, {fail_count} FAIL.",
        }
        if self.logger:
            self.logger.registrar(
                modulo="TESTS",
                accion=f"ejecutar_bloque_{nombre}",
                duracion_segundos=duracion_total,
                ok=fail_count == 0,
                errores=[r.archivo for r in resultados if not r.ok],
                detalle={"bloque": nombre, "total": len(resultados), "ok": ok_count, "fail": fail_count},
            )
        return informe

    def imprimir_informe(self, informe: Dict[str, Any], mostrar_errores: bool = True) -> None:
        print("\n" + "=" * 60)
        print("HOST AI TEST REPORT")
        print("=" * 60)
        print(f"Bloque: {informe.get('bloque')}")
        print(f"Resultado: {informe.get('ok')} / {informe.get('total')} OK")
        print(f"Errores: {informe.get('fail')}")
        print(f"Tiempo: {informe.get('duracion_segundos')} s")
        print("-" * 60)
        for r in informe.get("resultados", []):
            marca = "OK" if r.get("ok") else "FAIL"
            print(f"[{marca}] {r.get('archivo')} ({r.get('duracion_segundos')} s)")
            if mostrar_errores and not r.get("ok"):
                err = (r.get("error") or r.get("salida") or "")[-1000:]
                if err:
                    print(err)
                    print("-" * 60)
