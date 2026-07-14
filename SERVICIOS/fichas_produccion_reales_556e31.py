from __future__ import annotations

import json
import re
import shutil
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text).strip(" .")


def _load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _atomic_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_dir = path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    if path.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        shutil.copy2(path, backup_dir / f"{path.stem}_{stamp}{path.suffix}.bak")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, suffix=".tmp") as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp.flush()
        temp_path = Path(tmp.name)
    temp_path.replace(path)


class RepositorioFichasProduccion556E31:
    VERSION = "5.5.6E.3.1"
    TIPOS = {"activo", "pasivo", "mixto"}

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.path = self.base_dir / "DATOS" / "db" / "fichas_produccion_reales.json"

    def listar(self) -> List[Dict[str, Any]]:
        raw = _load(self.path, {"fichas": []})
        if isinstance(raw, list):
            return raw
        return list(raw.get("fichas", [])) if isinstance(raw, dict) else []

    def buscar(self, receta: str) -> Optional[Dict[str, Any]]:
        objetivo = _norm(receta)
        exactas = [f for f in self.listar() if _norm(f.get("receta")) == objetivo]
        if exactas:
            return exactas[0]
        parciales = [f for f in self.listar() if objetivo in _norm(f.get("receta")) or _norm(f.get("receta")) in objetivo]
        return parciales[0] if len(parciales) == 1 else None

    def validar(self, ficha: Dict[str, Any]) -> Dict[str, Any]:
        errores: List[str] = []
        avisos: List[str] = []
        receta = str(ficha.get("receta") or "").strip()
        if not receta:
            errores.append("Falta el nombre de la receta.")
        rendimiento = float(ficha.get("rendimiento_base") or 0)
        if rendimiento <= 0:
            errores.append("El rendimiento base debe ser mayor que cero.")
        fases = ficha.get("fases")
        if not isinstance(fases, list) or not fases:
            errores.append("Debe existir al menos una fase de producción.")
            fases = []
        for i, fase in enumerate(fases, start=1):
            if not str(fase.get("nombre") or fase.get("fase") or "").strip():
                errores.append(f"Fase {i}: falta nombre.")
            minutos = float(fase.get("duracion_base_min") or fase.get("duracion_min") or 0)
            if minutos <= 0:
                errores.append(f"Fase {i}: la duración debe ser mayor que cero.")
            tipo = str(fase.get("tipo_tiempo") or "activo").lower()
            if tipo not in self.TIPOS:
                errores.append(f"Fase {i}: tipo de tiempo no válido ({tipo}).")
            if tipo == "pasivo" and bool(fase.get("requiere_presencia", False)):
                avisos.append(f"Fase {i}: es pasiva pero requiere presencia; se tratará como mixta.")
        return {"valida": not errores, "errores": errores, "avisos": avisos}

    def guardar(self, ficha: Dict[str, Any], confirmar: bool = False) -> Dict[str, Any]:
        validacion = self.validar(ficha)
        if not validacion["valida"]:
            return {"estado": "FICHA_INVALIDA", **validacion, "datos_reales_modificados": False}
        normalizada = self._normalizar(ficha)
        existente = self.buscar(normalizada["receta"])
        if not confirmar:
            return {
                "estado": "PROPUESTA_LISTA",
                "accion": "ACTUALIZAR" if existente else "CREAR",
                "ficha": normalizada,
                **validacion,
                "datos_reales_modificados": False,
            }
        fichas = self.listar()
        replaced = False
        for idx, actual in enumerate(fichas):
            if _norm(actual.get("receta")) == _norm(normalizada["receta"]):
                normalizada["version"] = int(actual.get("version") or 1) + 1
                fichas[idx] = normalizada
                replaced = True
                break
        if not replaced:
            fichas.append(normalizada)
        payload = {"version_modelo": self.VERSION, "actualizado_en": datetime.now(timezone.utc).isoformat(), "fichas": fichas}
        _atomic_write(self.path, payload)
        return {
            "estado": "FICHA_ACTUALIZADA" if replaced else "FICHA_CREADA",
            "ficha": normalizada,
            **validacion,
            "datos_reales_modificados": True,
        }

    def _normalizar(self, ficha: Dict[str, Any]) -> Dict[str, Any]:
        fases = []
        for i, fase in enumerate(ficha.get("fases", []), start=1):
            tipo = str(fase.get("tipo_tiempo") or "activo").lower()
            requiere = bool(fase.get("requiere_presencia", tipo == "activo"))
            if tipo == "pasivo" and requiere:
                tipo = "mixto"
            fases.append({
                "orden": i,
                "nombre": str(fase.get("nombre") or fase.get("fase") or f"Fase {i}").strip(),
                "descripcion": str(fase.get("descripcion") or "").strip(),
                "duracion_base_min": int(round(float(fase.get("duracion_base_min") or fase.get("duracion_min") or 0))),
                "tipo_tiempo": tipo,
                "requiere_presencia": requiere,
                "escalable_por_volumen": bool(fase.get("escalable_por_volumen", tipo != "pasivo")),
                "recursos": list(dict.fromkeys(str(x).strip() for x in fase.get("recursos", []) if str(x).strip())),
                "puede_paralelizar": bool(fase.get("puede_paralelizar", tipo == "pasivo")),
                "punto_control": str(fase.get("punto_control") or "").strip(),
            })
        return {
            "id": str(ficha.get("id") or f"FPROD-{abs(hash(_norm(ficha.get('receta')))) % 10**10:010d}"),
            "receta": str(ficha.get("receta") or "").strip(),
            "rendimiento_base": float(ficha.get("rendimiento_base") or 1),
            "unidad_rendimiento": str(ficha.get("unidad_rendimiento") or "u").strip(),
            "version": int(ficha.get("version") or 1),
            "estado": "VALIDADA",
            "origen": str(ficha.get("origen") or "USUARIO").strip(),
            "validada_por": str(ficha.get("validada_por") or "jefe_cocina").strip(),
            "validada_en": datetime.now(timezone.utc).isoformat(),
            "fases": fases,
            "observaciones": str(ficha.get("observaciones") or "").strip(),
        }


def mensaje_falta_ficha_556e31(receta: str) -> str:
    return "\n".join([
        f"FALTA FICHA DE PRODUCCIÓN REAL — {receta}",
        "",
        "Tengo el escandallo de ingredientes, pero no tengo un proceso de elaboración validado.",
        "No voy a inventar fases, tiempos ni recursos y presentarlos como un planning real.",
        "",
        "SIGUIENTE PASO",
        "1. Pega o registra la receta/proceso real.",
        "2. Confirma fases, tiempos activos/pasivos y recursos.",
        "3. Después generaré el reparto profesional entre cocineros.",
        "",
        "Puedes crear una plantilla con:",
        f'python APP/gestionar_ficha_produccion_556e31.py "{receta}" --plantilla "ficha_{_norm(receta).replace(" ", "_")}.json"',
    ])


__all__ = ["RepositorioFichasProduccion556E31", "mensaje_falta_ficha_556e31"]
