from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from SERVICIOS.auditor_integridad_postimportacion_i1344 import AuditorIntegridadPostimportacionI1344, formatear_auditoria_i1344
from SERVICIOS.motor_escritura_segura_i1342 import MotorEscrituraSeguraI1342
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


class BandejaCorreccionPostimportacionI13441:
    VERSION = "I1.3.4.4.1"
    RUTA_MENUS = "DATOS/db/menus.json"
    RUTA_RECETAS = "DATOS/db/escandallos.json"
    RUTA_ARTICULOS = "DATOS/db/articulos.json"
    RUTA_SESIONES = "DATOS/mur/correcciones_i13441"

    def __init__(self, base_dir: str | Path, ruta_menus: str | None = None, ruta_recetas: str | None = None, ruta_articulos: str | None = None):
        self.base_dir = Path(base_dir).resolve()
        self.ruta_menus = ruta_menus or self.RUTA_MENUS
        self.ruta_recetas = ruta_recetas or self.RUTA_RECETAS
        self.ruta_articulos = ruta_articulos or self.RUTA_ARTICULOS
        self.motor = MotorEscrituraSeguraI1342(self.base_dir, [self.ruta_menus])
        self.auditor = AuditorIntegridadPostimportacionI1344(
            self.base_dir, self.ruta_menus, self.ruta_recetas, self.ruta_articulos,
            "DATOS/auditorias/i13441",
        )
        self.sesion_id = _stable_id("COR-I13441", _now(), self.ruta_menus)
        self.historial: list[dict[str, Any]] = []
        self.menus = self._cargar_lista(self.ruta_menus, obligatorio=True)
        self.recetas = self._cargar_lista(self.ruta_recetas, obligatorio=False)
        self.articulos = self._cargar_lista(self.ruta_articulos, obligatorio=False)
        self.ultima_auditoria = self.auditor.auditar(guardar_informe=False)

    def _cargar_lista(self, rel: str, *, obligatorio: bool) -> list[dict[str, Any]]:
        p = (self.base_dir / rel).resolve()
        if not p.exists():
            if obligatorio:
                raise FileNotFoundError(f"No existe el archivo requerido: {p}")
            return []
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"{rel} debe contener una lista JSON.")
        return [x for x in data if isinstance(x, dict)]

    def _registrar(self, accion: str, **datos: Any) -> None:
        self.historial.append({"fecha": _now(), "accion": accion, **datos})

    def incidencias(self) -> list[dict[str, Any]]:
        return list(self.ultima_auditoria.get("incidencias") or [])

    def resumen(self) -> dict[str, Any]:
        q = self.ultima_auditoria.get("resumen") or {}
        return {
            "sesion_id": self.sesion_id,
            "estado": self.ultima_auditoria.get("estado"),
            "errores": q.get("errores", 0),
            "avisos": q.get("avisos", 0),
            "total": q.get("total", 0),
            "acciones": len(self.historial),
        }

    def _buscar_menu(self, inc: dict[str, Any]) -> dict[str, Any]:
        mid = str(inc.get("menu_id") or "")
        mn = _norm(inc.get("menu"))
        for m in self.menus:
            if mid and str(m.get("menu_id") or m.get("id") or "") == mid:
                return m
            if mn and _norm(m.get("nombre")) == mn:
                return m
        raise ValueError(f"No se encontró el menú de la incidencia: {inc.get('menu')}")

    @staticmethod
    def _buscar_plato(menu: dict[str, Any], inc: dict[str, Any]) -> dict[str, Any] | None:
        pid = str(inc.get("plato_id") or "")
        pn = _norm(inc.get("plato"))
        for p in menu.get("platos") or []:
            if not isinstance(p, dict):
                continue
            if pid and str(p.get("plato_id") or p.get("id") or "") == pid:
                return p
            if pn and _norm(p.get("nombre")) == pn:
                return p
        return None

    @staticmethod
    def _buscar_componente(plato: dict[str, Any], inc: dict[str, Any]) -> dict[str, Any] | None:
        ref = _norm(inc.get("referencia"))
        entidad = str(inc.get("entidad") or "").upper()
        for c in plato.get("componentes") or []:
            if not isinstance(c, dict):
                continue
            if ref and _norm(c.get("nombre")) == ref and (not entidad or str(c.get("rol") or "").upper() == entidad):
                return c
        return None

    def _recalcular_resumen_menu(self, menu: dict[str, Any]) -> None:
        platos = [p for p in menu.get("platos") or [] if isinstance(p, dict)]
        menu["resumen"] = {
            "secciones": len([s for s in menu.get("secciones") or [] if isinstance(s, dict)]),
            "platos": len(platos),
            "componentes": sum(len([c for c in p.get("componentes") or [] if isinstance(c, dict)]) for p in platos),
            "articulos_directos": len([a for a in menu.get("articulos_directos") or [] if isinstance(a, dict)]),
            "bebidas": len([b for b in menu.get("bebidas") or [] if isinstance(b, dict)]),
            "complementos": len([c for c in menu.get("complementos") or [] if isinstance(c, dict)]),
        }
        menu["actualizado_en"] = _now()

    def eliminar(self, indices: list[int]) -> dict[str, int]:
        incidencias = self.incidencias()
        eliminados = 0
        for idx in sorted(set(indices), reverse=True):
            if idx < 1 or idx > len(incidencias):
                continue
            inc = incidencias[idx - 1]
            menu = self._buscar_menu(inc)
            plato = self._buscar_plato(menu, inc)
            codigo = inc.get("codigo")
            ref = _norm(inc.get("referencia"))
            if codigo in {"RECETA_REFERENCIA_INEXISTENTE", "COMPONENTE_PLATO_ID_INCORRECTO", "RELACION_COMPONENTE_DUPLICADA", "ROL_COMPONENTE_DESCONOCIDO"} and plato:
                comp = self._buscar_componente(plato, inc)
                if comp and comp in plato.get("componentes", []):
                    plato["componentes"].remove(comp); eliminados += 1
            elif codigo in {"ARTICULO_REFERENCIA_INEXISTENTE"}:
                antes = len(menu.get("articulos_directos") or [])
                menu["articulos_directos"] = [a for a in (menu.get("articulos_directos") or []) if _norm(a.get("nombre")) != ref]
                eliminados += antes - len(menu["articulos_directos"])
            elif codigo in {"PLATO_SIN_RECETA_PRINCIPAL", "PLATO_NOMBRE_DUPLICADO", "PLATO_SIN_ID", "PLATO_SIN_NOMBRE"} and plato:
                menu["platos"].remove(plato); eliminados += 1
            elif codigo in {"SECCION_REFERENCIA_INEXISTENTE"} and plato:
                plato["seccion"] = None; eliminados += 1
            elif codigo in {"MENU_SIN_PLATOS", "MENU_NOMBRE_DUPLICADO", "MENU_SIN_ID", "MENU_SIN_NOMBRE"}:
                self.menus.remove(menu); eliminados += 1
            self._recalcular_resumen_menu(menu) if menu in self.menus else None
            self._registrar("ELIMINAR", incidencia=inc, aplicado=bool(eliminados))
        self._refrescar()
        return {"eliminados": eliminados}

    def renombrar(self, indice: int, nuevo_nombre: str) -> None:
        inc = self.incidencias()[indice - 1]
        menu = self._buscar_menu(inc)
        plato = self._buscar_plato(menu, inc)
        codigo = inc.get("codigo")
        if codigo.startswith("MENU_") and not plato:
            menu["nombre"] = nuevo_nombre
        elif plato and inc.get("referencia"):
            comp = self._buscar_componente(plato, inc)
            if comp:
                comp["nombre"] = nuevo_nombre
            else:
                plato["nombre"] = nuevo_nombre
        elif plato:
            plato["nombre"] = nuevo_nombre
        else:
            raise ValueError("La incidencia no admite renombrado.")
        self._recalcular_resumen_menu(menu)
        self._registrar("RENOMBRAR", indice=indice, nuevo_nombre=nuevo_nombre)
        self._refrescar()

    def cambiar_seccion(self, indices: list[int], nueva_seccion: str, *, crear_si_falta: bool = True) -> int:
        cambios = 0
        for idx in sorted(set(indices)):
            inc = self.incidencias()[idx - 1]
            menu = self._buscar_menu(inc)
            plato = self._buscar_plato(menu, inc)
            if not plato:
                continue
            if crear_si_falta and _norm(nueva_seccion) not in {_norm(s.get("nombre")) for s in menu.get("secciones") or [] if isinstance(s, dict)}:
                menu.setdefault("secciones", []).append({"seccion_id": _stable_id("SEC", menu.get("menu_id"), nueva_seccion), "nombre": nueva_seccion})
            plato["seccion"] = nueva_seccion
            cambios += 1
            self._recalcular_resumen_menu(menu)
        self._registrar("CAMBIAR_SECCION", indices=indices, nueva_seccion=nueva_seccion, cambios=cambios)
        self._refrescar()
        return cambios

    def vincular_receta(self, indice: int, receta: dict[str, Any]) -> None:
        inc = self.incidencias()[indice - 1]
        menu = self._buscar_menu(inc)
        plato = self._buscar_plato(menu, inc)
        if not plato:
            raise ValueError("La incidencia no tiene plato destino.")
        comp = self._buscar_componente(plato, inc)
        rid = receta.get("receta_id") or receta.get("id") or receta.get("codigo")
        nombre = receta.get("nombre")
        if comp:
            comp["nombre"] = nombre
            comp["receta_id"] = rid
        else:
            plato.setdefault("componentes", []).append({
                "componente_id": _stable_id("COMP", menu.get("menu_id"), plato.get("plato_id"), rid or nombre),
                "rol": "RECETA_PRINCIPAL",
                "nombre": nombre,
                "receta_id": rid,
                "plato_id": plato.get("plato_id"),
            })
        self._recalcular_resumen_menu(menu)
        self._registrar("VINCULAR_RECETA", indice=indice, receta_id=rid, receta=nombre)
        self._refrescar()

    def vincular_articulo(self, indice: int, articulo: dict[str, Any]) -> None:
        inc = self.incidencias()[indice - 1]
        menu = self._buscar_menu(inc)
        ref = _norm(inc.get("referencia"))
        aid = articulo.get("articulo_id") or articulo.get("codigo") or articulo.get("id")
        nombre = articulo.get("nombre") or articulo.get("articulo")
        encontrado = False
        for a in menu.get("articulos_directos") or []:
            if _norm(a.get("nombre")) == ref:
                a["nombre"] = nombre; a["articulo_id"] = aid; encontrado = True
        if not encontrado:
            menu.setdefault("articulos_directos", []).append({"nombre": nombre, "articulo_id": aid})
        self._recalcular_resumen_menu(menu)
        self._registrar("VINCULAR_ARTICULO", indice=indice, articulo_id=aid, articulo=nombre)
        self._refrescar()

    def recalcular_economia(self, indices: list[int] | None = None) -> int:
        objetivos: set[str] = set()
        if indices:
            for idx in indices:
                inc = self.incidencias()[idx - 1]
                objetivos.add(str(inc.get("menu_id") or _norm(inc.get("menu"))))
        cambios = 0
        for menu in self.menus:
            key = str(menu.get("menu_id") or _norm(menu.get("nombre")))
            if objetivos and key not in objetivos:
                continue
            econ = menu.setdefault("economico", {})
            venta = _to_float(econ.get("precio_venta"))
            coste = _to_float(econ.get("coste_total"))
            if venta is None or coste is None:
                continue
            econ["food_cost_pct"] = (coste / venta * 100) if venta else None
            econ["beneficio"] = venta - coste
            cambios += 1
            self._recalcular_resumen_menu(menu)
        self._registrar("RECALCULAR_ECONOMIA", indices=indices or "TODOS", cambios=cambios)
        self._refrescar()
        return cambios

    def aceptar(self, indices: list[int]) -> None:
        # Solo registra la aceptación; la incidencia seguirá apareciendo si la auditoría la considera vigente.
        self._registrar("MANTENER", indices=indices)
        self._guardar_sesion()

    def buscar_recetas(self, texto: str) -> list[dict[str, Any]]:
        q = _norm(texto)
        return [r for r in self.recetas if q in _norm(r.get("nombre"))][:20]

    def buscar_articulos(self, texto: str) -> list[dict[str, Any]]:
        q = _norm(texto)
        return [a for a in self.articulos if q in _norm(a.get("nombre") or a.get("articulo"))][:20]

    def guardar(self, *, confirmar: bool) -> dict[str, Any]:
        if not confirmar:
            raise ValueError("La corrección real requiere confirmación explícita.")
        tx = self.motor.ejecutar({self.ruta_menus: self.menus}, idempotency_key=self.sesion_id)
        if tx.estado != "COMMIT":
            raise RuntimeError(f"La corrección terminó en {tx.estado}: {tx.error}")
        self._registrar("COMMIT", transaccion_id=tx.transaccion_id, backup=tx.backup_dir)
        self._guardar_sesion()
        self.ultima_auditoria = self.auditor.auditar(guardar_informe=True)
        return {"transaccion": tx.to_dict(), "auditoria": self.ultima_auditoria, "sesion": self._guardar_sesion()}

    def _refrescar(self) -> None:
        # Auditoría temporal sobre una copia aislada para no escribir antes del COMMIT.
        tmp_root = self.base_dir / "DATOS" / "mur" / "correcciones_i13441" / self.sesion_id / "preview"
        tmp_root.mkdir(parents=True, exist_ok=True)
        (tmp_root / "menus.json").write_text(json.dumps(self.menus, ensure_ascii=False, indent=2), encoding="utf-8")
        (tmp_root / "recetas.json").write_text(json.dumps(self.recetas, ensure_ascii=False, indent=2), encoding="utf-8")
        (tmp_root / "articulos.json").write_text(json.dumps(self.articulos, ensure_ascii=False, indent=2), encoding="utf-8")
        self.ultima_auditoria = AuditorIntegridadPostimportacionI1344(
            tmp_root, "menus.json", "recetas.json", "articulos.json", "informes"
        ).auditar(guardar_informe=False)
        self._guardar_sesion()

    def _guardar_sesion(self) -> str:
        out = self.base_dir / self.RUTA_SESIONES
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{self.sesion_id}.json"
        payload = {
            "version": self.VERSION,
            "sesion_id": self.sesion_id,
            "actualizado_en": _now(),
            "resumen": self.resumen(),
            "historial": self.historial,
            "auditoria_actual": self.ultima_auditoria,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)


def formatear_bandeja_i13441(b: BandejaCorreccionPostimportacionI13441) -> str:
    r = b.resumen()
    lines = [
        "I1.3.4.4.1 — BANDEJA DE CORRECCIÓN POSTIMPORTACIÓN",
        "=" * 78,
        f"Sesión: {r['sesion_id']} | Estado: {r['estado']}",
        f"Incidencias: {r['total']} | Errores: {r['errores']} | Avisos: {r['avisos']} | Acciones: {r['acciones']}",
        "-" * 78,
    ]
    for i, inc in enumerate(b.incidencias(), 1):
        ctx = " | ".join(x for x in [inc.get("menu"), inc.get("plato"), inc.get("referencia")] if x)
        lines.append(f"{i}. [{inc.get('severidad')}] {inc.get('codigo')}: {inc.get('mensaje')}" + (f" | {ctx}" if ctx else ""))
    lines.extend([
        "=" * 78,
        "E=Eliminar | R=Renombrar | V=Vincular | S=Sección | A=Economía | M=Mantener | G=Guardar cambios | 0=Salir",
        "Los cambios no afectan al catálogo real hasta confirmar G y escribir GUARDAR.",
    ])
    return "\n".join(lines)
