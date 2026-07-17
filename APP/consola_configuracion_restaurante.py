from __future__ import annotations

from typing import Any
import json

from SERVICIOS.configuracion_restaurante import ServicioConfiguracionRestaurante


class ConsolaConfiguracionRestaurante:
    def __init__(self, base_dir: Any):
        self.servicio = ServicioConfiguracionRestaurante(base_dir)
        self.servicio.asegurar_configuracion_valida()

    def ejecutar(self) -> None:
        while True:
            print("\nCONFIGURACION DEL RESTAURANTE")
            print("1. Ver configuracion")
            print("2. Datos generales")
            print("3. Servicios")
            print("4. Partidas")
            print("5. Equipamiento")
            print("6. Almacenes")
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


__all__ = ["ConsolaConfiguracionRestaurante"]
