from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
import json
import re
import unicodedata


class ServicioConfiguracionRestaurante:
    """Gestiona la configuracion estructural del restaurante (R1)."""

    VERSION = "R1"

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self.db_dir = self.base_dir / "DATOS" / "db"
        self.ruta_configuracion = self.db_dir / "restaurante.json"

    def crear_configuracion_inicial(self, forzar: bool = False) -> dict[str, Any]:
        self.db_dir.mkdir(parents=True, exist_ok=True)
        if self.ruta_configuracion.exists() and not forzar:
            return self.cargar_configuracion()
        config = self._configuracion_base()
        self.guardar_configuracion(config)
        return config

    def cargar_configuracion(self) -> dict[str, Any]:
        if not self.ruta_configuracion.exists():
            return self.crear_configuracion_inicial()
        try:
            bruto = json.loads(self.ruta_configuracion.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            bruto = {}
        normalizada = self._normalizar_configuracion(
            bruto if isinstance(bruto, dict) else {},
            resolver_conflictos=True,
        )
        validacion = self.validar_estructura(normalizada)
        if not validacion["ok"]:
            normalizada = self._configuracion_base()
        self.guardar_configuracion(normalizada)
        return normalizada

    def guardar_configuracion(self, configuracion: dict[str, Any]) -> dict[str, Any]:
        self.db_dir.mkdir(parents=True, exist_ok=True)
        normalizada = self._normalizar_configuracion(configuracion, resolver_conflictos=False)
        validacion = self.validar_estructura(normalizada)
        if not validacion["ok"]:
            raise ValueError("Configuracion invalida: " + " | ".join(validacion["errores"]))
        self.ruta_configuracion.write_text(
            json.dumps(normalizada, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return deepcopy(normalizada)

    def validar_estructura(self, configuracion: dict[str, Any] | None = None) -> dict[str, Any]:
        datos = configuracion if isinstance(configuracion, dict) else self._configuracion_base()
        errores: list[str] = []

        if not isinstance(datos.get("version"), str) or not str(datos.get("version", "")).strip():
            errores.append("version debe ser un texto no vacio")

        dg = datos.get("datos_generales")
        if not isinstance(dg, dict):
            errores.append("datos_generales debe ser un objeto")
        else:
            for campo in ["nombre_restaurante", "direccion", "telefono", "correo_electronico", "horario_general"]:
                if campo not in dg:
                    errores.append(f"Falta campo en datos_generales: {campo}")
                elif not isinstance(dg.get(campo), str):
                    errores.append(f"{campo} debe ser texto")

        if not isinstance(datos.get("servicios"), list):
            errores.append("servicios debe ser una lista")
        else:
            for i, item in enumerate(datos.get("servicios", [])):
                self._validar_item(item, ["id", "nombre", "hora_inicio", "hora_fin", "activo"], "servicios", i, errores)
            self._validar_duplicados_nombre_y_id(datos.get("servicios", []), "servicios", "servicio_", errores)

        if not isinstance(datos.get("partidas"), list):
            errores.append("partidas debe ser una lista")
        else:
            for i, item in enumerate(datos.get("partidas", [])):
                self._validar_item(item, ["id", "nombre", "orden", "activa"], "partidas", i, errores)
                if isinstance(item, dict) and not isinstance(item.get("orden"), int):
                    errores.append(f"partidas[{i}].orden debe ser entero")
            self._validar_duplicados_nombre_y_id(datos.get("partidas", []), "partidas", "partida_", errores)
            self._validar_orden_partidas(datos.get("partidas", []), errores)

        if not isinstance(datos.get("equipamiento"), list):
            errores.append("equipamiento debe ser una lista")
        else:
            for i, item in enumerate(datos.get("equipamiento", [])):
                self._validar_item(item, ["id", "nombre", "tipo", "activo"], "equipamiento", i, errores)
            self._validar_duplicados_nombre_y_id(datos.get("equipamiento", []), "equipamiento", "eq_", errores)

        if not isinstance(datos.get("almacenes"), list):
            errores.append("almacenes debe ser una lista")
        else:
            for i, item in enumerate(datos.get("almacenes", [])):
                self._validar_item(item, ["id", "nombre", "activo"], "almacenes", i, errores)
            self._validar_duplicados_nombre_y_id(datos.get("almacenes", []), "almacenes", "almacen_", errores)

        return {"ok": len(errores) == 0, "errores": errores}

    def obtener_configuracion(self) -> dict[str, Any]:
        return self.cargar_configuracion()

    def asegurar_configuracion_valida(self) -> dict[str, Any]:
        actual = self.cargar_configuracion()
        validacion = self.validar_estructura(actual)
        if not validacion["ok"]:
            actual = self._configuracion_base()
            self.guardar_configuracion(actual)
            validacion = self.validar_estructura(actual)
        return {"ok": validacion["ok"], "errores": validacion["errores"], "configuracion": actual}

    def _normalizar_configuracion(self, configuracion: dict[str, Any], resolver_conflictos: bool = False) -> dict[str, Any]:
        base = self._configuracion_base()
        out = {
            "version": str(configuracion.get("version") or base["version"]),
            "datos_generales": self._normalizar_datos_generales(configuracion.get("datos_generales") or {}),
            "servicios": self._normalizar_servicios(configuracion.get("servicios") or base["servicios"], resolver_conflictos),
            "partidas": self._normalizar_partidas(configuracion.get("partidas") or base["partidas"], resolver_conflictos),
            "equipamiento": self._normalizar_equipamiento(configuracion.get("equipamiento") or base["equipamiento"], resolver_conflictos),
            "almacenes": self._normalizar_almacenes(configuracion.get("almacenes") or base["almacenes"], resolver_conflictos),
        }
        return out

    def _normalizar_datos_generales(self, datos: dict[str, Any]) -> dict[str, str]:
        base = self._configuracion_base()["datos_generales"]
        out = {}
        for campo in ["nombre_restaurante", "direccion", "telefono", "correo_electronico", "horario_general"]:
            out[campo] = str(datos.get(campo) or base[campo]).strip()
        return out

    def _normalizar_servicios(self, items: list[Any], resolver_conflictos: bool) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        usados_id: set[str] = set()
        usados_nombre: set[str] = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            nombre = str(item.get("nombre") or "Servicio").strip()
            nombre_norm = self._normalizar_nombre(nombre)
            if resolver_conflictos and nombre_norm in usados_nombre:
                continue
            item_id = self._resolver_id_item(
                valor_actual=item.get("id"),
                nombre=nombre,
                prefijo="servicio",
                usados=usados_id,
                resolver_conflictos=resolver_conflictos,
            )
            out.append(
                {
                    "id": item_id,
                    "nombre": nombre,
                    "hora_inicio": str(item.get("hora_inicio") or "").strip(),
                    "hora_fin": str(item.get("hora_fin") or "").strip(),
                    "activo": bool(item.get("activo", True)),
                }
            )
            usados_nombre.add(nombre_norm)
        return out

    def _normalizar_partidas(self, items: list[Any], resolver_conflictos: bool) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        usados_id: set[str] = set()
        usados_nombre: set[str] = set()
        usados_orden: set[int] = set()
        for idx, item in enumerate(items, 1):
            if not isinstance(item, dict):
                continue
            nombre = str(item.get("nombre") or "Partida").strip()
            nombre_norm = self._normalizar_nombre(nombre)
            if resolver_conflictos and nombre_norm in usados_nombre:
                continue
            orden = item.get("orden", idx)
            try:
                orden_int = int(orden)
            except (TypeError, ValueError):
                orden_int = idx
            if orden_int < 1:
                orden_int = idx
            if resolver_conflictos:
                while orden_int in usados_orden:
                    orden_int += 1
            item_id = self._resolver_id_item(
                valor_actual=item.get("id"),
                nombre=nombre,
                prefijo="partida",
                usados=usados_id,
                resolver_conflictos=resolver_conflictos,
            )
            out.append(
                {
                    "id": item_id,
                    "nombre": nombre,
                    "orden": orden_int,
                    "activa": bool(item.get("activa", True)),
                }
            )
            usados_nombre.add(nombre_norm)
            usados_orden.add(orden_int)
        out.sort(key=lambda x: (int(x.get("orden", 9999)), str(x.get("nombre") or "")))
        return out

    def _normalizar_equipamiento(self, items: list[Any], resolver_conflictos: bool) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        usados_id: set[str] = set()
        usados_nombre: set[str] = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            nombre = str(item.get("nombre") or "Equipo").strip()
            nombre_norm = self._normalizar_nombre(nombre)
            if resolver_conflictos and nombre_norm in usados_nombre:
                continue
            item_id = self._resolver_id_item(
                valor_actual=item.get("id"),
                nombre=nombre,
                prefijo="eq",
                usados=usados_id,
                resolver_conflictos=resolver_conflictos,
            )
            out.append(
                {
                    "id": item_id,
                    "nombre": nombre,
                    "tipo": str(item.get("tipo") or "general").strip(),
                    "activo": bool(item.get("activo", True)),
                }
            )
            usados_nombre.add(nombre_norm)
        return out

    def _normalizar_almacenes(self, items: list[Any], resolver_conflictos: bool) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        usados_id: set[str] = set()
        usados_nombre: set[str] = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            nombre = str(item.get("nombre") or "Almacen").strip()
            nombre_norm = self._normalizar_nombre(nombre)
            if resolver_conflictos and nombre_norm in usados_nombre:
                continue
            item_id = self._resolver_id_item(
                valor_actual=item.get("id"),
                nombre=nombre,
                prefijo="almacen",
                usados=usados_id,
                resolver_conflictos=resolver_conflictos,
            )
            out.append(
                {
                    "id": item_id,
                    "nombre": nombre,
                    "activo": bool(item.get("activo", True)),
                }
            )
            usados_nombre.add(nombre_norm)
        return out

    @staticmethod
    def _normalizar_nombre(texto: Any) -> str:
        valor = str(texto or "").strip().lower()
        valor = "".join(
            c for c in unicodedata.normalize("NFD", valor)
            if unicodedata.category(c) != "Mn"
        )
        valor = re.sub(r"\s+", " ", valor)
        return valor.strip()

    def _generar_id_estable(self, nombre: str, prefijo: str) -> str:
        base = self._normalizar_nombre(nombre)
        base = re.sub(r"[^a-z0-9]+", "_", base).strip("_")
        if not base:
            base = prefijo
        if prefijo == "eq":
            return f"eq_{base}"[:64]
        return f"{prefijo}_{base}"[:64]

    def _resolver_id_item(
        self,
        valor_actual: Any,
        nombre: str,
        prefijo: str,
        usados: set[str],
        resolver_conflictos: bool,
    ) -> str:
        candidato = str(valor_actual or "").strip().lower()
        if not self._id_valido(candidato, prefijo):
            candidato = self._generar_id_estable(nombre, prefijo)
        if candidato not in usados:
            usados.add(candidato)
            return candidato
        if not resolver_conflictos:
            return candidato
        base = self._generar_id_estable(nombre, prefijo)
        n = 2
        while True:
            alt = f"{base}_{n}"[:64]
            if alt not in usados:
                usados.add(alt)
                return alt
            n += 1

    @staticmethod
    def _id_valido(valor: str, prefijo: str) -> bool:
        if not valor:
            return False
        if not re.fullmatch(r"[a-z0-9_]{3,64}", valor):
            return False
        if prefijo == "eq":
            return valor.startswith("eq_")
        return valor.startswith(f"{prefijo}_")

    @staticmethod
    def _validar_item(item: Any, campos: list[str], coleccion: str, indice: int, errores: list[str]) -> None:
        if not isinstance(item, dict):
            errores.append(f"{coleccion}[{indice}] debe ser un objeto")
            return
        for campo in campos:
            if campo not in item:
                errores.append(f"Falta {coleccion}[{indice}].{campo}")
        for campo in ["id", "nombre"]:
            if campo in item and not isinstance(item.get(campo), str):
                errores.append(f"{coleccion}[{indice}].{campo} debe ser texto")
        if "activo" in campos and "activo" in item and not isinstance(item.get("activo"), bool):
            errores.append(f"{coleccion}[{indice}].activo debe ser booleano")
        if "activa" in campos and "activa" in item and not isinstance(item.get("activa"), bool):
            errores.append(f"{coleccion}[{indice}].activa debe ser booleano")

    def _validar_duplicados_nombre_y_id(
        self,
        items: list[Any],
        coleccion: str,
        prefijo_id: str,
        errores: list[str],
    ) -> None:
        nombres_vistos: dict[str, int] = {}
        ids_vistos: dict[str, int] = {}
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            nombre = str(item.get("nombre") or "").strip()
            nombre_norm = self._normalizar_nombre(nombre)
            if not nombre_norm:
                errores.append(f"{coleccion}[{i}].nombre no puede estar vacio")
            elif nombre_norm in nombres_vistos:
                errores.append(
                    f"Nombre duplicado en {coleccion}: '{nombre}' (indices {nombres_vistos[nombre_norm]} y {i})"
                )
            else:
                nombres_vistos[nombre_norm] = i

            item_id = str(item.get("id") or "").strip().lower()
            if not item_id:
                errores.append(f"{coleccion}[{i}].id no puede estar vacio")
            else:
                if item_id in ids_vistos:
                    errores.append(
                        f"ID duplicado en {coleccion}: '{item_id}' (indices {ids_vistos[item_id]} y {i})"
                    )
                else:
                    ids_vistos[item_id] = i
                if not re.fullmatch(r"[a-z0-9_]{3,64}", item_id):
                    errores.append(f"{coleccion}[{i}].id tiene formato invalido")
                if not item_id.startswith(prefijo_id):
                    errores.append(f"{coleccion}[{i}].id debe empezar por {prefijo_id}")

    @staticmethod
    def _validar_orden_partidas(items: list[Any], errores: list[str]) -> None:
        vistos: dict[int, int] = {}
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            orden = item.get("orden")
            if not isinstance(orden, int):
                continue
            if orden < 1:
                errores.append(f"partidas[{i}].orden debe ser mayor o igual a 1")
                continue
            if orden in vistos:
                errores.append(f"Orden duplicado en partidas: {orden} (indices {vistos[orden]} y {i})")
            else:
                vistos[orden] = i

    def _configuracion_base(self) -> dict[str, Any]:
        return {
            "version": self.VERSION,
            "datos_generales": {
                "nombre_restaurante": "Restaurante Demo",
                "direccion": "",
                "telefono": "",
                "correo_electronico": "",
                "horario_general": "",
            },
            "servicios": [
                {"id": "servicio_desayuno", "nombre": "Desayuno", "hora_inicio": "", "hora_fin": "", "activo": True},
                {"id": "servicio_comida", "nombre": "Comida", "hora_inicio": "", "hora_fin": "", "activo": True},
                {"id": "servicio_cena", "nombre": "Cena", "hora_inicio": "", "hora_fin": "", "activo": True},
            ],
            "partidas": [
                {"id": "partida_frio", "nombre": "Frio", "orden": 1, "activa": True},
                {"id": "partida_caliente", "nombre": "Caliente", "orden": 2, "activa": True},
                {"id": "partida_postres", "nombre": "Postres", "orden": 3, "activa": True},
            ],
            "equipamiento": [
                {"id": "eq_horno_rational", "nombre": "Horno Rational", "tipo": "coccion", "activo": True},
                {"id": "eq_freidora", "nombre": "Freidora", "tipo": "coccion", "activo": True},
                {"id": "eq_plancha", "nombre": "Plancha", "tipo": "coccion", "activo": True},
                {"id": "eq_cocina", "nombre": "Cocina", "tipo": "coccion", "activo": True},
                {"id": "eq_abatidor", "nombre": "Abatidor", "tipo": "frio", "activo": True},
                {"id": "eq_camara_positiva", "nombre": "Camara positiva", "tipo": "almacen_frio", "activo": True},
                {"id": "eq_camara_negativa", "nombre": "Camara negativa", "tipo": "almacen_congelado", "activo": True},
            ],
            "almacenes": [
                {"id": "almacen_principal", "nombre": "Principal", "activo": True},
                {"id": "almacen_camara_positiva", "nombre": "Camara positiva", "activo": True},
                {"id": "almacen_camara_negativa", "nombre": "Camara negativa", "activo": True},
                {"id": "almacen_bodega", "nombre": "Bodega", "activo": True},
            ],
        }


__all__ = ["ServicioConfiguracionRestaurante"]
