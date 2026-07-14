class MotorSimuladorProduccionEvento:
    def simular_evento(self, evento, hora_inicio_produccion="08:00", margen_seguridad_min=60):
        tareas = []
        cronograma = []
        for servicio in evento.get("servicios", []):
            for pase in servicio.get("pases", []):
                for receta_id in pase.get("recetas", []):
                    tareas.append({
                        "titulo": f"Producción previa receta {receta_id}",
                        "receta_id": receta_id,
                        "pase": pase.get("nombre", ""),
                    })
                    cronograma.append({
                        "inicio": hora_inicio_produccion,
                        "fin": hora_inicio_produccion,
                        "titulo": f"Preparar {receta_id}",
                        "momento": "antes_evento",
                    })
        return {
            "evento_id": evento.get("id"),
            "evento": evento.get("nombre"),
            "tareas": tareas,
            "cronograma": cronograma,
            "avisos": [],
            "estado_simulacion": "ok",
            "lectura_host_ai": f"Simulación generada para '{evento.get('nombre')}'.",
        }
