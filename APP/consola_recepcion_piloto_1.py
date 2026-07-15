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

    def ejecutar(self, input_fn: Callable[[str], str] = input, print_fn: Callable[..., None] = print) -> None:
        while True:
            print_fn("\nRECEPCIONES — ¿QUÉ QUIERES HACER?")
            print_fn("1. Añadir una factura, albarán o recepción")
            print_fn("2. Retomar una recepción pendiente")
            print_fn("3. Ver recepciones pendientes")
            print_fn("4. Recepción guiada desde pedido esperado (RP-3)")
            print_fn("9. Diagnóstico aislado")
            print_fn("0. Volver")
            op = input_fn("Elige una opción: ").strip()
            if op == "9":
                print_fn(formatear_diagnostico_piloto1(self.service.diagnostico()))
            elif op == "1":
                self._nueva(input_fn, print_fn)
            elif op == "2":
                self._retomar(input_fn, print_fn)
            elif op == "3":
                self._listar_pendientes(print_fn)
            elif op == "4":
                self._recepcion_por_pedido(input_fn, print_fn)
            elif op == "0":
                return
            else:
                print_fn("Opción no válida.")

    def _recepcion_por_pedido(self, input_fn, print_fn) -> None:
        pedidos = [p for p in self.core.compras.listar_pedidos() if p.get("estado") in {"borrador", "preparado", "enviado"}]
        if not pedidos:
            print_fn("No hay pedidos abiertos para recepcionar.")
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
        print_fn("\nVALIDACIÓN RECEPCIÓN RP-3")
        print_fn("=" * 72)
        print_fn(f"Pedido esperado: {preview['pedido_id']} | Proveedor esperado: {preview['proveedor_esperado']} | Llegada: {preview['proveedor_llegada']}")
        print_fn(f"Diferencias detectadas: {len(preview.get('diferencias', []))}")
        for d in preview.get("diferencias", [])[:20]:
            print_fn(f"- {d.get('tipo')}: {d.get('detalle')}")
        print_fn(f"Stock antes: {preview.get('stock_antes', {}).get('total_items', 0)} articulo(s), {preview.get('stock_antes', {}).get('total_lotes', 0)} lote(s)")
        confirmar = input_fn("Escribe RECEPCIONAR para aplicar: ").strip()
        resultado = self.service_rp3.finalizar_recepcion(sesion["id"], confirmar)
        print_fn(resultado.get("mensaje", ""))
        if resultado.get("ok"):
            reg = resultado.get("registro", {})
            print_fn(f"Entradas stock: {len(reg.get('entradas_stock', []))} | Incidencias: {len(reg.get('incidencias', []))}")
            print_fn(f"Stock después: {resultado.get('stock_despues', {}).get('total_items', 0)} articulo(s), {resultado.get('stock_despues', {}).get('total_lotes', 0)} lote(s)")

    def _nueva(self, input_fn, print_fn) -> None:
        ruta = input_fn("Ruta del documento (PDF/Excel/CSV/TXT/imagen): ").strip().strip('"')
        proveedor = input_fn("Proveedor [detectar por documento/nombre]: ").strip()
        texto_manual = ""
        if Path(ruta).suffix.lower() in {".png", ".jpg", ".jpeg"}:
            print_fn("Pega el texto leído/OCR. Termina con una línea que contenga solo FIN.")
            lines=[]
            while True:
                x=input_fn("")
                if x.strip().upper()=="FIN": break
                lines.append(x)
            texto_manual="\n".join(lines)
        plan = self.service.preparar(ruta, texto_manual=texto_manual, proveedor=proveedor)
        self._procesar_plan(plan, input_fn, print_fn)

    def _procesar_plan(self, plan, input_fn, print_fn) -> None:
        self._mostrar(plan, print_fn)
        self._revisar(plan, input_fn, print_fn)
        path = self.service.guardar_plan(plan)
        if plan["estado"] != "LISTA_PARA_CONFIRMAR":
            self.bandeja.registrar_recepcion_pendiente(plan, "Recepción pendiente de resolver dudas.")
            print_fn(f"Recepción guardada en la bandeja: {path}")
            return
        print_fn("\n¿Qué quieres hacer ahora?")
        print_fn("1. Actualizar precios y stock ahora")
        print_fn("2. Guardar la recepción y actualizar al final del día")
        print_fn("3. Guardar solo como pendiente")
        decision = input_fn("Opción [2]: ").strip() or "2"
        if decision != "1":
            motivo = "Actualizar precios y stock al final del día" if decision == "2" else "Recepción guardada pendiente de decisión"
            self.bandeja.registrar_recepcion_pendiente(plan, motivo)
            print_fn("Recepción guardada. Aparece en la Bandeja de trabajo.")
            return
        confirm = input_fn("Escribe RECEPCIONAR para actualizar precios, stock y guardar la factura: ")
        if confirm.strip().upper() != "RECEPCIONAR":
            self.bandeja.registrar_recepcion_pendiente(plan, "Confirmación cancelada; recepción pendiente.")
            print_fn("Operación cancelada. La recepción queda en la Bandeja de trabajo.")
            return
        result = self.service.aplicar(plan, confirm)
        print_fn("\nRECEPCIÓN COMPLETADA")
        print_fn(f"Estado: {result['estado']} | Integridad: {result['integridad']}")
        print_fn(f"Artículos creados: {result['articulos_creados']} | Precios: {result['precios_actualizados']} | Entradas stock: {result['entradas_stock']}")
        print_fn(f"Backup: {result['backup']}")

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
        if not paths: print_fn("No hay recepciones pendientes.")
        return paths

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
        print_fn(f"Proveedor: {plan['proveedor'] or '-'} | Líneas: {plan['resumen']['lineas']} | Estado: {plan['estado']}")
        for x in plan["lineas"]:
            target = x["articulo_nombre"] or "SIN VINCULAR"
            print_fn(f"{x['numero']}. [{x['estado']}] {x['descripcion']} | {x['cantidad']} {x['unidad']} | {x.get('precio_unitario')} € | → {target} | {round(x['confianza']*100)}%")

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
                print_fn("Sin decisión: la recepción permanecerá bloqueada.")


__all__=["ConsolaRecepcionPiloto1"]
