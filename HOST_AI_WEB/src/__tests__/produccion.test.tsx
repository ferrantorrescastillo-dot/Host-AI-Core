import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

function response(items: unknown[]) {
  return {
    ok: true,
    version: "6.1",
    api_version: "1.0",
    request_id: "REQ-PRODUCCION-1",
    modo_seguro: true,
    datos_reales_modificados: false,
    dashboard: {
      modulos: {
        produccion: {
          estado: items.length ? "datos_disponibles" : "sin_datos",
          total: items.length,
          items,
          resumen: {
            planes_activos: items.length,
            tareas: items.length ? 2 : 0,
            pendientes: items.length ? 1 : 0,
            en_curso: items.length ? 1 : 0,
            bloqueadas: items.length ? 1 : 0,
          },
        },
      },
    },
  };
}

function renderPage() {
  return render(<MemoryRouter initialEntries={["/produccion"]}><App /></MemoryRouter>);
}

describe("Producción", () => {
  afterEach(() => vi.restoreAllMocks());

  it("muestra planes y tareas reales recibidos del dashboard", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => response([{
        id: "PLAN-1",
        nombre: "Producción boda",
        evento: "Boda López",
        fecha: "2026-08-10",
        pax: 80,
        responsable: "Jefa de partida",
        estado: "activo",
        porcentaje_completado: 25,
        tareas: [{
          id: "TAREA-1",
          titulo: "Preparar fondo",
          estado: "bloqueada",
          cantidad: 12,
          unidad: "l",
          bloqueo: "Falta marmita",
        }],
      }]),
    } as Response);

    renderPage();
    expect(screen.getByText("Cargando producción...")).toBeInTheDocument();
    const listado = await screen.findByLabelText("Planes de producción");
    expect(within(listado).getByText("Producción boda")).toBeInTheDocument();
    expect(within(listado).getByText("Preparar fondo")).toBeInTheDocument();
    expect(within(listado).getByText("Bloqueo: Falta marmita")).toBeInTheDocument();
    expect(screen.getByText("Request ID: REQ-PRODUCCION-1")).toBeInTheDocument();
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
    expect(await screen.findByText("No hay planes de producción activos.")).toBeInTheDocument();
  });

  it("muestra un error controlado y conserva request_id", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({
        ok: false,
        version: "6.1",
        api_version: "1.0",
        request_id: "REQ-PROD-ERROR",
        modo_seguro: true,
        datos_reales_modificados: false,
        error: { message: "Producción no disponible temporalmente." },
      }),
    } as Response);
    renderPage();
    expect(await screen.findByText("Producción no disponible temporalmente.")).toBeInTheDocument();
    expect(screen.getByText("Request ID: REQ-PROD-ERROR")).toBeInTheDocument();
  });
});
