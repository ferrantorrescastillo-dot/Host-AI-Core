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

### 3.4 Compras en dashboard

`GET /api/v1/dashboard` expone el resumen de Compras en
`dashboard.modulos.compras`:

- `estado`: estado normalizado del modulo.
- `total`: numero de necesidades pendientes.
- `items`: necesidades pendientes.
- `necesidades_pendientes`: alias numerico de `total`.
- `propuestas_pendientes`: numero de propuestas pendientes.
- `propuestas`: propuestas de compra pendientes.
- `total_propuestas`: numero de propuestas pendientes.
- `proveedores`: proveedores activos.
- `total_proveedores`: numero de proveedores activos.
- `historial`: compras registradas, ordenadas por el servicio de Compras.
- `total_historial`: numero de compras registradas.
- `mensaje`: detalle opcional cuando el modulo no esta disponible.

Las colecciones se devuelven vacias cuando no hay datos. Si falla la lectura
de Compras, el agregador conserva el contrato general del dashboard y marca
el modulo con `estado=error_parcial`.

### 3.5 Eventos en dashboard

`GET /api/v1/dashboard` expone el resumen de Eventos en
`dashboard.modulos.eventos`:

- `estado`: estado normalizado del modulo.
- `total`: numero de eventos activos o proximos.
- `items`: eventos ordenados por proximidad.
- `eventos_activos`: alias numerico de `total`.
- `total_servicios`: servicios asociados a los eventos mostrados.
- `total_avisos`: avisos operativos detectados por el motor de Eventos.
- `resumen`: totales de eventos, pax, servicios y avisos.

Cada elemento de `items` conserva `id`, `nombre`, `fecha`, `pax`, `estado`,
`dias` y `servicios`, y puede incluir `avisos`, `riesgos` y
`estado_operativo`. Los avisos proceden de `MotorEventos.resumen_ejecutivo`;
la fachada no recalcula reglas de negocio.

### 3.6 Produccion en dashboard

`GET /api/v1/dashboard` expone el resumen operativo de Produccion en
`dashboard.modulos.produccion`, construido por el agregador de lectura a
partir de `MotorProduccionReal`:

- `estado`, `total` e `items`: contrato base compatible del modulo.
- `planes_activos`: alias numerico de `total`.
- `total_tareas`, `tareas_pendientes`, `tareas_en_curso`,
  `tareas_bloqueadas` y `tareas_pausadas`: contadores procedentes del
  resumen de ejecucion del motor.
- `total_alertas`: avisos del plan y alertas operativas del motor.
- `resumen`: los mismos totales agrupados para consumidores de interfaz.

Cada plan de `items` conserva identificacion, evento, fecha, pax,
responsable, estado, duracion y porcentaje completado. Tambien incluye sus
tareas con estado, prioridad, cantidad, unidad, bloqueo, retraso, progreso e
incidencias. Solo se publican planes con tareas no finalizadas. La lectura no
modifica datos reales y no introduce reglas de produccion en la fachada HTTP.

### 3.7 Stock en dashboard

`GET /api/v1/dashboard` expone el estado operativo de Stock en
`dashboard.modulos.stock`, construido por `HostAIHomeReadService` mediante
las operaciones de lectura existentes de `MotorStock`.

- `estado`, `total` e `items`: contrato compatible de alertas de Stock.
- `existencias` y `total_existencias`: articulos agrupados y cantidades
  actuales devueltos por `stock_actual()`.
- `lotes` y `total_lotes`: lotes positivos ordenados por el motor.
- `movimientos` y `total_movimientos`: historial ordenado por el motor.
- `alertas` y `total_alertas`: alias explicito de las alertas del contrato
  base.
- `estado_operativo`: estado calculado por `diagnosticar_stock()`.
- `caducidades` y `total_caducidades`: alertas de caducidad ya calculadas
  por el motor.
- `resumen`: articulos, lotes, movimientos, alertas, stock bajo minimo,
  caducidades y valor total procedentes de `resumen_operativo()`.

El agregador no calcula disponibilidad, minimos ni fechas de caducidad. No
modifica datos reales y no accede directamente al almacenamiento.

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
