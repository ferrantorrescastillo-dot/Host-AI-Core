# HOST AI WEB CHAT V1

Fecha: 2026-07-29
Estado: Implementado

## Objetivo

Construir Chat Web v1 consumiendo exclusivamente POST /api/v1/chat sin mover logica conversacional al frontend.

## Componentes creados

- src/services/chatService.ts
- src/__tests__/chat-service.test.ts

## Componentes modificados

- src/ui/pages/ChatPage.tsx
- src/ui/styles.css
- src/api/client.ts
- src/__tests__/chat.test.tsx

## Endpoint consumido

- POST /api/v1/chat

## Funcionalidad implementada

- panel de mensajes con estado vacio
- caja de entrada multilinea
- boton Enviar
- envio con Enter
- Shift+Enter para salto de linea
- indicador de carga
- bloqueo de doble envio
- scroll automatico al ultimo mensaje
- boton Reintentar ante error
- request_id visible para soporte
- modo seguro visible cuando datos_reales_modificados=false
- alerta visible si datos_reales_modificados=true

## Politica de respuesta

- se muestra exactamente el texto recibido desde la API
- no se genera texto de respuesta en frontend
- no se resume ni se reinterpretan respuestas

## Estados de interfaz

- vacio
- cargando
- respuesta correcta
- error de red
- error HTTP

## Accesibilidad

- navegacion por teclado
- foco devuelto a la caja de entrada al terminar una peticion
- etiquetas accesibles y panel con aria-live
- contraste y estilos de foco visibles

## Tests objetivo

- render inicial
- envio
- Enter
- Shift+Enter
- bloqueo de doble envio
- respuesta correcta
- error
- request_id
- indicador de carga
- modo seguro
- consumo exclusivo del cliente API

## Como abrir

1. Entrar en HOST_AI_WEB
2. npm install
3. npm run dev
4. Abrir /chat

## Como ejecutar pruebas de chat

1. Entrar en HOST_AI_WEB
2. npm run test -- src/__tests__/chat.test.tsx src/__tests__/chat-service.test.ts

## Limitaciones

- sin historial persistente
- sin streaming
- sin websocket
- sin login ni JWT
- sin markdown enriquecido
- sin adjuntos
- sin voz
- sin IA en navegador
