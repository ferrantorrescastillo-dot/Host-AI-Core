import userEvent from "@testing-library/user-event";
import {
  cleanup,
  render,
  screen,
  within,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

function payload(
  compras: unknown[],
  extras: Record<string, unknown> = {},
) {
  return {
    ok: true,
    version: "6.1",
    api_version: "1.0",
    request_id: "REQ-COMPRAS-1",
    modo_seguro: true,
    datos_reales_modificados: false,
    dashboard: {
      modulos: {
        compras: {
          estado: compras.length ? "datos_disponibles" : "sin_datos",
          total: compras.length,
          items: compras,
          propuestas: [],
          proveedores: [],
          historial: [],
          ...extras,
        },
      },
    },
  };
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/compras"]}>
      <App />
    </MemoryRouter>,
  );
}

describe("Compras", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("muestra carga, resumen y compras del endpoint público real", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () =>
        payload(
          [
            {
              id: "NEC-1",
              nombre: "Tomate triturado",
              prioridad: 3,
              estado: "pendiente",
              fecha_necesaria: "2026-08-03",
            },
          ],
          {
            propuestas: [
              {
                id: "PROP-1",
                producto: "Tomate pera",
                comprar: 5,
                unidad: "kg",
                estado: "pendiente",
                proveedor_sugerido: "Proveedor Uno",
              },
            ],
            proveedores: [
              {
                id: "PROV-1",
                nombre: "Proveedor Uno",
                estado: "activo",
                email: "compras@proveedor.test",
              },
            ],
            historial: [
              {
                id: "COMPRA-1",
                producto: "Cebolla",
                cantidad: 2,
                unidad: "kg",
                proveedor: "Proveedor Uno",
                creado_en: "2026-07-28T10:00:00",
              },
            ],
          },
        ),
    } as Response);

    renderPage();

    expect(screen.getByText("Cargando compras...")).toBeInTheDocument();
    const item = await screen.findByText("Tomate triturado");
    const row = item.closest("li");
    expect(row).not.toBeNull();
    expect(
      within(row as HTMLElement).getByText("Estado: Pendiente"),
    ).toBeInTheDocument();
    expect(screen.getByText("Request ID: REQ-COMPRAS-1")).toBeInTheDocument();
    expect(screen.getByText("Tomate pera")).toBeInTheDocument();
    expect(screen.getAllByText("Proveedor Uno").length).toBeGreaterThan(0);
    expect(screen.getByText("Cebolla")).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/dashboard"),
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("muestra el estado vacío", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => payload([]),
    } as Response);

    renderPage();

    expect(
      await screen.findByText("No hay necesidades de compra pendientes."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("No hay propuestas de compra pendientes."),
    ).toBeInTheDocument();
    expect(screen.getByText("No hay proveedores activos.")).toBeInTheDocument();
    expect(screen.getByText("No hay compras registradas.")).toBeInTheDocument();
  });

  it("muestra error y reintenta la carga", async () => {
    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockResolvedValueOnce({
        ok: false,
        status: 503,
        json: async () => ({
          ok: false,
          version: "6.1",
          api_version: "1.0",
          request_id: "REQ-COMPRAS-ERROR",
          modo_seguro: true,
          datos_reales_modificados: false,
          error: { message: "Compras no disponible temporalmente." },
        }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => payload([]),
      } as Response);

    renderPage();

    expect(
      await screen.findByText("Compras no disponible temporalmente."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Request ID: REQ-COMPRAS-ERROR"),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Reintentar" }));

    expect(
      await screen.findByText("No hay necesidades de compra pendientes."),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
