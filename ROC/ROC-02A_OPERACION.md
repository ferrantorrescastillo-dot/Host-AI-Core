# ROC-02A — OPERACIÓN
## Registro Oficial de Componentes

Versión: 1.0
Estado: Oficial

# Componentes incluidos

- MotorProduccionReal
- ProduccionGuiadaPiloto13
- ProduccionStockPiloto14

# Objetivo

Este ROC define el dominio de Operación, responsable de ejecutar el trabajo diario de cocina y convertir la planificación en producción real.

# MotorProduccionReal

## Responsabilidad

Es la autoridad sobre:

- Planes de producción
- Tareas
- Estados
- Incidencias
- Bloqueos
- Progreso

Nunca debe modificar directamente:
- Compras
- Eventos
- Costes

# Producción Guiada

Es la interfaz operativa del cocinero.

Su función es:

- mostrar tareas;
- priorizar;
- iniciar;
- pausar;
- finalizar;
- registrar incidencias.

No contiene la lógica de producción; delega en MotorProduccionReal.

# Producción → Stock

Responsable del cierre de producción.

Flujo:

Producción
↓
Validación
↓
Consumo de ingredientes
↓
Entrada del producto terminado
↓
Actualización de lotes
↓
Trazabilidad

# Relaciones

MotorProduccionReal
↓
ProduccionGuiada
↓
ProduccionStock
↓
MotorStock

# Riesgos

- Bloqueos todavía simples.
- Rollback no atómico.
- Dependencia de persistencia JSON.
- Reconciliación pendiente con Bandeja.

# Reglas para Codex

Antes de modificar Producción:

- leer ROC-01;
- revisar auditoría funcional;
- no mover lógica al Core;
- mantener MotorProduccionReal como autoridad.

# Referencias

- ROC-01 Núcleo
- Auditoría Fase 1.2
- Auditoría Fase 1.3
- AGENTS.md

Fin de ROC-02A.
