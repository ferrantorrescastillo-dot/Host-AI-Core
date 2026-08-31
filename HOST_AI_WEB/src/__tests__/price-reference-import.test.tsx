import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import { articulosService } from "../services/articulosService";
import { ArticulosPage } from "../ui/pages/ArticulosPage";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("consolida, copia y prepara una importación determinista sin Web Search", async () => {
  vi.spyOn(articulosService, "list").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, catalogo: { items: [], total: 0, page: 1, page_size: 20, total_pages: 0, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } });
  vi.spyOn(articulosService, "withoutPrice").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, total: 1, coste_ia_usd: "0.00000000", articulos: [{ article_id: "ART-1", codigo: "ART-1", articulo: "Champiñones", unidad_base: "kg", unidad_compra: "bandeja", cantidad_formato: 500, unidad_formato: "g", recetas: ["REC-1", "REC-2"], usado_en_recetas: 2, precio_real: null, referencia: null, estado: "SIN_PRECIO" }] });
  vi.spyOn(articulosService, "exportWithoutPrice").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, texto: "ART-1 | Champiñones", total: 1, coste_ia_usd: "0.00000000" });
  vi.spyOn(articulosService, "previewImportedReferences").mockResolvedValue({ ok: true, request_id: "R", api_version: "1", version: "1", modo_seguro: true, datos_reales_modificados: false, formato_detectado: "CSV", listas: [{ fila: 1, article_id: "ART-1", articulo: "Champiñones", incluir: true, preview_token: "T", referencia: { tipo: "PRECIO_REFERENCIA_IMPORTADA", origen: "IMPORTADO", producto: "Champiñón", tienda_referencia: "Makro", precio_comercial: 2.5, cantidad_formato: 500, unidad_formato: "g", precio_normalizado: 5, unidad_normalizada: "kg", url: "https://example.test/champ", autoridad: "REFERENCIA_NO_REAL" } }], ambiguas: [], invalidas: [], resumen: { listas: 1, ambiguas: 0, invalidas: 0 }, requiere_confirmacion: true, coste_ia_usd: "0.00000000" });
  const writeText = vi.fn(); Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText } });
  render(<MemoryRouter><ArticulosPage /></MemoryRouter>);
  fireEvent.click(screen.getByRole("button", { name: "Artículos sin precio" }));
  expect(await screen.findByText("Champiñones")).toBeInTheDocument();
  expect(screen.getByText(/2 · REC-1, REC-2/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Copiar lista para buscar precios" })); await waitFor(() => expect(writeText).toHaveBeenCalledWith("ART-1 | Champiñones"));
  fireEvent.change(screen.getByLabelText("Importar referencias"), { target: { value: "article_id,precio\nART-1,2.50" } }); fireEvent.click(screen.getByRole("button", { name: "Preparar importación" }));
  expect(await screen.findByLabelText("Referencias a importar")).toHaveTextContent("coste IA $0");
  expect(screen.queryByText("Buscar precio online")).not.toBeInTheDocument();
});
