# HOST AI Platform API

Estado: HTTP operativo sobre fachada existente
Fecha: 2026-07-29

## Objetivo

Exponer por HTTP la fachada existente `HostAIPlatformAPI` sin mover logica de negocio al servidor.

## Framework usado

- FastAPI (servidor HTTP y tipado)
- Uvicorn (arranque ASGI)

## Dependencias Python

Host AI usa el sistema `requirements` ya existente:

- `API/requirements-http.txt`: runtime backend, importadores e integraciones.
- `API/requirements-dev.txt`: runtime más dependencias de test/desarrollo.

La versión certificada y el procedimiento completo para una máquina nueva están en
`DEVKIT/BOOTSTRAP_ENTORNO_NUEVO.md`.

Instalación de desarrollo en Windows PowerShell, desde la raíz del repositorio:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r API\requirements-dev.txt
```

## Punto de entrada HTTP

- `API/http_server.py`
- App ASGI exportada: `app`

## Comando exacto de arranque

Desde la raiz del repo:

```powershell
.\.venv\Scripts\python.exe -m uvicorn API.http_server:app --host 127.0.0.1 --port 8000
```

Host y puerto esperados:

- Host: `127.0.0.1`
- Puerto: `8000`

## Endpoints versionados expuestos

- GET `/api/v1/health`
- GET `/api/v1/version`
- GET `/api/v1/executive`
- GET `/api/v1/dashboard`
- POST `/api/v1/chat`

## URLs de comprobacion

- Health: `http://127.0.0.1:8000/api/v1/health`
- Version: `http://127.0.0.1:8000/api/v1/version`

PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health | ConvertTo-Json -Depth 10
```

## CORS

Por defecto solo se permite el origen local de Vite:

- `http://localhost:5173`

Variables de entorno:

- `HOST_AI_API_CORS_ALLOWED_ORIGINS` (lista separada por comas)
- `HOST_AI_API_ENV` (por defecto `development`)
- `HOST_AI_API_ALLOW_WILDCARD_CORS` (por defecto `false`)

Notas de seguridad:

- El wildcard `*` no se usa por defecto.
- Solo se habilita en desarrollo si se activa explicitamente `HOST_AI_API_ALLOW_WILDCARD_CORS=true`.

## Conexion con Vite (WEB)

Variable usada por la web:

- `VITE_HOST_AI_API_BASE_URL=http://127.0.0.1:8000`

Archivo ejemplo:

- `HOST_AI_WEB/.env.example`

## Ejemplo de peticion chat

```powershell
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/api/v1/chat -ContentType "application/json" -Body '{"mensaje":"hola","contexto":{}}' | ConvertTo-Json -Depth 10
```

## Limitaciones

- El servidor HTTP no contiene logica de negocio.
- Toda decision funcional sigue delegada en `API.router`, `API.facade` y servicios publicos certificados del Core.
- `datos_reales_modificados` se mantiene `false` en endpoints versionados actuales.
