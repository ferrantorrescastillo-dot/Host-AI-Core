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