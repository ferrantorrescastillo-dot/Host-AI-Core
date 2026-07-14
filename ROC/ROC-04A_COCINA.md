# ROC-04A — COCINA
## Registro Oficial de Componentes

Versión: 1.0
Estado: Oficial

# Componentes incluidos

- MotorEscandallos
- Orquestación Conversacional

# Objetivo

El dominio Cocina es responsable del conocimiento culinario del sistema. Define cómo se elaboran las recetas, cómo se calculan sus costes base y cómo el usuario interactúa con Host AI para consultar o generar información gastronómica.

# MotorEscandallos

## Autoridad

Es el propietario funcional de:

- Recetas
- Ingredientes
- Rendimientos
- Costes teóricos
- Relación receta ↔ artículos

Responsabilidades:

- Calcular escandallos.
- Resolver ingredientes.
- Mantener la coherencia de recetas.
- Proporcionar información a Costes y Producción.

No debe:

- Modificar stock.
- Crear pedidos.
- Gestionar eventos.

# Conversación

## Responsabilidad

Interpretar las peticiones culinarias del usuario y transformarlas en acciones sobre los motores correspondientes.

Ejemplos:

- Consultar una receta.
- Calcular un escandallo.
- Buscar ingredientes.
- Crear propuestas.

No contiene la lógica culinaria; coordina los componentes que sí la implementan.

# Flujo del dominio

Usuario
↓
Conversación
↓
MotorEscandallos
↓
Respuesta

# Contratos

MotorEscandallos garantiza:

- Cálculos reproducibles.
- Relación receta-artículos.
- Rendimientos consistentes.

Conversación garantiza:

- Interpretación de intención.
- Derivación al motor correcto.

# Riesgos

- Recetas incompletas.
- Ingredientes sin correspondencia.
- Conversaciones ambiguas.

# Fichas rápidas

MotorEscandallos
- Estado: Activo
- Criticidad: Muy alta
- Dominio: Cocina

Conversación
- Estado: Activo
- Criticidad: Alta
- Dominio: IA

# Reglas para Codex

Antes de modificar este dominio:

1. Leer ROC-01.
2. Leer ROC-03.
3. Revisar las reglas del DEVKIT.

Nunca:

- Utilizar artículos A.P como materias primas.
- Duplicar recetas.
- Cambiar cálculos sin actualizar pruebas.

# Referencias

- ROC-01 Núcleo
- ROC-03 Negocio
- DEVKIT
- AGENTS.md

## Conclusión

MotorEscandallos y Conversación constituyen el núcleo culinario de Host AI y proporcionan el conocimiento gastronómico sobre el que trabajan Producción, Costes y el asistente inteligente.
