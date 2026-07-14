# APP Host AI 4.7.6 - Material evento

from SERVICIOS.material_evento_476 import calcular_material_evento, resumen_material_evento


def main():
    evento = {"id_evento": "DEMO", "nombre": "Paella empresa", "personas": 140, "tipo": "paella"}
    menu = {"platos": ["Aperitivos", "Paella marisco", "Postre"]}
    print(resumen_material_evento(calcular_material_evento(evento, menu)))


if __name__ == "__main__":
    main()
