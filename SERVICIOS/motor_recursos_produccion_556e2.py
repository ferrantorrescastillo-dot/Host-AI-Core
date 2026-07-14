from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

from SERVICIOS.motor_tiempos_produccion_556e1 import MotorTiemposProduccion556E1


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text).strip(" .")


def _load(path: Path, default: Any) -> Any:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError): return default


class MotorRecursosProduccion556E2:
    VERSION = "5.5.6E.2"

    REGLAS = {
        "preparar": ["mesa_trabajo", "bascula"],
        "cocinar": ["fogones"],
        "cocer": ["fogones"],
        "hornear": ["horno"],
        "freir": ["freidora"],
        "enfriar": ["abatidor", "camara_fria"],
        "reposar": ["camara_fria"],
        "mezclar": ["mesa_trabajo"],
        "porcionar": ["mesa_trabajo", "bascula"],
        "envasar": ["mesa_trabajo", "envasadora"],
        "etiquetar": ["impresora_etiquetas"],
        "guardar": ["camara_fria"],
        "control": ["mesa_trabajo"],
    }

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.tiempos = MotorTiemposProduccion556E1(self.base_dir)
        self.config_path = self.base_dir / "DATOS" / "config" / "recursos_cocina_556e2.json"
        self.config = _load(self.config_path, {})

    def _recursos_para_fase(self, fase: Dict[str, Any]) -> List[str]:
        texto = _norm(f"{fase.get('fase','')} {fase.get('descripcion','')}")
        recursos: List[str] = []
        for clave, valores in self.REGLAS.items():
            if clave in texto:
                recursos.extend(valores)
        # Si no hay regla específica, una tarea activa necesita una mesa de trabajo.
        if not recursos and fase.get("tipo_tiempo") == "activo": recursos.append("mesa_trabajo")
        return list(dict.fromkeys(recursos))

    def analizar(self, termino: str, objetivo: float, unidad_objetivo: str = "personas") -> Dict[str, Any]:
        estimacion = self.tiempos.estimar(termino, objetivo, unidad_objetivo)
        disponibilidad = self.config.get("recursos", {}) if isinstance(self.config, dict) else {}
        fases=[]; incidencias=[]
        for fase in estimacion["fases"]:
            requeridos=self._recursos_para_fase(fase)
            detalle=[]
            for recurso in requeridos:
                cantidad=int(disponibilidad.get(recurso, 0) or 0)
                estado="DISPONIBLE" if cantidad>0 else "NO_CONFIGURADO"
                detalle.append({"recurso":recurso,"cantidad_disponible":cantidad,"estado":estado})
                if cantidad<=0:
                    incidencias.append({"gravedad":"MEDIO","fase":fase["fase"],"recurso":recurso,"motivo":"Recurso no configurado o sin disponibilidad registrada."})
            fases.append({**fase,"recursos":detalle})
        return {
            "version":self.VERSION,"receta":estimacion["receta"],"objetivo":objetivo,"unidad_objetivo":unidad_objetivo,
            "fases":fases,"recursos_configurados":disponibilidad,"incidencias":incidencias,
            "estado":"RECURSOS_OK" if not incidencias else "RECURSOS_A_REVISAR",
            "fuente_tiempos":estimacion["fuente_tiempos"],"solo_lectura":True,"datos_reales_modificados":False,
        }

    def detectar_conflictos(self, producciones: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detecta conflictos simples cuando varias producciones se solapan en la misma franja.

        Cada producción: receta, objetivo, inicio_min (minutos desde inicio de jornada), unidad opcional.
        """
        ocupaciones: Dict[str, List[Dict[str, Any]]] = {}
        planes=[]
        for prod in producciones:
            analisis=self.analizar(prod["receta"],float(prod["objetivo"]),prod.get("unidad","personas"))
            cursor=int(prod.get("inicio_min",0))
            for fase in analisis["fases"]:
                inicio=cursor; fin=inicio+int(fase["duracion_estimada_min"])
                for r in fase["recursos"]:
                    recurso=r["recurso"]
                    ocupaciones.setdefault(recurso,[]).append({"receta":analisis["receta"],"fase":fase["fase"],"inicio":inicio,"fin":fin})
                cursor=fin
            planes.append({"receta":analisis["receta"],"inicio":int(prod.get("inicio_min",0)),"fin":cursor})
        conflictos=[]
        disponibilidad=self.config.get("recursos",{}) if isinstance(self.config,dict) else {}
        for recurso, usos in ocupaciones.items():
            capacidad=max(int(disponibilidad.get(recurso,0) or 0),1)
            puntos=sorted({u["inicio"] for u in usos}|{u["fin"] for u in usos})
            for a,b in zip(puntos,puntos[1:]):
                activos=[u for u in usos if u["inicio"]<b and u["fin"]>a]
                if len(activos)>capacidad:
                    conflictos.append({"recurso":recurso,"inicio":a,"fin":b,"capacidad":capacidad,"demanda":len(activos),"usos":activos})
        return {"version":self.VERSION,"planes":planes,"conflictos":conflictos,"estado":"CONFLICTOS_DETECTADOS" if conflictos else "SIN_CONFLICTOS","solo_lectura":True,"datos_reales_modificados":False}


def formatear_recursos_556e2(resultado: Dict[str, Any]) -> str:
    lines=[f"RECURSOS DE PRODUCCIÓN — {resultado['receta']}",f"- Objetivo: {resultado['objetivo']:g} {resultado['unidad_objetivo']}",f"- Estado: {resultado['estado']}","","FASES Y RECURSOS"]
    for f in resultado["fases"]:
        nombres=", ".join(f"{r['recurso']} ({r['estado']})" for r in f["recursos"]) or "sin recurso específico"
        lines.append(f"{f['orden']}. {f['fase']} — {f['duracion_estimada_min']} min | {nombres}")
    if resultado["incidencias"]:
        lines += ["","INCIDENCIAS"]
        for i in resultado["incidencias"]: lines.append(f"- [{i['gravedad']}] {i['fase']}: {i['recurso']} — {i['motivo']}")
    lines += ["","SEGURIDAD","- Análisis en modo solo lectura.","- No se han reservado recursos ni creado órdenes."]
    return "\n".join(lines)

__all__=["MotorRecursosProduccion556E2","formatear_recursos_556e2"]
