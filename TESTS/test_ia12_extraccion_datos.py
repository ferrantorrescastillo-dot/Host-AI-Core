from datetime import date

from CORE.host_ai_core import HostAICore
from SERVICIOS.extractor_datos_ia12 import ExtractorDatosIA12


def test_ia12_extrae_evento_completo(tmp_path):
    core = HostAICore(tmp_path)
    resultado = core.motor_intenciones_ia11.clasificar(
        "Tengo una boda para 120 personas el 22/10/2026 a las 13:30"
    )
    assert resultado["intent"] == "crear_evento"
    assert resultado["datos"]["tipo_evento"] == "boda"
    assert resultado["datos"]["pax"] == 120
    assert resultado["datos"]["fecha"] == "2026-10-22"
    assert resultado["datos"]["hora"] == "13:30"
    assert resultado["faltan"] == []
    assert resultado["ejecutar"] is False
    assert resultado["version"] == "6.0.4-IA1.2"


def test_ia12_extrae_compra_articulo_cantidad_unidad_proveedor(tmp_path):
    core = HostAICore(tmp_path)
    resultado = core.motor_intenciones_ia11.clasificar(
        "Necesito comprar 5 kg de tomate triturado y se lo compro a Sarda"
    )
    assert resultado["intent"] == "registrar_necesidad_compra"
    assert resultado["datos"]["cantidad"] == 5
    assert resultado["datos"]["unidad"] == "kg"
    assert "Tomate" in resultado["datos"]["articulo"]
    assert resultado["datos"]["proveedor"] == "Sarda"
    assert resultado["faltan"] == []


def test_ia12_extrae_precio_receta_y_cocineros(tmp_path):
    core = HostAICore(tmp_path)
    receta = core.motor_intenciones_ia11.clasificar(
        "Calcula el coste de la receta carrillera a 20 euros por ración"
    )
    assert receta["datos"]["receta"] == "Carrillera"
    assert receta["datos"]["precio"] == 20.0

    produccion = core.motor_intenciones_ia11.clasificar(
        "Planifica la producción entre 3 cocineros"
    )
    assert produccion["intent"] == "planificar_produccion"
    assert produccion["datos"]["cocineros"] == 3


def test_ia12_fechas_naturales_y_campos_faltantes():
    extractor = ExtractorDatosIA12()
    resultado = extractor.extraer(
        "Crea una boda mañana para 80 personas",
        intent="crear_evento",
        fecha_referencia=date(2026, 7, 11),
    )
    assert resultado["datos"]["fecha"] == "2026-07-12"
    assert resultado["datos"]["pax"] == 80
    assert resultado["faltan"] == []

    incompleto = extractor.extraer("Necesito comprar tomates", intent="registrar_necesidad_compra")
    assert incompleto["datos"]["articulo"] == "Tomates"
    assert incompleto["faltan"] == ["cantidad", "unidad"]
    assert incompleto["requiere_aclaracion"] is True


def test_ia12_no_ejecuta_y_acepta_contexto():
    extractor = ExtractorDatosIA12()
    resultado = extractor.extraer(
        "Calcula el coste",
        intent="calcular_costes",
        contexto={"receta_id": "REC-CARRILLERA"},
    )
    assert resultado["datos"]["receta_id"] == "REC-CARRILLERA"
    assert resultado["ejecutar"] is False
