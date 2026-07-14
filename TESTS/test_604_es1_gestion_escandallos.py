from SERVICIOS.base_datos_local import BaseDatosLocal
from MOTORES.motor_escandallos_inteligente import MotorEscandallosInteligente


def test_es1_ciclo_completo_y_persistencia(tmp_path):
    db = BaseDatosLocal(tmp_path)
    motor = MotorEscandallosInteligente(db)

    creado = motor.registrar_escandallo(
        receta_id="REC-TEST",
        nombre="Receta test",
        raciones_base=10,
        lineas=[],
        grupo="Pruebas",
        observaciones="ES1",
    )
    assert creado["receta_id"] == "REC-TEST"

    linea = motor.agregar_linea("REC-TEST", {
        "nombre": "Tomate",
        "cantidad": 2,
        "unidad": "kg",
        "articulo_id": "ART-001",
        "merma_porcentaje": 10,
    })
    assert linea["nombre"] == "Tomate"

    editada = motor.editar_linea("REC-TEST", linea["id"], cantidad=3, unidad="KG")
    assert editada["cantidad"] == 3

    ficha = motor.editar_escandallo("REC-TEST", nombre="Receta test editada", raciones_base=12)
    assert ficha["raciones_base"] == 12

    copia = motor.duplicar("REC-TEST", "REC-TEST-COPIA")
    assert copia["receta_id"] == "REC-TEST-COPIA"
    assert copia["lineas"][0]["id"] != linea["id"]

    motor.editar_escandallo("REC-TEST", activo=False)
    assert motor.listar() == [copia]
    assert len(motor.listar(incluir_inactivos=True)) == 2

    recargado = MotorEscandallosInteligente(db)
    assert recargado.obtener("REC-TEST-COPIA").nombre.startswith("Receta test")
    assert recargado.eliminar("REC-TEST") is True
    assert len(recargado.buscar("test", incluir_inactivos=True)) == 1
