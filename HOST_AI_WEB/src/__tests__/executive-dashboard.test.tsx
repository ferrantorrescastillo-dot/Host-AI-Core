import userEvent from "@testing-library/user-event";
import { cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

function renderDashboard() {
  return render(<MemoryRouter initialEntries={["/executive"]}><App /></MemoryRouter>);
}

describe("Executive Dashboard", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("agrega exclusivamente los cuatro módulos del dashboard", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        ok: true,
        version: "1.0",
        api_version: "1.0",
        request_id: "REQ-EXEC-1",
        modo_seguro: true,
        datos_reales_modificados: false,
        dashboard: {
          prioridad: { titulo: "NO MOSTRAR" },
          modulos: {
            produccion: { items: [{ id: "P1", nombre: "Banquete", estado: "en_curso" }], tareas_en_curso: 2 },
            compras: { items: [{ id: "C1", nombre: "Tomate", fecha_necesaria: "2026-08-01" }], necesidades_pendientes: 1, propuestas: [{ id: "CP1", producto: "Aceite", estado: "pendiente" }], propuestas_pendientes: 1 },
            eventos: { items: [{ id: "E1", nombre: "Boda Norte", fecha: "2026-08-02", pax: 90, estado: "confirmado", avisos: ["Falta cerrar menú"], riesgos: ["Servicio exterior"] }], eventos_activos: 1, resumen: { pax_total: 90 } },
            stock: { alertas: [{ tipo: "stock_minimo", nivel: "alto", mensaje: "Tomate bajo mínimo" }] },
          },
        },
      }),
    } as Response);

    renderDashboard();

    expect(await screen.findByText("Resumen ejecutivo")).toBeInTheDocument();
    expect(screen.getByText("Banquete")).toBeInTheDocument();
    expect(screen.getByText("Boda Norte")).toBeInTheDocument();
    expect(screen.getByText("Aceite")).toBeInTheDocument();
    expect(screen.getByText("Tomate bajo mínimo")).toBeInTheDocument();
    expect(screen.getByText("Servicio exterior")).toBeInTheDocument();
    expect(screen.getByText("Falta cerrar menú")).toBeInTheDocument();
    expect(screen.queryByText("NO MOSTRAR")).not.toBeInTheDocument();
    const kpis = screen.getByRole("region", { name: "KPIs principales" });
    expect(within(kpis).getByText("90")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/dashboard"),
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("muestra un estado vacío sin inventar datos", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-EMPTY",
        modo_seguro: true, datos_reales_modificados: false, dashboard: { modulos: {} },
      }),
    } as Response);

    renderDashboard();
    expect(await screen.findByText("No hay producción en curso.")).toBeInTheDocument();
    expect(screen.getByText("No hay compras pendientes.")).toBeInTheDocument();
    expect(screen.getByText("No hay próximos eventos.")).toBeInTheDocument();
  });

  it("muestra el error controlado y permite reintentar", async () => {
    const fetchMock = vi.spyOn(global, "fetch")
      .mockResolvedValueOnce({
        ok: false,
        status: 503,
        json: async () => ({
          ok: false, version: "1.0", api_version: "1.0", request_id: "REQ-EXEC-ERR",
          modo_seguro: true, datos_reales_modificados: false,
          error: { message: "Dashboard temporalmente no disponible." },
        }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-EXEC-OK",
          modo_seguro: true, datos_reales_modificados: false, dashboard: { modulos: {} },
        }),
      } as Response);

    renderDashboard();
    expect(await screen.findByText("Dashboard temporalmente no disponible.")).toBeInTheDocument();
    expect(screen.getByText("Request ID: REQ-EXEC-ERR")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByText("Resumen ejecutivo")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
