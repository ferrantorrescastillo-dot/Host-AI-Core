import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import { articulosService } from "../services/articulosService";
import { ArticulosPage } from "../ui/pages/ArticulosPage";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("abre la revisión inline como acordeón, cambia de candidato y cancela", async () => {
  vi.spyOn(articulosService, "list").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, catalogo: { items: [], total: 0, page: 1, page_size: 20, total_pages: 0, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } });
  const candidate = (article_id: string, articulo: string) => ({ article_id, articulo, registro_actual: { precio: null, proveedor: "LEGACY", origen: "excel" }, coincidencias: [{ elaboracion_id: `REC-${article_id}`, nombre: articulo }], senales: ["MISMO_NOMBRE_ELABORACION", "ORIGEN_EXCEL"], estado: "REQUIERE_REVISION" as const, acciones_permitidas: ["VINCULAR_COMO_ELABORACION"] });
  vi.spyOn(articulosService, "reclassificationCandidates").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, total: 4, candidatos: [candidate("SALSA", "Salsa naranja"), candidate("PICO", "Pico de gallo"), candidate("CEVICHE", "Ceviche"), candidate("PAN", "Pan de cristal")] });
  const preview = vi.spyOn(articulosService, "previewReclassification").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, propuestas: [{ article_id: "ART-CEVICHE", registro_actual: {}, propuesto: { tipo_entidad: "ELABORACION_INTERNA", elaboracion_id: "REC-CEVICHE", origen_coste: "COSTE_DERIVADO_ELABORACION" }, consecuencias: [] }], preview_token: "TOKEN", requiere_confirmacion: true });
  const confirm = vi.spyOn(articulosService, "confirmReclassification").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: true, modificados: ["ART-CEVICHE"], sin_cambios: [], idempotente: false, writes_logicos: 1 });
  render(<MemoryRouter><ArticulosPage /></MemoryRouter>);
  fireEvent.click(screen.getByRole("button", { name: "Candidatos de reclasificación" }));
  const ceviche = (await screen.findByText(/Ceviche · CEVICHE/)).closest("article")!;
  const pico = screen.getByText(/Pico de gallo · PICO/).closest("article")!;
  fireEvent.click(within(ceviche).getByRole("button", { name: "Revisar" }));
  expect(within(ceviche).getByRole("region", { name: "Revisión de Ceviche" })).toBeInTheDocument();
  expect(within(pico).queryByText("REGISTRO ACTUAL")).not.toBeInTheDocument();
  fireEvent.click(within(pico).getByRole("button", { name: "Revisar" }));
  expect(within(ceviche).queryByText("REGISTRO ACTUAL")).not.toBeInTheDocument();
  expect(within(pico).getByRole("region", { name: "Revisión de Pico de gallo" })).toBeInTheDocument();
  fireEvent.click(within(pico).getByRole("button", { name: "Cancelar" }));
  expect(screen.queryByText("REGISTRO ACTUAL")).not.toBeInTheDocument();
  expect(preview).not.toHaveBeenCalled(); expect(confirm).not.toHaveBeenCalled();
});
