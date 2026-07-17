from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
import json
import re
import unicodedata

from SERVICIOS.configuracion_restaurante import ServicioConfiguracionRestaurante


class ServicioRecursosRestaurante:
    """Gestiona recursos operativos del restaurante (R2)."""

    VERSION = "R2"

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self.db_dir = self.base_dir / "DATOS" / "db"
        self.ruta_configuracion = self.db_dir / "recursos_restaurante.json"

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
        validacion = self.validar_datos(normalizada)
        if not validacion["ok"]:
            normalizada = self._configuracion_base()
        self.guardar_configuracion(normalizada)
        return normalizada

    def guardar_configuracion(self, configuracion: dict[str, Any]) -> dict[str, Any]:
        self.db_dir.mkdir(parents=True, exist_ok=True)
        normalizada = self._normalizar_configuracion(configuracion, resolver_conflictos=False)
        validacion = self.validar_datos(normalizada)
        if not validacion["ok"]:
            raise ValueError("Configuracion de recursos invalida: " + " | ".join(validacion["errores"]))
        self.ruta_configuracion.write_text(
            json.dumps(normalizada, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return deepcopy(normalizada)

    def obtener_configuracion(self) -> dict[str, Any]:
        return self.cargar_configuracion()

    def asegurar_configuracion_valida(self) -> dict[str, Any]:
        actual = self.cargar_configuracion()
        validacion = self.validar_datos(actual)
        if not validacion["ok"]:
            actual = self._configuracion_base()
            self.guardar_configuracion(actual)
            validacion = self.validar_datos(actual)
        return {"ok": validacion["ok"], "errores": validacion["errores"], "configuracion": actual}

    def validar_datos(self, configuracion: dict[str, Any] | None = None) -> dict[str, Any]:
        datos = configuracion if isinstance(configuracion, dict) else self._configuracion_base()
        errores: list[str] = []

        if not isinstance(datos.get("version"), str) or not str(datos.get("version", "")).strip():
            errores.append("version debe ser un texto no vacio")

        roles = datos.get("roles")
        if not isinstance(roles, list):
            errores.append("roles debe ser una lista")
            roles = []

        turnos = datos.get("turnos")
        if not isinstance(turnos, list):
            errores.append("turnos debe ser una lista")
            turnos = []

        personal = datos.get("personal")
        if not isinstance(personal, list):
            errores.append("personal debe ser una lista")
            personal = []

        capacidades = datos.get("capacidades")
        if not isinstance(capacidades, dict):
            errores.append("capacidades debe ser un objeto")
            capacidades = {}

        self._validar_catalogo(roles, "roles", "rol_", errores)
        self._validar_catalogo(turnos, "turnos", "turno_", errores)

        partidas_ids, _partidas_nombre = self._catalogo_partidas_r1()
        roles_ids = {str(r.get("id") or "").strip().lower() for r in roles if isinstance(r, dict)}

        nombres_personal: dict[str, int] = {}
        ids_personal: dict[str, int] = {}
        for i, item in enumerate(personal):
            if not isinstance(item, dict):
                errores.append(f"personal[{i}] debe ser un objeto")
                continue

            for campo in ["id", "nombre", "rol", "partidas", "activo"]:
                if campo not in item:
                    errores.append(f"Falta personal[{i}].{campo}")

            nombre = str(item.get("nombre") or "").strip()
            nombre_norm = self._normalizar_nombre(nombre)
            if not nombre_norm:
                errores.append(f"personal[{i}].nombre es obligatorio")
            elif nombre_norm in nombres_personal:
                errores.append(
                    f"Nombre duplicado en personal: '{nombre}' (indices {nombres_personal[nombre_norm]} y {i})"
                )
            else:
                nombres_personal[nombre_norm] = i

            persona_id = str(item.get("id") or "").strip().lower()
            if not self._id_valido(persona_id, "persona"):
                errores.append(f"personal[{i}].id tiene formato invalido")
            elif persona_id in ids_personal:
                errores.append(
                    f"ID duplicado en personal: '{persona_id}' (indices {ids_personal[persona_id]} y {i})"
                )
            else:
                ids_personal[persona_id] = i

            rol_id = str(item.get("rol") or "").strip().lower()
            if not rol_id:
                errores.append(f"personal[{i}].rol es obligatorio")
            elif rol_id not in roles_ids:
                errores.append(f"personal[{i}].rol no existe: {rol_id}")

            partidas = item.get("partidas")
            if not isinstance(partidas, list):
                errores.append(f"personal[{i}].partidas debe ser una lista")
            else:
                if not partidas:
                    errores.append(f"personal[{i}].partidas no puede estar vacia")
                repetidas: set[str] = set()
                vistas: set[str] = set()
                for pid_raw in partidas:
                    pid = str(pid_raw or "").strip().lower()
                    if not pid:
                        errores.append(f"personal[{i}].partidas contiene un id vacio")
                        continue
                    if pid in vistas:
                        repetidas.add(pid)
                    vistas.add(pid)
                    if pid not in partidas_ids:
                        errores.append(f"personal[{i}].partidas contiene partida no existente: {pid}")
                for dup in sorted(repetidas):
                    errores.append(f"personal[{i}].partidas contiene partida repetida: {dup}")

            if not isinstance(item.get("activo"), bool):
                errores.append(f"personal[{i}].activo debe ser booleano")

        for campo in [
            "cocineros_simultaneos",
            "produccion_maxima_turno",
            "elaboraciones_simultaneas",
        ]:
            valor = capacidades.get(campo)
            if not isinstance(valor, (int, float)):
                errores.append(f"capacidades.{campo} debe ser numerico")
                continue
            if float(valor) <= 0:
                errores.append(f"capacidades.{campo} debe ser mayor que cero")

        return {"ok": len(errores) == 0, "errores": errores}

    def esta_partida_en_uso(self, partida_id: str) -> bool:
        pid = str(partida_id or "").strip().lower()
        if not pid:
            return False
        cfg = self.obtener_configuracion()
        for persona in list(cfg.get("personal") or []):
            if not isinstance(persona, dict):
                continue
            partidas = list(persona.get("partidas") or [])
            if pid in {str(x or "").strip().lower() for x in partidas}:
                return True
        return False

    def _normalizar_configuracion(self, configuracion: dict[str, Any], resolver_conflictos: bool) -> dict[str, Any]:
        base = self._configuracion_base()
        roles = self._normalizar_catalogo(
            configuracion.get("roles") or base["roles"],
            prefijo="rol",
            etiqueta_defecto="Rol",
            resolver_conflictos=resolver_conflictos,
        )
        turnos = self._normalizar_catalogo(
            configuracion.get("turnos") or base["turnos"],
            prefijo="turno",
            etiqueta_defecto="Turno",
            resolver_conflictos=resolver_conflictos,
        )
        partidas_ids, partidas_por_nombre = self._catalogo_partidas_r1()
        personal = self._normalizar_personal(
            configuracion.get("personal") or base["personal"],
            roles=roles,
            partidas_ids=partidas_ids,
            partidas_por_nombre=partidas_por_nombre,
            resolver_conflictos=resolver_conflictos,
        )
        return {
            "version": str(configuracion.get("version") or base["version"]),
            "roles": roles,
            "turnos": turnos,
            "personal": personal,
            "capacidades": self._normalizar_capacidades(
                configuracion.get("capacidades") or base["capacidades"],
                resolver_conflictos,
            ),
        }

    def _normalizar_catalogo(
        self,
        items: list[Any],
        prefijo: str,
        etiqueta_defecto: str,
        resolver_conflictos: bool,
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        usados_id: set[str] = set()
        usados_nombre: set[str] = set()
        for item in items:
            if isinstance(item, str):
                raw = {"nombre": item, "activo": True}
            elif isinstance(item, dict):
                raw = item
            else:
                continue

            nombre = str(raw.get("nombre") or etiqueta_defecto).strip()
            nombre_norm = self._normalizar_nombre(nombre)
            if resolver_conflictos and nombre_norm in usados_nombre:
                continue

            item_id = self._resolver_id_item(
                valor_actual=raw.get("id"),
                nombre=nombre,
                prefijo=prefijo,
                usados=usados_id,
                resolver_conflictos=resolver_conflictos,
            )
            out.append(
                {
                    "id": item_id,
                    "nombre": nombre,
                    "activo": bool(raw.get("activo", True)),
                }
            )
            usados_nombre.add(nombre_norm)
        return out

    def _normalizar_personal(
        self,
        items: list[Any],
        roles: list[dict[str, Any]],
        partidas_ids: set[str],
        partidas_por_nombre: dict[str, str],
        resolver_conflictos: bool,
    ) -> list[dict[str, Any]]:
        roles_por_nombre = {
            self._normalizar_nombre(r.get("nombre")): str(r.get("id") or "").strip().lower()
            for r in roles
            if isinstance(r, dict)
        }
        roles_ids = {str(r.get("id") or "").strip().lower() for r in roles if isinstance(r, dict)}

        out: list[dict[str, Any]] = []
        usados_id: set[str] = set()
        usados_nombre: set[str] = set()

        for item in items:
            if not isinstance(item, dict):
                continue

            nombre = str(item.get("nombre") or "").strip()
            nombre_norm = self._normalizar_nombre(nombre)
            if resolver_conflictos and nombre_norm in usados_nombre:
                continue

            rol_raw = str(item.get("rol") or "").strip()
            rol_id = rol_raw.lower()
            if rol_id not in roles_ids:
                rol_id = roles_por_nombre.get(self._normalizar_nombre(rol_raw), rol_id)

            partidas_out: list[str] = []
            partidas_vistas: set[str] = set()

            partidas_in = item.get("partidas")
            if isinstance(partidas_in, list):
                fuentes_partidas = [str(x or "").strip() for x in partidas_in]
            else:
                # Migracion segura desde formato antiguo "partida": "partida_frio"
                fuentes_partidas = [str(item.get("partida") or "").strip()] if str(item.get("partida") or "").strip() else []

            for partida_raw in fuentes_partidas:
                partida_id = partida_raw.lower()
                if partida_id not in partidas_ids:
                    partida_id = partidas_por_nombre.get(self._normalizar_nombre(partida_raw), partida_id)
                if not partida_id:
                    continue
                if partida_id in partidas_vistas:
                    continue
                partidas_vistas.add(partida_id)
                partidas_out.append(partida_id)

            if resolver_conflictos and not partidas_out and partidas_ids:
                # Fallback de migracion para no perder persona por dato incompleto.
                partidas_out = [sorted(partidas_ids)[0]]

            persona_id = self._resolver_id_item(
                valor_actual=item.get("id"),
                nombre=nombre,
                prefijo="persona",
                usados=usados_id,
                resolver_conflictos=resolver_conflictos,
            )

            out.append(
                {
                    "id": persona_id,
                    "nombre": nombre,
                    "rol": rol_id,
                    "partidas": partidas_out,
                    "activo": bool(item.get("activo", True)),
                }
            )
            usados_nombre.add(nombre_norm)

        return out

    def _normalizar_capacidades(self, capacidades: dict[str, Any], resolver_conflictos: bool) -> dict[str, Any]:
        base = self._configuracion_base()["capacidades"]
        out: dict[str, Any] = {}
        for campo in [
            "cocineros_simultaneos",
            "produccion_maxima_turno",
            "elaboraciones_simultaneas",
        ]:
            valor = capacidades.get(campo, base[campo])
            out[campo] = self._coaccion_numerica(valor, base[campo], resolver_conflictos)
        return out

    @staticmethod
    def _coaccion_numerica(valor: Any, defecto: int, resolver_conflictos: bool) -> Any:
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            return defecto if resolver_conflictos else valor
        if numero <= 0:
            return defecto if resolver_conflictos else numero
        if int(numero) == numero:
            return int(numero)
        return numero

    def _catalogo_partidas_r1(self) -> tuple[set[str], dict[str, str]]:
        config_r1 = ServicioConfiguracionRestaurante(self.base_dir).obtener_configuracion()
        partidas = list(config_r1.get("partidas") or [])
        ids = {str(p.get("id") or "").strip().lower() for p in partidas if isinstance(p, dict)}
        por_nombre = {
            self._normalizar_nombre(p.get("nombre")): str(p.get("id") or "").strip().lower()
            for p in partidas
            if isinstance(p, dict)
        }
        return ids, por_nombre

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
        return valor.startswith(f"{prefijo}_")

    def _validar_catalogo(self, items: list[Any], coleccion: str, prefijo_id: str, errores: list[str]) -> None:
        nombres_vistos: dict[str, int] = {}
        ids_vistos: dict[str, int] = {}
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                errores.append(f"{coleccion}[{i}] debe ser un objeto")
                continue
            for campo in ["id", "nombre", "activo"]:
                if campo not in item:
                    errores.append(f"Falta {coleccion}[{i}].{campo}")

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

            if not isinstance(item.get("activo"), bool):
                errores.append(f"{coleccion}[{i}].activo debe ser booleano")

    def _configuracion_base(self) -> dict[str, Any]:
        return {
            "version": self.VERSION,
            "roles": [
                {"id": "rol_jefe_cocina", "nombre": "Jefe de cocina", "activo": True},
                {"id": "rol_cocinero", "nombre": "Cocinero", "activo": True},
                {"id": "rol_ayudante", "nombre": "Ayudante", "activo": True},
                {"id": "rol_pastelero", "nombre": "Pastelero", "activo": True},
                {"id": "rol_office", "nombre": "Office", "activo": True},
            ],
            "turnos": [
                {"id": "turno_manana", "nombre": "Manana", "activo": True},
                {"id": "turno_partido", "nombre": "Partido", "activo": True},
                {"id": "turno_tarde", "nombre": "Tarde", "activo": True},
            ],
            "personal": [],
            "capacidades": {
                "cocineros_simultaneos": 3,
                "produccion_maxima_turno": 120,
                "elaboraciones_simultaneas": 6,
            },
        }


__all__ = ["ServicioRecursosRestaurante"]
