# HOST AI Platform - API-01 Base

Estado: Propuesta implementada (estructura)
Fecha: 2026-07-29

## 1. Arquitectura propuesta

Arquitectura objetivo:

Usuario
-> Web
-> API
-> Host AI Core
-> Motores
-> Datos

Principio de diseno:

- La API es solo fachada.
- La autoridad funcional se mantiene en Core.
- No se mueve logica de negocio a API.

## 2. Arbol de carpetas (API-01)

API/
- __init__.py
- app.py
- README.md
- router.py
- contracts/
  - __init__.py
  - http_models.py
- facade/
  - __init__.py
  - core_public_facade.py
  - core_public_stub.py
- endpoints/
  - __init__.py
  - health.py
  - version.py
  - executive.py
  - dashboard.py
  - eventos.py
  - workflow.py
  - plan.py
  - chat.py

## 3. Responsabilidades por modulo

- contracts/http_models.py:
  - Contratos de entrada/salida HTTP neutrales.

- facade/core_public_facade.py:
  - Contrato unico de acceso permitido al Core desde API.

- facade/core_public_stub.py:
  - Implementacion temporal sin negocio para API-01.

- endpoints/*.py:
  - Capa de transporte; traduce request -> fachada -> response.

- router.py:
  - Tabla oficial de rutas y despacho por metodo/path.

- app.py:
  - Ensamblaje de la API.

## 4. Que reutiliza del Core

Reutilizacion prevista (sin implementacion funcional en API-01):

- Executive: SERVICIOS/host_ai_executive.py
- Workflow operativo: SERVICIOS/orquestador_flujo_operativo.py
- Servicios publicos certificados de lectura y contexto:
  - SERVICIOS/host_ai_home_read_service.py
  - SERVICIOS/chat_host_ai_shell_service.py
  - SERVICIOS/host_ai_tool_registry.py
  - SERVICIOS/host_ai_tool_resolver.py
  - SERVICIOS/host_ai_tool_executor.py

Nota: En API-01 se define solo el contrato de integracion. No se conectan aun llamadas de negocio.

## 5. Que queda para API-02

- Conectar facade contra Executive/Workflow/servicios publicos certificados.
- Definir modelos de respuesta API estables por endpoint.
- Gestion de errores y codigos HTTP por contrato.
- Trazabilidad tecnica por request_id.
- Pruebas de contrato de endpoints (sin tocar Core).
- Arranque HTTP real (framework y servidor) sin alterar logica de Core.

## 6. Restricciones respetadas

- No se modifico Core.
- No se modifico Executive.
- No se modificaron Workflows.
- No se modificaron Produccion, Compras, Stock ni Eventos.
- No se modificaron datos reales.
- No se introdujo IA generativa.
- No se uso Git.
