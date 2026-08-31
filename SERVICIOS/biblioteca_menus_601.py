from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from SERVICIOS.repository_initialization_policy import should_initialize_persistently

from SERVICIOS.biblioteca_escandallos_601 import RepositorioBibliotecaEscandallos601
from SERVICIOS.biblioteca_culinaria_read_service import BibliotecaCulinariaReadService
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.motor_calculo_menus_601 import (
    ESTADO_ARCHIVADO,
    ESTADO_BORRADOR,
    ESTADO_CON_INCIDENCIAS,
    ESTADO_DESACTUALIZADO,
    ESTADO_OPERATIVO,
    MotorCalculoMenus601,
)
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


class RepositorioBibliotecaMenus601:
    VERSION_MODELO = "6.0.1"
    RUTA = "DATOS/db/menus.json"

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.path = self.base_dir / self.RUTA
        if should_initialize_persistently():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                self._guardar([])

    def _leer(self) -> list[dict[str, Any]]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        return []

    def _guardar(self, data: list[dict[str, Any]]) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.path.parent, suffix=".tmp") as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2)
            tmp.flush()
            temp = Path(tmp.name)
        temp.replace(self.path)

    @staticmethod
    def _norm(txt: Any) -> str:
        return " ".join(str(txt or "").strip().lower().split())

    def _next_id(self, menus: list[dict[str, Any]]) -> str:
        last = 0
        for m in menus:
            mid = str(m.get("menu_id") or "")
            if mid.startswith("MENU601-"):
                try:
                    last = max(last, int(mid.split("-")[-1]))
                except ValueError:
                    continue
        return f"MENU601-{last + 1:06d}"

    def _next_code(self, nombre: str, menus: list[dict[str, Any]]) -> str:
        base = "MEN-" + "-".join(x for x in str(nombre or "").upper().split() if x)
        base = "".join(ch for ch in base if ch.isalnum() or ch == "-")[:40] or "MENU"
        usados = {str(m.get("codigo") or "").upper() for m in menus if str(m.get("modelo_biblioteca") or "") == "MENU_601"}
        if base not in usados:
            return base
        i = 2
        while f"{base}-{i}" in usados:
            i += 1
        return f"{base}-{i}"

    def _es_menu_601(self, menu: dict[str, Any]) -> bool:
        return str(menu.get("modelo_biblioteca") or "") == "MENU_601"

    def listar(self, incluir_archivados: bool = False) -> list[dict[str, Any]]:
        data = [m for m in self._leer() if self._es_menu_601(m)]
        if incluir_archivados:
            return data
        return [m for m in data if str(m.get("estado") or "") != ESTADO_ARCHIVADO]

    def obtener(self, id_o_codigo: str) -> dict[str, Any] | None:
        clave = self._norm(id_o_codigo)
        if not clave:
            return None
        for m in self.listar(incluir_archivados=True):
            if clave in {self._norm(m.get("menu_id")), self._norm(m.get("codigo")), self._norm(m.get("nombre"))}:
                return m
        return None

    def buscar(self, filtros: dict[str, str]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        fn = self._norm(filtros.get("nombre", ""))
        fc = self._norm(filtros.get("codigo", ""))
        ft = self._norm(filtros.get("tipo", ""))
        fp = self._norm(filtros.get("plato", ""))
        fi = self._norm(filtros.get("ingrediente", ""))
        fe = self._norm(filtros.get("estado", ""))
        for m in self.listar(incluir_archivados=True):
            if fn and fn not in self._norm(m.get("nombre")):
                continue
            if fc and fc not in self._norm(m.get("codigo")):
                continue
            if ft and ft not in self._norm(m.get("tipo")):
                continue
            if fe and fe != self._norm(m.get("estado")):
                continue
            lineas = list(m.get("lineas") or [])
            if fp and not any(fp in self._norm(l.get("referencia")) for l in lineas):
                continue
            if fi and not any(fi in self._norm(l.get("referencia")) for l in lineas):
                continue
            out.append(m)
        return out

    def guardar_nuevo(self, menu: dict[str, Any]) -> dict[str, Any]:
        data = self._leer()
        menus_601 = [m for m in data if self._es_menu_601(m)]
        now = datetime.now().isoformat(timespec="seconds")
        nuevo = dict(menu)
        nuevo.setdefault("menu_id", self._next_id(menus_601))
        nuevo.setdefault("codigo", self._next_code(str(menu.get("nombre") or "Menú"), menus_601))
        nuevo.setdefault("estado", ESTADO_BORRADOR)
        nuevo.setdefault("creado_en", now)
        nuevo.setdefault("actualizado_en", now)
        nuevo.setdefault("version_menu", 1)
        nuevo.setdefault("historial", [])
        nuevo["modelo_biblioteca"] = "MENU_601"
        nuevo["origen_importacion"] = str(menu.get("origen_importacion") or "BIBLIOTECA_601")
        data.append(nuevo)
        self._guardar(data)
        return nuevo

    def actualizar(self, id_o_codigo: str, cambios: dict[str, Any], motivo_historial: str = "edicion") -> dict[str, Any]:
        data = self._leer()
        obj = self.obtener(id_o_codigo)
        if not obj:
            raise ValueError("Menú no encontrado.")
        now = datetime.now().isoformat(timespec="seconds")
        upd = dict(obj)
        upd.update(cambios)
        upd["actualizado_en"] = now
        upd["version_menu"] = int(obj.get("version_menu") or 1) + 1
        historial = list(upd.get("historial") or [])
        historial.append(
            {
                "fecha": now,
                "coste": float(upd.get("coste_total") or 0.0),
                "margen": float(upd.get("margen_porcentual") or 0.0),
                "precio_venta": float(upd.get("precio_venta_total") or 0.0),
                "comensales": float(upd.get("comensales_recomendado") or 0.0),
                "version_menu": int(upd.get("version_menu") or 1),
                "motivo": motivo_historial,
            }
        )
        upd["historial"] = historial

        for i, m in enumerate(data):
            if str(m.get("menu_id") or "") == str(obj.get("menu_id") or ""):
                data[i] = upd
                break
        self._guardar(data)
        return upd

    def duplicar(self, id_o_codigo: str) -> dict[str, Any]:
        data = self._leer()
        menus_601 = [m for m in data if self._es_menu_601(m)]
        obj = self.obtener(id_o_codigo)
        if not obj:
            raise ValueError("Menú no encontrado.")
        now = datetime.now().isoformat(timespec="seconds")
        cp = dict(obj)
        cp["menu_id"] = self._next_id(menus_601)
        cp["codigo"] = self._next_code(str(obj.get("nombre") or "Menú"), menus_601)
        cp["nombre"] = f"{obj.get('nombre', 'Menú')} (Copia)"
        cp["estado"] = ESTADO_BORRADOR
        cp["estado_publicacion"] = ESTADO_BORRADOR
        cp["creado_en"] = now
        cp["actualizado_en"] = now
        cp["version_menu"] = 1
        cp["historial"] = []
        data.append(cp)
        self._guardar(data)
        return cp

    def archivar(self, id_o_codigo: str) -> dict[str, Any]:
        return self.actualizar(
            id_o_codigo,
            {"estado": ESTADO_ARCHIVADO, "estado_publicacion": ESTADO_ARCHIVADO},
            motivo_historial="archivado",
        )


class BibliotecaMenus601:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.repo = RepositorioBibliotecaMenus601(self.base_dir)
        self.repo_esc = RepositorioBibliotecaEscandallos601(self.base_dir)
        self.repo_rec = RepositorioBibliotecaRecetas601(self.base_dir)
        self.repo_prod = RepositorioProductosMaestro601(self.base_dir)
        self.biblioteca = BibliotecaCulinariaReadService(base_dir)
        self.motor = MotorCalculoMenus601(
            self.repo_esc,
            self.repo_rec,
            self.repo_prod,
            elaboracion_resolver=self._resolver_elaboracion,
        )

    def _resolver_elaboracion(self, referencia: str) -> dict[str, Any] | None:
        result = self.biblioteca.detalle(referencia)
        return result.get("elaboracion") if result.get("ok") else None

    @staticmethod
    def _empty_composicion() -> dict[str, list[dict[str, Any]]]:
        return {
            "Aperitivos": [],
            "Entrantes": [],
            "Principales": [],
            "Postres": [],
            "Bodega": [],
            "Extras": [],
        }

    def buscar(self, filtros: dict[str, str]) -> dict[str, Any]:
        data = self.repo.buscar(filtros)
        return {"ok": True, "total": len(data), "menus": data}

    def ver_todos(self) -> dict[str, Any]:
        data = self.repo.listar(incluir_archivados=True)
        return {"ok": True, "total": len(data), "menus": data}

    def ver_detalle(self, id_o_codigo: str) -> dict[str, Any]:
        menu = self.repo.obtener(id_o_codigo)
        if not menu:
            return {"ok": False, "mensaje": "Menú no encontrado."}
        desactualizado, cambios = self.motor.detectar_desactualizado(menu)
        if desactualizado and str(menu.get("estado") or "") not in {ESTADO_ARCHIVADO, ESTADO_DESACTUALIZADO}:
            menu = self.repo.actualizar(id_o_codigo, {"estado": ESTADO_DESACTUALIZADO}, motivo_historial="desactualizacion")
        return {"ok": True, "menu": menu, "desactualizado": desactualizado, "cambios": cambios}

    def nuevo_menu(self, datos: dict[str, Any]) -> dict[str, Any]:
        comp = dict(datos.get("composicion") or self._empty_composicion())
        calc = self.motor.calcular(
            nombre_menu=str(datos.get("nombre") or "Menú"),
            comensales=float(datos.get("comensales_recomendado") or 0.0),
            composicion=comp,
            precio_venta_comensal=float(datos.get("precio_venta_comensal") or 0.0),
            precio_venta_total=float(datos.get("precio_venta_total") or 0.0),
        )
        menu = self.repo.guardar_nuevo(
            {
                "codigo": str(datos.get("codigo") or ""),
                "nombre": str(datos.get("nombre") or "Menú"),
                "familia": str(datos.get("familia") or ""),
                "tipo": str(datos.get("tipo") or ""),
                "comensales_recomendado": float(datos.get("comensales_recomendado") or 0.0),
                "observaciones": str(datos.get("observaciones") or ""),
                "estado": str(calc.get("estado_calculo") or ESTADO_BORRADOR),
                "estado_publicacion": str(
                    datos.get("estado_publicacion") or ESTADO_BORRADOR
                ),
                "composicion": comp,
                "lineas": list(calc.get("lineas") or []),
                "coste_por_comensal": calc.get("coste_por_comensal"),
                "coste_total": calc.get("coste_total"),
                "coste_completo": calc.get("coste_completo"),
                "lineas_sin_coste": calc.get("lineas_sin_coste"),
                "advertencias_coste": list(calc.get("advertencias") or []),
                "precio_venta_comensal": calc.get("precio_venta_comensal"),
                "precio_venta_total": calc.get("precio_venta_total"),
                "margen_total": calc.get("margen_total"),
                "margen_porcentual": calc.get("margen_porcentual"),
                "rentabilidad": calc.get("rentabilidad"),
                "incidencias": list(calc.get("incidencias") or []),
                "ultima_generacion": calc.get("fecha_calculo"),
            }
        )
        return {"ok": True, "menu": menu}

    def editar_menu(self, id_o_codigo: str, cambios: dict[str, Any]) -> dict[str, Any]:
        obj = self.repo.obtener(id_o_codigo)
        if not obj:
            return {"ok": False, "mensaje": "Menú no encontrado."}

        comp = dict(cambios.get("composicion") or obj.get("composicion") or self._empty_composicion())
        calc = self.motor.calcular(
            nombre_menu=str(cambios.get("nombre") or obj.get("nombre") or "Menú"),
            comensales=float(cambios.get("comensales_recomendado") or obj.get("comensales_recomendado") or 0.0),
            composicion=comp,
            precio_venta_comensal=float(cambios.get("precio_venta_comensal") or obj.get("precio_venta_comensal") or 0.0),
            precio_venta_total=float(cambios.get("precio_venta_total") or obj.get("precio_venta_total") or 0.0),
        )
        upd = self.repo.actualizar(
            id_o_codigo,
            {
                **obj,
                **cambios,
                "composicion": comp,
                "lineas": list(calc.get("lineas") or []),
                "coste_por_comensal": calc.get("coste_por_comensal"),
                "coste_total": calc.get("coste_total"),
                "coste_completo": calc.get("coste_completo"),
                "lineas_sin_coste": calc.get("lineas_sin_coste"),
                "advertencias_coste": list(calc.get("advertencias") or []),
                "precio_venta_comensal": calc.get("precio_venta_comensal"),
                "precio_venta_total": calc.get("precio_venta_total"),
                "margen_total": calc.get("margen_total"),
                "margen_porcentual": calc.get("margen_porcentual"),
                "rentabilidad": calc.get("rentabilidad"),
                "incidencias": list(calc.get("incidencias") or []),
                "ultima_generacion": calc.get("fecha_calculo"),
                "estado": ESTADO_CON_INCIDENCIAS if calc.get("incidencias") else ESTADO_OPERATIVO,
            },
            motivo_historial="edicion",
        )
        return {"ok": True, "menu": upd}

    def duplicar_menu(self, id_o_codigo: str) -> dict[str, Any]:
        try:
            m = self.repo.duplicar(id_o_codigo)
            return {"ok": True, "menu": m}
        except ValueError as exc:
            return {"ok": False, "mensaje": str(exc)}

    def archivar_menu(self, id_o_codigo: str) -> dict[str, Any]:
        try:
            m = self.repo.archivar(id_o_codigo)
            return {"ok": True, "menu": m}
        except ValueError as exc:
            return {"ok": False, "mensaje": str(exc)}

    def generar_escandallo_menu(self, id_o_codigo: str) -> dict[str, Any]:
        obj = self.repo.obtener(id_o_codigo)
        if not obj:
            return {"ok": False, "mensaje": "Menú no encontrado."}
        comp = dict(obj.get("composicion") or self._empty_composicion())
        calc = self.motor.calcular(
            nombre_menu=str(obj.get("nombre") or "Menú"),
            comensales=float(obj.get("comensales_recomendado") or 0.0),
            composicion=comp,
            precio_venta_comensal=float(obj.get("precio_venta_comensal") or 0.0),
            precio_venta_total=float(obj.get("precio_venta_total") or 0.0),
        )
        upd = self.repo.actualizar(
            id_o_codigo,
            {
                **obj,
                "lineas": list(calc.get("lineas") or []),
                "coste_por_comensal": calc.get("coste_por_comensal"),
                "coste_total": calc.get("coste_total"),
                "coste_completo": calc.get("coste_completo"),
                "lineas_sin_coste": calc.get("lineas_sin_coste"),
                "advertencias_coste": list(calc.get("advertencias") or []),
                "margen_total": calc.get("margen_total"),
                "margen_porcentual": calc.get("margen_porcentual"),
                "rentabilidad": calc.get("rentabilidad"),
                "incidencias": list(calc.get("incidencias") or []),
                "ultima_generacion": calc.get("fecha_calculo"),
                "estado": ESTADO_CON_INCIDENCIAS if calc.get("incidencias") else ESTADO_OPERATIVO,
            },
            motivo_historial="generacion_escandallo_menu",
        )
        return {"ok": True, "menu": upd, "calculo": calc}

    def rentabilidad(self, id_o_codigo: str) -> dict[str, Any]:
        detalle = self.ver_detalle(id_o_codigo)
        if not detalle.get("ok"):
            return detalle
        menu = detalle.get("menu") or {}
        return {
            "ok": True,
            "menu": menu,
            "rentabilidad": {
                "coste_por_comensal": menu.get("coste_por_comensal"),
                "coste_total": menu.get("coste_total"),
                "precio_venta_comensal": menu.get("precio_venta_comensal"),
                "precio_venta_total": menu.get("precio_venta_total"),
                "margen_total": menu.get("margen_total"),
                "margen_porcentual": menu.get("margen_porcentual"),
                "rentabilidad": menu.get("rentabilidad"),
            },
        }

    def menus_con_incidencias(self) -> dict[str, Any]:
        data = [
            m
            for m in self.repo.listar(incluir_archivados=False)
            if str(m.get("estado") or "") in {ESTADO_CON_INCIDENCIAS, ESTADO_DESACTUALIZADO} or (m.get("incidencias") or [])
        ]
        return {"ok": True, "total": len(data), "menus": data}

    def historial(self, id_o_codigo: str = "") -> dict[str, Any]:
        if id_o_codigo:
            m = self.repo.obtener(id_o_codigo)
            if not m:
                return {"ok": False, "mensaje": "Menú no encontrado."}
            h = list(m.get("historial") or [])
            return {"ok": True, "historial": h, "total": len(h)}
        data = []
        for m in self.repo.listar(incluir_archivados=True):
            for h in list(m.get("historial") or []):
                data.append({"menu": m.get("nombre"), "codigo": m.get("codigo"), **h})
        data.sort(key=lambda x: str(x.get("fecha") or ""), reverse=True)
        return {"ok": True, "historial": data, "total": len(data)}


class BibliotecaMenusUI601:
    def __init__(self, base_dir: Path):
        self.servicio = BibliotecaMenus601(base_dir)

    @staticmethod
    def _menu() -> None:
        print("\nBIBLIOTECA DE MENUS")
        print("1. Buscar menú")
        print("2. Ver todos")
        print("3. Nuevo menú")
        print("4. Editar menú")
        print("5. Duplicar menú")
        print("6. Archivar menú")
        print("7. Generar escandallo del menú")
        print("8. Rentabilidad del menú")
        print("9. Menús con incidencias")
        print("10. Historial")
        print("0. Volver")

    @staticmethod
    def _mostrar(m: dict[str, Any]) -> None:
        print(
            f"- {m.get('codigo')} | {m.get('nombre')} | {m.get('tipo')} | {m.get('estado')} | "
            f"comensales={m.get('comensales_recomendado')} | coste/comensal={m.get('coste_por_comensal')} | "
            f"margen={m.get('margen_porcentual')}"
        )

    @staticmethod
    def _pedir_composicion() -> dict[str, list[dict[str, Any]]]:
        secciones = ["Aperitivos", "Entrantes", "Principales", "Postres", "Bodega", "Extras"]
        comp: dict[str, list[dict[str, Any]]] = {s: [] for s in secciones}
        for sec in secciones:
            print(f"\nSección {sec} (Enter sin nombre para terminar)")
            while True:
                ref = input("Referencia receta/escandallo/producto: ").strip()
                if not ref:
                    break
                tipo = input("Tipo referencia [ESCANDALLO/RECETA/PRODUCTO] (ESCANDALLO): ").strip().upper() or "ESCANDALLO"
                cant = input("Cantidad por comensal (1): ").strip() or "1"
                comp[sec].append({"tipo_referencia": tipo, "referencia": ref, "cantidad": cant})
        return comp

    def ejecutar(self) -> None:
        while True:
            self._menu()
            op = input("Elige una opción: ").strip()
            if op == "0":
                return
            if op == "1":
                self._buscar()
            elif op == "2":
                self._ver_todos()
            elif op == "3":
                self._nuevo()
            elif op == "4":
                self._editar()
            elif op == "5":
                self._duplicar()
            elif op == "6":
                self._archivar()
            elif op == "7":
                self._generar()
            elif op == "8":
                self._rentabilidad()
            elif op == "9":
                self._incidencias()
            elif op == "10":
                self._historial()
            else:
                print("Opción no válida")

    def _buscar(self) -> None:
        filtros = {
            "nombre": input("Nombre: ").strip(),
            "codigo": input("Código: ").strip(),
            "tipo": input("Tipo: ").strip(),
            "plato": input("Plato: ").strip(),
            "ingrediente": input("Ingrediente: ").strip(),
            "estado": input("Estado: ").strip(),
        }
        res = self.servicio.buscar(filtros)
        print(f"Total: {res.get('total', 0)}")
        for m in res.get("menus", [])[:200]:
            self._mostrar(m)

    def _ver_todos(self) -> None:
        res = self.servicio.ver_todos()
        print(f"Total: {res.get('total', 0)}")
        for m in res.get("menus", [])[:200]:
            self._mostrar(m)

    def _nuevo(self) -> None:
        datos = {
            "codigo": input("Código (opcional): ").strip(),
            "nombre": input("Nombre: ").strip(),
            "familia": input("Familia: ").strip(),
            "tipo": input("Tipo (Boda/Empresa/Cocktail/...): ").strip(),
            "comensales_recomendado": input("Número de comensales recomendado: ").strip(),
            "observaciones": input("Observaciones: ").strip(),
            "precio_venta_comensal": input("Precio venta por comensal: ").strip(),
            "composicion": self._pedir_composicion(),
        }
        res = self.servicio.nuevo_menu(datos)
        if not res.get("ok"):
            print(res.get("mensaje"))
            return
        self._mostrar(res.get("menu") or {})

    def _editar(self) -> None:
        clave = input("ID o código del menú: ").strip()
        cambios: dict[str, Any] = {}
        nv = input("Nuevo nombre (vacío mantiene): ").strip()
        if nv:
            cambios["nombre"] = nv
        tipo = input("Nuevo tipo (vacío mantiene): ").strip()
        if tipo:
            cambios["tipo"] = tipo
        com = input("Nuevos comensales (vacío mantiene): ").strip()
        if com:
            cambios["comensales_recomendado"] = com
        pvp = input("Nuevo precio venta/comensal (vacío mantiene): ").strip()
        if pvp:
            cambios["precio_venta_comensal"] = pvp
        if input("¿Sustituir composición? (s/N): ").strip().lower() == "s":
            cambios["composicion"] = self._pedir_composicion()
        res = self.servicio.editar_menu(clave, cambios)
        if not res.get("ok"):
            print(res.get("mensaje"))
            return
        self._mostrar(res.get("menu") or {})

    def _duplicar(self) -> None:
        clave = input("ID o código del menú: ").strip()
        res = self.servicio.duplicar_menu(clave)
        if not res.get("ok"):
            print(res.get("mensaje"))
            return
        self._mostrar(res.get("menu") or {})

    def _archivar(self) -> None:
        clave = input("ID o código del menú: ").strip()
        res = self.servicio.archivar_menu(clave)
        if not res.get("ok"):
            print(res.get("mensaje"))
            return
        self._mostrar(res.get("menu") or {})

    def _generar(self) -> None:
        clave = input("ID o código del menú: ").strip()
        res = self.servicio.generar_escandallo_menu(clave)
        if not res.get("ok"):
            print(res.get("mensaje"))
            return
        self._mostrar(res.get("menu") or {})
        for i in (res.get("calculo") or {}).get("incidencias", [])[:50]:
            print(f"  * {i.get('tipo')}: {i.get('detalle')}")

    def _rentabilidad(self) -> None:
        clave = input("ID o código del menú: ").strip()
        res = self.servicio.rentabilidad(clave)
        if not res.get("ok"):
            print(res.get("mensaje"))
            return
        r = res.get("rentabilidad") or {}
        print(f"Coste/comensal: {r.get('coste_por_comensal')}")
        print(f"Coste total: {r.get('coste_total')}")
        print(f"Precio venta/comensal: {r.get('precio_venta_comensal')}")
        print(f"Precio venta total: {r.get('precio_venta_total')}")
        print(f"Margen total: {r.get('margen_total')}")
        print(f"Margen (%): {r.get('margen_porcentual')}")
        print(f"Rentabilidad: {r.get('rentabilidad')}")

    def _incidencias(self) -> None:
        res = self.servicio.menus_con_incidencias()
        print(f"Total con incidencias: {res.get('total', 0)}")
        for m in res.get("menus", [])[:200]:
            self._mostrar(m)

    def _historial(self) -> None:
        clave = input("ID/código menú (vacío=todos): ").strip()
        res = self.servicio.historial(clave)
        if not res.get("ok"):
            print(res.get("mensaje"))
            return
        print(f"Entradas: {res.get('total', 0)}")
        for h in res.get("historial", [])[:300]:
            print(
                f"- {h.get('fecha')} | {h.get('codigo') or ''} | coste={h.get('coste')} | "
                f"margen={h.get('margen')} | venta={h.get('precio_venta')} | comensales={h.get('comensales')} | v={h.get('version_menu')}"
            )


__all__ = [
    "RepositorioBibliotecaMenus601",
    "BibliotecaMenus601",
    "BibliotecaMenusUI601",
]
