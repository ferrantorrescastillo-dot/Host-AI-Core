# ROC-04B — COCINA
## Registro Oficial de Componentes

Versión: 1.0
Estado: Oficial

# Componentes incluidos

- Importadores
- Motores auxiliares
- Integración del dominio Cocina

# Objetivo

Completar el dominio Cocina definiendo los componentes encargados de importar información culinaria, asistir a los motores principales y conectar Cocina con Producción, Compras y Costes.

# Importadores

## Responsabilidad

Los importadores permiten incorporar información externa al sistema.

Funciones principales:

- Importación de artículos.
- Importación de recetas.
- Importación de menús.
- Normalización de datos.
- Validación previa.

Los importadores nunca deben modificar directamente los datos definitivos sin pasar por las validaciones correspondientes.

# Motores auxiliares

Agrupan utilidades comunes utilizadas por distintos dominios.

Ejemplos:

- Resolución de ingredientes.
- Conversión de unidades.
- Equivalencias culinarias.
- Validaciones.

No deben convertirse en propietarios de información de negocio.

# Integración

Usuario
↓
Conversación
↓
Importadores / Motores auxiliares
↓
MotorEscandallos
↓
Producción
↓
Costes

# Contratos

Importadores garantizan:

- Datos estructurados.
- Validaciones previas.
- Compatibilidad con el modelo oficial.

Motores auxiliares garantizan:

- Servicios reutilizables.
- Ausencia de lógica duplicada.

# Riesgos

- Importaciones incompletas.
- Datos duplicados.
- Reglas culinarias inconsistentes.

# Fichas rápidas

Importadores
- Estado: Activo
- Criticidad: Alta

Motores auxiliares
- Estado: Activo
- Criticidad: Media

# Reglas para Codex

Antes de modificar:

1. Leer ROC-01.
2. Leer ROC-04A.
3. Revisar DEVKIT.

Nunca:

- Saltarse las validaciones.
- Duplicar lógica existente.
- Crear nuevos importadores si ya existe uno reutilizable.

# Referencias

- ROC-01
- ROC-04A
- DEVKIT
- AGENTS.md

## Conclusión

Con ROC-04A y ROC-04B queda documentado el dominio Cocina y su integración con el resto de Host AI.
