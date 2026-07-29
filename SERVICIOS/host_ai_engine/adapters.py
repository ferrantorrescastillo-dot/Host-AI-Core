from __future__ import annotations

from pathlib import Path
from typing import Any

from SERVICIOS.biblioteca_escandallos_601 import BibliotecaEscandallos601
from SERVICIOS.biblioteca_menus_601 import BibliotecaMenus601
from SERVICIOS.biblioteca_recetas_601 import RepositorioBibliotecaRecetas601
from SERVICIOS.centro_importacion_601 import FlujoImportacionUnificado601, LectorTexto601
from SERVICIOS.host_ai_engine.models import (
    HostAIEngineRequest,
    INC_CAPACIDAD_NO_IMPLEMENTADA,
    INC_DATO_AMBIGUO,
    INC_DATO_OBLIGATORIO_AUSENTE,
)
from SERVICIOS.host_ai_engine.providers import SimulatedProvider
from SERVICIOS.repositorio_productos_maestro_601 import RepositorioProductosMaestro601


class HostAIAgentRouter:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.repo_productos = RepositorioProductosMaestro601(self.base_dir)
        self.repo_recetas = RepositorioBibliotecaRecetas601(self.base_dir)
        self.biblioteca_escandallos = BibliotecaEscandallos601(self.base_dir)
        self.biblioteca_menus = BibliotecaMenus601(self.base_dir)
        self.importacion = FlujoImportacionUnificado601(self.base_dir)
        self.simulator = SimulatedProvider()

    @staticmethod
    def _respuesta(ok: bool, **kwargs: Any) -> dict[str, Any]:
        return {"ok": ok, **kwargs}

    @staticmethod
    def _norm(txt: Any) -> str:
        return " ".join(str(txt or "").strip().lower().split())

    def ejecutar_paso(
        self,
        solicitud,
        step,
        dependency_results: dict[int, dict[str, Any]],
        confirmation_scope: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if str((solicitud.datos_de_entrada or {}).get("forzar_error_step") or "") == str(step.operacion):
            raise RuntimeError(f"Error forzado para paso {step.operacion}")

        operation = str(step.operacion or "")
        mapping = {
            "analizar_origen": self._importacion_analizar_origen,
            "preparar_importacion": self._importacion_preparar_importacion,
            "listar_incidencias": self._importacion_listar_incidencias,
            "buscar_producto": self._catalogo_buscar_producto,
            "detectar_similares": self._catalogo_detectar_similares,
            "revisar_datos_producto": self._catalogo_revisar_datos_producto,
            "proponer_alta_producto": self._catalogo_proponer_alta_producto,
            "modificar_precio_autorizado": self._catalogo_modificar_precio_autorizado,
            "buscar_receta": self._recetas_buscar_receta,
            "revisar_completitud": self._recetas_revisar_completitud,
            "proponer_receta": self._recetas_proponer_receta,
            "preparar_duplicado": self._recetas_preparar_duplicado,
            "crear_recetas_autorizadas": self._recetas_crear_recetas_autorizadas,
            "buscar_escandallo": self._escandallos_buscar,
            "simular_calculo": self._escandallos_simular,
            "detectar_desactualizacion": self._escandallos_detectar_desactualizacion,
            "detectar_afectados_producto": self._escandallos_detectar_afectados_producto,
            "proponer_recalculo": self._escandallos_proponer_recalculo,
            "generar_escandallos_autorizados": self._escandallos_generar_autorizados,
            "recalcular_impactados_autorizado": self._escandallos_recalcular_impactados_autorizado,
            "buscar_menu": self._menus_buscar,
            "calcular_rentabilidad": self._menus_rentabilidad,
            "detectar_incidencias": self._menus_incidencias,
            "proponer_duplicado": self._menus_proponer_duplicado,
            "detectar_afectados_escandallos": self._menus_detectar_afectados_escandallos,
            "proponer_menu": self._menus_proponer_menu,
            "crear_menu_autorizado": self._menus_crear_menu_autorizado,
            "registrar_historico_menu": self._menus_registrar_historico_menu,
            "actualizar_menus_afectados": self._menus_actualizar_menus_afectados,
            "detectar_pendiente_menu": self._menus_detectar_pendiente_menu,
        }
        fn = mapping.get(operation)
        if fn:
            return fn(solicitud, step, dependency_results, confirmation_scope or {})
        return self._simulado(solicitud, step, dependency_results)

    def _importacion_analizar_origen(self, solicitud, step, dependency_results, confirmation_scope):
        texto = str(step.entradas.get("texto_importacion") or solicitud.texto_original or "").strip()
        if not texto and not str(step.entradas.get("origen_documento") or "").strip():
            return self._respuesta(False, incidencias=[{"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "Falta origen o contenido para analizar importación."}])
        formato = str(step.entradas.get("formato_entrada") or solicitud.formato_entrada or "texto").lower()
        tipo = "RECETAS"
        normalizado = self._norm(texto)
        if "menu:" in normalizado or "menú:" in normalizado:
            tipo = "MENUS"
        elif "escandallo" in normalizado:
            tipo = "ESCANDALLOS"
        return self._respuesta(True, formato_detectado=formato, tipo_contenido_sugerido=tipo, origen_analizado=step.entradas.get("origen_documento") or solicitud.origen)

    def _importacion_preparar_importacion(self, solicitud, step, dependency_results, confirmation_scope):
        base = dependency_results.get(1, {})
        tipo = str(step.entradas.get("tipo_contenido") or base.get("tipo_contenido_sugerido") or "RECETAS").upper()
        texto = str(step.entradas.get("texto_importacion") or solicitud.texto_original or "").strip()
        if not texto:
            return self._respuesta(False, incidencias=[{"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "Falta texto para preparar la importación."}])
        if tipo == "MENUS":
            doc = self.importacion.crear_documento_menus_desde_texto(texto)
        elif tipo == "ESCANDALLOS":
            doc = self.importacion.crear_documento_escandallos_desde_texto(texto)
        else:
            doc = LectorTexto601().leer(texto)
        contexto = self.importacion.ejecutar(doc)
        return self._respuesta(True, contexto_importacion=contexto, tipo_contenido=tipo)

    def _importacion_listar_incidencias(self, solicitud, step, dependency_results, confirmation_scope):
        contexto = (dependency_results.get(2) or {}).get("contexto_importacion") or {}
        incidencias = list(contexto.get("incidencias") or [])
        return self._respuesta(True, incidencias=incidencias, total=len(incidencias))

    def _catalogo_buscar_producto(self, solicitud, step, dependency_results, confirmation_scope):
        nombre = str(step.entradas.get("nombre") or step.entradas.get("codigo") or "").strip()
        if not nombre:
            return self._respuesta(False, incidencias=[{"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "Falta nombre o código de producto."}])
        encontrados = self.repo_productos.buscar_productos({"nombre": nombre, "codigo": nombre})
        if len(encontrados) > 1:
            return self._respuesta(False, incidencias=[{"tipo": INC_DATO_AMBIGUO, "detalle": f"Hay {len(encontrados)} productos posibles para '{nombre}'."}], candidatos=encontrados[:10])
        return self._respuesta(True, productos=encontrados, total=len(encontrados))

    def _catalogo_detectar_similares(self, solicitud, step, dependency_results, confirmation_scope):
        contexto = (dependency_results.get(2) or {}).get("contexto_importacion") or {}
        recetas = list(contexto.get("recetas") or [])
        salida: list[dict[str, Any]] = []
        vistos: set[str] = set()
        for receta in recetas:
            for ingrediente in list(receta.get("ingredientes") or []):
                clave = self._norm(ingrediente)
                if not clave or clave in vistos:
                    continue
                vistos.add(clave)
                encontrados = self.repo_productos.buscar_productos({"nombre": ingrediente})
                salida.append({
                    "ingrediente": ingrediente,
                    "total_coincidencias": len(encontrados),
                    "coincidencias": [{"codigo": p.get("codigo"), "nombre": p.get("nombre")} for p in encontrados[:5]],
                })
        return self._respuesta(True, analisis=salida, total=len(salida))

    def _catalogo_revisar_datos_producto(self, solicitud, step, dependency_results, confirmation_scope):
        producto = dict(step.entradas.get("producto") or {})
        faltantes = [k for k in ["nombre", "unidad_base", "precio"] if not str(producto.get(k) or "").strip()]
        return self._respuesta(True, producto=producto, faltantes=faltantes, completo=not faltantes)

    def _catalogo_proponer_alta_producto(self, solicitud, step, dependency_results, confirmation_scope):
        producto = dict(step.entradas.get("producto") or {})
        return self._respuesta(True, propuesta={"accion": "crear_producto_autorizado", "producto": producto, "persistido": False})

    def _catalogo_modificar_precio_autorizado(self, solicitud, step, dependency_results, confirmation_scope):
        codigo = str(step.entradas.get("codigo") or step.entradas.get("producto_codigo") or solicitud.datos_de_entrada.get("producto_codigo") or "").strip()
        if not codigo:
            return self._respuesta(False, incidencias=[{"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "Falta código de producto para modificar precio."}])
        cambios = {
            "precio": step.entradas.get("precio") or solicitud.datos_de_entrada.get("precio"),
            "fecha_precio": step.entradas.get("fecha_precio") or solicitud.datos_de_entrada.get("fecha_precio") or "2026-07-23",
        }
        actualizado = self.repo_productos.editar_producto(codigo, cambios)
        return self._respuesta(True, producto_actualizado={"codigo": actualizado.get("codigo"), "nombre": actualizado.get("nombre"), "precio": actualizado.get("precio")})

    def _recetas_buscar_receta(self, solicitud, step, dependency_results, confirmation_scope):
        nombre = str(step.entradas.get("nombre") or step.entradas.get("codigo") or "").strip()
        if not nombre:
            return self._respuesta(False, incidencias=[{"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "Falta referencia de receta."}])
        directa = self.repo_recetas.obtener(nombre)
        if directa:
            return self._respuesta(True, recetas=[directa], total=1)
        encontradas = self.repo_recetas.buscar(nombre=nombre, incluir_archivadas=True)
        if len(encontradas) > 1:
            return self._respuesta(False, incidencias=[{"tipo": INC_DATO_AMBIGUO, "detalle": f"Hay {len(encontradas)} recetas posibles para '{nombre}'."}], candidatos=encontradas[:10])
        return self._respuesta(True, recetas=encontradas, total=len(encontradas))

    def _recetas_revisar_completitud(self, solicitud, step, dependency_results, confirmation_scope):
        receta = dict(step.entradas.get("receta") or {})
        if not receta:
            lista = (dependency_results.get(1) or {}).get("recetas") or []
            receta = dict(lista[0] if lista else {})
        faltantes = [k for k in ["nombre", "ingredientes", "cantidades", "elaboracion"] if not receta.get(k)]
        return self._respuesta(True, receta=receta, faltantes=faltantes, completa=not faltantes)

    def _recetas_proponer_receta(self, solicitud, step, dependency_results, confirmation_scope):
        contexto = (dependency_results.get(2) or {}).get("contexto_importacion") or {}
        propuestas: list[dict[str, Any]] = []
        for receta in list(contexto.get("recetas") or []):
            faltantes = [k for k in ["nombre", "ingredientes", "cantidades", "elaboracion"] if not receta.get(k)]
            propuestas.append({
                "nombre": receta.get("nombre"),
                "codigo": receta.get("codigo") or "",
                "receta": receta,
                "faltantes": faltantes,
                "completa": not faltantes,
                "accion_sugerida": "crear_recetas_autorizadas",
            })
        return self._respuesta(True, propuestas=propuestas, total=len(propuestas))

    def _recetas_preparar_duplicado(self, solicitud, step, dependency_results, confirmation_scope):
        receta = dict(step.entradas.get("receta") or {})
        return self._respuesta(True, propuesta_duplicado={"receta": receta, "persistido": False})

    def _recetas_crear_recetas_autorizadas(self, solicitud, step, dependency_results, confirmation_scope):
        propuestas = list((dependency_results.get(4) or {}).get("propuestas") or [])
        if not propuestas:
            return self._respuesta(False, incidencias=[{"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "No hay propuestas de receta para crear."}])
        permitidas = set(str(x).strip().lower() for x in list((confirmation_scope or {}).get("recetas_autorizadas") or []))
        creadas: list[dict[str, Any]] = []
        rechazadas: list[dict[str, Any]] = []
        errores: list[str] = []
        for propuesta in propuestas:
            nombre = str(propuesta.get("nombre") or "").strip()
            if permitidas and self._norm(nombre) not in permitidas and self._norm(str(propuesta.get("codigo") or "")) not in permitidas:
                rechazadas.append({"nombre": nombre, "motivo": "Fuera del alcance autorizado"})
                continue
            resultado = self.repo_recetas.crear(dict(propuesta.get("receta") or {}))
            if resultado.get("ok"):
                creada = dict((resultado.get("receta") or {}))
                creadas.append({"nombre": creada.get("nombre"), "codigo": creada.get("codigo")})
            else:
                errores.extend(list(resultado.get("errores") or []))
        return self._respuesta(True, creadas=creadas, omitidas=rechazadas, errores_creacion=errores)

    def _escandallos_buscar(self, solicitud, step, dependency_results, confirmation_scope):
        filtros = dict(step.entradas or {})
        return self.biblioteca_escandallos.buscar(filtros)

    def _escandallos_simular(self, solicitud, step, dependency_results, confirmation_scope):
        creadas = list((dependency_results.get(6) or {}).get("creadas") or [])
        if not creadas:
            return self._respuesta(True, simulaciones=[], total=0)
        resultados: list[dict[str, Any]] = []
        for receta in creadas:
            ref = str(receta.get("codigo") or receta.get("nombre") or "")
            sim = self.biblioteca_escandallos.generar_desde_receta(ref, simular=True)
            resultados.append({"receta": ref, "resultado": sim})
        return self._respuesta(True, simulaciones=resultados, total=len(resultados))

    def _escandallos_detectar_desactualizacion(self, solicitud, step, dependency_results, confirmation_scope):
        ref = str(step.entradas.get("id_o_codigo") or "").strip()
        if not ref:
            return self._respuesta(False, incidencias=[{"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "Falta identificador de escandallo."}])
        return self.biblioteca_escandallos.ver_detalle(ref)

    def _escandallos_proponer_recalculo(self, solicitud, step, dependency_results, confirmation_scope):
        ref = str(step.entradas.get("id_o_codigo") or "").strip()
        return self._respuesta(True, propuesta={"accion": "recalcular_escandallo_persistente", "id_o_codigo": ref, "persistido": False})

    def _escandallos_detectar_afectados_producto(self, solicitud, step, dependency_results, confirmation_scope):
        codigo = str(step.entradas.get("codigo") or solicitud.datos_de_entrada.get("producto_codigo") or "").strip()
        nombre = str(step.entradas.get("nombre") or solicitud.datos_de_entrada.get("producto_nombre") or "").strip()
        afectados: list[dict[str, Any]] = []
        for esc in self.biblioteca_escandallos.repo_esc.listar(incluir_archivados=True):
            for linea in list(esc.get("lineas") or []):
                codigo_linea = str(linea.get("producto_codigo") or "").strip()
                nombre_linea = self._norm(linea.get("nombre_mostrado") or linea.get("producto") or "")
                if (codigo and codigo_linea == codigo) or (nombre and self._norm(nombre) == nombre_linea):
                    afectados.append({"id": esc.get("id"), "codigo": esc.get("codigo"), "nombre": esc.get("nombre")})
                    break
        return self._respuesta(True, escandallos_afectados=afectados, total=len(afectados))

    def _escandallos_generar_autorizados(self, solicitud, step, dependency_results, confirmation_scope):
        creadas = list((dependency_results.get(6) or {}).get("creadas") or [])
        if not creadas:
            creadas = list(step.entradas.get("recetas") or [])
        generados: list[dict[str, Any]] = []
        errores: list[str] = []
        for receta in creadas:
            ref = str(receta.get("codigo") or receta.get("nombre") or receta).strip()
            out = self.biblioteca_escandallos.generar_desde_receta(ref, simular=False)
            if out.get("ok"):
                esc = out.get("escandallo") or {}
                generados.append({"id": esc.get("id"), "codigo": esc.get("codigo"), "nombre": esc.get("nombre")})
            else:
                errores.append(str(out.get("mensaje") or "Error generando escandallo"))
        return self._respuesta(True, escandallos_generados=generados, total=len(generados), errores_generacion=errores)

    def _escandallos_recalcular_impactados_autorizado(self, solicitud, step, dependency_results, confirmation_scope):
        afectados: list[dict[str, Any]] = []
        vistos: set[str] = set()
        for dep in list(step.dependencias or []):
            for esc in list((dependency_results.get(dep) or {}).get("escandallos_afectados") or []):
                clave = str(esc.get("id") or esc.get("codigo") or "").strip()
                if clave and clave not in vistos:
                    vistos.add(clave)
                    afectados.append(esc)
        recalculados: list[dict[str, Any]] = []
        errores: list[str] = []
        for esc in afectados:
            ref = str(esc.get("id") or esc.get("codigo") or "").strip()
            out = self.biblioteca_escandallos.recalcular(ref, 1)
            if out.get("ok"):
                recalculados.append({"id": ref, "resumen": out.get("resumen")})
            else:
                errores.append(str(out.get("mensaje") or "Error recalculando escandallo"))
        return self._respuesta(True, escandallos_recalculados=recalculados, total=len(recalculados), errores_recalculo=errores)

    def _menus_buscar(self, solicitud, step, dependency_results, confirmation_scope):
        return self.biblioteca_menus.buscar(dict(step.entradas or {}))

    def _menus_rentabilidad(self, solicitud, step, dependency_results, confirmation_scope):
        ref = str(step.entradas.get("id_o_codigo") or step.entradas.get("codigo") or "").strip()
        if not ref:
            return self._respuesta(False, incidencias=[{"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "Falta menú para calcular rentabilidad."}])
        return self.biblioteca_menus.rentabilidad(ref)

    def _menus_incidencias(self, solicitud, step, dependency_results, confirmation_scope):
        return self.biblioteca_menus.menus_con_incidencias()

    def _menus_proponer_duplicado(self, solicitud, step, dependency_results, confirmation_scope):
        ref = str(step.entradas.get("id_o_codigo") or "").strip()
        return self._respuesta(True, propuesta={"accion": "duplicar_menu", "id_o_codigo": ref, "persistido": False})

    def _menus_detectar_afectados_escandallos(self, solicitud, step, dependency_results, confirmation_scope):
        escandallos = list((dependency_results.get(step.dependencias[0]) or {}).get("escandallos_generados") or []) if step.dependencias else []
        if not escandallos:
            escandallos = list((dependency_results.get(step.dependencias[0]) or {}).get("escandallos_afectados") or []) if step.dependencias else []
        recetas_creadas = list((dependency_results.get(6) or {}).get("creadas") or []) if 6 in dependency_results else []
        refs_esc = set()
        for x in escandallos:
            refs_esc.add(self._norm(x.get("id") or ""))
            refs_esc.add(self._norm(x.get("codigo") or ""))
            refs_esc.add(self._norm(x.get("nombre") or ""))
        refs_rec = set()
        for x in recetas_creadas:
            refs_rec.add(self._norm(x.get("codigo") or ""))
            refs_rec.add(self._norm(x.get("nombre") or ""))
        afectados: list[dict[str, Any]] = []
        for menu in self.biblioteca_menus.repo.listar(incluir_archivados=True):
            hit = False
            for linea in list(menu.get("lineas") or []):
                snap = dict(linea.get("snapshot_referencia") or {})
                ref = self._norm(snap.get("id") or snap.get("codigo") or snap.get("nombre") or "")
                rec = self._norm(((snap.get("receta") or {}).get("codigo") or (snap.get("receta") or {}).get("nombre") or ""))
                if ref in refs_esc or rec in refs_rec:
                    hit = True
                    break
            if not hit:
                comp = dict(menu.get("composicion") or {})
                for items in comp.values():
                    for item in list(items or []):
                        ref = self._norm(item.get("referencia") or "")
                        if ref in refs_esc or ref in refs_rec:
                            hit = True
                            break
                    if hit:
                        break
            if hit:
                afectados.append({"menu_id": menu.get("menu_id"), "codigo": menu.get("codigo"), "nombre": menu.get("nombre")})
        return self._respuesta(True, menus_afectados=afectados, total=len(afectados))

    def _menus_proponer_menu(self, solicitud, step, dependency_results, confirmation_scope):
        datos = dict(solicitud.datos_de_entrada or {})
        nombre = str(datos.get("nombre_menu") or step.entradas.get("nombre_menu") or "Menú propuesto").strip()
        recetas = list(datos.get("recetas") or step.entradas.get("recetas") or [])
        escandallos = list(datos.get("escandallos") or step.entradas.get("escandallos") or [])
        composicion = {"Aperitivos": [], "Entrantes": [], "Principales": [], "Postres": [], "Bodega": [], "Extras": []}
        for receta in recetas:
            composicion["Principales"].append({"tipo_referencia": "RECETA", "referencia": str(receta), "cantidad": 1})
        for esc in escandallos:
            composicion["Principales"].append({"tipo_referencia": "ESCANDALLO", "referencia": str(esc), "cantidad": 1})
        calc = self.biblioteca_menus.motor.calcular(
            nombre_menu=nombre,
            comensales=float(datos.get("comensales") or step.entradas.get("comensales") or 0.0),
            composicion=composicion,
            precio_venta_comensal=float(datos.get("precio_venta_comensal") or step.entradas.get("precio_venta_comensal") or 0.0),
            precio_venta_total=float(datos.get("precio_venta_total") or step.entradas.get("precio_venta_total") or 0.0),
        )
        return self._respuesta(True, propuesta_menu={"nombre": nombre, "composicion": composicion, "calculo": calc, "persistido": False})

    def _menus_crear_menu_autorizado(self, solicitud, step, dependency_results, confirmation_scope):
        propuesta = dict((dependency_results.get(step.dependencias[0]) or {}).get("propuesta_menu") or {})
        if not propuesta:
            return self._respuesta(False, incidencias=[{"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "No hay propuesta de menú para crear."}])
        calc = dict(propuesta.get("calculo") or {})
        res = self.biblioteca_menus.nuevo_menu(
            {
                "nombre": propuesta.get("nombre"),
                "tipo": str((solicitud.datos_de_entrada or {}).get("tipo_menu") or ""),
                "familia": str((solicitud.datos_de_entrada or {}).get("familia_menu") or ""),
                "comensales_recomendado": float((solicitud.datos_de_entrada or {}).get("comensales") or 0.0),
                "precio_venta_comensal": float((solicitud.datos_de_entrada or {}).get("precio_venta_comensal") or 0.0),
                "precio_venta_total": float((solicitud.datos_de_entrada or {}).get("precio_venta_total") or 0.0),
                "composicion": propuesta.get("composicion") or {},
                "observaciones": "Creado por orquestación ERP Host AI Engine",
            }
        )
        if not res.get("ok"):
            return res
        menu = res.get("menu") or {}
        return self._respuesta(True, menu_creado={"menu_id": menu.get("menu_id"), "codigo": menu.get("codigo"), "nombre": menu.get("nombre"), "coste_total": calc.get("coste_total")})

    def _menus_registrar_historico_menu(self, solicitud, step, dependency_results, confirmation_scope):
        creado = dict((dependency_results.get(step.dependencias[0]) or {}).get("menu_creado") or {})
        if not creado:
            return self._respuesta(False, incidencias=[{"tipo": INC_DATO_OBLIGATORIO_AUSENTE, "detalle": "No hay menú creado para registrar histórico."}])
        out = self.biblioteca_menus.generar_escandallo_menu(str(creado.get("menu_id") or creado.get("codigo") or ""))
        if not out.get("ok"):
            return out
        menu = out.get("menu") or {}
        return self._respuesta(True, menu_historizado={"menu_id": menu.get("menu_id"), "codigo": menu.get("codigo"), "nombre": menu.get("nombre")})

    def _menus_actualizar_menus_afectados(self, solicitud, step, dependency_results, confirmation_scope):
        afectados = list((dependency_results.get(step.dependencias[0]) or {}).get("menus_afectados") or []) if step.dependencias else []
        actualizados: list[dict[str, Any]] = []
        for menu in afectados:
            ref = str(menu.get("menu_id") or menu.get("codigo") or "").strip()
            actual = self.biblioteca_menus.repo.obtener(ref)
            if not actual:
                continue
            actualizado = self.biblioteca_menus.repo.actualizar(ref, {**actual, "estado": "DESACTUALIZADO"}, motivo_historial="impacto_orquestacion_erp")
            actualizados.append({"menu_id": actualizado.get("menu_id"), "codigo": actualizado.get("codigo"), "estado": actualizado.get("estado")})
        return self._respuesta(True, menus_actualizados=actualizados, total=len(actualizados))

    def _menus_detectar_pendiente_menu(self, solicitud, step, dependency_results, confirmation_scope):
        recetas = list((dependency_results.get(6) or {}).get("creadas") or []) if 6 in dependency_results else []
        escandallos = list((dependency_results.get(7) or {}).get("escandallos_generados") or []) if 7 in dependency_results else []
        refs = {self._norm(x.get("codigo") or x.get("nombre") or "") for x in recetas + escandallos}
        encontrados = []
        for menu in self.biblioteca_menus.repo.listar(incluir_archivados=True):
            comp = dict(menu.get("composicion") or {})
            for items in comp.values():
                for item in list(items or []):
                    if self._norm(item.get("referencia") or "") in refs:
                        encontrados.append({"menu_id": menu.get("menu_id"), "codigo": menu.get("codigo"), "nombre": menu.get("nombre")})
                        break
        return self._respuesta(True, pendiente_menu=not bool(encontrados), menus_relacionados=encontrados, total=len(encontrados))

    def _simulado(self, solicitud, step, dependency_results):
        request = HostAIEngineRequest(
            origen=solicitud.origen,
            modulo=step.agente,
            tipo_peticion=step.operacion,
            datos_enviados={
                "sim_scenario": str((solicitud.datos_de_entrada or {}).get("sim_scenario") or ""),
                "step": step.to_dict(),
                "dependency_results": dependency_results,
            },
        )
        resultado = self.simulator.ejecutar(request)
        return self._respuesta(resultado.ok, simulado=True, salida=resultado.salida, errores=resultado.errores, incidencias=[{"tipo": INC_CAPACIDAD_NO_IMPLEMENTADA, "detalle": f"Capacidad no conectada con servicio real: {step.operacion}"}])


__all__ = ["HostAIAgentRouter"]