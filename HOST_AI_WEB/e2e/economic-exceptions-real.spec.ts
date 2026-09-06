import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

const backendPort = Number(process.env.HOST_AI_E2E_BACKEND_PORT || 8061);
const supervisorPort = Number(process.env.HOST_AI_E2E_SUPERVISOR_PORT || 8062);
const runtimeName = process.env.HOST_AI_E2E_RUNTIME_NAME || "fase1-economic-exceptions-smoke";
const apiBase = `http://127.0.0.1:${backendPort}`;
const supervisorBase = `http://127.0.0.1:${supervisorPort}`;
const currentDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(currentDir, "../..");
const runtimeDir = path.join(projectRoot, ".test-runs", runtimeName);
const state = JSON.parse(readFileSync(path.join(runtimeDir, "e2e-state.json"), "utf-8"));

function hashFile(filename: string) {
  return createHash("sha256").update(readFileSync(filename)).digest("hex").toUpperCase();
}

function protectedHashes() {
  return Object.fromEntries(Object.keys(state.protected_hashes).map((filename) => [
    filename,
    hashFile(path.join(runtimeDir, "DATOS", "db", filename)),
  ]));
}

test("XLSX público autocontenido: precio externo provisional y revisión operativa agrupada persisten sin WRITE", async ({ browser, request }) => {
  const sourcePath = path.join(runtimeDir, state.source_file);
  expect(hashFile(sourcePath)).toBe(state.source_sha256);
  expect(protectedHashes()).toEqual(state.protected_hashes);

  const initialResponse = await request.get(
    `${apiBase}/api/v1/biblioteca/recetas/completado-ia/${state.batch_id}/estado`,
  );
  expect(initialResponse.ok()).toBe(true);
  const initial = await initialResponse.json();
  expect(initial).toMatchObject({
    import_id: state.import_id,
    batch_id: state.batch_id,
    datos_reales_modificados: false,
  });
  expect(["PROPUESTAS_LISTAS", "PROPUESTAS_LISTAS_CON_ERRORES", "PREVIEW"]).toContain(initial.estado);
  expect(initial.progreso).toMatchObject({ total: 52, analizadas: 52, propuestas: state.proposal_count });
  expect(initial.validacion_externa.campos).toMatchObject({
    utiles: state.safe_count, operativos_agrupables: state.grouped_count,
    requieren_revision: state.review_count,
  });
  expect(initial.validacion_externa.referencias_precio).toMatchObject({
    referencias_utiles: 3, referencias_consolidadas: 3, rechazadas: 0,
  });
  expect(initial.validacion_externa.referencias_precio.pendientes).toBeGreaterThanOrEqual(1);
  expect(initial.resumen_masivo).toMatchObject({
    production_ready_provisional: state.production_ready_provisional,
    production_ready_confirmed: 0,
    campos_operativos_agrupables: state.grouped_count,
    campos_criticos_individuales: state.critical_count,
  });
  const initialAgua = initial.resultados.find((item: any) => item.recipe_id === "REC601-000007");
  expect(initialAgua.proyeccion_provisional.escandallo).toMatchObject({
    estado_coste: "PARCIAL", coste_total_parcial: 11.63,
    precios_referencia: 3, completitud_coste_porcentaje: 75,
  });
  expect(initialAgua.proyeccion_provisional.escandallo.lineas).toHaveLength(4);
  expect(initial.referencias_precio_externas).toHaveLength(3);
  expect(initial.referencias_precio_externas.every((reference: any) =>
    reference.autoridad === "REFERENCIA_NO_REAL"
    && reference.origen === "REFERENCIA_EXTERNA"
    && reference.estado_revision !== "CONFIRMADO",
  )).toBe(true);
  if (initial.preview) {
    const initialPreviewAgua = initial.preview.items.find((item: any) => item.recipe_id === "REC601-000007");
    expect(initialPreviewAgua.proyeccion_provisional.escandallo).toMatchObject({
      estado_coste: "PARCIAL", coste_total_parcial: 11.63,
      precios_referencia: 3, completitud_coste_porcentaje: 75,
    });
    expect(initialPreviewAgua.cambios).not.toHaveProperty("ingredientes_estructurados");
  }

  const context = await browser.newContext();
  expect(await context.storageState()).toEqual({ cookies: [], origins: [] });
  const page = await context.newPage();
  await page.goto("/biblioteca/importaciones");
  const cta = page.getByRole("button", { name: "Revisar propuestas externas · 52 recetas" });
  await expect(cta).toBeVisible({ timeout: 30_000 });
  await cta.click();
  const recoveredPreview = page.getByRole("region", { name: "Preview consolidado" });
  if (await recoveredPreview.isVisible()) {
    await recoveredPreview.getByRole("button", { name: "Volver a propuestas" }).click();
  }

  await expect(page.getByText(`Archivo procesado: ${state.source_file}`, { exact: false })).toBeVisible();
  const fieldSummary = page.getByText(`Campos seguros: ${state.safe_count}`, { exact: false });
  await expect(fieldSummary).toContainText(`Operativos agrupables: ${state.grouped_count}`);
  await expect(fieldSummary).toContainText(`Críticos individuales: ${state.review_count}`);
  await expect(page.getByText("Referencias externas:", { exact: false })).toContainText("3 identidades reutilizables");
  const summary = page.getByRole("region", { name: "Resumen masivo production-ready" });
  await expect(summary).toContainText(`Production-ready provisional${state.production_ready_provisional}`);

  const reviewSection = page.getByRole("region", { name: "Revisar propuestas externas de recetas" });
  const recipeSearch = page.getByLabel("Buscar receta por nombre o ID");
  const recipeCards = reviewSection.locator('[data-recipe-view="review"]');
  await expect(recipeCards).toHaveCount(52);
  await expect(recipeCards.filter({ hasText: "Ensaladilla" })).toHaveCount(1);
  await expect(page.getByText("Mostrando 52 de 52 recetas.")).toBeVisible();
  await recipeSearch.fill("agua");
  await expect(recipeSearch).toHaveValue("agua");
  await expect(recipeCards).toHaveCount(1);
  await expect(recipeCards.first().locator(":scope > summary")).toContainText("Agua de jamaica");
  await expect(recipeCards.first()).toHaveAttribute("data-recipe-id", "REC601-000007");
  for (const excluded of ["Ensaladilla", "Crema de calabaza", "Gazpacho de tomate", "Salmorejo cordobés", "Salsa romesco", "Paella de alcachofas"]) {
    await expect(recipeCards.filter({ hasText: excluded })).toHaveCount(0);
  }
  await expect(page.getByText("Mostrando 1 de 52 recetas.")).toBeVisible();
  const agua = recipeCards.first();
  await agua.locator(":scope > summary").click();
  const projection = agua.getByRole("region", { name: "Ficha técnica y escandallo provisionales" });
  await expect(projection).toContainText("Estado: PARCIAL");
  await expect(projection).toContainText("3 con precio de referencia");
  await expect(projection).toContainText("Herbolínea");
  await expect(projection).toContainText("Alcampo");
  await expect(projection).toContainText("11.63");
  await page.getByRole("button", { name: "Limpiar" }).click();
  await expect(recipeCards).toHaveCount(52);
  await expect(page.getByText("Mostrando 52 de 52 recetas.")).toBeVisible();

  const groupedAction = page.getByRole("button", {
    name: `Revisar y seleccionar operativas provisionales · ${state.grouped_count}`,
  });
  if (await groupedAction.isVisible()) await groupedAction.click();
  else await page.getByRole("button", { name: "Volver a vista previa" }).click();
  const preview = page.getByRole("region", { name: "Preview consolidado" });
  await expect(preview).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText(new RegExp(`${state.grouped_count} operativas agrupadas`))).toBeVisible();
  await expect(preview).toContainText("Revisión agrupada");
  await expect(preview).not.toContainText("ingredientes_estructurados");
  await expect(page.getByRole("button", { name: "Confirmar cambios" })).toBeVisible();
  const previewCards = preview.locator('[data-recipe-view="preview"]');
  await expect(previewCards).toHaveCount(52);
  await expect(previewCards.filter({ hasText: "Ensaladilla" })).toHaveCount(1);
  await recipeSearch.fill("REC601-000007");
  await expect(recipeSearch).toHaveValue("REC601-000007");
  await expect(previewCards).toHaveCount(1);
  await expect(previewCards.first()).toHaveAttribute("data-recipe-id", "REC601-000007");
  await expect(preview.getByRole("heading", { name: "Agua de jamaica" })).toBeVisible();
  await expect(preview.getByText("REC601-000007", { exact: true })).toBeVisible();
  for (const excluded of ["Ensaladilla", "Crema de calabaza", "Gazpacho de tomate", "Salmorejo cordobés", "Salsa romesco", "Paella de alcachofas"]) {
    await expect(previewCards.filter({ hasText: excluded })).toHaveCount(0);
  }
  await expect(page.getByText("Mostrando 1 de 52 recetas.")).toBeVisible();
  const previewProjection = preview.getByRole("region", { name: "Ficha técnica y escandallo provisionales" });
  await expect(previewProjection).toContainText("Estado: PARCIAL");
  await expect(previewProjection).toContainText("3 con precio de referencia");
  await expect(previewProjection).toContainText("11.63");
  await expect(previewProjection).toContainText("Cobertura: 75%");
  await expect(previewProjection).toContainText("Ingredientes pendientes de coste: Agua");
  await expect(previewProjection).toContainText("Herbolínea");
  await expect(previewProjection).not.toContainText("Estado: SIN_COSTE");
  await expect(previewProjection).not.toContainText("No calculable");
  await page.getByRole("button", { name: "Limpiar" }).click();
  await expect(previewCards).toHaveCount(52);

  const selected = await (await request.get(
    `${apiBase}/api/v1/biblioteca/recetas/completado-ia/${state.batch_id}/estado`,
  )).json();
  expect(Object.values(selected.selecciones_agrupadas).reduce(
    (total: number, fields: any) => total + Object.keys(fields).length, 0,
  )).toBe(state.grouped_count);
  expect(selected.selecciones_individuales).toEqual({});
  expect(selected.preview.cambios_a_aplicar).toBe(state.grouped_count);
  expect(selected.preview.items.flatMap((item: any) => item.detalle_cambios).every(
    (change: any) => change.clasificacion === "REVISION_AGRUPADA",
  )).toBe(true);
  expect(selected.estado).toBe("PREVIEW");
  expect(selected.datos_reales_modificados).toBe(false);

  await page.reload();
  const refreshedCta = page.getByRole("button", { name: "Revisar propuestas externas · 52 recetas" });
  await expect(refreshedCta).toBeVisible({ timeout: 30_000 });
  await refreshedCta.click();
  const refreshedPreview = page.getByRole("region", { name: "Preview consolidado" });
  await expect(refreshedPreview).toBeVisible({ timeout: 30_000 });
  await page.getByLabel("Buscar receta por nombre o ID").fill("agua");
  await expect(page.getByText("Mostrando 1 de 52 recetas.")).toBeVisible();
  const refreshedProjection = refreshedPreview.getByRole("region", { name: "Ficha técnica y escandallo provisionales" });
  await expect(refreshedProjection).toContainText("Estado: PARCIAL");
  await expect(refreshedProjection).toContainText("11.63");
  await expect(refreshedProjection).toContainText("3 con precio de referencia");
  await expect(refreshedProjection).not.toContainText("SIN_COSTE");
  await expect(refreshedProjection).not.toContainText("No calculable");

  await context.close();

  expect((await request.post(`${supervisorBase}/restart-frontend`)).ok()).toBe(true);
  const frontendRestartContext = await browser.newContext();
  expect(await frontendRestartContext.storageState()).toEqual({ cookies: [], origins: [] });
  const frontendRestartPage = await frontendRestartContext.newPage();
  await frontendRestartPage.goto("/biblioteca/importaciones");
  await expect(frontendRestartPage.getByRole("button", {
    name: "Revisar propuestas externas · 52 recetas",
  })).toBeVisible({ timeout: 30_000 });
  await frontendRestartContext.close();

  expect((await request.post(`${supervisorBase}/restart-backend`)).ok()).toBe(true);
  const afterBackendRestart = await (await request.get(
    `${apiBase}/api/v1/biblioteca/recetas/completado-ia/${state.batch_id}/estado`,
  )).json();
  expect(afterBackendRestart.preview.cambios_a_aplicar).toBe(state.grouped_count);
  expect(afterBackendRestart.datos_reales_modificados).toBe(false);

  expect((await request.post(`${supervisorBase}/restart-all`)).ok()).toBe(true);
  const afterRestart = await (await request.get(
    `${apiBase}/api/v1/biblioteca/recetas/completado-ia/${state.batch_id}/estado`,
  )).json();
  expect(afterRestart.preview.cambios_a_aplicar).toBe(state.grouped_count);
  expect(afterRestart.validacion_externa.referencias_precio.referencias_consolidadas).toBe(3);
  expect(afterRestart.estado).toBe("PREVIEW");
  expect(afterRestart.datos_reales_modificados).toBe(false);
  const restartedPreviewAgua = afterRestart.preview.items.find((item: any) => item.recipe_id === "REC601-000007");
  expect(restartedPreviewAgua.proyeccion_provisional.escandallo).toMatchObject({
    estado_coste: "PARCIAL", coste_total_parcial: 11.63,
    precios_referencia: 3, completitud_coste_porcentaje: 75,
  });
  expect(restartedPreviewAgua.cambios).not.toHaveProperty("ingredientes_estructurados");
  expect(protectedHashes()).toEqual(state.protected_hashes);

  const finalContext = await browser.newContext();
  expect(await finalContext.storageState()).toEqual({ cookies: [], origins: [] });
  const finalPage = await finalContext.newPage();
  await finalPage.goto("/biblioteca/importaciones");
  const finalCta = finalPage.getByRole("button", { name: "Revisar propuestas externas · 52 recetas" });
  await expect(finalCta).toBeVisible({ timeout: 30_000 });
  await finalCta.click();
  const finalPreview = finalPage.getByRole("region", { name: "Preview consolidado" });
  await expect(finalPreview).toBeVisible({ timeout: 30_000 });
  const finalCards = finalPreview.locator('[data-recipe-view="preview"]');
  await expect(finalCards).toHaveCount(52);
  await expect(finalCards.filter({ hasText: "Ensaladilla" })).toHaveCount(1);
  const finalSearch = finalPage.getByLabel("Buscar receta por nombre o ID");
  await finalSearch.fill("agua");
  await expect(finalSearch).toHaveValue("agua");
  await expect(finalPage.getByText("Mostrando 1 de 52 recetas.")).toBeVisible();
  await expect(finalCards).toHaveCount(1);
  await expect(finalCards.first()).toHaveAttribute("data-recipe-id", "REC601-000007");
  await expect(finalCards.first()).toContainText("Agua de jamaica");
  await expect(finalCards.first()).toContainText("REC601-000007");
  await expect(finalCards.first().getByRole("region", { name: "Ficha técnica y escandallo provisionales" })).toBeVisible();
  const finalProjection = finalCards.first().getByRole("region", { name: "Ficha técnica y escandallo provisionales" });
  await expect(finalProjection).toContainText("Estado: PARCIAL");
  await expect(finalProjection).toContainText("11.63");
  await expect(finalProjection).toContainText("3 con precio de referencia");
  await expect(finalProjection).toContainText("Ingredientes pendientes de coste: Agua");
  await expect(finalProjection).not.toContainText("SIN_COSTE");
  await expect(finalProjection).not.toContainText("No calculable");
  for (const excluded of ["Ensaladilla", "Crema de calabaza", "Gazpacho de tomate", "Salmorejo cordobés", "Salsa romesco", "Paella de alcachofas"]) {
    await expect(finalCards.filter({ hasText: excluded })).toHaveCount(0);
  }
  await finalPage.getByRole("button", { name: "Limpiar" }).click();
  await expect(finalCards).toHaveCount(52);
  await expect(finalPage.getByText("Mostrando 52 de 52 recetas.")).toBeVisible();
  expect(protectedHashes()).toEqual(state.protected_hashes);
  await finalContext.close();
});
