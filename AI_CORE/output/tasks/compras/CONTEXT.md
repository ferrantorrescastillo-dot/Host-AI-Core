# Task Context

- Tarea: Compras
- Dominio inferido: compras

# Host AI - Paquete de Contexto AI_CORE v1

## Objetivo del paquete
Contexto documental de solo lectura para guiar a un agente de IA sin copiar masivamente documentación, manteniendo autoridad y trazabilidad.

## Parámetros
- Dominio solicitado: compras
- Fuentes seleccionadas: 10 de 517

## Documentos consultados
- AGENTS.md (categoria=gobierno, prioridad=2, estado=selected)
- MASTER_PLAN.md (categoria=gobierno, prioridad=3, estado=selected)
- CODEX-01.md (categoria=gobierno, prioridad=4, estado=selected)
- CODEX-02.md (categoria=gobierno, prioridad=5, estado=selected)
- ROC/ROC-01A_NUCLEO.md (categoria=arquitectura, prioridad=110, estado=selected)
- ROC/ROC-01B_NUCLEO.md (categoria=arquitectura, prioridad=110, estado=selected)
- ROC/ROC-02A_OPERACION.md (categoria=arquitectura, prioridad=110, estado=selected)
- ROC/ROC-02B_OPERACION.md (categoria=arquitectura, prioridad=110, estado=selected)
- ROC/ROC-03A_NEGOCIO.md (categoria=arquitectura, prioridad=110, estado=selected)
- ROC/ROC-03B_NEGOCIO.md (categoria=arquitectura, prioridad=110, estado=selected)

## Orden de autoridad aplicado
1. AGENTS.md (categoria=gobierno, prioridad=2)
2. MASTER_PLAN.md (categoria=gobierno, prioridad=3)
3. CODEX-01.md (categoria=gobierno, prioridad=4)
4. CODEX-02.md (categoria=gobierno, prioridad=5)
5. ROC/ROC-01A_NUCLEO.md (categoria=arquitectura, prioridad=110)
6. ROC/ROC-01B_NUCLEO.md (categoria=arquitectura, prioridad=110)
7. ROC/ROC-02A_OPERACION.md (categoria=arquitectura, prioridad=110)
8. ROC/ROC-02B_OPERACION.md (categoria=arquitectura, prioridad=110)

## Resumen estructurado por fuente
### AGENTS.md
- Título detectado: AGENTS.md — HOST AI
- > Punto de entrada obligatorio para cualquier agente de programación que trabaje en este repositorio.
- > Aplicable a Codex y a cualquier otro agente compatible con instrucciones de repositorio.
- Tu función es colaborar en el desarrollo de Host AI sin perder su identidad, sin duplicar lógica, sin romper componentes certificados y sin modificar datos reales durante pruebas o diagnósticos.
- Host AI es un segundo de cocina digital para restaurantes, caterings, hoteles y colectividades.
- No es un chatbot independiente.
- Referencia original: consultar el archivo fuente para precisión operativa.

### MASTER_PLAN.md
- Título detectado: MASTER_PLAN.md
- Este documento es el panel de control oficial del desarrollo de Host AI.
- No sustituye al DEVKIT, AGENTS ni a los ROC. Su función es indicar en todo momento:
- dónde está el proyecto;
- qué está terminado;
- qué se está desarrollando;
- Referencia original: consultar el archivo fuente para precisión operativa.

### CODEX-01.md
- Título detectado: CODEX-01.md
- Este documento define cómo debe trabajar cualquier agente de programación (Codex u otro) dentro del proyecto Host AI.
- No describe la arquitectura (ROC) ni el estado del proyecto (MASTER_PLAN). Describe el método de trabajo.
- Antes de modificar cualquier línea de código, el agente debe leer:
- 3. El ROC correspondiente al dominio afectado
- Si el cambio afecta a varios dominios, deberá consultar todos los ROC implicados.
- Referencia original: consultar el archivo fuente para precisión operativa.

### CODEX-02.md
- Título detectado: CODEX-02.md
- Antes de cerrar cualquier sprint el agente debe:
- Ejecutar los tests relacionados con el dominio afectado.
- Verificar que no aparecen regresiones.
- Si crea una funcionalidad nueva, añadir pruebas cuando proceda.
- Nunca dar por terminado un sprint sin validar el comportamiento.
- Referencia original: consultar el archivo fuente para precisión operativa.

### ROC/ROC-01A_NUCLEO.md
- Título detectado: ROC-01A — NÚCLEO DEL SISTEMA
- **Dominio:** Núcleo del sistema
- Este documento define el Núcleo Oficial de Host AI.
- Su objetivo es definir los componentes que hacen posible el funcionamiento de Host AI, establecer claramente sus responsabilidades y fijar las reglas que ningún desarrollador ni ningún agente debe romper.
- HostAICore
- BaseDatosLocal
- Referencia original: consultar el archivo fuente para precisión operativa.

### ROC/ROC-01B_NUCLEO.md
- Título detectado: ROC-01B — NÚCLEO DEL SISTEMA
- BaseDatosLocal es la capa oficial de persistencia utilizada por la línea activa del piloto.
- cargar colecciones;
- guardar colecciones;
- mantener metadatos;
- ofrecer una API sencilla al resto del sistema.
- Referencia original: consultar el archivo fuente para precisión operativa.

### ROC/ROC-02A_OPERACION.md
- Título detectado: ROC-02A — OPERACIÓN
- MotorProduccionReal
- ProduccionGuiadaPiloto13
- ProduccionStockPiloto14
- Este ROC define el dominio de Operación, responsable de ejecutar el trabajo diario de cocina y convertir la planificación en producción real.
- Planes de producción
- Referencia original: consultar el archivo fuente para precisión operativa.

### ROC/ROC-02B_OPERACION.md
- Título detectado: ROC-02B — OPERACIÓN
- JornadaPiloto12
- BandejaTrabajoPiloto11
- Este documento completa el dominio de Operación definiendo cómo se organizan y presentan las tareas diarias del restaurante.
- Mi Jornada ofrece al usuario una vista unificada del trabajo pendiente.
- Agrupa información procedente de:
- Referencia original: consultar el archivo fuente para precisión operativa.

### ROC/ROC-03A_NEGOCIO.md
- Título detectado: ROC-03A — NEGOCIO
- MotorStock
- MotorCompras
- El dominio de Negocio gobierna el inventario y el abastecimiento del restaurante. Su misión es garantizar que exista stock suficiente, que las compras sean coherentes y que toda la información económica parta de datos fiables.
- MotorStock es el propietario funcional del stock.
- Gestión de lotes.
- Referencia original: consultar el archivo fuente para precisión operativa.

### ROC/ROC-03B_NEGOCIO.md
- Título detectado: ROC-03B — NEGOCIO
- RecepcionInteligentePiloto1
- MotorEventos
- MotorCostesInteligente
- Completar el dominio de Negocio definiendo los componentes responsables de la recepción de mercancías, la gestión de eventos y el cálculo de costes.
- Es el punto oficial de entrada del producto al sistema.
- Referencia original: consultar el archivo fuente para precisión operativa.

## Advertencias
- Sin advertencias críticas detectadas.

## Instrucciones para el agente
- Si existe conflicto entre resúmenes, consultar primero el documento original de mayor autoridad según el orden anterior.
- No asumir que el resumen sustituye a la fuente: usarlo solo como mapa de arranque.
- Si falta un documento obligatorio, detener decisiones críticas y solicitar revisión humana.
