from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import re

from SERVICIOS.motor_reconocimiento_menus_i1321 import (
    MotorReconocimientoMenusI1321,
    normalizar,
)


CONECTORES = {
    "a", "al", "amb", "acompanada", "acompanado", "con", "de", "del",
    "el", "en", "i", "la", "las", "los", "sobre", "y", "una", "un",
    "servida", "servido", "servides", "servidos",
}

PALABRAS_SALSA = {
    "salsa", "alioli", "allioli", "mojo", "vinagreta", "mayonesa", "mahonesa",
    "romesco", "pesto", "demiglace", "demi", "glace",
}
PALABRAS_GUARNICION = {
    "parmentier", "pure", "patata", "patatas", "arroz", "verdura", "verduras",
    "ensalada", "guarnicion", "guarnicio", "cuscus", "couscous", "polenta",
    "boniato", "esparragos", "setas",
}
PALABRAS_ELABORACION = {
    "crema", "espuma", "gel", "crujiente", "tierra", "aceite", "reduccion",
    "caldo", "fondo", "consome", "pico", "gallo", "guacamole",
}


@dataclass(frozen=True)
class ComponenteSemanticoI1322:
    rol: str
    nombre: str
    tipo_entidad: str
    entidad_id: str
    estado: str
    confianza: float
    catalogado: bool
    origen: str

    def a_dict(self) -> dict[str, Any]:
        return asdict(self)


class ConstructorArbolSemanticoMenusI1322:
    """I1.3.2.2 — convierte reconocimiento en árbol culinario sin escribir datos.

    Reglas de seguridad:
    - una RECETA_COMPLETA se conserva como receta principal;
    - en un mapa parcial, la primera receta no auxiliar es la principal;
    - salsas/guarniciones/elaboraciones se clasifican por conocimiento explícito;
    - texto no catalogado se conserva como pendiente, nunca se crea una receta;
    - no importa menús ni modifica catálogos o base de datos.
    """

    VERSION = "I1.3.2.2"

    def __init__(self, base_dir: str | Path, motor: MotorReconocimientoMenusI1321 | None = None):
        self.base_dir = Path(base_dir).resolve()
        self.motor = motor or MotorReconocimientoMenusI1321(self.base_dir)

    @staticmethod
    def _rol_por_nombre(nombre: str) -> str | None:
        tokens = set(normalizar(nombre).split())
        if tokens & PALABRAS_SALSA:
            return "SALSA"
        if tokens & PALABRAS_GUARNICION:
            return "GUARNICION"
        if tokens & PALABRAS_ELABORACION:
            return "ELABORACION"
        return None

    @staticmethod
    def _segmentos_sin_resolver(texto: str, coincidencias: list[dict[str, Any]]) -> list[str]:
        tokens = normalizar(texto).split()
        ocupados = {i for c in coincidencias for i in range(int(c["inicio_token"]), int(c["fin_token"]))}
        segmentos: list[list[str]] = []
        actual: list[str] = []
        for i, token in enumerate(tokens):
            if i in ocupados:
                if actual:
                    segmentos.append(actual)
                    actual = []
                continue
            if token in CONECTORES:
                if actual:
                    segmentos.append(actual)
                    actual = []
                continue
            actual.append(token)
        if actual:
            segmentos.append(actual)
        return [" ".join(s).strip() for s in segmentos if " ".join(s).strip()]

    @classmethod
    def _rol_pendiente(cls, segmento: str) -> str:
        return cls._rol_por_nombre(segmento) or "COMPONENTE_PENDIENTE"

    @staticmethod
    def _componente(c: dict[str, Any], rol: str) -> ComponenteSemanticoI1322:
        return ComponenteSemanticoI1322(
            rol=rol,
            nombre=str(c.get("nombre") or ""),
            tipo_entidad=str(c.get("tipo") or ""),
            entidad_id=str(c.get("entidad_id") or ""),
            estado=str(c.get("estado") or ""),
            confianza=float(c.get("confianza") or 0),
            catalogado=True,
            origen=str(c.get("origen") or ""),
        )

    def construir_texto(self, texto: str, reconocimiento: dict[str, Any] | None = None) -> dict[str, Any]:
        rec = reconocimiento or self.motor.reconocer_texto(texto)
        coincidencias = list(rec.get("coincidencias") or [])
        modo = rec.get("modo")

        principal: ComponenteSemanticoI1322 | None = None
        elaboraciones: list[ComponenteSemanticoI1322] = []
        guarniciones: list[ComponenteSemanticoI1322] = []
        salsas: list[ComponenteSemanticoI1322] = []
        articulos: list[ComponenteSemanticoI1322] = []
        pendientes: list[ComponenteSemanticoI1322] = []

        if modo == "RECETA_COMPLETA" and coincidencias:
            principal = self._componente(coincidencias[0], "RECETA_PRINCIPAL")
        elif modo == "ARTICULO_COMPLETO" and coincidencias:
            articulos.append(self._componente(coincidencias[0], "ARTICULO_DIRECTO"))
        else:
            # Se recorren por posición para respetar el orden del nombre del plato.
            for c in sorted(coincidencias, key=lambda x: (x.get("inicio_token", 0), x.get("fin_token", 0))):
                if c.get("tipo") == "ARTICULO":
                    articulos.append(self._componente(c, "ARTICULO_DIRECTO"))
                    continue
                rol_auxiliar = self._rol_por_nombre(str(c.get("nombre") or ""))
                if principal is None and rol_auxiliar is None:
                    principal = self._componente(c, "RECETA_PRINCIPAL")
                elif rol_auxiliar == "SALSA":
                    salsas.append(self._componente(c, "SALSA"))
                elif rol_auxiliar == "GUARNICION":
                    guarniciones.append(self._componente(c, "GUARNICION"))
                else:
                    elaboraciones.append(self._componente(c, "ELABORACION"))

            # Si todas las recetas reconocidas eran auxiliares, la primera conserva
            # la condición de principal para no dejar el plato sin núcleo.
            if principal is None:
                recetas = [c for c in coincidencias if c.get("tipo") == "RECETA"]
                if recetas:
                    primera = recetas[0]
                    nombre = str(primera.get("nombre") or "")
                    principal = self._componente(primera, "RECETA_PRINCIPAL")
                    elaboraciones = [x for x in elaboraciones if x.nombre != nombre]
                    guarniciones = [x for x in guarniciones if x.nombre != nombre]
                    salsas = [x for x in salsas if x.nombre != nombre]

        for segmento in self._segmentos_sin_resolver(texto, coincidencias):
            rol = self._rol_pendiente(segmento)
            pendiente = ComponenteSemanticoI1322(
                rol=rol,
                nombre=segmento,
                tipo_entidad="NO_CATALOGADO",
                entidad_id="",
                estado="PENDIENTE_CATALOGO",
                confianza=0.70 if rol != "COMPONENTE_PENDIENTE" else 0.50,
                catalogado=False,
                origen="texto_menu",
            )
            if rol == "SALSA":
                salsas.append(pendiente)
            elif rol == "GUARNICION":
                guarniciones.append(pendiente)
            elif rol == "ELABORACION":
                elaboraciones.append(pendiente)
            else:
                pendientes.append(pendiente)

        arbol = {
            "texto_original": texto,
            "receta_principal": principal.a_dict() if principal else None,
            "elaboraciones": [x.a_dict() for x in elaboraciones],
            "guarniciones": [x.a_dict() for x in guarniciones],
            "salsas": [x.a_dict() for x in salsas],
            "articulos_directos": [x.a_dict() for x in articulos],
            "componentes_pendientes": [x.a_dict() for x in pendientes],
        }
        total_pendientes = sum(
            1 for grupo in (elaboraciones, guarniciones, salsas, pendientes)
            for x in grupo if not x.catalogado
        )
        return {
            "version": self.VERSION,
            "reconocimiento": rec,
            "arbol": arbol,
            "estado_semantico": "COMPLETO" if principal and total_pendientes == 0 else (
                "PARCIAL" if principal or articulos else "SIN_NUCLEO"
            ),
            "componentes_no_catalogados": total_pendientes,
            "solo_vista_previa": True,
            "datos_modificados": False,
            "importacion_disponible": False,
        }

    def construir_previa(self, reconocimiento_previa: dict[str, Any]) -> dict[str, Any]:
        menus: list[dict[str, Any]] = []
        total = completos = parciales = sin_nucleo = pendientes = 0
        for menu in reconocimiento_previa.get("menus", []):
            platos = []
            for plato in menu.get("platos", []):
                sem = self.construir_texto(
                    str(plato.get("nombre") or ""),
                    plato.get("reconocimiento"),
                )
                platos.append({**plato, "semantica": sem})
                total += 1
                estado = sem["estado_semantico"]
                completos += estado == "COMPLETO"
                parciales += estado == "PARCIAL"
                sin_nucleo += estado == "SIN_NUCLEO"
                pendientes += int(sem["componentes_no_catalogados"])
            menus.append({
                "hoja": menu.get("hoja"),
                "nombre": menu.get("nombre"),
                "platos": platos,
                "articulos_directos": menu.get("articulos_directos", []),
                "complementos": menu.get("complementos", []),
            })
        return {
            "version": self.VERSION,
            "catalogo": reconocimiento_previa.get("catalogo", {}),
            "resumen": {
                "menus": len(menus), "platos": total, "arboles_completos": completos,
                "arboles_parciales": parciales, "sin_nucleo": sin_nucleo,
                "componentes_no_catalogados": pendientes,
            },
            "menus": menus,
            "solo_vista_previa": True,
            "datos_modificados": False,
            "importacion_disponible": False,
        }

    def preparar_desde_excel(self, ruta_excel: str | Path, hojas: list[str] | None = None) -> dict[str, Any]:
        reconocimiento = self.motor.preparar_desde_excel(ruta_excel, hojas=hojas)
        return self.construir_previa(reconocimiento)


def _linea_componente(prefijo: str, item: dict[str, Any]) -> str:
    marca = "✔" if item.get("catalogado") else "?"
    estado = "catalogado" if item.get("catalogado") else "pendiente de catálogo"
    return f"    {marca} {prefijo}: {item.get('nombre')} [{estado}]"


def formatear_arbol_semantico_i1322(resultado: dict[str, Any]) -> str:
    r = resultado.get("resumen", {})
    cat = resultado.get("catalogo", {})
    lineas = [
        "I1.3.2.2 — CONSTRUCTOR DEL ÁRBOL SEMÁNTICO",
        "=" * 78,
        f"Catálogo: {cat.get('recetas', 0)} recetas | {cat.get('articulos', 0)} artículos",
        f"Menús: {r.get('menus', 0)} | Platos: {r.get('platos', 0)} | "
        f"Árbol completo: {r.get('arboles_completos', 0)} | "
        f"Árbol parcial: {r.get('arboles_parciales', 0)} | "
        f"Sin núcleo: {r.get('sin_nucleo', 0)} | "
        f"No catalogados: {r.get('componentes_no_catalogados', 0)}",
    ]
    for menu in resultado.get("menus", []):
        lineas.append(f"\n{menu.get('nombre')} | Hoja: {menu.get('hoja')}")
        for plato in menu.get("platos", []):
            sem = plato.get("semantica", {})
            arbol = sem.get("arbol", {})
            lineas.append(f"- {plato.get('nombre')} [{sem.get('estado_semantico')}]")
            principal = arbol.get("receta_principal")
            if principal:
                lineas.append(_linea_componente("RECETA PRINCIPAL", principal))
            for item in arbol.get("elaboraciones", []):
                lineas.append(_linea_componente("ELABORACIÓN", item))
            for item in arbol.get("guarniciones", []):
                lineas.append(_linea_componente("GUARNICIÓN", item))
            for item in arbol.get("salsas", []):
                lineas.append(_linea_componente("SALSA", item))
            for item in arbol.get("articulos_directos", []):
                lineas.append(_linea_componente("ARTÍCULO DIRECTO", item))
            for item in arbol.get("componentes_pendientes", []):
                lineas.append(_linea_componente("COMPONENTE", item))
            if not any([
                principal, arbol.get("elaboraciones"), arbol.get("guarniciones"),
                arbol.get("salsas"), arbol.get("articulos_directos"),
                arbol.get("componentes_pendientes"),
            ]):
                lineas.append("    — Sin estructura reconocible")
    lineas.extend([
        "=" * 78,
        "SOLO ÁRBOL SEMÁNTICO: no se creó ninguna receta ni componente pendiente.",
        "No se importó ningún menú y no se modificó la base de datos.",
        "I1.3.2.2 no permite importar.",
    ])
    return "\n".join(lineas)
