import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

test.setTimeout(360_000);

const runtimeName = process.env.HOST_AI_E2E_RUNTIME_NAME || "fase1-contract-e2e";
const backendPort = Number(process.env.HOST_AI_E2E_BACKEND_PORT || 8041);
const supervisorPort = Number(process.env.HOST_AI_E2E_SUPERVISOR_PORT || 8042);
const apiBase = `http://127.0.0.1:${backendPort}`;
const supervisorBase = `http://127.0.0.1:${supervisorPort}`;
const currentDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(currentDir, "../..");
const runtimeDir = path.join(projectRoot, ".test-runs", runtimeName);
const stateFile = path.join(runtimeDir, "e2e-state.json");

function completeFromPublicWorkbook(source: string, target: string) {
  const script = String.raw`
import json, sys
from openpyxl import load_workbook

source, target = sys.argv[1], sys.argv[2]
book = load_workbook(source)
assert set(["METADATA", "PROMPT_IA", "INSTRUCCIONES", "SCHEMA", "RECETAS", "ARTICULOS_PENDIENTES", "PRECIOS_REFERENCIA", "SCHEMA_PRECIOS"]).issubset(book.sheetnames)
prompt_rows = list(book["PROMPT_IA"].iter_rows(min_row=2, values_only=True))
assert len(prompt_rows) == 1
assert "Procesa TODAS las recetas" in str(prompt_rows[0][2])
assert "REFERENCIA_EXTERNA" in str(prompt_rows[0][2])
instructions = dict(book["INSTRUCCIONES"].iter_rows(min_row=2, values_only=True))
assert "campos_pendientes_claves" in instructions["SOLO_PENDIENTES"]
schema_rows = list(book["SCHEMA"].iter_rows(values_only=True))
schema = {row[0]: dict(zip(schema_rows[0], row)) for row in schema_rows[1:]}
sheet = book["RECETAS"]
headers = {cell.value: cell.column for cell in sheet[1]}
for row_number in range(2, sheet.max_row + 1):
    pending = json.loads(sheet.cell(row_number, headers["campos_pendientes_claves"]).value or "[]")
    ingredient_names = json.loads(sheet.cell(row_number, headers["ingredientes"]).value or "[]")
    recipe_name = str(sheet.cell(row_number, headers["nombre"]).value or "")
    metadata = {}
    for field in pending:
        spec = schema[field]
        if field == "alergenos":
            continue
        if field == "puede_congelarse":
            value = False
        elif field == "intervencion_activa":
            value = True
        elif field in {"tiempo_descongelacion", "vida_util_congelado"}:
            value = spec["ejemplo_no_aplica"]
        elif field == "regeneracion" and recipe_name == "Agua de jamaica":
            value = spec["ejemplo_no_aplica"]
        elif spec["tipo_esperado"] == "boolean":
            value = True
        elif field == "ingredientes_estructurados":
            lines = [{
                "line_id": f"EXT-{row_number}-{index}",
                "nombre_original": name, "name_raw": name,
                "cantidad": 1, "unidad": "kg",
                "cantidad_normalizada": 1, "unidad_normalizada": "kg",
                "dato_provisional": True,
                "procedencia_propuesta": {
                    "origen": "IA_PROPUESTA", "confianza": 0.75,
                    "motivo": "Cantidad provisional basada en el contexto publico del XLSX",
                },
            } for index, name in enumerate(ingredient_names, start=1)]
            if recipe_name == "Agua de jamaica":
                lines.append({
                    "line_id": "EXT-AGUA-CANDIDATO", "nombre_original": "Agua de proceso",
                    "name_raw": "Agua de proceso", "cantidad": 8, "unidad": "l",
                    "cantidad_normalizada": 8, "unidad_normalizada": "l",
                    "estado_relacion": "CANDIDATO_NUEVO", "dato_provisional": True,
                })
            value = json.dumps(lines, ensure_ascii=False, separators=(",", ":"))
        else:
            value = spec["ejemplo_valido"]
        if row_number == 3 and field == "unidad_rendimiento":
            value = "sacos"
        if row_number == 4 and field == "tipo_elaboracion":
            value = "TIPO_INVENTADO"
        sheet.cell(row_number, headers[f"{field}_propuesto"]).value = value
        metadata[field] = {
            "origen": "IA_PROPUESTA", "confianza": 0.75,
            "motivo": "Propuesta generada exclusivamente desde las hojas publicas del XLSX",
            "fuente": "METADATA+INSTRUCCIONES+SCHEMA+RECETAS", "modelo": "PUBLIC_CONTRACT_COMPLETER",
        }
        if field in {"tiempo_descongelacion", "vida_util_congelado"} or (
            field == "regeneracion" and recipe_name == "Agua de jamaica"
        ):
            metadata[field]["estado_campo"] = "NO_APLICA"
    sheet.cell(row_number, headers["metadatos_propuestas"]).value = json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))
    sheet.cell(row_number, headers["origen_propuesta"]).value = "CHATGPT"
prices = book["PRECIOS_REFERENCIA"]
price_headers = {cell.value: cell.column for cell in prices[1]}
price_completed = 0
for price_row in range(2, prices.max_row + 1):
    base_unit = str(prices.cell(price_row, price_headers["unidad_base"]).value or "").lower()
    if base_unit not in {"kg", "l", "u"}:
        continue
    price_values = {
        "producto_encontrado": str(prices.cell(price_row, price_headers["nombre_canonico"]).value or "Producto comparable"),
        "comercio_fuente": "Distribuidor externo de prueba", "precio_observado": 2.5,
        "moneda": "EUR", "formato_envase": f"1 {base_unit}", "cantidad_envase": 1,
        "unidad_envase": base_unit, "precio_normalizado": 2.5,
        "unidad_precio_normalizado": base_unit, "url_fuente": "https://example.test/referencia-publica",
        "fecha_consulta": "2026-09-05", "observacion_equivalencia": "Producto comparable de prueba",
        "confianza": 0.8, "price_basis": "DESCONOCIDO", "procedencia": "REFERENCIA_EXTERNA",
        "estado_referencia": "REFERENCIA_PROPUESTA",
    }
    for field, value in price_values.items():
        prices.cell(price_row, price_headers[field]).value = value
    price_completed = 1
    break
assert price_completed == 1
book.save(target)
print(json.dumps({"rows": sheet.max_row - 1, "schema_fields": len(schema), "prices": price_completed}))
`;
  const completed = spawnSync("python", ["-c", script, source, target], {
    cwd: projectRoot,
    encoding: "utf-8",
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
  });
  expect(completed.status, completed.stderr).toBe(0);
  return JSON.parse(completed.stdout);
}

test("completador externo usa solo el contrato publico y aísla valores inválidos", async ({ browser, request }) => {
  const prepared = JSON.parse(readFileSync(stateFile, "utf-8"));
  const importId = String(prepared.import_id);
  const recipeIds = Object.keys(prepared.recipe_names);
  expect(recipeIds.length).toBeGreaterThan(50);

  const exportedResponse = await request.post(`${apiBase}/api/v1/biblioteca/recetas/completado-externo/exportar`, {
    data: { recipe_ids: recipeIds, scope: "IMPORTACION", import_id: importId },
  });
  expect(exportedResponse.status()).toBe(200);
  const exported = await exportedResponse.json();
  expect(exported.contrato).toEqual({ format: "HOSTAI_RECIPE_COMPLETION_PACKAGE", version: "0.3" });
  mkdirSync(path.join(runtimeDir, "contract-realistic"), { recursive: true });
  const blank = path.join(runtimeDir, "contract-realistic", exported.filename);
  const completed = path.join(runtimeDir, "contract-realistic", "completado-solo-contrato-publico.xlsx");
  writeFileSync(blank, Buffer.from(exported.contenido_base64, "base64"));
  expect(completeFromPublicWorkbook(blank, completed)).toMatchObject({ rows: recipeIds.length, prices: 1 });

  const context = await browser.newContext();
  expect(await context.storageState()).toEqual({ cookies: [], origins: [] });
  const page = await context.newPage();
  await page.goto("/biblioteca/importaciones");
  const upload = page.getByRole("button", { name: "Importar XLSX completado" });
  await expect(upload).toBeVisible({ timeout: 30_000 });
  const [chooser] = await Promise.all([page.waitForEvent("filechooser"), upload.click()]);
  const responsePromise = page.waitForResponse((response) =>
    response.url().includes("/completado-externo/importar") && response.request().method() === "POST",
  );
  await chooser.setFiles(completed);
  const importedResponse = await responsePromise;
  expect(importedResponse.status()).toBe(200);
  const imported = await importedResponse.json();
  expect(imported.validacion).toMatchObject({
    filas_recibidas: recipeIds.length,
    filas_rechazadas: 0,
    campos: { rechazados: 2, bloqueados_criticos: 0 },
    datos_reales_modificados: false,
  });
  expect(imported.validacion.referencias_precio).toMatchObject({
    referencias_utiles: 1, rechazadas: 0, datos_reales_modificados: false,
  });
  expect(imported.validacion.referencias_precio.filas.find((row: { estado: string }) => row.estado === "REFERENCIA_PROPUESTA").referencia).toMatchObject({
    origen: "REFERENCIA_EXTERNA", autoridad: "REFERENCIA_NO_REAL", estado_revision: "REQUIERE_REVISION_HUMANA",
  });
  expect(imported.batch.resumen_masivo).toMatchObject({
    recetas_procesadas: recipeIds.length,
    production_ready_provisional: recipeIds.length - 2,
    production_ready_confirmed: 0,
    articulos_precios_pendientes: 1,
    errores: 2,
    datos_reales_modificados: false,
  });
  const agua = imported.batch.resultados.find((item: { nombre: string }) => item.nombre === "Agua de jamaica");
  expect(agua.completitud).toMatchObject({
    production_ready_provisional: true,
    production_ready_confirmed: false,
  });
  expect(agua.completitud.no_aplica).toContain("regeneracion");
  expect(agua.datos_requieren_revision_individual.ingredientes_estructurados.at(-1)).toMatchObject({
    nombre_original: "Agua de proceso", estado_relacion: "CANDIDATO_NUEVO", dato_provisional: true,
  });
  expect(agua.proyeccion_provisional.escandallo).toMatchObject({
    estado_coste: "PARCIAL", ingredientes_sin_coste: 1,
  });
  expect(agua.proyeccion_provisional.escandallo.ingredientes_pendientes_coste).toContain("Agua de proceso");
  expect(imported.datos_reales_modificados).toBe(false);
  const rejectionMessages = imported.validacion.filas.flatMap((row: { rechazos_detallados?: Array<{ mensajes?: string[] }> }) =>
    (row.rechazos_detallados ?? []).flatMap((entry) => entry.mensajes ?? []));
  expect(rejectionMessages.some((message: string) => message.includes("unidades_admitidas_json"))).toBe(true);
  expect(rejectionMessages.some((message: string) => message.includes("enum_permitidos_json"))).toBe(true);
  expect(JSON.stringify(imported.batch.resultados)).not.toContain("Texto culinario provisional");
  expect(JSON.stringify(imported.batch.resultados)).not.toContain('"PUBLIC-');

  const summary = page.getByRole("region", { name: "Resumen masivo production-ready" });
  await expect(summary).toContainText(`Production-ready provisional${recipeIds.length - 2}`);
  await expect(summary).toContainText("Production-ready confirmado0");
  await expect(summary).toContainText("Artículos/precios pendientes1");
  const aguaCard = page.locator("details").filter({ hasText: "Agua de jamaica" }).first();
  await aguaCard.locator(":scope > summary").click();
  const projection = aguaCard.getByRole("region", { name: /Ficha t.*cnica y escandallo provisionales/ });
  await expect(projection).toContainText(/Ficha t.*cnica provisional/);
  await expect(projection).toContainText("Escandallo provisional");
  const regeneration = projection.locator("dt").filter({ hasText: /^Regeneraci/ }).locator("xpath=following-sibling::dd[1]");
  const defrost = projection.locator("dt").filter({ hasText: /^Tiempo de descongelaci/ }).locator("xpath=following-sibling::dd[1]");
  await expect(regeneration).toContainText("No aplica");
  await expect(defrost).toContainText("No aplica");
  await expect(regeneration).toContainText("IA_PROPUESTA");
  await expect(regeneration).toContainText("REQUIERE_REVISION_HUMANA");
  await expect(aguaCard).toContainText("Agua de proceso");
  await expect(projection).toContainText("PARCIAL");
  await page.reload();
  await expect(page.getByRole("button", { name: `Revisar propuestas externas · ${recipeIds.length} recetas` })).toBeVisible();
  const durable = await (await request.get(
    `${apiBase}/api/v1/biblioteca/recetas/completado-ia/${imported.batch.batch_id}/estado`,
  )).json();
  expect(durable.resumen_masivo.production_ready_provisional).toBe(recipeIds.length - 2);
  expect(durable.datos_reales_modificados).toBe(false);
  await context.close();

  expect((await request.post(`${supervisorBase}/restart-all`)).ok()).toBe(true);
  const afterRestart = await (await request.get(
    `${apiBase}/api/v1/biblioteca/recetas/completado-ia/${imported.batch.batch_id}/estado`,
  )).json();
  expect(afterRestart.resumen_masivo.production_ready_provisional).toBe(recipeIds.length - 2);
  expect(afterRestart.datos_reales_modificados).toBe(false);
  const restartedContext = await browser.newContext();
  expect(await restartedContext.storageState()).toEqual({ cookies: [], origins: [] });
  const restartedPage = await restartedContext.newPage();
  await restartedPage.goto("/biblioteca/importaciones");
  await expect(restartedPage.getByRole("button", {
    name: new RegExp(`Revisar propuestas externas .* ${recipeIds.length} recetas`),
  })).toBeVisible({ timeout: 30_000 });
  await restartedContext.close();
});
