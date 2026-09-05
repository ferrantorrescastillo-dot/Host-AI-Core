import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "@playwright/test";

const currentDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(currentDir, "..");
const runtimeName = process.env.HOST_AI_E2E_RUNTIME_NAME || "fase1-e2e";
const runtimeDir = path.join(projectRoot, ".test-runs", runtimeName);
const frontendPort = Number(process.env.HOST_AI_E2E_FRONTEND_PORT || 5178);
const backendPort = Number(process.env.HOST_AI_E2E_BACKEND_PORT || 8011);
const supervisorPort = Number(process.env.HOST_AI_E2E_SUPERVISOR_PORT || 8012);
const reuseExistingServer = process.env.HOST_AI_E2E_REUSE_EXISTING_SERVER === "1";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 120_000,
  reporter: "line",
  outputDir: path.join(projectRoot, ".test-runs", "fase1-playwright-output"),
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
    channel: "chrome",
    headless: true,
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "node e2e/fase1-supervisor.mjs",
      url: `http://127.0.0.1:${supervisorPort}/health`,
      timeout: 120_000,
      reuseExistingServer,
      env: {
        HOST_AI_E2E_BASE_DIR: runtimeDir,
        HOST_AI_E2E_FRONTEND_PORT: String(frontendPort),
        HOST_AI_E2E_BACKEND_PORT: String(backendPort),
        HOST_AI_E2E_SUPERVISOR_PORT: String(supervisorPort),
      },
    },
  ],
});
