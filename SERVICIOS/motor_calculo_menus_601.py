from __future__ import annotations

from datetime import datetime
from typing import Any

from SERVICIOS.biblioteca_escandallos_601 import RepositorioBibliotecaEscandallos601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


ESTADO_BORRADOR = "BORRADOR"
ESTADO_OPERATIVO = "OPERATIVO"
ESTADO_CON_INCIDENCIAS = "CON_INCIDENCIAS"
ESTADO_DESACTUALIZADO = "DESACTUALIZADO"
ESTADO_ARCHIVADO = "ARCHIVADO"

INC_PLATO_INEXISTENTE = "PLATO_INEXISTENTE"
INC_ESCANDALLO_INEXISTENTE = "ESCANDALLO_INEXISTENTE"
INC_ESCANDALLO_DESACTUALIZADO = "ESCANDALLO_DESACTUALIZADO"
INC_PRODUCTO_SIN_PRECIO = "PRODUCTO_SIN_PRECIO"
INC_PLATO_ARCHIVADO = "PLATO_ARCHIVADO"
INC_DUPLICADO = "DUPLICADO"


class MotorCalculoMenus601:
    def __init__(
        self,
        repo_esc: RepositorioBibliotecaEscandallos601,
        repo_rec: RepositorioBibliotecaRecetas601,
        repo_prod: RepositorioProductosMaestro601,
    ):
        self.repo_esc = repo_esc
        self.repo_rec = repo_rec
        self.repo_prod = repo_prod

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def _norm(txt: Any) -> str:
        return " ".join(str(txt or "").strip().lower().split())

    @staticmethod
    def _to_float(value: Any) -> float:
        if value in (None, ""):
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        txt = str(value).strip().replace("€", "").replace(" ", "")
        if "," in txt and "." in txt:
            txt = txt.replace(".", "").replace(",", ".")
        else:
            txt = txt.replace(",", ".")
        try:
            return float(txt)
        except ValueError:
            return 0.0

    def _buscar_escandallo(self, ref: str) -> dict[str, Any] | None:
        if not ref:
            return None
        e = self.repo_esc.obtener(ref)
        if e:
            return e
        clave = self._norm(ref)
        for item in self.repo_esc.listar(incluir_archivados=True):
            if clave == self._norm(item.get("nombre")):
                return item
        return None

    def _buscar_receta(self, ref: str) -> dict[str, Any] | None:
        if not ref:
            return None
        r = self.repo_rec.obtener(ref)
        if r:
            return r
        clave = self._norm(ref)
        for item in self.repo_rec.listar(incluir_archivadas=True):
            if clave == self._norm(item.get("nombre")):
                return item
        return None

    def _buscar_producto(self, ref: str) -> dict[str, Any] | None:
        if not ref:
            return None
        p = self.repo_prod.obtener_producto(ref)
        if p:
            return p
        encontrados = self.repo_prod.buscar_productos({"nombre": ref})
        if not encontrados:
            return None
        return encontrados[0]

    def calcular(
        self,
        *,
        nombre_menu: str,
        comensales: float,
        composicion: dict[str, list[dict[str, Any]]],
        precio_venta_comensal: float = 0.0,
        precio_venta_total: float = 0.0,
    ) -> dict[str, Any]:
        incidencias: list[dict[str, Any]] = []
        lineas: list[dict[str, Any]] = []
        vistos: set[tuple[str, str, str]] = set()

        for seccion, items in (composicion or {}).items():
            for item in list(items or []):
                tipo_ref = str(item.get("tipo_referencia") or "ESCANDALLO").upper()
                referencia = str(item.get("referencia") or item.get("nombre") or "").strip()
                cantidad = self._to_float(item.get("cantidad") or 1) or 1.0
                key = (self._norm(seccion), self._norm(tipo_ref), self._norm(referencia))
                if key in vistos:
                    incidencias.append({
                        "tipo": INC_DUPLICADO,
                        "detalle": f"Elemento duplicado en menú: {seccion} - {referencia}",
                    })
                vistos.add(key)

                coste_por_comensal = 0.0
                estado_linea = ESTADO_OPERATIVO
                inc_linea: list[dict[str, Any]] = []
                snapshot_ref: dict[str, Any] = {}

                if tipo_ref == "ESCANDALLO":
                    esc = self._buscar_escandallo(referencia)
                    if not esc:
                        inc_linea.append({"tipo": INC_ESCANDALLO_INEXISTENTE, "detalle": f"Escandallo inexistente: {referencia}"})
                    else:
                        estado_esc = str(esc.get("estado") or "")
                        if estado_esc == ESTADO_ARCHIVADO:
                            inc_linea.append({"tipo": INC_PLATO_ARCHIVADO, "detalle": f"Escandallo archivado: {esc.get('nombre')}"})
                        if estado_esc == ESTADO_DESACTUALIZADO:
                            inc_linea.append({"tipo": INC_ESCANDALLO_DESACTUALIZADO, "detalle": f"Escandallo desactualizado: {esc.get('nombre')}"})
                        coste_por_comensal = self._to_float(esc.get("coste_por_racion")) * cantidad
                        snapshot_ref = {
                            "tipo": "ESCANDALLO",
                            "id": esc.get("id"),
                            "codigo": esc.get("codigo"),
                            "nombre": esc.get("nombre"),
                            "estado": esc.get("estado"),
                            "calculo_version": esc.get("calculo_version"),
                            "fecha_ultimo_calculo": esc.get("fecha_ultimo_calculo"),
                        }
                elif tipo_ref == "RECETA":
                    receta = self._buscar_receta(referencia)
                    if not receta:
                        inc_linea.append({"tipo": INC_PLATO_INEXISTENTE, "detalle": f"Receta inexistente: {referencia}"})
                    else:
                        if str(receta.get("estado") or "") == "ARCHIVADA":
                            inc_linea.append({"tipo": INC_PLATO_ARCHIVADO, "detalle": f"Receta archivada: {receta.get('nombre')}"})
                        esc = None
                        rid = str(receta.get("id") or "")
                        rcod = str(receta.get("codigo") or "")
                        for candidato in self.repo_esc.listar(incluir_archivados=True):
                            ra = candidato.get("receta_asociada") or {}
                            if rid and str(ra.get("id") or "") == rid:
                                esc = candidato
                                break
                            if rcod and str(ra.get("codigo") or "") == rcod:
                                esc = candidato
                                break
                        if not esc:
                            inc_linea.append({"tipo": INC_ESCANDALLO_INEXISTENTE, "detalle": f"Receta sin escandallo asociado: {receta.get('nombre')}"})
                        else:
                            if str(esc.get("estado") or "") == ESTADO_DESACTUALIZADO:
                                inc_linea.append({"tipo": INC_ESCANDALLO_DESACTUALIZADO, "detalle": f"Escandallo desactualizado para receta: {receta.get('nombre')}"})
                            coste_por_comensal = self._to_float(esc.get("coste_por_racion")) * cantidad
                            snapshot_ref = {
                                "tipo": "ESCANDALLO",
                                "id": esc.get("id"),
                                "codigo": esc.get("codigo"),
                                "nombre": esc.get("nombre"),
                                "estado": esc.get("estado"),
                                "calculo_version": esc.get("calculo_version"),
                                "fecha_ultimo_calculo": esc.get("fecha_ultimo_calculo"),
                                "receta": {"id": receta.get("id"), "codigo": receta.get("codigo"), "nombre": receta.get("nombre")},
                            }
                elif tipo_ref == "PRODUCTO":
                    producto = self._buscar_producto(referencia)
                    if not producto:
                        inc_linea.append({"tipo": INC_PLATO_INEXISTENTE, "detalle": f"Producto inexistente: {referencia}"})
                    else:
                        precio = self._to_float(producto.get("precio"))
                        if precio <= 0:
                            inc_linea.append({"tipo": INC_PRODUCTO_SIN_PRECIO, "detalle": f"Producto sin precio: {producto.get('nombre')}"})
                        coste_por_comensal = precio * cantidad
                        snapshot_ref = {
                            "tipo": "PRODUCTO",
                            "codigo": producto.get("codigo"),
                            "nombre": producto.get("nombre"),
                            "estado": producto.get("estado"),
                            "precio": producto.get("precio"),
                            "fecha_precio": producto.get("fecha_precio"),
                        }
                else:
                    inc_linea.append({"tipo": INC_PLATO_INEXISTENTE, "detalle": f"Tipo de referencia no soportado: {tipo_ref}"})

                if inc_linea:
                    estado_linea = ESTADO_CON_INCIDENCIAS
                    incidencias.extend(inc_linea)

                lineas.append(
                    {
                        "seccion": str(seccion or "").strip(),
                        "tipo_referencia": tipo_ref,
                        "referencia": referencia,
                        "cantidad": cantidad,
                        "coste_por_comensal": round(coste_por_comensal, 6),
                        "coste_total": round(coste_por_comensal * comensales, 6),
                        "estado_linea": estado_linea,
                        "incidencias": inc_linea,
                        "snapshot_referencia": snapshot_ref,
                    }
                )

        coste_comensal = round(sum(float(x.get("coste_por_comensal") or 0.0) for x in lineas), 6)
        coste_total = round(coste_comensal * comensales, 6)
        venta_total = self._to_float(precio_venta_total)
        if venta_total <= 0 and self._to_float(precio_venta_comensal) > 0:
            venta_total = self._to_float(precio_venta_comensal) * comensales
        venta_comensal = round((venta_total / comensales), 6) if comensales > 0 else self._to_float(precio_venta_comensal)

        margen_total = round(venta_total - coste_total, 6) if venta_total > 0 else 0.0
        margen_pct = round((margen_total / venta_total) * 100.0, 6) if venta_total > 0 else 0.0
        rentabilidad = "NEGATIVA" if margen_total < 0 else ("BAJA" if margen_pct < 20 else ("MEDIA" if margen_pct < 40 else "ALTA"))

        estado = ESTADO_OPERATIVO if not incidencias else ESTADO_CON_INCIDENCIAS

        return {
            "nombre": nombre_menu,
            "comensales_recomendado": comensales,
            "lineas": lineas,
            "coste_por_comensal": coste_comensal,
            "coste_total": coste_total,
            "precio_venta_comensal": venta_comensal,
            "precio_venta_total": round(venta_total, 6),
            "margen_total": margen_total,
            "margen_porcentual": margen_pct,
            "rentabilidad": rentabilidad,
            "estado_calculo": estado,
            "incidencias": incidencias,
            "fecha_calculo": self._now(),
        }

    def detectar_desactualizado(self, menu: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
        cambios: list[dict[str, Any]] = []
        for linea in list(menu.get("lineas") or []):
            snap = dict(linea.get("snapshot_referencia") or {})
            if str(snap.get("tipo") or "") != "ESCANDALLO":
                continue
            ref = str(snap.get("id") or snap.get("codigo") or "")
            actual = self._buscar_escandallo(ref)
            if not actual:
                cambios.append({
                    "tipo": INC_ESCANDALLO_INEXISTENTE,
                    "detalle": f"Escandallo eliminado: {snap.get('nombre')}",
                    "referencia": ref,
                })
                continue
            if int(actual.get("calculo_version") or 0) != int(snap.get("calculo_version") or -1):
                cambios.append({
                    "tipo": INC_ESCANDALLO_DESACTUALIZADO,
                    "detalle": f"Escandallo con nueva versión: {actual.get('nombre')}",
                    "referencia": ref,
                    "version_anterior": snap.get("calculo_version"),
                    "version_actual": actual.get("calculo_version"),
                })
            if str(actual.get("estado") or "") == ESTADO_DESACTUALIZADO:
                cambios.append({
                    "tipo": INC_ESCANDALLO_DESACTUALIZADO,
                    "detalle": f"Escandallo marcado desactualizado: {actual.get('nombre')}",
                    "referencia": ref,
                })
            if str(actual.get("estado") or "") == ESTADO_ARCHIVADO:
                cambios.append({
                    "tipo": INC_PLATO_ARCHIVADO,
                    "detalle": f"Escandallo archivado: {actual.get('nombre')}",
                    "referencia": ref,
                })
        return (len(cambios) > 0, cambios)


__all__ = [
    "MotorCalculoMenus601",
    "ESTADO_BORRADOR",
    "ESTADO_OPERATIVO",
    "ESTADO_CON_INCIDENCIAS",
    "ESTADO_DESACTUALIZADO",
    "ESTADO_ARCHIVADO",
    "INC_PLATO_INEXISTENTE",
    "INC_ESCANDALLO_INEXISTENTE",
    "INC_ESCANDALLO_DESACTUALIZADO",
    "INC_PRODUCTO_SIN_PRECIO",
    "INC_PLATO_ARCHIVADO",
    "INC_DUPLICADO",
]
