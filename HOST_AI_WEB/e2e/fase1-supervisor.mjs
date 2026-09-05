import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

const currentDir = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(currentDir, "..");
const projectRoot = path.resolve(webRoot, "..");
const runtimeDir = process.env.HOST_AI_E2E_BASE_DIR || path.join(projectRoot, ".test-runs", "fase1-e2e");
const pythonScript = path.join(projectRoot, "TESTS", "fase1_e2e_server.py");
const statePath = path.join(runtimeDir, "e2e-state.json");
const frontendPort = Number(process.env.HOST_AI_E2E_FRONTEND_PORT || 5178);
const backendPort = Number(process.env.HOST_AI_E2E_BACKEND_PORT || 8011);
const supervisorPort = Number(process.env.HOST_AI_E2E_SUPERVISOR_PORT || 8012);
const childEnv = {
  ...process.env,
  HOST_AI_E2E_BASE_DIR: runtimeDir,
  HOST_AI_API_CORS_ALLOWED_ORIGINS: `http://127.0.0.1:${frontendPort}`,
};

let backend;
let frontend;
let stopping = false;

function prepare() {
  const result = spawnSync("python", [pythonScript, "--prepare-only"], {
    cwd: projectRoot,
    env: childEnv,
    stdio: "inherit",
  });
  if (result.status !== 0) throw new Error(`No se pudo preparar el runtime E2E (${result.status}).`);
}

function startChildren() {
  backend = spawn("python", [pythonScript, "--serve-only"], {
    cwd: projectRoot,
    env: childEnv,
    stdio: "inherit",
  });
  frontend = spawn("cmd.exe", ["/d", "/s", "/c", `npm.cmd run dev -- --host 127.0.0.1 --port ${frontendPort}`], {
    cwd: webRoot,
    env: { ...childEnv, VITE_HOST_AI_API_BASE_URL: `http://127.0.0.1:${backendPort}` },
    stdio: "inherit",
    windowsHide: true,
  });
}

function terminateTree(child) {
  return new Promise((resolve) => {
    if (!child?.pid || child.exitCode !== null) return resolve();
    const done = () => resolve();
    child.once("exit", done);
    if (process.platform === "win32") {
      const killer = spawn("taskkill", ["/pid", String(child.pid), "/T", "/F"], {
        stdio: "ignore",
        windowsHide: true,
      });
      killer.once("exit", () => setTimeout(done, 50));
    } else {
      child.kill("SIGTERM");
    }
  });
}

function reachable(url) {
  return new Promise((resolve) => {
    const request = http.get(url, (response) => {
      response.resume();
      resolve(Boolean(response.statusCode && response.statusCode < 500));
    });
    request.setTimeout(500, () => { request.destroy(); resolve(false); });
    request.on("error", () => resolve(false));
  });
}

async function waitUntilReady() {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    if (await reachable(`http://127.0.0.1:${backendPort}/api/v1/health`)
      && await reachable(`http://127.0.0.1:${frontendPort}/biblioteca/importaciones`)) return;
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error("Backend/frontend E2E no quedaron disponibles tras el reinicio.");
}

async function restartAll() {
  await Promise.all([terminateTree(frontend), terminateTree(backend)]);
  startChildren();
  await waitUntilReady();
}

async function shutdown() {
  if (stopping) return;
  stopping = true;
  server.close();
  await Promise.all([terminateTree(frontend), terminateTree(backend)]);
  process.exit(0);
}

if (process.env.HOST_AI_E2E_REUSE_PREPARED === "1") {
  if (!existsSync(statePath)) throw new Error(`No existe el runtime E2E preparado: ${statePath}`);
} else {
  prepare();
}
startChildren();

const server = http.createServer(async (request, response) => {
  if (request.method === "GET" && request.url === "/health") {
    const ready = await reachable(`http://127.0.0.1:${backendPort}/api/v1/health`)
      && await reachable(`http://127.0.0.1:${frontendPort}/biblioteca/importaciones`);
    response.writeHead(ready ? 200 : 503, { "Content-Type": "application/json" });
    response.end(JSON.stringify({ ok: ready }));
    return;
  }
  if (request.method === "POST" && request.url === "/restart-all") {
    try {
      await restartAll();
      response.writeHead(200, { "Content-Type": "application/json" });
      response.end(JSON.stringify({ ok: true }));
    } catch (error) {
      response.writeHead(500, { "Content-Type": "application/json" });
      response.end(JSON.stringify({ ok: false, error: String(error) }));
    }
    return;
  }
  response.writeHead(404);
  response.end();
});

server.listen(supervisorPort, "127.0.0.1");
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
