from pathlib import Path
from tempfile import TemporaryDirectory
from MOTORES.motor_stock import MotorStock
from SERVICIOS.base_datos_local import BaseDatosLocal


def test_rr161c_fifo_y_resumen_ampliado():
    with TemporaryDirectory() as td:
        db = BaseDatosLocal(Path(td))
        motor = MotorStock(db)
        r1 = motor.registrar_entrada('Arroz bomba', 2, 'kg', ubicacion='seco', articulo_id='ART1', coste_unitario=0)
        r2 = motor.registrar_entrada('Arroz bomba', 5, 'kg', ubicacion='', articulo_id='ART1', coste_unitario=1.65)
        lotes = motor.lotes_listado('arroz')
        assert len(lotes) == 2
        assert lotes[0]['fecha_entrada'] <= lotes[1]['fecha_entrada']
        resumen = motor.resumen_operativo()
        assert resumen['lotes_sin_precio'] == 1
        assert resumen['lotes_sin_ubicacion'] == 1
        assert resumen['valor_total'] == 8.25
