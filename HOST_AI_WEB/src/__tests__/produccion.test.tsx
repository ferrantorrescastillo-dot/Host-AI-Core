import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
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

  it("previsualiza el consumo y exige confirmación antes de modificar Stock", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/consumo-previsto")) return { ok: true, json: async () => ({ ...response([]), consumo_previsto: { ok: true, estado: "LISTO", mensaje: "Stock suficiente", consumos: [{ nombre: "Patata", articulo_id: "ART-1", cantidad: 2.5, unidad: "kg", disponible: 10 }], faltantes: [] }, stock_modificado: false }) } as Response;
      if (url.endsWith("/confirmar") && init?.method === "POST") return { ok: true, json: async () => ({ ...response([]), resultado: { estado: "REGISTRADA", mensaje: "Producción terminada y stock actualizado correctamente." }, plan: {}, stock_modificado: true }) } as Response;
      return { ok: true, json: async () => response([{ id: "PLAN-MENU", nombre: "Producción menú", estado: "borrador", tareas: [{ id: "TASK-1", titulo: "Ensaladilla", estado: "pendiente", cantidad: 10, unidad: "raciones" }] }]) } as Response;
    });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    renderPage();
    await userEvent.click(await screen.findByRole("button", { name: "Ver consumo previsto" }));
    expect(await screen.findByText(/Patata: 2,5 kg/)).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/confirmar"))).toBe(false);
    await userEvent.click(screen.getByRole("button", { name: "Confirmar producción terminada" }));
    expect(window.confirm).toHaveBeenCalled();
    expect(await screen.findByText("Producción terminada y stock actualizado correctamente.")).toBeInTheDocument();
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/confirmar"))).toHaveLength(1);
  });
});
