import { createHash } from "node:crypto";
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
const realGptHash = "0624F4C00FF2560CB5BF411A5F4E170A33EAEFC69475311BB0BA641DAC81E22C";

test("smoke limpio de solo lectura: XLSX GPT real, Agua de jamaica y persistencia", async ({ browser, request }) => {
  const prepared = JSON.parse(readFileSync(stateFile, "utf-8"));
  const importId = String(prepared.import_id);
  const batchId = String(prepared.batch_id);
  const sourcePath = process.env.HOST_AI_REAL_GPT_XLSX || path.join(
    process.env.USERPROFILE || "", "Downloads", String(prepared.source_file),
  );
  expect(createHash("sha256").update(readFileSync(sourcePath)).digest("hex").toUpperCase()).toBe(realGptHash);
  expect(prepared.real_gpt_sha256).toBe(realGptHash);
  expect(importId).toBe("IMPWEB-6F402EBB0868");
  expect(prepared.recipe_count).toBe(52);
  expect(prepared.proposal_count).toBe(1736);
  expect(prepared.rejected_count).toBe(136);
  expect(prepared.agua_production_ready_provisional).toBe(true);
  expect(prepared.agua_production_ready_confirmed).toBe(false);
  const expectedNames = prepared.recipe_names as Record<string, string>;
  expect(Object.keys(expectedNames)).toHaveLength(52);
  expect(Object.values(expectedNames).every((name) => name.length > 0 && !/^Receta\s+\d+$/.test(name))).toBe(true);
  expect(prepared.name_audit).toEqual({
    canonical_matches_xlsx: true, xlsx_matches_batch: true, human_names: 52,
  });

  const initialResponse = await request.get(
    `${apiBase}/api/v1/biblioteca/recetas/completado-ia/${batchId}/estado`,
  );
  expect(initialResponse.ok()).toBe(true);
  const initial = await initialResponse.json();
  expect(initial.import_id).toBe(importId);
  expect(initial.estado).toBe("PROPUESTAS_LISTAS_CON_ERRORES");
  expect(initial.preview).toBeNull();
  expect(initial.datos_reales_modificados).toBe(false);
  expect(initial.progreso).toMatchObject({ total: 52, analizadas: 52, exitosas: 52, fallidas: 0, propuestas: 1736 });
  expect(initial.validacion_externa.campos).toMatchObject({
    recibidos: 1872, utiles: 156, requieren_revision: 1580, rechazados: 136, bloqueados_criticos: 0,
  });
  expect(initial.archivo_externo).toMatchObject({
    nombre: prepared.source_file, tamano: 60029, sha256: realGptHash.toLowerCase(),
  });
  expect(Object.fromEntries(initial.resultados.map((item: { recipe_id: string; nombre: string }) => [item.recipe_id, item.nombre]))).toEqual(expectedNames);

  const context = await browser.newContext();
  expect(await context.storageState()).toEqual({ cookies: [], origins: [] });
  const page = await context.newPage();
  await page.goto("/biblioteca/importaciones");
  const cta = page.getByRole("button", { name: "Revisar propuestas externas · 52 recetas" });
  await expect(cta).toBeVisible({ timeout: 30_000 });
  await cta.click();

  await expect(page.getByText(`Archivo procesado: ${prepared.source_file}`, { exact: false })).toBeVisible();
  await expect(page.getByText("SHA-256 0624f4c00ff2…", { exact: false })).toBeVisible();
  await expect(page.getByText("Campos utilizables: 156", { exact: false })).toBeVisible();
  await expect(page.getByText("Campos críticos para revisión: 1580", { exact: false })).toBeVisible();
  await expect(page.getByText("Rechazados: 136", { exact: false })).toBeVisible();

  for (const [recipeId, name] of Object.entries(expectedNames)) {
    const cardSummary = page.locator("details > summary").filter({ hasText: `${name} ·` });
    await expect(cardSummary, `${recipeId} debe conservar ${name}`).toBeVisible();
  }

  const summary = page.getByRole("region", { name: "Resumen masivo production-ready" });
  await expect(summary).toContainText("Recetas procesadas52");
  await expect(summary).toContainText("Production-ready provisional1");
  await expect(summary).toContainText("Production-ready confirmado0");
  await expect(summary).toContainText("Errores13");
  await expect(summary).toContainText("Imposibles de estimar0");
  await expect(summary).toContainText("Con NO_APLICA34");

  const agua = page.locator("details").filter({ hasText: "Agua de jamaica" }).first();
  await agua.locator(":scope > summary").click();
  await expect(agua.getByRole("region", { name: "Completitud de receta" })).toContainText(
    "Production-ready provisional: Sí",
  );
  await expect(agua.getByRole("region", { name: "Completitud de receta" })).toContainText(
    "Production-ready confirmado: No",
  );
  await expect(agua).toContainText("Infusión fría de flor de jamaica, limón y azúcar para servicio.");
  await expect(agua).toContainText("Infusionar la flor de hibiscus en agua caliente");
  await expect(agua).toContainText("Flor de hibiscus");
  await expect(agua).toContainText("Limones");
  await expect(agua).toContainText("Azúcar");
  await expect(agua).toContainText("Agua");
  await expect(agua).toContainText("CANDIDATO_NUEVO");
  await expect(agua).not.toContainText("Texto culinario provisional");
  await expect(agua).not.toContainText("Proveedor fixture");
  await expect(agua).not.toContainText("PUBLIC-");

  const projection = agua.getByRole("region", { name: "Ficha técnica y escandallo provisionales" });
  await expect(projection).toContainText("Ficha técnica provisional");
  await expect(projection).toContainText("Escandallo provisional");
  const regeneration = projection.locator("dt").filter({ hasText: /^Regeneración$/ }).locator("xpath=following-sibling::dd[1]");
  const defrost = projection.locator("dt").filter({ hasText: /^Tiempo de descongelación$/ }).locator("xpath=following-sibling::dd[1]");
  await expect(regeneration).toContainText("No aplica");
  await expect(defrost).toContainText("No aplica");
  await expect(regeneration).toContainText("IA_PROPUESTA");
  await expect(regeneration).toContainText("Nombre de la receta y contexto exportado por Host AI");
  await expect(regeneration).toContainText("REQUIERE_REVISION_HUMANA");
  await expect(projection).toContainText("SIN_COSTE");
  await expect(projection).toContainText("Coste total: No calculable");
  await expect(projection).toContainText("Coste por ración: No calculable");
  await expect(projection).toContainText("0 con precio de referencia");

  await page.reload();
  await expect(cta).toBeVisible({ timeout: 30_000 });
  await cta.click();
  await expect(page.getByText(`Archivo procesado: ${prepared.source_file}`, { exact: false })).toBeVisible();
  await expect(page.locator("details > summary").filter({ hasText: "Agua de jamaica ·" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Resumen masivo production-ready" })).toContainText(
    "Production-ready provisional1",
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
  expect(afterRestart.archivo_externo.sha256).toBe(realGptHash.toLowerCase());
  expect(afterRestart.preview).toBeNull();
  expect(Object.fromEntries(afterRestart.resultados.map((item: { recipe_id: string; nombre: string }) => [item.recipe_id, item.nombre]))).toEqual(expectedNames);
  expect(afterRestart.datos_reales_modificados).toBe(false);
  const restartedContext = await browser.newContext();
  expect(await restartedContext.storageState()).toEqual({ cookies: [], origins: [] });
  const restartedPage = await restartedContext.newPage();
  await restartedPage.goto("/biblioteca/importaciones");
  await restartedPage.getByRole("button", { name: "Revisar propuestas externas · 52 recetas" }).click();
  await expect(restartedPage.getByText(`Archivo procesado: ${prepared.source_file}`, { exact: false })).toBeVisible();
  await expect(restartedPage.locator("details > summary").filter({ hasText: "Agua de jamaica ·" })).toBeVisible();
  await restartedContext.close();
});
