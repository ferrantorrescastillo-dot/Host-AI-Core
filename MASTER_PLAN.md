# MASTER_PLAN.md
# HOST AI — Plan Maestro del Proyecto

Versión: 1.0
Estado: Activo

---

# 1. Objetivo

Este documento es el panel de control oficial del desarrollo de Host AI.

No sustituye al DEVKIT, AGENTS ni a los ROC. Su función es indicar en todo momento:

- dónde está el proyecto;
- qué está terminado;
- qué se está desarrollando;
- cuál es el siguiente sprint.

---

# 2. Estado actual

## Documentación completada

- AGENTS.md
- Auditoría Fase 1
- ROC-01 Núcleo
- ROC-02 Operación
- ROC-03 Negocio
- ROC-04 Cocina

## Pendiente

- CODEX.md
- Consolidación del repositorio
- Integración con Codex
- Primer sprint de mantenimiento

---

# 3. Arquitectura oficial

Núcleo:
- HostAICore
- BaseDatosLocal
- BasePipeline
- Orquestador IA

Operación:
- Producción
- Producción Guiada
- Producción→Stock
- Jornada
- Bandeja

Negocio:
- Stock
- Compras
- Recepción
- Eventos
- Costes

Cocina:
- Escandallos
- Conversación
- Importadores

---

# 4. Roadmap

✔ Auditorías
✔ ROC
▶ CODEX.md
▶ Consolidación para Codex
▶ DEVKIT-CODEX-0.1
▶ Integración GPT
▶ Evolución funcional

---

# 5. Sprint activo

Nombre:
Preparación para Codex

Objetivo:
Dejar el proyecto documentado y listo para trabajar con un agente de programación.

Fuera de alcance:
- Nuevas funcionalidades.
- Refactors masivos.

---

# 6. Riesgos conocidos

- Persistencia JSON no transaccional.
- Componentes históricos en el repositorio.
- Algunos tests dependen de recursos externos.
- Reconciliación de Bandeja pendiente.

---

# 7. Reglas

Antes de modificar código:

1. Leer AGENTS.md.
2. Leer MASTER_PLAN.md.
3. Leer el ROC correspondiente.
4. Revisar auditorías si el cambio afecta al dominio.

---

# 8. Próximo trabajo

1. Finalizar CODEX.md.
2. Instalar Codex.
3. Ejecutar DEVKIT-CODEX-0.1.
4. Consolidar la suite de tests.
5. Comenzar nuevos sprints funcionales.

---

# 9. Criterio de éxito

El proyecto estará preparado para desarrollo asistido cuando:

- La documentación principal esté completa.
- Los ROC sean la referencia de arquitectura.
- Codex pueda ejecutar un sprint completo siguiendo AGENTS + MASTER_PLAN + ROC.

Fin del documento.
