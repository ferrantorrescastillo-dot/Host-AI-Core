# CODEX-01.md
# Manual Operativo para Agentes de Programación (Parte 1)

Versión: 1.0
Estado: Activo

# 1. Objetivo

Este documento define cómo debe trabajar cualquier agente de programación (Codex u otro) dentro del proyecto Host AI.

No describe la arquitectura (ROC) ni el estado del proyecto (MASTER_PLAN). Describe el método de trabajo.

---

# 2. Documentos obligatorios

Antes de modificar cualquier línea de código, el agente debe leer:

1. AGENTS.md
2. MASTER_PLAN.md
3. El ROC correspondiente al dominio afectado

Si el cambio afecta a varios dominios, deberá consultar todos los ROC implicados.

---

# 3. Filosofía

Host AI no es una colección de scripts.

Es un producto modular para hostelería.

Cada modificación debe:

- respetar la arquitectura;
- reutilizar componentes existentes;
- evitar duplicidad de lógica;
- mantener la separación de responsabilidades.

---

# 4. Flujo de trabajo obligatorio

Solicitud
↓
Analizar documentación
↓
Analizar código
↓
Diseñar solución
↓
Implementar cambios mínimos
↓
Ejecutar pruebas
↓
Actualizar documentación
↓
Entregar

Nunca implementar sin comprender antes el dominio.

---

# 5. Reglas generales

- No crear motores si ya existe uno equivalente.
- No mover responsabilidades entre dominios.
- No romper compatibilidad sin justificarlo.
- Priorizar simplicidad y mantenimiento.

---

# 6. Qué nunca debe hacer un agente

- Modificar HostAICore sin evaluar impacto.
- Saltarse los motores para escribir datos.
- Eliminar código histórico sin autorización.
- Cambiar contratos públicos sin actualizar documentación.

---

# 7. Preparación antes de un sprint

Leer:
- AGENTS.md
- MASTER_PLAN.md
- ROC correspondiente

Revisar:
- pruebas existentes
- auditorías relacionadas

Definir:
- alcance
- riesgos
- criterio de éxito

---

# 8. Resultado esperado

Al finalizar un sprint:

- Código funcional.
- Tests ejecutados.
- Documentación coherente.
- Sin duplicidades.

Fin de CODEX-01.
