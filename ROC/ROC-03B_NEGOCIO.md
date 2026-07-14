# ROC-03B — NEGOCIO
## Registro Oficial de Componentes

Versión: 1.0
Estado: Oficial

# Componentes incluidos

- RecepcionInteligentePiloto1
- MotorEventos
- MotorCostesInteligente

# Objetivo

Completar el dominio de Negocio definiendo los componentes responsables de la recepción de mercancías, la gestión de eventos y el cálculo de costes.

# Recepción Inteligente

## Responsabilidad

Es el punto oficial de entrada del producto al sistema.

Funciones:
- Validar recepciones.
- Registrar entradas.
- Actualizar stock mediante los flujos oficiales.
- Mantener la trazabilidad.

No debe crear pedidos ni modificar escandallos.

# MotorEventos

## Responsabilidad

Gobierna la planificación operativa de eventos.

Funciones:
- Crear eventos.
- Gestionar servicios y pases.
- Servir de origen para Producción y Costes.

No debe modificar directamente el stock.

# MotorCostesInteligente

## Responsabilidad

Calcular costes reales y previstos utilizando la información de artículos, escandallos, compras y eventos.

No modifica datos de negocio; únicamente analiza y calcula.

# Flujo del dominio

Compras
↓
Recepción Inteligente
↓
Stock
↓
Producción
↓
Evento
↓
Costes

# Contratos

Recepción garantiza:
- Entrada oficial al inventario.
- Trazabilidad.

Eventos garantiza:
- Planificación del servicio.

Costes garantiza:
- Cálculo reproducible.

# Riesgos

- Recepciones fuera del flujo oficial.
- Eventos modificados sin recalcular producción.
- Costes basados en datos incompletos.

# Fichas rápidas

Recepción Inteligente
- Estado: Activo
- Criticidad: Muy alta

MotorEventos
- Estado: Activo
- Criticidad: Alta

MotorCostesInteligente
- Estado: Activo
- Criticidad: Alta

# Reglas para Codex

Antes de modificar este dominio:

1. Leer ROC-01.
2. Leer ROC-02.
3. Leer ROC-03A.
4. Revisar las auditorías funcionales.

Nunca:
- Actualizar stock fuera de los flujos oficiales.
- Calcular costes con datos parciales sin avisar.
- Saltarse la autoridad de cada motor.

# Referencias

- ROC-01 Núcleo
- ROC-02 Operación
- ROC-03A Negocio
- Auditorías Fase 1
- AGENTS.md

## Conclusión

Con ROC-03A y ROC-03B queda definido el dominio de Negocio y las responsabilidades de sus componentes principales.
