import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

const backendPort = Number(process.env.HOST_AI_E2E_BACKEND_PORT || 8041);
const supervisorPort = Number(process.env.HOST_AI_E2E_SUPERVISOR_PORT || 8042);
const runtimeName = process.env.HOST_AI_E2E_RUNTIME_NAME || "fase1-mass-smoke";
const apiBase = `http://127.0.0.1:${backendPort}`;
const supervisorBase = `http://127.0.0.1:${supervisorPort}`;
const currentDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(currentDir, "../..");
const stateFile = path.join(projectRoot, ".test-runs", runtimeName, "e2e-state.json");

test("smoke limpio de solo lectura: nombres humanos, Agua de jamaica y persistencia", async ({ browser, request }) => {
  const prepared = JSON.parse(readFileSync(stateFile, "utf-8"));
  const importId = String(prepared.import_id);
  const batchId = String(prepared.batch_id);
  expect(prepared.recipe_count).toBe(52);
  expect(prepared.agua_production_ready_provisional).toBe(true);
  const expectedNames = prepared.recipe_names as Record<string, string>;
  expect(Object.keys(expectedNames)).toHaveLength(52);
  expect(Object.values(expectedNames).every((name) => name.length > 0 && !/^Receta\s+\d+$/.test(name))).toBe(true);
  expect(prepared.name_audit).toEqual({
    canonical_matches_xlsx: true, xlsx_matches_batch: true, human_names: 52,
  });

  const initial = await (await request.get(
    `${apiBase}/api/v1/biblioteca/recetas/completado-ia/${batchId}/estado`,
  )).json();
  expect(initial.import_id).toBe(importId);
  expect(initial.estado).toBe("PROPUESTAS_LISTAS_CON_ERRORES");
  expect(initial.preview).toBeNull();
  expect(initial.datos_reales_modificados).toBe(false);
  expect(Object.fromEntries(initial.resultados.map((item: { recipe_id: string; nombre: string }) => [item.recipe_id, item.nombre]))).toEqual(expectedNames);

  const context = await browser.newContext();
  expect(await context.storageState()).toEqual({ cookies: [], origins: [] });
  const page = await context.newPage();
  await page.goto("/biblioteca/importaciones");
  const cta = page.getByRole("button", { name: "Revisar propuestas externas · 52 recetas" });
  await expect(cta).toBeVisible({ timeout: 30_000 });
  await cta.click();

  for (const [recipeId, name] of Object.entries(expectedNames)) {
    const cardSummary = page.locator("details > summary").filter({ hasText: `${name} ·` });
    await expect(cardSummary, `${recipeId} debe conservar ${name}`).toBeVisible();
  }

  const summary = page.getByRole("region", { name: "Resumen masivo production-ready" });
  await expect(summary).toContainText("Recetas procesadas52");
  await expect(summary).toContainText("Production-ready provisional49");
  await expect(summary).toContainText("Errores2");
  await expect(summary).toContainText("Imposibles de estimar1");

  const agua = page.locator("details").filter({ hasText: "Agua de jamaica" }).first();
  await agua.locator("summary").click();
  await expect(agua.getByRole("region", { name: "Completitud de receta" })).toContainText(
    "Production-ready provisional: Sí",
  );
  const projection = agua.getByRole("region", { name: "Ficha técnica y escandallo provisionales" });
  await expect(projection).toContainText("Ficha técnica provisional");
  await expect(projection).toContainText("Escandallo provisional");
  const regeneration = projection.locator("dt").filter({ hasText: /^Regeneración$/ }).locator("xpath=following-sibling::dd[1]");
  const defrost = projection.locator("dt").filter({ hasText: /^Tiempo de descongelación$/ }).locator("xpath=following-sibling::dd[1]");
  await expect(regeneration).toContainText("No aplica");
  await expect(defrost).toContainText("No aplica");
  await expect(regeneration).toContainText("IA_PROPUESTA · ARCHIVO_EXTERNO");
  await expect(regeneration).toContainText("REQUIERE_REVISION_HUMANA");
  await expect(projection).toContainText("PROVISIONAL");
  await expect(projection).toContainText("Coste total: 5.8");
  await expect(agua).toContainText("Flor de hibiscus");
  await expect(agua).toContainText("Limones");
  await expect(agua).toContainText("Azúcar");
  await expect(agua).toContainText("IA_PROPUESTA");
  await expect(agua).toContainText("NO_APLICA");

  await page.reload();
  await expect(cta).toBeVisible({ timeout: 30_000 });
  await cta.click();
  await expect(page.locator("details > summary").filter({ hasText: "Crema de calabaza ·" })).toBeVisible();
  await expect(page.locator("details > summary").filter({ hasText: "Gazpacho de tomate ·" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Resumen masivo production-ready" })).toContainText(
    "Production-ready provisional49",
  );
  const recovered = await (await request.get(
    `${apiBase}/api/v1/biblioteca/importaciones/${importId}`,
  )).json();
  expect(recovered.importacion.completado_recetas_activo.batch_id).toBe(batchId);
  expect(recovered.datos_reales_modificados).toBe(false);
  await context.close();

  expect((await request.post(`${supervisorBase}/restart-all`)).ok()).toBe(true);
  const afterRestart = await (await request.get(
    `${apiBase}/api/v1/biblioteca/recetas/completado-ia/${batchId}/estado`,
  )).json();
  expect(Object.fromEntries(afterRestart.resultados.map((item: { recipe_id: string; nombre: string }) => [item.recipe_id, item.nombre]))).toEqual(expectedNames);
  expect(afterRestart.datos_reales_modificados).toBe(false);
  const restartedContext = await browser.newContext();
  expect(await restartedContext.storageState()).toEqual({ cookies: [], origins: [] });
  const restartedPage = await restartedContext.newPage();
  await restartedPage.goto("/biblioteca/importaciones");
  await restartedPage.getByRole("button", { name: "Revisar propuestas externas · 52 recetas" }).click();
  await expect(restartedPage.locator("details > summary").filter({ hasText: "Crema de calabaza ·" })).toBeVisible();
  await expect(restartedPage.locator("details > summary").filter({ hasText: "Agua de jamaica ·" })).toBeVisible();
  await restartedContext.close();
});
