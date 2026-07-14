from SERVICIOS.checklist_final_produccion_467 import generar_checklist_final, imprimir_checklist


def main():
    tareas = [
        {"id": "c1", "nombre": "Croquetas", "estado": "terminada", "etiquetada": True, "guardada": True, "ubicacion_destino": "Cámara"},
        {"id": "f1", "nombre": "Fondo", "estado": "pendiente", "etiquetada": False},
    ]
    checklist = generar_checklist_final(tareas, stock={"Arroz": 2, "Harina": -1}, documentos=[])
    assert checklist["ok"] is False
    assert checklist["pendientes"] >= 2
    texto = imprimir_checklist(checklist)
    assert "CHECKLIST" in texto
    assert "Harina" in texto
    print("TEST OK 4.6.7 Checklist final de producción")


if __name__ == "__main__":
    main()
