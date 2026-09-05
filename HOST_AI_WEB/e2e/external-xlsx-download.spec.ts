import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

const runtimeName = process.env.HOST_AI_E2E_RUNTIME_NAME || "fase1-mass-smoke";
const currentDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(currentDir, "../..");
const stateFile = path.join(projectRoot, ".test-runs", runtimeName, "e2e-state.json");
const runtimeDir = path.dirname(stateFile);
const backendPort = Number(process.env.HOST_AI_E2E_BACKEND_PORT || 8041);
const apiBase = `http://127.0.0.1:${backendPort}`;

function inspectWorkbook(filename: string) {
  const script = [
    "import json, sys",
    "from openpyxl import load_workbook",
    "book = load_workbook(sys.argv[1], read_only=True, data_only=True)",
    "metadata = dict(book['METADATA'].values)",
    "sheet = book['RECETAS']",
    "rows = list(sheet.iter_rows(values_only=True))",
    "headers = list(rows[0])",
    "items = [dict(zip(headers, row)) for row in rows[1:]]",
    "print(json.dumps({'sheets': book.sheetnames, 'metadata': metadata, 'headers': headers, 'rows': len(items), 'import_ids': sorted(set(str(item.get('import_id') or '') for item in items)), 'context_rows': sum(bool(item.get('contexto_documental')) and bool(item.get('ingredientes_contexto')) for item in items), 'names': {str(item.get('recipe_id') or ''): str(item.get('nombre') or '') for item in items}}, ensure_ascii=False))",
  ].join("; ");
  const result = spawnSync("python", ["-c", script, filename], {
    cwd: projectRoot,
    encoding: "utf-8",
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
  });
  expect(result.status, result.stderr).toBe(0);
  return JSON.parse(result.stdout);
}

test("el CTA principal descarga y conserva el batch externo sin duplicarlo", async ({ browser, request }) => {
  const prepared = JSON.parse(readFileSync(stateFile, "utf-8"));
  const importId = String(prepared.import_id);
  const hasExternalBatch = Boolean(prepared.has_external_batch ?? prepared.batch_id);
  expect(prepared.recipe_count).toBe(52);

  const detailBeforeResponse = await request.get(`${apiBase}/api/v1/biblioteca/importaciones/${importId}`);
  expect(detailBeforeResponse.status()).toBe(200);
  const detailBefore = await detailBeforeResponse.json();
  const batchBefore = detailBefore.importacion.completado_recetas_activo?.batch_id ?? null;
  expect(batchBefore).toBe(hasExternalBatch ? prepared.batch_id : null);

  const context = await browser.newContext({ acceptDownloads: true });
  expect(await context.storageState()).toEqual({ cookies: [], origins: [] });
  const page = await context.newPage();
  const requests: string[] = [];
  const responses: string[] = [];
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];

  page.on("request", (request) => requests.push(`${request.method()} ${request.url()}`));
  page.on("response", (response) => responses.push(`${response.status()} ${response.url()}`));
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));

  await page.goto("/biblioteca/importaciones");
  const button = page.getByRole("button", {
    name: `Completar externamente con XLSX · ${prepared.recipe_count}`,
  });
  await expect(button).toBeVisible({ timeout: 30_000 });

  const exportResponsePromise = page.waitForResponse((response) =>
    response.url().includes("/completado-externo/exportar"), { timeout: 30_000 });
  const downloadPromise = page.waitForEvent("download", { timeout: 30_000 });
  await button.click();
  try {
    const [download, exportResponse] = await Promise.all([downloadPromise, exportResponsePromise]);
    expect(exportResponse.status()).toBe(200);
    const exportPayload = await exportResponse.json();
    expect(exportPayload).toMatchObject({
      ok: true,
      contrato: { format: "HOSTAI_RECIPE_COMPLETION_PACKAGE", version: "0.3" },
      recetas_exportadas: 52,
      datos_reales_modificados: false,
    });
    expect(exportPayload.recipe_ids).toHaveLength(52);
    expect(download.suggestedFilename()).toBe(exportPayload.filename);
    expect(download.suggestedFilename()).toMatch(/\.xlsx$/i);

    const downloadDir = path.join(runtimeDir, "downloads");
    mkdirSync(downloadDir, { recursive: true });
    const savedAs = path.join(downloadDir, download.suggestedFilename());
    await download.saveAs(savedAs);
    expect(await download.failure()).toBeNull();
    expect(existsSync(savedAs)).toBe(true);
    const workbook = inspectWorkbook(savedAs);
    expect(workbook.sheets).toEqual(["METADATA", "INSTRUCCIONES", "RECETAS"]);
    expect(workbook.metadata).toMatchObject({
      format: "HOSTAI_RECIPE_COMPLETION_PACKAGE",
      version: "0.3",
      scope: "IMPORTACION",
      import_id: importId,
    });
    expect(workbook.rows).toBe(52);
    expect(workbook.import_ids).toEqual([importId]);
    expect(workbook.context_rows).toBe(52);
    expect(workbook.names).toEqual(prepared.recipe_names);
    expect(Object.values(workbook.names).every((name) => !/^Receta\s+\d+$/.test(String(name)))).toBe(true);
    expect(workbook.headers).toEqual(expect.arrayContaining([
      "recipe_id", "import_id", "contexto_documental", "ingredientes_contexto",
      "articulos_relacionados", "menus_contexto", "contexto_servicio",
      "tipo_elaboracion_propuesto", "rendimiento_neto_propuesto",
      "personal_recomendado_propuesto", "recursos_necesarios_propuesto",
      "estacion_zona_propuesto",
    ]));

    await expect(page.getByRole("status").filter({ hasText: "XLSX descargado" })).toContainText(
      `XLSX descargado · 52 recetas · ${download.suggestedFilename()}`,
    );
    const exportRequests = requests.filter((entry) => entry.includes("/completado-externo/exportar"));
    expect(exportRequests).toHaveLength(1);
    expect(consoleErrors.filter((entry) => !entry.includes("404"))).toEqual([]);
    expect(pageErrors).toEqual([]);
    await expect(page).toHaveURL(/\/biblioteca\/importaciones$/);

    const detailAfter = await (await request.get(
      `${apiBase}/api/v1/biblioteca/importaciones/${importId}`,
    )).json();
    expect(detailAfter.importacion.completado_recetas_activo?.batch_id ?? null).toBe(batchBefore);
    expect(detailAfter.datos_reales_modificados).toBe(false);

    await page.reload();
    await expect(button).toBeVisible({ timeout: 30_000 });
    if (hasExternalBatch) {
      await expect(page.getByRole("button", {
        name: `Revisar propuestas externas · ${prepared.recipe_count} recetas`,
      })).toBeVisible();
    } else {
      await expect(page.getByRole("button", { name: /Revisar propuestas externas/ })).toHaveCount(0);
    }
  } catch (error) {
    console.log(JSON.stringify({ requests, responses, consoleErrors, pageErrors }, null, 2));
    throw error;
  } finally {
    await context.close();
  }
});
