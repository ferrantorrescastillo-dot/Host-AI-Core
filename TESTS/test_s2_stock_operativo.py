from datetime import date, timedelta

from MOTORES.motor_stock import MotorStock
from SERVICIOS.base_datos_local import BaseDatosLocal


def test_s2_stock_operativo_completo(tmp_path):
    db = BaseDatosLocal(tmp_path)
    stock = MotorStock(db)

    caducidad = (date.today() + timedelta(days=2)).isoformat()
    entrada = stock.registrar_entrada(
        "Tomate triturado", 10, "kg", familia="Conservas",
        ubicacion="Seco", articulo_id="ART000001",
        caducidad=caducidad, coste_unitario=2.5,
    )
    lote_id = entrada["lote"]["id"]

    resumen = stock.resumen_operativo(7)
    assert resumen["total_articulos"] == 1
    assert resumen["total_lotes"] == 1
    assert resumen["valor_total"] == 25.0
    assert resumen["lotes_caducan_pronto"] == 1
    assert resumen["ubicaciones"][0]["ubicacion"] == "Seco"

    actualizado = stock.actualizar_lote(lote_id, ubicacion="Cámara", caducidad=caducidad)
    assert actualizado["ok"] is True
    assert actualizado["lote"]["ubicacion"] == "Cámara"

    merma = stock.registrar_merma("Tomate triturado", 2, "kg", motivo="envase roto", articulo_id="ART000001")
    assert merma["ok"] is True
    assert stock.stock_actual()["items"][0]["cantidad"] == 8

    ajuste = stock.ajustar_inventario("Tomate triturado", 6, "kg", articulo_id="ART000001", motivo="conteo físico")
    assert ajuste["ok"] is True
    assert ajuste["tipo"] == "ajuste_negativo"
    assert stock.stock_actual()["items"][0]["cantidad"] == 6

    ajuste_positivo = stock.ajustar_inventario(
        "Tomate triturado", 9, "kg", articulo_id="ART000001",
        familia="Conservas", ubicacion="Cámara", motivo="conteo físico",
    )
    assert ajuste_positivo["ok"] is True
    assert ajuste_positivo["tipo"] == "ajuste_positivo"
    assert stock.stock_actual()["items"][0]["cantidad"] == 9

    movimientos = stock.movimientos_articulo("tomate")
    tipos = {m["tipo"] for m in movimientos}
    assert {"entrada", "merma", "ajuste_negativo", "ajuste_positivo"}.issubset(tipos)

    lotes = stock.lotes_listado(ubicacion="cámara")
    assert lotes
    assert all("cámara" in (l["ubicacion"] or "").lower() for l in lotes)

    recargado = MotorStock(db)
    assert recargado.stock_actual()["items"][0]["cantidad"] == 9
    assert recargado.movimientos_articulo("tomate")
