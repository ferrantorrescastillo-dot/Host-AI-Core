# RR1.6.2 — Recertificación final Restaurant Ready

## Estado automático

- [ ] Ejecutar `python ejecutar_certificacion_rr162.py`
- [ ] Todas las pruebas automáticas en verde
- [ ] Sin errores de colección

## Caso manual oficial

### 1. Evento
- [ ] Crear o seleccionar evento
- [ ] Añadir servicios
- [ ] Añadir pases y recetas
- [ ] Revisar ficha y línea temporal

### 2. Producción
- [ ] Crear plan desde el evento activo
- [ ] Generar planificación inteligente
- [ ] Ver reparto, horarios y conflictos
- [ ] Iniciar, pausar, reanudar y finalizar una tarea
- [ ] Revisar panel y recomendaciones

### 3. Stock
- [ ] Consultar un artículo por nombre parcial
- [ ] Registrar entrada con lote, ubicación, caducidad y coste
- [ ] Ver FIFO, valor y resumen operativo
- [ ] Registrar merma o ajuste físico

### 4. Compras
- [ ] Registrar necesidad
- [ ] Generar pedido sin duplicados
- [ ] Cambiar estado o confirmar advertencia de borrador
- [ ] Recibir pedido
- [ ] Ver resumen correcto y stock actualizado

### 5. Escandallos y costes
- [ ] Calcular coste de receta
- [ ] Confirmar ingredientes y precios
- [ ] Calcular coste operativo del evento activo
- [ ] Analizar y simular rentabilidad

### 6. IA contextual segura
- [ ] “¿Qué tengo que preparar para la boda?”
- [ ] “¿Qué tengo que cocinar primero?”
- [ ] “¿Qué tengo que comprar?”
- [ ] “¿Cuánto voy a ganar con esta boda?”
- [ ] Confirmar que no modifica datos en modo seguro

## Criterios de aprobación

- Cero errores críticos.
- Cero pérdida o corrupción de datos.
- El contexto activo se conserva entre módulos y tras reiniciar.
- Las cantidades y costes son coherentes entre Escandallos, Compras, Stock y Costes.
- No se duplica una recepción ni un pedido.
- La IA contextual propone el motor correcto y no ejecuta cambios.

## Resultado final

- [ ] APROBADO — Host AI Restaurant Ready v1.0
- [ ] APROBADO CON OBSERVACIONES
- [ ] NO APROBADO

Observaciones:

---
