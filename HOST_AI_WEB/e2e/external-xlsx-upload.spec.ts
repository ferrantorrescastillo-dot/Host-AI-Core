import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

const runtimeName = process.env.HOST_AI_E2E_RUNTIME_NAME || "fase1-contract-e2e";
const currentDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(currentDir, "../..");
const runtimeDir = path.join(projectRoot, ".test-runs", runtimeName);
const stateFile = path.join(runtimeDir, "e2e-state.json");
const completedWorkbook = path.join(runtimeDir, "fixture-completado-externo.xlsx");
const backendPort = Number(process.env.HOST_AI_E2E_BACKEND_PORT || 8041);
const apiBase = `http://127.0.0.1:${backendPort}`;

test("reimporta el XLSX completado desde un batch activo y lo conserva sin confirmar", async ({ browser, request }, testInfo) => {
  const prepared = JSON.parse(readFileSync(stateFile, "utf-8"));
  const importId = String(prepared.import_id);
  expect(existsSync(completedWorkbook)).toBe(true);
  expect(prepared.xlsx_version).toBe("0.3");

  const before = await (await request.get(
    `${apiBase}/api/v1/biblioteca/importaciones/${importId}`,
  )).json();
  const batchIdBefore = String(before.importacion.completado_recetas_activo.batch_id);
  expect(batchIdBefore).toMatch(/^RECIPE-BATCH-/);
  expect(before.datos_reales_modificados).toBe(false);

  const context = await browser.newContext();
  expect(await context.storageState()).toEqual({ cookies: [], origins: [] });
  const page = await context.newPage();
  const completionRequests: string[] = [];
  const confirmRequests: string[] = [];
  page.on("request", (entry) => {
    if (entry.url().includes("/completado-externo/importar")) completionRequests.push(entry.url());
    if (entry.url().includes("/confirmar")) confirmRequests.push(entry.url());
  });

  await page.goto("/biblioteca/importaciones");
  await expect(page.getByRole("button", {
    name: `Revisar propuestas externas · ${prepared.recipe_count} recetas`,
  })).toBeVisible();

  const uploadButton = page.getByRole("button", { name: "Importar XLSX completado" });
  await expect(uploadButton).toBeVisible();
  const xlsxInput = page.getByLabel("Seleccionar XLSX completado");
  await expect(xlsxInput).toHaveAttribute(
    "accept",
    ".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  );
  await expect(page.getByLabel("Seleccionar paquete Host AI preparado")).toHaveAttribute(
    "accept",
    "application/json,.json",
  );

  const [fileChooser] = await Promise.all([
    page.waitForEvent("filechooser"),
    uploadButton.click(),
  ]);
  expect(fileChooser.isMultiple()).toBe(false);
  const evidenceDir = path.join(runtimeDir, "evidence-hotfix-xlsx");
  mkdirSync(evidenceDir, { recursive: true });
  const chooserEvidence = JSON.stringify({
    multiple: fileChooser.isMultiple(),
    accept: await xlsxInput.getAttribute("accept"),
    filename: path.basename(completedWorkbook),
  }, null, 2);
  writeFileSync(path.join(evidenceDir, "file-chooser.json"), chooserEvidence, "utf-8");
  await testInfo.attach("file-chooser-xlsx", {
    body: Buffer.from(chooserEvidence),
    contentType: "application/json",
  });

  const importResponsePromise = page.waitForResponse((response) =>
    response.url().includes("/completado-externo/importar") && response.request().method() === "POST",
  );
  await fileChooser.setFiles(completedWorkbook);
  const importResponse = await importResponsePromise;
  expect(importResponse.status()).toBe(200);
  const payload = await importResponse.json();
  expect(payload).toMatchObject({
    ok: true,
    datos_reales_modificados: false,
    contrato: { format: "HOSTAI_RECIPE_COMPLETION_PACKAGE", version: "0.3" },
    batch: {
      import_id: importId,
      modo_generacion: "ARCHIVO_EXTERNO",
    },
  });
  expect(payload.batch.batch_id).not.toBe(batchIdBefore);
  expect(payload.batch.progreso.total).toBe(prepared.recipe_count);
  expect(payload.batch.progreso.propuestas).toBe(prepared.proposal_count);
  expect(payload.validacion.filas_recibidas).toBe(prepared.recipe_count);

  await expect(page.getByText(
    `XLSX completado aceptado · ${prepared.proposal_count} propuestas · sin cambios en datos reales`,
  )).toBeVisible();
  await expect(page.getByText(/Archivo procesado:/)).toContainText(path.basename(completedWorkbook));
  await expect(page.getByRole("region", { name: "Revisar propuestas externas de recetas" })).toContainText(
    `Propuestas generadas: ${prepared.proposal_count}`,
  );
  expect(completionRequests).toHaveLength(1);
  expect(confirmRequests).toEqual([]);
  const screenshot = await page.screenshot({
    fullPage: true,
    path: path.join(evidenceDir, "resultado-importacion-xlsx.png"),
  });
  await testInfo.attach("resultado-importacion-xlsx", {
    body: screenshot,
    contentType: "image/png",
  });

  const durable = await (await request.get(
    `${apiBase}/api/v1/biblioteca/importaciones/${importId}`,
  )).json();
  expect(durable.importacion.completado_recetas_activo.batch_id).toBe(payload.batch.batch_id);
  expect(durable.importacion.completado_recetas_activo.progreso.propuestas).toBe(prepared.proposal_count);
  expect(durable.datos_reales_modificados).toBe(false);

  await page.reload();
  const recoveredCta = page.getByRole("button", {
    name: `Revisar propuestas externas · ${prepared.recipe_count} recetas`,
  });
  await expect(recoveredCta).toBeVisible();
  await expect(page.getByRole("button", { name: "Importar XLSX completado" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Revisar propuestas externas de recetas" })).toContainText(
    `Propuestas generadas: ${prepared.proposal_count}`,
  );
  expect(completionRequests).toHaveLength(1);
  expect(confirmRequests).toEqual([]);
  await context.close();
});
