from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from SERVICIOS.simulador_importacion_menus_i13411 import _norm, _stable_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class IncidenciaAuditoria:
    codigo: str
    severidad: str
    mensaje: str
    menu_id: str | None = None
    menu: str | None = None
    plato_id: str | None = None
    plato: str | None = None
    entidad: str | None = None
    referencia: str | None = None


class AuditorIntegridadPostimportacionI1344:
    VERSION = "I1.3.4.4"
    RUTA_MENUS = "DATOS/db/menus.json"
    RUTA_RECETAS = "DATOS/db/escandallos.json"
    RUTA_ARTICULOS = "DATOS/db/articulos.json"
    RUTA_INFORMES = "DATOS/auditorias/i1344"

    ROLES_RECETA = {
        "RECETA_PRINCIPAL", "RECETA", "SALSA", "GUARNICION",
        "ELABORACION", "CONDIMENTO", "ACABADO",
    }

    def __init__(
        self,
        base_dir: str | Path,
        ruta_menus: str | None = None,
        ruta_recetas: str | None = None,
        ruta_articulos: str | None = None,
        ruta_informes: str | None = None,
    ):
        self.base_dir = Path(base_dir).resolve()
        self.ruta_menus = ruta_menus or self.RUTA_MENUS
        self.ruta_recetas = ruta_recetas or self.RUTA_RECETAS
        self.ruta_articulos = ruta_articulos or self.RUTA_ARTICULOS
        self.ruta_informes = ruta_informes or self.RUTA_INFORMES

    def _cargar_lista(self, ruta: str, etiqueta: str, *, opcional: bool = False) -> list[dict[str, Any]]:
        path = (self.base_dir / ruta).resolve()
        if not path.exists():
            if opcional:
                return []
            raise FileNotFoundError(f"No existe {etiqueta}: {path}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{etiqueta} contiene JSON inválido: {exc.msg}") from exc
        if not isinstance(data, list):
            raise ValueError(f"{etiqueta} debe ser una lista JSON.")
        return [x for x in data if isinstance(x, dict)]

    @staticmethod
    def _indice_recetas(recetas: list[dict[str, Any]]) -> tuple[set[str], set[str]]:
        nombres: set[str] = set()
        ids: set[str] = set()
        for r in recetas:
            if r.get("activo", True) is False:
                continue
            nombres.add(_norm(r.get("nombre")))
            for campo in ("receta_id", "id", "codigo"):
                if r.get(campo):
                    ids.add(str(r[campo]))
        nombres.discard("")
        return nombres, ids

    @staticmethod
    def _indice_articulos(articulos: list[dict[str, Any]]) -> tuple[set[str], set[str]]:
        nombres: set[str] = set()
        ids: set[str] = set()
        for a in articulos:
            if a.get("activo", True) is False:
                continue
            nombres.add(_norm(a.get("nombre") or a.get("articulo")))
            for campo in ("articulo_id", "codigo", "id"):
                if a.get(campo):
                    ids.add(str(a[campo]))
        nombres.discard("")
        return nombres, ids

    def auditar(self, *, guardar_informe: bool = True) -> dict[str, Any]:
        menus = self._cargar_lista(self.ruta_menus, "el catálogo de menús")
        recetas = self._cargar_lista(self.ruta_recetas, "el catálogo de recetas", opcional=True)
        articulos = self._cargar_lista(self.ruta_articulos, "el catálogo de artículos", opcional=True)
        recetas_nombres, recetas_ids = self._indice_recetas(recetas)
        articulos_nombres, articulos_ids = self._indice_articulos(articulos)
        incidencias: list[IncidenciaAuditoria] = []

        def add(codigo: str, severidad: str, mensaje: str, **ctx: Any) -> None:
            incidencias.append(IncidenciaAuditoria(codigo, severidad, mensaje, **ctx))

        menu_ids: list[str] = []
        menu_names: list[str] = []
        stats = Counter()
        all_plato_ids: set[tuple[str, str]] = set()
        all_component_ids: set[tuple[str, str]] = set()

        for menu in menus:
            mid = str(menu.get("menu_id") or menu.get("id") or "").strip()
            mn = str(menu.get("nombre") or "").strip()
            menu_ids.append(mid)
            menu_names.append(_norm(mn))
            stats["menus"] += 1
            if not mid:
                add("MENU_SIN_ID", "ERROR", "El menú no tiene identificador.", menu=mn, entidad="MENU")
            if not mn:
                add("MENU_SIN_NOMBRE", "ERROR", "El menú no tiene nombre.", menu_id=mid, entidad="MENU")

            secciones = menu.get("secciones") if isinstance(menu.get("secciones"), list) else []
            platos = menu.get("platos") if isinstance(menu.get("platos"), list) else []
            articulos_directos = menu.get("articulos_directos") if isinstance(menu.get("articulos_directos"), list) else []
            bebidas = menu.get("bebidas") if isinstance(menu.get("bebidas"), list) else []
            complementos = menu.get("complementos") if isinstance(menu.get("complementos"), list) else []
            servicios = menu.get("servicios") if isinstance(menu.get("servicios"), list) else []
            stats.update({"secciones": len(secciones), "platos": len(platos), "articulos_directos": len(articulos_directos), "bebidas": len(bebidas), "complementos": len(complementos), "servicios": len(servicios)})
            if not platos:
                add("MENU_SIN_PLATOS", "AVISO", "El menú no contiene platos.", menu_id=mid, menu=mn, entidad="MENU")

            section_names = {_norm(s.get("nombre")) for s in secciones if isinstance(s, dict)}
            section_names.discard("")
            duplicate_sections = [x for x, n in Counter(_norm(s.get("nombre")) for s in secciones if isinstance(s, dict)).items() if x and n > 1]
            for sec in duplicate_sections:
                add("SECCION_DUPLICADA", "AVISO", f"La sección aparece repetida: {sec}.", menu_id=mid, menu=mn, entidad="SECCION", referencia=sec)

            plato_names = Counter()
            for plato in platos:
                if not isinstance(plato, dict):
                    add("PLATO_FORMATO_INVALIDO", "ERROR", "Existe un plato con formato inválido.", menu_id=mid, menu=mn, entidad="PLATO")
                    continue
                pid = str(plato.get("plato_id") or plato.get("id") or "").strip()
                pn = str(plato.get("nombre") or "").strip()
                plato_names[_norm(pn)] += 1
                stats["componentes"] += len(plato.get("componentes") or []) if isinstance(plato.get("componentes"), list) else 0
                if not pid:
                    add("PLATO_SIN_ID", "ERROR", "El plato no tiene identificador.", menu_id=mid, menu=mn, plato=pn, entidad="PLATO")
                elif (mid, pid) in all_plato_ids:
                    add("PLATO_ID_DUPLICADO", "ERROR", f"Identificador de plato duplicado: {pid}.", menu_id=mid, menu=mn, plato_id=pid, plato=pn, entidad="PLATO")
                else:
                    all_plato_ids.add((mid, pid))
                if not pn:
                    add("PLATO_SIN_NOMBRE", "ERROR", "El plato no tiene nombre.", menu_id=mid, menu=mn, plato_id=pid, entidad="PLATO")
                sec = _norm(plato.get("seccion"))
                if sec and section_names and sec not in section_names:
                    add("SECCION_REFERENCIA_INEXISTENTE", "AVISO", f"La sección del plato no está registrada: {plato.get('seccion')}.", menu_id=mid, menu=mn, plato_id=pid, plato=pn, entidad="SECCION")

                componentes = plato.get("componentes") if isinstance(plato.get("componentes"), list) else []
                principales = [c for c in componentes if isinstance(c, dict) and c.get("rol") in {"RECETA_PRINCIPAL", "RECETA"}]
                if not principales:
                    add("PLATO_SIN_RECETA_PRINCIPAL", "AVISO", "El plato no tiene receta principal vinculada.", menu_id=mid, menu=mn, plato_id=pid, plato=pn, entidad="PLATO")
                if len(principales) > 1:
                    add("PLATO_VARIAS_RECETAS_PRINCIPALES", "ERROR", "El plato tiene más de una receta principal.", menu_id=mid, menu=mn, plato_id=pid, plato=pn, entidad="PLATO")

                component_key_counter = Counter()
                for comp in componentes:
                    if not isinstance(comp, dict):
                        add("COMPONENTE_FORMATO_INVALIDO", "ERROR", "Existe un componente con formato inválido.", menu_id=mid, menu=mn, plato_id=pid, plato=pn, entidad="COMPONENTE")
                        continue
                    cid = str(comp.get("componente_id") or comp.get("id") or "").strip()
                    cn = str(comp.get("nombre") or "").strip()
                    rol = str(comp.get("rol") or "").strip().upper()
                    component_key_counter[(_norm(cn), rol)] += 1
                    if not cid:
                        add("COMPONENTE_SIN_ID", "ERROR", "El componente no tiene identificador.", menu_id=mid, menu=mn, plato_id=pid, plato=pn, entidad=rol, referencia=cn)
                    elif (mid, cid) in all_component_ids:
                        add("COMPONENTE_ID_DUPLICADO", "ERROR", f"Identificador de componente duplicado: {cid}.", menu_id=mid, menu=mn, plato_id=pid, plato=pn, entidad=rol, referencia=cn)
                    else:
                        all_component_ids.add((mid, cid))
                    if str(comp.get("plato_id") or "") != pid:
                        add("COMPONENTE_PLATO_ID_INCORRECTO", "ERROR", "El componente no apunta al plato que lo contiene.", menu_id=mid, menu=mn, plato_id=pid, plato=pn, entidad=rol, referencia=cn)
                    if rol not in self.ROLES_RECETA:
                        add("ROL_COMPONENTE_DESCONOCIDO", "AVISO", f"Rol no reconocido: {rol or '-'}.", menu_id=mid, menu=mn, plato_id=pid, plato=pn, entidad=rol, referencia=cn)
                    ref_id = str(comp.get("receta_id") or comp.get("referencia_id") or "").strip()
                    existe = (ref_id and ref_id in recetas_ids) or _norm(cn) in recetas_nombres
                    if rol in self.ROLES_RECETA and not existe:
                        add("RECETA_REFERENCIA_INEXISTENTE", "ERROR", f"No se encontró la receta/elaboración vinculada: {cn}.", menu_id=mid, menu=mn, plato_id=pid, plato=pn, entidad=rol, referencia=cn)
                for (nombre_norm, rol), total in component_key_counter.items():
                    if nombre_norm and total > 1:
                        add("RELACION_COMPONENTE_DUPLICADA", "ERROR", f"Relación repetida {rol}: {nombre_norm} ({total} veces).", menu_id=mid, menu=mn, plato_id=pid, plato=pn, entidad=rol, referencia=nombre_norm)

            for pn, total in plato_names.items():
                if pn and total > 1:
                    add("PLATO_NOMBRE_DUPLICADO", "AVISO", f"El plato aparece {total} veces: {pn}.", menu_id=mid, menu=mn, entidad="PLATO", referencia=pn)

            for art in articulos_directos:
                if not isinstance(art, dict):
                    continue
                an = str(art.get("nombre") or "").strip()
                aid = str(art.get("articulo_id") or art.get("codigo") or "").strip()
                if not ((aid and aid in articulos_ids) or _norm(an) in articulos_nombres):
                    add("ARTICULO_REFERENCIA_INEXISTENTE", "ERROR", f"No se encontró el artículo directo: {an}.", menu_id=mid, menu=mn, entidad="ARTICULO_DIRECTO", referencia=an)

            econ = menu.get("economico") if isinstance(menu.get("economico"), dict) else {}
            venta = _to_float(econ.get("precio_venta"))
            coste = _to_float(econ.get("coste_total"))
            food = _to_float(econ.get("food_cost_pct"))
            beneficio = _to_float(econ.get("beneficio"))
            if venta is None or coste is None:
                add("ECONOMIA_INCOMPLETA", "AVISO", "Faltan precio de venta o coste total.", menu_id=mid, menu=mn, entidad="ECONOMICO")
            else:
                esperado_food = (coste / venta * 100) if venta else None
                esperado_beneficio = venta - coste
                if esperado_food is None:
                    add("VENTA_CERO", "ERROR", "El precio de venta es cero; no puede calcularse food cost.", menu_id=mid, menu=mn, entidad="ECONOMICO")
                elif food is None or abs(food - esperado_food) > 0.05:
                    add("FOOD_COST_INCOHERENTE", "AVISO", f"Food cost guardado={food}; recalculado={esperado_food:.4f}%.", menu_id=mid, menu=mn, entidad="ECONOMICO")
                if beneficio is None or abs(beneficio - esperado_beneficio) > 0.02:
                    add("BENEFICIO_INCOHERENTE", "AVISO", f"Beneficio guardado={beneficio}; recalculado={esperado_beneficio:.4f} €.", menu_id=mid, menu=mn, entidad="ECONOMICO")
                if food is not None and (food < 0 or food > 100):
                    add("FOOD_COST_FUERA_RANGO", "AVISO", f"Food cost fuera de rango habitual: {food:.2f}%.", menu_id=mid, menu=mn, entidad="ECONOMICO")

            resumen = menu.get("resumen") if isinstance(menu.get("resumen"), dict) else {}
            esperado_resumen = {
                "secciones": len(secciones), "platos": len(platos),
                "componentes": sum(len(p.get("componentes") or []) for p in platos if isinstance(p, dict)),
                "articulos_directos": len(articulos_directos), "bebidas": len(bebidas),
                "complementos": len(complementos),
            }
            for campo, esperado in esperado_resumen.items():
                if resumen.get(campo) != esperado:
                    add("RESUMEN_DESACTUALIZADO", "AVISO", f"Resumen {campo}: guardado={resumen.get(campo)}, real={esperado}.", menu_id=mid, menu=mn, entidad="RESUMEN", referencia=campo)

        for mid, n in Counter(menu_ids).items():
            if mid and n > 1:
                add("MENU_ID_DUPLICADO", "ERROR", f"Identificador de menú repetido {n} veces: {mid}.", menu_id=mid, entidad="MENU")
        for mn, n in Counter(menu_names).items():
            if mn and n > 1:
                add("MENU_NOMBRE_DUPLICADO", "AVISO", f"Nombre de menú repetido {n} veces: {mn}.", menu=mn, entidad="MENU")

        conteo = Counter(x.severidad for x in incidencias)
        estado = "CERTIFICADA" if conteo["ERROR"] == 0 else "NO_CERTIFICADA"
        if estado == "CERTIFICADA" and conteo["AVISO"]:
            estado = "CERTIFICADA_CON_AVISOS"
        resultado = {
            "version": self.VERSION,
            "auditoria_id": _stable_id("AUD-I1344", _now(), self.ruta_menus),
            "generado_en": _now(),
            "estado": estado,
            "integridad": "OK" if conteo["ERROR"] == 0 else "ERROR",
            "estadisticas": dict(stats),
            "incidencias": [asdict(x) for x in incidencias],
            "resumen": {"errores": conteo["ERROR"], "avisos": conteo["AVISO"], "informativos": conteo["INFO"], "total": len(incidencias)},
            "fuentes": {"menus": self.ruta_menus, "recetas": self.ruta_recetas, "articulos": self.ruta_articulos},
        }
        if guardar_informe:
            resultado.update(self._guardar_informe(resultado))
        return resultado

    def _guardar_informe(self, resultado: dict[str, Any]) -> dict[str, str]:
        out_dir = (self.base_dir / self.ruta_informes).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        aid = resultado["auditoria_id"]
        json_path = out_dir / f"{aid}.json"
        txt_path = out_dir / f"{aid}.txt"
        json_path.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        txt_path.write_text(formatear_auditoria_i1344(resultado, detalle=True), encoding="utf-8")
        return {"informe_json": str(json_path), "informe_txt": str(txt_path)}


def formatear_auditoria_i1344(r: dict[str, Any], *, detalle: bool = True) -> str:
    s = r.get("estadisticas", {})
    q = r.get("resumen", {})
    lines = [
        "I1.3.4.4 — AUDITORÍA E INTEGRIDAD POSTIMPORTACIÓN",
        "=" * 78,
        f"Estado: {r.get('estado')} | Integridad: {r.get('integridad')}",
        f"Menús: {s.get('menus', 0)} | Secciones: {s.get('secciones', 0)} | Platos: {s.get('platos', 0)} | Componentes: {s.get('componentes', 0)}",
        f"Artículos directos: {s.get('articulos_directos', 0)} | Bebidas: {s.get('bebidas', 0)} | Complementos: {s.get('complementos', 0)} | Servicios: {s.get('servicios', 0)}",
        f"Errores: {q.get('errores', 0)} | Avisos: {q.get('avisos', 0)} | Informativos: {q.get('informativos', 0)}",
    ]
    if detalle and r.get("incidencias"):
        lines.extend(["-" * 78, "INCIDENCIAS"])
        for i, inc in enumerate(r["incidencias"], 1):
            contexto = " | ".join(x for x in [inc.get("menu"), inc.get("plato"), inc.get("referencia")] if x)
            lines.append(f"{i}. [{inc.get('severidad')}] {inc.get('codigo')}: {inc.get('mensaje')}" + (f" | {contexto}" if contexto else ""))
    lines.extend(["-" * 78, "Auditoría de solo lectura: no se modificaron menús, recetas ni artículos."])
    if r.get("informe_json"):
        lines.append(f"Informe JSON: {r['informe_json']}")
    if r.get("informe_txt"):
        lines.append(f"Informe TXT: {r['informe_txt']}")
    return "\n".join(lines)
