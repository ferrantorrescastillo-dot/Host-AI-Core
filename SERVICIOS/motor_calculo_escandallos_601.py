from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any

from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


ESTADO_BORRADOR = "BORRADOR"
ESTADO_OPERATIVO = "OPERATIVO"
ESTADO_PENDIENTE_PRECIOS = "PENDIENTE_DE_PRECIOS"
ESTADO_PENDIENTE_UNIDADES = "PENDIENTE_DE_UNIDADES"
ESTADO_CON_INCIDENCIAS = "CON_INCIDENCIAS"
ESTADO_DESACTUALIZADO = "DESACTUALIZADO"
ESTADO_ARCHIVADO = "ARCHIVADO"


INC_PRODUCTO_INEXISTENTE = "PRODUCTO_INEXISTENTE"
INC_PRODUCTO_ARCHIVADO = "PRODUCTO_ARCHIVADO"
INC_PRODUCTO_SIN_PRECIO = "PRODUCTO_SIN_PRECIO"
INC_PRECIO_PROVISIONAL = "PRECIO_PROVISIONAL"
INC_PRECIO_SIN_PROVEEDOR = "PRECIO_SIN_PROVEEDOR"
INC_PRECIO_SIN_FECHA = "PRECIO_SIN_FECHA"
INC_IVA_DESCONOCIDO = "IVA_DESCONOCIDO"
INC_UNIDAD_INCOMPATIBLE = "UNIDAD_INCOMPATIBLE"
INC_CONVERSION_INEXISTENTE = "CONVERSION_INEXISTENTE"
INC_MERMA_INVALIDA = "MERMA_INVALIDA"
INC_CANTIDAD_INEXISTENTE = "CANTIDAD_INEXISTENTE"
INC_INGREDIENTE_AL_GUSTO = "INGREDIENTE_AL_GUSTO"
INC_RECETA_SIN_RACIONES = "RECETA_SIN_RACIONES"
INC_COMPONENTE_SIN_ESCANDALLO = "COMPONENTE_SIN_ESCANDALLO"
INC_PRECIO_VENTA_CERO = "PRECIO_VENTA_IGUAL_A_CERO"
INC_MARGEN_NEGATIVO = "MARGEN_NEGATIVO"


_UNIDADES_ALIAS = {
    "unidad": "u",
    "unidades": "u",
    "ud": "u",
    "uds": "u",
    "pieza": "u",
    "piezas": "u",
    "kg": "kg",
    "kilo": "kg",
    "kilos": "kg",
    "g": "g",
    "gr": "g",
    "gramo": "g",
    "gramos": "g",
    "l": "l",
    "lt": "l",
    "litro": "l",
    "litros": "l",
    "ml": "ml",
    "mili": "ml",
    "mililitros": "ml",
    "pax": "u",
    "racion": "u",
    "raciones": "u",
}


@dataclass
class PrecioSeleccionado601:
    precio_neto_unidad_base: float
    unidad_base: str
    proveedor: str
    fecha: str
    provisional: bool
    iva: float | None
    precio_incluye_iva: bool
    referencia: dict[str, Any]


class MotorCalculoEscandallos601:
    """Motor centralizado de cálculo económico para escandallos 6.0.1."""

    def __init__(self, repo_productos: RepositorioProductosMaestro601):
        self.repo_productos = repo_productos

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def _norm(txt: Any) -> str:
        return " ".join(str(txt or "").strip().lower().split())

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value in (None, ""):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        txt = str(value).strip().replace("€", "")
        txt = txt.replace(" ", "")
        if "," in txt and "." in txt:
            txt = txt.replace(".", "").replace(",", ".")
        else:
            txt = txt.replace(",", ".")
        try:
            return float(txt)
        except ValueError:
            return None

    @classmethod
    def _unidad_canonica(cls, unidad: Any) -> str:
        u = cls._norm(unidad)
        return _UNIDADES_ALIAS.get(u, u)

    def _parse_cantidad_unidad(self, texto: Any) -> tuple[float | None, str]:
        if isinstance(texto, (int, float)):
            return float(texto), ""
        raw = str(texto or "").strip()
        if not raw:
            return None, ""
        if self._norm(raw) in {"al gusto", "c/s", "cs", "a gusto"}:
            return None, "al gusto"
        m = re.search(r"(-?\d+(?:[\.,]\d+)?)\s*([a-zA-ZáéíóúÁÉÍÓÚ/]+)?", raw)
        if not m:
            return None, ""
        cantidad = self._to_float(m.group(1))
        unidad = self._unidad_canonica(m.group(2) or "")
        return cantidad, unidad

    def _convertir_unidades(self, cantidad: float, unidad_origen: str, unidad_destino: str) -> float | None:
        uo = self._unidad_canonica(unidad_origen)
        ud = self._unidad_canonica(unidad_destino)
        if not uo or not ud:
            return None
        if uo == ud:
            return float(cantidad)

        # masa
        if uo == "kg" and ud == "g":
            return float(cantidad) * 1000.0
        if uo == "g" and ud == "kg":
            return float(cantidad) / 1000.0

        # volumen
        if uo == "l" and ud == "ml":
            return float(cantidad) * 1000.0
        if uo == "ml" and ud == "l":
            return float(cantidad) / 1000.0

        # unidades discretas
        if uo == "u" and ud == "u":
            return float(cantidad)

        return None

    def _merma_pct(self, producto: dict[str, Any], merma_especifica: Any) -> float | None:
        if merma_especifica not in (None, ""):
            m = self._to_float(merma_especifica)
            return m
        raw = str(producto.get("merma_habitual") or "").strip().replace("%", "")
        if not raw:
            return 0.0
        return self._to_float(raw)

    def _aplicar_iva(self, precio: float, incluye_iva: bool, iva: float | None) -> float | None:
        if not incluye_iva:
            return precio
        if iva is None:
            return None
        if iva < 0:
            return None
        return precio / (1.0 + (iva / 100.0))

    def _precio_desde_producto_base(self, producto: dict[str, Any]) -> tuple[float | None, str, list[dict[str, Any]]]:
        incidencias: list[dict[str, Any]] = []
        precio = self._to_float(producto.get("precio"))
        if precio is None or precio <= 0:
            return None, "", incidencias

        unidad_base = self._unidad_canonica(producto.get("unidad_base") or producto.get("unidad"))
        unidad_compra = self._unidad_canonica(producto.get("unidad_compra") or unidad_base)
        cantidad_formato = self._to_float(producto.get("cantidad_formato"))

        if not unidad_base:
            return None, "", [{"tipo": INC_UNIDAD_INCOMPATIBLE, "detalle": "Producto sin unidad base."}]

        # Si viene precio por formato (caja/bolsa/bandeja/botella), lo convertimos a unidad base.
        if unidad_compra not in {"", unidad_base} and cantidad_formato and cantidad_formato > 0:
            precio_unidad_base = precio / cantidad_formato
            return precio_unidad_base, unidad_base, incidencias

        return precio, unidad_base, incidencias

    def _seleccionar_precio(self, producto: dict[str, Any], proveedor_forzado: str = "") -> tuple[PrecioSeleccionado601 | None, list[dict[str, Any]]]:
        incidencias: list[dict[str, Any]] = []
        codigo = str(producto.get("codigo") or "")
        historial = self.repo_productos.obtener_proveedores_y_precios(codigo)
        asociaciones = list(historial.get("asociaciones") or [])
        registros = list(historial.get("historico_precios") or [])

        proveedor_pref = self._norm(proveedor_forzado or producto.get("proveedor_preferente") or producto.get("proveedor"))
        candidatos: list[tuple[int, float, dict[str, Any]]] = []

        for a in asociaciones:
            precio_habitual = self._to_float(a.get("precio_habitual"))
            if not precio_habitual or precio_habitual <= 0:
                continue
            prov = self._norm(a.get("proveedor_nombre"))
            score = 10
            if bool(a.get("preferente")):
                score = 1
            if proveedor_pref and prov == proveedor_pref:
                score = 0
            candidatos.append((score, precio_habitual, {
                "fuente": "asociacion",
                "proveedor": str(a.get("proveedor_nombre") or ""),
                "fecha": str(a.get("ultima_actualizacion_precio") or ""),
                "unidad": str(a.get("unidad_precio") or producto.get("unidad_base") or producto.get("unidad") or ""),
                "provisional": False,
                "iva": self._to_float(producto.get("iva")),
                "precio_incluye_iva": bool(producto.get("precio_incluye_iva", False)),
            }))

        for r in registros:
            p = self._to_float(r.get("precio"))
            if not p or p <= 0:
                continue
            prov = self._norm(r.get("proveedor_nombre") or r.get("proveedor_id"))
            score = 3
            if proveedor_pref and prov == proveedor_pref:
                score = 2
            fecha = str(r.get("fecha_factura") or r.get("creado_en") or r.get("fecha_registro") or "")
            candidatos.append((score, p, {
                "fuente": "historico",
                "proveedor": str(r.get("proveedor_nombre") or r.get("proveedor_id") or ""),
                "fecha": fecha,
                "unidad": str(r.get("unidad") or producto.get("unidad_base") or producto.get("unidad") or ""),
                "provisional": bool(r.get("provisional", False)),
                "iva": self._to_float(r.get("iva")) if r.get("iva") not in (None, "") else self._to_float(producto.get("iva")),
                "precio_incluye_iva": bool(r.get("precio_incluye_iva", False)),
            }))

        p_producto, u_producto, inc_producto = self._precio_desde_producto_base(producto)
        incidencias.extend(inc_producto)
        if p_producto and p_producto > 0:
            candidatos.append((4, p_producto, {
                "fuente": "catalogo_producto",
                "proveedor": str(producto.get("proveedor_preferente") or producto.get("proveedor") or ""),
                "fecha": str(producto.get("fecha_precio") or ""),
                "unidad": u_producto,
                "provisional": False,
                "iva": self._to_float(producto.get("iva")),
                "precio_incluye_iva": bool(producto.get("precio_incluye_iva", False)),
            }))

        if not candidatos:
            incidencias.append({"tipo": INC_PRODUCTO_SIN_PRECIO, "detalle": f"Producto sin precio utilizable: {producto.get('nombre')}"})
            return None, incidencias

        candidatos.sort(key=lambda x: x[0])
        _, precio_raw, meta = candidatos[0]

        iva = meta.get("iva")
        precio_neto = self._aplicar_iva(precio_raw, bool(meta.get("precio_incluye_iva", False)), iva)
        if precio_neto is None:
            incidencias.append({"tipo": INC_IVA_DESCONOCIDO, "detalle": f"No se pudo convertir IVA para {producto.get('nombre')}"})
            precio_neto = precio_raw

        if not str(meta.get("proveedor") or "").strip():
            incidencias.append({"tipo": INC_PRECIO_SIN_PROVEEDOR, "detalle": f"Precio sin proveedor para {producto.get('nombre')}"})
        if not str(meta.get("fecha") or "").strip():
            incidencias.append({"tipo": INC_PRECIO_SIN_FECHA, "detalle": f"Precio sin fecha para {producto.get('nombre')}"})
        if bool(meta.get("provisional", False)):
            incidencias.append({"tipo": INC_PRECIO_PROVISIONAL, "detalle": f"Precio provisional usado en {producto.get('nombre')}"})

        unidad_base = self._unidad_canonica(meta.get("unidad") or producto.get("unidad_base") or producto.get("unidad"))
        precio_sel = PrecioSeleccionado601(
            precio_neto_unidad_base=float(precio_neto),
            unidad_base=unidad_base,
            proveedor=str(meta.get("proveedor") or ""),
            fecha=str(meta.get("fecha") or ""),
            provisional=bool(meta.get("provisional", False)),
            iva=iva,
            precio_incluye_iva=bool(meta.get("precio_incluye_iva", False)),
            referencia=meta,
        )
        return precio_sel, incidencias

    def calcular(
        self,
        *,
        nombre_escandallo: str,
        numero_raciones: float,
        lineas_entrada: list[dict[str, Any]],
        precio_venta_total: float = 0.0,
        precio_venta_por_racion: float = 0.0,
        venta_incluye_iva: bool = False,
        iva_venta: float | None = None,
        receta_asociada: dict[str, Any] | None = None,
        precios_fijados: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        incidencias: list[dict[str, Any]] = []
        lineas_salida: list[dict[str, Any]] = []
        precios_referencia: list[dict[str, Any]] = []

        if numero_raciones <= 0:
            incidencias.append({"tipo": INC_RECETA_SIN_RACIONES, "detalle": "Número de raciones no válido."})

        for entrada in lineas_entrada:
            linea_inc: list[dict[str, Any]] = []
            nombre_linea = str(entrada.get("nombre_mostrado") or entrada.get("producto") or entrada.get("ingrediente") or "").strip()
            codigo = str(entrada.get("producto_codigo") or "").strip()

            cantidad_neta = self._to_float(entrada.get("cantidad_neta"))
            unidad_receta = self._unidad_canonica(entrada.get("unidad_receta"))
            if cantidad_neta is None:
                cantidad_neta, unidad_parseada = self._parse_cantidad_unidad(entrada.get("cantidad_texto") or entrada.get("cantidad") or "")
                if not unidad_receta:
                    unidad_receta = unidad_parseada

            if cantidad_neta is None:
                if self._norm(entrada.get("cantidad_texto") or entrada.get("cantidad")) in {"al gusto", "c/s", "cs", "a gusto"}:
                    linea_inc.append({"tipo": INC_INGREDIENTE_AL_GUSTO, "detalle": f"Ingrediente al gusto: {nombre_linea}"})
                else:
                    linea_inc.append({"tipo": INC_CANTIDAD_INEXISTENTE, "detalle": f"Cantidad no válida: {nombre_linea}"})
                cantidad_neta = 0.0

            # Resolver producto real desde catálogo.
            producto = None
            if codigo:
                producto = self.repo_productos.obtener_producto(codigo)
            if producto is None and nombre_linea:
                encontrados = self.repo_productos.buscar_productos({"nombre": nombre_linea})
                if encontrados:
                    producto = encontrados[0]

            if producto is None:
                linea_inc.append({"tipo": INC_PRODUCTO_INEXISTENTE, "detalle": f"Producto no encontrado: {nombre_linea}"})
                lineas_salida.append({
                    "producto_codigo": codigo,
                    "nombre_mostrado": nombre_linea,
                    "cantidad_neta": cantidad_neta,
                    "unidad_receta": unidad_receta,
                    "merma_pct": 0.0,
                    "cantidad_bruta": 0.0,
                    "unidad_base_calculo": "",
                    "factor_conversion": None,
                    "precio_compra_utilizado": None,
                    "unidad_precio": "",
                    "proveedor_precio": "",
                    "fecha_precio": "",
                    "coste_linea": 0.0,
                    "estado_linea": "CON_INCIDENCIAS",
                    "observaciones": str(entrada.get("observaciones") or ""),
                    "precio_provisional": False,
                    "dato_manual": bool(entrada.get("dato_manual", False)),
                    "incidencias": linea_inc,
                })
                incidencias.extend(linea_inc)
                continue

            if str(producto.get("estado") or "") == ESTADO_ARCHIVADO:
                linea_inc.append({"tipo": INC_PRODUCTO_ARCHIVADO, "detalle": f"Producto archivado: {producto.get('nombre')}"})

            merma_pct = self._merma_pct(producto, entrada.get("merma_especifica"))
            if merma_pct is None or merma_pct < 0 or merma_pct >= 100:
                linea_inc.append({"tipo": INC_MERMA_INVALIDA, "detalle": f"Merma inválida en {producto.get('nombre')}"})
                merma_pct = 0.0

            divisor = (1.0 - (float(merma_pct) / 100.0))
            cantidad_bruta = (float(cantidad_neta) / divisor) if divisor > 0 else 0.0

            precio_fijado = None
            if precios_fijados and str(producto.get("codigo") or "") in precios_fijados:
                precio_fijado = precios_fijados[str(producto.get("codigo") or "")]

            if precio_fijado:
                precio_sel = PrecioSeleccionado601(
                    precio_neto_unidad_base=float(precio_fijado.get("precio_neto_unidad_base") or 0.0),
                    unidad_base=self._unidad_canonica(precio_fijado.get("unidad_base") or producto.get("unidad_base") or producto.get("unidad")),
                    proveedor=str(precio_fijado.get("proveedor") or ""),
                    fecha=str(precio_fijado.get("fecha") or ""),
                    provisional=bool(precio_fijado.get("provisional", False)),
                    iva=self._to_float(precio_fijado.get("iva")),
                    precio_incluye_iva=bool(precio_fijado.get("precio_incluye_iva", False)),
                    referencia=dict(precio_fijado),
                )
                precio_inc: list[dict[str, Any]] = []
            else:
                precio_sel, precio_inc = self._seleccionar_precio(producto, str(entrada.get("proveedor_forzado") or ""))
            linea_inc.extend(precio_inc)

            unidad_base = self._unidad_canonica((precio_sel.unidad_base if precio_sel else "") or producto.get("unidad_base") or producto.get("unidad"))
            cantidad_en_base = None
            factor = None
            if unidad_receta and unidad_base and cantidad_bruta > 0:
                cantidad_en_base = self._convertir_unidades(cantidad_bruta, unidad_receta, unidad_base)
                if cantidad_en_base is not None:
                    factor = cantidad_en_base / cantidad_bruta if cantidad_bruta else 1.0

            if cantidad_en_base is None and cantidad_bruta > 0:
                linea_inc.append({"tipo": INC_CONVERSION_INEXISTENTE, "detalle": f"No hay conversión {unidad_receta} -> {unidad_base} para {producto.get('nombre')}"})
                linea_inc.append({"tipo": INC_UNIDAD_INCOMPATIBLE, "detalle": f"Unidad incompatible en {producto.get('nombre')}"})
                cantidad_en_base = 0.0

            precio_utilizado = float(precio_sel.precio_neto_unidad_base) if precio_sel else 0.0
            coste_linea = float(cantidad_en_base) * precio_utilizado

            estado_linea = "OPERATIVA" if not linea_inc else "CON_INCIDENCIAS"
            if any(i.get("tipo") == INC_PRODUCTO_SIN_PRECIO for i in linea_inc):
                estado_linea = "PENDIENTE_DE_PRECIOS"
            if any(i.get("tipo") in {INC_CONVERSION_INEXISTENTE, INC_UNIDAD_INCOMPATIBLE} for i in linea_inc):
                estado_linea = "PENDIENTE_DE_UNIDADES"

            linea_out = {
                "producto_codigo": str(producto.get("codigo") or ""),
                "producto_ref": str(producto.get("codigo") or ""),
                "nombre_mostrado": str(nombre_linea or producto.get("nombre") or ""),
                "cantidad_neta": round(float(cantidad_neta or 0.0), 6),
                "unidad_receta": unidad_receta,
                "merma_pct": round(float(merma_pct or 0.0), 4),
                "tipo_merma": "porcentual",
                "cantidad_bruta": round(float(cantidad_bruta or 0.0), 6),
                "unidad_base_calculo": unidad_base,
                "factor_conversion": round(float(factor), 8) if factor is not None else None,
                "precio_compra_utilizado": round(precio_utilizado, 6) if precio_sel else None,
                "unidad_precio": unidad_base,
                "proveedor_precio": str(precio_sel.proveedor) if precio_sel else "",
                "fecha_precio": str(precio_sel.fecha) if precio_sel else "",
                "coste_linea": round(coste_linea, 6),
                "estado_linea": estado_linea,
                "observaciones": str(entrada.get("observaciones") or ""),
                "precio_provisional": bool(precio_sel.provisional) if precio_sel else False,
                "dato_manual": bool(entrada.get("dato_manual", False)),
                "incidencias": linea_inc,
                "precio_referencia": dict(precio_sel.referencia) if precio_sel else {},
            }
            lineas_salida.append(linea_out)
            incidencias.extend(linea_inc)

            if precio_sel:
                precios_referencia.append({
                    "producto_codigo": str(producto.get("codigo") or ""),
                    "producto": str(producto.get("nombre") or ""),
                    "precio_neto_unidad_base": round(precio_sel.precio_neto_unidad_base, 6),
                    "unidad_base": unidad_base,
                    "proveedor": precio_sel.proveedor,
                    "fecha": precio_sel.fecha,
                    "provisional": precio_sel.provisional,
                    "iva": precio_sel.iva,
                    "precio_incluye_iva": precio_sel.precio_incluye_iva,
                    "referencia": precio_sel.referencia,
                })

        coste_total = round(sum(float(l.get("coste_linea") or 0.0) for l in lineas_salida), 6)
        raciones = float(numero_raciones or 0)
        coste_por_racion = round(coste_total / raciones, 6) if raciones > 0 else 0.0

        venta_total = float(precio_venta_total or 0.0)
        if venta_total <= 0 and float(precio_venta_por_racion or 0.0) > 0 and raciones > 0:
            venta_total = float(precio_venta_por_racion) * raciones

        if venta_total <= 0:
            incidencias.append({"tipo": INC_PRECIO_VENTA_CERO, "detalle": "Precio de venta igual a cero."})

        venta_neta = venta_total
        iva_v = self._to_float(iva_venta) if iva_venta is not None else None
        if venta_incluye_iva and venta_total > 0:
            if iva_v is None:
                incidencias.append({"tipo": INC_IVA_DESCONOCIDO, "detalle": "IVA de venta desconocido para precio con IVA."})
            else:
                venta_neta = venta_total / (1.0 + (iva_v / 100.0))

        beneficio_total = round(venta_neta - coste_total, 6) if venta_neta > 0 else 0.0
        beneficio_por_racion = round(beneficio_total / raciones, 6) if raciones > 0 else 0.0
        margen_monetario = beneficio_total
        margen_pct = round((beneficio_total / venta_neta) * 100.0, 6) if venta_neta > 0 else 0.0
        coste_sobre_venta_pct = round((coste_total / venta_neta) * 100.0, 6) if venta_neta > 0 else 0.0

        if beneficio_total < 0:
            incidencias.append({"tipo": INC_MARGEN_NEGATIVO, "detalle": "Margen negativo."})

        estado = ESTADO_OPERATIVO
        if any(i.get("tipo") in {INC_CONVERSION_INEXISTENTE, INC_UNIDAD_INCOMPATIBLE, INC_MERMA_INVALIDA} for i in incidencias):
            estado = ESTADO_PENDIENTE_UNIDADES
        elif any(i.get("tipo") in {INC_PRODUCTO_SIN_PRECIO, INC_PRECIO_SIN_PROVEEDOR, INC_PRECIO_SIN_FECHA, INC_IVA_DESCONOCIDO} for i in incidencias):
            estado = ESTADO_PENDIENTE_PRECIOS
        elif incidencias:
            estado = ESTADO_CON_INCIDENCIAS

        if not lineas_salida:
            estado = ESTADO_BORRADOR

        return {
            "nombre": nombre_escandallo,
            "receta_asociada": receta_asociada or {},
            "numero_raciones": raciones,
            "lineas": lineas_salida,
            "coste_total": coste_total,
            "coste_por_racion": coste_por_racion,
            "precio_venta_total": round(venta_total, 6),
            "precio_venta_por_racion": round((venta_total / raciones), 6) if raciones > 0 else float(precio_venta_por_racion or 0.0),
            "beneficio_total": beneficio_total,
            "beneficio_por_racion": beneficio_por_racion,
            "margen_monetario": margen_monetario,
            "margen_porcentual": margen_pct,
            "coste_sobre_venta_porcentual": coste_sobre_venta_pct,
            "incidencias": incidencias,
            "estado": estado,
            "referencia_precios": precios_referencia,
            "fecha_calculo": self._now(),
        }

    def detectar_desactualizado(self, escandallo: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
        cambios: list[dict[str, Any]] = []
        for linea in list(escandallo.get("lineas") or []):
            codigo = str(linea.get("producto_codigo") or "")
            if not codigo:
                continue
            prod = self.repo_productos.obtener_producto(codigo)
            if not prod:
                continue
            actual = self._to_float(prod.get("precio"))
            usado = self._to_float(linea.get("precio_compra_utilizado"))
            if actual and usado and abs(actual - usado) > 1e-9:
                cambios.append({
                    "producto_codigo": codigo,
                    "producto": str(prod.get("nombre") or linea.get("nombre_mostrado") or ""),
                    "precio_usado": usado,
                    "precio_actual": actual,
                    "tipo": "CAMBIO_PRECIO",
                })
        return (len(cambios) > 0, cambios)


__all__ = [
    "MotorCalculoEscandallos601",
    "ESTADO_BORRADOR",
    "ESTADO_OPERATIVO",
    "ESTADO_PENDIENTE_PRECIOS",
    "ESTADO_PENDIENTE_UNIDADES",
    "ESTADO_CON_INCIDENCIAS",
    "ESTADO_DESACTUALIZADO",
    "ESTADO_ARCHIVADO",
]
