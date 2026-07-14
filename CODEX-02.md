# CODEX-02.md
# Manual Operativo para Agentes de Programación (Parte 2)

Versión: 1.0
Estado: Activo

# 9. Sistema de pruebas

Antes de cerrar cualquier sprint el agente debe:

- Ejecutar los tests relacionados con el dominio afectado.
- Verificar que no aparecen regresiones.
- Si crea una funcionalidad nueva, añadir pruebas cuando proceda.

Nunca dar por terminado un sprint sin validar el comportamiento.

---

# 10. Normas de desarrollo

Principios obligatorios:

- Cambios pequeños y controlados.
- Reutilizar componentes existentes.
- No duplicar lógica.
- Mantener una única autoridad por dominio.
- Evitar dependencias innecesarias.

---

# 11. Documentación obligatoria

Si un sprint modifica el comportamiento del sistema, revisar si corresponde actualizar:

- MASTER_PLAN.md
- ROC del dominio afectado
- CHANGELOG
- Documentación técnica relacionada

No modificar documentación que no haya cambiado.

---

# 12. Cierre de sprint

Checklist mínimo:

[ ] Código implementado.
[ ] Tests ejecutados.
[ ] Sin errores conocidos nuevos.
[ ] Documentación revisada.
[ ] Riesgos identificados.
[ ] Resultado resumido.

Solo entonces el sprint puede marcarse como completado.

---

# 13. Gestión de incidencias

Si durante el trabajo aparecen:

- contratos rotos;
- deuda técnica;
- componentes duplicados;
- riesgos arquitectónicos;

el agente debe registrarlos y no ocultarlos.

---

# 14. Buenas prácticas

- Explicar decisiones relevantes.
- Mantener coherencia con AGENTS.md.
- Respetar MASTER_PLAN.
- Consultar siempre el ROC correspondiente.

---

# 15. Qué hacer cuando exista una duda

Orden de prioridad:

1. AGENTS.md
2. MASTER_PLAN.md
3. ROC correspondiente
4. Código existente
5. Auditorías

Nunca inventar comportamiento si puede deducirse del proyecto.

---

# 16. Objetivo final

El agente debe actuar como un desarrollador que mantiene Host AI, no como un generador de código aislado.

Cada cambio debe dejar el proyecto:

- más estable;
- mejor documentado;
- más fácil de mantener.

Fin de CODEX-02.
