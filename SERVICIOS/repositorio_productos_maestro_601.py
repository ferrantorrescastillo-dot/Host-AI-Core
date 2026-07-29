from __future__ import annotations

import json
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any


ESTADO_ACTIVO = "ACTIVO"
ESTADO_PENDIENTE = "PENDIENTE_DE_COMPLETAR"
ESTADO_ARCHIVADO = "ARCHIVADO"


class RepositorioProductosMaestro601:
    """Repositorio maestro reutilizando la fuente real del proyecto.

    Fuente principal:
    - DATOS/db/articulos.json
    Fuentes complementarias:
    - DATOS/db/proveedores.json
    - DATOS/db/compras_producto_proveedor.json
    - DATOS/facturas/historico_precios.json
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.path_articulos = self.base_dir / "DATOS" / "db" / "articulos.json"
        self.path_proveedores = self.base_dir / "DATOS" / "db" / "proveedores.json"
        self.path_producto_proveedor = self.base_dir / "DATOS" / "db" / "compras_producto_proveedor.json"
        self.path_historico_precios = self.base_dir / "DATOS" / "facturas" / "historico_precios.json"

        self.path_articulos.parent.mkdir(parents=True, exist_ok=True)
        self.path_proveedores.parent.mkdir(parents=True, exist_ok=True)
        self.path_producto_proveedor.parent.mkdir(parents=True, exist_ok=True)
        self.path_historico_precios.parent.mkdir(parents=True, exist_ok=True)

        if not self.path_articulos.exists():
            self._guardar_lista(self.path_articulos, [])
        if not self.path_proveedores.exists():
            self._guardar_lista(self.path_proveedores, [])
        if not self.path_producto_proveedor.exists():
            self._guardar_lista(self.path_producto_proveedor, [])
        if not self.path_historico_precios.exists():
            self._guardar_json(self.path_historico_precios, {"version": "3.0.3.5.3", "registros": []})

    @staticmethod
    def _norm(texto: Any) -> str:
        t = str(texto or "").strip().lower()
        t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
        return " ".join(t.split())

    @staticmethod
    def _slug(texto: Any) -> str:
        t = RepositorioProductosMaestro601._norm(texto).upper().replace(" ", "-")
        out = []
        for ch in t:
            if "A" <= ch <= "Z" or "0" <= ch <= "9" or ch == "-":
                out.append(ch)
        s = "".join(out).strip("-")
        return s or "SIN-NOMBRE"

    def _leer_json(self, path: Path, default: Any) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return default

    def _guardar_json(self, path: Path, data: Any) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, suffix=".tmp") as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2)
            tmp.flush()
            tmp_path = Path(tmp.name)
        tmp_path.replace(path)

    def _leer_lista(self, path: Path) -> list[dict[str, Any]]:
        data = self._leer_json(path, [])
        return data if isinstance(data, list) else []

    def _guardar_lista(self, path: Path, data: list[dict[str, Any]]) -> None:
        self._guardar_json(path, data)

    def _siguiente_codigo_articulo(self, articulos: list[dict[str, Any]]) -> str:
        max_num = 0
        for art in articulos:
            cod = str(art.get("codigo") or "")
            if cod.startswith("ART") and cod[3:].isdigit():
                max_num = max(max_num, int(cod[3:]))
        return f"ART{max_num + 1:06d}"

    def _siguiente_codigo_proveedor(self, proveedores: list[dict[str, Any]]) -> str:
        max_num = 0
        for p in proveedores:
            cod = str(p.get("codigo") or "")
            if cod.startswith("PROV") and cod[4:].isdigit():
                max_num = max(max_num, int(cod[4:]))
        return f"PROV{max_num + 1:04d}"

    def _estado_producto(self, art: dict[str, Any], forzar_archivado: bool = False) -> str:
        if forzar_archivado or art.get("activo") is False:
            return ESTADO_ARCHIVADO
        nombre = str(art.get("nombre") or "").strip()
        precio = art.get("precio")
        unidad = str(art.get("unidad") or "").strip()
        if not nombre:
            return ESTADO_PENDIENTE
        if precio in (None, "", 0, 0.0) or not unidad:
            return ESTADO_PENDIENTE
        return ESTADO_ACTIVO

    def _enriquecer(self, art: dict[str, Any]) -> dict[str, Any]:
        out = dict(art)
        out.setdefault("codigo", "")
        out.setdefault("nombre", "")
        out.setdefault("familia", "")
        out.setdefault("proveedor", "")
        out.setdefault("precio", None)
        out.setdefault("activo", True)

        meta = dict(out.get("catalogo_maestro") or {})
        out["catalogo_maestro"] = meta

        out["id_interno"] = out.get("codigo") or out.get("id") or self._slug(out.get("nombre"))
        out["nombre_normalizado"] = self._norm(out.get("nombre"))
        out["subfamilia"] = str(meta.get("subfamilia") or "")
        out["marca"] = str(meta.get("marca") or "")
        out["referencia_proveedor"] = str(meta.get("referencia_proveedor") or "")
        out["unidad_compra"] = str(meta.get("unidad_compra") or out.get("unidad") or "")
        out["cantidad_formato"] = str(meta.get("cantidad_formato") or "")
        out["unidad_base"] = str(meta.get("unidad_base") or out.get("unidad") or "")
        out["unidad_recetas"] = str(meta.get("unidad_recetas") or out.get("unidad") or "")
        out["conversion_unidades"] = str(meta.get("conversion_unidades") or "")
        out["iva"] = str(meta.get("iva") or "")
        out["precio_incluye_iva"] = bool(meta.get("precio_incluye_iva", False))
        out["fecha_precio"] = str(meta.get("fecha_precio") or "")
        out["proveedor_preferente"] = str(meta.get("proveedor_preferente") or out.get("proveedor") or "")
        out["merma_habitual"] = str(meta.get("merma_habitual") or "")
        out["alergenos"] = list(meta.get("alergenos") or [])
        out["conservacion"] = str(meta.get("conservacion") or "")
        out["stock_minimo"] = meta.get("stock_minimo")
        out["observaciones_ext"] = str(meta.get("observaciones_ext") or out.get("observaciones") or "")
        out["estado"] = self._estado_producto(out)
        out["fecha_creacion"] = str(out.get("fecha_importacion") or meta.get("fecha_creacion") or "")
        out["fecha_modificacion"] = str(meta.get("fecha_modificacion") or out.get("fecha_importacion") or "")
        return out

    def listar_productos(self, incluir_archivados: bool = True) -> list[dict[str, Any]]:
        articulos = [self._enriquecer(a) for a in self._leer_lista(self.path_articulos)]
        if incluir_archivados:
            return articulos
        return [a for a in articulos if a.get("estado") != ESTADO_ARCHIVADO]

    def buscar_productos(self, filtros: dict[str, str]) -> list[dict[str, Any]]:
        productos = self.listar_productos(incluir_archivados=True)
        nombre = self._norm(filtros.get("nombre", ""))
        codigo = self._norm(filtros.get("codigo", ""))
        familia = self._norm(filtros.get("familia", ""))
        subfamilia = self._norm(filtros.get("subfamilia", ""))
        marca = self._norm(filtros.get("marca", ""))
        proveedor = self._norm(filtros.get("proveedor", ""))
        referencia = self._norm(filtros.get("referencia", ""))
        estado = self._norm(filtros.get("estado", ""))

        out = []
        for p in productos:
            if nombre:
                n = self._norm(p.get("nombre"))
                if nombre not in n and n not in nombre:
                    continue
            if codigo and codigo not in self._norm(p.get("codigo")):
                continue
            if familia and familia not in self._norm(p.get("familia")):
                continue
            if subfamilia and subfamilia not in self._norm(p.get("subfamilia")):
                continue
            if marca and marca not in self._norm(p.get("marca")):
                continue
            if proveedor and proveedor not in self._norm(p.get("proveedor")) and proveedor not in self._norm(p.get("proveedor_preferente")):
                continue
            if referencia and referencia not in self._norm(p.get("referencia_proveedor")):
                continue
            if estado and estado != self._norm(p.get("estado")):
                continue
            out.append(p)
        return out

    def obtener_producto(self, codigo: str) -> dict[str, Any] | None:
        clave = self._norm(codigo)
        for art in self._leer_lista(self.path_articulos):
            if clave == self._norm(art.get("codigo")):
                return self._enriquecer(art)
        return None

    def crear_producto(self, datos: dict[str, Any]) -> dict[str, Any]:
        articulos = self._leer_lista(self.path_articulos)
        nombre = str(datos.get("nombre") or "").strip()
        if not nombre:
            raise ValueError("El nombre del producto es obligatorio.")

        codigo = str(datos.get("codigo") or "").strip() or self._siguiente_codigo_articulo(articulos)
        if any(self._norm(a.get("codigo")) == self._norm(codigo) for a in articulos):
            raise ValueError("Ya existe un producto con ese código.")

        now = datetime.now().isoformat(timespec="seconds")
        registro = {
            "codigo": codigo,
            "nombre": nombre,
            "observaciones": str(datos.get("observaciones") or "").strip() or None,
            "proveedor": str(datos.get("proveedor") or "").strip() or None,
            "familia": str(datos.get("familia") or "").strip() or None,
            "precio": self._to_float_or_none(datos.get("precio")),
            "unidad": str(datos.get("unidad_base") or datos.get("unidad") or "").strip() or None,
            "activo": True,
            "origen": "catalogo_maestro_601",
            "fecha_importacion": now,
            "catalogo_maestro": {
                "subfamilia": str(datos.get("subfamilia") or "").strip(),
                "marca": str(datos.get("marca") or "").strip(),
                "referencia_proveedor": str(datos.get("referencia_proveedor") or "").strip(),
                "unidad_compra": str(datos.get("unidad_compra") or "").strip(),
                "cantidad_formato": str(datos.get("cantidad_formato") or "").strip(),
                "unidad_base": str(datos.get("unidad_base") or "").strip(),
                "unidad_recetas": str(datos.get("unidad_recetas") or "").strip(),
                "conversion_unidades": str(datos.get("conversion_unidades") or "").strip(),
                "iva": str(datos.get("iva") or "").strip(),
                "precio_incluye_iva": bool(datos.get("precio_incluye_iva", False)),
                "fecha_precio": str(datos.get("fecha_precio") or "").strip(),
                "proveedor_preferente": str(datos.get("proveedor_preferente") or datos.get("proveedor") or "").strip(),
                "merma_habitual": str(datos.get("merma_habitual") or "").strip(),
                "alergenos": list(datos.get("alergenos") or []),
                "conservacion": str(datos.get("conservacion") or "").strip(),
                "stock_minimo": self._to_float_or_none(datos.get("stock_minimo")),
                "observaciones_ext": str(datos.get("observaciones") or "").strip(),
                "estado": "",
                "fecha_creacion": now,
                "fecha_modificacion": now,
            },
        }
        registro["catalogo_maestro"]["estado"] = self._estado_producto(registro)
        articulos.append(registro)
        self._guardar_lista(self.path_articulos, articulos)

        # Si llega precio, registrar histórico sin sobrescribir.
        if registro.get("precio") not in (None, 0, 0.0):
            self.registrar_precio_historico({
                "codigo": codigo,
                "nombre": nombre,
                "precio": registro.get("precio"),
                "unidad": registro.get("unidad") or "",
                "proveedor": registro.get("proveedor") or "",
                "precio_incluye_iva": registro.get("catalogo_maestro", {}).get("precio_incluye_iva", False),
                "iva": registro.get("catalogo_maestro", {}).get("iva", ""),
                "fecha": registro.get("catalogo_maestro", {}).get("fecha_precio", "") or now,
                "preferente": True,
                "provisional": False,
            })

        return self._enriquecer(registro)

    def editar_producto(self, codigo: str, cambios: dict[str, Any]) -> dict[str, Any]:
        articulos = self._leer_lista(self.path_articulos)
        clave = self._norm(codigo)
        for art in articulos:
            if self._norm(art.get("codigo")) != clave:
                continue

            meta = dict(art.get("catalogo_maestro") or {})
            now = datetime.now().isoformat(timespec="seconds")

            # Campos base compatibles
            for campo_base in ("nombre", "familia", "proveedor", "observaciones"):
                if campo_base in cambios and cambios[campo_base] is not None:
                    v = str(cambios[campo_base]).strip()
                    art[campo_base] = v or None
            if "precio" in cambios:
                art["precio"] = self._to_float_or_none(cambios.get("precio"))
            if "unidad_base" in cambios and cambios.get("unidad_base") is not None:
                art["unidad"] = str(cambios.get("unidad_base") or "").strip() or None
            if "activo" in cambios and cambios.get("activo") is not None:
                art["activo"] = bool(cambios.get("activo"))

            # Extensiones de catálogo maestro
            mapping = {
                "subfamilia": "subfamilia",
                "marca": "marca",
                "referencia_proveedor": "referencia_proveedor",
                "unidad_compra": "unidad_compra",
                "cantidad_formato": "cantidad_formato",
                "unidad_base": "unidad_base",
                "unidad_recetas": "unidad_recetas",
                "conversion_unidades": "conversion_unidades",
                "iva": "iva",
                "precio_incluye_iva": "precio_incluye_iva",
                "fecha_precio": "fecha_precio",
                "proveedor_preferente": "proveedor_preferente",
                "merma_habitual": "merma_habitual",
                "conservacion": "conservacion",
                "stock_minimo": "stock_minimo",
            }
            for src, dst in mapping.items():
                if src not in cambios:
                    continue
                val = cambios[src]
                if dst in {"precio_incluye_iva"}:
                    meta[dst] = bool(val)
                elif dst in {"stock_minimo"}:
                    meta[dst] = self._to_float_or_none(val)
                else:
                    meta[dst] = str(val or "").strip()

            if "alergenos" in cambios:
                al = cambios.get("alergenos")
                if isinstance(al, list):
                    meta["alergenos"] = [str(x).strip() for x in al if str(x).strip()]
                else:
                    txt = str(al or "").strip()
                    meta["alergenos"] = [s.strip() for s in txt.split(",") if s.strip()] if txt else []

            meta["observaciones_ext"] = str(cambios.get("observaciones") or art.get("observaciones") or "").strip()
            meta["fecha_modificacion"] = now
            art["catalogo_maestro"] = meta
            art["catalogo_maestro"]["estado"] = self._estado_producto(art)

            self._guardar_lista(self.path_articulos, articulos)

            if "precio" in cambios and art.get("precio") not in (None, 0, 0.0):
                self.registrar_precio_historico({
                    "codigo": art.get("codigo"),
                    "nombre": art.get("nombre"),
                    "precio": art.get("precio"),
                    "unidad": art.get("unidad") or "",
                    "proveedor": art.get("proveedor") or "",
                    "precio_incluye_iva": art.get("catalogo_maestro", {}).get("precio_incluye_iva", False),
                    "iva": art.get("catalogo_maestro", {}).get("iva", ""),
                    "fecha": art.get("catalogo_maestro", {}).get("fecha_precio", "") or now,
                    "preferente": bool(art.get("catalogo_maestro", {}).get("proveedor_preferente")),
                    "provisional": bool(cambios.get("precio_provisional", False)),
                })

            return self._enriquecer(art)

        raise ValueError("Producto no encontrado para editar.")

    def archivar_producto(self, codigo: str) -> dict[str, Any]:
        return self.editar_producto(codigo, {"activo": False})

    def productos_pendientes(self) -> list[dict[str, Any]]:
        return [p for p in self.listar_productos(incluir_archivados=False) if p.get("estado") == ESTADO_PENDIENTE]

    def crear_proveedor(self, datos: dict[str, Any]) -> dict[str, Any]:
        proveedores = self._leer_lista(self.path_proveedores)
        nombre = str(datos.get("nombre") or "").strip()
        if not nombre:
            raise ValueError("El nombre del proveedor es obligatorio.")

        nombre_norm = self._norm(nombre)
        for p in proveedores:
            if self._norm(p.get("nombre")) == nombre_norm:
                return p

        nuevo = {
            "codigo": self._siguiente_codigo_proveedor(proveedores),
            "nombre": nombre,
            "nombre_normalizado": nombre_norm,
            "articulos_asociados": 0,
            "variantes_detectadas": [nombre],
            "estado": "activo",
            "observaciones": str(datos.get("observaciones") or "").strip() or None,
        }
        proveedores.append(nuevo)
        self._guardar_lista(self.path_proveedores, proveedores)
        return nuevo

    def listar_proveedores(self) -> list[dict[str, Any]]:
        return self._leer_lista(self.path_proveedores)

    def obtener_proveedores_y_precios(self, codigo_producto: str = "") -> dict[str, Any]:
        asociaciones = self._leer_lista(self.path_producto_proveedor)
        historico = self._leer_json(self.path_historico_precios, {"registros": []})
        registros = historico.get("registros", []) if isinstance(historico, dict) else []

        clave = self._norm(codigo_producto)
        if clave:
            producto = self.obtener_producto(codigo_producto)
            nombre_norm = self._norm(producto.get("nombre")) if producto else ""
            asociaciones = [a for a in asociaciones if self._norm(a.get("producto")) == nombre_norm]
            registros = [r for r in registros if self._norm(r.get("articulo_id")) == clave or self._norm(r.get("nombre_articulo")) == nombre_norm]

        return {
            "asociaciones": asociaciones,
            "historico_precios": registros,
        }

    def registrar_precio_historico(self, datos: dict[str, Any]) -> dict[str, Any]:
        payload = self._leer_json(self.path_historico_precios, {"version": "3.0.3.5.3", "registros": []})
        registros = payload.get("registros") if isinstance(payload, dict) else None
        if not isinstance(registros, list):
            registros = []

        entry = {
            "articulo_id": str(datos.get("codigo") or "").strip(),
            "nombre_articulo": str(datos.get("nombre") or "").strip(),
            "precio": float(datos.get("precio") or 0),
            "unidad": str(datos.get("unidad") or "").strip(),
            "proveedor_id": "",
            "proveedor_nombre": str(datos.get("proveedor") or "").strip(),
            "numero_factura": "",
            "fecha_factura": str(datos.get("fecha") or datetime.now().isoformat(timespec="seconds")),
            "origen": "catalogo_maestro_601",
            "fecha_registro": datetime.now().isoformat(timespec="seconds"),
            "precio_incluye_iva": bool(datos.get("precio_incluye_iva", False)),
            "iva": str(datos.get("iva") or ""),
            "preferente": bool(datos.get("preferente", False)),
            "provisional": bool(datos.get("provisional", False)),
        }
        registros.append(entry)
        payload["registros"] = registros
        self._guardar_json(self.path_historico_precios, payload)

        # Asociación producto-proveedor para compras, sin borrar histórico previo.
        self._actualizar_asociacion_producto_proveedor(entry)
        return entry

    def _actualizar_asociacion_producto_proveedor(self, precio: dict[str, Any]) -> None:
        asociaciones = self._leer_lista(self.path_producto_proveedor)
        nombre = str(precio.get("nombre_articulo") or "").strip()
        proveedor = str(precio.get("proveedor_nombre") or "").strip()
        if not nombre or not proveedor:
            return

        nombre_norm = self._norm(nombre)
        proveedor_norm = self._norm(proveedor)
        now = datetime.now().isoformat(timespec="seconds")

        objetivo = None
        for a in asociaciones:
            if self._norm(a.get("producto")) == nombre_norm and self._norm(a.get("proveedor_nombre")) == proveedor_norm:
                objetivo = a
                break

        if objetivo is None:
            pid = self._slug(proveedor)[:10]
            aid = self._slug(nombre)[:10]
            objetivo = {
                "producto": nombre,
                "producto_normalizado": nombre_norm,
                "proveedor_id": f"PROVCMP-{pid}",
                "proveedor_nombre": proveedor,
                "preferente": bool(precio.get("preferente", False)),
                "frecuencia": 0,
                "ultima_compra": "",
                "veces_usado": 0,
                "precio_habitual": None,
                "unidad_precio": "",
                "cantidad_minima_producto": None,
                "plazo_entrega_dias": None,
                "ultima_actualizacion_precio": "",
                "observaciones": "",
                "numero_compras": 0,
                "ultima_compra_en": "",
                "activo": True,
                "id": f"ASOCPROV-{aid}{pid}"[:18],
                "creado_en": now,
                "actualizado_en": now,
            }
            asociaciones.append(objetivo)

        objetivo["precio_habitual"] = float(precio.get("precio") or 0)
        objetivo["unidad_precio"] = str(precio.get("unidad") or "")
        objetivo["ultima_actualizacion_precio"] = str(precio.get("fecha_factura") or now)
        objetivo["proveedor_nombre"] = proveedor
        if bool(precio.get("preferente", False)):
            for a in asociaciones:
                if self._norm(a.get("producto")) == nombre_norm:
                    a["preferente"] = False
            objetivo["preferente"] = True
        objetivo["actualizado_en"] = now

        self._guardar_lista(self.path_producto_proveedor, asociaciones)

    @staticmethod
    def _to_float_or_none(valor: Any) -> float | None:
        if valor in (None, ""):
            return None
        if isinstance(valor, (int, float)):
            return float(valor)
        t = str(valor).replace("€", "").replace(" ", "").strip()
        if "," in t and "." in t:
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", ".")
        try:
            return float(t)
        except ValueError:
            return None


__all__ = [
    "RepositorioProductosMaestro601",
    "ESTADO_ACTIVO",
    "ESTADO_PENDIENTE",
    "ESTADO_ARCHIVADO",
]
