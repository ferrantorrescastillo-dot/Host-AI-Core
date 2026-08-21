# General Agent Platform Interfaces V1

Estado: infraestructura aditiva, no integrada en runtime.

Este paquete define contratos neutrales para tools, autorización, policy,
ejecución mediante handlers inyectados, sesión namespaced y contextos opacos de
acciones. No registra capabilities de negocio ni importa servicios de dominio.

El runtime histórico continúa siendo la autoridad operativa. La migración se
realizará incrementalmente por dominio; añadir estas interfaces no cambia Chat,
la API pública, el frontend ni la persistencia actuales.
