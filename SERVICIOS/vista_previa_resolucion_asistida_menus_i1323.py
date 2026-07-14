from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json

from SERVICIOS.constructor_arbol_semantico_menus_i1322 import (
    ConstructorArbolSemanticoMenusI1322,
    formatear_arbol_semantico_i1322,
)
from SERVICIOS.motor_reconocimiento_menus_i1321 import normalizar


@dataclass(frozen=True)
class DecisionResolucionI1323:
    texto_origen: str
    rol: str
    accion: str
    nombre_destino: str = ""
    tipo_destino: str = ""
    entidad_id: str = ""
    confianza: float = 1.0

    def a_dict(self) -> dict[str, Any]:
        return asdict(self)


class VistaPreviaResolucionAsistidaMenusI1323:
    """I1.3.2.3 — vista previa inteligente y resolución asistida.

    No importa menús ni crea recetas/artículos. Las decisiones se aplican a la
    vista previa. Solo se guardan en memoria si el usuario lo confirma.
    """

    VERSION = "I1.3.2.3"

    def __init__(self, base_dir: str | Path, constructor: ConstructorArbolSemanticoMenusI1322 | None = None):
        self.base_dir = Path(base_dir).resolve()
        self.constructor = constructor or ConstructorArbolSemanticoMenusI1322(self.base_dir)
        self.motor = self.constructor.motor
        self.ruta_memoria = self.base_dir / "DATOS" / "db" / "memoria_resoluciones_menu_i1323.json"
        self.memoria = self._cargar_memoria()

    def _cargar_memoria(self) -> dict[str, dict[str, Any]]:
        if not self.ruta_memoria.exists():
            return {}
        try:
            data = json.loads(self.ruta_memoria.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def guardar_decision(self, decision: DecisionResolucionI1323) -> None:
        clave = normalizar(decision.texto_origen)
        self.memoria[clave] = decision.a_dict()
        self.ruta_memoria.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.ruta_memoria.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.memoria, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.ruta_memoria)

    def candidatos(self, texto: str, limite: int = 8) -> dict[str, list[dict[str, Any]]]:
        q = normalizar(texto)
        def score(nombre: str) -> tuple[int, int, str]:
            n = normalizar(nombre)
            contiene = 0 if q and q in n else 1
            comun = -len(set(q.split()) & set(n.split()))
            return (contiene, comun, n)
        recetas = sorted(self.motor.recetas, key=lambda e: score(e.nombre))[:limite]
        articulos = sorted(self.motor.articulos, key=lambda e: score(e.nombre))[:limite]
        return {
            "recetas": [{"tipo":"RECETA","entidad_id":e.entidad_id,"nombre":e.nombre,"origen":e.origen} for e in recetas],
            "articulos": [{"tipo":"ARTICULO","entidad_id":e.entidad_id,"nombre":e.nombre,"origen":e.origen} for e in articulos],
        }

    @staticmethod
    def _iter_pendientes(arbol: dict[str, Any]):
        for grupo, rol in (("elaboraciones","ELABORACION"),("guarniciones","GUARNICION"),("salsas","SALSA"),("componentes_pendientes","COMPONENTE_PENDIENTE")):
            for idx, item in enumerate(arbol.get(grupo, [])):
                if not item.get("catalogado"):
                    yield grupo, idx, rol, item

    def _aplicar_decision(self, sem: dict[str, Any], decision: dict[str, Any]) -> bool:
        clave = normalizar(decision.get("texto_origen"))
        arbol = sem["arbol"]
        for grupo, idx, rol, item in list(self._iter_pendientes(arbol)):
            if normalizar(item.get("nombre")) != clave:
                continue
            accion = decision.get("accion")
            if accion == "MANTENER_PENDIENTE":
                item["resolucion"] = "MANTENIDO_PENDIENTE"
                return True
            nuevo = {
                "rol": decision.get("rol") or rol,
                "nombre": decision.get("nombre_destino") or item.get("nombre"),
                "tipo_entidad": decision.get("tipo_destino") or "PROPUESTA_RECETA",
                "entidad_id": decision.get("entidad_id") or "",
                "estado": "RESUELTO_ASISTIDO" if accion != "PROPONER_NUEVA_RECETA" else "PROPUESTA_NUEVA_RECETA",
                "confianza": float(decision.get("confianza") or 1.0),
                "catalogado": accion in {"VINCULAR_RECETA", "VINCULAR_ARTICULO"},
                "origen": "memoria_i1323" if decision.get("recordada") else "sesion_i1323",
                "resolucion": accion,
            }
            arbol[grupo][idx] = nuevo
            return True
        return False

    def preparar_desde_excel(self, ruta_excel: str | Path, hojas: list[str] | None = None) -> dict[str, Any]:
        base = self.constructor.preparar_desde_excel(ruta_excel, hojas=hojas)
        pendientes = []
        recordadas = 0
        for menu in base.get("menus", []):
            for plato in menu.get("platos", []):
                sem = plato["semantica"]
                for _, _, rol, item in list(self._iter_pendientes(sem["arbol"])):
                    clave = normalizar(item.get("nombre"))
                    decision = self.memoria.get(clave)
                    if decision:
                        d = dict(decision); d["recordada"] = True
                        if self._aplicar_decision(sem, d):
                            recordadas += 1
                    else:
                        pendientes.append({"menu":menu.get("nombre"),"plato":plato.get("nombre"),"texto":item.get("nombre"),"rol":rol})
        base["version"] = self.VERSION
        base["resumen_resolucion"] = {"pendientes_revision":len(pendientes),"decisiones_recordadas_aplicadas":recordadas}
        base["pendientes_revision"] = pendientes
        base["importacion_disponible"] = False
        base["datos_modificados"] = False
        return base

    def aplicar_decision(self, resultado: dict[str, Any], texto_origen: str, rol: str, accion: str,
                         destino: dict[str, Any] | None = None, recordar: bool = False) -> bool:
        destino = destino or {}
        decision = DecisionResolucionI1323(
            texto_origen=texto_origen, rol=rol, accion=accion,
            nombre_destino=str(destino.get("nombre") or texto_origen),
            tipo_destino=str(destino.get("tipo") or ""),
            entidad_id=str(destino.get("entidad_id") or ""),
            confianza=1.0,
        )
        aplicada = False
        for menu in resultado.get("menus", []):
            for plato in menu.get("platos", []):
                aplicada = self._aplicar_decision(plato["semantica"], decision.a_dict()) or aplicada
        if aplicada and recordar:
            self.guardar_decision(decision)
        resultado["pendientes_revision"] = [p for p in resultado.get("pendientes_revision", []) if normalizar(p.get("texto")) != normalizar(texto_origen)]
        resultado["resumen_resolucion"]["pendientes_revision"] = len(resultado["pendientes_revision"])
        resultado["datos_modificados"] = bool(recordar and aplicada)
        return aplicada


def formatear_vista_previa_i1323(resultado: dict[str, Any]) -> str:
    texto = formatear_arbol_semantico_i1322(resultado)
    rr = resultado.get("resumen_resolucion", {})
    lineas = texto.splitlines()
    lineas[0] = "I1.3.2.3 — VISTA PREVIA INTELIGENTE Y RESOLUCIÓN ASISTIDA"
    pies_i1322 = {
        "SOLO ÁRBOL SEMÁNTICO: no se creó ninguna receta ni componente pendiente.",
        "No se importó ningún menú y no se modificó la base de datos.",
        "I1.3.2.2 no permite importar.",
    }
    lineas = [linea for linea in lineas if linea not in pies_i1322]
    lineas.extend([
        f"Pendientes de revisión: {rr.get('pendientes_revision',0)} | Decisiones recordadas aplicadas: {rr.get('decisiones_recordadas_aplicadas',0)}",
        "RESOLUCIÓN ASISTIDA: las decisiones solo afectan a la vista previa; únicamente se recuerdan con confirmación explícita.",
        "No se importó ningún menú ni se creó ninguna receta o artículo.",
    ])
    return "\n".join(lineas)
