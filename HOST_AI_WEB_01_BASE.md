# HOST AI WEB-01 BASE

Fecha: 2026-07-29
Estado: Implementado (esqueleto inicial)

## Tecnologia elegida

- React 18 + TypeScript + Vite
- Motivo:
  - no existia frontend implementado en el repositorio,
  - stack moderno y estable,
  - arranque minimo,
  - conexion simple con API,
  - testing ligero con Vitest + Testing Library.

## Como arrancar la web

1. Entrar en carpeta HOST_AI_WEB
2. Instalar dependencias: npm install
3. Ejecutar desarrollo: npm run dev
4. Ejecutar tests: npm run test
5. Compilar: npm run build

Nota: en este entorno no hay Node/npm instalado, por eso no fue posible ejecutar estos comandos aqui.

## Variables de entorno

Archivo de ejemplo:

- HOST_AI_WEB/.env.example

Variable usada:

- VITE_HOST_AI_API_BASE_URL

## Estructura de carpetas

HOST_AI_WEB/
- package.json
- tsconfig.json
- vite.config.ts
- index.html
- .env.example
- src/
  - main.tsx
  - config/env.ts
  - api/client.ts
  - types/api.ts
  - ui/
    - App.tsx
    - styles.css
    - layout/AppLayout.tsx
    - components/LoadingState.tsx
    - components/ErrorState.tsx
    - pages/HomePage.tsx
    - pages/DashboardPage.tsx
    - pages/ChatPage.tsx
    - pages/PlaceholderPage.tsx
    - pages/NotFoundPage.tsx
  - test/
    - setup.ts
  - __tests__/
    - layout.test.tsx
    - navigation.test.tsx
    - dashboard.test.tsx
    - chat.test.tsx
    - api-client.test.ts
    - no-core-import.test.ts
    - placeholders.test.tsx
    - responsive.test.ts

## Rutas WEB-01

- /
- /dashboard
- /chat
- /eventos
- /produccion
- /compras
- /stock
- /configuracion
- ruta 404 para no encontradas

## Endpoints consumidos

- GET /api/v1/dashboard
- POST /api/v1/chat

La web no llama directamente a Core, motores ni DATOS.

## Limitaciones de WEB-01

- Sin autenticacion
- Sin JWT
- Sin websocket
- Sin streaming
- Sin historial persistente de chat
- Sin acciones de escritura de negocio
- Modulos no funcionales fuera de Dashboard y Chat muestran placeholder

## Siguiente sprint recomendado

WEB-02:

- conectividad robusta con API (reintentos controlados y telemetria basica),
- refinado de UX operativa,
- contratos visuales por modulo,
- pruebas de integracion ligera frontend-api.
