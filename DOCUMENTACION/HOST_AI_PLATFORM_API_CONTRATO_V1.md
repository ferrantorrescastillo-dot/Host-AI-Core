# Host AI Platform API - Contrato Publico Unico v1

Estado: Oficial para API-06
Fecha: 2026-07-29
Ambito: Capa API de Host AI Platform

## 1. Objetivo

Este documento define el contrato publico unico de respuestas HTTP para todos los endpoints versionados de Host AI Platform.

No introduce logica de negocio.
No modifica autoridad funcional del Core.

## 2. Endpoints cubiertos

- GET /api/v1/health
- GET /api/v1/version
- GET /api/v1/executive
- GET /api/v1/dashboard
- POST /api/v1/chat

## 3. Contrato de respuesta comun

Todas las respuestas JSON (exito o error) deben incluir:

- ok: boolean
- version: string
- api_version: string
- request_id: string
- modo_seguro: boolean
- datos_reales_modificados: boolean

### 3.1 Campos obligatorios

- ok
- version
- api_version
- request_id
- modo_seguro
- datos_reales_modificados

### 3.2 Campos opcionales de negocio

Dependen del endpoint:

- health
- version_info
- executive
- dashboard
- chat
- contexto
- respuesta

### 3.3 Estructura de error HTTP

En errores, ademas de los campos comunes, se devuelve:

- error: {
  - status: int
  - code: string
  - message: string
}

Restricciones:

- No devolver tracebacks.
- No devolver rutas internas.
- No devolver detalles tecnicos sensibles.

## 4. Codigos de estado

- 200: respuesta valida (incluye respuestas funcionales de endpoint).
- 404: endpoint no encontrado.
- 500: error interno de infraestructura API.

Nota:
Los errores de dominio del flujo delegado pueden representarse con ok=false y status HTTP 200 si asi lo define el endpoint existente; el contrato comun se mantiene igual.

## 5. Request ID

- request_id se genera por peticion si no llega informado.
- Debe ser trazable y unico por llamada.
- Debe aparecer en todas las respuestas.

## 6. Versionado

- version: version del contrato publico de respuesta (v1.0).
- api_version: version tecnica de la API (v1.0).

## 7. Modo seguro

- modo_seguro: true en los endpoints actuales.
- datos_reales_modificados: false en los endpoints actuales certificados.

## 8. Ejemplos

### 8.1 Exito generico

{
  "ok": true,
  "version": "1.0",
  "api_version": "1.0",
  "request_id": "...",
  "modo_seguro": true,
  "datos_reales_modificados": false,
  "executive": { }
}

### 8.2 Error generico

{
  "ok": false,
  "version": "1.0",
  "api_version": "1.0",
  "request_id": "...",
  "modo_seguro": true,
  "datos_reales_modificados": false,
  "error": {
    "status": 404,
    "code": "not_found",
    "message": "Endpoint no encontrado."
  }
}
