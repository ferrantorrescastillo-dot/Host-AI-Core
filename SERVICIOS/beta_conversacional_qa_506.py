
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from SERVICIOS.clasificador_intenciones_503 import ClasificadorIntenciones503


@dataclass
class ResultadoCasoQA506:
    id: str
    categoria: str
    usuario: str
    esperado: str
    obtenido: str
    confianza: float
    estado: str
    detalle: str


class BetaConversacionalQA506:
    """
    Host AI 5.0.6 - Beta Conversacional QA.

    Ejecuta conversaciones reales contra el clasificador/núcleo actual para medir
    comportamiento. No modifica stock, compras ni eventos. La Beta 1 evalúa si
    Host AI entiende la intención correcta antes de ejecutar motores.
    """

    VERSION = "5.0.6"

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self.qa_dir = self.base_dir / "QA"
        self.clasificador = ClasificadorIntenciones503()

    def cargar_casos(self, categoria: Optional[str] = None) -> List[Dict[str, Any]]:
        if categoria:
            ruta = self.qa_dir / categoria.upper() / "casos.json"
        else:
            ruta = self.qa_dir / "BETA_1_100_CONVERSACIONES.json"
        if not ruta.exists():
            raise FileNotFoundError(f"No existe la batería QA: {ruta}")
        return json.loads(ruta.read_text(encoding="utf-8"))

    def ejecutar(self, categoria: Optional[str] = None) -> Dict[str, Any]:
        casos = self.cargar_casos(categoria)
        resultados = [self.ejecutar_caso(c) for c in casos]
        return self.generar_informe(resultados)

    def ejecutar_caso(self, caso: Dict[str, Any]) -> ResultadoCasoQA506:
        texto = caso.get("usuario", "")
        esperado = caso.get("intencion_esperada", "")
        clasificacion = self.clasificador.clasificar(texto, {})
        ganadora = clasificacion.get("intencion_ganadora", {})
        obtenido = ganadora.get("intencion", "desconocida")
        confianza = float(ganadora.get("confianza", 0.0) or 0.0)

        if obtenido == esperado and confianza >= 0.55:
            estado = "OK"
            detalle = "Intención correcta con confianza suficiente."
        elif obtenido == esperado:
            estado = "PARCIAL"
            detalle = "Intención correcta, pero confianza baja."
        else:
            estado = "FAIL"
            detalle = f"Esperado {esperado}, obtenido {obtenido}."

        return ResultadoCasoQA506(
            id=caso.get("id", "SIN_ID"),
            categoria=caso.get("categoria", "general"),
            usuario=texto,
            esperado=esperado,
            obtenido=obtenido,
            confianza=round(confianza, 3),
            estado=estado,
            detalle=detalle,
        )

    def generar_informe(self, resultados: List[ResultadoCasoQA506]) -> Dict[str, Any]:
        total = len(resultados)
        ok = sum(1 for r in resultados if r.estado == "OK")
        parcial = sum(1 for r in resultados if r.estado == "PARCIAL")
        fail = sum(1 for r in resultados if r.estado == "FAIL")
        por_categoria: Dict[str, Dict[str, Any]] = {}
        for r in resultados:
            cat = r.categoria
            por_categoria.setdefault(cat, {"total": 0, "ok": 0, "parcial": 0, "fail": 0, "nota": 0.0})
            por_categoria[cat]["total"] += 1
            por_categoria[cat][r.estado.lower()] += 1
        for datos in por_categoria.values():
            datos["nota"] = round(((datos["ok"] + datos["parcial"] * 0.5) / max(datos["total"], 1)) * 100, 2)
        nota_global = round(((ok + parcial * 0.5) / max(total, 1)) * 100, 2)
        return {
            "version": self.VERSION,
            "nombre": "Host AI Beta Conversacional QA - Beta 1",
            "total": total,
            "ok": ok,
            "parcial": parcial,
            "fail": fail,
            "nota_global": nota_global,
            "por_categoria": por_categoria,
            "resultados": [asdict(r) for r in resultados],
            "fallos": [asdict(r) for r in resultados if r.estado == "FAIL"],
            "recomendacion": self._recomendacion(nota_global),
        }

    def guardar_informe(self, informe: Dict[str, Any]) -> Path:
        salida = self.base_dir / "DOCS" / "QA_BETA_1" / "INFORME_BETA_CONVERSACIONAL_506.json"
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        return salida

    def imprimir_informe(self, informe: Dict[str, Any]) -> None:
        print("=" * 70)
        print("HOST AI 5.0.6 - BETA CONVERSACIONAL QA")
        print("=" * 70)
        print(f"Total casos: {informe['total']}")
        print(f"OK: {informe['ok']} | PARCIAL: {informe['parcial']} | FAIL: {informe['fail']}")
        print(f"Nota global: {informe['nota_global']} / 100")
        print("\nPor categoría:")
        for cat, datos in sorted(informe["por_categoria"].items()):
            print(f"- {cat}: {datos['nota']}% ({datos['ok']} OK, {datos['parcial']} parcial, {datos['fail']} fail, total {datos['total']})")
        if informe["fallos"]:
            print("\nFallos principales:")
            for fallo in informe["fallos"][:20]:
                print(f"- {fallo['id']}: esperado {fallo['esperado']} | obtenido {fallo['obtenido']} | texto: {fallo['usuario']}")
        print("\nRecomendación:")
        print(informe["recomendacion"])

    def _recomendacion(self, nota: float) -> str:
        if nota >= 95:
            return "Release Candidate: la conversación está lista para prueba real controlada."
        if nota >= 85:
            return "Beta 2: buen nivel. Corregir fallos por categoría antes de interfaz avanzada."
        if nota >= 70:
            return "Beta 1 válida. Priorizar intención, memoria y selector de motores."
        return "Aún no está listo para beta real. Reforzar clasificador y rutas conversacionales."


__all__ = ["BetaConversacionalQA506", "ResultadoCasoQA506"]
