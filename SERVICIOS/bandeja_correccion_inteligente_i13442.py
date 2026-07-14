from __future__ import annotations

from typing import Any

from SERVICIOS.bandeja_correccion_postimportacion_i13441 import (
    BandejaCorreccionPostimportacionI13441,
)
from SERVICIOS.simulador_importacion_menus_i13411 import _norm
from SERVICIOS.utilidades_importador_i135 import (
    agrupar_incidencias, coincidencias_exactas, filtrar_incidencias, fingerprint_incidencia,
)


class BandejaCorreccionInteligenteI13442(BandejaCorreccionPostimportacionI13441):
    """Navegación, agrupación y corrección masiva conservadora sobre I1.3.4.4.1."""

    VERSION = "I1.3.4.4.2"
    RUTA_SESIONES = "DATOS/mur/correcciones_i13442"

    @staticmethod
    def _fingerprint(inc: dict[str, Any]) -> tuple[str, str, str, str, str]:
        return fingerprint_incidencia(inc)

    def incidencias_filtradas(
        self,
        *,
        severidad: str | None = None,
        codigo: str | None = None,
        menu: str | None = None,
    ) -> list[tuple[int, dict[str, Any]]]:
        return filtrar_incidencias(self.incidencias(), severidad=severidad, codigo=codigo, menu=menu)

    def agrupar_por_tipo(self) -> list[dict[str, Any]]:
        return agrupar_incidencias(self.incidencias(), campo="codigo", valor_vacio="SIN_CODIGO")

    def agrupar_por_menu(self) -> list[dict[str, Any]]:
        return agrupar_incidencias(self.incidencias(), campo="menu", valor_vacio="Sin menú")

    def indices_por_codigo(self, codigo: str) -> list[int]:
        return [i for i, _ in self.incidencias_filtradas(codigo=codigo)]

    def indices_por_menu(self, menu: str) -> list[int]:
        return [i for i, _ in self.incidencias_filtradas(menu=menu)]

    def _indice_por_fingerprint(self, fp: tuple[str, str, str, str, str]) -> int | None:
        for i, inc in enumerate(self.incidencias(), 1):
            if self._fingerprint(inc) == fp:
                return i
        return None

    @staticmethod
    def _coincidencias_exactas(catalogo: list[dict[str, Any]], texto: str, campos: tuple[str, ...]) -> list[dict[str, Any]]:
        return coincidencias_exactas(catalogo, texto, campos)

    def resolver_automaticamente_univocos(self) -> dict[str, Any]:
        """Resuelve solo incidencias con una única respuesta exacta y segura."""
        objetivos = [self._fingerprint(inc) for inc in self.incidencias()]
        acciones: list[dict[str, Any]] = []
        omitidas: list[dict[str, Any]] = []

        for fp in objetivos:
            idx = self._indice_por_fingerprint(fp)
            if idx is None:
                continue
            inc = self.incidencias()[idx - 1]
            codigo = str(inc.get("codigo") or "")
            try:
                if codigo == "SECCION_REFERENCIA_INEXISTENTE":
                    seccion = str(inc.get("referencia") or "").strip()
                    if not seccion:
                        mensaje = str(inc.get("mensaje") or "")
                        marca = "no está registrada:"
                        if marca in mensaje:
                            seccion = mensaje.split(marca, 1)[1].strip().rstrip(".")
                    if not seccion or _norm(seccion) in {"sin seccion", "ninguna"}:
                        omitidas.append({"codigo": codigo, "motivo": "Sección vacía o no concreta", "incidencia": inc})
                        continue
                    cambios = self.cambiar_seccion([idx], seccion, crear_si_falta=True)
                    acciones.append({"codigo": codigo, "accion": "CREAR_O_ASIGNAR_SECCION", "cantidad": cambios, "valor": seccion})
                    continue

                if codigo in {"FOOD_COST_INCOHERENTE", "BENEFICIO_INCOHERENTE"}:
                    cambios = self.recalcular_economia([idx])
                    acciones.append({"codigo": codigo, "accion": "RECALCULAR_ECONOMIA", "cantidad": cambios})
                    continue

                if codigo == "RECETA_REFERENCIA_INEXISTENTE":
                    texto = str(inc.get("referencia") or inc.get("plato") or "")
                    candidatos = self._coincidencias_exactas(self.recetas, texto, ("nombre", "receta", "descripcion"))
                    if len(candidatos) == 1:
                        self.vincular_receta(idx, candidatos[0])
                        acciones.append({"codigo": codigo, "accion": "VINCULAR_RECETA_EXACTA", "valor": candidatos[0].get("nombre")})
                    else:
                        omitidas.append({"codigo": codigo, "motivo": f"Coincidencias exactas: {len(candidatos)}", "incidencia": inc})
                    continue

                if codigo == "PLATO_SIN_RECETA_PRINCIPAL":
                    texto = str(inc.get("plato") or "")
                    candidatos = self._coincidencias_exactas(self.recetas, texto, ("nombre", "receta", "descripcion"))
                    if len(candidatos) == 1:
                        self.vincular_receta(idx, candidatos[0])
                        acciones.append({"codigo": codigo, "accion": "VINCULAR_RECETA_POR_PLATO_EXACTO", "valor": candidatos[0].get("nombre")})
                    else:
                        omitidas.append({"codigo": codigo, "motivo": f"Coincidencias exactas: {len(candidatos)}", "incidencia": inc})
                    continue

                if codigo == "ARTICULO_REFERENCIA_INEXISTENTE":
                    texto = str(inc.get("referencia") or "")
                    candidatos = self._coincidencias_exactas(self.articulos, texto, ("nombre", "articulo", "descripcion"))
                    if len(candidatos) == 1:
                        self.vincular_articulo(idx, candidatos[0])
                        acciones.append({"codigo": codigo, "accion": "VINCULAR_ARTICULO_EXACTO", "valor": candidatos[0].get("nombre") or candidatos[0].get("articulo")})
                    else:
                        omitidas.append({"codigo": codigo, "motivo": f"Coincidencias exactas: {len(candidatos)}", "incidencia": inc})
                    continue

                omitidas.append({"codigo": codigo, "motivo": "No existe regla automática segura", "incidencia": inc})
            except Exception as exc:  # La automatización nunca debe romper la sesión completa.
                omitidas.append({"codigo": codigo, "motivo": f"Error controlado: {exc}", "incidencia": inc})

        resultado = {
            "resueltas": len(acciones),
            "acciones": acciones,
            "omitidas": len(omitidas),
            "detalle_omitidas": omitidas,
            "resumen_final": self.resumen(),
        }
        self._registrar("RESOLUCION_AUTOMATICA_UNIVOCA", resueltas=len(acciones), omitidas=len(omitidas))
        self._guardar_sesion()
        return resultado


def formatear_navegacion_i13442(
    bandeja: BandejaCorreccionInteligenteI13442,
    *,
    vista: str = "TODAS",
    valor: str | None = None,
) -> str:
    r = bandeja.resumen()
    vista = vista.upper()
    if vista == "ERRORES":
        filas = bandeja.incidencias_filtradas(severidad="ERROR")
    elif vista == "AVISOS":
        filas = bandeja.incidencias_filtradas(severidad="AVISO")
    elif vista == "TIPO" and valor:
        filas = bandeja.incidencias_filtradas(codigo=valor)
    elif vista == "MENU" and valor:
        filas = bandeja.incidencias_filtradas(menu=valor)
    else:
        filas = list(enumerate(bandeja.incidencias(), 1))

    lines = [
        "I1.3.4.4.2 — CORRECCIÓN INTELIGENTE MASIVA Y NAVEGACIÓN",
        "=" * 78,
        f"Sesión: {r['sesion_id']} | Estado: {r['estado']} | Vista: {vista}" + (f" ({valor})" if valor else ""),
        f"Incidencias totales: {r['total']} | Errores: {r['errores']} | Avisos: {r['avisos']} | Mostradas: {len(filas)}",
        "-" * 78,
    ]
    for i, inc in filas:
        ctx = " | ".join(x for x in [inc.get("menu"), inc.get("plato"), inc.get("referencia")] if x)
        lines.append(f"{i}. [{inc.get('severidad')}] {inc.get('codigo')}: {inc.get('mensaje')}" + (f" | {ctx}" if ctx else ""))
    lines.extend([
        "=" * 78,
        "X=Automático unívoco | F=Filtros | T=Agrupar tipo | U=Agrupar menú | B=Acción masiva",
        "E=Eliminar | R=Renombrar | V=Vincular | S=Sección | A=Economía | M=Mantener | G=Guardar | 0=Salir",
        "Nada afecta al catálogo real hasta confirmar G y escribir GUARDAR.",
    ])
    return "\n".join(lines)


def formatear_grupos_tipo_i13442(bandeja: BandejaCorreccionInteligenteI13442) -> str:
    lines = ["INCIDENCIAS AGRUPADAS POR TIPO", "=" * 78]
    for i, g in enumerate(bandeja.agrupar_por_tipo(), 1):
        lines.append(f"{i}. {g['codigo']} | total={g['cantidad']} | errores={g['errores']} | avisos={g['avisos']} | índices={','.join(map(str, g['indices']))}")
    return "\n".join(lines)


def formatear_grupos_menu_i13442(bandeja: BandejaCorreccionInteligenteI13442) -> str:
    lines = ["INCIDENCIAS AGRUPADAS POR MENÚ", "=" * 78]
    for i, g in enumerate(bandeja.agrupar_por_menu(), 1):
        lines.append(f"{i}. {g['menu']} | total={g['cantidad']} | errores={g['errores']} | avisos={g['avisos']} | índices={','.join(map(str, g['indices']))}")
    return "\n".join(lines)
