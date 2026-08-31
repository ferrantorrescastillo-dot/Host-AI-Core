from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from SERVICIOS.repository_initialization_policy import should_initialize_persistently

from SERVICIOS.asistente_resolucion_incidencias_601 import AsistenteResolucionIncidencias601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.motor_calculo_escandallos_601 import (
    ESTADO_ARCHIVADO,
    ESTADO_BORRADOR,
    ESTADO_CON_INCIDENCIAS,
    ESTADO_DESACTUALIZADO,
    ESTADO_OPERATIVO,
    MotorCalculoEscandallos601,
)
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


class _RepositorioIncidenciasEscandallos601:
    """Adaptador local para resolver incidencias sin depender de centro_importacion_601."""

    def __init__(self, base_dir: Path):
        self.repo_catalogo = RepositorioProductosMaestro601(Path(base_dir).resolve())

    def listar_productos(self) -> list[dict[str, Any]]:
        productos = self.repo_catalogo.listar_productos(incluir_archivados=True)
        salida: list[dict[str, Any]] = []
        for p in productos:
            item = dict(p)
            item.setdefault("id", item.get("codigo"))
            salida.append(item)
        return salida

    def listar_proveedores(self) -> list[dict[str, Any]]:
        proveedores = self.repo_catalogo.listar_proveedores()
        salida: list[dict[str, Any]] = []
        for p in proveedores:
            item = dict(p)
            item.setdefault("id", item.get("codigo"))
            salida.append(item)
        return salida

    def crear_producto(self, producto: dict[str, Any]) -> dict[str, Any]:
        data = dict(producto)
        if "cantidad_por_envase" in data and "cantidad_formato" not in data:
            data["cantidad_formato"] = data.get("cantidad_por_envase")
        if "unidad_receta" in data and "unidad_recetas" not in data:
            data["unidad_recetas"] = data.get("unidad_receta")
        if "unidad_formato" in data and "unidad_base" not in data:
            data["unidad_base"] = data.get("unidad_formato")
        elif "unidad_compra" in data and "unidad_base" not in data:
            data["unidad_base"] = data.get("unidad_compra")
        creado = self.repo_catalogo.crear_producto(data)
        out = dict(creado)
        out.setdefault("id", out.get("codigo"))
        return out

    def actualizar_producto(self, producto_id: str, cambios: dict[str, Any]) -> dict[str, Any] | None:
        data = dict(cambios)
        if "cantidad_por_envase" in data and "cantidad_formato" not in data:
            data["cantidad_formato"] = data.get("cantidad_por_envase")
        if "unidad_receta" in data and "unidad_recetas" not in data:
            data["unidad_recetas"] = data.get("unidad_receta")
        if "unidad_formato" in data and "unidad_base" not in data:
            data["unidad_base"] = data.get("unidad_formato")
        elif "unidad_compra" in data and "unidad_base" not in data:
            data["unidad_base"] = data.get("unidad_compra")
        codigo = str(producto_id or "").strip()
        try:
            actualizado = self.repo_catalogo.editar_producto(codigo, data)
            out = dict(actualizado)
            out.setdefault("id", out.get("codigo"))
            return out
        except ValueError:
            return None

    def asegurar_producto_basico(self, nombre: str) -> dict[str, Any]:
        encontrados = self.repo_catalogo.buscar_productos({"nombre": str(nombre or "")})
        if encontrados:
            out = dict(encontrados[0])
            out.setdefault("id", out.get("codigo"))
            return out
        creado = self.repo_catalogo.crear_producto({"nombre": nombre})
        out = dict(creado)
        out.setdefault("id", out.get("codigo"))
        return out

    def crear_proveedor(self, proveedor: dict[str, Any]) -> dict[str, Any]:
        nuevo = self.repo_catalogo.crear_proveedor(proveedor)
        out = dict(nuevo)
        out.setdefault("id", out.get("codigo"))
        return out


class RepositorioBibliotecaEscandallos601:
    VERSION_MODELO = "6.0.1"

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.path = self.base_dir / "DATOS" / "db" / "biblioteca_escandallos_601.json"
        if should_initialize_persistently():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._asegurar_archivo()

    def _asegurar_archivo(self) -> None:
        if self.path.exists():
            return
        self._guardar(
            {
                "version_modelo": self.VERSION_MODELO,
                "actualizado_en": datetime.now().isoformat(timespec="seconds"),
                "escandallos": [],
                "historial_calculos": [],
                "simulaciones": [],
            }
        )

    def _leer(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            data = {}
        return {
            "version_modelo": str(data.get("version_modelo") or self.VERSION_MODELO),
            "actualizado_en": str(data.get("actualizado_en") or ""),
            "escandallos": list(data.get("escandallos") or []),
            "historial_calculos": list(data.get("historial_calculos") or []),
            "simulaciones": list(data.get("simulaciones") or []),
        }

    def _guardar(self, payload: dict[str, Any]) -> None:
        payload["version_modelo"] = self.VERSION_MODELO
        payload["actualizado_en"] = datetime.now().isoformat(timespec="seconds")
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.path.parent, suffix=".tmp") as tmp:
            json.dump(payload, tmp, ensure_ascii=False, indent=2)
            tmp.flush()
            tmp_path = Path(tmp.name)
        tmp_path.replace(self.path)

    @staticmethod
    def _norm(txt: Any) -> str:
        return " ".join(str(txt or "").strip().lower().split())

    def _next_id(self, escs: list[dict[str, Any]]) -> str:
        last = 0
        for e in escs:
            txt = str(e.get("id") or "")
            if txt.startswith("ESC601-"):
                try:
                    last = max(last, int(txt.split("-")[-1]))
                except ValueError:
                    continue
        return f"ESC601-{last + 1:06d}"

    def _next_code(self, nombre: str, escs: list[dict[str, Any]]) -> str:
        base = "ESC-" + "-".join(x for x in str(nombre or "").upper().split() if x)
        base = "".join(ch for ch in base if ch.isalnum() or ch == "-")[:42] or "ESCANDALLO"
        used = {str(e.get("codigo") or "").upper() for e in escs}
        if base not in used:
            return base
        idx = 2
        while f"{base}-{idx}" in used:
            idx += 1
        return f"{base}-{idx}"

    def listar(self, incluir_archivados: bool = False) -> list[dict[str, Any]]:
        escs = list(self._leer().get("escandallos") or [])
        if incluir_archivados:
            return escs
        return [e for e in escs if str(e.get("estado") or "") != ESTADO_ARCHIVADO]

    def obtener(self, id_o_codigo: str) -> dict[str, Any] | None:
        clave = self._norm(id_o_codigo)
        if not clave:
            return None
        for e in self.listar(incluir_archivados=True):
            if clave in {self._norm(e.get("id")), self._norm(e.get("codigo"))}:
                return e
        return None

    def buscar(self, filtros: dict[str, str]) -> list[dict[str, Any]]:
        lista = self.listar(incluir_archivados=True)
        fn = self._norm(filtros.get("nombre", ""))
        fc = self._norm(filtros.get("codigo", ""))
        fr = self._norm(filtros.get("receta", ""))
        fi = self._norm(filtros.get("ingrediente", ""))
        ff = self._norm(filtros.get("familia", ""))
        fe = self._norm(filtros.get("estado", ""))
        out: list[dict[str, Any]] = []
        for e in lista:
            if fn and fn not in self._norm(e.get("nombre")):
                continue
            if fc and fc not in self._norm(e.get("codigo")):
                continue
            rec = e.get("receta_asociada") or {}
            if fr and fr not in self._norm(rec.get("nombre")) and fr not in self._norm(rec.get("codigo")):
                continue
            if ff and ff not in self._norm(e.get("familia")):
                continue
            if fe and fe != self._norm(e.get("estado")):
                continue
            if fi:
                hay = any(fi in self._norm(x.get("nombre_mostrado")) for x in list(e.get("lineas") or []))
                if not hay:
                    continue
            out.append(e)
        return out

    def guardar_nuevo(self, esc: dict[str, Any]) -> dict[str, Any]:
        payload = self._leer()
        escs = list(payload.get("escandallos") or [])
        now = datetime.now().isoformat(timespec="seconds")
        nuevo = dict(esc)
        nuevo.setdefault("id", self._next_id(escs))
        nuevo.setdefault("codigo", self._next_code(str(nuevo.get("nombre") or "Escandallo"), escs))
        nuevo.setdefault("fecha_creacion", now)
        nuevo.setdefault("fecha_ultimo_calculo", now)
        nuevo.setdefault("calculo_version", 1)
        nuevo.setdefault("estado", ESTADO_BORRADOR)
        escs.append(nuevo)
        payload["escandallos"] = escs
        self._guardar(payload)
        return nuevo

    def actualizar(self, id_o_codigo: str, cambios: dict[str, Any], *, motivo_historial: str = "edicion") -> dict[str, Any]:
        payload = self._leer()
        escs = list(payload.get("escandallos") or [])
        objetivo = self.obtener(id_o_codigo)
        if not objetivo:
            raise ValueError("Escandallo no encontrado.")

        now = datetime.now().isoformat(timespec="seconds")
        actualizado = dict(objetivo)
        actualizado.update(cambios)
        actualizado["actualizado_en"] = now
        actualizado["fecha_ultimo_calculo"] = str(cambios.get("fecha_calculo") or actualizado.get("fecha_ultimo_calculo") or now)
        actualizado["calculo_version"] = int(objetivo.get("calculo_version") or 1) + 1

        for i, e in enumerate(escs):
            if str(e.get("id")) == str(objetivo.get("id")):
                escs[i] = actualizado
                break

        payload["escandallos"] = escs
        payload.setdefault("historial_calculos", []).append(
            {
                "escandallo_id": str(actualizado.get("id") or ""),
                "codigo": str(actualizado.get("codigo") or ""),
                "fecha": now,
                "usuario": "sistema",
                "coste_total": float(actualizado.get("coste_total") or 0.0),
                "coste_por_racion": float(actualizado.get("coste_por_racion") or 0.0),
                "precio_venta_total": float(actualizado.get("precio_venta_total") or 0.0),
                "precio_venta_por_racion": float(actualizado.get("precio_venta_por_racion") or 0.0),
                "margen": float(actualizado.get("margen_porcentual") or 0.0),
                "raciones": float(actualizado.get("numero_raciones") or 0.0),
                "mermas": [float(x.get("merma_pct") or 0.0) for x in list(actualizado.get("lineas") or [])],
                "productos_precios": [
                    {
                        "producto_codigo": x.get("producto_codigo"),
                        "producto": x.get("nombre_mostrado"),
                        "precio": x.get("precio_compra_utilizado"),
                        "unidad": x.get("unidad_precio"),
                        "proveedor": x.get("proveedor_precio"),
                        "fecha_precio": x.get("fecha_precio"),
                        "provisional": x.get("precio_provisional"),
                    }
                    for x in list(actualizado.get("lineas") or [])
                ],
                "motivo": motivo_historial,
                "foto_calculo": {
                    "coste_total": float(actualizado.get("coste_total") or 0.0),
                    "coste_por_racion": float(actualizado.get("coste_por_racion") or 0.0),
                    "lineas": list(actualizado.get("lineas") or []),
                    "referencia_precios": list(actualizado.get("referencia_precios") or []),
                    "incidencias": list(actualizado.get("incidencias") or []),
                },
            }
        )
        self._guardar(payload)
        return actualizado

    def duplicar(self, id_o_codigo: str) -> dict[str, Any]:
        payload = self._leer()
        escs = list(payload.get("escandallos") or [])
        original = self.obtener(id_o_codigo)
        if not original:
            raise ValueError("Escandallo no encontrado para duplicar.")

        now = datetime.now().isoformat(timespec="seconds")
        copia = dict(original)
        copia["id"] = self._next_id(escs)
        copia["codigo"] = self._next_code(str(original.get("nombre") or "Escandallo"), escs)
        copia["nombre"] = f"{original.get('nombre', 'Escandallo')} (Copia)"
        copia["estado"] = ESTADO_BORRADOR
        copia["fecha_creacion"] = now
        copia["fecha_ultimo_calculo"] = now
        copia["calculo_version"] = 1
        escs.append(copia)
        payload["escandallos"] = escs
        self._guardar(payload)
        return copia

    def archivar(self, id_o_codigo: str) -> dict[str, Any]:
        return self.actualizar(id_o_codigo, {"estado": ESTADO_ARCHIVADO}, motivo_historial="archivado")

    def historial(self, escandallo_id: str = "") -> list[dict[str, Any]]:
        data = list(self._leer().get("historial_calculos") or [])
        sid = self._norm(escandallo_id)
        if sid:
            data = [h for h in data if sid in {self._norm(h.get("escandallo_id")), self._norm(h.get("codigo"))}]
        return sorted(data, key=lambda x: str(x.get("fecha") or ""), reverse=True)


class BibliotecaEscandallos601:
    def __init__(self, base_dir: Path, repo_incidencias: Any | None = None):
        self.base_dir = Path(base_dir).resolve()
        self.repo_esc = RepositorioBibliotecaEscandallos601(self.base_dir)
        self.repo_rec = RepositorioBibliotecaRecetas601(self.base_dir)
        self.repo_prod = RepositorioProductosMaestro601(self.base_dir)
        self.motor = MotorCalculoEscandallos601(self.repo_prod)
        repo = repo_incidencias or _RepositorioIncidenciasEscandallos601(self.base_dir)
        self.asistente_incidencias = AsistenteResolucionIncidencias601(repo, self.base_dir)

    def buscar(self, filtros: dict[str, str]) -> dict[str, Any]:
        data = self.repo_esc.buscar(filtros)
        return {"ok": True, "total": len(data), "escandallos": data}

    def ver_todos(self) -> dict[str, Any]:
        data = self.repo_esc.listar(incluir_archivados=True)
        return {"ok": True, "total": len(data), "escandallos": data}

    def ver_detalle(self, id_o_codigo: str) -> dict[str, Any]:
        esc = self.repo_esc.obtener(id_o_codigo)
        if not esc:
            return {"ok": False, "mensaje": "Escandallo no encontrado."}
        desactualizado, cambios = self.motor.detectar_desactualizado(esc)
        if desactualizado and str(esc.get("estado") or "") not in {ESTADO_ARCHIVADO, ESTADO_DESACTUALIZADO}:
            esc = self.repo_esc.actualizar(str(esc.get("id") or esc.get("codigo") or ""), {"estado": ESTADO_DESACTUALIZADO}, motivo_historial="desactualizacion")
        return {
            "ok": True,
            "escandallo": esc,
            "desactualizado": desactualizado,
            "cambios_detectados": cambios,
        }

    def _lineas_desde_receta(self, receta: dict[str, Any]) -> list[dict[str, Any]]:
        ingredientes = list(receta.get("ingredientes") or [])
        cantidades = list(receta.get("cantidades") or [])
        while len(cantidades) < len(ingredientes):
            cantidades.append("")

        out: list[dict[str, Any]] = []
        recetas_existentes = self.repo_rec.listar(incluir_archivadas=True)
        nombres_recetas = {str(r.get("nombre") or "").strip().lower(): r for r in recetas_existentes}

        for nombre, cantidad in zip(ingredientes, cantidades):
            n = str(nombre or "").strip()
            ref_componente = nombres_recetas.get(n.lower())
            if ref_componente:
                esc_comp = self._buscar_escandallo_operativo_por_receta(ref_componente)
                if esc_comp:
                    out.append(
                        {
                            "producto": n,
                            "nombre_mostrado": n,
                            "cantidad_texto": cantidad,
                            "unidad_receta": "u",
                            "dato_manual": False,
                            "observaciones": "Componente con coste de escandallo asociado.",
                            "componente_escandallo_id": esc_comp.get("id"),
                            "coste_fijo_componente": float(esc_comp.get("coste_por_racion") or 0.0),
                        }
                    )
                else:
                    out.append(
                        {
                            "producto": n,
                            "nombre_mostrado": n,
                            "cantidad_texto": cantidad,
                            "unidad_receta": "u",
                            "dato_manual": False,
                            "observaciones": "Componente sin escandallo operativo.",
                            "incidencia_forzada": "COMPONENTE_SIN_ESCANDALLO",
                        }
                    )
            else:
                out.append(
                    {
                        "producto": n,
                        "nombre_mostrado": n,
                        "cantidad_texto": cantidad,
                        "dato_manual": False,
                    }
                )
        return out

    def _buscar_escandallo_operativo_por_receta(self, receta: dict[str, Any]) -> dict[str, Any] | None:
        rid = str(receta.get("id") or "")
        rcod = str(receta.get("codigo") or "")
        for e in self.repo_esc.listar(incluir_archivados=False):
            r = e.get("receta_asociada") or {}
            if str(r.get("id") or "") == rid or str(r.get("codigo") or "") == rcod:
                if str(e.get("estado") or "") == ESTADO_OPERATIVO:
                    return e
        return None

    def generar_desde_receta(self, id_o_codigo_receta: str, *, precio_venta_total: float = 0.0, simular: bool = False) -> dict[str, Any]:
        receta = self.repo_rec.obtener(id_o_codigo_receta)
        if not receta:
            return {"ok": False, "mensaje": "Receta no encontrada."}

        lineas_entrada = self._lineas_desde_receta(receta)
        calculo = self.motor.calcular(
            nombre_escandallo=str(receta.get("nombre") or "Escandallo"),
            numero_raciones=float(receta.get("numero_raciones") or 0.0),
            lineas_entrada=lineas_entrada,
            precio_venta_total=float(precio_venta_total or 0.0),
            receta_asociada={
                "id": str(receta.get("id") or ""),
                "codigo": str(receta.get("codigo") or ""),
                "nombre": str(receta.get("nombre") or ""),
                "version": int(receta.get("version") or 1),
            },
        )

        for entrada, linea in zip(lineas_entrada, calculo.get("lineas", [])):
            if entrada.get("incidencia_forzada") == "COMPONENTE_SIN_ESCANDALLO":
                linea.setdefault("incidencias", []).append({"tipo": "COMPONENTE_SIN_ESCANDALLO", "detalle": f"Componente sin escandallo operativo: {entrada.get('producto')}"})
                linea["estado_linea"] = "CON_INCIDENCIAS"
                calculo.setdefault("incidencias", []).append({"tipo": "COMPONENTE_SIN_ESCANDALLO", "detalle": f"Componente sin escandallo operativo: {entrada.get('producto')}"})

        if simular:
            payload = dict(calculo)
            payload["simulacion"] = True
            return {"ok": True, "escandallo": payload, "guardado": False}

        guardado = self.repo_esc.guardar_nuevo(
            {
                **calculo,
                "nombre": str(calculo.get("nombre") or receta.get("nombre") or "Escandallo"),
                "codigo": str(receta.get("codigo") or ""),
                "estado": str(calculo.get("estado") or ESTADO_BORRADOR),
                "rendimiento_total": float(receta.get("numero_raciones") or 0.0),
                "unidad_rendimiento": "racion",
                "observaciones_economicas": "",
                "familia": str(receta.get("familia") or ""),
            }
        )
        return {"ok": True, "escandallo": guardado, "guardado": True}

    def crear_manual(self, datos: dict[str, Any], *, simular: bool = False) -> dict[str, Any]:
        lineas = list(datos.get("lineas") or [])
        calculo = self.motor.calcular(
            nombre_escandallo=str(datos.get("nombre") or "Escandallo manual"),
            numero_raciones=float(datos.get("numero_raciones") or 0.0),
            lineas_entrada=lineas,
            precio_venta_total=float(datos.get("precio_venta_total") or 0.0),
            precio_venta_por_racion=float(datos.get("precio_venta_por_racion") or 0.0),
            venta_incluye_iva=bool(datos.get("venta_incluye_iva", False)),
            iva_venta=float(datos.get("iva_venta")) if datos.get("iva_venta") not in (None, "") else None,
            receta_asociada={
                "id": str(datos.get("receta_asociada_id") or ""),
                "codigo": str(datos.get("receta_asociada_codigo") or ""),
                "nombre": str(datos.get("receta_asociada_nombre") or ""),
                "version": int(datos.get("receta_asociada_version") or 0),
            },
        )

        if simular:
            out = dict(calculo)
            out["simulacion"] = True
            return {"ok": True, "escandallo": out, "guardado": False}

        esc = self.repo_esc.guardar_nuevo(
            {
                **calculo,
                "nombre": str(datos.get("nombre") or calculo.get("nombre") or "Escandallo manual"),
                "codigo": str(datos.get("codigo") or ""),
                "rendimiento_total": float(datos.get("rendimiento_total") or datos.get("numero_raciones") or 0.0),
                "unidad_rendimiento": str(datos.get("unidad_rendimiento") or "racion"),
                "observaciones_economicas": str(datos.get("observaciones_economicas") or "Este escandallo no está vinculado todavía a una receta."),
                "familia": str(datos.get("familia") or ""),
            }
        )
        return {"ok": True, "escandallo": esc, "guardado": True}

    def generar_pendientes(self, *, confirmar: bool = False, recetas_seleccionadas: list[str] | None = None) -> dict[str, Any]:
        recetas = self.repo_rec.listar(incluir_archivadas=False)
        existentes = self.repo_esc.listar(incluir_archivados=True)

        pendientes: list[dict[str, Any]] = []
        for r in recetas:
            rid = str(r.get("id") or "")
            asociados = [e for e in existentes if str((e.get("receta_asociada") or {}).get("id") or "") == rid]
            if not asociados:
                pendientes.append({"receta": r, "motivo": "sin_escandallo"})
                continue
            if all(str(e.get("estado") or "") == ESTADO_ARCHIVADO for e in asociados):
                pendientes.append({"receta": r, "motivo": "escandallo_archivado"})
                continue
            if any(str(e.get("estado") or "") == ESTADO_DESACTUALIZADO for e in asociados):
                pendientes.append({"receta": r, "motivo": "escandallo_desactualizado"})
                continue

        if not confirmar:
            return {"ok": True, "pendientes": pendientes, "total": len(pendientes)}

        seleccion = set(recetas_seleccionadas or [])
        generadas = 0
        advertencias = 0
        bloqueadas = 0
        detalle: list[dict[str, Any]] = []
        for p in pendientes:
            receta = p["receta"]
            codigo = str(receta.get("codigo") or "")
            if seleccion and codigo not in seleccion and str(receta.get("id") or "") not in seleccion:
                continue
            res = self.generar_desde_receta(codigo)
            if not res.get("ok"):
                bloqueadas += 1
                detalle.append({"receta": codigo, "estado": "bloqueada", "motivo": res.get("mensaje")})
                continue
            esc = res.get("escandallo") or {}
            estado = str(esc.get("estado") or "")
            if estado == ESTADO_OPERATIVO:
                generadas += 1
                detalle.append({"receta": codigo, "estado": "generada"})
            elif estado in {ESTADO_CON_INCIDENCIAS, ESTADO_DESACTUALIZADO}:
                advertencias += 1
                detalle.append({"receta": codigo, "estado": "advertencias"})
            else:
                bloqueadas += 1
                detalle.append({"receta": codigo, "estado": "bloqueada", "motivo": estado})

        return {
            "ok": True,
            "recetas_analizadas": len(pendientes),
            "escandallos_generados": generadas,
            "generados_con_advertencias": advertencias,
            "pendientes": bloqueadas,
            "detalle": detalle,
        }

    def editar(self, id_o_codigo: str, cambios: dict[str, Any]) -> dict[str, Any]:
        actual = self.repo_esc.obtener(id_o_codigo)
        if not actual:
            return {"ok": False, "mensaje": "Escandallo no encontrado."}

        lineas = list(cambios.get("lineas") or actual.get("lineas") or [])
        calculo = self.motor.calcular(
            nombre_escandallo=str(cambios.get("nombre") or actual.get("nombre") or "Escandallo"),
            numero_raciones=float(cambios.get("numero_raciones") or actual.get("numero_raciones") or 0.0),
            lineas_entrada=lineas,
            precio_venta_total=float(cambios.get("precio_venta_total") or actual.get("precio_venta_total") or 0.0),
            receta_asociada=dict(actual.get("receta_asociada") or {}),
        )

        actualizado = self.repo_esc.actualizar(
            id_o_codigo,
            {
                **actual,
                **cambios,
                **calculo,
            },
            motivo_historial="edicion",
        )
        return {"ok": True, "escandallo": actualizado}

    def duplicar(self, id_o_codigo: str) -> dict[str, Any]:
        try:
            nuevo = self.repo_esc.duplicar(id_o_codigo)
            return {"ok": True, "escandallo": nuevo}
        except ValueError as exc:
            return {"ok": False, "mensaje": str(exc)}

    def recalcular(self, id_o_codigo: str, opcion: int, precios_por_linea: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
        esc = self.repo_esc.obtener(id_o_codigo)
        if not esc:
            return {"ok": False, "mensaje": "Escandallo no encontrado."}

        lineas_entrada = []
        precios_fijados: dict[str, dict[str, Any]] = {}
        for l in list(esc.get("lineas") or []):
            lineas_entrada.append(
                {
                    "producto_codigo": l.get("producto_codigo"),
                    "producto": l.get("nombre_mostrado"),
                    "cantidad_neta": l.get("cantidad_neta"),
                    "unidad_receta": l.get("unidad_receta"),
                    "merma_especifica": l.get("merma_pct"),
                    "dato_manual": l.get("dato_manual", False),
                }
            )
            if opcion == 2:
                precios_fijados[str(l.get("producto_codigo") or "")] = {
                    "precio_neto_unidad_base": l.get("precio_compra_utilizado"),
                    "unidad_base": l.get("unidad_base_calculo"),
                    "proveedor": l.get("proveedor_precio"),
                    "fecha": l.get("fecha_precio"),
                    "provisional": l.get("precio_provisional", False),
                }
        if opcion == 3 and precios_por_linea:
            precios_fijados.update(precios_por_linea)

        recalculo = self.motor.calcular(
            nombre_escandallo=str(esc.get("nombre") or "Escandallo"),
            numero_raciones=float(esc.get("numero_raciones") or 0.0),
            lineas_entrada=lineas_entrada,
            precio_venta_total=float(esc.get("precio_venta_total") or 0.0),
            receta_asociada=dict(esc.get("receta_asociada") or {}),
            precios_fijados=precios_fijados if precios_fijados else None,
        )

        coste_anterior = float(esc.get("coste_total") or 0.0)
        coste_nuevo = float(recalculo.get("coste_total") or 0.0)
        variacion = coste_nuevo - coste_anterior
        variacion_pct = (variacion / coste_anterior * 100.0) if coste_anterior else 0.0

        resumen = {
            "lineas_afectadas": len(recalculo.get("lineas") or []),
            "coste_anterior": round(coste_anterior, 6),
            "coste_nuevo": round(coste_nuevo, 6),
            "variacion": round(variacion, 6),
            "variacion_pct": round(variacion_pct, 6),
        }

        if opcion == 4:
            return {"ok": True, "simulacion": True, "resumen": resumen, "escandallo": recalculo}

        actualizado = self.repo_esc.actualizar(id_o_codigo, {**esc, **recalculo}, motivo_historial="actualizacion_precios")
        return {"ok": True, "simulacion": False, "resumen": resumen, "escandallo": actualizado}

    def archivar(self, id_o_codigo: str) -> dict[str, Any]:
        try:
            out = self.repo_esc.archivar(id_o_codigo)
            return {"ok": True, "escandallo": out, "usos_detectados": {"menus": 0, "eventos": 0, "simulaciones": 0, "historicos": len(self.repo_esc.historial(id_o_codigo))}}
        except ValueError as exc:
            return {"ok": False, "mensaje": str(exc)}

    def escandallos_con_incidencias(self) -> dict[str, Any]:
        data = [e for e in self.repo_esc.listar(incluir_archivados=False) if str(e.get("estado") or "") in {ESTADO_CON_INCIDENCIAS, ESTADO_DESACTUALIZADO} or (e.get("incidencias") or [])]
        return {"ok": True, "total": len(data), "escandallos": data}

    def historial_calculos(self, id_o_codigo: str = "") -> dict[str, Any]:
        return {"ok": True, "historial": self.repo_esc.historial(id_o_codigo), "total": len(self.repo_esc.historial(id_o_codigo))}


class BibliotecaEscandallosUI601:
    def __init__(self, base_dir: Path):
        self.servicio = BibliotecaEscandallos601(base_dir)

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
                self._nuevo_manual()
            elif op == "4":
                self._generar_desde_receta()
            elif op == "5":
                self._generar_pendientes()
            elif op == "6":
                self._editar()
            elif op == "7":
                self._duplicar()
            elif op == "8":
                self._recalcular()
            elif op == "9":
                self._archivar()
            elif op == "10":
                self._incidencias()
            elif op == "11":
                self._historial()
            else:
                print("Opción no válida")

    @staticmethod
    def _menu() -> None:
        print("\nBIBLIOTECA DE ESCANDALLOS")
        print("1. Buscar escandallo")
        print("2. Ver todos los escandallos")
        print("3. Nuevo escandallo")
        print("4. Generar desde receta")
        print("5. Generar escandallos pendientes")
        print("6. Editar escandallo")
        print("7. Duplicar escandallo")
        print("8. Recalcular escandallo")
        print("9. Archivar escandallo")
        print("10. Escandallos con incidencias")
        print("11. Historial de cálculos")
        print("0. Volver")

    @staticmethod
    def _mostrar_esc(e: dict[str, Any]) -> None:
        print(
            f"- {e.get('codigo')} | {e.get('nombre')} | {e.get('estado')} | "
            f"coste={e.get('coste_total')} | coste/racion={e.get('coste_por_racion')} | "
            f"venta={e.get('precio_venta_total')} | margen={e.get('margen_porcentual')} | "
            f"ultimo={e.get('fecha_ultimo_calculo')}"
        )

    def _buscar(self) -> None:
        filtros = {
            "nombre": input("Nombre: ").strip(),
            "codigo": input("Código: ").strip(),
            "receta": input("Receta asociada: ").strip(),
            "ingrediente": input("Ingrediente: ").strip(),
            "familia": input("Familia: ").strip(),
            "estado": input("Estado: ").strip(),
        }
        res = self.servicio.buscar(filtros)
        print(f"Total: {res.get('total', 0)}")
        for e in res.get("escandallos", [])[:200]:
            self._mostrar_esc(e)

    def _ver_todos(self) -> None:
        res = self.servicio.ver_todos()
        print(f"Total: {res.get('total', 0)}")
        for e in res.get("escandallos", [])[:200]:
            self._mostrar_esc(e)

    @staticmethod
    def _pedir_lineas() -> list[dict[str, Any]]:
        print("Introduce líneas de ingredientes (Enter en nombre para terminar).")
        lineas: list[dict[str, Any]] = []
        while True:
            nombre = input("Ingrediente/Producto: ").strip()
            if not nombre:
                break
            codigo = input("Código producto (opcional): ").strip()
            cantidad = input("Cantidad (ej. 350 g): ").strip()
            merma = input("Merma % (opcional): ").strip()
            lineas.append(
                {
                    "producto": nombre,
                    "producto_codigo": codigo,
                    "cantidad_texto": cantidad,
                    "merma_especifica": merma,
                }
            )
        return lineas

    def _nuevo_manual(self) -> None:
        datos = {
            "nombre": input("Nombre escandallo: ").strip(),
            "codigo": input("Código (opcional): ").strip(),
            "numero_raciones": input("Número de raciones: ").strip(),
            "rendimiento_total": input("Rendimiento total: ").strip(),
            "unidad_rendimiento": input("Unidad rendimiento: ").strip() or "racion",
            "precio_venta_total": input("Precio de venta total (opcional): ").strip(),
            "observaciones_economicas": input("Observaciones económicas: ").strip() or "Este escandallo no está vinculado todavía a una receta.",
            "lineas": self._pedir_lineas(),
        }
        sim = input("¿Simular sin guardar? (s/N): ").strip().lower() == "s"
        res = self.servicio.crear_manual(datos, simular=sim)
        print("Guardado" if res.get("guardado") else "Simulación")
        esc = res.get("escandallo") or {}
        self._mostrar_esc(esc)
        for i in esc.get("incidencias", [])[:50]:
            print(f"  * {i.get('tipo')}: {i.get('detalle')}")

    def _generar_desde_receta(self) -> None:
        receta = input("ID o código de receta: ").strip()
        pvp = input("Precio venta total (opcional): ").strip()
        res = self.servicio.generar_desde_receta(receta, precio_venta_total=float(pvp or 0), simular=False)
        if not res.get("ok"):
            print(res.get("mensaje"))
            return
        esc = res.get("escandallo") or {}
        self._mostrar_esc(esc)
        for i in esc.get("incidencias", [])[:50]:
            print(f"  * {i.get('tipo')}: {i.get('detalle')}")

    def _generar_pendientes(self) -> None:
        pre = self.servicio.generar_pendientes(confirmar=False)
        print(f"Recetas pendientes: {pre.get('total', 0)}")
        for p in pre.get("pendientes", [])[:100]:
            r = p.get("receta") or {}
            print(f"- {r.get('codigo')} | {r.get('nombre')} | motivo={p.get('motivo')}")
        if input("¿Generar ahora? (s/N): ").strip().lower() != "s":
            return
        res = self.servicio.generar_pendientes(confirmar=True)
        print(
            f"Recetas analizadas: {res.get('recetas_analizadas', 0)}\n"
            f"Escandallos generados: {res.get('escandallos_generados', 0)}\n"
            f"Generados con advertencias: {res.get('generados_con_advertencias', 0)}\n"
            f"Pendientes: {res.get('pendientes', 0)}"
        )

    def _editar(self) -> None:
        clave = input("ID o código escandallo: ").strip()
        nr = input("Nuevo número de raciones (vacío mantiene): ").strip()
        pvp = input("Nuevo precio venta total (vacío mantiene): ").strip()
        print("¿Deseas sustituir líneas?")
        nuevas_lineas = self._pedir_lineas()
        cambios: dict[str, Any] = {}
        if nr:
            cambios["numero_raciones"] = float(nr)
        if pvp:
            cambios["precio_venta_total"] = float(pvp)
        if nuevas_lineas:
            cambios["lineas"] = nuevas_lineas
        res = self.servicio.editar(clave, cambios)
        if not res.get("ok"):
            print(res.get("mensaje"))
            return
        self._mostrar_esc(res.get("escandallo") or {})

    def _duplicar(self) -> None:
        clave = input("ID o código escandallo: ").strip()
        res = self.servicio.duplicar(clave)
        if not res.get("ok"):
            print(res.get("mensaje"))
            return
        self._mostrar_esc(res.get("escandallo") or {})

    def _recalcular(self) -> None:
        clave = input("ID o código escandallo: ").strip()
        print("1. Recalcular con precios actuales")
        print("2. Mantener precios utilizados")
        print("3. Elegir precios por línea (manual)")
        print("4. Simular sin guardar")
        print("5. Cancelar")
        op = input("Opción: ").strip()
        if op == "5":
            return
        opcion = int(op or 1)
        precios_linea: dict[str, dict[str, Any]] = {}
        if opcion == 3:
            print("Introduce precios por código de producto (Enter para terminar).")
            while True:
                cod = input("Código producto: ").strip()
                if not cod:
                    break
                pr = input("Precio neto unidad base: ").strip()
                uni = input("Unidad base: ").strip()
                prov = input("Proveedor: ").strip()
                precios_linea[cod] = {
                    "precio_neto_unidad_base": float(pr or 0.0),
                    "unidad_base": uni,
                    "proveedor": prov,
                    "fecha": datetime.now().date().isoformat(),
                    "provisional": False,
                }
        res = self.servicio.recalcular(clave, opcion, precios_por_linea=precios_linea)
        if not res.get("ok"):
            print(res.get("mensaje"))
            return
        s = res.get("resumen") or {}
        print("Se han detectado cambios de precio.")
        print(f"Líneas afectadas: {s.get('lineas_afectadas', 0)}")
        print(f"Coste anterior: {s.get('coste_anterior', 0)}")
        print(f"Coste nuevo: {s.get('coste_nuevo', 0)}")
        print(f"Variación: {s.get('variacion', 0)}")
        print(f"Variación (%): {s.get('variacion_pct', 0)}")

    def _archivar(self) -> None:
        clave = input("ID o código escandallo: ").strip()
        res = self.servicio.archivar(clave)
        if not res.get("ok"):
            print(res.get("mensaje"))
            return
        usos = res.get("usos_detectados") or {}
        print(
            "Usos detectados antes de archivar: "
            f"menus={usos.get('menus', 0)}, eventos={usos.get('eventos', 0)}, "
            f"simulaciones={usos.get('simulaciones', 0)}, historicos={usos.get('historicos', 0)}"
        )
        self._mostrar_esc(res.get("escandallo") or {})

    def _incidencias(self) -> None:
        res = self.servicio.escandallos_con_incidencias()
        print(f"Total con incidencias: {res.get('total', 0)}")
        for e in res.get("escandallos", [])[:200]:
            self._mostrar_esc(e)
            for i in list(e.get("incidencias") or [])[:10]:
                print(f"  * {i.get('tipo')}: {i.get('detalle')}")

    def _historial(self) -> None:
        clave = input("ID/código escandallo (vacío=todo): ").strip()
        res = self.servicio.historial_calculos(clave)
        print(f"Entradas historial: {res.get('total', 0)}")
        for h in res.get("historial", [])[:200]:
            print(
                f"- {h.get('fecha')} | {h.get('codigo')} | "
                f"coste={h.get('coste_total')} | venta={h.get('precio_venta_total')} | "
                f"margen={h.get('margen')} | motivo={h.get('motivo')}"
            )


__all__ = [
    "RepositorioBibliotecaEscandallos601",
    "BibliotecaEscandallos601",
    "BibliotecaEscandallosUI601",
]
