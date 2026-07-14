from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from SERVICIOS.preimportador_definitivo_menus_i133 import PreimportadorDefinitivoMenusI133
from SERVICIOS.detector_multihoja_menus_i13411 import DetectorMultihojaMenusI13411


def _norm(texto: Any) -> str:
    texto = str(texto or "").strip().lower()
    texto = re.sub(r"[^a-z0-9áéíóúüñç]+", " ", texto)
    return " ".join(texto.split())


def _stable_id(prefix: str, *parts: Any) -> str:
    raw = "|".join(_norm(p) for p in parts)
    return f"{prefix}-{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:12].upper()}"


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class SimuladorImportacionMenusI13411:
    """I1.3.4.1.1 — detecta y simula uno, varios o todos los menús sin escribir datos."""

    VERSION = "I1.3.4.1.1"
    RUTAS_VIGILADAS = (
        "DATOS/db/articulos.json",
        "DATOS/db/escandallos.json",
        "DATOS/db/escandallos_canonicos.json",
        "DATOS/db/menus.json",
        "DATOS/db/eventos.json",
        "DATOS/db/precios.json",
        "DATOS/db/stock_lotes.json",
        "DATOS/db/compras_pedidos.json",
    )

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir).resolve()
        self.preimportador = PreimportadorDefinitivoMenusI133(self.base_dir)
        self.detector_multihoja = DetectorMultihojaMenusI13411()

    def _huellas(self) -> dict[str, str | None]:
        return {ruta: _sha256(self.base_dir / ruta) for ruta in self.RUTAS_VIGILADAS}

    def _menus_existentes(self) -> list[dict[str, Any]]:
        ruta = self.base_dir / "DATOS" / "db" / "menus.json"
        if not ruta.exists():
            return []
        try:
            data = json.loads(ruta.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    @staticmethod
    def _accion(tipo: str, entidad: str, nombre: str, estado: str = "PLANIFICADA", **detalle: Any) -> dict[str, Any]:
        return {
            "accion_id": _stable_id("ACT", tipo, entidad, nombre, detalle.get("menu"), detalle.get("plato")),
            "tipo": tipo,
            "entidad": entidad,
            "nombre": nombre,
            "estado": estado,
            "detalle": detalle,
        }

    def construir_plan(self, pre: dict[str, Any], menus_existentes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        existentes = menus_existentes if menus_existentes is not None else self._menus_existentes()
        por_nombre = {_norm(m.get("nombre")): m for m in existentes}
        acciones: list[dict[str, Any]] = []
        avisos: list[dict[str, Any]] = []
        bloqueos = deepcopy(pre.get("bloqueos", []))

        for menu in pre.get("menus", []):
            nombre = str(menu.get("nombre") or "Menú sin nombre")
            existe = por_nombre.get(_norm(nombre))
            menu_id = (existe or {}).get("menu_id") or (existe or {}).get("id") or _stable_id("MENU", nombre, menu.get("hoja"))
            tipo_menu = "ACTUALIZAR" if existe else "CREAR"
            acciones.append(self._accion(tipo_menu, "MENU", nombre, menu_id=menu_id, hoja=menu.get("hoja")))

            for seccion in menu.get("secciones", []):
                nom_sec = seccion.get("nombre") if isinstance(seccion, dict) else str(seccion)
                if not nom_sec:
                    continue
                acciones.append(self._accion("CREAR_O_REUTILIZAR", "SECCION", nom_sec, menu=nombre, menu_id=menu_id))

            for plato in menu.get("platos", []):
                plato_nombre = str(plato.get("nombre_original") or "")
                acciones.append(self._accion(
                    "CREAR_RELACION", "PLATO_MENU", plato_nombre,
                    menu=nombre, menu_id=menu_id, seccion=plato.get("seccion"),
                    coste_racion=plato.get("coste_racion"), fila=plato.get("fila"),
                ))
                for comp in plato.get("componentes", []):
                    catalogado = bool(comp.get("catalogado"))
                    estado = "PLANIFICADA" if catalogado else "BLOQUEADA"
                    tipo = "VINCULAR" if catalogado else "RESOLVER_ANTES_DE_IMPORTAR"
                    acciones.append(self._accion(
                        tipo, comp.get("grupo") or "COMPONENTE", str(comp.get("nombre") or ""), estado,
                        menu=nombre, menu_id=menu_id, plato=plato_nombre,
                        rol=comp.get("rol"), catalogado=catalogado,
                        resolucion=comp.get("resolucion"),
                    ))

            for art in menu.get("articulos_directos", []):
                acciones.append(self._accion(
                    "VINCULAR", "ARTICULO_DIRECTO", str(art.get("nombre") or ""),
                    menu=nombre, menu_id=menu_id, coste_racion=art.get("coste_racion"),
                ))
            for comp in menu.get("complementos", []):
                acciones.append(self._accion(
                    "CREAR_RELACION", "COMPLEMENTO", str(comp.get("nombre") or ""),
                    menu=nombre, menu_id=menu_id,
                ))

            eco = menu.get("economico", {})
            acciones.append(self._accion(
                "REGISTRAR", "DATOS_ECONOMICOS", nombre,
                menu=nombre, menu_id=menu_id,
                precio_venta=eco.get("precio_venta"), venta_neta=eco.get("venta_neta"),
                coste_total=eco.get("coste_total"), food_cost_pct=eco.get("food_cost_pct"),
                beneficio=eco.get("beneficio"),
            ))

        if not pre.get("menus"):
            avisos.append({"codigo": "SIN_MENUS", "mensaje": "No se detectó ningún menú para simular."})

        ejecutables = [a for a in acciones if a["estado"] == "PLANIFICADA"]
        bloqueadas = [a for a in acciones if a["estado"] == "BLOQUEADA"]
        estado = "LISTA_PARA_TRANSACCION" if acciones and not bloqueos and not bloqueadas else "BLOQUEADA"
        payload = {
            "version": self.VERSION,
            "estado_simulacion": estado,
            "acciones": acciones,
            "bloqueos": bloqueos,
            "avisos": avisos,
            "resumen": {
                "menus": len(pre.get("menus", [])),
                "acciones": len(acciones),
                "ejecutables": len(ejecutables),
                "bloqueadas": len(bloqueadas),
                "crear": sum(1 for a in acciones if a["tipo"] == "CREAR"),
                "actualizar": sum(1 for a in acciones if a["tipo"] == "ACTUALIZAR"),
                "vincular": sum(1 for a in acciones if a["tipo"] == "VINCULAR"),
                "relaciones": sum(1 for a in acciones if a["tipo"] in {"CREAR_RELACION", "CREAR_O_REUTILIZAR"}),
                "registrar": sum(1 for a in acciones if a["tipo"] == "REGISTRAR"),
                "bloqueos": len(bloqueos),
            },
            "plan_id": _stable_id("PLAN", self.VERSION, json.dumps(acciones, ensure_ascii=False, sort_keys=True)),
            "escrituras_habilitadas": False,
            "datos_modificados": False,
        }
        return payload

    def detectar_menus(self, ruta_excel: str | Path) -> dict[str, Any]:
        return self.detector_multihoja.detectar(ruta_excel)

    def simular(self, ruta_excel: str | Path, hojas: list[str] | None = None, incluir_probables: bool = False) -> dict[str, Any]:
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
        plan["integridad"] = {
            "huellas_antes": antes,
            "huellas_despues": despues,
            "archivos_modificados": cambios,
            "sin_escrituras": not cambios,
        }
        plan["datos_modificados"] = bool(cambios)
        if cambios:
            plan["estado_simulacion"] = "ERROR_INTEGRIDAD"
        return plan


def _n(valor: Any, dec: int = 4) -> str:
    if valor is None:
        return "-"
    try:
        return f"{float(valor):.{dec}f}"
    except Exception:
        return str(valor)


def formatear_simulacion_i13411(resultado: dict[str, Any]) -> str:
    r = resultado.get("resumen", {})
    sel = resultado.get("seleccion", {})
    det = resultado.get("deteccion_multihoja", {})
    lineas = [
        "I1.3.4.1.1 — DETECCIÓN Y SIMULACIÓN MULTIMENÚ",
        "=" * 78,
        "ARCHIVO ANALIZADO",
        f"Hojas del libro: {det.get('hojas_totales', 0)} | Menús detectados: {sel.get('menus_detectados_en_archivo', 0)} | Menús seleccionados: {sel.get('menus_seleccionados', 0)}",
        "Hojas seleccionadas: " + ", ".join(sel.get("hojas_seleccionadas", [])),
        "-" * 78,
        "BASE DE DATOS HOST AI",
        f"Menús existentes: {sel.get('menus_existentes_en_host_ai', 0)} | Se crearán: {sel.get('menus_a_crear', 0)} | Se actualizarán: {sel.get('menus_a_actualizar', 0)}",
        "-" * 78,
        "PLAN DE IMPORTACIÓN (SOLO SIMULACIÓN)",
        f"Plan: {resultado.get('plan_id')} | Estado: {resultado.get('estado_simulacion')}",
        f"Acciones: {r.get('acciones',0)} | Ejecutables: {r.get('ejecutables',0)} | Bloqueadas: {r.get('bloqueadas',0)}",
        f"Vincular: {r.get('vincular',0)} | Relaciones: {r.get('relaciones',0)} | Registrar: {r.get('registrar',0)}",
    ]
    for a in resultado.get("acciones", []):
        icono = "✖" if a.get("estado") == "BLOQUEADA" else "•"
        d = a.get("detalle", {})
        extra = []
        if d.get("menu"): extra.append(f"menú={d['menu']}")
        if d.get("plato"): extra.append(f"plato={d['plato']}")
        if d.get("seccion"): extra.append(f"sección={d['seccion']}")
        if a.get("entidad") == "DATOS_ECONOMICOS":
            extra.append(f"venta={_n(d.get('precio_venta'),2)} €")
            extra.append(f"coste={_n(d.get('coste_total'),4)} €")
            extra.append(f"food cost={_n(d.get('food_cost_pct'),4)}%")
        sufijo = f" | {' | '.join(extra)}" if extra else ""
        lineas.append(f"{icono} [{a.get('estado')}] {a.get('tipo')} {a.get('entidad')}: {a.get('nombre')}{sufijo}")
    lineas.append("=" * 78)
    if resultado.get("bloqueos"):
        lineas.append("SIMULACIÓN BLOQUEADA")
        for i,b in enumerate(resultado["bloqueos"],1):
            lineas.append(f"{i}. {b.get('componente')} | {b.get('rol')} | {b.get('mensaje')}")
    else:
        lineas.append("SIMULACIÓN LISTA: el plan no contiene bloqueos técnicos.")
    integ = resultado.get("integridad", {})
    lineas.append(f"Integridad: archivos de negocio modificados={len(integ.get('archivos_modificados', []))} | sin escrituras={'SÍ' if integ.get('sin_escrituras') else 'NO'}")
    lineas.extend([
        "SOLO SIMULACIÓN: no se creó, actualizó ni vinculó ningún dato real.",
        "I1.3.4.1.1 permite seleccionar uno, varios o todos los menús detectados.",
        "La importación definitiva continúa deshabilitada.",
    ])
    return "\n".join(lineas)

