from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from CORE.host_ai_core import HostAICore
from SERVICIOS.recepcion_inteligente_piloto_1 import RecepcionInteligentePiloto1, formatear_diagnostico_piloto1
from SERVICIOS.recepcion_operativa_rp3 import RecepcionOperativaRP3
from SERVICIOS.bandeja_trabajo_piloto_11 import BandejaTrabajoPiloto11


class ConsolaRecepcionPiloto1:
    def __init__(self, base_dir: Path, core=None):
        self.base_dir = Path(base_dir)
        self.core = core or HostAICore(self.base_dir)
        self.service = RecepcionInteligentePiloto1(self.base_dir)
        self.service_rp3 = RecepcionOperativaRP3(self.core)
        self.bandeja = BandejaTrabajoPiloto11(self.base_dir)
        self._contexto_documento = {}

    def ejecutar(self, input_fn: Callable[[str], str] = input, print_fn: Callable[..., None] = print) -> None:
        while True:
            print_fn("\nRECEPCIONES — HA LLEGADO MERCANCÍA")
            print_fn("1. Ha llegado un proveedor")
            print_fn("2. Recibir un pedido esperado")
            print_fn("3. Continuar una recepción pendiente")
            print_fn("4. Ver recepciones pendientes")
            print_fn("5. Ver historial o detalle")
            print_fn("\nOPCIONES TÉCNICAS")
            print_fn("9. Diagnóstico aislado")
            print_fn("0. Volver")
            op = input_fn("Elige una opción: ").strip()
            if op == "9":
                print_fn(formatear_diagnostico_piloto1(self.service.diagnostico()))
            elif op == "1":
                self._nueva(input_fn, print_fn)
            elif op == "2":
                self._recepcion_por_pedido(input_fn, print_fn)
            elif op == "3":
                self._retomar(input_fn, print_fn)
            elif op == "4":
                self._listar_pendientes(print_fn)
            elif op == "5":
                self._mostrar_historial(input_fn, print_fn)
            elif op == "0":
                return
            else:
                print_fn("Opción no válida.")

    def _recepcion_por_pedido(self, input_fn, print_fn) -> None:
        pedidos = [p for p in self.core.compras.listar_pedidos() if p.get("estado") in {"borrador", "preparado", "enviado"}]
        if not pedidos:
            self._mostrar_sin_pedidos(print_fn)
            return
        print_fn("\nPEDIDOS ABIERTOS")
        for i, p in enumerate(pedidos, 1):
            print_fn(f"{i}. {p.get('id')} | {p.get('proveedor')} | {p.get('estado')} | {p.get('total_lineas', 0)} linea(s)")
        raw = input_fn("Selecciona pedido (0=cancelar): ").strip()
        if raw == "0":
            return
        if not raw.isdigit() or not 1 <= int(raw) <= len(pedidos):
            print_fn("Selección no válida.")
            return
        pedido = pedidos[int(raw) - 1]
        proveedor_llegada = input_fn(f"Proveedor que llega [{pedido.get('proveedor')}]: ").strip()
        sesion = self.service_rp3.iniciar_recepcion(pedido["id"], proveedor_llegada)
        print_fn(f"Sesión creada: {sesion['id']}")

        for linea in sesion.get("lineas_esperadas", []):
            print_fn("\n" + "-" * 72)
            print_fn(f"Esperado: {linea['nombre']} | {linea['cantidad_esperada']} {linea['unidad_esperada']} | precio {linea.get('precio_esperado', 0)}")
            print_fn("1. Aceptar completa")
            print_fn("2. Parcial")
            print_fn("3. No recibido")
            print_fn("4. Rechazado")
            print_fn("5. Sustitución")
            op = input_fn("Decisión [1]: ").strip() or "1"

            if op == "1":
                cant = float(input_fn(f"Cantidad recibida [{linea['cantidad_esperada']}]: ").strip() or str(linea["cantidad_esperada"]))
                uni = input_fn(f"Unidad [{linea['unidad_esperada']}]: ").strip() or linea["unidad_esperada"]
                precio = input_fn(f"Precio [{linea.get('precio_esperado', 0)}]: ").strip()
                lote = input_fn("Lote (opcional): ").strip()
                cad = input_fn("Caducidad (AAAA-MM-DD, opcional): ").strip()
                self.service_rp3.actualizar_linea_esperada(
                    sesion["id"], linea["linea_id"],
                    cantidad_recibida=cant,
                    unidad_recibida=uni,
                    precio_recibido=(float(precio.replace(",", ".")) if precio else linea.get("precio_esperado", 0)),
                    lote=lote,
                    caducidad=cad,
                    estado_linea="aceptada",
                )
            elif op == "2":
                cant = float(input_fn("Cantidad recibida: ").strip() or "0")
                uni = input_fn(f"Unidad [{linea['unidad_esperada']}]: ").strip() or linea["unidad_esperada"]
                precio = input_fn(f"Precio [{linea.get('precio_esperado', 0)}]: ").strip()
                motivo = input_fn("Motivo parcial: ").strip()
                self.service_rp3.actualizar_linea_esperada(
                    sesion["id"], linea["linea_id"],
                    cantidad_recibida=cant,
                    unidad_recibida=uni,
                    precio_recibido=(float(precio.replace(",", ".")) if precio else linea.get("precio_esperado", 0)),
                    estado_linea="parcial",
                    motivo=motivo,
                )
            elif op == "3":
                motivo = input_fn("Motivo no recibido: ").strip()
                self.service_rp3.actualizar_linea_esperada(
                    sesion["id"], linea["linea_id"],
                    cantidad_recibida=0,
                    unidad_recibida=linea["unidad_esperada"],
                    precio_recibido=linea.get("precio_esperado", 0),
                    estado_linea="no_recibida",
                    motivo=motivo,
                )
            elif op == "4":
                motivo = input_fn("Motivo rechazo: ").strip()
                self.service_rp3.actualizar_linea_esperada(
                    sesion["id"], linea["linea_id"],
                    cantidad_recibida=0,
                    unidad_recibida=linea["unidad_esperada"],
                    precio_recibido=linea.get("precio_esperado", 0),
                    estado_linea="rechazada",
                    motivo=motivo,
                )
            elif op == "5":
                nombre_s = input_fn("Nombre producto sustituto: ").strip()
                art_s = input_fn("Articulo ID sustituto (opcional): ").strip()
                cant = float(input_fn("Cantidad recibida: ").strip() or "0")
                uni = input_fn(f"Unidad [{linea['unidad_esperada']}]: ").strip() or linea["unidad_esperada"]
                precio = input_fn(f"Precio [{linea.get('precio_esperado', 0)}]: ").strip()
                lote = input_fn("Lote (opcional): ").strip()
                cad = input_fn("Caducidad (AAAA-MM-DD, opcional): ").strip()
                self.service_rp3.actualizar_linea_esperada(
                    sesion["id"], linea["linea_id"],
                    cantidad_recibida=cant,
                    unidad_recibida=uni,
                    precio_recibido=(float(precio.replace(",", ".")) if precio else linea.get("precio_esperado", 0)),
                    lote=lote,
                    caducidad=cad,
                    estado_linea="sustitucion",
                    articulo_id_recibido=art_s,
                    nombre_recibido=nombre_s,
                )
            else:
                print_fn("Opción no válida. Se deja como pendiente.")

        add = input_fn("¿Registrar producto adicional? (s/n): ").strip().lower()
        while add in {"s", "si", "sí"}:
            nombre = input_fn("Nombre producto adicional: ").strip()
            cant = float(input_fn("Cantidad: ").strip() or "0")
            uni = input_fn("Unidad: ").strip() or "ud"
            precio = float((input_fn("Precio unitario [0]: ").strip() or "0").replace(",", "."))
            art = input_fn("Articulo ID (opcional): ").strip()
            lote = input_fn("Lote (opcional): ").strip()
            cad = input_fn("Caducidad (AAAA-MM-DD, opcional): ").strip()
            motivo = input_fn("Motivo adicional (opcional): ").strip()
            self.service_rp3.registrar_adicional(
                sesion["id"],
                nombre=nombre,
                cantidad=cant,
                unidad=uni,
                precio_unitario=precio,
                articulo_id=art,
                lote=lote,
                caducidad=cad,
                motivo=motivo,
            )
            add = input_fn("¿Registrar otro adicional? (s/n): ").strip().lower()

        preview = self.service_rp3.preparar_validacion(sesion["id"])
        print_fn("\nQUÉ DEBES REVISAR")
        print_fn("=" * 72)
        self._mostrar_resumen_diferencias(preview, print_fn)
        confirmar = input_fn("Escribe RECEPCIONAR para aplicar: ").strip()
        try:
            resultado = self.service_rp3.finalizar_recepcion(sesion["id"], confirmar)
        except ValueError:
            print_fn("Recepción no aplicada. La sesión conserva lo revisado para continuar después.")
            print_fn("Siguiente paso: vuelve a Recepciones y elige 'Continuar una recepción pendiente'.")
            return
        print_fn(resultado.get("mensaje", ""))
        if resultado.get("ok"):
            self._mostrar_final_rp3(resultado, preview, input_fn, print_fn)
        else:
            print_fn("No se ha aplicado la recepción; el stock y el pedido mantienen su estado anterior.")
            print_fn("Siguiente paso: revisa las diferencias e inténtalo de nuevo, o continúa la recepción más tarde.")

    def _mostrar_sin_pedidos(self, print_fn) -> None:
        print_fn("\nNo hay pedidos pendientes de recibir.")
        avisos = []
        for plan in self.core.produccion_real.listar_planes():
            for tarea in plan.get("tareas", []) or []:
                if str(tarea.get("bloqueo") or "").strip():
                    avisos.append(f"Producción bloqueada: {tarea.get('titulo')} — {tarea.get('bloqueo')}")
        eventos = [e for e in self.core.eventos.listar_eventos() if str(getattr(e, "estado", "")).lower() not in {"cancelado", "cerrado"}]
        if avisos:
            print_fn(f"Atención: {avisos[0]}")
        elif eventos:
            print_fn(f"Hay {len(eventos)} evento(s) abierto(s); revisa si la mercancía llegó sin pedido registrado.")
        print_fn("Puedes:")
        print_fn("1. Registrar una recepción manual con 'Ha llegado un proveedor'.")
        print_fn("2. Revisar pedidos y necesidades desde Compras.")
        print_fn("3. Volver a la jornada.")
        print_fn("4. Ver recepciones pendientes.")
        print_fn("Siguiente acción recomendada: si la mercancía está delante, usa la recepción manual.")

    @staticmethod
    def _mostrar_resumen_diferencias(preview: dict, print_fn) -> None:
        resumen = preview.get("resumen") or {}
        total = int(resumen.get("esperadas", len(preview.get("lineas_esperadas", []))) or 0)
        parciales = int(resumen.get("parciales", 0) or 0)
        no_recibidas = int(resumen.get("no_recibidas", 0) or 0)
        rechazadas = int(resumen.get("rechazadas", 0) or 0)
        aceptadas = int(resumen.get("aceptadas", 0) or 0)
        sustituciones = sum(1 for x in preview.get("lineas_esperadas", []) if x.get("estado_linea") == "sustitucion")
        diferencias = list(preview.get("diferencias") or [])
        precios = sum(1 for x in diferencias if x.get("tipo") == "precio_incorrecto")
        print_fn(f"{preview.get('proveedor_llegada') or preview.get('proveedor_esperado') or 'Proveedor'} — {total} líneas")
        print_fn(f"{aceptadas} correctas")
        if parciales: print_fn(f"{parciales} recibida(s) parcialmente")
        if no_recibidas: print_fn(f"{no_recibidas} no recibida(s)")
        if sustituciones: print_fn(f"{sustituciones} sustituida(s)")
        if rechazadas: print_fn(f"{rechazadas} rechazada(s)")
        if precios: print_fn(f"{precios} diferencia(s) de precio")
        if diferencias:
            print_fn(f"\nRevisa estas {len(diferencias)} diferencias:")
            for diferencia in diferencias[:20]:
                etiquetas = {
                    "cantidad_incorrecta": "Cantidad parcial",
                    "no_recibido": "No recibido",
                    "producto_rechazado": "Rechazado",
                    "sustitucion": "Sustituido",
                    "precio_incorrecto": "Precio distinto",
                    "unidad_diferente": "Unidad distinta",
                    "caducidad": "Caducidad a revisar",
                    "lote": "Lote informado",
                    "producto_adicional": "Producto no esperado",
                }
                print_fn(f"- {etiquetas.get(diferencia.get('tipo'), 'Diferencia')}: {diferencia.get('detalle')}")
        else:
            print_fn("Todo coincide con el pedido. Puedes confirmar la recepción.")

    def _mostrar_final_rp3(self, resultado: dict, preview: dict, input_fn, print_fn) -> None:
        registro = resultado.get("registro") or {}
        resumen = preview.get("resumen") or {}
        incidencias = list(registro.get("incidencias") or [])
        print_fn("\nRECEPCIÓN GUARDADA Y STOCK ACTUALIZADO")
        print_fn(f"Llegó: {len(registro.get('entradas_stock', []))} entrada(s) de stock")
        print_fn(f"Parcial: {resumen.get('parciales', 0)} | No recibido: {resumen.get('no_recibidas', 0)} | Rechazado: {resumen.get('rechazadas', 0)}")
        print_fn(f"Precios distintos: {sum(1 for x in incidencias if x.get('tipo') == 'precio_incorrecto')}")
        print_fn(f"Queda pendiente: {sum(int(resumen.get(k, 0) or 0) for k in ('parciales', 'no_recibidas', 'rechazadas'))} línea(s)")
        print_fn("\n¿Qué quieres hacer ahora?")
        print_fn("1. Guardar y cerrar")
        print_fn("2. Revisar diferencias")
        print_fn("3. Continuar con otra recepción")
        print_fn("4. Volver a la jornada")
        opcion = input_fn("Opción [1]: ").strip() or "1"
        if opcion == "2":
            self._mostrar_resumen_diferencias(preview, print_fn)
        elif opcion == "3":
            self._nueva(input_fn, print_fn)
        elif opcion == "4":
            from APP.consola_jornada_piloto_12 import ConsolaJornadaPiloto12
            ConsolaJornadaPiloto12(self.base_dir).ejecutar(input_fn=input_fn, print_fn=print_fn)
        else:
            print_fn("Recepción cerrada. Siguiente paso: continúa con la jornada.")

    def _nueva(self, input_fn, print_fn) -> None:
        print_fn("\nHA LLEGADO UN PROVEEDOR")
        print_fn("Selecciona o arrastra el albarán, factura o documento del proveedor.")
        print_fn("Se leerá primero en vista previa; no se cambiarán precios ni stock sin confirmación.")
        ruta = input_fn("Documento (0=cancelar): ").strip().strip('"')
        if ruta == "0" or not ruta:
            print_fn("Recepción cancelada antes de leer el documento. No se ha modificado ningún dato.")
            return
        print_fn(f"Documento elegido: {Path(ruta).name}")
        proveedor = input_fn("Proveedor [detectar por documento/nombre]: ").strip()
        self._contexto_documento = {"ruta": ruta, "proveedor": proveedor, "estado": "leyendo"}
        try:
            plan = self.service.preparar(ruta, proveedor=proveedor)
        except (ValueError, FileNotFoundError, OSError) as exc:
            mensaje = str(exc).lower()
            if "texto extraíble" in mensaje or "ocr/manual" in mensaje or Path(ruta).suffix.lower() in {".png", ".jpg", ".jpeg"}:
                self._documento_sin_texto(ruta, proveedor, input_fn, print_fn)
            else:
                self._contexto_documento["estado"] = "fallo_lectura"
                print_fn(f"No he podido leer el documento: {exc}")
                print_fn("El proveedor y la ruta siguen disponibles durante esta recepción.")
                print_fn("Siguiente paso: comprueba el archivo, carga otra versión o cancela sin aplicar cambios.")
            return
        self._contexto_documento["estado"] = "leido"
        self._procesar_plan(plan, input_fn, print_fn)

    def _documento_sin_texto(self, ruta: str, proveedor: str, input_fn, print_fn) -> None:
        self._contexto_documento["estado"] = "pendiente_lectura"
        print_fn("\nEL DOCUMENTO PARECE ESTAR ESCANEADO")
        print_fn("No contiene texto extraíble. Aún no se ha modificado ningún dato.")

        ocr = getattr(self.core, "motor_ocr_simulado", None)
        if ocr is not None:
            try:
                resultado = ocr.extraer_texto(ruta)
                texto = str(resultado.get("texto_extraido") or "").strip()
            except (ValueError, FileNotFoundError, OSError):
                texto = ""
            if texto:
                print_fn("He encontrado una lectura OCR asociada anteriormente. La revisaré en vista previa.")
                plan = self.service.preparar(ruta, texto_manual=texto, proveedor=proveedor)
                self._contexto_documento["estado"] = "leido_con_ocr_existente"
                self._procesar_plan(plan, input_fn, print_fn)
                return

        print_fn("No hay lectura visual automática disponible en este entorno.")
        print_fn("1. Cargar otra versión del documento")
        print_fn("2. Introducir solo los productos esenciales")
        print_fn("3. Mantener el contexto y continuar después")
        print_fn("0. Cancelar sin aplicar cambios")
        opcion = input_fn("Elige una opción: ").strip()
        if opcion == "1":
            self._nueva(input_fn, print_fn)
        elif opcion == "2":
            texto = self._capturar_lineas_esenciales(input_fn, print_fn)
            if not texto:
                print_fn("No se introdujeron productos. La recepción sigue pendiente de lectura y no se aplicó nada.")
                return
            plan = self.service.preparar(ruta, texto_manual=texto, proveedor=proveedor)
            self._contexto_documento["estado"] = "leido_manual_esencial"
            self._procesar_plan(plan, input_fn, print_fn)
        elif opcion == "3":
            print_fn("Conservo el proveedor y el documento durante esta sesión.")
            print_fn("Siguiente paso: carga otra versión o introduce las líneas esenciales cuando puedas.")
        else:
            self._contexto_documento["estado"] = "cancelado"
            print_fn("Lectura cancelada. No se ha modificado ningún dato.")

    @staticmethod
    def _capturar_lineas_esenciales(input_fn, print_fn) -> str:
        print_fn("Introduce una línea por producto: nombre ; cantidad ; unidad ; precio opcional")
        print_fn("Escribe FIN cuando hayas terminado o FIN directamente para cancelar.")
        lineas = []
        while True:
            linea = input_fn("Producto: ").strip()
            if linea.upper() == "FIN":
                break
            if linea:
                lineas.append(linea)
        return "\n".join(lineas)

    def _procesar_plan(self, plan, input_fn, print_fn) -> None:
        self._mostrar(plan, print_fn)
        self._revisar(plan, input_fn, print_fn)
        path = self.service.guardar_plan(plan)
        if plan["estado"] != "LISTA_PARA_CONFIRMAR":
            self.bandeja.registrar_recepcion_pendiente(plan, "Recepción pendiente de resolver dudas.")
            print_fn(f"Recepción guardada para continuar después: {path}")
            print_fn("Hay productos que no he podido identificar. Revísalos desde 'Continuar una recepción pendiente'.")
            return
        print_fn("\n¿Qué quieres hacer ahora?")
        print_fn("1. Actualizar precios y stock ahora")
        print_fn("2. Guardar la recepción y actualizar al final del día")
        print_fn("3. Guardar solo como pendiente")
        decision = input_fn("Opción [2]: ").strip() or "2"
        if decision != "1":
            motivo = "Actualizar precios y stock al final del día" if decision == "2" else "Recepción guardada pendiente de decisión"
            self.bandeja.registrar_recepcion_pendiente(plan, motivo)
            print_fn("Recepción guardada. Aparece en la Bandeja de trabajo y no se ha actualizado el stock.")
            print_fn("Siguiente paso: continúa con otra recepción o vuelve a la jornada.")
            return
        confirm = input_fn("Escribe RECEPCIONAR para actualizar precios, stock y guardar la factura: ")
        if confirm.strip().upper() != "RECEPCIONAR":
            self.bandeja.registrar_recepcion_pendiente(plan, "Confirmación cancelada; recepción pendiente.")
            print_fn("Operación cancelada. La recepción queda en la Bandeja de trabajo.")
            return
        try:
            result = self.service.aplicar(plan, confirm)
        except Exception:
            print_fn("No he podido terminar la recepción.")
            print_fn("No des por actualizados el stock ni los precios. El documento guardado permite volver a revisarla.")
            print_fn("Siguiente paso: abre 'Continuar una recepción pendiente' y comprueba las líneas antes de repetir.")
            return
        print_fn("\nRECEPCIÓN GUARDADA Y STOCK ACTUALIZADO")
        print_fn(f"Productos nuevos: {result['articulos_creados']} | Precios actualizados: {result['precios_actualizados']} | Entradas de stock: {result['entradas_stock']}")
        print_fn("Siguiente paso: guarda el documento del proveedor y continúa con la jornada.")

    def _listar_pendientes(self, print_fn) -> list[Path]:
        folder = self.base_dir / "DATOS" / "piloto" / "recepciones"
        results = {p.name.replace("_resultado.json", "") for p in folder.glob("*_resultado.json")} if folder.exists() else set()
        paths=[]
        if folder.exists():
            for p in sorted(folder.glob("REC-*.json")):
                if p.name.endswith("_resultado.json") or p.stem in results: continue
                try:
                    data=json.loads(p.read_text(encoding="utf-8"))
                except Exception: continue
                if data.get("estado") in {"LISTA_PARA_CONFIRMAR","REQUIERE_REVISION"}:
                    paths.append(p)
                    print_fn(f"{len(paths)}. {data.get('proveedor') or '-'} | {data.get('plan_id')} | {data.get('estado')} | {data.get('resumen',{}).get('lineas',0)} líneas")
        if not paths:
            print_fn("No hay recepciones pendientes.")
            print_fn("Estado actual: todo lo guardado está resuelto o aplicado.")
            print_fn("Siguiente paso: registra la mercancía que acaba de llegar o vuelve a la jornada.")
        return paths

    def _mostrar_historial(self, input_fn, print_fn) -> None:
        registros = list(self.service_rp3._leer_lista(self.service_rp3.path_registros))
        resultados = sorted((self.base_dir / "DATOS" / "piloto" / "recepciones").glob("*_resultado.json")) if (self.base_dir / "DATOS" / "piloto" / "recepciones").exists() else []
        print_fn("\nHISTORIAL DE RECEPCIONES")
        if not registros and not resultados:
            print_fn("Todavía no hay recepciones terminadas.")
            print_fn("Siguiente paso: usa 'Ha llegado un proveedor' o recibe un pedido esperado.")
            return
        for i, registro in enumerate(registros, 1):
            print_fn(f"{i}. {registro.get('proveedor_llegada') or registro.get('proveedor_esperado') or '-'} | {registro.get('pedido_id')} | {len(registro.get('entradas_stock', []))} entradas | {len(registro.get('incidencias', []))} diferencias")
        if resultados:
            print_fn(f"Recepciones documentales terminadas: {len(resultados)}")
        input_fn("Pulsa Intro para volver: ")

    def _retomar(self, input_fn, print_fn) -> None:
        paths=self._listar_pendientes(print_fn)
        if not paths: return
        raw=input_fn("Número de recepción: ").strip()
        if not raw.isdigit() or not 1 <= int(raw) <= len(paths):
            print_fn("Selección no válida."); return
        plan=json.loads(paths[int(raw)-1].read_text(encoding="utf-8"))
        self._procesar_plan(plan,input_fn,print_fn)

    @staticmethod
    def _mostrar(plan, print_fn):
        print_fn("\nVISTA PREVIA — NO SE HAN MODIFICADO DATOS")
        print_fn("="*78)
        print_fn(f"Proveedor: {plan['proveedor'] or '-'} | Líneas detectadas: {plan['resumen']['lineas']}")
        print_fn(f"Reconocidas: {plan['resumen']['exactas']} | Dudosas: {plan['resumen']['probables']} | Sin identificar: {plan['resumen']['pendientes']}")
        for x in plan["lineas"]:
            target = x["articulo_nombre"] or "No he podido identificar este producto"
            print_fn(f"{x['numero']}. {x['descripcion']} | {x['cantidad']} {x['unidad']} | {x.get('precio_unitario')} € | {target}")

    def _revisar(self, plan, input_fn, print_fn):
        pending = [x for x in plan["lineas"] if x["estado"] in {"PROBABLE", "SIN_RESOLVER"}]
        for line in pending:
            print_fn(f"\nLínea {line['numero']}: {line['descripcion']}")
            candidates = self.service.buscar_articulos(line["descripcion"], plan.get("proveedor", ""))
            for i, art in enumerate(candidates[:5],1):
                print_fn(f"{i}. {art.get('nombre')} | {art.get('proveedor') or '-'} | {round(art['confianza']*100)}%")
            print_fn("V=número para vincular | C=crear artículo | O=omitir | P=dejar pendiente")
            op=input_fn("Decisión: ").strip().upper()
            if op.isdigit() and 1 <= int(op) <= min(5,len(candidates)):
                self.service.actualizar_decision(plan,line["numero"],"VINCULAR",candidates[int(op)-1])
            elif op=="C":
                name=input_fn(f"Nombre [{line['descripcion']}]: ").strip() or line["descripcion"]
                unit=input_fn(f"Unidad [{line['unidad']}]: ").strip() or line["unidad"]
                self.service.actualizar_decision(plan,line["numero"],"CREAR",nombre_nuevo=name,unidad=unit)
            elif op=="O":
                self.service.actualizar_decision(plan,line["numero"],"OMITIR")
            elif op=="P":
                print_fn("La línea queda pendiente.")
            else:
                print_fn("No he entendido la decisión. Esta línea queda pendiente y todavía no se actualizará el stock.")
                print_fn("Siguiente paso: elige un producto, créalo, omite la línea o déjala pendiente de forma explícita.")


__all__=["ConsolaRecepcionPiloto1"]
