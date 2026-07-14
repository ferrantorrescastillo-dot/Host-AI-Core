# HOST AI 5.5.5B.7.3.2

## Precio de venta y rentabilidad completa

Este parche permite proponer un precio de venta opcional para un escandallo, calcular su impacto económico y guardarlo únicamente después de una confirmación explícita.

### Flujo seguro

1. `Pon un precio de venta de 9,50 € por unidad para ensaladilla de gamba.`
2. Host AI muestra coste, beneficio, food cost y margen previstos, sin escribir datos.
3. `Confirma el precio de venta.`
4. Host AI crea una copia de seguridad y actualiza atómicamente `DATOS/db/escandallos_canonicos.json`.

También se puede cancelar con:

`Cancela el precio de venta.`

### Consultas

`Muéstrame la rentabilidad de ensaladilla de gamba.`

La consulta muestra coste total, coste unitario, PVP, beneficio bruto, beneficio sobre coste, food cost, margen bruto e IVA.

### Seguridad

- El primer comando solo crea una propuesta pendiente.
- La escritura requiere confirmación explícita.
- Se crea una copia de seguridad antes de modificar la base canónica.
- La escritura utiliza reemplazo atómico.
