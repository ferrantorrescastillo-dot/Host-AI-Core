from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Iterable, List

from SERVICIOS.motor_recursos_produccion_556e2 import MotorRecursosProduccion556E2
from SERVICIOS.recursos_cocina_465 import RECURSOS_DEFECTO


def _texto(valor: Any) -> str:
    return str(valor or "").strip()


def _clave(valor: Any) -> str:
    texto = _texto(valor).lower()
    texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[\s\-/]+", "_", texto)
    return re.sub(r"_+", "_", texto).strip("_")


class InventarioRecursosProduccion:
    """Fuente única de inventario de recursos para producción real.

    Construye una vista de solo lectura a partir de los planes existentes y la
    configuración confirmada de recursos. No calcula ocupación, conflictos ni
    paralelismo.
    """

    VERSION = "A2.1"
    VERSION_OCUPACION = "A2.2"

    ALIAS_FISICOS = {
        "horno": "horno",
        "fuego": "fogones",
        "fogon": "fogones",
        "fogones": "fogones",
        "thermomix": "thermomix",
        "abatidor": "abatidor",
        "freidora": "freidora",
        "mesa_trabajo": "mesa_trabajo",
        "mesa_de_trabajo": "mesa_trabajo",
        "mesa_de_trabajo_": "mesa_trabajo",
        "camara": "camara",
        "camara_fria": "camara_fria",
        "nevera": "nevera",
        "congelador": "congelador",
        "transporte": "transporte",
        "zona_servicio": "zona_servicio",
    }

    ALIAS_HUMANOS = {
        "jefe_cocina": "jefe_cocina",
        "jefe_de_cocina": "jefe_cocina",
        "cocinero": "cocinero",
        "ayudante": "ayudante",
        "jefe_partida": "jefe_partida",
        "jefe_de_partida": "jefe_partida",
        "pastelero": "pastelero",
        "office": "office",
        "equipo": "equipo",
    }

    ETIQUETAS_FISICAS = {
        "abatidor": "Abatidor",
        "camara": "Cámara",
        "camara_fria": "Cámara fría",
        "congelador": "Congelador",
        "fogones": "Fuego / fogón",
        "freidora": "Freidora",
        "horno": "Horno",
        "mesa_trabajo": "Mesa de trabajo",
        "nevera": "Nevera",
        "thermomix": "Thermomix",
        "transporte": "Transporte",
        "zona_servicio": "Zona de servicio",
    }

    ETIQUETAS_HUMANAS = {
        "ayudante": "Ayudante",
        "cocinero": "Cocinero",
        "equipo": "Equipo",
        "jefe_cocina": "Jefe de cocina",
        "jefe_partida": "Jefe de partida",
        "office": "Office",
        "pastelero": "Pastelero",
    }

    def __init__(self, core: Any):
        self.core = core
        self.motor_556e2 = MotorRecursosProduccion556E2(core.base_dir)
        self.capacidades_confirmadas = self._leer_capacidades_confirmadas()
        self.nombres_catalogo = {
            clave: str(datos.get("nombre") or self.ETIQUETAS_FISICAS.get(clave) or clave.replace("_", " ").title())
            for clave, datos in RECURSOS_DEFECTO.items()
        }

    def construir_inventario_plan(self, plan: Any) -> Dict[str, Any]:
        plan_dict = plan.to_dict() if hasattr(plan, "to_dict") else dict(plan or {})
        fisicos: Dict[str, Dict[str, Any]] = {}
        humanos: Dict[str, Dict[str, Any]] = {}
        datos_incompletos: List[Dict[str, Any]] = []

        for tarea in list(plan_dict.get("tareas", []) or []):
            tarea_titulo = _texto(tarea.get("titulo") or tarea.get("nombre") or tarea.get("id") or "Tarea")
            for fase in list(tarea.get("fases", []) or []):
                uso = {
                    "tarea": tarea_titulo,
                    "fase": _texto(fase.get("nombre") or fase.get("id") or "Fase"),
                }
                self._registrar_recurso_fisico(fisicos, datos_incompletos, fase.get("recurso"), uso)
                self._registrar_recurso_humano(humanos, datos_incompletos, fase.get("responsable"), uso)

        # Compatibilidad defensiva con planes antiguos o parciales sin fases completas.
        for bloque in list((plan_dict.get("planificacion_inteligente") or {}).get("bloques", []) or []):
            recurso = bloque.get("recurso")
            if not _texto(recurso):
                continue
            uso = {
                "tarea": _texto(bloque.get("nombre") or bloque.get("clave") or "Tarea"),
                "fase": _texto(bloque.get("tipo_tiempo") or "bloque"),
            }
            self._registrar_recurso_fisico(fisicos, datos_incompletos, recurso, uso)

        self._completar_capacidades_fisicas(fisicos, datos_incompletos)
        self._completar_cantidades_humanas(humanos, plan_dict, datos_incompletos)

        return {
            "version": self.VERSION,
            "plan_id": _texto(plan_dict.get("id")),
            "recursos_fisicos": self._ordenar_recursos(fisicos.values(), "id_normalizado"),
            "recursos_humanos": self._ordenar_recursos(humanos.values(), "rol"),
            "datos_incompletos": datos_incompletos,
            "solo_lectura": True,
            "datos_reales_modificados": False,
        }

    def construir_ocupacion_plan(self, plan: Any, cronologia: Dict[str, Any] | None = None) -> Dict[str, Any]:
        plan_dict = plan.to_dict() if hasattr(plan, "to_dict") else dict(plan or {})
        inventario = self.construir_inventario_plan(plan)
        cronologia = dict(cronologia or {})
        tramos = list(cronologia.get("tramos") or [])
        recursos = {
            recurso["id_normalizado"]: {
                **dict(recurso),
                "bloques_ocupacion": [],
            }
            for recurso in list(inventario.get("recursos_fisicos") or [])
        }
        bloques: List[Dict[str, Any]] = []
        datos_incompletos = list(inventario.get("datos_incompletos") or [])
        fases = self._indice_fases(plan_dict)
        planificados = self._indice_planificacion(plan_dict)

        for tramo in tramos:
            recurso_original = _texto(tramo.get("recurso"))
            if not recurso_original:
                continue
            recurso = self._normalizar_fisico(recurso_original)
            if not recurso:
                datos_incompletos.append({
                    "tipo": "ocupacion_recurso_no_clasificado",
                    "valor_original": recurso_original,
                    "tarea": _texto(tramo.get("tarea")),
                    "fase": _texto(tramo.get("fase")),
                })
                continue

            tarea_id = _texto(tramo.get("tarea_id"))
            fase_id = _texto(tramo.get("fase_id"))
            fase = fases.get((tarea_id, fase_id), {})
            responsable = _texto(fase.get("responsable"))
            bloque_planificado = None
            if tramo.get("inicio", {}).get("tipo") != "real" and tramo.get("fin", {}).get("tipo") != "real":
                bloque_planificado = self._consumir_planificado(planificados, tarea_id, recurso)

            bloque = self._construir_bloque_ocupacion(tramo, fase, recurso, recurso_original, responsable, bloque_planificado)
            if not bloque:
                datos_incompletos.append({
                    "tipo": "ocupacion_incompleta",
                    "recurso": recurso,
                    "tarea": _texto(tramo.get("tarea")),
                    "fase": _texto(tramo.get("fase")),
                })
                continue
            bloques.append(bloque)

            entrada = recursos.setdefault(recurso, {
                "id_normalizado": recurso,
                "nombre": self.ETIQUETAS_FISICAS.get(recurso) or recurso.replace("_", " ").title(),
                "nombres_origen": [recurso_original],
                "capacidad": "desconocida",
                "capacidad_confirmada": False,
                "capacidad_origen": "",
                "usado_por": [],
                "bloques_ocupacion": [],
            })
            self._append_unique(entrada["nombres_origen"], recurso_original)
            self._append_unique_dict(entrada["usado_por"], {"tarea": bloque["tarea"], "fase": bloque["fase"]})
            entrada["bloques_ocupacion"].append(bloque)

        for entrada in recursos.values():
            entrada["bloques_ocupacion"] = sorted(
                [dict(b) for b in entrada.get("bloques_ocupacion", [])],
                key=lambda item: (int(item.get("dia", 1) or 1), int(item.get("inicio_min", 0) or 0), str(item.get("tarea") or "")),
            )

        bloques = sorted(
            bloques,
            key=lambda item: (int(item.get("dia", 1) or 1), int(item.get("inicio_min", 0) or 0), str(item.get("recurso") or ""), str(item.get("tarea") or "")),
        )
        return {
            "version": self.VERSION_OCUPACION,
            "plan_id": _texto(plan_dict.get("id")),
            "base_horaria": dict(cronologia.get("base_horaria") or {}),
            "recursos_fisicos": self._ordenar_recursos(recursos.values(), "id_normalizado"),
            "recursos_humanos": self._ordenar_recursos(inventario.get("recursos_humanos") or [], "rol"),
            "bloques": bloques,
            "resumen": {
                "total_bloques": len(bloques),
                "recursos_con_ocupacion": sum(1 for entrada in recursos.values() if entrada.get("bloques_ocupacion")),
                "bloques_planificados": sum(1 for bloque in bloques if bloque.get("origen_dato") == "planificacion_estimada"),
                "bloques_reales": sum(1 for bloque in bloques if bloque.get("origen_dato") == "ejecucion_real"),
                "bloques_calculo_interno": sum(1 for bloque in bloques if bloque.get("origen_dato") == "calculo_interno"),
            },
            "datos_incompletos": datos_incompletos,
            "solo_lectura": True,
            "datos_reales_modificados": False,
        }

    def _leer_capacidades_confirmadas(self) -> Dict[str, int]:
        recursos = {}
        config = self.motor_556e2.config if isinstance(self.motor_556e2.config, dict) else {}
        for clave, valor in dict(config.get("recursos") or {}).items():
            try:
                canonica = self.ALIAS_FISICOS.get(_clave(clave), _clave(clave))
                recursos[canonica] = int(valor)
            except (TypeError, ValueError):
                continue
        return recursos

    def _indice_fases(self, plan_dict: Dict[str, Any]) -> Dict[tuple[str, str], Dict[str, Any]]:
        fases: Dict[tuple[str, str], Dict[str, Any]] = {}
        for tarea in list(plan_dict.get("tareas", []) or []):
            tarea_id = _texto(tarea.get("id"))
            for fase in list(tarea.get("fases", []) or []):
                fases[(tarea_id, _texto(fase.get("id")))] = dict(fase)
        return fases

    def _indice_planificacion(self, plan_dict: Dict[str, Any]) -> Dict[tuple[str, str], List[Dict[str, Any]]]:
        planificados: Dict[tuple[str, str], List[Dict[str, Any]]] = {}
        for bloque in list((plan_dict.get("planificacion_inteligente") or {}).get("bloques", []) or []):
            recurso_original = _texto(bloque.get("recurso"))
            recurso = self._normalizar_fisico(recurso_original)
            if not recurso:
                continue
            clave = _texto(bloque.get("clave")).replace("_pasivo", "")
            planificados.setdefault((clave, recurso), []).append(dict(bloque))
        for lista in planificados.values():
            lista.sort(key=lambda item: (int(item.get("dia", 1) or 1), int(item.get("inicio_min", 0) or 0), int(item.get("fin_min", 0) or 0)))
        return planificados

    @staticmethod
    def _consumir_planificado(planificados: Dict[tuple[str, str], List[Dict[str, Any]]], tarea_id: str, recurso: str) -> Dict[str, Any] | None:
        lista = planificados.get((tarea_id, recurso)) or []
        if not lista:
            return None
        return lista.pop(0)

    def _construir_bloque_ocupacion(
        self,
        tramo: Dict[str, Any],
        fase: Dict[str, Any],
        recurso: str,
        recurso_original: str,
        responsable: str,
        bloque_planificado: Dict[str, Any] | None,
    ) -> Dict[str, Any] | None:
        inicio = dict(tramo.get("inicio") or {})
        fin = dict(tramo.get("fin") or {})
        dia = 1
        inicio_min = inicio.get("minutos")
        fin_min = fin.get("minutos")
        origen_dato = "calculo_interno"
        origen_tiempo = {"inicio": "calculo_interno", "fin": "calculo_interno"}
        origen_referencia = "cronologia_operativa_prevista"

        if inicio.get("tipo") == "real" or fin.get("tipo") == "real":
            origen_dato = "ejecucion_real"
            origen_tiempo = {
                "inicio": "ejecucion_real" if inicio.get("tipo") == "real" else "calculo_interno",
                "fin": "ejecucion_real" if fin.get("tipo") == "real" else "calculo_interno",
            }
        elif bloque_planificado is not None:
            dia = max(1, int(bloque_planificado.get("dia", 1) or 1))
            inicio_min = int(bloque_planificado.get("inicio_min", 0) or 0)
            fin_min = int(bloque_planificado.get("fin_min", 0) or 0)
            origen_dato = "planificacion_estimada"
            origen_tiempo = {"inicio": "planificacion_estimada", "fin": "planificacion_estimada"}
            origen_referencia = "planificacion_inteligente.bloques"

        if inicio_min is None or fin_min is None:
            return None

        return {
            "dia": int(dia),
            "inicio_min": int(inicio_min),
            "fin_min": int(fin_min),
            "inicio": self._marca_ocupacion(int(dia), int(inicio_min), origen_tiempo["inicio"]),
            "fin": self._marca_ocupacion(int(dia), int(fin_min), origen_tiempo["fin"]),
            "recurso": recurso,
            "recurso_original": recurso_original,
            "tarea_id": _texto(tramo.get("tarea_id")),
            "tarea": _texto(tramo.get("tarea")),
            "fase_id": _texto(tramo.get("fase_id")),
            "fase": _texto(tramo.get("fase")),
            "responsable": responsable,
            "origen_dato": origen_dato,
            "origen_tiempo": origen_tiempo,
            "origen_referencia": origen_referencia,
        }

    @staticmethod
    def _hora_desde_minutos(minutos: int) -> str:
        total = max(0, int(minutos or 0))
        return f"{(total // 60) % 24:02d}:{total % 60:02d}"

    def _marca_ocupacion(self, dia: int, minutos: int, origen: str) -> Dict[str, Any]:
        origen = _texto(origen).lower() or "calculo_interno"
        precision = 1 if origen == "ejecucion_real" else 5
        mostrado = int(minutos) if precision == 1 else (int(minutos) // 5) * 5
        sufijo = "" if origen == "ejecucion_real" else " (estimado)"
        return {
            "dia": int(dia),
            "minutos": int(minutos),
            "texto": f"Día {int(dia)} · {self._hora_desde_minutos(mostrado)}{sufijo}",
            "tipo": "real" if origen == "ejecucion_real" else "estimado",
            "precision_min": precision,
        }

    def _registrar_recurso_fisico(
        self,
        fisicos: Dict[str, Dict[str, Any]],
        datos_incompletos: List[Dict[str, Any]],
        original: Any,
        uso: Dict[str, str],
    ) -> None:
        valor = _texto(original)
        if not valor:
            return
        clave = self._normalizar_fisico(valor)
        if not clave:
            datos_incompletos.append({
                "tipo": "recurso_no_clasificado",
                "valor_original": valor,
                "usado_por": [uso],
            })
            return
        entrada = fisicos.setdefault(clave, {
            "id_normalizado": clave,
            "nombre": self.ETIQUETAS_FISICAS.get(clave) or self.nombres_catalogo.get(clave) or valor.replace("_", " ").title(),
            "nombres_origen": [],
            "capacidad": "desconocida",
            "capacidad_confirmada": False,
            "capacidad_origen": "",
            "usado_por": [],
        })
        self._append_unique(entrada["nombres_origen"], valor)
        self._append_unique_dict(entrada["usado_por"], uso)

    def _registrar_recurso_humano(
        self,
        humanos: Dict[str, Dict[str, Any]],
        datos_incompletos: List[Dict[str, Any]],
        original: Any,
        uso: Dict[str, str],
    ) -> None:
        valor = _texto(original)
        if not valor:
            return
        clave = self._normalizar_humano(valor)
        if not clave:
            datos_incompletos.append({
                "tipo": "responsable_no_clasificado",
                "valor_original": valor,
                "usado_por": [uso],
            })
            return
        entrada = humanos.setdefault(clave, {
            "rol": clave,
            "nombre": self.ETIQUETAS_HUMANAS.get(clave) or valor.replace("_", " ").title(),
            "nombres_origen": [],
            "cantidad": "desconocida",
            "cantidad_confirmada": False,
            "cantidad_origen": "",
            "usado_por": [],
        })
        self._append_unique(entrada["nombres_origen"], valor)
        self._append_unique_dict(entrada["usado_por"], uso)

    def _completar_capacidades_fisicas(self, fisicos: Dict[str, Dict[str, Any]], datos_incompletos: List[Dict[str, Any]]) -> None:
        for clave, entrada in fisicos.items():
            capacidad = self.capacidades_confirmadas.get(clave)
            if capacidad is not None:
                entrada["capacidad"] = capacidad
                entrada["capacidad_confirmada"] = True
                entrada["capacidad_origen"] = "DATOS/config/recursos_cocina_556e2.json"
            else:
                datos_incompletos.append({
                    "tipo": "capacidad_desconocida",
                    "recurso": clave,
                    "nombres_origen": list(entrada["nombres_origen"]),
                })

    def _completar_cantidades_humanas(
        self,
        humanos: Dict[str, Dict[str, Any]],
        plan_dict: Dict[str, Any],
        datos_incompletos: List[Dict[str, Any]],
    ) -> None:
        asignaciones = list((plan_dict.get("asignacion_recursos") or {}).get("asignaciones", []) or [])
        por_rol: Dict[str, set[str]] = {}
        for asignacion in asignaciones:
            nombre = _texto(asignacion.get("cocinero"))
            if not nombre:
                continue
            rol = self._normalizar_humano(nombre)
            if not rol:
                continue
            por_rol.setdefault(rol, set()).add(nombre)

        cfg = dict(plan_dict.get("configuracion_planificacion") or {})
        cantidad_cocineros = cfg.get("cocineros")

        for clave, entrada in humanos.items():
            if clave == "cocinero" and isinstance(cantidad_cocineros, int):
                entrada["cantidad"] = int(cantidad_cocineros)
                entrada["cantidad_confirmada"] = True
                entrada["cantidad_origen"] = "plan.configuracion_planificacion.cocineros"
                continue
            nombres = por_rol.get(clave) or set()
            if nombres:
                entrada["cantidad"] = len(nombres)
                entrada["cantidad_confirmada"] = True
                entrada["cantidad_origen"] = "plan.asignacion_recursos.asignaciones"
                for nombre in sorted(nombres):
                    self._append_unique(entrada["nombres_origen"], nombre)
                continue
            datos_incompletos.append({
                "tipo": "cantidad_humana_desconocida",
                "rol": clave,
                "nombres_origen": list(entrada["nombres_origen"]),
            })

    def _normalizar_fisico(self, valor: str) -> str:
        clave = _clave(valor)
        return self.ALIAS_FISICOS.get(clave, clave if clave in self.capacidades_confirmadas else "")

    def _normalizar_humano(self, valor: str) -> str:
        clave = _clave(valor)
        if re.fullmatch(r"cocinero_?\d+", clave):
            return "cocinero"
        return self.ALIAS_HUMANOS.get(clave, "")

    @staticmethod
    def _append_unique(destino: List[str], valor: str) -> None:
        if valor not in destino:
            destino.append(valor)

    @staticmethod
    def _append_unique_dict(destino: List[Dict[str, str]], valor: Dict[str, str]) -> None:
        if valor not in destino:
            destino.append(valor)

    @staticmethod
    def _ordenar_recursos(recursos: Iterable[Dict[str, Any]], clave: str) -> List[Dict[str, Any]]:
        return sorted((dict(recurso) for recurso in recursos), key=lambda item: _texto(item.get(clave)).lower())


__all__ = ["InventarioRecursosProduccion"]