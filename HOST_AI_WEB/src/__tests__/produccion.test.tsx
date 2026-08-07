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

function last<T>(items: T[]): T { return items[items.length - 1]; }

function plan(overrides = {}) {
  return { id: "PLAN-1", plan_id: "PLAN-1", nombre: "Producción boda", menu_id: "MENU-1", menu_version: 1, comensales: 80, fecha: "2026-08-10", estado: "BLOQUEADO", generated_at: "2026-08-08T10:00:00", solo_planificacion: true, stock_modificado: false, advertencias: [], errores_bloqueantes: [], subelaboraciones: [{ nombre: "Fondo", cantidad_a_producir: 3, unidad: "l", origenes: [] }], ingredientes: [{ nombre: "Patata", articulo_id: "ART-1", cantidad: 2.5, unidad: "kg", disponible: 1, faltante: 1.5 }], resumen: { elaboraciones: 1, subelaboraciones: 1, ingredientes: 1, faltantes: 1, bloqueadas: 1, coste_previsto: 5 }, elaboraciones: [{ id: "TAREA-1", titulo: "Ensaladilla", receta_id: "REC-1", cantidad: 10, cantidad_a_producir: 10, unidad: "raciones", estado: "BLOQUEADO", factor_escalado: 2.5, rendimiento_base: 4, coste_estimado: 5, origen: "menu:MENU-1", ingredientes: [{ nombre: "Patata", articulo_id: "ART-1", cantidad: 2.5, unidad: "kg", disponible: 1, faltante: 1.5 }], subelaboraciones: { componentes: [{ tipo: "elaboracion", nombre: "Fondo", cantidad_necesaria: 3, unidad: "l", detalle: { componentes: [] } }] } }], ...overrides };
}

describe("Producción", () => {
  afterEach(() => vi.restoreAllMocks());

  it("muestra planes y tareas reales recibidos del dashboard", async () => {
    vi.spyOn(global, "fetch").mockImplementation(async (input) => {
      if (String(input).includes("/api/v1/produccion/planes/")) return { ok: true, json: async () => ({ ...response([]), plan: plan() }) } as Response;
      return { ok: true, json: async () => response([{
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
      }]) } as Response;
    });

    renderPage();
    expect(screen.getByText("Cargando producción...")).toBeInTheDocument();
    const listado = await screen.findByLabelText("Planes de producción");
    expect(within(listado).getByText("Producción boda")).toBeInTheDocument();
    expect(within(listado).getByText("Ensaladilla")).toBeInTheDocument();
    expect(within(listado).getByText("BLOQUEADO — faltan ingredientes")).toBeInTheDocument();
    expect(screen.getByText("Request ID: REQ-PRODUCCION-1")).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledTimes(2);
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

  it("muestra resumen, ingredientes, dependencias y navegación a Compras sin consumir Stock", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/api/v1/produccion/planes/")) return { ok: true, json: async () => ({ ...response([]), plan: plan() }) } as Response;
      return { ok: true, json: async () => response([{ id: "PLAN-MENU", nombre: "Producción menú", estado: "borrador", tareas: [{ id: "TASK-1", titulo: "Ensaladilla", estado: "pendiente", cantidad: 10, unidad: "raciones" }] }]) } as Response;
    });
    renderPage();
    expect(last(await screen.findAllByText("Coste previsto"))).toBeInTheDocument();
    await userEvent.click(last(screen.getAllByRole("button", { name: "Ver ingredientes" })));
    expect(await screen.findByText(/Faltan 1,5 kg/)).toBeInTheDocument();
    await userEvent.click(last(screen.getAllByRole("button", { name: "Ver dependencias" })));
    expect(await screen.findByText(/Fondo: 3 l/)).toBeInTheDocument();
    expect(last(screen.getAllByRole("link", { name: "Ir a Compras" }))).toHaveAttribute("href", "/compras");
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/confirmar"))).toBe(false);
    expect(screen.queryByText("Confirmar producción terminada")).not.toBeInTheDocument();
  });
});
