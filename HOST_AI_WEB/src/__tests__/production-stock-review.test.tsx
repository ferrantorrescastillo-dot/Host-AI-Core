import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ProductionStockReviewPage } from "../ui/pages/ProductionStockReviewPage";

const envelope = { ok: true, version: "6", api_version: "1", request_id: "REQ", modo_seguro: true, datos_reales_modificados: false };
const review = { production_plan_id: "PLAN-1", plan_nombre: "Production · pbd", menu_id: "MENU-1", menu_version: 2, stock_modificado: false, resumen: { ingredientes_totales: 2, cubiertos: 0, faltantes_conocidos: 1, stock_desconocido: 1, sin_relacionar: 0, unidad_pendiente: 0, conversion_pendiente: 0 }, ingredientes: [
  { nombre: "Patata", articulo_id: "ART-1", cantidad: .75, unidad: "kg", unidad_base: "kg", disponible: .5, faltante: .25, estado_resolucion: "FALTANTE_CONOCIDO" },
  { nombre: "Zanahoria", articulo_id: "ART-2", cantidad: .375, unidad: "kg", unidad_base: "kg", unidad_base_sugerida: true, estado_unidad_base: "SUGERIDA_PENDIENTE_REVISION", disponible: null, faltante: null, estado_resolucion: "STOCK_DESCONOCIDO" },
] };

describe("resolución masiva de Stock", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("muestra contexto, filtra pendientes y conserva el regreso al plan", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, json: async () => ({ ...envelope, revision_stock: review }) })));
    render(<MemoryRouter initialEntries={["/produccion/PLAN-1/stock"]}><Routes><Route path="/produccion/:planId/stock" element={<ProductionStockReviewPage/>}/></Routes></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: /Revisar stock del plan/i })).toBeInTheDocument();
    expect(screen.getByText(/Production · pbd/)).toBeInTheDocument();
    expect(screen.getByText("FALTANTE_CONOCIDO")).toBeInTheDocument();
    expect(screen.getByText("STOCK_DESCONOCIDO")).toBeInTheDocument();
    expect(screen.getByText(/Unidad sugerida \/ pendiente de revisión/)).toBeInTheDocument();
    expect(screen.getByLabelText("Cambiar unidad sugerida")).toHaveValue("kg");
    fireEvent.click(screen.getByRole("button", { name: "Faltantes" }));
    expect(screen.queryByText("Zanahoria")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Volver a Producción" })).toHaveAttribute("href", "/produccion");
  });
  it("registra inventario con trazabilidad y refresca la fila", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const payload = url.includes("stock/movimientos") ? { ...envelope, movimiento: { movement_id: "MOV-1" }, stock_anterior: 0, stock_actual: 2, mensaje: "Movimiento registrado", pedidos_creados: 0, recepciones_creadas: 0 }
        : url.includes("/articulos/ART-2") && init?.method === "PATCH" ? { ...envelope, articulo: { nombre: "Zanahoria", unidad_base: "kg", unidad_base_sugerida: false } }
        : url.includes("/articulos/ART-2") ? { ...envelope, articulo: { nombre: "Zanahoria", unidad_base: "kg", unidad_base_sugerida: true } }
        : { ...envelope, revision_stock: review };
      return { ok: true, json: async () => payload };
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<MemoryRouter initialEntries={["/produccion/PLAN-1/stock"]}><Routes><Route path="/produccion/:planId/stock" element={<ProductionStockReviewPage/>}/></Routes></MemoryRouter>);
    await screen.findByText("Zanahoria"); fireEvent.change(screen.getByLabelText("Cantidad"), { target: { value: "2" } }); fireEvent.click(screen.getByRole("button", { name: "Registrar inventario" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url).includes("stock/movimientos"))).toBe(true));
    const patchIndex = fetchMock.mock.calls.findIndex(([url, init]) => String(url).includes("/articulos/ART-2") && init?.method === "PATCH");
    const movementIndex = fetchMock.mock.calls.findIndex(([url]) => String(url).includes("stock/movimientos"));
    expect(patchIndex).toBeGreaterThan(-1); expect(patchIndex).toBeLessThan(movementIndex);
    expect(JSON.parse(String(fetchMock.mock.calls[patchIndex][1]?.body))).toMatchObject({ unidad_base: "kg" });
    expect(JSON.parse(String(fetchMock.mock.calls[movementIndex][1]?.body))).toMatchObject({ unidad: "kg", production_plan_id: "PLAN-1" });
  });
});
