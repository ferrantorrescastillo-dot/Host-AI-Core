from __future__ import annotations

from typing import Any
import json

from SERVICIOS.configuracion_restaurante import ServicioConfiguracionRestaurante
from SERVICIOS.recursos_restaurante import ServicioRecursosRestaurante


class ConsolaConfiguracionRestaurante:
    def __init__(self, base_dir: Any):
        self.base_dir = base_dir
        self.servicio = ServicioConfiguracionRestaurante(base_dir)
        self.servicio_recursos = ServicioRecursosRestaurante(base_dir)
        self.servicio.asegurar_configuracion_valida()
        self.servicio_recursos.asegurar_configuracion_valida()

    def ejecutar(self) -> None:
        while True:
            print("\nCONFIGURACION DEL RESTAURANTE")
            print("1. Ver configuracion")
            print("2. Datos generales")
            print("3. Servicios")
            print("4. Partidas")
            print("5. Equipamiento")
            print("6. Almacenes")
            print("7. Recursos Operativos")
            print("0. Volver")
            opcion = input("Elige una opcion: ").strip()

            if opcion == "1":
                self._ver_configuracion()
            elif opcion == "2":
                self._editar_datos_generales()
            elif opcion == "3":
                self._editar_servicios()
            elif opcion == "4":
                self._editar_partidas()
            elif opcion == "5":
                self._editar_equipamiento()
            elif opcion == "6":
                self._editar_almacenes()
            elif opcion == "7":
                self._menu_recursos_operativos()
            elif opcion == "0":
                return
            else:
                print("Opcion no valida.")

    def _ver_configuracion(self) -> None:
        config = self.servicio.obtener_configuracion()
        print(json.dumps(config, ensure_ascii=False, indent=2))

    def _editar_datos_generales(self) -> None:
        config = self.servicio.obtener_configuracion()
        datos = dict(config.get("datos_generales") or {})
        campos = [
            ("nombre_restaurante", "Nombre del restaurante"),
            ("direccion", "Direccion"),
            ("telefono", "Telefono"),
            ("correo_electronico", "Correo electronico"),
            ("horario_general", "Horario general"),
        ]
        print("\nDATOS GENERALES")
        for clave, etiqueta in campos:
            actual = str(datos.get(clave) or "")
            nuevo = input(f"{etiqueta} [{actual}]: ").strip()
            if nuevo:
                datos[clave] = nuevo
        config["datos_generales"] = datos
        self.servicio.guardar_configuracion(config)
        print("Datos generales actualizados.")

    def _editar_servicios(self) -> None:
        self._menu_coleccion(
            clave="servicios",
            titulo="SERVICIOS",
            campos=["nombre", "hora_inicio", "hora_fin", "activo"],
            campo_activo="activo",
        )

    def _editar_partidas(self) -> None:
        self._menu_coleccion(
            clave="partidas",
            titulo="PARTIDAS",
            campos=["nombre", "orden", "activa"],
            campo_activo="activa",
        )

    def _editar_equipamiento(self) -> None:
        self._menu_coleccion(
            clave="equipamiento",
            titulo="EQUIPAMIENTO",
            campos=["nombre", "tipo", "activo"],
            campo_activo="activo",
        )

    def _editar_almacenes(self) -> None:
        self._menu_coleccion(
            clave="almacenes",
            titulo="ALMACENES",
            campos=["nombre", "activo"],
            campo_activo="activo",
        )

    def _menu_coleccion(self, clave: str, titulo: str, campos: list[str], campo_activo: str) -> None:
        while True:
            config = self.servicio.obtener_configuracion()
            items = list(config.get(clave) or [])
            print(f"\n{titulo}")
            if not items:
                print("(sin elementos)")
            for i, item in enumerate(items, 1):
                print(f"{i}. {self._formatear_item(item, ["id", *campos])}")
            print("A. Anadir")
            print("E. Editar")
            print("T. Activar/desactivar")
            print("X. Eliminar")
            if clave == "partidas":
                print("R. Reordenar")
            print("0. Volver")
            op = input("Elige una opcion: ").strip().lower()

            if op == "0":
                return
            if op == "a":
                nuevo = self._crear_item(campos, len(items) + 1, clave)
                if clave == "partidas" and self._orden_ocupado_partidas(items, int(nuevo.get("orden", 0) or 0)):
                    print("No se puede anadir la partida: el orden ya esta ocupado. Elige otro orden.")
                    continue
                items.append(nuevo)
                config[clave] = items
                if self._guardar_configuracion(config):
                    print("Elemento anadido.")
                continue
            if op == "e":
                indice = self._seleccionar_indice(items)
                if indice is None:
                    continue
                actualizado = self._editar_item(items[indice], campos)
                if clave == "partidas":
                    orden = int(actualizado.get("orden", 0) or 0)
                    if self._orden_ocupado_partidas(items, orden, indice_excluir=indice):
                        print("No se puede actualizar la partida: el orden ya esta ocupado. Elige otro orden.")
                        continue
                items[indice] = actualizado
                config[clave] = items
                if self._guardar_configuracion(config):
                    print("Elemento actualizado.")
                continue
            if op == "t":
                indice = self._seleccionar_indice(items)
                if indice is None:
                    continue
                actual = bool(items[indice].get(campo_activo, True))
                items[indice][campo_activo] = not actual
                config[clave] = items
                if self._guardar_configuracion(config):
                    print("Estado actualizado.")
                continue
            if op == "x":
                indice = self._seleccionar_indice(items)
                if indice is None:
                    continue
                if clave == "partidas":
                    partida_id = str(items[indice].get("id") or "")
                    if self.servicio_recursos.esta_partida_en_uso(partida_id):
                        print("No se puede eliminar la partida: esta asignada a personal en Recursos Operativos.")
                        continue
                borrado = items.pop(indice)
                config[clave] = items
                if self._guardar_configuracion(config):
                    print(f"Elemento eliminado: {borrado.get('nombre') or borrado.get('id')}")
                continue
            if op == "r" and clave == "partidas":
                if not items:
                    print("No hay partidas para reordenar.")
                    continue
                origen = self._seleccionar_indice(items, mensaje="Indice de partida a mover")
                if origen is None:
                    continue
                destino = self._seleccionar_indice(items, mensaje="Nuevo indice")
                if destino is None:
                    continue
                item = items.pop(origen)
                items.insert(destino, item)
                for idx, actual in enumerate(items, 1):
                    actual["orden"] = idx
                config[clave] = items
                if self._guardar_configuracion(config):
                    print("Orden actualizado.")
                continue
            print("Opcion no valida.")

    @staticmethod
    def _seleccionar_indice(items: list[dict[str, Any]], mensaje: str = "Indice") -> int | None:
        if not items:
            print("No hay elementos.")
            return None
        valor = input(f"{mensaje} (1-{len(items)}): ").strip()
        if not valor.isdigit():
            print("Seleccion no valida.")
            return None
        indice = int(valor) - 1
        if not 0 <= indice < len(items):
            print("Seleccion fuera de rango.")
            return None
        return indice

    @staticmethod
    def _formatear_item(item: dict[str, Any], campos: list[str]) -> str:
        partes = []
        for campo in campos:
            partes.append(f"{campo}={item.get(campo)}")
        return " | ".join(partes)

    @staticmethod
    def _valor_tipeado(campo: str, valor: str, por_defecto: Any) -> Any:
        if campo in {"activo", "activa"}:
            if not valor:
                return bool(por_defecto)
            return valor.strip().lower() in {"1", "s", "si", "sí", "true", "t", "y", "yes"}
        if campo == "orden":
            if not valor:
                try:
                    return int(por_defecto)
                except (TypeError, ValueError):
                    return 1
            try:
                return int(valor)
            except ValueError:
                return 1
        if not valor:
            return str(por_defecto)
        return valor.strip()

    def _crear_item(self, campos: list[str], numero: int, prefijo: str) -> dict[str, Any]:
        out: dict[str, Any] = {}
        defaults: dict[str, Any] = {"nombre": f"{prefijo.capitalize()} {numero}", "activo": True, "activa": True, "orden": numero, "hora_inicio": "", "hora_fin": "", "tipo": "general"}
        for campo in campos:
            base = defaults.get(campo, "")
            valor = input(f"{campo} [{base}]: ").strip()
            out[campo] = self._valor_tipeado(campo, valor, base)
        return out

    def _editar_item(self, item: dict[str, Any], campos: list[str]) -> dict[str, Any]:
        out = dict(item)
        for campo in campos:
            actual = out.get(campo)
            valor = input(f"{campo} [{actual}]: ").strip()
            out[campo] = self._valor_tipeado(campo, valor, actual)
        return out

    @staticmethod
    def _orden_ocupado_partidas(items: list[dict[str, Any]], orden: int, indice_excluir: int | None = None) -> bool:
        if orden < 1:
            return True
        for i, item in enumerate(items):
            if indice_excluir is not None and i == indice_excluir:
                continue
            if int(item.get("orden", 0) or 0) == orden:
                return True
        return False

    def _guardar_configuracion(self, config: dict[str, Any]) -> bool:
        try:
            self.servicio.guardar_configuracion(config)
            return True
        except ValueError as exc:
            print(str(exc))
            print("No se han guardado cambios.")
            return False

    def _menu_recursos_operativos(self) -> None:
        while True:
            print("\nRECURSOS OPERATIVOS")
            print("1. Personal")
            print("2. Roles")
            print("3. Turnos")
            print("4. Capacidades")
            print("0. Volver")
            op = input("Elige una opcion: ").strip()
            if op == "1":
                self._menu_personal()
            elif op == "2":
                self._menu_roles()
            elif op == "3":
                self._menu_turnos()
            elif op == "4":
                self._menu_capacidades()
            elif op == "0":
                return
            else:
                print("Opcion no valida.")

    def _menu_personal(self) -> None:
        while True:
            cfg = self.servicio_recursos.obtener_configuracion()
            personal = list(cfg.get("personal") or [])
            roles = {str(r.get("id") or ""): str(r.get("nombre") or "") for r in list(cfg.get("roles") or []) if isinstance(r, dict)}
            partidas_cfg = list((self.servicio.obtener_configuracion().get("partidas") or []))
            partidas = {str(p.get("id") or ""): str(p.get("nombre") or "") for p in partidas_cfg if isinstance(p, dict)}
            print("\nPERSONAL")
            if not personal:
                print("(sin personal)")
            for i, item in enumerate(personal, 1):
                partidas_txt = ", ".join(partidas.get(str(pid), str(pid)) for pid in list(item.get("partidas") or []))
                print(
                    f"{i}. id={item.get('id')} | nombre={item.get('nombre')} | "
                    f"rol={roles.get(str(item.get('rol') or ''), item.get('rol'))} | partidas={partidas_txt or '-'} | activo={item.get('activo')}"
                )
            print("A. Anadir")
            print("E. Editar")
            print("T. Activar/desactivar")
            print("X. Eliminar")
            print("0. Volver")
            op = input("Elige una opcion: ").strip().lower()
            if op == "0":
                return
            if op == "a":
                nuevo = self._crear_persona(cfg)
                if nuevo is None:
                    continue
                personal.append(nuevo)
                cfg["personal"] = personal
                if self._guardar_recursos(cfg):
                    print("Persona anadida.")
                continue
            if op == "e":
                idx = self._seleccionar_indice(personal)
                if idx is None:
                    continue
                editado = self._editar_persona(cfg, personal[idx])
                if editado is None:
                    continue
                personal[idx] = editado
                cfg["personal"] = personal
                if self._guardar_recursos(cfg):
                    print("Persona actualizada.")
                continue
            if op == "t":
                idx = self._seleccionar_indice(personal)
                if idx is None:
                    continue
                personal[idx]["activo"] = not bool(personal[idx].get("activo", True))
                cfg["personal"] = personal
                if self._guardar_recursos(cfg):
                    print("Estado actualizado.")
                continue
            if op == "x":
                idx = self._seleccionar_indice(personal)
                if idx is None:
                    continue
                borrada = personal.pop(idx)
                cfg["personal"] = personal
                if self._guardar_recursos(cfg):
                    print(f"Persona eliminada: {borrada.get('nombre')}")
                continue
            print("Opcion no valida.")

    def _menu_roles(self) -> None:
        while True:
            cfg = self.servicio_recursos.obtener_configuracion()
            roles = list(cfg.get("roles") or [])
            personal = list(cfg.get("personal") or [])
            print("\nROLES")
            for i, item in enumerate(roles, 1):
                print(f"{i}. id={item.get('id')} | nombre={item.get('nombre')} | activo={item.get('activo')}")
            print("A. Anadir")
            print("E. Editar")
            print("X. Eliminar")
            print("0. Volver")
            op = input("Elige una opcion: ").strip().lower()
            if op == "0":
                return
            if op == "a":
                nombre = input("Nombre del rol: ").strip()
                if not nombre:
                    print("El nombre es obligatorio.")
                    continue
                roles.append({"nombre": nombre, "activo": True})
                cfg["roles"] = roles
                if self._guardar_recursos(cfg):
                    print("Rol anadido.")
                continue
            if op == "e":
                idx = self._seleccionar_indice(roles)
                if idx is None:
                    continue
                nombre = input(f"Nombre [{roles[idx].get('nombre')}]: ").strip()
                if nombre:
                    roles[idx]["nombre"] = nombre
                cfg["roles"] = roles
                if self._guardar_recursos(cfg):
                    print("Rol actualizado.")
                continue
            if op == "x":
                idx = self._seleccionar_indice(roles)
                if idx is None:
                    continue
                rol_id = str(roles[idx].get("id") or "")
                if any(str(p.get("rol") or "") == rol_id for p in personal):
                    print("No se puede eliminar: el rol esta siendo utilizado por personal.")
                    continue
                eliminado = roles.pop(idx)
                cfg["roles"] = roles
                if self._guardar_recursos(cfg):
                    print(f"Rol eliminado: {eliminado.get('nombre')}")
                continue
            print("Opcion no valida.")

    def _menu_turnos(self) -> None:
        while True:
            cfg = self.servicio_recursos.obtener_configuracion()
            turnos = list(cfg.get("turnos") or [])
            print("\nTURNOS")
            for i, item in enumerate(turnos, 1):
                print(f"{i}. id={item.get('id')} | nombre={item.get('nombre')} | activo={item.get('activo')}")
            print("A. Anadir")
            print("E. Editar")
            print("X. Eliminar")
            print("0. Volver")
            op = input("Elige una opcion: ").strip().lower()
            if op == "0":
                return
            if op == "a":
                nombre = input("Nombre del turno: ").strip()
                if not nombre:
                    print("El nombre es obligatorio.")
                    continue
                turnos.append({"nombre": nombre, "activo": True})
                cfg["turnos"] = turnos
                if self._guardar_recursos(cfg):
                    print("Turno anadido.")
                continue
            if op == "e":
                idx = self._seleccionar_indice(turnos)
                if idx is None:
                    continue
                nombre = input(f"Nombre [{turnos[idx].get('nombre')}]: ").strip()
                if nombre:
                    turnos[idx]["nombre"] = nombre
                cfg["turnos"] = turnos
                if self._guardar_recursos(cfg):
                    print("Turno actualizado.")
                continue
            if op == "x":
                idx = self._seleccionar_indice(turnos)
                if idx is None:
                    continue
                eliminado = turnos.pop(idx)
                cfg["turnos"] = turnos
                if self._guardar_recursos(cfg):
                    print(f"Turno eliminado: {eliminado.get('nombre')}")
                continue
            print("Opcion no valida.")

    def _menu_capacidades(self) -> None:
        cfg = self.servicio_recursos.obtener_configuracion()
        capacidades = dict(cfg.get("capacidades") or {})
        print("\nCAPACIDADES")
        for campo in [
            "cocineros_simultaneos",
            "produccion_maxima_turno",
            "elaboraciones_simultaneas",
        ]:
            actual = capacidades.get(campo)
            valor = input(f"{campo} [{actual}]: ").strip()
            if not valor:
                continue
            try:
                numero = float(valor)
                capacidades[campo] = int(numero) if int(numero) == numero else numero
            except ValueError:
                capacidades[campo] = valor
        cfg["capacidades"] = capacidades
        if self._guardar_recursos(cfg):
            print("Capacidades actualizadas.")

    def _crear_persona(self, cfg: dict[str, Any]) -> dict[str, Any] | None:
        nombre = input("Nombre: ").strip()
        if not nombre:
            print("El nombre es obligatorio.")
            return None
        rol_id = self._seleccionar_rol(cfg)
        if not rol_id:
            return None
        partidas_ids = self._seleccionar_partidas_multiples()
        if not partidas_ids:
            return None
        return {
            "nombre": nombre,
            "rol": rol_id,
            "partidas": partidas_ids,
            "activo": True,
        }

    def _editar_persona(self, cfg: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any] | None:
        out = dict(actual)
        nombre = input(f"Nombre [{out.get('nombre')}]: ").strip()
        if nombre:
            out["nombre"] = nombre

        cambiar_rol = input("Cambiar rol? (s/n) [n]: ").strip().lower()
        if cambiar_rol in {"s", "si", "sí"}:
            rol_id = self._seleccionar_rol(cfg)
            if not rol_id:
                return None
            out["rol"] = rol_id

        cambiar_partidas = input("Cambiar partidas? (s/n) [n]: ").strip().lower()
        if cambiar_partidas in {"s", "si", "sí"}:
            partidas_ids = self._seleccionar_partidas_multiples()
            if not partidas_ids:
                return None
            out["partidas"] = partidas_ids
        return out

    def _seleccionar_rol(self, cfg: dict[str, Any]) -> str | None:
        roles = list(cfg.get("roles") or [])
        if not roles:
            print("No hay roles configurados.")
            return None
        print("Roles disponibles:")
        for i, rol in enumerate(roles, 1):
            print(f"{i}. {rol.get('nombre')} ({rol.get('id')})")
        idx = self._seleccionar_indice(roles, "Indice de rol")
        if idx is None:
            return None
        return str(roles[idx].get("id") or "")

    def _seleccionar_partida(self) -> str | None:
        cfg = self.servicio.obtener_configuracion()
        partidas = list(cfg.get("partidas") or [])
        if not partidas:
            print("No hay partidas configuradas en R1.")
            return None
        print("Partidas disponibles:")
        for i, partida in enumerate(partidas, 1):
            print(f"{i}. {partida.get('nombre')} ({partida.get('id')})")
        idx = self._seleccionar_indice(partidas, "Indice de partida")
        if idx is None:
            return None
        return str(partidas[idx].get("id") or "")

    def _seleccionar_partidas_multiples(self) -> list[str] | None:
        cfg = self.servicio.obtener_configuracion()
        partidas = list(cfg.get("partidas") or [])
        if not partidas:
            print("No hay partidas configuradas en R1.")
            return None
        print("\nPARTIDAS DISPONIBLES")
        for i, partida in enumerate(partidas, 1):
            print(f"{i}. {partida.get('nombre')}")
        print("A. Todas")
        print("Selecciona una o varias partidas separadas por comas.")
        print("Ejemplo: 1,2")
        bruto = input("Seleccion: ").strip()
        if not bruto:
            print("Debes seleccionar al menos una partida.")
            return None

        if bruto.lower() == "a":
            return [str(p.get("id") or "") for p in partidas if str(p.get("id") or "")]

        tokens = [t.strip() for t in bruto.split(",") if t.strip()]
        if not tokens:
            print("Debes seleccionar al menos una partida.")
            return None

        seleccion: list[str] = []
        vistos: set[str] = set()
        for token in tokens:
            if not token.isdigit():
                print(f"Seleccion invalida: {token}")
                return None
            idx = int(token)
            if not 1 <= idx <= len(partidas):
                print(f"Seleccion fuera de rango: {token}")
                return None
            partida_id = str(partidas[idx - 1].get("id") or "")
            if partida_id and partida_id not in vistos:
                vistos.add(partida_id)
                seleccion.append(partida_id)

        if not seleccion:
            print("Debes seleccionar al menos una partida.")
            return None
        return seleccion

    def _guardar_recursos(self, config: dict[str, Any]) -> bool:
        try:
            self.servicio_recursos.guardar_configuracion(config)
            return True
        except ValueError as exc:
            print(str(exc))
            print("No se han guardado cambios.")
            return False


__all__ = ["ConsolaConfiguracionRestaurante"]
