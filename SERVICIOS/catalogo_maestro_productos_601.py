from __future__ import annotations

from pathlib import Path
from typing import Any

from SERVICIOS.centro_importacion_601 import CentroImportacionUI601
from SERVICIOS.repositorio_productos_maestro_601 import (
    RepositorioProductosMaestro601,
    ESTADO_ACTIVO,
    ESTADO_ARCHIVADO,
    ESTADO_PENDIENTE,
)


class CatalogoMaestroProductos601:
    """Casos de uso del Catálogo Maestro de Productos.

    Reutiliza la fuente real del proyecto y no crea una base paralela.
    """

    def __init__(self, base_dir: Path):
        self.repositorio = RepositorioProductosMaestro601(base_dir)

    def listar(self, incluir_archivados: bool = True) -> dict[str, Any]:
        productos = self.repositorio.listar_productos(incluir_archivados=incluir_archivados)
        return {
            "ok": True,
            "total": len(productos),
            "productos": productos,
        }

    def buscar(self, filtros: dict[str, str]) -> dict[str, Any]:
        resultado = self.repositorio.buscar_productos(filtros)
        return {
            "ok": True,
            "filtros": filtros,
            "total": len(resultado),
            "productos": resultado,
        }

    def obtener(self, codigo: str) -> dict[str, Any]:
        producto = self.repositorio.obtener_producto(codigo)
        if not producto:
            return {"ok": False, "mensaje": "Producto no encontrado."}
        precios = self.repositorio.obtener_proveedores_y_precios(codigo)
        return {
            "ok": True,
            "producto": producto,
            "asociaciones": precios.get("asociaciones", []),
            "historico_precios": precios.get("historico_precios", []),
        }

    def crear(self, datos: dict[str, Any]) -> dict[str, Any]:
        try:
            producto = self.repositorio.crear_producto(datos)
            return {"ok": True, "mensaje": "Producto creado.", "producto": producto}
        except ValueError as exc:
            return {"ok": False, "mensaje": str(exc)}

    def editar(self, codigo: str, cambios: dict[str, Any]) -> dict[str, Any]:
        try:
            producto = self.repositorio.editar_producto(codigo, cambios)
            return {"ok": True, "mensaje": "Producto actualizado.", "producto": producto}
        except ValueError as exc:
            return {"ok": False, "mensaje": str(exc)}

    def archivar(self, codigo: str) -> dict[str, Any]:
        try:
            producto = self.repositorio.archivar_producto(codigo)
            return {"ok": True, "mensaje": "Producto archivado.", "producto": producto}
        except ValueError as exc:
            return {"ok": False, "mensaje": str(exc)}

    def pendientes(self) -> dict[str, Any]:
        productos = self.repositorio.productos_pendientes()
        return {"ok": True, "total": len(productos), "productos": productos}

    def registrar_precio_manual(self, datos: dict[str, Any]) -> dict[str, Any]:
        if not datos.get("codigo"):
            return {"ok": False, "mensaje": "El código de producto es obligatorio."}
        producto = self.repositorio.obtener_producto(str(datos.get("codigo")))
        if not producto:
            return {"ok": False, "mensaje": "No existe el producto indicado."}

        payload = {
            "codigo": producto.get("codigo"),
            "nombre": producto.get("nombre"),
            "precio": datos.get("precio"),
            "unidad": datos.get("unidad") or producto.get("unidad_base") or "",
            "proveedor": datos.get("proveedor") or producto.get("proveedor_preferente") or producto.get("proveedor") or "",
            "precio_incluye_iva": bool(datos.get("precio_incluye_iva", False)),
            "iva": datos.get("iva") or "",
            "fecha": datos.get("fecha") or "",
            "preferente": bool(datos.get("preferente", False)),
            "provisional": bool(datos.get("provisional", False)),
        }
        registro = self.repositorio.registrar_precio_historico(payload)
        return {"ok": True, "mensaje": "Precio registrado.", "registro": registro}

    def importar_desde_excel(self, asistente_importacion_excel: Any, ruta_archivo: str, confirmar: bool = False) -> dict[str, Any]:
        sesion = asistente_importacion_excel.preparar_importacion(ruta_archivo)
        if not confirmar:
            return {
                "ok": True,
                "modo": "vista_previa",
                "sesion": sesion,
                "mensaje": "Vista previa generada. Confirma para ejecutar.",
            }

        sugeridos = (sesion or {}).get("importadores_sugeridos", [])
        importador = "articulos" if "articulos" in sugeridos else "auto"
        resultado = asistente_importacion_excel.ejecutar_importacion(
            sesion_id=sesion.get("id", ""),
            importador=importador,
            forzar=False,
        )
        return {
            "ok": True,
            "modo": "importacion",
            "sesion": resultado,
            "mensaje": "Importación ejecutada sobre la fuente real de artículos.",
        }


class CatalogoMaestroProductosUI601:
    def __init__(self, servicio: CatalogoMaestroProductos601, base_dir: Path | None = None):
        self.servicio = servicio
        self.base_dir = Path(base_dir or self.servicio.repositorio.base_dir).resolve()
        self.centro_importacion = CentroImportacionUI601(self.base_dir)

    def ejecutar(self) -> None:
        while True:
            self._cabecera()
            opcion = input("Selecciona opción: ").strip()

            if opcion == "0":
                print("Volviendo al módulo Escandallos y Recetas...")
                return
            if opcion == "1":
                self._listar(incluir_archivados=False)
                continue
            if opcion == "2":
                self._buscar()
                continue
            if opcion == "3":
                self._crear()
                continue
            if opcion == "4":
                self._editar()
                continue
            if opcion == "5":
                self._archivar()
                continue
            if opcion == "6":
                self._ver_detalle()
                continue
            if opcion == "7":
                self._pendientes()
                continue
            if opcion == "8":
                self._registrar_precio_manual()
                continue
            if opcion == "9":
                self._importar_excel()
                continue

            print("Opción no válida.")

    def _cabecera(self) -> None:
        print("\n=== CATÁLOGO MAESTRO DE PRODUCTOS 6.0.1 ===")
        print("Fuente única: DATOS/db/articulos.json + proveedores + asociaciones compra")
        print("1) Listar productos activos")
        print("2) Buscar productos (filtros)")
        print("3) Crear producto")
        print("4) Editar producto")
        print("5) Archivar producto")
        print("6) Ver detalle (incluye proveedores y histórico)")
        print("7) Ver productos pendientes")
        print("8) Registrar precio manual")
        print("9) Importar productos desde Excel (flujo unificado)")
        print("0) Volver")

    def _listar(self, incluir_archivados: bool = False) -> None:
        data = self.servicio.listar(incluir_archivados=incluir_archivados)
        print(f"Total: {data['total']}")
        for p in data["productos"][:100]:
            print(
                f"- {p.get('codigo', '')}: {p.get('nombre', '')} | "
                f"familia={p.get('familia', '')} | proveedor={p.get('proveedor_preferente') or p.get('proveedor') or ''} | "
                f"precio={p.get('precio')} | estado={p.get('estado')}"
            )

    def _buscar(self) -> None:
        filtros = {
            "nombre": input("Nombre contiene (vacío para omitir): ").strip(),
            "codigo": input("Código contiene (vacío para omitir): ").strip(),
            "familia": input("Familia contiene (vacío para omitir): ").strip(),
            "subfamilia": input("Subfamilia contiene (vacío para omitir): ").strip(),
            "marca": input("Marca contiene (vacío para omitir): ").strip(),
            "proveedor": input("Proveedor contiene (vacío para omitir): ").strip(),
            "referencia": input("Referencia proveedor contiene (vacío para omitir): ").strip(),
            "estado": input("Estado exacto ACTIVO/PENDIENTE_DE_COMPLETAR/ARCHIVADO (vacío para omitir): ").strip(),
        }
        data = self.servicio.buscar(filtros)
        print(f"Resultados: {data['total']}")
        for p in data["productos"][:100]:
            print(f"- {p.get('codigo')}: {p.get('nombre')} | estado={p.get('estado')} | precio={p.get('precio')}")

    def _crear(self) -> None:
        alergenos = input("Alérgenos (coma separados, opcional): ").strip()
        datos = {
            "codigo": input("Código (opcional): ").strip(),
            "nombre": input("Nombre: ").strip(),
            "familia": input("Familia: ").strip(),
            "subfamilia": input("Subfamilia: ").strip(),
            "marca": input("Marca: ").strip(),
            "referencia_proveedor": input("Referencia proveedor: ").strip(),
            "proveedor": input("Proveedor principal: ").strip(),
            "proveedor_preferente": input("Proveedor preferente: ").strip(),
            "unidad_compra": input("Unidad compra: ").strip(),
            "cantidad_formato": input("Cantidad por formato: ").strip(),
            "unidad_base": input("Unidad base: ").strip(),
            "unidad_recetas": input("Unidad recetas: ").strip(),
            "conversion_unidades": input("Conversión unidades: ").strip(),
            "precio": input("Precio: ").strip(),
            "precio_incluye_iva": input("Precio incluye IVA? (s/N): ").strip().lower() == "s",
            "iva": input("IVA (%): ").strip(),
            "fecha_precio": input("Fecha precio (YYYY-MM-DD): ").strip(),
            "merma_habitual": input("Merma habitual: ").strip(),
            "conservacion": input("Conservación: ").strip(),
            "stock_minimo": input("Stock mínimo: ").strip(),
            "observaciones": input("Observaciones: ").strip(),
            "alergenos": [x.strip() for x in alergenos.split(",") if x.strip()],
        }
        res = self.servicio.crear(datos)
        print(res.get("mensaje"))
        if res.get("ok"):
            p = res.get("producto", {})
            print(f"Creado: {p.get('codigo')} - {p.get('nombre')}")

    def _editar(self) -> None:
        codigo = input("Código del producto a editar: ").strip()
        print("Deja vacío para no cambiar un campo.")
        alergenos = input("Alérgenos (coma separados): ").strip()
        cambios = {
            "nombre": input("Nombre: ").strip(),
            "familia": input("Familia: ").strip(),
            "subfamilia": input("Subfamilia: ").strip(),
            "marca": input("Marca: ").strip(),
            "referencia_proveedor": input("Referencia proveedor: ").strip(),
            "proveedor": input("Proveedor principal: ").strip(),
            "proveedor_preferente": input("Proveedor preferente: ").strip(),
            "unidad_compra": input("Unidad compra: ").strip(),
            "cantidad_formato": input("Cantidad por formato: ").strip(),
            "unidad_base": input("Unidad base: ").strip(),
            "unidad_recetas": input("Unidad recetas: ").strip(),
            "conversion_unidades": input("Conversión unidades: ").strip(),
            "precio": input("Precio: ").strip(),
            "precio_incluye_iva": input("Precio incluye IVA? (s/N): ").strip().lower() == "s",
            "iva": input("IVA (%): ").strip(),
            "fecha_precio": input("Fecha precio (YYYY-MM-DD): ").strip(),
            "merma_habitual": input("Merma habitual: ").strip(),
            "conservacion": input("Conservación: ").strip(),
            "stock_minimo": input("Stock mínimo: ").strip(),
            "observaciones": input("Observaciones: ").strip(),
            "alergenos": [x.strip() for x in alergenos.split(",") if x.strip()] if alergenos else "",
        }
        cambios_limpios = {k: v for k, v in cambios.items() if v not in ("", None)}
        res = self.servicio.editar(codigo, cambios_limpios)
        print(res.get("mensaje"))

    def _archivar(self) -> None:
        codigo = input("Código del producto a archivar: ").strip()
        confirm = input("Confirmar archivado? (s/N): ").strip().lower()
        if confirm != "s":
            print("Operación cancelada.")
            return
        res = self.servicio.archivar(codigo)
        print(res.get("mensaje"))

    def _ver_detalle(self) -> None:
        codigo = input("Código de producto: ").strip()
        res = self.servicio.obtener(codigo)
        if not res.get("ok"):
            print(res.get("mensaje"))
            return

        p = res.get("producto", {})
        print(f"Código: {p.get('codigo')}")
        print(f"Nombre: {p.get('nombre')}")
        print(f"Estado: {p.get('estado')}")
        print(f"Familia/Subfamilia: {p.get('familia')} / {p.get('subfamilia')}")
        print(f"Proveedor principal/preferente: {p.get('proveedor')} / {p.get('proveedor_preferente')}")
        print(f"Precio: {p.get('precio')} {p.get('unidad_base')}")
        print(f"Histórico precios: {len(res.get('historico_precios', []))} registros")
        print(f"Asociaciones proveedor: {len(res.get('asociaciones', []))}")

    def _pendientes(self) -> None:
        res = self.servicio.pendientes()
        print(f"Pendientes: {res.get('total', 0)}")
        for p in res.get("productos", [])[:100]:
            print(f"- {p.get('codigo')}: {p.get('nombre')} | precio={p.get('precio')} | unidad={p.get('unidad_base')}")

    def _registrar_precio_manual(self) -> None:
        datos = {
            "codigo": input("Código producto: ").strip(),
            "precio": input("Precio: ").strip(),
            "unidad": input("Unidad (opcional): ").strip(),
            "proveedor": input("Proveedor (opcional): ").strip(),
            "precio_incluye_iva": input("Incluye IVA? (s/N): ").strip().lower() == "s",
            "iva": input("IVA (%): ").strip(),
            "fecha": input("Fecha precio (YYYY-MM-DD, opcional): ").strip(),
            "preferente": input("Marcar proveedor como preferente? (s/N): ").strip().lower() == "s",
            "provisional": input("Precio provisional? (s/N): ").strip().lower() == "s",
        }
        res = self.servicio.registrar_precio_manual(datos)
        print(res.get("mensaje"))

    def _importar_excel(self) -> None:
        print("\nImportación Excel delegada al Centro de Importación (flujo real unificado).")
        self.centro_importacion.importar_excel()


__all__ = [
    "CatalogoMaestroProductos601",
    "CatalogoMaestroProductosUI601",
    "ESTADO_ACTIVO",
    "ESTADO_PENDIENTE",
    "ESTADO_ARCHIVADO",
]
