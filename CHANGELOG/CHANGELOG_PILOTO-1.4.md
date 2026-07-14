# PILOTO-1.4 — Producción → Stock

## Incorporado
- Vista previa de consumos calculada desde el escandallo real.
- Escalado según la cantidad de la tarea y las raciones base.
- Validación de existencias antes de cerrar.
- Consumo delegado a `MotorStock.consumir`.
- Alta de la elaboración terminada delegada a `MotorStock.registrar_entrada`.
- Cierre de tarea delegado a `MotorProduccionReal.finalizar_tarea`.
- Trazabilidad en `DATOS/piloto/produccion_stock_registros.json`.
- Protección contra dobles registros.
- Rollback de stock y producción ante errores.
- Registro de incidencia bloqueante cuando falta stock.

## Seguridad
- No se fuerza stock negativo.
- Sin escandallo no se cierra ni se modifica stock.
- Una tarea ya registrada no vuelve a descontar ingredientes.
