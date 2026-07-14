from SERVICIOS.motor_decisiones_operativas_491 import evaluar_decision_operativa, generar_decisiones_operativas, resumen_decisiones_operativas


def main():
    decision = evaluar_decision_operativa({"modulo": "stock", "descripcion": "Arroz bajo", "stock_actual": 1, "stock_minimo": 10})
    assert decision["prioridad"] in {"media", "alta", "critica"}
    assert decision["accion_recomendada"] == "proponer_compra_o_entrada_stock"
    resultado = generar_decisiones_operativas([decision, {"modulo": "rentabilidad", "descripcion": "Plato margen bajo", "margen": 0.1}])
    assert resultado["total_decisiones"] == 2
    assert resultado["siguiente_accion"] is not None
    assert "Prioridad" in resumen_decisiones_operativas(resultado)
    print("TEST OK 4.9.1 Motor de decisiones operativas")


if __name__ == "__main__":
    main()
