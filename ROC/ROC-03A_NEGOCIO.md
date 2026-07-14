# ROC-03A — NEGOCIO
## Registro Oficial de Componentes

Versión: 1.0
Estado: Oficial

# Componentes incluidos

- MotorStock
- MotorCompras

# Objetivo

El dominio de Negocio gobierna el inventario y el abastecimiento del restaurante. Su misión es garantizar que exista stock suficiente, que las compras sean coherentes y que toda la información económica parta de datos fiables.

# MotorStock

## Autoridad

MotorStock es el propietario funcional del stock.

Responsabilidades:

- Gestión de lotes.
- Entradas y salidas.
- Trazabilidad.
- Existencias.
- Consumos.

No debe:

- Generar pedidos.
- Planificar producción.
- Crear eventos.

# MotorCompras

## Autoridad

MotorCompras gobierna las necesidades y pedidos.

Responsabilidades:

- Detectar necesidades.
- Generar propuestas.
- Gestionar pedidos.
- Seguimiento de recepción.

No debe modificar directamente el stock; esa responsabilidad corresponde a Recepción Inteligente y a los flujos oficiales de entrada.

# Relación entre ambos

Producción
↓
MotorStock
↓
Necesidades
↓
MotorCompras
↓
Pedido
↓
Recepción
↓
MotorStock

# Contratos

## MotorStock

Garantiza:
- Estado actual del inventario.
- Gestión de movimientos.
- Consulta de existencias.

No garantiza:
- Compras automáticas.
- Producción.

## MotorCompras

Garantiza:
- Gestión del ciclo de compra.
- Relación con proveedores.
- Propuestas de pedido.

No garantiza:
- Actualización directa del inventario.

# Riesgos

- Stock desincronizado tras recepciones incompletas.
- Necesidades duplicadas.
- Persistencia JSON no transaccional.

# Fichas rápidas

MotorStock
- Estado: Activo
- Criticidad: Muy alta
- Dominio: Inventario

MotorCompras
- Estado: Activo
- Criticidad: Muy alta
- Dominio: Abastecimiento

# Reglas para Codex

Antes de modificar:
1. Leer ROC-01.
2. Leer ROC-02.
3. Revisar auditorías de persistencia.

Nunca:
- Fusionar responsabilidades de Stock y Compras.
- Saltarse los motores para modificar datos.
- Duplicar reglas de negocio.

# Referencias

- ROC-01 Núcleo
- ROC-02 Operación
- Auditoría Fase 1.2
- Auditoría Fase 1.3
- AGENTS.md

## Conclusión

MotorStock y MotorCompras forman la base operativa del abastecimiento y deben mantenerse como autoridades independientes que colaboran mediante contratos claros.
