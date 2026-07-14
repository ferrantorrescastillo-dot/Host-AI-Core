from SERVICIOS.conflictos_replanificacion_466 import detectar_conflictos_produccion, replanificar_basico


def main():
    tareas = [
        {"id": "fondo", "nombre": "Fondo oscuro", "inicio": "2026-07-09T08:00", "fin": "2026-07-09T09:00", "recurso": "horno", "cocinero": "Ana"},
        {"id": "pollo", "nombre": "Pollo asado", "inicio": "2026-07-09T08:30", "fin": "2026-07-09T09:15", "recurso": "horno", "cocinero": "Ana"},
        {"id": "salsa", "nombre": "Salsa", "inicio": "2026-07-09T08:45", "fin": "2026-07-09T09:30", "depende_de": ["fondo"], "cocinero": "Marc"},
    ]
    conflictos = detectar_conflictos_produccion(tareas, {"horno": 1})
    assert any(c["tipo"] == "sobrecarga_recurso" for c in conflictos)
    assert any(c["tipo"] == "cocinero_solapado" for c in conflictos)
    assert any(c["tipo"] == "dependencia_no_respetada" for c in conflictos)
    resultado = replanificar_basico(tareas, {"horno": 2})
    assert "tareas" in resultado
    print("TEST OK 4.6.6 Conflictos y replanificación")


if __name__ == "__main__":
    main()
