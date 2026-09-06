# Bootstrap de Host AI en un entorno nuevo

Estado: procedimiento canónico de aprovisionamiento local

Versión Python certificada: 3.13.14

Rama de referencia: `feature/compras-web`

## Requisitos

- Git.
- Python 3.13.x de 64 bits. La versión recomendada y certificada es 3.13.14.
- Node.js 24.x y npm 11.x. La combinación verificada es Node.js 24.18.0 con
  npm 11.16.0.

Host AI no requiere Poetry, uv ni un entorno virtual preexistente. El entorno se
crea dentro del clon y no debe habilitar `system-site-packages`.

## Instalación desde cero

Desde Windows PowerShell:

```powershell
git clone --branch feature/compras-web --single-branch https://github.com/ferrantorrescastillo-dot/Host-AI-Core.git host-ai
Set-Location host-ai

py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r API\requirements-dev.txt

Set-Location HOST_AI_WEB
npm ci
Set-Location ..
```

Para una instalación exclusivamente runtime puede usarse
`API\requirements-http.txt`. El fichero `API\requirements-dev.txt` incluye el
runtime y añade solamente el cliente HTTP y el runner necesarios para los tests.

No configure `PYTHONPATH`: los comandos se ejecutan desde la raíz del clon para
que Python resuelva los paquetes versionados del proyecto.

## Arranque

Terminal de backend, desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m uvicorn API.http_server:app --host 127.0.0.1 --port 8000
```

Terminal de frontend:

```powershell
Set-Location HOST_AI_WEB
$env:VITE_HOST_AI_API_BASE_URL = "http://127.0.0.1:8000"
npm run dev
```

Comprobación del backend:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

## Comprobaciones básicas

Desde la raíz, con el backend detenido para evitar colisiones de puertos:

```powershell
.\.venv\Scripts\python.exe -m compileall -q API CORE MODELOS MOTORES PIPELINES SERVICIOS TESTS
$pytestTemp = Join-Path ([System.IO.Path]::GetTempPath()) "host-ai-bootstrap-pytest"
.\.venv\Scripts\python.exe -m pytest -q --basetemp=$pytestTemp TESTS\test_fase1_importacion_certificacion.py

Set-Location HOST_AI_WEB
npm test -- --run
npm run typecheck
npm run build
```

La raíz temporal corta evita superar `MAX_PATH` en Windows cuando el clon está
dentro de una ruta profunda. No contiene datos de dominio y pytest la recrea para
cada ejecución.

Los E2E de Fase 1 levantan su propio runtime aislado. Para ejecutarlos con el
Python del entorno nuevo, active primero el entorno o anteponga `.venv\Scripts`
al `PATH` de esa terminal.

## Autoridad de dependencias

- Runtime: `API/requirements-http.txt`.
- Test/desarrollo: `API/requirements-dev.txt`.
- Frontend: `HOST_AI_WEB/package.json` y `HOST_AI_WEB/package-lock.json`.

Las dependencias se derivan de imports versionados. No se genera el manifiesto
mediante `pip freeze`, para no incorporar paquetes globales o históricos.

## Aislamiento y datos

- No reutilizar `.venv`, `site-packages`, `PYTHONPATH` ni runtimes de otro clon.
- No usar archivos de Descargas, documentos privados ni artefactos ignorados.
- Los tests backend instalan un guard que impide escrituras sobre `DATOS` real.
- Los E2E deben usar sus raíces aisladas bajo `.test-runs`.
- No confirmar propuestas ni ejecutar WRITE sobre datos reales durante bootstrap.
