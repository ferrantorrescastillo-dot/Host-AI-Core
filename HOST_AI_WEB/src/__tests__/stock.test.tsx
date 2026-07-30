import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

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
  afterEach(() => vi.restoreAllMocks());

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
});
