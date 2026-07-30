import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

const base = { ok: true, version: "1.0", api_version: "1.0", request_id: "LIB-1", modo_seguro: true, datos_reales_modificados: false };
const item = { id: "REC601-1", codigo: "SALSA", nombre: "Salsa de tomate", categoria: "Salsas", tipo: "Elaboración", estado: "OPERATIVA", rendimiento: 10, raciones: 10, coste_total: 8.5, coste_por_racion: 0.85, tiene_receta: true, tiene_escandallo: true, tiene_ficha_tecnica: true, tiene_fotografia: false, tiene_documentos: false, completitud: 80 };
const list = { ...base, elaboraciones: { items: [item], page: 1, page_size: 20, total: 1, total_pages: 1, filters: { estados: ["OPERATIVA"], categorias: ["Salsas"] }, capabilities: {} } };

describe("Biblioteca Culinaria", () => {
  afterEach(() => vi.restoreAllMocks());
  it("navega al resumen y muestra métricas reales", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({ ...base, biblioteca: { estado: "datos_disponibles", total_elaboraciones: 1, sin_receta: 0, sin_escandallo: 0, sin_ficha_tecnica: 0, con_documentos: 0, capacidades: {} } }) } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Biblioteca" })).toBeInTheDocument();
    expect(screen.getByText("Cada dato se introduce una sola vez y se reutiliza en todo el sistema.")).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledWith("http://127.0.0.1:8000/api/v1/biblioteca", expect.objectContaining({ method: "GET" }));
  });
  it("lista, busca y filtra elaboraciones en backend", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => list } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Salsa de tomate")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Buscar elaboraciones"), { target: { value: "tomate" } });
    await waitFor(() => expect(global.fetch).toHaveBeenLastCalledWith(expect.stringContaining("q=tomate"), expect.anything()));
    expect(screen.queryByText(/\bAP\b/)).not.toBeInTheDocument();
  });
  it("muestra receta, enlace al artículo, escandallo y ficha técnica", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({ ...base, elaboracion: { ...item, receta: { ingredientes: [{ articulo_id: "ART-001", nombre_original: "Tomate pera", cantidad_texto: "2 kg", estado_relacion: "relacionado" }], procedimiento: "Cocer.", tecnicas: [] }, escandallo: { coste_total: 8.5, coste_por_racion: 0.85, rendimiento: 10, estado: "OPERATIVO", desactualizado: false, incidencias: [] }, ficha_tecnica: { receta: {} }, alergenos: [], conservacion: "Refrigerado", produccion: {}, documentos: [], imagenes: [], versiones: [{ version: 1 }], menus: [], eventos: [], historial: [], pendientes: [] } }) } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/elaboraciones/REC601-1?tab=receta"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Salsa de tomate" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Tomate pera" })).toHaveAttribute("href", "/articulos/ART-001");
    fireEvent.click(screen.getByRole("button", { name: "Escandallo" }));
    expect(screen.getAllByText("0.85 €").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "Ficha Tecnica" }));
    expect(screen.getByText("Ficha técnica estructurada disponible.")).toBeInTheDocument();
  });
  it("cubre vistas globales, vacío y error", async () => {
    const mock = vi.spyOn(global, "fetch").mockResolvedValueOnce({ ok: true, json: async () => ({ ...list, elaboraciones: { ...list.elaboraciones, items: [], total: 0, total_pages: 0 } }) } as Response);
    const first = render(<MemoryRouter initialEntries={["/biblioteca/recetas"]}><App /></MemoryRouter>);
    expect(await screen.findByText("No hay recetas para los filtros seleccionados.")).toBeInTheDocument();
    first.unmount();
    mock.mockResolvedValueOnce({ ok: false, status: 503, json: async () => ({ ...base, ok: false, error: { message: "Biblioteca no disponible." } }) } as Response);
    render(<MemoryRouter initialEntries={["/biblioteca/escandallos"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Biblioteca no disponible.")).toBeInTheDocument();
  });
});
