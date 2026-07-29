from __future__ import annotations

from pathlib import Path
from typing import Any


TIPO_PRODUCTO_INEXISTENTE = "PRODUCTO_INEXISTENTE"
TIPO_PRODUCTO_SIN_PRECIO = "PRODUCTO_SIN_PRECIO"
TIPO_PRODUCTO_DUPLICADO = "PRODUCTO_DUPLICADO"
TIPO_INGREDIENTE_SIN_CANTIDAD = "INGREDIENTE_SIN_CANTIDAD"
TIPO_PROVEEDOR_INEXISTENTE = "PROVEEDOR_INEXISTENTE"
TIPO_RECETA_INCOMPLETA = "RECETA_INCOMPLETA"
TIPO_UNIDAD_DESCONOCIDA = "UNIDAD_DESCONOCIDA"
TIPO_RECETA_INEXISTENTE = "RECETA_INEXISTENTE"
TIPO_CANTIDAD_AUSENTE = "CANTIDAD_AUSENTE"
TIPO_MERMA_INVALIDA = "MERMA_INVALIDA"
TIPO_COSTE_IMPORTADO_DISCREPANTE = "COSTE_IMPORTADO_DISCREPANTE"

ESTADO_PENDIENTE = "PENDIENTE"
ESTADO_RESUELTA = "RESUELTA"


class AsistenteResolucionIncidencias601:
    """Asistente interactivo de resolución desacoplado del origen de importación."""

    def __init__(self, repositorio_centro: Any, base_dir: Path):
        self.repo = repositorio_centro
        self.base_dir = Path(base_dir).resolve()

    def resolver(self, contexto: dict[str, Any]) -> dict[str, Any]:
        incidencias = list(contexto.get("incidencias") or [])
        acciones = {
            "productos_nuevos": 0,
            "precios_añadidos": 0,
            "proveedores_nuevos": 0,
        }

        if not incidencias:
            return {"incidencias": incidencias, "acciones": acciones}

        print("\nResolver incidencias ahora")
        resolver_ahora = input("Sí/No: ").strip().lower()
        if resolver_ahora not in {"si", "sí", "s", "yes", "y"}:
            return {"incidencias": incidencias, "acciones": acciones}

        for incidencia in incidencias:
            tipo = str(incidencia.get("tipo") or "").upper()
            if tipo == TIPO_PRODUCTO_INEXISTENTE:
                self._resolver_producto_inexistente(incidencia, acciones)
            elif tipo == TIPO_PRODUCTO_SIN_PRECIO:
                self._resolver_producto_sin_precio(incidencia, acciones)
            elif tipo == TIPO_PRODUCTO_DUPLICADO:
                self._resolver_producto_duplicado(incidencia)
            elif tipo == TIPO_INGREDIENTE_SIN_CANTIDAD:
                self._resolver_ingrediente_sin_cantidad(incidencia, contexto)
            elif tipo == TIPO_PROVEEDOR_INEXISTENTE:
                self._resolver_proveedor_inexistente(incidencia, acciones)
            elif tipo == TIPO_RECETA_INCOMPLETA:
                self._resolver_receta_incompleta(incidencia, contexto)
            elif tipo == TIPO_UNIDAD_DESCONOCIDA:
                self._resolver_unidad_desconocida(incidencia, contexto)
            elif tipo == TIPO_RECETA_INEXISTENTE:
                self._resolver_receta_inexistente(incidencia, contexto)
            elif tipo == TIPO_CANTIDAD_AUSENTE:
                self._resolver_cantidad_ausente(incidencia, contexto)
            elif tipo == TIPO_MERMA_INVALIDA:
                self._resolver_merma_invalida(incidencia, contexto)
            elif tipo == TIPO_COSTE_IMPORTADO_DISCREPANTE:
                self._resolver_coste_discrepante(incidencia, contexto)
            else:
                incidencia["estado"] = str(incidencia.get("estado") or ESTADO_PENDIENTE)

        return {"incidencias": incidencias, "acciones": acciones}

    def _resolver_producto_inexistente(self, incidencia: dict[str, Any], acciones: dict[str, int]) -> None:
        producto = str(incidencia.get("producto") or "Producto sin nombre")
        print("\nProducto inexistente")
        print(f"Producto: {producto}")
        print("¿Qué deseas hacer?")
        print("1. Crear producto nuevo")
        print("2. Relacionarlo con un producto existente")
        print("3. Dejar pendiente")
        op = input("Elige una opción: ").strip()

        if op == "1":
            data = self._pedir_datos_producto(producto)
            creado = self.repo.crear_producto(data)
            producto_id = creado.get("codigo") or creado.get("id")
            incidencia["estado"] = ESTADO_RESUELTA
            incidencia["resolucion"] = f"Producto creado: {producto_id}"
            incidencia["producto_relacionado_id"] = producto_id
            acciones["productos_nuevos"] += 1
        elif op == "2":
            elegido = self._seleccionar_producto_existente()
            if elegido:
                producto_id = elegido.get("codigo") or elegido.get("id")
                incidencia["estado"] = ESTADO_RESUELTA
                incidencia["resolucion"] = f"Relacionado con producto existente: {producto_id}"
                incidencia["producto_relacionado_id"] = producto_id
            else:
                incidencia["estado"] = ESTADO_PENDIENTE
                incidencia["resolucion"] = "Sin selección, queda pendiente"
        else:
            incidencia["estado"] = ESTADO_PENDIENTE
            incidencia["resolucion"] = "Pendiente por decisión de usuario"

    def _resolver_producto_sin_precio(self, incidencia: dict[str, Any], acciones: dict[str, int]) -> None:
        producto = str(incidencia.get("producto") or "Producto sin nombre")
        print("\nProducto sin precio")
        print("El producto existe pero no tiene precio.")
        print(f"Producto: {producto}")
        print("1. Añadir precio")
        print("2. Elegir proveedor existente")
        print("3. Precio provisional")
        print("4. Dejar pendiente")
        op = input("Elige una opción: ").strip()

        if op == "1":
            precio = input("Precio: ").strip()
            prod = self.repo.asegurar_producto_basico(producto)
            pid = prod.get("codigo") or prod.get("id")
            self.repo.actualizar_producto(pid, {"precio": precio})
            incidencia["estado"] = ESTADO_RESUELTA
            incidencia["resolucion"] = f"Precio añadido: {precio}"
            acciones["precios_añadidos"] += 1
        elif op == "2":
            proveedor = self._seleccionar_proveedor_existente()
            if proveedor:
                prod = self.repo.asegurar_producto_basico(producto)
                pid = prod.get("codigo") or prod.get("id")
                self.repo.actualizar_producto(pid, {"proveedor": proveedor.get("nombre")})
                incidencia["estado"] = ESTADO_RESUELTA
                incidencia["resolucion"] = f"Proveedor asignado: {proveedor.get('nombre')}"
            else:
                incidencia["estado"] = ESTADO_PENDIENTE
                incidencia["resolucion"] = "Sin proveedor seleccionado"
        elif op == "3":
            precio = input("Precio provisional: ").strip()
            prod = self.repo.asegurar_producto_basico(producto)
            pid = prod.get("codigo") or prod.get("id")
            self.repo.actualizar_producto(pid, {"precio": precio, "precio_provisional": True})
            incidencia["estado"] = ESTADO_RESUELTA
            incidencia["resolucion"] = f"Precio provisional asignado: {precio}"
            acciones["precios_añadidos"] += 1
        else:
            incidencia["estado"] = ESTADO_PENDIENTE
            incidencia["resolucion"] = "Pendiente por decisión de usuario"

    def _resolver_producto_duplicado(self, incidencia: dict[str, Any]) -> None:
        producto = str(incidencia.get("producto") or "Producto")
        candidatos = list(incidencia.get("candidatos") or [])
        print("\nProducto duplicado")
        print(producto)
        if candidatos:
            print("Posibles coincidencias:")
            for i, c in enumerate(candidatos, 1):
                print(f"{i}. {c}")
        print("Opciones:")
        print("1. Relacionar")
        print("2. Crear nuevo")
        print("3. Ignorar")
        op = input("Elige una opción: ").strip()

        if op == "1":
            elegido = self._seleccionar_producto_existente()
            if elegido:
                producto_id = elegido.get("codigo") or elegido.get("id")
                incidencia["estado"] = ESTADO_RESUELTA
                incidencia["resolucion"] = f"Relacionado con {producto_id}"
            else:
                incidencia["estado"] = ESTADO_PENDIENTE
                incidencia["resolucion"] = "Sin selección"
        elif op == "2":
            data = self._pedir_datos_producto(producto)
            nuevo = self.repo.crear_producto(data)
            producto_id = nuevo.get("codigo") or nuevo.get("id")
            incidencia["estado"] = ESTADO_RESUELTA
            incidencia["resolucion"] = f"Producto creado: {producto_id}"
        else:
            incidencia["estado"] = ESTADO_PENDIENTE
            incidencia["resolucion"] = "Ignorado por usuario"

    def _resolver_ingrediente_sin_cantidad(self, incidencia: dict[str, Any], contexto: dict[str, Any]) -> None:
        receta_nombre = str(incidencia.get("receta") or "Receta")
        ingrediente = str(incidencia.get("ingrediente") or "Ingrediente")
        print("\nIngrediente sin cantidad")
        print(f"Receta: {receta_nombre}")
        print(f"Ingrediente: {ingrediente}")
        print("1. Introducir cantidad")
        print("2. Marcar 'al gusto'")
        print("3. Dejar pendiente")
        print("4. Eliminar ingrediente")
        op = input("Elige una opción: ").strip()

        idx_receta = incidencia.get("receta_index")
        idx_ing = incidencia.get("ingrediente_index")
        if not isinstance(idx_receta, int) or not isinstance(idx_ing, int):
            incidencia["estado"] = ESTADO_PENDIENTE
            incidencia["resolucion"] = "No se pudo localizar ingrediente en contexto"
            return

        recetas = list(contexto.get("recetas") or [])
        if not (0 <= idx_receta < len(recetas)):
            incidencia["estado"] = ESTADO_PENDIENTE
            incidencia["resolucion"] = "Receta fuera de contexto"
            return

        receta = recetas[idx_receta]
        ingredientes = list(receta.get("ingredientes") or [])
        cantidades = list(receta.get("cantidades") or [])
        while len(cantidades) < len(ingredientes):
            cantidades.append("")

        if not (0 <= idx_ing < len(ingredientes)):
            incidencia["estado"] = ESTADO_PENDIENTE
            incidencia["resolucion"] = "Índice de ingrediente inválido"
            return

        if op == "1":
            cantidad = input("Introduce cantidad: ").strip()
            if cantidad:
                cantidades[idx_ing] = cantidad
                receta["cantidades"] = cantidades
                incidencia["estado"] = ESTADO_RESUELTA
                incidencia["resolucion"] = f"Cantidad informada: {cantidad}"
            else:
                incidencia["estado"] = ESTADO_PENDIENTE
                incidencia["resolucion"] = "Cantidad vacía"
        elif op == "2":
            cantidades[idx_ing] = "al gusto"
            receta["cantidades"] = cantidades
            incidencia["estado"] = ESTADO_RESUELTA
            incidencia["resolucion"] = "Marcado como al gusto"
        elif op == "4":
            ingredientes.pop(idx_ing)
            cantidades.pop(idx_ing)
            receta["ingredientes"] = ingredientes
            receta["cantidades"] = cantidades
            incidencia["estado"] = ESTADO_RESUELTA
            incidencia["resolucion"] = "Ingrediente eliminado"
        else:
            incidencia["estado"] = ESTADO_PENDIENTE
            incidencia["resolucion"] = "Pendiente por decisión de usuario"

    def _resolver_proveedor_inexistente(self, incidencia: dict[str, Any], acciones: dict[str, int]) -> None:
        proveedor = str(incidencia.get("proveedor") or "Proveedor")
        print("\nProveedor inexistente")
        print(f"Proveedor: {proveedor}")
        print("1. Crear proveedor")
        print("2. Relacionar con proveedor existente")
        print("3. Dejar pendiente")
        op = input("Elige una opción: ").strip()

        if op == "1":
            nombre = input(f"Nombre [{proveedor}]: ").strip() or proveedor
            nuevo = self.repo.crear_proveedor({"nombre": nombre})
            proveedor_id = nuevo.get("codigo") or nuevo.get("id")
            incidencia["estado"] = ESTADO_RESUELTA
            incidencia["resolucion"] = f"Proveedor creado: {proveedor_id}"
            acciones["proveedores_nuevos"] += 1
        elif op == "2":
            existente = self._seleccionar_proveedor_existente()
            if existente:
                proveedor_id = existente.get("codigo") or existente.get("id")
                incidencia["estado"] = ESTADO_RESUELTA
                incidencia["resolucion"] = f"Relacionado con proveedor: {proveedor_id}"
            else:
                incidencia["estado"] = ESTADO_PENDIENTE
                incidencia["resolucion"] = "Sin selección"
        else:
            incidencia["estado"] = ESTADO_PENDIENTE
            incidencia["resolucion"] = "Pendiente por decisión de usuario"

    def _resolver_receta_incompleta(self, incidencia: dict[str, Any], contexto: dict[str, Any]) -> None:
        receta_nombre = str(incidencia.get("receta") or "Receta")
        print("\nReceta incompleta")
        print(f"Receta: {receta_nombre}")
        print("1. Completar ahora")
        print("2. Dejar pendiente")
        op = input("Elige una opción: ").strip()

        if op != "1":
            incidencia["estado"] = ESTADO_PENDIENTE
            incidencia["resolucion"] = "Pendiente por decisión de usuario"
            return

        idx_receta = incidencia.get("receta_index")
        recetas = list(contexto.get("recetas") or [])
        if not isinstance(idx_receta, int) or not (0 <= idx_receta < len(recetas)):
            incidencia["estado"] = ESTADO_PENDIENTE
            incidencia["resolucion"] = "No se pudo localizar receta"
            return

        receta = recetas[idx_receta]
        if not str(receta.get("elaboracion") or "").strip():
            receta["elaboracion"] = input("Elaboración: ").strip()

        ingredientes = list(receta.get("ingredientes") or [])
        cantidades = list(receta.get("cantidades") or [])
        if not ingredientes:
            while True:
                ing = input("Ingrediente (Enter para terminar): ").strip()
                if not ing:
                    break
                cant = input("Cantidad: ").strip()
                ingredientes.append(ing)
                cantidades.append(cant)
            receta["ingredientes"] = ingredientes
            receta["cantidades"] = cantidades

        incidencia["estado"] = ESTADO_RESUELTA if receta.get("elaboracion") and receta.get("ingredientes") else ESTADO_PENDIENTE
        incidencia["resolucion"] = "Receta completada en asistente" if incidencia["estado"] == ESTADO_RESUELTA else "Receta sigue incompleta"

    @staticmethod
    def _localizar_linea_modelo(contexto: dict[str, Any], incidencia: dict[str, Any]) -> dict[str, Any] | None:
        idx = incidencia.get("linea_index")
        lineas = list(contexto.get("modelo_intermedio") or [])
        if isinstance(idx, int) and 0 <= idx < len(lineas):
            return lineas[idx]
        return None

    def _resolver_unidad_desconocida(self, incidencia: dict[str, Any], contexto: dict[str, Any]) -> None:
        print("\nUnidad desconocida")
        print(incidencia.get("detalle") or "")
        linea = self._localizar_linea_modelo(contexto, incidencia)
        print("1. Corregir unidad")
        print("2. Dejar pendiente")
        op = input("Elige una opción: ").strip()
        if op == "1" and linea is not None:
            unidad = input("Unidad corregida: ").strip()
            if unidad:
                linea["unidad"] = unidad
                incidencia["estado"] = ESTADO_RESUELTA
                incidencia["resolucion"] = f"Unidad corregida a {unidad}"
                return
        incidencia["estado"] = ESTADO_PENDIENTE
        incidencia["resolucion"] = "Pendiente"

    def _resolver_receta_inexistente(self, incidencia: dict[str, Any], contexto: dict[str, Any]) -> None:
        print("\nReceta inexistente")
        print(incidencia.get("detalle") or "")
        linea = self._localizar_linea_modelo(contexto, incidencia)
        print("1. Introducir receta válida")
        print("2. Dejar pendiente")
        op = input("Elige una opción: ").strip()
        if op == "1" and linea is not None:
            receta = input("Receta: ").strip()
            if receta:
                linea["receta"] = receta
                incidencia["estado"] = ESTADO_RESUELTA
                incidencia["resolucion"] = f"Receta corregida: {receta}"
                return
        incidencia["estado"] = ESTADO_PENDIENTE
        incidencia["resolucion"] = "Pendiente"

    def _resolver_cantidad_ausente(self, incidencia: dict[str, Any], contexto: dict[str, Any]) -> None:
        print("\nCantidad ausente")
        print(incidencia.get("detalle") or "")
        linea = self._localizar_linea_modelo(contexto, incidencia)
        print("1. Introducir cantidad")
        print("2. Marcar al gusto")
        print("3. Dejar pendiente")
        op = input("Elige una opción: ").strip()
        if linea is None:
            incidencia["estado"] = ESTADO_PENDIENTE
            incidencia["resolucion"] = "Sin línea localizada"
            return
        if op == "1":
            cantidad = input("Cantidad: ").strip()
            if cantidad:
                linea["cantidad"] = cantidad
                incidencia["estado"] = ESTADO_RESUELTA
                incidencia["resolucion"] = f"Cantidad informada: {cantidad}"
                return
        elif op == "2":
            linea["cantidad"] = "al gusto"
            incidencia["estado"] = ESTADO_RESUELTA
            incidencia["resolucion"] = "Marcada al gusto"
            return
        incidencia["estado"] = ESTADO_PENDIENTE
        incidencia["resolucion"] = "Pendiente"

    def _resolver_merma_invalida(self, incidencia: dict[str, Any], contexto: dict[str, Any]) -> None:
        print("\nMerma inválida")
        print(incidencia.get("detalle") or "")
        linea = self._localizar_linea_modelo(contexto, incidencia)
        print("1. Corregir merma")
        print("2. Usar 0")
        print("3. Dejar pendiente")
        op = input("Elige una opción: ").strip()
        if linea is None:
            incidencia["estado"] = ESTADO_PENDIENTE
            incidencia["resolucion"] = "Sin línea localizada"
            return
        if op == "1":
            merma = input("Merma (%): ").strip()
            linea["merma"] = merma
            incidencia["estado"] = ESTADO_RESUELTA
            incidencia["resolucion"] = f"Merma corregida: {merma}"
            return
        if op == "2":
            linea["merma"] = "0"
            incidencia["estado"] = ESTADO_RESUELTA
            incidencia["resolucion"] = "Merma fijada a 0"
            return
        incidencia["estado"] = ESTADO_PENDIENTE
        incidencia["resolucion"] = "Pendiente"

    def _resolver_coste_discrepante(self, incidencia: dict[str, Any], contexto: dict[str, Any]) -> None:
        print("\nCoste importado discrepante")
        print(incidencia.get("detalle") or "")
        print(f"Coste importado: {incidencia.get('coste_importado')}")
        print(f"Coste calculado: {incidencia.get('coste_calculado')}")
        print("1. Usar cálculo del sistema")
        print("2. Conservar coste importado como dato manual")
        print("3. Revisar línea")
        print("4. Dejar pendiente")
        op = input("Elige una opción: ").strip()

        linea = self._localizar_linea_modelo(contexto, incidencia)
        if linea is None:
            incidencia["estado"] = ESTADO_PENDIENTE
            incidencia["resolucion"] = "Sin línea localizada"
            return

        if op == "1":
            linea["decision_coste"] = "USAR_SISTEMA"
            incidencia["estado"] = ESTADO_RESUELTA
            incidencia["resolucion"] = "Se usará coste calculado"
            return
        if op == "2":
            linea["decision_coste"] = "MANTENER_IMPORTADO"
            linea["coste_linea_manual"] = incidencia.get("coste_importado")
            incidencia["estado"] = ESTADO_RESUELTA
            incidencia["resolucion"] = "Se conserva coste importado manual"
            return
        if op == "3":
            cantidad = input("Cantidad (vacío mantiene): ").strip()
            unidad = input("Unidad (vacío mantiene): ").strip()
            merma = input("Merma (vacío mantiene): ").strip()
            precio = input("Precio unitario (vacío mantiene): ").strip()
            if cantidad:
                linea["cantidad"] = cantidad
            if unidad:
                linea["unidad"] = unidad
            if merma:
                linea["merma"] = merma
            if precio:
                linea["precio"] = precio
            incidencia["estado"] = ESTADO_RESUELTA
            incidencia["resolucion"] = "Línea revisada manualmente"
            return

        linea["decision_coste"] = "PENDIENTE"
        incidencia["estado"] = ESTADO_PENDIENTE
        incidencia["resolucion"] = "Pendiente por decisión de usuario"

    @staticmethod
    def _pedir_datos_producto(nombre_sugerido: str) -> dict[str, Any]:
        nombre = input(f"Nombre [{nombre_sugerido}]: ").strip() or nombre_sugerido
        return {
            "nombre": nombre,
            "familia": input("Familia: ").strip(),
            "unidad_compra": input("Unidad de compra: ").strip(),
            "cantidad_formato": input("Cantidad por envase: ").strip(),
            "unidad_recetas": input("Unidad utilizada en recetas: ").strip(),
            "unidad_base": input("Unidad base: ").strip(),
            "precio": input("Precio: ").strip(),
            "proveedor": input("Proveedor: ").strip(),
            "iva": input("IVA: ").strip(),
            "merma": input("Merma: ").strip(),
            "observaciones": input("Observaciones: ").strip(),
        }

    def _seleccionar_producto_existente(self) -> dict[str, Any] | None:
        productos = self.repo.listar_productos()
        if not productos:
            print("No hay productos registrados aún.")
            return None
        for i, p in enumerate(productos, 1):
            print(f"{i}. {p.get('nombre')} | {p.get('codigo') or p.get('id')}")
        sel = input("Selecciona número (Enter=cancelar): ").strip()
        if not sel.isdigit():
            return None
        idx = int(sel)
        if idx < 1 or idx > len(productos):
            return None
        return productos[idx - 1]

    def _seleccionar_proveedor_existente(self) -> dict[str, Any] | None:
        proveedores = self.repo.listar_proveedores()
        if not proveedores:
            print("No hay proveedores registrados aún.")
            return None
        for i, p in enumerate(proveedores, 1):
            print(f"{i}. {p.get('nombre')} | {p.get('codigo') or p.get('id')}")
        sel = input("Selecciona número (Enter=cancelar): ").strip()
        if not sel.isdigit():
            return None
        idx = int(sel)
        if idx < 1 or idx > len(proveedores):
            return None
        return proveedores[idx - 1]


__all__ = ["AsistenteResolucionIncidencias601"]
