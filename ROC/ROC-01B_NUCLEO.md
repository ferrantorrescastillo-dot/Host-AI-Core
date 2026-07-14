# ROC-01B — NÚCLEO DEL SISTEMA
## Registro Oficial de Componentes (ROC)

**Versión:** 1.0
**Estado:** Oficial

# 12. BaseDatosLocal

## Misión
BaseDatosLocal es la capa oficial de persistencia utilizada por la línea activa del piloto.

Su función es:
- cargar colecciones;
- guardar colecciones;
- mantener metadatos;
- ofrecer una API sencilla al resto del sistema.

No debe contener reglas de negocio.

## Fuente de verdad

Actualmente administra, entre otras, las colecciones:

- eventos
- planes_produccion
- stock_lotes
- stock_movimientos
- compras_necesidades
- compras_pedidos
- escandallos
- precios

## Garantiza

- Lectura consistente.
- Escritura de colecciones.
- Uso compartido por los motores.

## No garantiza

- Transacciones atómicas.
- Journaling.
- Recuperación automática tras una caída del proceso.

# 13. BasePipeline

## Objetivo

Definir un contrato común para todos los pipelines del proyecto.

Debe unificar:

- entrada;
- validación;
- ejecución;
- salida.

Ventajas:

- comportamiento homogéneo;
- reutilización;
- menor duplicidad.

# 14. Orquestador IA

## Misión

Interpretar las peticiones del usuario y decidir qué componente debe resolverlas.

No es propietario de Producción, Compras o Stock.

Debe coordinar, nunca sustituir a los motores.

# 15. Dependencias oficiales

HostAICore
↓
BaseDatosLocal
↓
Motores
↓
Servicios
↓
Interfaz

El Orquestador utiliza este ecosistema, pero no rompe la jerarquía.

# 16. Contratos oficiales

## HostAICore

Garantiza:

- inicialización;
- composición;
- compartición de dependencias.

No garantiza:

- lógica de negocio;
- persistencia;
- reconciliación funcional.

## BaseDatosLocal

Garantiza:

- persistencia JSON.

No garantiza:

- concurrencia avanzada;
- rollback de sistema de archivos.

## BasePipeline

Garantiza:

- contrato común.

## Orquestador

Garantiza:

- coordinación.

No garantiza:

- autoridad sobre los datos.

# 17. Impacto de modificaciones

Modificar HostAICore puede afectar:

- Producción
- Compras
- Stock
- Eventos
- Costes
- Recepción
- Mi Jornada
- Bandeja

Modificar BaseDatosLocal afecta a todos los motores que persisten datos.

# 18. Riesgos

- HostAICore demasiado centralizado.
- Persistencia JSON no atómica.
- Convivencia de componentes históricos.
- Contratos antiguos presentes en algunos tests.

# 19. Reglas para Codex

Antes de modificar el Núcleo:

1. Leer AGENTS.md.
2. Leer MASTER_PLAN.md.
3. Leer ROC-01.
4. Revisar la última auditoría.

Nunca:

- mover responsabilidades de los motores al Core;
- duplicar componentes;
- cambiar contratos públicos sin justificarlo.

# 20. Referencias

Documentación relacionada:

- AGENTS.md
- MASTER_PLAN.md
- Auditoría Fase 1
- DEVKIT
- ROC-02 (Operación)
- ROC-03 (Negocio)

# Conclusión

El Núcleo proporciona la infraestructura común de Host AI. Su misión es construir y coordinar el sistema, dejando toda la lógica de negocio en los motores especializados.

Con ROC-01A y ROC-01B queda definido el Registro Oficial del Núcleo sobre el que se apoyará el resto de componentes.
