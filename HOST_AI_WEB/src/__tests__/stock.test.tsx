import { cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { App } from "../ui/App";

function last<T>(items: T[]): T {
  return items[items.length - 1];
}

function response(existencias: unknown[]) {
  return {
    ok: true,
    version: "6.1",
    api_version: "1.0",
    request_id: "REQ-STOCK-1",
    modo_seguro: true,
    datos_reales_modificados: false,
    dashboard: {
      modulos: {
        stock: {
          estado: existencias.length ? "datos_disponibles" : "sin_datos",
          total: existencias.length ? 1 : 0,
          items: existencias.length
            ? [{ tipo: "bajo_stock", nivel: "alto", mensaje: "Tomate bajo mínimo." }]
            : [],
          alertas: existencias.length
            ? [{ tipo: "bajo_stock", nivel: "alto", mensaje: "Tomate bajo mínimo." }]
            : [],
          existencias,
          lotes: existencias.length
            ? [{ id: "LOTE-1", nombre: "Tomate", cantidad: 4, unidad: "kg", ubicacion: "Cámara", caducidad: "2026-08-02" }]
            : [],
          movimientos: existencias.length
            ? [{ id: "MOV-1", tipo: "entrada", nombre: "Tomate", cantidad: 4, unidad: "kg", motivo: "Recepción" }]
            : [],
          caducidades: [],
          resumen: {
            articulos: existencias.length,
            lotes: existencias.length,
            movimientos: existencias.length,
            alertas: existencias.length,
          },
        },
      },
    },
  };
}

function renderPage() {
  return render(<MemoryRouter initialEntries={["/stock"]}><App /></MemoryRouter>);
}

describe("Stock", () => {
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it("muestra existencias, lotes, movimientos y alertas del dashboard", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => response([{
        clave: "ART-TOMATE",
        nombre: "Tomate",
        cantidad: 4,
        unidad: "kg",
        familia: "Verduras",
        lotes: [{ id: "LOTE-1" }],
      }]),
    } as Response);

    renderPage();
    expect(screen.getByText("Cargando stock...")).toBeInTheDocument();
    const existencias = await screen.findByLabelText("Resumen de stock");
    expect(within(existencias).getByText("Artículos")).toBeInTheDocument();
    expect(screen.getAllByText("Tomate").length).toBeGreaterThanOrEqual(3);
    expect(screen.getByText("Tomate bajo mínimo.")).toBeInTheDocument();
    expect(screen.getByText("Cámara")).toBeInTheDocument();
    expect(screen.getByText("Entrada · Recepción")).toBeInTheDocument();
    expect(screen.getByText("Request ID: REQ-STOCK-1")).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/dashboard"),
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("muestra el estado sin datos", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => response([]),
    } as Response);
    renderPage();
    expect(await screen.findByText("No hay existencias de stock registradas.")).toBeInTheDocument();
  });

  it("muestra un error controlado y conserva request_id", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({
        ok: false,
        version: "6.1",
        api_version: "1.0",
        request_id: "REQ-STOCK-ERROR",
        modo_seguro: true,
        datos_reales_modificados: false,
        error: { message: "Stock no disponible temporalmente." },
      }),
    } as Response);
    renderPage();
    expect(await screen.findByText("Stock no disponible temporalmente.")).toBeInTheDocument();
    expect(screen.getByText("Request ID: REQ-STOCK-ERROR")).toBeInTheDocument();
  });

  it("busca un artículo, registra inventario y refresca existencia y movimientos", async () => {
    let saved = false;
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/api/v1/articulos?")) return { ok: true, json: async () => ({ ok: true, version: "6.1", api_version: "1.0", request_id: "REQ-ART", modo_seguro: true, datos_reales_modificados: false, catalogo: { items: [{ id: "ART-PATATA", codigo: "ART-PATATA", nombre: "Patata Monalisa", unidad: "kg", estado: "activo", con_stock: false, tiene_ficha_tecnica: false }], total: 1, page: 1, page_size: 25, total_pages: 1, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } }) } as Response;
      if (url.endsWith("/api/v1/stock/movimientos") && init?.method === "POST") { saved = true; return { ok: true, status: 201, json: async () => ({ ok: true, version: "6.1", api_version: "1.0", request_id: "REQ-MOV", modo_seguro: true, datos_reales_modificados: true, movimiento: { id: "MOV-2", movement_id: "MOV-2", tipo: "inventario_inicial", nombre: "Patata Monalisa", cantidad: 0.5, unidad: "kg", article_id: "ART-PATATA", signo: 1, usuario: "web", origen: "inventario_inicial" }, stock_anterior: 0, stock_actual: 0.5, mensaje: "Movimiento registrado correctamente.", pedidos_creados: 0, recepciones_creadas: 0 }) } as Response; }
      return { ok: true, json: async () => response(saved ? [{ clave: "ART-PATATA", articulo_id: "ART-PATATA", nombre: "Patata Monalisa", cantidad: 0.5, unidad: "kg", familia: "Verduras", lotes: [{ id: "LOTE-2" }] }] : []) } as Response;
    });
    renderPage();
    await screen.findByText("No hay existencias de stock registradas.");
    await userEvent.click(last(screen.getAllByRole("button", { name: "Registrar inventario / ajuste" })));
    await userEvent.type(last(screen.getAllByLabelText("Buscar artículo")), "Patata");
    await userEvent.click(last(screen.getAllByRole("button", { name: "Buscar" })));
    await userEvent.click(last(await screen.findAllByRole("button", { name: "Patata Monalisa · ART-PATATA" })));
    expect(last(screen.getAllByLabelText("Artículo"))).toHaveValue("ART-PATATA");
    await userEvent.type(last(screen.getAllByLabelText("Cantidad")), "0.5");
    await userEvent.click(last(screen.getAllByRole("button", { name: "Guardar movimiento" })));
    expect(await screen.findByText(/Movimiento registrado correctamente. Stock actual: 0,5 kg/)).toBeInTheDocument();
    expect((await screen.findAllByText("Patata Monalisa")).length).toBeGreaterThan(0);
    expect(fetchMock.mock.calls.some(([url, init]) => String(url).endsWith("/stock/movimientos") && init?.method === "POST")).toBe(true);
  });

  it("muestra cero resultados sin seleccionar ni modificar Stock", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/api/v1/articulos?")) return { ok: true, json: async () => ({ ok: true, version: "6.1", api_version: "1.0", request_id: "REQ-EMPTY", modo_seguro: true, datos_reales_modificados: false, catalogo: { items: [], total: 0, page: 1, page_size: 25, total_pages: 0, filtros: { familias: [], proveedores: [], estados: [] }, capacidades: {} } }) } as Response;
      return { ok: true, json: async () => response([]) } as Response;
    });
    renderPage();
    await screen.findByText("No hay existencias de stock registradas.");
    await userEvent.click(last(screen.getAllByRole("button", { name: "Registrar inventario / ajuste" })));
    await userEvent.type(last(screen.getAllByLabelText("Buscar artículo")), "No existe");
    await userEvent.click(last(screen.getAllByRole("button", { name: "Buscar" })));
    expect(await screen.findByText("No se encontraron artículos.")).toBeInTheDocument();
    expect(last(screen.getAllByLabelText("Artículo"))).toHaveValue("");
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes("/stock/movimientos"))).toBe(false);
  });
});
