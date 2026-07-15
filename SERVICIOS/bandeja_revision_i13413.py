from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from SERVICIOS.simulador_importacion_menus_i13412 import SimuladorImportacionMenusI13412
from SERVICIOS.simulador_importacion_menus_i13411 import _stable_id, _norm


@dataclass
class IncidenciaRevision:
    incidencia_id: str
    numero: int
    nivel: str
    tipo: str
    nombre: str
    menu: str
    plato: str | None
    propuesta: str
    confianza: int
    motivo: str
    accion_ids: list[str]
    fingerprint: str
    estado: str = "PENDIENTE"
    decision: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BandejaRevisionI13413:
    """I1.3.4.1.3 — revisión y limpieza del plan, sin escribir datos de negocio."""

    VERSION = "I1.3.4.1.3"
    TIPOS_VALIDOS = {
        "PLATO_RECETA", "PLATO_COMPUESTO", "PLATO_PENDIENTE", "APERITIVO_PREPARADO",
        "MATERIA_PRIMA", "ARTICULO_COMERCIAL", "BEBIDA", "VINO", "CAVA", "AGUA",
        "CAFE_INFUSION", "PAN", "COMPLEMENTO", "SERVICIO", "ARTICULO_DIRECTO",
    }
    PATRONES_CULINARIOS = re.compile(
        r"\b(tartar|tempura|ensalada|coulant|lingote|crema|salsa|parrillada|gazpacho|salmorejo|brocheta|croqueta|hamburguesa|lenguado|solomillo|tournedo|postre|pastel|tarta)\b",
        re.I,
    )

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir).resolve()
        self.simulador = SimuladorImportacionMenusI13412(self.base_dir)
        self.dir_sesiones = self.base_dir / "DATOS" / "mur" / "revisiones_i13413"
        self.ruta_aprendizaje = self.base_dir / "DATOS" / "mur" / "aprendizajes_revision_i13413.json"

    @staticmethod
    def _ahora() -> str:
        return datetime.now(timezone.utc).isoformat()

    def preparar(self, ruta_excel: str | Path, hojas: list[str] | None = None) -> dict[str, Any]:
        plan = self.simulador.simular(ruta_excel, hojas=hojas)
        return self.crear_sesion(plan, origen={"excel": str(ruta_excel), "hojas": hojas or []})

    @staticmethod
    def _fingerprint_incidencia(menu: str, plato: str | None, nombre: str, tipo: str, nivel: str) -> str:
        return _stable_id("FP", _norm(menu), _norm(plato), _norm(nombre), tipo, nivel)

    def crear_sesion(self, plan: dict[str, Any], origen: dict[str, Any] | None = None) -> dict[str, Any]:
        trabajo = deepcopy(plan)
        incidencias = self._extraer_incidencias(trabajo)
        sesion_id = _stable_id("REV", self.VERSION, trabajo.get("plan_id"), self._ahora())
        sesion = {
            "version": self.VERSION,
            "sesion_id": sesion_id,
            "creada_en": self._ahora(),
            "actualizada_en": self._ahora(),
            "origen": origen or {},
            "plan_original_id": trabajo.get("plan_id"),
            "plan": trabajo,
            "incidencias": [i.to_dict() for i in incidencias],
            "historial": [],
            "resumen_revision": {},
            "escrituras_habilitadas": False,
        }
        self._recalcular(sesion)
        self._guardar_sesion(sesion)
        return sesion

    def _extraer_incidencias(self, plan: dict[str, Any]) -> list[IncidenciaRevision]:
        grupos: dict[tuple[str, str, str], dict[str, Any]] = {}
        for a in plan.get("acciones", []):
            d = a.get("detalle", {})
            nombre = str(a.get("nombre") or "")
            menu = str(d.get("menu") or "")
            plato = str(d.get("plato") or "") or None
            bloqueada = a.get("estado") == "BLOQUEADA"
            dudosa = False
            motivo = ""
            propuesta = str(a.get("entidad") or "")
            confianza = 100
            nivel = "BLOQUEANTE" if bloqueada else "AVISO"
            tipo = "BLOQUEO" if bloqueada else "CLASIFICACION_DUDOSA"

            if bloqueada:
                motivo = "Elemento o componente no resuelto antes de importar."
                confianza = 0
            elif a.get("entidad") in {"COMPLEMENTO", "ARTICULO_DIRECTO"} and self.PATRONES_CULINARIOS.search(nombre):
                dudosa = True
                motivo = "La clasificación automática es válida, pero el nombre parece una elaboración culinaria."
                confianza = 55 if a.get("entidad") == "COMPLEMENTO" else 65
            elif a.get("entidad") == "PLATO_MENU" and not plato:
                # El plato principal se revisará por sus componentes; no se duplica salvo nombres muy extraños.
                if len(nombre.split()) <= 1:
                    dudosa = True
                    motivo = "Nombre demasiado corto para confirmar que es un plato."
                    confianza = 45
            if not bloqueada and not dudosa:
                continue

            clave = (_norm(menu), _norm(plato or nombre), _norm(nombre))
            g = grupos.setdefault(clave, {
                "nivel": nivel, "tipo": tipo, "nombre": nombre, "menu": menu,
                "plato": plato, "propuesta": propuesta, "confianza": confianza,
                "motivo": motivo, "accion_ids": [],
            })
            g["accion_ids"].append(a.get("accion_id"))
            if bloqueada:
                g.update({"nivel": "BLOQUEANTE", "tipo": "BLOQUEO", "confianza": 0, "motivo": motivo})

        salida = []
        for n, g in enumerate(grupos.values(), 1):
            fp = self._fingerprint_incidencia(
                str(g.get("menu") or ""),
                str(g.get("plato") or "") or None,
                str(g.get("nombre") or ""),
                str(g.get("tipo") or ""),
                str(g.get("nivel") or ""),
            )
            iid = _stable_id("INC", self.VERSION, fp, n)
            salida.append(IncidenciaRevision(incidencia_id=iid, numero=n, fingerprint=fp, **g))
        return salida

    @staticmethod
    def _parse_numeros(valor: str | list[int]) -> list[int]:
        if isinstance(valor, list):
            return sorted({int(x) for x in valor if int(x) > 0})
        nums: set[int] = set()
        for parte in re.split(r"[,;\s]+", str(valor).strip()):
            if parte.isdigit() and int(parte) > 0:
                nums.add(int(parte))
        return sorted(nums)

    def aplicar_masiva(self, sesion: dict[str, Any], numeros: str | list[int], accion: str, **datos: Any) -> dict[str, Any]:
        seleccion = self._parse_numeros(numeros)
        mapa = {int(i["numero"]): i for i in sesion.get("incidencias", []) if i.get("estado") == "PENDIENTE"}
        elegidas = [mapa[n] for n in seleccion if n in mapa]
        if not elegidas:
            raise ValueError("No se seleccionó ninguna incidencia pendiente válida.")
        accion = accion.strip().upper()
        if accion not in {"ELIMINAR", "CLASIFICAR", "MANTENER"}:
            raise ValueError("Acción masiva no permitida.")
        for inc in elegidas:
            if accion == "ELIMINAR":
                self._eliminar(sesion, inc)
            elif accion == "CLASIFICAR":
                self._reclasificar(sesion, inc, str(datos.get("clasificacion") or ""))
            else:
                self._mantener(sesion, inc)
        self._registrar(sesion, accion, elegidas, datos)
        self._recalcular(sesion)
        self._guardar_sesion(sesion)
        return sesion

    def renombrar(self, sesion: dict[str, Any], numero: int, nuevo_nombre: str, recordar: bool = False) -> dict[str, Any]:
        inc = self._obtener(sesion, numero)
        nuevo = str(nuevo_nombre or "").strip()
        if not nuevo:
            raise ValueError("El nuevo nombre no puede estar vacío.")
        for a in sesion["plan"].get("acciones", []):
            if a.get("accion_id") in inc["accion_ids"]:
                a["nombre"] = nuevo
                if a.get("detalle", {}).get("plato") == inc.get("nombre"):
                    a["detalle"]["plato"] = nuevo
                a["estado"] = "PLANIFICADA"
                if a.get("tipo") == "RESOLVER_ANTES_DE_IMPORTAR":
                    a["tipo"] = "RENOMBRAR_Y_REVISAR"
        inc["estado"] = "RESUELTA"
        inc["decision"] = {"accion": "RENOMBRAR", "valor": nuevo}
        self._registrar(sesion, "RENOMBRAR", [inc], {"nuevo_nombre": nuevo})
        if recordar:
            self._aprender(inc, "RENOMBRAR", nuevo)
        self._recalcular(sesion); self._guardar_sesion(sesion)
        return sesion

    def vincular(self, sesion: dict[str, Any], numero: int, tipo: str, destino: str, recordar: bool = False) -> dict[str, Any]:
        inc = self._obtener(sesion, numero)
        tipo = tipo.strip().upper()
        if tipo not in {"RECETA", "ARTICULO"}:
            raise ValueError("Tipo de vínculo no válido.")
        destino = str(destino or "").strip()
        if not destino:
            raise ValueError("El destino no puede estar vacío.")
        for a in sesion["plan"].get("acciones", []):
            if a.get("accion_id") in inc["accion_ids"]:
                a["tipo"] = "VINCULAR"
                a["entidad"] = "RECETA_PRINCIPAL" if tipo == "RECETA" else "ARTICULO_DIRECTO"
                a["nombre"] = destino
                a["estado"] = "PLANIFICADA"
                a.setdefault("detalle", {})["resuelto_por_revision"] = True
        inc["estado"] = "RESUELTA"
        inc["decision"] = {"accion": "VINCULAR", "tipo": tipo, "destino": destino}
        self._registrar(sesion, "VINCULAR", [inc], inc["decision"])
        if recordar:
            self._aprender(inc, f"VINCULAR_{tipo}", destino)
        self._recalcular(sesion); self._guardar_sesion(sesion)
        return sesion

    def _obtener(self, sesion: dict[str, Any], numero: int) -> dict[str, Any]:
        inc = next((i for i in sesion.get("incidencias", []) if int(i["numero"]) == int(numero) and i.get("estado") == "PENDIENTE"), None)
        if not inc:
            raise ValueError("Incidencia no encontrada o ya resuelta.")
        return inc

    def _eliminar(self, sesion: dict[str, Any], inc: dict[str, Any]) -> None:
        ids = set(inc.get("accion_ids", []))
        nombre = _norm(inc.get("nombre")); menu = _norm(inc.get("menu")); plato = _norm(inc.get("plato"))
        nuevas=[]
        for a in sesion["plan"].get("acciones", []):
            d=a.get("detalle", {})
            relacionada = a.get("accion_id") in ids
            # Si se elimina un plato, elimina su relación y todos sus componentes.
            if plato and _norm(d.get("plato")) == plato and _norm(d.get("menu")) == menu:
                relacionada = True
            if not plato and _norm(a.get("nombre")) == nombre and _norm(d.get("menu")) == menu:
                relacionada = True
            if not relacionada:
                nuevas.append(a)
        sesion["plan"]["acciones"] = nuevas
        inc["estado"] = "ELIMINADA"
        inc["decision"] = {"accion": "ELIMINAR_DE_SIMULACION"}

    def _reclasificar(self, sesion: dict[str, Any], inc: dict[str, Any], clasificacion: str) -> None:
        clasificacion = clasificacion.strip().upper()
        if clasificacion not in self.TIPOS_VALIDOS:
            raise ValueError("Clasificación no válida.")
        mapping = {
            "PLATO_RECETA": ("CREAR_RELACION", "PLATO_MENU"),
            "PLATO_COMPUESTO": ("CREAR_RELACION", "PLATO_MENU"),
            "PLATO_PENDIENTE": ("CREAR_RELACION", "PLATO_MENU"),
            "APERITIVO_PREPARADO": ("VINCULAR", "APERITIVO_PREPARADO"),
            "MATERIA_PRIMA": ("VINCULAR", "ARTICULO_DIRECTO"),
            "ARTICULO_COMERCIAL": ("VINCULAR", "ARTICULO_DIRECTO"),
            "ARTICULO_DIRECTO": ("VINCULAR", "ARTICULO_DIRECTO"),
            "BEBIDA": ("VINCULAR", "BEBIDA_MENU"), "VINO": ("VINCULAR", "BEBIDA_MENU"),
            "CAVA": ("VINCULAR", "BEBIDA_MENU"), "AGUA": ("VINCULAR", "BEBIDA_MENU"),
            "CAFE_INFUSION": ("CREAR_RELACION", "COMPLEMENTO"), "PAN": ("CREAR_RELACION", "COMPLEMENTO"),
            "COMPLEMENTO": ("CREAR_RELACION", "COMPLEMENTO"), "SERVICIO": ("CREAR_RELACION", "SERVICIO"),
        }
        tipo, entidad = mapping[clasificacion]
        for a in sesion["plan"].get("acciones", []):
            if a.get("accion_id") in inc["accion_ids"]:
                a.update({"tipo": tipo, "entidad": entidad, "estado": "PLANIFICADA"})
                a.setdefault("detalle", {})["clasificacion_revision"] = clasificacion
        inc["estado"] = "RESUELTA"
        inc["decision"] = {"accion": "CLASIFICAR", "valor": clasificacion}

    @staticmethod
    def _mantener(sesion: dict[str, Any], inc: dict[str, Any]) -> None:
        # Mantener un aviso lo cierra; un bloqueo continúa abierto por seguridad.
        if inc.get("nivel") == "BLOQUEANTE":
            inc["decision"] = {"accion": "MANTENER_BLOQUEO"}
        else:
            inc["estado"] = "RESUELTA"
            inc["decision"] = {"accion": "MANTENER"}

    def _registrar(self, sesion: dict[str, Any], accion: str, incidencias: list[dict[str, Any]], datos: dict[str, Any]) -> None:
        marca_tiempo = self._ahora()
        sesion.setdefault("historial", []).append({
            "fecha": marca_tiempo, "accion": accion,
            "incidencias": [i.get("incidencia_id") for i in incidencias], "datos": datos,
        })
        for inc in incidencias:
            fp = str(inc.get("fingerprint") or "")
            for a in sesion.get("plan", {}).get("acciones", []):
                if a.get("accion_id") in set(inc.get("accion_ids", [])):
                    d = a.setdefault("detalle", {})
                    d["revision_sesion_id"] = sesion.get("sesion_id")
                    d["revision_incidencia_id"] = inc.get("incidencia_id")
                    d["revision_fingerprint"] = fp
                    d["revision_ultima_accion"] = accion
                    d["revision_ultima_accion_en"] = marca_tiempo
        sesion["actualizada_en"] = marca_tiempo

    def _recalcular(self, sesion: dict[str, Any]) -> None:
        plan = sesion["plan"]
        acciones = plan.get("acciones", [])
        bloqueadas = [a for a in acciones if a.get("estado") == "BLOQUEADA"]
        plan["bloqueos"] = [b for b in plan.get("bloqueos", []) if any(_norm(a.get("nombre")) == _norm(b.get("componente") or b.get("nombre")) and a.get("estado") == "BLOQUEADA" for a in acciones)]
        plan["resumen"].update({
            "acciones": len(acciones), "ejecutables": sum(a.get("estado") == "PLANIFICADA" for a in acciones),
            "bloqueadas": len(bloqueadas), "vincular": sum(a.get("tipo") == "VINCULAR" for a in acciones),
            "relaciones": sum(a.get("tipo") in {"CREAR_RELACION", "CREAR_O_REUTILIZAR"} for a in acciones),
        })
        pendientes = [i for i in sesion.get("incidencias", []) if i.get("estado") == "PENDIENTE"]
        bloqueantes = [i for i in pendientes if i.get("nivel") == "BLOQUEANTE"]
        pendientes_ordenadas = sorted(pendientes, key=lambda i: str(i.get("fingerprint") or ""))
        huella_pendientes = _stable_id(
            "DUDAS", self.VERSION,
            *(str(i.get("fingerprint") or "") for i in pendientes_ordenadas),
        )
        plan["estado_simulacion"] = "LISTA_PARA_TRANSACCION" if not bloqueadas and not bloqueantes else "BLOQUEADA"
        sesion["dudas_pendientes"] = [
            {
                "numero": i.get("numero"),
                "incidencia_id": i.get("incidencia_id"),
                "fingerprint": i.get("fingerprint"),
                "menu": i.get("menu"),
                "plato": i.get("plato"),
                "nombre": i.get("nombre"),
                "nivel": i.get("nivel"),
                "tipo": i.get("tipo"),
            }
            for i in pendientes_ordenadas
        ]

        menu_ids_por_nombre: dict[str, str] = {}
        for a in acciones:
            if a.get("entidad") != "MENU":
                continue
            d = a.get("detalle", {})
            menu_nombre_norm = _norm(a.get("nombre") or d.get("menu"))
            menu_id = str(d.get("menu_id") or _stable_id("MENU", a.get("nombre"), d.get("hoja")))
            if menu_nombre_norm:
                menu_ids_por_nombre[menu_nombre_norm] = menu_id
        menus_pendientes = {
            menu_ids_por_nombre.get(_norm(i.get("menu")))
            for i in pendientes
            if menu_ids_por_nombre.get(_norm(i.get("menu")))
        }
        menus_validados = sorted(mid for mid in menu_ids_por_nombre.values() if mid not in menus_pendientes)
        menus_bloqueados = sorted(mid for mid in menus_pendientes)

        sesion["resumen_revision"] = {
            "iniciales": len(sesion.get("incidencias", [])),
            "pendientes": len(pendientes),
            "bloqueantes": len(bloqueantes),
            "resueltas": sum(i.get("estado") == "RESUELTA" for i in sesion.get("incidencias", [])),
            "eliminadas": sum(i.get("estado") == "ELIMINADA" for i in sesion.get("incidencias", [])),
            "estado_plan": plan["estado_simulacion"],
            "huella_dudas_pendientes": huella_pendientes,
            "menus_validados": len(menus_validados),
            "menus_bloqueados": len(menus_bloqueados),
        }
        plan["revision"] = {
            "version": self.VERSION,
            "sesion_id": sesion.get("sesion_id"),
            "actualizada_en": sesion.get("actualizada_en"),
            "pendientes": len(pendientes),
            "bloqueantes": len(bloqueantes),
            "huella_dudas_pendientes": huella_pendientes,
        }
        plan["menus_validados"] = menus_validados
        plan["menus_bloqueados"] = menus_bloqueados
        plan["plan_id"] = _stable_id("PLAN", self.VERSION, *(a.get("accion_id") for a in acciones), *(str(i.get("decision")) for i in sesion.get("incidencias", [])))

    def _guardar_sesion(self, sesion: dict[str, Any]) -> Path:
        self.dir_sesiones.mkdir(parents=True, exist_ok=True)
        ruta = self.dir_sesiones / f"{sesion['sesion_id']}.json"
        tmp = ruta.with_suffix(".tmp")
        tmp.write_text(json.dumps(sesion, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(ruta)
        sesion["ruta_sesion"] = str(ruta)
        return ruta

    def _aprender(self, inc: dict[str, Any], accion: str, valor: str) -> None:
        self.ruta_aprendizaje.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = json.loads(self.ruta_aprendizaje.read_text(encoding="utf-8")) if self.ruta_aprendizaje.exists() else []
        except Exception:
            data = []
        clave = _stable_id("APR", inc.get("nombre"), inc.get("menu"), accion)
        reg = {"id": clave, "texto": inc.get("nombre"), "menu": inc.get("menu"), "accion": accion, "valor": valor, "confirmado": True, "fecha": self._ahora()}
        data = [x for x in data if x.get("id") != clave] + [reg]
        tmp = self.ruta_aprendizaje.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.ruta_aprendizaje)


def formatear_bandeja_i13413(sesion: dict[str, Any], solo_pendientes: bool = True) -> str:
    rr = sesion.get("resumen_revision", {})
    lineas = [
        "I1.3.4.1.3 — BANDEJA DE REVISIÓN Y LIMPIEZA MASIVA", "=" * 78,
        f"Sesión: {sesion.get('sesion_id')} | Plan: {sesion.get('plan', {}).get('plan_id')}",
        f"Incidencias iniciales: {rr.get('iniciales', 0)} | Pendientes: {rr.get('pendientes', 0)} | Bloqueantes: {rr.get('bloqueantes', 0)}",
        f"Resueltas: {rr.get('resueltas', 0)} | Eliminadas: {rr.get('eliminadas', 0)} | Estado plan: {rr.get('estado_plan')}",
        "-" * 78,
    ]
    items = [i for i in sesion.get("incidencias", []) if not solo_pendientes or i.get("estado") == "PENDIENTE"]
    if not items:
        lineas.append("No quedan elementos pendientes de revisión.")
    for i in items:
        contexto = f" | menú={i.get('menu')}" + (f" | plato={i.get('plato')}" if i.get('plato') else "")
        lineas += [
            f"{i.get('numero')}. [{i.get('nivel')}] {i.get('nombre')}",
            f"   Propuesta: {i.get('propuesta')} | Confianza: {i.get('confianza')}%{contexto}",
            f"   Motivo: {i.get('motivo')}",
        ]
    lineas += [
        "=" * 78,
        "E=Eliminar varios | C=Cambiar clasificación | R=Renombrar | V=Vincular | M=Mantener | 0=Terminar",
        "Las eliminaciones afectan solo a la simulación. No se modifica el Excel ni la base de datos.",
    ]
    return "\n".join(lineas)
