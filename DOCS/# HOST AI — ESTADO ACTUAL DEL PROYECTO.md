# HOST AI — ESTADO ACTUAL DEL PROYECTO

Última actualización: R4.3 (pendiente de validación final)

---

# Rama de desarrollo

```
develop-6.1
```

---

# Filosofía del proyecto

Host AI no es un TPV ni un ERP tradicional.

Host AI es un sistema operativo para restaurantes.

La filosofía principal del proyecto es:

- La IA recomienda.
- El usuario decide.
- Ninguna decisión crítica se automatiza.
- Toda recomendación debe ser explicable.
- Todo debe ser trazable.
- Todo debe ser reversible.
- La lógica crítica nunca depende de IA generativa.

---

# Flujo de trabajo

Siempre trabajamos así:

Codex implementa

↓

Validación manual

↓

Revisión con ChatGPT

↓

git status

↓

Limpieza de JSON de pruebas

↓

Commit

↓

Push

Codex nunca hace commit.

Codex nunca hace push.

---

# Arquitectura

Se mantiene la arquitectura actual del proyecto.

APP

↓

CORE

↓

PIPELINES

↓

MOTORES

↓

MODELOS

↓

SERVICIOS

↓

DATOS

Cada capa tiene una responsabilidad clara y no debe mezclarse.

---

# Estado de desarrollo

## R1

Configuración del restaurante.

Estado:

✅ Completado.

---

## R2

Recursos operativos.

Incluye:

- personal
- turnos
- capacidades
- multiestación

Estado:

✅ Completado.

---

## R3

Producción.

Incluye:

- producción
- necesidades
- validación de recursos
- diagnósticos

Estado:

✅ Completado.

---

## R4.1

Centro de compras inteligentes.

Incluye:

- necesidades
- propuestas
- compras manuales
- historial
- proveedores
- persistencia

Estado:

✅ Completado.

---

## R4.1.1

Idempotencia.

Incluye:

- consolidación
- eliminación de duplicados
- migración
- tests

Estado:

✅ Completado.

---

## R4.2

Proveedor recomendado.

Incluye:

- proveedor preferente
- aprendizaje
- asociaciones producto-proveedor
- recomendación
- agrupación

Estado:

✅ Completado.

---

## R4.3

Optimización de compras.

Incluye:

- comparación de proveedores
- precios
- portes
- pedido mínimo
- plazos
- explicación de recomendaciones
- agrupación optimizada
- condiciones comerciales

Estado actual:

⏳ Implementado por Codex.

Pendiente únicamente de:

- validación manual
- revisión de git
- commit
- push

---

# Próximo sprint

R4.4

Gestión completa del ciclo de compra.

Flujo operativo objetivo:

Necesidad

↓

Propuesta

↓

Proveedor recomendado

↓

Confirmación manual

↓

Pedido

↓

Envío (manual)

↓

Recepción

↓

Entrada en almacén

↓

Stock disponible

Objetivos previstos:

- pedidos
- estados
- recepción
- albaranes
- incidencias
- entrada en almacén

---

# Roadmap previsto

Después de R4:

R5

Inventario inteligente.

- stock
- movimientos
- inventarios
- lotes
- trazabilidad
- caducidades
- mermas

---

R6

Congelación del Core.

Objetivos:

- estabilización
- integración completa
- optimización
- refactorización
- cobertura de tests

Al finalizar R6 el backend se considerará terminado.

---

# Fase posterior

Desarrollo de la aplicación web.

La web utilizará el Core ya construido.

Incluirá:

- dashboard
- producción
- compras
- inventario
- eventos
- reservas
- clientes
- personal
- costes
- KPIs
- IA integrada

---

# Fuente de verdad

El código del repositorio es siempre la fuente de verdad.

Este documento únicamente sirve para indicar el estado actual del proyecto y el punto exacto del roadmap.

Pendiente: Revisar si las propuestas de compra deben recalcular el proveedor recomendado cuando cambian los proveedores habituales.

El único punto que dejaría en la lista de mejoras es revisar la coherencia entre los avisos de bloqueo de la apertura de cocina y el estado que muestra la bandeja de trabajo. Es una mejora funcional, no un defecto que impida el uso del sistema.

Mejoras que anotaría

No son bloqueantes, pero sí interesantes para futuras versiones:

"Sin fecha" en el plan de producción, cuando el evento sí tiene fecha.
Diferenciar en el resumen conflictos reales de avisos por datos incompletos.
El aviso de "Supera el tiempo previsto en 1735.7 min" podría presentarse de forma más legible (por ejemplo, "1 día y 5 h") o indicar desde cuándo está abierta la tarea.


La única mejora que anotaría es el tratamiento de FIN cuando el usuario lo escribe al final de una línea de producto, para evitar duplicados accidentales. No afecta a la integridad de los datos porque el sistema sigue mostrando una vista previa antes de aplicar cualquier cambio. pythonpy.