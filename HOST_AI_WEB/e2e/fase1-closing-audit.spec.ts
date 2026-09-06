import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

test.setTimeout(360_000);

const backendPort = Number(process.env.HOST_AI_E2E_BACKEND_PORT || 8031);
const supervisorPort = Number(process.env.HOST_AI_E2E_SUPERVISOR_PORT || 8032);
const runtimeName = process.env.HOST_AI_E2E_RUNTIME_NAME || "fase1-closing-e2e";
const apiBase = `http://127.0.0.1:${backendPort}`;
const supervisorBase = `http://127.0.0.1:${supervisorPort}`;
const currentDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(currentDir, "../..");
const runtimeDir = path.join(projectRoot, ".test-runs", runtimeName);
const stateFile = path.join(runtimeDir, "e2e-state.json");
const recipeStore = path.join(runtimeDir, "DATOS", "db", "biblioteca_recetas_601.json");
const articleStore = path.join(runtimeDir, "DATOS", "db", "articulos.json");
const referenceAudit = path.join(runtimeDir, "DATOS", "auditoria", "precios_referencia_web.jsonl");

function sha256(filename: string): string {
  return createHash("sha256").update(readFileSync(filename)).digest("hex");
}

function articles() {
  return JSON.parse(readFileSync(articleStore, "utf-8")) as Array<Record<string, unknown>>;
}

test("Fase 1 completa Boronat: análisis, propuestas, artículos, referencia, reinicio y rerun idempotente", async ({ browser, request }) => {
  const prepared = JSON.parse(readFileSync(stateFile, "utf-8"));
  const importId = String(prepared.import_id);
  const batchId = String(prepared.batch_id);
  const recipeCount = Number(prepared.recipe_count);
  const safeCount = Number(prepared.safe_count);
  const proposalCount = Number(prepared.proposal_count);
  const aguaRecipeId = String(prepared.agua_recipe_id);
  expect(prepared.xlsx_version).toBe("0.3");
  expect(prepared.export_context_complete).toBe(true);
  expect(Number(prepared.detected_recipes)).toBeGreaterThanOrEqual(recipeCount);
  expect(Number(prepared.menus)).toBeGreaterThan(0);
  expect(Number(prepared.ap_excluded)).toBeGreaterThan(0);
  expect(recipeCount).toBeGreaterThanOrEqual(30);
  const recipeHashBefore = sha256(recipeStore);
  const articleCountBefore = articles().length;
  let browserImports = 0;

  const firstContext = await browser.newContext();
  firstContext.on("request", (browserRequest) => {
    if (browserRequest.url().endsWith("/completado-externo/importar")) browserImports += 1;
  });
  const page = await firstContext.newPage();
  await page.goto("/biblioteca/importaciones");
  const externalCta = page.getByRole("button", { name: `Revisar propuestas externas · ${recipeCount} recetas` });
  await expect(externalCta).toBeVisible({ timeout: 30_000 });
  await externalCta.click();
  await expect(page.getByRole("status").filter({ hasText: `Filas recibidas: ${recipeCount}` })).toContainText(`Requieren revisión: ${recipeCount}`);
  await expect(page.getByRole("region", { name: "Revisar propuestas externas de recetas" })).toContainText(`Propuestas generadas: ${proposalCount}`);
  const aguaProposal = page.locator("details").filter({ hasText: "Agua de jamaica" }).first();
  await aguaProposal.locator(":scope > summary").click();
  await expect(aguaProposal.getByRole("region", { name: "Completitud de receta" })).toContainText("Documento:");
  await expect(aguaProposal.getByRole("region", { name: "Completitud de receta" })).toContainText("Con propuestas IA:");
  await expect(aguaProposal.getByRole("region", { name: "Ficha técnica y escandallo provisionales" })).toContainText("Ficha técnica provisional");
  await expect(aguaProposal.getByRole("region", { name: "Ficha técnica y escandallo provisionales" })).toContainText("Escandallo provisional");
  await expect(aguaProposal.getByRole("region", { name: "Ficha técnica y escandallo provisionales" })).toContainText("PROVISIONAL");
  await expect(aguaProposal.getByRole("region", { name: "Ficha técnica y escandallo provisionales" })).toContainText("Coste por ración: 0.88");
  await expect(aguaProposal).toContainText("IA_PROPUESTA");
  await expect(aguaProposal).toContainText("NO_APLICA");
  await expect(aguaProposal).toContainText("confianza 90%");
  await page.getByRole("button", { name: "Aceptar propuestas seguras de todas" }).click();
  const initialPreview = page.getByRole("region", { name: "Preview consolidado" });
  await expect(initialPreview).toContainText(`Recetas afectadas: ${recipeCount} · Cambios a aplicar: ${safeCount}`);
  await expect(initialPreview).not.toContainText("ingredientes_estructurados");

  const beforeRestart = await (await request.get(`${apiBase}/api/v1/biblioteca/importaciones/${importId}`)).json();
  expect(beforeRestart.importacion.completado_recetas_activo.batch_id).toBe(batchId);
  expect(beforeRestart.importacion.completado_recetas_activo.preview.cambios_a_aplicar).toBe(safeCount);
  await firstContext.close();
  expect((await request.post(`${supervisorBase}/restart-all`)).ok()).toBe(true);

  const recoveredContext = await browser.newContext();
  const recovered = await recoveredContext.newPage();
  await recovered.goto("/biblioteca/importaciones");
  const recoveredCta = recovered.getByRole("button", { name: `Revisar propuestas externas · ${recipeCount} recetas` });
  await expect(recoveredCta).toBeVisible({ timeout: 30_000 });
  await recoveredCta.click();
  await expect(recovered.getByRole("region", { name: "Preview consolidado" })).toContainText(`Cambios a aplicar: ${safeCount}`);
  await recovered.getByRole("button", { name: "Volver a propuestas" }).click();
  const recoveredAgua = recovered.locator("details").filter({ hasText: "Agua de jamaica" }).first();
  const groupedOperationalFields = [
    "rendimiento", "unidad_rendimiento", "numero_raciones",
    "cantidad_por_racion", "tiempo_total",
    "produccion_maxima", "personal_recomendado",
    "recursos_necesarios",
  ];
  const criticalOperationalFields = ["conservacion", "tiempo_descongelacion", "ingredientes_estructurados"];
  await recoveredAgua.evaluate((element: HTMLDetailsElement) => { element.open = true; });
  const firstOperational = recoveredAgua.locator("li").filter({ hasText: "ingredientes_estructurados" }).first();
  await firstOperational.getByRole("button", { name: "Validar y seleccionar este campo" }).click();
  await expect(recovered.getByRole("region", { name: "Preview consolidado" })).toBeVisible();
  const selectedBatch = await (await request.get(`${apiBase}/api/v1/biblioteca/recetas/completado-ia/${batchId}/estado`)).json();
  const aguaResult = selectedBatch.resultados.find((item: { recipe_id: string }) => item.recipe_id === aguaRecipeId);
  const groupedOperationalSelection = Object.fromEntries(
    groupedOperationalFields.map((field) => [field, aguaResult.datos_operativos_agrupables[field]]),
  );
  const criticalOperationalSelection = Object.fromEntries(
    criticalOperationalFields.map((field) => [field, aguaResult.datos_requieren_revision_individual[field]]),
  );
  expect(Object.values(groupedOperationalSelection).every((value) => value !== undefined)).toBe(true);
  expect(Object.values(criticalOperationalSelection).every((value) => value !== undefined)).toBe(true);
  expect((await request.post(
    `${apiBase}/api/v1/biblioteca/recetas/completado-ia/${batchId}/seleccion`,
    { data: {
      selections: { [aguaRecipeId]: selectedBatch.selecciones[aguaRecipeId] },
      grouped_selections: { [aguaRecipeId]: groupedOperationalSelection },
      individual_selections: { [aguaRecipeId]: criticalOperationalSelection },
    } },
  )).ok()).toBe(true);
  expect((await request.post(
    `${apiBase}/api/v1/biblioteca/recetas/completado-ia/${batchId}/preview`, { data: {} },
  )).ok()).toBe(true);
  await recovered.reload();
  const reloadedCta = recovered.getByRole("button", { name: `Revisar propuestas externas · ${recipeCount} recetas` });
  await expect(reloadedCta).toBeVisible({ timeout: 30_000 });
  await reloadedCta.click();
  const operationalPreview = recovered.getByRole("region", { name: "Preview consolidado" });
  await expect(operationalPreview).toContainText("ingredientes_estructurados");
  await expect(operationalPreview).toContainText("tiempo_descongelacion");
  await expect(operationalPreview).toContainText("NO_APLICA");
  await expect(operationalPreview).toContainText("Propuesta E2E basada");
  await expect(operationalPreview.getByRole("region", { name: "Ficha técnica y escandallo provisionales" }).filter({ hasText: "Coste total: 8.8" })).toBeVisible();
  const readyBatch = await (await request.get(`${apiBase}/api/v1/biblioteca/recetas/completado-ia/${batchId}/estado`)).json();
  const operationalFingerprint = String(readyBatch.preview.fingerprint);
  await operationalPreview.getByRole("button", { name: "Confirmar cambios" }).click();
  await expect(recovered.getByRole("status").filter({ hasText: "Completado:" })).toBeVisible({ timeout: 60_000 });
  const repeatedConfirm = await (await request.post(
    `${apiBase}/api/v1/biblioteca/recetas/completado-ia/${batchId}/confirmar`,
    { data: { fingerprint: operationalFingerprint } },
  )).json();
  expect(repeatedConfirm.idempotente).toBe(true);
  const aguaAfterConfirm = await (await request.get(`${apiBase}/api/v1/biblioteca/elaboraciones/${aguaRecipeId}`)).json();
  expect(aguaAfterConfirm.elaboracion.ficha_tecnica.rendimiento).toBe(10);
  expect(aguaAfterConfirm.elaboracion.ficha_tecnica.unidad_rendimiento).toBe("raciones");
  expect(aguaAfterConfirm.elaboracion.ficha_tecnica.estados_campos_operativos.tiempo_descongelacion.estado).toBe("NO_APLICA");
  expect(aguaAfterConfirm.elaboracion.ficha_tecnica.tiempos.tiempo_descongelacion ?? null).toBeNull();
  expect(aguaAfterConfirm.elaboracion.receta.ingredientes).toHaveLength(3);
  expect(aguaAfterConfirm.elaboracion.escandallo.estado_coste).toBe("DISPONIBLE");
  expect(aguaAfterConfirm.elaboracion.escandallo.coste_total).toBe(8.8);
  await recovered.getByRole("button", { name: "Volver al resumen" }).click();

  await recovered.getByRole("button", { name: /Revisar artículos ·/ }).click();
  const candidates = recovered.getByRole("region", { name: "Ingredientes nuevos y artículos candidatos" });
  await expect(candidates).toContainText("Ingredientes nuevos · 1");
  await expect(candidates).toContainText("2 apariciones");
  await candidates.getByRole("button", { name: "Preparar alta autorizada" }).click();
  await candidates.getByRole("button", { name: "Revisar y guardar" }).click();
  const catalogPreview = candidates.getByRole("region", { name: "Vista previa" });
  await expect(catalogPreview).toContainText("Estragón nuevo E2E");
  expect(articles().filter((item) => item.nombre === "Estragón nuevo E2E")).toHaveLength(0);
  await catalogPreview.getByRole("button", { name: "Confirmar" }).click();
  await expect(candidates).toContainText("Todos los ingredientes nuevos ya tienen un artículo vinculado.");

  const importAfterLink = await (await request.get(`${apiBase}/api/v1/biblioteca/importaciones/${importId}`)).json();
  const linked = importAfterLink.importacion.borrador.recipes.flatMap((recipe: { ingredients?: Array<Record<string, unknown>> }) => recipe.ingredients || []).filter((ingredient: Record<string, unknown>) => ingredient.name_raw === "Estragón nuevo E2E");
  expect(linked).toHaveLength(2);
  expect(new Set(linked.map((ingredient: Record<string, unknown>) => ingredient.article_id)).size).toBe(1);

  await candidates.getByRole("link", { name: "Exportar y enriquecer artículos incompletos" }).click();
  await expect(recovered).toHaveURL(/\/articulos\?panel=referencias/);
  await recovered.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await expect(recovered.getByRole("heading", { name: "Artículos incompletos" })).toBeVisible();
  const missing = await (await request.get(`${apiBase}/api/v1/articulos/sin-precio`)).json();
  const incomplete = missing.articulos.find((item: { articulo: string }) => item.articulo === "Estragón nuevo E2E");
  expect(incomplete).toBeTruthy();
  expect(incomplete.precio_real).toBeNull();
  expect(incomplete.proveedor_real).toBeNull();
  await recovered.getByRole("button", { name: "Copiar lista para enriquecimiento externo" }).click();
  await expect(recovered.getByRole("status")).toContainText("Lista de artículos incompletos copiada");
  const exportedArticles = await (await request.get(`${apiBase}/api/v1/articulos/sin-precio/exportar`)).json();
  expect(exportedArticles.texto).toContain(incomplete.article_id);

  const raw = `article_id,artículo,producto,proveedor_referencia,formato,precio,moneda,url\n${incomplete.article_id},Estragón nuevo E2E,Estragón,Proveedor externo E2E,100 g,2.50,EUR,https://example.test/estragon`;
  await recovered.getByLabel("Reimportar precio y proveedor/tienda de referencia").fill(raw);
  await recovered.getByRole("button", { name: "Preparar vista previa" }).click();
  let referencePreview = recovered.getByRole("region", { name: "Referencias a importar" });
  await expect(referencePreview).toContainText("Actual real: precio sin informar · proveedor sin informar");
  await expect(referencePreview).toContainText("Proveedor externo E2E");
  expect(articles().find((item) => item.codigo === incomplete.article_id)?.precios_referencia).toBeUndefined();
  await referencePreview.getByRole("button", { name: "Confirmar referencias seleccionadas" }).click();
  await expect(recovered.getByRole("status")).toContainText("El precio y el proveedor reales siguen sin modificarse");
  expect((articles().find((item) => item.codigo === incomplete.article_id)?.precios_referencia as unknown[])).toHaveLength(1);
  await recoveredContext.close();

  expect((await request.post(`${supervisorBase}/restart-all`)).ok()).toBe(true);
  const stateAfterRestart = await (await request.get(`${apiBase}/api/v1/articulos/referencias-importadas/estado`)).json();
  expect(stateAfterRestart.workflow.estado).toBe("CONFIRMADO");
  expect(stateAfterRestart.workflow.preview.listas[0].article_id).toBe(incomplete.article_id);

  const finalContext = await browser.newContext();
  const finalPage = await finalContext.newPage();
  await finalPage.goto("/articulos?panel=referencias");
  referencePreview = finalPage.getByRole("region", { name: "Referencias a importar" });
  await expect(referencePreview).toContainText("VISTA PREVIA CONSERVADA · CONFIRMADA");
  await expect(referencePreview).toContainText("Proveedor externo E2E");
  await finalPage.reload();
  await expect(finalPage.getByRole("region", { name: "Referencias a importar" })).toContainText("Proveedor externo E2E");

  await finalPage.getByLabel("Reimportar precio y proveedor/tienda de referencia").fill(raw);
  await finalPage.getByRole("button", { name: "Preparar vista previa" }).click();
  referencePreview = finalPage.getByRole("region", { name: "Referencias a importar" });
  await referencePreview.getByRole("button", { name: "Confirmar referencias seleccionadas" }).click();
  const finalArticle = articles().find((item) => item.codigo === incomplete.article_id) as Record<string, unknown>;
  expect(finalArticle.precio ?? null).toBeNull();
  expect(finalArticle.proveedor || null).toBeNull();
  expect(finalArticle.precios_referencia as unknown[]).toHaveLength(1);
  expect(articles().filter((item) => item.nombre === "Estragón nuevo E2E")).toHaveLength(1);
  expect(articles()).toHaveLength(articleCountBefore + 1);
  expect(readFileSync(referenceAudit, "utf-8").trim().split(/\r?\n/)).toHaveLength(1);
  expect(sha256(recipeStore)).not.toBe(recipeHashBefore);
  expect(browserImports).toBe(0);
  await finalContext.close();

  const cleanImportContext = await browser.newContext();
  expect(await cleanImportContext.storageState()).toEqual({ cookies: [], origins: [] });
  const cleanImportPage = await cleanImportContext.newPage();
  await cleanImportPage.goto("/biblioteca/importaciones");
  let completedBatchCta = cleanImportPage.getByRole("button", { name: `Revisar propuestas externas · ${recipeCount} recetas` });
  await expect(completedBatchCta).toBeVisible({ timeout: 30_000 });
  await completedBatchCta.click();
  await expect(cleanImportPage.getByRole("region", { name: "Revisar propuestas externas de recetas" })).toContainText(`Propuestas generadas: ${proposalCount}`);
  let completedDetail = await (await request.get(`${apiBase}/api/v1/biblioteca/importaciones/${importId}`)).json();
  expect(completedDetail.importacion.completado_recetas_activo.batch_id).toBe(batchId);
  expect(completedDetail.importacion.completado_recetas_activo.estado).toBe("COMPLETADO");
  await cleanImportPage.reload();
  completedBatchCta = cleanImportPage.getByRole("button", { name: `Revisar propuestas externas · ${recipeCount} recetas` });
  await expect(completedBatchCta).toBeVisible({ timeout: 30_000 });
  await completedBatchCta.click();
  await expect(cleanImportPage.getByRole("region", { name: "Revisar propuestas externas de recetas" })).toContainText(`Propuestas generadas: ${proposalCount}`);
  completedDetail = await (await request.get(`${apiBase}/api/v1/biblioteca/importaciones/${importId}`)).json();
  expect(completedDetail.importacion.completado_recetas_activo.batch_id).toBe(batchId);
  expect(browserImports).toBe(0);
  await cleanImportContext.close();
});
