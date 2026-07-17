from __future__ import annotations

import copy
from types import SimpleNamespace

from APP.consola_produccion_guiada_piloto_13 import ConsolaProduccionGuiadaPiloto13
from SERVICIOS.produccion_guiada_piloto_13 import ProduccionGuiadaPiloto13


def _capturar(llamada):
    lineas = []
    llamada(lineas.append)
    return "\n".join(lineas)


def _panel_base() -> dict:
    return {
        "plan": "Servicio sábado",
        "avance": 15,
        "pendientes": 2,
        "en_curso": 1,
        "bloqueadas": 0,
        "alertas": [],
        "siguiente_accion": {
            "texto": "Continúa con Carrillera",
            "explicacion": "Está en marcha.",
        },
        "tareas": [
            {
                "id": "T1",
                "titulo": "Carrillera",
                "estado_texto": "🟠 En marcha",
                "estado_codigo": "en_curso",
                "prioridad_texto": "Muy urgente",
                "tiempo_restante_texto": "1 h",
                "bloqueo": "",
            }
        ],
        "inventario_recursos": {
            "recursos_fisicos": [
                {
                    "id_normalizado": "horno",
                    "nombre": "Horno",
                    "tipo": "fisico",
                    "capacidad": 2,
                    "unidad": "uso",
                    "capacidad_confirmada": True,
                    "capacidad_origen": "config_confirmada",
                    "nombres_origen": ["horno"],
                }
            ],
            "datos_incompletos": [],
        },
        "ocupacion_recursos": {
            "bloques": [
                {
                    "recurso": "horno",
                    "tarea": "Carrillera",
                    "responsable": "cocinero",
                    "dia": 1,
                    "inicio_min": 30,
                    "fin_min": 60,
                    "inicio": {"texto": "09:30"},
                    "fin": {"texto": "10:00"},
                    "origen_dato": "planificacion_estimada",
                }
            ],
            "resumen": {"total_bloques": 1},
            "datos_incompletos": [],
        },
        "simultaneidad_recursos": {
            "tramos": [
                {
                    "intervalo": "Día 1 · 09:30-10:00",
                    "cantidad_total_ocupaciones": 2,
                    "recursos_fisicos_activos": ["horno"],
                    "tareas_activas": ["Carrillera", "Costillar"],
                    "responsables_activos": ["cocinero", "ayudante"],
                }
            ],
            "resumen": {"maximo_nivel_simultaneidad": 2},
            "datos_incompletos": [],
        },
        "conflictos_recursos": {
            "conflictos": [
                {
                    "id": "CFX-0001",
                    "severidad": "alta",
                    "recurso": "horno",
                    "responsable": "",
                    "tareas_afectadas": ["Carrillera", "Costillar"],
                    "intervalo": "Día 1 · 09:30-10:00",
                    "descripcion": "Capacidad superada",
                    "origen": "simultaneidad",
                    "datos_reales": False,
                    "datos_estimados": True,
                }
            ],
            "resumen": {"total": 1},
        },
    }


class _PlanFake:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._data


class _MotorPanelFake:
    def __init__(self):
        self.plan = {
            "id": "P1",
            "nombre": "Servicio sábado",
            "fecha": "2026-07-17",
            "estado": "en_produccion",
            "tareas": [{"id": "T1"}],
        }
        self.tareas = [{"id": "T1", "titulo": "Carrillera", "estado_ejecucion": "pendiente", "prioridad": 90, "tiempo_real_min": 0, "tiempo_restante_estimado_min": 60, "fases": [], "bloqueo": "", "checklist_pendiente": 0}]

    def listar_planes(self):
        return [self.plan]

    def obtener_plan(self, _):
        return _PlanFake(self.plan)

    def resumen_ejecucion(self, _):
        return {
            "plan": "Servicio sábado",
            "estado_plan": "en_produccion",
            "porcentaje_completado": 0,
            "total_tareas": 1,
            "tareas": self.tareas,
            "alertas": [],
            "tareas_pendientes": self.tareas,
        }

    def panel_produccion(self, _):
        return {
            "clasificacion_jornada": {"resumen": {}, "detalle": []},
            "cuellos_botella_previstos": {"resumen": {}, "detalle": []},
            "cronologia_operativa_prevista": {"resumen": {}, "base_horaria": {}, "alertas": [], "tramos": []},
            "inventario_recursos": {"recursos_fisicos": [{"id_normalizado": "horno"}]},
            "ocupacion_temporal_recursos": {"bloques": [{"recurso": "horno"}], "resumen": {"total_bloques": 1}},
            "simultaneidad_recursos": {"tramos": [{"cantidad_total_ocupaciones": 1}], "resumen": {"maximo_nivel_simultaneidad": 1}},
            "conflictos_recursos": {"conflictos": [], "resumen": {"total": 0}},
        }

    def siguiente_tarea_recomendada(self, _):
        return {"codigo": "SUGERIDA", "tarea_id": "T1", "criterios": ["inicio natural"]}


class _ServicioDummy:
    def __init__(self, panel):
        self.panel = panel
        self.calls = []

    def construir_panel(self, _):
        return copy.deepcopy(self.panel)

    def listar_planes_operativos(self):
        return [{"id": "P1", "nombre": "Servicio sábado", "fecha": "2026-07-17", "estado": "en_produccion"}]

    def iniciar(self, *a):
        self.calls.append(("iniciar", a))

    def pausar(self, *a):
        self.calls.append(("pausar", a))

    def reanudar(self, *a):
        self.calls.append(("reanudar", a))

    def actualizar_avance(self, *a):
        self.calls.append(("avance", a))

    def registrar_incidencia(self, *a):
        self.calls.append(("incidencia", a))

    def resolver_bloqueo(self, *a):
        self.calls.append(("resolver", a))

    def registrar_merma(self, *a):
        self.calls.append(("merma", a))

    def cambiar_fase(self, *a):
        self.calls.append(("fase", a))


class _CoreFake:
    def __init__(self):
        self.produccion_real = _MotorPanelFake()


def _input_seq(*values):
    datos = list(values)

    def _next(_prompt=""):
        if not datos:
            return "0"
        return datos.pop(0)

    return _next


def test_01_resumen_con_todos_los_bloques_presentes():
    panel = _panel_base()
    salida = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_resumen_recursos(panel, p))
    assert "DIAGNÓSTICO DE RECURSOS" in salida
    assert "Recursos conocidos: 1" in salida
    assert "Ocupaciones registradas: 1" in salida
    assert "Máxima simultaneidad: 2" in salida
    assert "Conflictos detectados: 1" in salida


def test_02_ausencia_total_de_datos_de_recursos():
    panel = _panel_base()
    panel.pop("inventario_recursos")
    panel.pop("ocupacion_recursos")
    panel.pop("simultaneidad_recursos")
    panel.pop("conflictos_recursos")
    salida = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_resumen_recursos(panel, p))
    assert "Sin información de recursos disponible" in salida


def test_03_inventario_vacio():
    panel = _panel_base()
    panel["inventario_recursos"] = {"recursos_fisicos": []}
    salida = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_inventario_recursos(panel, p))
    assert "No hay recursos en inventario" in salida


def test_04_ocupacion_vacia():
    panel = _panel_base()
    panel["ocupacion_recursos"] = {"bloques": []}
    salida = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_ocupacion_recursos(panel, p))
    assert "No hay ocupaciones registradas" in salida


def test_05_simultaneidad_vacia():
    panel = _panel_base()
    panel["simultaneidad_recursos"] = {"tramos": []}
    salida = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_simultaneidad_recursos(panel, p))
    assert "No hay tramos de simultaneidad registrados" in salida


def test_06_conflictos_vacios():
    panel = _panel_base()
    panel["conflictos_recursos"] = {"conflictos": []}
    salida = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_conflictos_recursos(panel, p))
    assert "No se detectan conflictos" in salida


def test_07_campos_incompletos_no_rompen_detalles():
    panel = _panel_base()
    panel["inventario_recursos"]["recursos_fisicos"] = [{"id_normalizado": "horno"}]
    panel["conflictos_recursos"]["conflictos"] = [{"id": "CFX-0002"}]
    out_inv = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_inventario_recursos(panel, p))
    out_conf = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_conflictos_recursos(panel, p))
    assert "no indicado" in out_inv
    assert "no indicado" in out_conf


def test_08_intervalos_invalidos_se_muestran_como_incompletos():
    panel = _panel_base()
    panel["ocupacion_recursos"]["bloques"] = [
        {
            "recurso": "horno",
            "tarea": "Carrillera",
            "inicio_min": 60,
            "fin_min": 60,
        }
    ]
    salida = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_ocupacion_recursos(panel, p))
    assert "información incompleta" in salida


def test_09_simultaneidad_no_equivale_a_conflicto():
    panel = _panel_base()
    panel["simultaneidad_recursos"]["tramos"][0]["cantidad_total_ocupaciones"] = 3
    panel["conflictos_recursos"] = {"conflictos": [], "resumen": {"total": 0}}
    salida_sim = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_simultaneidad_recursos(panel, p))
    salida_conf = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_conflictos_recursos(panel, p))
    assert "no implica conflicto confirmado" in salida_sim
    assert "No se detectan conflictos" in salida_conf


def test_10_detalle_inventario_muestra_campos_clave():
    salida = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_inventario_recursos(_panel_base(), p))
    assert "Recurso: Horno" in salida
    assert "Capacidad: 2" in salida
    assert "Unidad:" in salida
    assert "Origen:" in salida


def test_11_detalle_ocupacion_muestra_campos_clave():
    salida = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_ocupacion_recursos(_panel_base(), p))
    assert "Carrillera" in salida
    assert "Responsable:" in salida
    assert "Inicio:" in salida
    assert "Carácter:" in salida


def test_12_detalle_simultaneidad_muestra_campos_clave():
    salida = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_simultaneidad_recursos(_panel_base(), p))
    assert "Ocupaciones simultáneas" in salida
    assert "Tareas implicadas" in salida
    assert "Responsables implicados" in salida


def test_13_detalle_conflictos_muestra_campos_clave():
    salida = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_conflictos_recursos(_panel_base(), p))
    assert "ID: CFX-0001" in salida
    assert "Severidad:" in salida
    assert "Descripción:" in salida
    assert "Origen:" in salida


def test_14_menu_conserva_opciones_anteriores_y_agrega_nuevas():
    panel = _panel_base()
    consola = ConsolaProduccionGuiadaPiloto13.__new__(ConsolaProduccionGuiadaPiloto13)
    consola.service = _ServicioDummy(panel)
    salida = _capturar(lambda p: consola._trabajar_plan("P1", _input_seq("0"), p))
    assert "A. Ver detalle de clasificación" in salida
    assert "B. Ver detalle de cuellos previstos" in salida
    assert "C. Ver detalle de cronología prevista" in salida
    assert "D. Ver inventario de recursos" in salida
    assert "E. Ver ocupación de recursos" in salida
    assert "F. Ver simultaneidad de recursos" in salida
    assert "G. Ver conflictos de recursos" in salida


def test_15_navegacion_regreso_no_modifica_plan():
    panel = _panel_base()
    consola = ConsolaProduccionGuiadaPiloto13.__new__(ConsolaProduccionGuiadaPiloto13)
    servicio = _ServicioDummy(panel)
    consola.service = servicio
    snapshot = copy.deepcopy(panel)
    consola._trabajar_plan("P1", _input_seq("d", "", "0"), lambda *a, **k: None)
    assert panel == snapshot
    assert servicio.calls == []


def test_16_presentacion_no_muta_estructuras_recibidas():
    panel = _panel_base()
    original = copy.deepcopy(panel)
    ConsolaProduccionGuiadaPiloto13._mostrar_resumen_recursos(panel, lambda *_: None)
    ConsolaProduccionGuiadaPiloto13._mostrar_inventario_recursos(panel, lambda *_: None)
    ConsolaProduccionGuiadaPiloto13._mostrar_ocupacion_recursos(panel, lambda *_: None)
    ConsolaProduccionGuiadaPiloto13._mostrar_simultaneidad_recursos(panel, lambda *_: None)
    ConsolaProduccionGuiadaPiloto13._mostrar_conflictos_recursos(panel, lambda *_: None)
    assert panel == original


def test_17_compatibilidad_con_planes_antiguos():
    panel_antiguo = {
        "plan": "Plan viejo",
        "avance": 0,
        "pendientes": 0,
        "en_curso": 0,
        "bloqueadas": 0,
        "alertas": [],
        "siguiente_accion": {"texto": "Sin acción", "explicacion": ""},
        "tareas": [],
    }
    salida = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_panel(panel_antiguo, p))
    assert "DIAGNÓSTICO DE RECURSOS" in salida
    assert "Sin información de recursos disponible" in salida


def test_18_integracion_correcta_en_produccion_guiada():
    servicio = ProduccionGuiadaPiloto13(SimpleNamespace(produccion_real=_MotorPanelFake()))
    panel = servicio.construir_panel("P1")
    assert "inventario_recursos" in panel
    assert "ocupacion_recursos" in panel
    assert "simultaneidad_recursos" in panel
    assert "conflictos_recursos" in panel
    salida = _capturar(lambda p: ConsolaProduccionGuiadaPiloto13._mostrar_panel(panel, p))
    assert "DIAGNÓSTICO DE RECURSOS" in salida
