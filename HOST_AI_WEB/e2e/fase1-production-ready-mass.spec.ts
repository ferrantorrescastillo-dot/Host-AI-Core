import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

test.setTimeout(360_000);

const backendPort = Number(process.env.HOST_AI_E2E_BACKEND_PORT || 8041);
const supervisorPort = Number(process.env.HOST_AI_E2E_SUPERVISOR_PORT || 8042);
const runtimeName = process.env.HOST_AI_E2E_RUNTIME_NAME || "fase1-mass-e2e";
const apiBase = `http://127.0.0.1:${backendPort}`;
const supervisorBase = `http://127.0.0.1:${supervisorPort}`;
const currentDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(currentDir, "../..");
const stateFile = path.join(projectRoot, ".test-runs", runtimeName, "e2e-state.json");

test("lote físico 52: excepciones aisladas, preview, confirmación aislada, reinicio e idempotencia", async ({ browser, request }) => {
  const prepared = JSON.parse(readFileSync(stateFile, "utf-8"));
  const importId = String(prepared.import_id);
  const batchId = String(prepared.batch_id);
  expect(prepared.xlsx_version).toBe("0.3");
  expect(Number(prepared.recipe_count)).toBeGreaterThanOrEqual(50);
  expect(Number(prepared.production_ready_provisional)).toBe(49);
  expect(Number(prepared.mass_errors)).toBe(2);
  expect(Number(prepared.mass_impossible)).toBe(1);

  const initial = await (await request.get(`${apiBase}/api/v1/biblioteca/recetas/completado-ia/${batchId}/estado`)).json();
  expect(initial.import_id).toBe(importId);
  expect(initial.progreso.total).toBe(52);
  expect(initial.progreso.analizadas).toBe(52);
  expect(initial.resumen_masivo.production_ready_provisional).toBe(49);
  expect(initial.resumen_masivo.errores).toBe(2);
  expect(initial.resumen_masivo.imposibles_estimar).toBe(1);
  expect(initial.datos_reales_modificados).toBe(false);

  const cleanContext = await browser.newContext();
  expect(await cleanContext.storageState()).toEqual({ cookies: [], origins: [] });
  const page = await cleanContext.newPage();
  await page.goto("/biblioteca/importaciones");
  const cta = page.getByRole("button", { name: "Revisar propuestas externas · 52 recetas" });
  await expect(cta).toBeVisible({ timeout: 30_000 });
  await cta.click();
  const summary = page.getByRole("region", { name: "Resumen masivo production-ready" });
  await expect(summary).toContainText("Recetas procesadas52");
  await expect(summary).toContainText("Production-ready provisional49");
  await expect(summary).toContainText("Errores2");
  await expect(summary).toContainText("Imposibles de estimar1");
  await expect(summary).toContainText("Con NO_APLICA51");

  const aguaProposal = page.locator("details").filter({ hasText: "Agua de jamaica" }).first();
  await aguaProposal.locator("summary").click();
  await expect(aguaProposal.getByRole("region", { name: "Completitud de receta" })).toContainText("Production-ready provisional: Sí");
  const aguaProjection = aguaProposal.getByRole("region", { name: "Ficha técnica y escandallo provisionales" });
  await expect(aguaProjection).toContainText("Ficha técnica provisional");
  await expect(aguaProjection).toContainText("Escandallo provisional");
  await expect(aguaProjection).toContainText("PROVISIONAL");
  await expect(aguaProjection).toContainText("Coste total: 5.8");
  await expect(aguaProposal).toContainText("Flor de hibiscus");
  await expect(aguaProposal).toContainText("Limones");
  await expect(aguaProposal).toContainText("Azúcar");
  await expect(aguaProposal).toContainText("IA_PROPUESTA");
  await expect(aguaProposal).toContainText("NO_APLICA");

  await page.getByLabel("Filtrar recetas del lote").selectOption("ERRORES");
  await expect(page.getByText("Mostrando 2 de 52 recetas.")).toBeVisible();
  await page.getByLabel("Filtrar recetas del lote").selectOption("NO_PRODUCTION_READY");
  await expect(page.getByText("Mostrando 3 de 52 recetas.")).toBeVisible();
  await page.getByLabel("Filtrar recetas del lote").selectOption("IMPOSIBLES");
  await expect(page.getByText("Mostrando 1 de 52 recetas.")).toBeVisible();
  await page.getByLabel("Filtrar recetas del lote").selectOption("TODAS");

  await page.getByRole("button", { name: "Aceptar propuestas seguras de todas" }).click();
  const preview = page.getByRole("region", { name: "Preview consolidado" });
  await expect(preview).toContainText(`Cambios a aplicar: ${prepared.safe_count}`);
  const selected = await (await request.get(`${apiBase}/api/v1/biblioteca/recetas/completado-ia/${batchId}/estado`)).json();
  expect(selected.preview.cambios_a_aplicar).toBe(Number(prepared.safe_count));
  expect(selected.datos_reales_modificados).toBe(false);
  await page.reload();
  await page.getByRole("button", { name: "Revisar propuestas externas · 52 recetas" }).click();
  await expect(page.getByRole("region", { name: "Preview consolidado" })).toContainText(`Cambios a aplicar: ${prepared.safe_count}`);

  const fingerprint = String(selected.preview.fingerprint);
  await page.getByRole("button", { name: "Confirmar cambios" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Completado:" })).toBeVisible({ timeout: 60_000 });
  const repeated = await (await request.post(
    `${apiBase}/api/v1/biblioteca/recetas/completado-ia/${batchId}/confirmar`,
    { data: { fingerprint } },
  )).json();
  expect(repeated.idempotente).toBe(true);
  const confirmedBatch = await (await request.get(`${apiBase}/api/v1/biblioteca/recetas/completado-ia/${batchId}/estado`)).json();
  const confirmedRecipeId = confirmedBatch.preview.items[0].recipe_id;
  const postRead = await (await request.get(`${apiBase}/api/v1/biblioteca/elaboraciones/${confirmedRecipeId}`)).json();
  expect(postRead.ok).toBe(true);
  expect(postRead.elaboracion.ficha_tecnica.proceso.procedimiento).toContain("Elaboracion REC601");

  await page.getByRole("button", { name: "Volver al resumen" }).click();
  await page.getByRole("button", { name: /Revisar artículos ·/ }).click();
  const candidates = page.getByRole("region", { name: "Ingredientes nuevos y artículos candidatos" });
  await expect(candidates).toContainText("Ingredientes nuevos · 1");
  await expect(candidates).toContainText("2 apariciones");
  await candidates.getByRole("button", { name: "Preparar alta autorizada" }).click();
  await candidates.getByRole("button", { name: "Revisar y guardar" }).click();
  const catalogPreview = candidates.getByRole("region", { name: "Vista previa" });
  await expect(catalogPreview).toContainText("Estragón nuevo E2E");
  await catalogPreview.getByRole("button", { name: "Confirmar" }).click();
  await expect(candidates).toContainText("Todos los ingredientes nuevos ya tienen un artículo vinculado.");
  const linkedImport = await (await request.get(`${apiBase}/api/v1/biblioteca/importaciones/${importId}`)).json();
  const linked = linkedImport.importacion.borrador.recipes
    .flatMap((recipe: { ingredients?: Array<Record<string, unknown>> }) => recipe.ingredients || [])
    .filter((ingredient: Record<string, unknown>) => ingredient.name_raw === "Estragón nuevo E2E");
  expect(linked).toHaveLength(2);
  expect(new Set(linked.map((ingredient: Record<string, unknown>) => ingredient.article_id)).size).toBe(1);

  await candidates.getByRole("link", { name: "Exportar y enriquecer artículos incompletos" }).click();
  await expect(page).toHaveURL(/\/articulos\?panel=referencias/);
  const missing = await (await request.get(`${apiBase}/api/v1/articulos/sin-precio`)).json();
  const incomplete = missing.articulos.find(
    (item: { articulo: string }) => item.articulo === "Estragón nuevo E2E",
  );
  expect(incomplete).toBeTruthy();
  expect(incomplete.precio_real).toBeNull();
  expect(incomplete.proveedor_real).toBeNull();
  const raw = `article_id,artículo,producto,proveedor_referencia,formato,precio,moneda,url\n${incomplete.article_id},Estragón nuevo E2E,Estragón,Proveedor externo E2E,100 g,2.50,EUR,https://example.test/estragon`;
  await page.getByLabel("Reimportar precio y proveedor/tienda de referencia").fill(raw);
  await page.getByRole("button", { name: "Preparar vista previa" }).click();
  const referencePreview = page.getByRole("region", { name: "Referencias a importar" });
  await expect(referencePreview).toContainText("Actual real: precio sin informar · proveedor sin informar");
  await referencePreview.getByRole("button", { name: "Confirmar referencias seleccionadas" }).click();
  await expect(page.getByRole("status")).toContainText(
    "El precio y el proveedor reales siguen sin modificarse",
  );
  await cleanContext.close();

  expect((await request.post(`${supervisorBase}/restart-all`)).ok()).toBe(true);
  const recovered = await (await request.get(`${apiBase}/api/v1/biblioteca/importaciones/${importId}`)).json();
  expect(recovered.importacion.completado_recetas_activo.batch_id).toBe(batchId);
  expect(recovered.importacion.completado_recetas_activo.estado).toBe("COMPLETADO");
  const recoveredReference = await (await request.get(
    `${apiBase}/api/v1/articulos/referencias-importadas/estado`,
  )).json();
  expect(recoveredReference.workflow.estado).toBe("CONFIRMADO");
  expect(recoveredReference.workflow.preview.listas[0].article_id).toBe(incomplete.article_id);
  const finalContext = await browser.newContext();
  const finalPage = await finalContext.newPage();
  await finalPage.goto("/biblioteca/importaciones");
  await expect(finalPage.getByRole("button", { name: "Revisar propuestas externas · 52 recetas" })).toBeVisible({ timeout: 30_000 });
  await finalContext.close();
});
