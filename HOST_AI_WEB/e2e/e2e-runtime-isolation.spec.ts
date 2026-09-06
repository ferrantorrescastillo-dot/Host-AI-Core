import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

const runtimeName = process.env.HOST_AI_E2E_RUNTIME_NAME || "fase1-contract-e2e";
const backendPort = Number(process.env.HOST_AI_E2E_BACKEND_PORT || 8041);
const humanBackendPort = Number(process.env.HOST_AI_HUMAN_BACKEND_PORT || 58421);
const currentDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(currentDir, "../..");
const runtimeDir = path.join(projectRoot, ".test-runs", runtimeName);
const humanRuntimeDir = path.join(projectRoot, ".test-runs", "fase1-mass-smoke");

function durableManifest(root: string): string {
  const files: string[] = [];
  function visit(directory: string) {
    for (const name of readdirSync(directory).sort()) {
      const absolute = path.join(directory, name);
      if (statSync(absolute).isDirectory()) visit(absolute);
      else files.push(absolute);
    }
  }
  visit(root);
  const digest = createHash("sha256");
  for (const filename of files) {
    digest.update(path.relative(root, filename).replaceAll("\\", "/"));
    digest.update("\0");
    digest.update(readFileSync(filename));
    digest.update("\n");
  }
  return digest.digest("hex");
}

test("una reimportación E2E no altera el runtime humano ni su batch activo", async ({ request }) => {
  expect(runtimeName).not.toBe("fase1-mass-smoke");
  const state = JSON.parse(readFileSync(path.join(runtimeDir, "e2e-state.json"), "utf-8"));
  const fixture = path.join(runtimeDir, "fixture-completado-externo.xlsx");
  const humanState = JSON.parse(readFileSync(path.join(humanRuntimeDir, "e2e-state.json"), "utf-8"));
  expect(existsSync(fixture)).toBe(true);
  const humanData = path.join(humanRuntimeDir, "DATOS");
  const manifestBefore = durableManifest(humanData);
  const humanBefore = await (await request.get(
    `http://127.0.0.1:${humanBackendPort}/api/v1/biblioteca/importaciones/${humanState.import_id}`,
  )).json();
  const humanBatchBefore = humanBefore.importacion.completado_recetas_activo?.batch_id;

  const isolatedResponse = await request.post(
    `http://127.0.0.1:${backendPort}/api/v1/biblioteca/recetas/completado-externo/importar`,
    { data: {
      filename: path.basename(fixture),
      contenido_base64: readFileSync(fixture).toString("base64"),
      recipe_ids: Object.keys(state.recipe_names),
      scope: "IMPORTACION",
      import_id: state.import_id,
      origen_propuesta: "CHATGPT",
    } },
  );
  expect(isolatedResponse.status()).toBe(200);
  const isolated = await isolatedResponse.json();
  expect(isolated.batch.import_id).toBe(state.import_id);
  expect(isolated.datos_reales_modificados).toBe(false);

  const humanAfter = await (await request.get(
    `http://127.0.0.1:${humanBackendPort}/api/v1/biblioteca/importaciones/${humanState.import_id}`,
  )).json();
  expect(humanAfter.importacion.completado_recetas_activo?.batch_id).toBe(humanBatchBefore);
  expect(humanAfter.datos_reales_modificados).toBe(false);
  expect(durableManifest(humanData)).toBe(manifestBefore);
});
