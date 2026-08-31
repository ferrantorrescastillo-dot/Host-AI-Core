import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import { articulosService } from "../services/articulosService";
import { ArticulosPage } from "../ui/pages/ArticulosPage";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("separa artículos comprables sin precio de costes derivados", async () => {
  vi.spyOn(articulosService, "list").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, catalogo: { items: [], total: 0, page: 1, page_size: 20, total_pages: 0, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } });
  vi.spyOn(articulosService, "withoutPrice").mockResolvedValue({
    ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true,
    datos_reales_modificados: false, total: 1, total_costes_derivados: 2,
    coste_ia_usd: "0.00000000",
    articulos: [{ article_id: "ART-CORVINA", codigo: "ART-CORVINA", articulo: "Corvina", tipo_entidad: "ARTICULO_COMPRADO", recetas: [], usado_en_recetas: 0, precio_real: null, referencia: null, estado: "SIN_PRECIO" }],
    costes_derivados: [
      { article_id: "ART-CEVICHE", articulo: "Ceviche", tipo_entidad: "ELABORACION_INTERNA", elaboracion_id: "REC-CEVICHE", origen_coste: "COSTE_DERIVADO_ELABORACION", estado: "COSTE_DERIVADO_ESCANDALLO", coste_total: 34.48, coste_por_racion: 0.59 },
      { article_id: "ART-FONDO", articulo: "Fondo oscuro", tipo_entidad: "SUBELABORACION", elaboracion_id: "REC-FONDO", origen_coste: "COSTE_DERIVADO_ELABORACION", estado: "ESCANDALLO_PENDIENTE" },
    ],
  });

  render(<MemoryRouter><ArticulosPage /></MemoryRouter>);
  fireEvent.click(screen.getByRole("button", { name: "Artículos sin precio" }));

  expect(await screen.findByText("Corvina")).toBeInTheDocument();
  expect(screen.getByText("Ceviche").closest("section")).toHaveAttribute("aria-label", "Costes derivados");
  expect(screen.getByText(/Coste derivado de escandallo/)).toBeInTheDocument();
  expect(screen.getByText(/Escandallo pendiente/)).toBeInTheDocument();
});
