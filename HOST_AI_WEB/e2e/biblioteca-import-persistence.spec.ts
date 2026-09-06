import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

const backendPort = Number(process.env.HOST_AI_E2E_BACKEND_PORT || 8011);
const supervisorPort = Number(process.env.HOST_AI_E2E_SUPERVISOR_PORT || 8012);
const runtimeName = process.env.HOST_AI_E2E_RUNTIME_NAME || "fase1-e2e";
const apiBase = `http://127.0.0.1:${backendPort}`;
const supervisorBase = `http://127.0.0.1:${supervisorPort}`;
const currentDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(currentDir, "../..");
const runtimeDir = path.join(projectRoot, ".test-runs", runtimeName);
const recipeStore = path.join(runtimeDir, "DATOS", "db", "biblioteca_recetas_601.json");
const batchStore = path.join(runtimeDir, "DATOS", "db", "biblioteca_completado_recetas_batches.json");
const importStore = path.join(runtimeDir, "DATOS", "db", "biblioteca_importaciones_web.json");
const stateFile = path.join(runtimeDir, "e2e-state.json");
const articleStore = path.join(runtimeDir, "DATOS", "db", "articulos.json");

function sha256(filename: string): string {
  return createHash("sha256").update(readFileSync(filename)).digest("hex");
}

test("importación POST-FIX aparece sin pista local tras reiniciar backend y frontend", async ({ browser, request }) => {
  const prepared = JSON.parse(readFileSync(stateFile, "utf-8"));
  const importId = prepared.import_id as string;
  const batchId = prepared.batch_id as string;
  const proposalCount = Number(prepared.proposal_count);
  const safeCount = Number(prepared.safe_count);
  const domainBefore = sha256(recipeStore);
  let browserImports = 0;

  const firstContext = await browser.newContext();
  firstContext.on("request", (browserRequest) => {
    if (browserRequest.url().endsWith("/completado-externo/importar")) browserImports += 1;
  });
  const page = await firstContext.newPage();
  await page.goto("/biblioteca/importaciones");
  const summaryCta = page.getByRole("button", { name: "Revisar propuestas externas · 30 recetas" });
  await expect(summaryCta).toBeVisible();
  await summaryCta.click();
  await expect(page.getByRole("status").filter({ hasText: "Filas recibidas: 30" })).toContainText("Requieren revisión: 30");
  await expect(page.getByRole("region", { name: "Revisar propuestas externas de recetas" })).toContainText(`Propuestas generadas: ${proposalCount}`);

  await page.getByRole("button", { name: "Aceptar propuestas seguras de todas" }).click();
  let preview = page.getByRole("region", { name: "Preview consolidado" });
  await expect(preview).toContainText(`Recetas afectadas: 30 · Cambios a aplicar: ${safeCount}`);
  await preview.getByRole("button", { name: "Volver a propuestas" }).click();

  const ensaladilla = page.locator("details").filter({ hasText: "Ensaladilla · CON_PROPUESTAS" });
  await ensaladilla.locator(":scope > summary").click();
  await ensaladilla.getByRole("button", { name: "Usar solo propuestas seguras de esta receta" }).click();
  preview = page.getByRole("region", { name: "Preview consolidado" });
  await expect(preview).toContainText("Recetas afectadas: 1 · Cambios a aplicar: 2");
  await preview.getByRole("button", { name: "Volver a propuestas" }).click();
  await ensaladilla.locator(":scope > summary").click();
  await ensaladilla.getByRole("button", { name: "Validar y seleccionar este campo" }).first().click();
  preview = page.getByRole("region", { name: "Preview consolidado" });
  await expect(preview).toContainText("Cambios a aplicar: 3");
  await preview.getByRole("button", { name: "Volver a propuestas" }).click();
  await ensaladilla.locator(":scope > summary").click();
  await ensaladilla.getByRole("button", { name: "Usar solo propuestas seguras de esta receta" }).click();
  preview = page.getByRole("region", { name: "Preview consolidado" });
  await expect(preview).toContainText("Recetas afectadas: 1 · Cambios a aplicar: 2");

  const beforeRestartList = await (await request.get(`${apiBase}/api/v1/biblioteca/importaciones`)).json();
  expect(beforeRestartList.importaciones[0].importacion_id).toBe(importId);
  expect(beforeRestartList.importaciones[0].post_persistence).toBe(true);
  const beforeRestartDetail = await (await request.get(`${apiBase}/api/v1/biblioteca/importaciones/${importId}`)).json();
  expect(beforeRestartDetail.importacion.completado_recetas_activo.batch_id).toBe(batchId);
  expect(beforeRestartDetail.importacion.completado_recetas_activo.preview.cambios_a_aplicar).toBe(2);

  await firstContext.close();
  const restarted = await request.post(`${supervisorBase}/restart-all`);
  expect(restarted.ok()).toBe(true);

  const afterRestartList = await (await request.get(`${apiBase}/api/v1/biblioteca/importaciones`)).json();
  expect(afterRestartList.importaciones).toHaveLength(1);
  expect(afterRestartList.importaciones[0].importacion_id).toBe(importId);
  const afterRestartDetail = await (await request.get(`${apiBase}/api/v1/biblioteca/importaciones/${importId}`)).json();
  expect(afterRestartDetail.importacion.completado_recetas_activo.batch_id).toBe(batchId);
  expect(afterRestartDetail.importacion.completado_recetas_activo.progreso.propuestas).toBe(proposalCount);
  expect(afterRestartDetail.importacion.completado_recetas_activo.preview.cambios_a_aplicar).toBe(2);

  const cleanContext = await browser.newContext();
  cleanContext.on("request", (browserRequest) => {
    if (browserRequest.url().endsWith("/completado-externo/importar")) browserImports += 1;
  });
  const reopened = await cleanContext.newPage();
  await reopened.goto("/biblioteca/importaciones");
  const reopenedCta = reopened.getByRole("button", { name: "Revisar propuestas externas · 30 recetas" });
  await expect(reopenedCta).toBeVisible();
  expect(await reopened.evaluate(() => localStorage.getItem("hostai.active_import_session_id"))).toBe(importId);
  await reopenedCta.click();
  await expect(reopened.getByRole("region", { name: "Preview consolidado" })).toContainText("Cambios a aplicar: 2");
  await reopened.reload();
  await expect(reopened.getByRole("button", { name: "Revisar propuestas externas · 30 recetas" })).toBeVisible();
  await reopened.getByRole("button", { name: "Revisar propuestas externas · 30 recetas" }).click();
  await expect(reopened.getByRole("region", { name: "Preview consolidado" })).toContainText("Cambios a aplicar: 2");

  const persistedImports = JSON.parse(readFileSync(importStore, "utf-8"));
  const persistedBatches = JSON.parse(readFileSync(batchStore, "utf-8"));
  expect(persistedImports.schema_version).toBe(2);
  expect(persistedImports.created_at).toBeTruthy();
  expect(persistedImports.updated_at).toBeTruthy();
  expect(persistedBatches.schema_version).toBe(3);
  expect(Object.keys(persistedBatches.batches)).toHaveLength(1);
  expect(browserImports).toBe(0);
  expect(sha256(recipeStore)).toBe(domainBefore);
  await cleanContext.close();
});

test("ingrediente nuevo recorre alta autorizada, enlace, exportación y referencia externa", async ({ page, request }) => {
  await page.goto("/biblioteca/importaciones");
  const reviewArticles = page.getByRole("button", { name: "Revisar artículos · 1" });
  await expect(reviewArticles).toBeVisible();
  await reviewArticles.click();
  const candidates = page.getByRole("region", { name: "Ingredientes nuevos y artículos candidatos" });
  await expect(candidates).toContainText("Ingredientes nuevos · 1");
  await expect(candidates).toContainText("2 apariciones");

  await candidates.getByRole("button", { name: "Preparar alta autorizada" }).click();
  await candidates.getByRole("button", { name: "Revisar y guardar" }).click();
  const articlePreview = candidates.getByRole("region", { name: "Vista previa" });
  await expect(articlePreview).toContainText("Estragón nuevo E2E");
  await expect(articlePreview).toContainText("PENDIENTE_DE_COMPLETAR");
  let missing = await (await request.get(`${apiBase}/api/v1/articulos/sin-precio`)).json();
  expect(missing.articulos.some((item: { articulo: string }) => item.articulo === "Estragón nuevo E2E")).toBe(false);

  await articlePreview.getByRole("button", { name: "Confirmar" }).click();
  await expect(candidates).toContainText("Todos los ingredientes nuevos ya tienen un artículo vinculado.");
  missing = await (await request.get(`${apiBase}/api/v1/articulos/sin-precio`)).json();
  const incomplete = missing.articulos.find((item: { articulo: string }) => item.articulo === "Estragón nuevo E2E");
  expect(incomplete).toBeTruthy();
  expect(incomplete.precio_real).toBeNull();
  expect(incomplete.proveedor_real).toBeNull();

  await candidates.getByRole("link", { name: "Exportar y enriquecer artículos incompletos" }).click();
  await expect(page).toHaveURL(/\/articulos\?panel=referencias/);
  await expect(page.getByRole("heading", { name: "Artículos incompletos" })).toBeVisible();
  await page.getByLabel("Reimportar precio y proveedor/tienda de referencia").fill(
    `article_id,artículo,producto,proveedor_referencia,formato,precio,moneda,url\n${incomplete.article_id},Estragón nuevo E2E,Estragón,Proveedor externo E2E,100 g,2.50,EUR,https://example.test/estragon`,
  );
  await page.getByRole("button", { name: "Preparar vista previa" }).click();
  const referencePreview = page.getByRole("region", { name: "Referencias a importar" });
  await expect(referencePreview).toContainText("Actual real: precio sin informar · proveedor sin informar");
  await expect(referencePreview).toContainText("Proveedor externo E2E");
  let stored = JSON.parse(readFileSync(articleStore, "utf-8")).find((item: { codigo: string }) => item.codigo === incomplete.article_id);
  expect(stored.precios_referencia).toBeUndefined();

  await referencePreview.getByRole("button", { name: "Confirmar referencias seleccionadas" }).click();
  await expect(page.getByRole("status")).toContainText("El precio y el proveedor reales siguen sin modificarse");
  stored = JSON.parse(readFileSync(articleStore, "utf-8")).find((item: { codigo: string }) => item.codigo === incomplete.article_id);
  expect(stored.precio ?? null).toBeNull();
  expect(stored.proveedor || null).toBeNull();
  expect(stored.precios_referencia).toHaveLength(1);
  expect(stored.precios_referencia[0].tienda_referencia).toBe("Proveedor externo E2E");
});
