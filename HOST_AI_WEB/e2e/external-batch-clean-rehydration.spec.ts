import { expect, test } from "@playwright/test";

const backendPort = Number(process.env.HOST_AI_E2E_BACKEND_PORT || 8031);
const apiBase = `http://127.0.0.1:${backendPort}`;

test("rehidrata el batch externo completado en Chrome limpio y después de F5", async ({ browser, request }) => {
  const expectedImportId = "IMPWEB-9CFB9A4EC21E";
  const expectedBatchId = "RECIPE-BATCH-CBF31653B5A5";

  const listed = await (await request.get(`${apiBase}/api/v1/biblioteca/importaciones`)).json();
  expect(listed.importaciones.some((item: { importacion_id: string }) => item.importacion_id === expectedImportId)).toBe(true);
  const detail = await (await request.get(`${apiBase}/api/v1/biblioteca/importaciones/${expectedImportId}`)).json();
  expect(detail.importacion.completado_recetas_activo.batch_id).toBe(expectedBatchId);
  expect(detail.importacion.completado_recetas_activo.estado).toBe("COMPLETADO");
  expect(detail.importacion.completado_recetas_activo.progreso).toMatchObject({ total: 34, propuestas: 392 });
  const batch = await (await request.get(`${apiBase}/api/v1/biblioteca/recetas/completado-ia/${expectedBatchId}/estado`)).json();
  expect(batch).toMatchObject({
    batch_id: expectedBatchId, import_id: expectedImportId, estado: "COMPLETADO",
    datos_reales_modificados: false, progreso: { total: 34, propuestas: 392 },
  });

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
  let cta = page.getByRole("button", { name: "Revisar propuestas externas · 34 recetas" });
  await expect(cta).toBeVisible({ timeout: 30_000 });
  await cta.click();
  await expect(page.getByRole("region", { name: "Revisar propuestas externas de recetas" })).toContainText("Propuestas generadas: 392");

  await page.reload();
  cta = page.getByRole("button", { name: "Revisar propuestas externas · 34 recetas" });
  await expect(cta).toBeVisible({ timeout: 30_000 });
  await cta.click();
  await expect(page.getByRole("region", { name: "Revisar propuestas externas de recetas" })).toContainText("Propuestas generadas: 392");
  const detailAfterReload = await (await request.get(`${apiBase}/api/v1/biblioteca/importaciones/${expectedImportId}`)).json();
  expect(detailAfterReload.importacion.completado_recetas_activo.batch_id).toBe(expectedBatchId);
  expect(externalImports).toBe(0);
  await cleanContext.close();
});
