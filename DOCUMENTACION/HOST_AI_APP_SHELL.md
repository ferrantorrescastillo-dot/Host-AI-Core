# HOST AI APP SHELL

Estado: Implementado (APP-01)
Fecha: 2026-07-23
Alcance: Base visual y estructural de transicion

Nota de arranque (Freeze-A2): el shell no es una ruta oficial de arranque por si mismo.
Se abre como modulo desde la ruta oficial: main.py -> lanzador_piloto_01 -> modo piloto.

## 1. Arquitectura visual

Application Shell

- Sidebar
- Header
- Main Content
- Host AI Panel
- Notifications
- Context Indicator

Implementacion APP-01 en consola:

- APP/app_shell_host_ai.py (composicion del shell)
- SERVICIOS/contexto_activo_host_ai.py (contrato de contexto)
- SERVICIOS/chat_host_ai_shell_service.py (servicio de chat por orquestador/engine)

## 2. Componentes

### Sidebar

Navegacion principal con modulos:

- Inicio / Host AI
- Eventos
- Produccion
- Compras
- Stock
- Recetas y Escandallos
- Menus
- Catalogo
- Importaciones
- Incidencias
- Estadisticas
- Configuracion

### Header

Muestra:

- entorno;
- proveedor IA activo;
- contexto activo.

### Main Content

HOME inicial con:

- saludo;
- estado general;
- caja de entrada de chat (acceso por panel);
- bandeja inteligente provisional;
- acciones rapidas;
- actividad reciente;
- indicadores basicos.

### Host AI Panel

- vista resumida del ultimo mensaje chat;
- estado de conversacion.

### Notifications

- advertencias y errores de integracion;
- fallback de modulos no integrados de forma directa.

### Context Indicator

Contrato desacoplado de UI en ServicioContextoActivoHostAI.

## 3. Navegacion

Estrategia APP-01:

- No eliminar menus existentes.
- Reutilizar metodos de AppConsolaHostAI.
- Fallback seguro cuando no haya panel dedicado.

## 4. Relacion con modulos existentes

El shell no reimplementa negocio:

- eventos -> app._menu_eventos()
- produccion -> app._menu_produccion_real()
- compras -> app._menu_compras()
- stock -> app._menu_stock()
- recetas/escandallos -> app._menu_escandallos_recetas()
- importaciones -> app._menu_excel()

Menus, catalogo, incidencias y estadisticas mantienen fallback con notificacion.

## 5. Relacion con Host AI Engine

Flujo de chat APP-01:

UI (AppShellHostAI)
-> ServicioChatHostAIShell
-> Orquestador (SolicitudHostAI host_ai_engine_consulta)
-> Host AI Engine
-> Proveedor SIMULADO
-> Respuesta normalizada

No hay llamadas directas a providers desde UI.

## 6. Estrategia de transicion

- Integracion en modo piloto como opcion adicional visible.
- Coexistencia con UI actual.
- Migracion incremental por modulos/paneles, no big bang.

## 7. Riesgos

- Divergencia entre shell y rutas legacy.
- Sobrecarga de estado visual en consola.
- Cobertura parcial de paneles dedicados.

## 8. Decisiones tomadas

1. Mantener stack actual (consola Python).
2. Aislar chat y contexto en servicios de UI.
3. Reutilizar Core/Orquestador/Engine existentes sin cambios.
4. No introducir persistencia nueva de conversaciones.

## 9. Trabajo pendiente

- Paneles nativos para Catalogo, Incidencias y Estadisticas.
- Modelo unico de actividad reciente multi-modulo.
- Integracion contextual avanzada por pantalla (evento/receta/menu/produccion).
- Preparar adaptador para futura UI grafica sin romper contratos.

## 10. Actualizacion APP-01.5

- Home conectada a datos reales de solo lectura mediante `HostAIHomeReadService`.
- Bandeja inteligente determinista con prioridad reproducible y severidad explicita.
- Chat integrado con router determinista y acciones de navegacion seguras.
- Soporte de errores parciales por modulo sin bloquear toda la pantalla.
- Flujo mantenido: UI -> Chat Service -> Orquestador -> Host AI Engine -> SIMULADO.
