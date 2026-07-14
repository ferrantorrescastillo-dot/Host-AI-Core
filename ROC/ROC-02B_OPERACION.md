# ROC-02B — OPERACIÓN
## Registro Oficial de Componentes

Versión: 1.0
Estado: Oficial

# Componentes incluidos

- JornadaPiloto12
- BandejaTrabajoPiloto11

# Objetivo

Este documento completa el dominio de Operación definiendo cómo se organizan y presentan las tareas diarias del restaurante.

# JornadaPiloto12

## Misión

Mi Jornada ofrece al usuario una vista unificada del trabajo pendiente.

Agrupa información procedente de:

- Producción
- Compras
- Eventos
- Recepciones
- Bandeja

No genera tareas nuevas; únicamente las organiza y prioriza.

# BandejaTrabajoPiloto11

## Misión

La Bandeja centraliza tareas procedentes de distintos dominios.

Tipos habituales:

- Producción
- Compras
- Recepciones
- Eventos
- Revisiones

Es el punto común para el seguimiento operativo.

# Flujo operativo

Eventos
↓
Producción
↓
Bandeja
↓
Mi Jornada
↓
Usuario
↓
Ejecución
↓
Producción → Stock

# Contratos

## Jornada

Garantiza:
- Vista consolidada.
- Priorización.

No garantiza:
- Reconciliación automática de estados.

## Bandeja

Garantiza:
- Registro de tareas.
- Estado operativo.

No garantiza:
- Sincronización automática con todas las fuentes.

# Riesgos identificados

- Reconciliación pendiente entre Bandeja y dominios.
- Posibles tareas huérfanas.
- Dependencia de la persistencia JSON.

# Fichas rápidas

## JornadaPiloto12
Estado: Activo
Criticidad: Alta
Autoridad: Vista operativa diaria

## BandejaTrabajoPiloto11
Estado: Activo
Criticidad: Muy alta
Autoridad: Gestión transversal de tareas

# Reglas para Codex

Antes de modificar estos componentes:

1. Revisar ROC-01.
2. Revisar ROC-02A.
3. Consultar la Auditoría Funcional Fase 1.3.

Nunca:
- Duplicar tareas.
- Saltarse MotorProduccionReal.
- Crear estados incompatibles entre Bandeja y Jornada.

# Referencias

- ROC-01 Núcleo
- ROC-02A Operación
- Auditoría Fase 1.3
- Auditoría Fase 1.4
- AGENTS.md

## Conclusión

Con ROC-02A y ROC-02B queda documentado el dominio de Operación y su relación con el resto del sistema.
