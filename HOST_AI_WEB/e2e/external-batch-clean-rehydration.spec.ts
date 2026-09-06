import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const backendPort = Number(process.env.HOST_AI_E2E_BACKEND_PORT || 8031);
const runtimeName = process.env.HOST_AI_E2E_RUNTIME_NAME || "fase1-e2e";
const apiBase = `http://127.0.0.1:${backendPort}`;
const currentDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(currentDir, "../..");
const stateFile = path.join(projectRoot, ".test-runs", runtimeName, "e2e-state.json");

test("rehidrata el batch externo persistido en Chrome limpio y después de F5", async ({ browser, request }) => {
  const prepared = JSON.parse(readFileSync(stateFile, "utf-8"));
  const expectedImportId = String(prepared.import_id);
  const expectedBatchId = String(prepared.batch_id);
  const expectedRecipes = Number(prepared.recipe_count);
  const expectedProposals = Number(prepared.proposal_count);

  const listed = await (await request.get(`${apiBase}/api/v1/biblioteca/importaciones`)).json();
  expect(listed.importaciones.some((item: { importacion_id: string }) => item.importacion_id === expectedImportId)).toBe(true);
  const detail = await (await request.get(`${apiBase}/api/v1/biblioteca/importaciones/${expectedImportId}`)).json();
  expect(detail.importacion.completado_recetas_activo.batch_id).toBe(expectedBatchId);
  expect(detail.importacion.completado_recetas_activo.estado).toMatch(/^PROPUESTAS_LISTAS/);
  expect(detail.importacion.completado_recetas_activo.progreso).toMatchObject({ total: expectedRecipes, propuestas: expectedProposals });
  const batch = await (await request.get(`${apiBase}/api/v1/biblioteca/recetas/completado-ia/${expectedBatchId}/estado`)).json();
  expect(batch).toMatchObject({
    batch_id: expectedBatchId, import_id: expectedImportId,
    datos_reales_modificados: false, progreso: { total: expectedRecipes, propuestas: expectedProposals },
  });
  expect(batch.estado).toMatch(/^PROPUESTAS_LISTAS/);

  const previousBrowserSession = await browser.newContext();
  await previousBrowserSession.newPage();
  await previousBrowserSession.close();

  const cleanContext = await browser.newContext();
  expect(await cleanContext.storageState()).toEqual({ cookies: [], origins: [] });
  let externalImports = 0;
  cleanContext.on("request", (browserRequest) => {
    if (browserRequest.url().endsWith("/completado-externo/importar")) externalImports += 1;
  });
  const page = await cleanContext.newPage();
  await page.goto("/biblioteca/importaciones");
  let cta = page.getByRole("button", { name: `Revisar propuestas externas · ${expectedRecipes} recetas` });
  await expect(cta).toBeVisible({ timeout: 30_000 });
  await cta.click();
  await expect(page.getByRole("region", { name: "Revisar propuestas externas de recetas" })).toContainText(`Propuestas generadas: ${expectedProposals}`);

  await page.reload();
  cta = page.getByRole("button", { name: `Revisar propuestas externas · ${expectedRecipes} recetas` });
  await expect(cta).toBeVisible({ timeout: 30_000 });
  await cta.click();
  await expect(page.getByRole("region", { name: "Revisar propuestas externas de recetas" })).toContainText(`Propuestas generadas: ${expectedProposals}`);
  const detailAfterReload = await (await request.get(`${apiBase}/api/v1/biblioteca/importaciones/${expectedImportId}`)).json();
  expect(detailAfterReload.importacion.completado_recetas_activo.batch_id).toBe(expectedBatchId);
  expect(externalImports).toBe(0);
  await cleanContext.close();
});
