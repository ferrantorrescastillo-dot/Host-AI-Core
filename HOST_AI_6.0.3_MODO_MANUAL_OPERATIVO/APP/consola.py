from __future__ import annotations

from datetime import date
from CORE.orquestador import SolicitudHostAI


class AppConsolaHostAI:
    """
    Consola operativa de Host AI Base 6.0.3.

    Primera capa de uso real por terminal.
    No sustituye la futura interfaz gráfica, pero permite usar Host AI como programa.
    """

    def __init__(self, core):
        self.core = core
        self.ultimo_evento_id = None

    def ejecutar(self):
        self._cabecera()
        while True:
            self._menu_principal()
            opcion = input("Elige una opción: ").strip()

            if opcion == "1":
                self._hablar_host_ai()
            elif opcion == "2":
                self._menu_eventos()
            elif opcion == "3":
                self._menu_stock()
            elif opcion == "4":
                self._menu_compras()
            elif opcion == "5":
                self._menu_escandallos()
            elif opcion == "6":
                self._menu_costes()
            elif opcion == "7":
                self._menu_produccion_real()
            elif opcion == "8":
                self._estado_sistema()
            elif opcion == "9":
                self._menu_base_datos()
            elif opcion == "10":
                self._menu_excel()
            elif opcion == "0":
                print("Saliendo de Host AI.")
                break
            else:
                print("Opción no válida.")

    def _cabecera(self):
        print("=" * 70)
        print("HOST AI BASE 6.0.3 - MODO MANUAL OPERATIVO")
        print("=" * 70)

    def _menu_principal(self):
        print("\nMENÚ PRINCIPAL")
        print("1. Hablar con Host AI")
        print("2. Eventos")
        print("3. Stock")
        print("4. Compras")
        print("5. Escandallos")
        print("6. Costes")
        print("7. Producción real")
        print("8. Estado del sistema")
        print("9. Base de datos local")
        print("10. Excel / importaciones")
        print("0. Salir")

    # ------------------------------------------------------------------
    # CHAT
    # ------------------------------------------------------------------
    def _hablar_host_ai(self):
        print("\nHabla con Host AI. Escribe 'salir' para volver.")
        while True:
            texto = input("Tú: ").strip()
            if texto.lower() in {"salir", "volver", "0"}:
                break

            contexto = {}
            if self.ultimo_evento_id:
                contexto["evento_id"] = self.ultimo_evento_id

            r = self.core.orquestador.resolver(SolicitudHostAI("chat_host_ai", {
                "texto": texto,
                "contexto": contexto,
            }))
            print("Host AI:", r.mensaje)

            # Guarda último evento si el chat crea uno.
            try:
                evento = r.datos["resultado"]["datos"]["evento"]
                self.ultimo_evento_id = evento["id"]
                print(f"Evento activo: {self.ultimo_evento_id}")
            except Exception:
                pass

    # ------------------------------------------------------------------
    # EVENTOS
    # ------------------------------------------------------------------
    def _menu_eventos(self):
        print("\nEVENTOS")
        print("1. Crear evento rápido")
        print("2. Añadir servicio al último evento")
        print("3. Añadir pase al último evento")
        print("4. Ver línea temporal del último evento")
        print("0. Volver")
        op = input("Elige una opción: ").strip()

        if op == "1":
            nombre = input("Nombre del evento: ").strip() or "Evento Demo"
            pax = int(input("Pax: ").strip() or "0")
            tipo = input("Tipo (boda/catering/evento): ").strip() or "evento"
            fecha = input("Fecha YYYY-MM-DD (vacío=hoy): ").strip() or date.today().isoformat()
            r = self.core.orquestador.resolver(SolicitudHostAI("crear_evento", {
                "nombre": nombre,
                "fecha": fecha,
                "pax": pax,
                "tipo": tipo,
            }))
            print(r.mensaje)
            if r.ok:
                self.ultimo_evento_id = r.datos["evento"]["id"]
                print(f"Evento activo: {self.ultimo_evento_id}")

        elif op == "2":
            if not self._requiere_evento():
                return
            nombre = input("Nombre servicio: ").strip() or "Servicio"
            hora = input("Hora inicio HH:MM: ").strip() or "20:00"
            r = self.core.orquestador.resolver(SolicitudHostAI("agregar_servicio_evento", {
                "evento_id": self.ultimo_evento_id,
                "nombre": nombre,
                "tipo": nombre.lower(),
                "hora_inicio": hora,
                "duracion_min": 180,
            }))
            print(r.mensaje)

        elif op == "3":
            if not self._requiere_evento():
                return
            evento = self.core.eventos.obtener(self.ultimo_evento_id).to_dict()
            if not evento.get("servicios"):
                print("Primero añade un servicio.")
                return
            servicio_id = evento["servicios"][-1]["id"]
            nombre = input("Nombre pase: ").strip() or "Pase"
            hora = input("Hora pase HH:MM: ").strip() or "21:00"
            recetas_txt = input("Recetas separadas por coma (ej REC-CARRILLERA): ").strip()
            recetas = [r.strip() for r in recetas_txt.split(",") if r.strip()]
            r = self.core.orquestador.resolver(SolicitudHostAI("agregar_pase_evento", {
                "evento_id": self.ultimo_evento_id,
                "servicio_id": servicio_id,
                "nombre": nombre,
                "hora_inicio": hora,
                "duracion_min": 35,
                "recetas": recetas,
            }))
            print(r.mensaje)

        elif op == "4":
            if not self._requiere_evento():
                return
            r = self.core.orquestador.resolver(SolicitudHostAI("linea_temporal_evento", {
                "evento_id": self.ultimo_evento_id
            }))
            print(r.mensaje)
            print(r.datos)

    # ------------------------------------------------------------------
    # STOCK
    # ------------------------------------------------------------------
    def _menu_stock(self):
        print("\nSTOCK")
        print("1. Registrar entrada")
        print("2. Ver stock actual")
        print("3. Diagnosticar stock")
        print("0. Volver")
        op = input("Elige una opción: ").strip()

        if op == "1":
            nombre = input("Artículo: ").strip()
            cantidad = float(input("Cantidad: ").strip() or "0")
            unidad = input("Unidad: ").strip() or "kg"
            familia = input("Familia: ").strip()
            r = self.core.orquestador.resolver(SolicitudHostAI("registrar_entrada_stock", {
                "nombre": nombre,
                "cantidad": cantidad,
                "unidad": unidad,
                "familia": familia,
            }))
            print(r.mensaje)

        elif op == "2":
            r = self.core.orquestador.resolver(SolicitudHostAI("stock_actual", {}))
            print(r.mensaje)
            for item in r.datos.get("items", []):
                print(f"- {item['nombre']}: {item['cantidad']} {item['unidad']}")

        elif op == "3":
            r = self.core.orquestador.resolver(SolicitudHostAI("diagnosticar_stock", {}))
            print(r.mensaje)
            for aviso in r.datos.get("avisos", []):
                print("-", aviso.get("mensaje"))

    # ------------------------------------------------------------------
    # COMPRAS
    # ------------------------------------------------------------------
    def _menu_compras(self):
        print("\nCOMPRAS")
        print("1. Registrar necesidad de compra")
        print("2. Listar necesidades")
        print("3. Generar pedidos sugeridos")
        print("0. Volver")
        op = input("Elige una opción: ").strip()

        if op == "1":
            nombre = input("Artículo: ").strip()
            cantidad = float(input("Cantidad: ").strip() or "0")
            unidad = input("Unidad: ").strip() or "kg"
            proveedor = input("Proveedor preferente: ").strip()
            r = self.core.orquestador.resolver(SolicitudHostAI("registrar_necesidad_compra", {
                "nombre": nombre,
                "cantidad": cantidad,
                "unidad": unidad,
                "proveedor_preferente": proveedor,
                "prioridad": 80,
            }))
            print(r.mensaje)

        elif op == "2":
            r = self.core.orquestador.resolver(SolicitudHostAI("listar_necesidades_compra", {}))
            print(r.mensaje)
            for n in r.datos.get("necesidades", []):
                print(f"- {n['nombre']}: {n['cantidad']} {n['unidad']} | {n['proveedor_preferente']}")

        elif op == "3":
            r = self.core.orquestador.resolver(SolicitudHostAI("generar_pedidos_sugeridos", {}))
            print(r.mensaje)
            for p in r.datos.get("pedidos_sugeridos", []):
                print(f"\nProveedor: {p['proveedor']}")
                for n in p["necesidades"]:
                    print(f"- {n['nombre']}: {n['cantidad']} {n['unidad']}")

    # ------------------------------------------------------------------
    # ESCANDALLOS
    # ------------------------------------------------------------------
    def _menu_escandallos(self):
        print("\nESCANDALLOS")
        print("1. Crear escandallo demo carrillera")
        print("2. Listar escandallos")
        print("3. Calcular escandallo receta")
        print("0. Volver")
        op = input("Elige una opción: ").strip()

        if op == "1":
            r = self.core.orquestador.resolver(SolicitudHostAI("registrar_escandallo", self._escandallo_demo()))
            print(r.mensaje)

        elif op == "2":
            r = self.core.orquestador.resolver(SolicitudHostAI("listar_escandallos", {}))
            print(r.mensaje)
            for e in r.datos.get("escandallos", []):
                print(f"- {e['receta_id']} | {e['nombre']} | {e['raciones_base']} raciones")

        elif op == "3":
            receta_id = input("Receta ID: ").strip() or "REC-CARRILLERA"
            raciones = int(input("Raciones: ").strip() or "10")
            r = self.core.orquestador.resolver(SolicitudHostAI("calcular_escandallo_receta", {
                "receta_id": receta_id,
                "raciones": raciones,
            }))
            print(r.mensaje)
            for n in r.datos.get("necesidades", []):
                print(f"- {n['nombre']}: {n['cantidad_bruta']} {n['unidad']}")

    # ------------------------------------------------------------------
    # COSTES
    # ------------------------------------------------------------------
    def _menu_costes(self):
        print("\nCOSTES")
        print("1. Registrar precio")
        print("2. Calcular coste receta")
        print("3. Calcular coste último evento")
        print("0. Volver")
        op = input("Elige una opción: ").strip()

        if op == "1":
            nombre = input("Artículo: ").strip()
            precio = float(input("Precio unitario: ").strip() or "0")
            unidad = input("Unidad: ").strip() or "kg"
            articulo_id = input("Artículo ID (opcional): ").strip()
            r = self.core.orquestador.resolver(SolicitudHostAI("registrar_precio", {
                "nombre": nombre,
                "precio_unitario": precio,
                "unidad": unidad,
                "articulo_id": articulo_id,
            }))
            print(r.mensaje)

        elif op == "2":
            receta_id = input("Receta ID: ").strip() or "REC-CARRILLERA"
            raciones = int(input("Raciones: ").strip() or "10")
            precio = float(input("Precio venta/ración: ").strip() or "0")
            r = self.core.orquestador.resolver(SolicitudHostAI("calcular_coste_receta", {
                "receta_id": receta_id,
                "raciones": raciones,
                "precio_venta_por_racion": precio,
            }))
            print(r.mensaje)

        elif op == "3":
            if not self._requiere_evento():
                return
            precio = float(input("Precio venta por pax: ").strip() or "0")
            r = self.core.orquestador.resolver(SolicitudHostAI("calcular_coste_evento", {
                "evento_id": self.ultimo_evento_id,
                "precio_venta_por_pax": precio,
                "extras": [],
            }))
            print(r.mensaje)

    # ------------------------------------------------------------------
    # PRODUCCIÓN REAL
    # ------------------------------------------------------------------
    def _menu_produccion_real(self):
        print("\nPRODUCCIÓN REAL")
        print("1. Planificar último evento")
        print("2. Listar planes")
        print("0. Volver")
        op = input("Elige una opción: ").strip()

        if op == "1":
            if not self._requiere_evento():
                return
            hora = input("Hora inicio producción: ").strip() or "08:00"
            equipo = int(input("Equipo cocina: ").strip() or "2")
            r = self.core.orquestador.resolver(SolicitudHostAI("planificar_produccion_real_evento", {
                "evento_id": self.ultimo_evento_id,
                "hora_inicio": hora,
                "equipo_cocina": equipo,
            }))
            print(r.mensaje)
            for b in r.datos.get("cronograma", [])[:20]:
                print(f"{b['inicio']}-{b['fin']} | {b['titulo']} | {b['responsable']}")

        elif op == "2":
            r = self.core.orquestador.resolver(SolicitudHostAI("listar_planes_produccion_real", {}))
            print(r.mensaje)
            for p in r.datos.get("planes", []):
                print(f"- {p['id']} | {p['evento']} | {p['duracion_total_min']} min")

    # ------------------------------------------------------------------
    # ESTADO
    # ------------------------------------------------------------------
    def _estado_sistema(self):
        r = self.core.orquestador.resolver(SolicitudHostAI("listar_pipelines", {}))
        print(r.mensaje)
        for p in r.datos.get("pipelines", []):
            print(f"- {p['nombre']}: {p['descripcion']}")



    def _menu_excel(self):
        print("\nEXCEL / IMPORTACIONES")
        print("1. Analizar archivo Excel")
        print("2. Detectar tipo de documento Excel")
        print("3. Vista previa escandallos Excel")
        print("4. Importar escandallos Excel")
        print("5. Vista previa artículos Excel")
        print("6. Importar artículos Excel")
        print("7. Vista previa inventario Excel")
        print("8. Importar inventario Excel")
        print("0. Volver")
        op = input("Elige una opción: ").strip()
        if op == "1":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            r = self.core.orquestador.resolver(SolicitudHostAI("analizar_excel", {
                "ruta_archivo": ruta,
                "filas_preview": 10,
                "exportar_json": True,
            }))
            print(r.mensaje)
            for h in r.datos.get("hojas", []):
                print(f"- {h['nombre']}: {h['filas']} filas, {h['columnas']} columnas")
                for c in h.get("columnas_detectadas", [])[:8]:
                    print(f"  · {c['letra']} {c['nombre_detectado']} | {c['tipo_detectado']} | vacío {c['porcentaje_vacio']}%")

        elif op == "2":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            r = self.core.orquestador.resolver(SolicitudHostAI("detectar_documento_excel", {
                "ruta_archivo": ruta,
                "filas_preview": 10,
                "exportar_json": True,
            }))
            print(r.mensaje)
            for h in r.datos.get("hojas", []):
                print(f"- {h['hoja']}: {h['tipo_principal']} ({h['confianza']}%)")
                for aviso in h.get("avisos", []):
                    print(f"  Aviso: {aviso}")

        elif op == "3":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            r = self.core.orquestador.resolver(SolicitudHostAI("vista_previa_escandallos_excel", {
                "ruta_archivo": ruta,
                "filas_preview": 50,
            }))
            print(r.mensaje)
            for e in r.datos.get("escandallos", []):
                print(f"- {e['receta_id']} | {e['nombre']} | {len(e['lineas'])} líneas")

        elif op == "4":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            r = self.core.orquestador.resolver(SolicitudHostAI("importar_escandallos_excel", {
                "ruta_archivo": ruta,
                "filas_preview": 200,
                "reemplazar": True,
            }))
            print(r.mensaje)
            for e in r.datos.get("escandallos", []):
                print(f"- Importado: {e['receta_id']} | {e['nombre']}")

        elif op == "5":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            r = self.core.orquestador.resolver(SolicitudHostAI("vista_previa_articulos_excel", {
                "ruta_archivo": ruta,
                "filas_preview": 100,
            }))
            print(r.mensaje)
            for a in r.datos.get("articulos", [])[:20]:
                print(f"- {a['articulo_id']} | {a['nombre']} | {a['unidad']} | {a['precio_unitario']}")

        elif op == "6":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            r = self.core.orquestador.resolver(SolicitudHostAI("importar_articulos_excel", {
                "ruta_archivo": ruta,
                "filas_preview": 500,
                "actualizar_existentes": True,
            }))
            print(r.mensaje)
            for a in r.datos.get("articulos", [])[:20]:
                print(f"- Importado: {a['articulo_id']} | {a['nombre']}")

        elif op == "7":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            r = self.core.orquestador.resolver(SolicitudHostAI("vista_previa_inventario_excel", {
                "ruta_archivo": ruta,
                "filas_preview": 200,
            }))
            print(r.mensaje)
            for l in r.datos.get("lineas", [])[:20]:
                print(f"- {l['articulo_id']} | {l['nombre']} | {l['cantidad']} {l['unidad']} | {l['ubicacion']}")

        elif op == "8":
            ruta = input("Ruta del Excel: ").strip().strip('"')
            r = self.core.orquestador.resolver(SolicitudHostAI("importar_inventario_excel", {
                "ruta_archivo": ruta,
                "filas_preview": 1000,
                "crear_articulos": True,
                "actualizar_stock": True,
            }))
            print(r.mensaje)
            for c in r.datos.get("cambios", [])[:20]:
                print(f"- {c['nombre']}: {c['anterior']} -> {c['nuevo']} {c['unidad']}")

    def _menu_base_datos(self):
        print("\nBASE DE DATOS LOCAL")
        print("1. Guardar todo")
        print("2. Ver resumen")
        print("3. Crear snapshot")
        print("0. Volver")
        op = input("Elige una opción: ").strip()
        if op == "1":
            r = self.core.orquestador.resolver(SolicitudHostAI("guardar_todo_db", {}))
            print(r.mensaje)
        elif op == "2":
            r = self.core.orquestador.resolver(SolicitudHostAI("resumen_db", {}))
            print(r.mensaje)
            for c in r.datos.get("colecciones", []):
                print(f"- {c['coleccion']}: {c['total']} registros")
        elif op == "3":
            nombre = input("Nombre snapshot (opcional): ").strip()
            r = self.core.orquestador.resolver(SolicitudHostAI("snapshot_db", {"nombre": nombre}))
            print(r.mensaje)

    def _requiere_evento(self):
        if not self.ultimo_evento_id:
            print("No hay evento activo. Crea uno primero.")
            return False
        return True

    def _escandallo_demo(self):
        return {
            "receta_id": "REC-CARRILLERA",
            "nombre": "Carrillera melosa",
            "raciones_base": 10,
            "grupo": "Carnes",
            "lineas": [
                {
                    "nombre": "Carrillera de ternera",
                    "cantidad": 1.8,
                    "unidad": "kg",
                    "tipo": "articulo",
                    "articulo_id": "ART-CARRILLERA",
                    "merma_porcentaje": 10,
                    "familia": "carnes",
                    "proveedor_preferente": "Proveedor Carnes",
                    "coste_unitario": 8.5,
                },
                {
                    "nombre": "Demi-glace",
                    "cantidad": 0.8,
                    "unidad": "L",
                    "tipo": "elaboracion",
                    "elaboracion_id": "ELAB-DEMI",
                    "merma_porcentaje": 0,
                    "familia": "salsas",
                    "proveedor_preferente": "Producción interna",
                    "coste_unitario": 3.0,
                },
            ],
        }
