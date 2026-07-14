from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from SERVICIOS.clasificador_gastronomico_i13412 import ClasificadorGastronomicoI13412, _norm
from SERVICIOS.simulador_importacion_menus_i13411 import SimuladorImportacionMenusI13411, _stable_id


class SimuladorImportacionMenusI13412(SimuladorImportacionMenusI13411):
    """I1.3.4.1.2 — simulación multimenú con clasificación gastronómica previa."""

    VERSION = "I1.3.4.1.2"

    def __init__(self, base_dir: str | Path):
        super().__init__(base_dir)
        self.clasificador = ClasificadorGastronomicoI13412()

    @staticmethod
    def _deduplicar_secciones(secciones: list[Any]) -> list[Any]:
        vistas: set[str] = set()
        salida: list[Any] = []
        for sec in secciones:
            nombre = sec.get("nombre") if isinstance(sec, dict) else str(sec)
            clave = _norm(nombre)
            if not clave or clave in vistas:
                continue
            vistas.add(clave)
            salida.append(sec)
        return salida

    def _clasificar_preimportacion(self, pre: dict[str, Any]) -> dict[str, Any]:
        resultado = deepcopy(pre)
        resumen_tipos: dict[str, int] = {}
        bloqueos_validos: list[dict[str, Any]] = []

        for menu in resultado.get("menus", []):
            nombre_menu = str(menu.get("nombre") or "")
            menu["secciones"] = self._deduplicar_secciones(menu.get("secciones", []))
            nuevos_platos: list[dict[str, Any]] = []
            articulos = list(menu.get("articulos_directos", []))
            complementos = list(menu.get("complementos", []))
            bebidas = list(menu.get("bebidas", []))
            clasificaciones: list[dict[str, Any]] = []

            for plato in menu.get("platos", []):
                nombre = str(plato.get("nombre_original") or "")
                clasif = self.clasificador.clasificar(nombre, plato.get("componentes", []))
                cd = clasif.to_dict()
                cd.update({"nombre": nombre, "fila": plato.get("fila"), "seccion": plato.get("seccion")})
                clasificaciones.append(cd)
                resumen_tipos[clasif.tipo] = resumen_tipos.get(clasif.tipo, 0) + 1

                if clasif.activa_arbol_semantico:
                    componentes_filtrados = []
                    for comp in plato.get("componentes", []):
                        if not comp.get("catalogado") and self.clasificador.es_ruido_semantico(str(comp.get("nombre") or ""), nombre_menu):
                            continue
                        componentes_filtrados.append(comp)
                    plato["componentes"] = componentes_filtrados
                    plato["clasificacion_gastronomica"] = cd
                    nuevos_platos.append(plato)
                else:
                    registro = {
                        "fila": plato.get("fila"),
                        "nombre": nombre,
                        "seccion": plato.get("seccion"),
                        "cantidad": plato.get("cantidad"),
                        "coste_racion": plato.get("coste_racion"),
                        "clasificacion_gastronomica": cd,
                    }
                    if clasif.destino_importacion == "BEBIDA_MENU":
                        bebidas.append(registro)
                    elif clasif.destino_importacion == "COMPLEMENTO_MENU":
                        complementos.append(registro)
                    else:
                        articulos.append(registro)

            # Clasifica también artículos y complementos ya detectados.
            for grupo, items in (("articulos_directos", articulos), ("complementos", complementos), ("bebidas", bebidas)):
                for item in items:
                    if "clasificacion_gastronomica" not in item:
                        c = self.clasificador.clasificar(str(item.get("nombre") or ""), [])
                        item["clasificacion_gastronomica"] = c.to_dict()
                        resumen_tipos[c.tipo] = resumen_tipos.get(c.tipo, 0) + 1

            menu["platos"] = nuevos_platos
            menu["articulos_directos"] = self._deduplicar_entidades(articulos)
            menu["complementos"] = self._deduplicar_entidades(complementos)
            menu["bebidas"] = self._deduplicar_entidades(bebidas)
            menu["clasificaciones_gastronomicas"] = clasificaciones

        # Solo conserva bloqueos que siguen existiendo después del filtrado.
        pendientes_validos = set()
        for menu in resultado.get("menus", []):
            for plato in menu.get("platos", []):
                for comp in plato.get("componentes", []):
                    if not comp.get("catalogado"):
                        pendientes_validos.add((_norm(menu.get("nombre")), _norm(plato.get("nombre_original")), _norm(comp.get("nombre"))))
        for bloqueo in resultado.get("bloqueos", []):
            clave = (_norm(bloqueo.get("menu")), _norm(bloqueo.get("plato")), _norm(bloqueo.get("componente") or bloqueo.get("nombre")))
            if clave in pendientes_validos:
                bloqueos_validos.append(bloqueo)
        resultado["bloqueos"] = bloqueos_validos
        resultado["estado_preimportacion"] = "LISTA" if not bloqueos_validos else "BLOQUEADA"
        resultado["clasificacion_gastronomica"] = {
            "version": self.VERSION,
            "tipos": resumen_tipos,
            "total": sum(resumen_tipos.values()),
        }
        return resultado

    @staticmethod
    def _deduplicar_entidades(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        vistas: set[tuple[str, str]] = set()
        salida = []
        for item in items:
            clave = (_norm(item.get("nombre")), _norm(item.get("seccion")))
            if not clave[0] or clave in vistas:
                continue
            vistas.add(clave)
            salida.append(item)
        return salida

    def construir_plan(self, pre: dict[str, Any], menus_existentes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        pre_clasificada = self._clasificar_preimportacion(pre)
        plan = super().construir_plan(pre_clasificada, menus_existentes)
        plan["version"] = self.VERSION
        plan["clasificacion_gastronomica"] = pre_clasificada.get("clasificacion_gastronomica", {})

        # Añade bebidas como relaciones propias, nunca como PLATO_MENU.
        acciones = plan.get("acciones", [])
        existentes_acc = {(a.get("entidad"), _norm(a.get("nombre")), _norm(a.get("detalle", {}).get("menu"))) for a in acciones}
        for menu in pre_clasificada.get("menus", []):
            nombre_menu = str(menu.get("nombre") or "")
            menu_acc = next((a for a in acciones if a.get("entidad") == "MENU" and _norm(a.get("nombre")) == _norm(nombre_menu)), None)
            menu_id = (menu_acc or {}).get("detalle", {}).get("menu_id") or _stable_id("MENU", nombre_menu, menu.get("hoja"))
            for bebida in menu.get("bebidas", []):
                clave = ("BEBIDA_MENU", _norm(bebida.get("nombre")), _norm(nombre_menu))
                if clave in existentes_acc:
                    continue
                acciones.append(self._accion(
                    "VINCULAR", "BEBIDA_MENU", str(bebida.get("nombre") or ""),
                    menu=nombre_menu, menu_id=menu_id, subtipo=bebida.get("clasificacion_gastronomica", {}).get("tipo"),
                    coste_racion=bebida.get("coste_racion"),
                ))
                existentes_acc.add(clave)

        # Regenera identificadores deterministas incluyendo menu_id e índice. Esto evita
        # colisiones cuando varias hojas tienen el mismo título interno de menú.
        for indice, accion in enumerate(acciones, 1):
            d = accion.get("detalle", {})
            accion["accion_id"] = _stable_id(
                "ACT", self.VERSION, indice, accion.get("tipo"), accion.get("entidad"),
                accion.get("nombre"), d.get("menu_id"), d.get("plato"), d.get("seccion"),
            )

        # Recalcula resumen tras añadir bebidas.
        bloqueadas = [a for a in acciones if a.get("estado") == "BLOQUEADA"]
        ejecutables = [a for a in acciones if a.get("estado") == "PLANIFICADA"]
        plan["resumen"].update({
            "acciones": len(acciones),
            "ejecutables": len(ejecutables),
            "bloqueadas": len(bloqueadas),
            "vincular": sum(1 for a in acciones if a.get("tipo") == "VINCULAR"),
            "relaciones": sum(1 for a in acciones if a.get("tipo") in {"CREAR_RELACION", "CREAR_O_REUTILIZAR"}),
            "bebidas": sum(1 for a in acciones if a.get("entidad") == "BEBIDA_MENU"),
        })
        plan["estado_simulacion"] = "LISTA_PARA_TRANSACCION" if acciones and not plan.get("bloqueos") and not bloqueadas else "BLOQUEADA"
        plan["plan_id"] = _stable_id("PLAN", self.VERSION, *(a["accion_id"] for a in acciones))
        return plan

    def simular(self, ruta_excel: str | Path, hojas: list[str] | None = None, incluir_probables: bool = False) -> dict[str, Any]:
        # Copia del flujo padre, sustituyendo únicamente la construcción del plan.
        deteccion = self.detectar_menus(ruta_excel)
        candidatas = list(deteccion.get("hojas_confirmadas", []))
        if incluir_probables:
            candidatas.extend(x for x in deteccion.get("hojas_probables", []) if x not in candidatas)
        seleccion = list(hojas) if hojas else candidatas
        disponibles = {x.get("hoja") for x in deteccion.get("confirmadas", []) + deteccion.get("probables", [])}
        inexistentes = [h for h in seleccion if h not in disponibles]
        if inexistentes:
            raise ValueError("Hojas no reconocidas como menú: " + ", ".join(inexistentes))
        if not seleccion:
            raise ValueError("No se detectaron hojas de menú para simular.")
        antes = self._huellas()
        pre = self.preimportador.preparar(ruta_excel, hojas=seleccion)
        existentes = self._menus_existentes()
        plan = self.construir_plan(pre, existentes)
        despues = self._huellas()
        cambios = [ruta for ruta in antes if antes[ruta] != despues[ruta]]
        crear = sum(1 for a in plan.get("acciones", []) if a.get("entidad") == "MENU" and a.get("tipo") == "CREAR")
        actualizar = sum(1 for a in plan.get("acciones", []) if a.get("entidad") == "MENU" and a.get("tipo") == "ACTUALIZAR")
        plan["deteccion_multihoja"] = deteccion
        plan["seleccion"] = {
            "hojas_seleccionadas": seleccion,
            "menus_detectados_en_archivo": len(candidatas),
            "menus_seleccionados": len(seleccion),
            "menus_existentes_en_host_ai": len(existentes),
            "menus_a_crear": crear,
            "menus_a_actualizar": actualizar,
        }
        plan["integridad"] = {"huellas_antes": antes, "huellas_despues": despues, "archivos_modificados": cambios, "sin_escrituras": not cambios}
        plan["datos_modificados"] = bool(cambios)
        if cambios:
            plan["estado_simulacion"] = "ERROR_INTEGRIDAD"
        return plan


def formatear_simulacion_i13412(resultado: dict[str, Any]) -> str:
    r = resultado.get("resumen", {})
    sel = resultado.get("seleccion", {})
    det = resultado.get("deteccion_multihoja", {})
    cg = resultado.get("clasificacion_gastronomica", {})
    integ = resultado.get("integridad", {})
    lineas = [
        "I1.3.4.1.2 — CLASIFICADOR GASTRONÓMICO Y SIMULACIÓN MULTIMENÚ",
        "=" * 78,
        "ARCHIVO ANALIZADO",
        f"Hojas: {det.get('hojas_totales', 0)} | Menús detectados: {sel.get('menus_detectados_en_archivo', 0)} | Seleccionados: {sel.get('menus_seleccionados', 0)}",
        "-" * 78,
        "BASE DE DATOS HOST AI",
        f"Menús existentes: {sel.get('menus_existentes_en_host_ai', 0)} | Se crearán: {sel.get('menus_a_crear', 0)} | Se actualizarán: {sel.get('menus_a_actualizar', 0)}",
        "-" * 78,
        "CLASIFICACIÓN GASTRONÓMICA",
        f"Elementos clasificados: {cg.get('total', 0)} | Tipos: " + ", ".join(f"{k}={v}" for k, v in sorted(cg.get('tipos', {}).items())),
        "-" * 78,
        "PLAN DE IMPORTACIÓN (SOLO SIMULACIÓN)",
        f"Plan: {resultado.get('plan_id')} | Estado: {resultado.get('estado_simulacion')}",
        f"Acciones: {r.get('acciones', 0)} | Ejecutables: {r.get('ejecutables', 0)} | Bloqueadas: {r.get('bloqueadas', 0)} | Bebidas: {r.get('bebidas', 0)}",
    ]
    for a in resultado.get("acciones", []):
        marca = "✖" if a.get("estado") == "BLOQUEADA" else "•"
        d = a.get("detalle", {})
        extra = []
        if d.get("menu"): extra.append(f"menú={d['menu']}")
        if d.get("plato"): extra.append(f"plato={d['plato']}")
        if d.get("subtipo"): extra.append(f"tipo={d['subtipo']}")
        sufijo = " | " + " | ".join(extra) if extra else ""
        lineas.append(f"{marca} [{a.get('estado')}] {a.get('tipo')} {a.get('entidad')}: {a.get('nombre')}{sufijo}")
    lineas.extend([
        "=" * 78,
        f"Integridad: {'OK, 0 escrituras' if integ.get('sin_escrituras') else 'ERROR, hubo cambios'}",
        "Las bebidas, vinos, aguas, cafés, panes, A.P, M.P, artículos comerciales y servicios no activan el árbol semántico.",
        "I1.3.4.1.2 sigue siendo solo simulación y no permite importar.",
    ])
    return "\n".join(lineas)
