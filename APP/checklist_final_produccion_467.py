from SERVICIOS.checklist_final_produccion_467 import generar_checklist_final, imprimir_checklist


def main():
    tareas = [{"id": "t1", "nombre": "Croquetas", "estado": "terminada", "etiquetada": True, "guardada": True, "ubicacion_destino": "Cámara"}]
    checklist = generar_checklist_final(tareas, documentos=["parte_produccion_2026_07_09.pdf"])
    print(imprimir_checklist(checklist))


if __name__ == "__main__":
    main()
