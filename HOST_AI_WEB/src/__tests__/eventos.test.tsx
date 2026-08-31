import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

function response(eventos: unknown[], overrides = {}) {
  return {
    ok: true,
    version: "6.1",
    api_version: "1.0",
    request_id: "REQ-EVENTOS-1",
    modo_seguro: true,
    datos_reales_modificados: false,
    dashboard: {
      modulos: {
        eventos: {
          estado: eventos.length ? "datos_disponibles" : "sin_datos",
          total: eventos.length,
          items: eventos,
          resumen: {
            eventos_activos: eventos.length,
            pax_total: eventos.length ? 120 : 0,
            servicios: eventos.length ? 2 : 0,
            avisos: eventos.length ? 1 : 0,
          },
        },
      },
    },
    ...overrides,
  };
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/eventos"]}>
      <App />
    </MemoryRouter>,
  );
}

describe("Eventos", () => {
  afterEach(() => vi.restoreAllMocks());

  it("muestra carga y el listado recibido de la API", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () =>
        response([
          {
            id: "EVT-1",
            nombre: "Boda Martínez",
            fecha: "2026-08-02",
            pax: 120,
            estado: "confirmado",
            dias: 4,
            servicios: 2,
            avisos: ["Hay servicios sin pases."],
          },
        ]),
    } as Response);

    renderPage();

    expect(screen.getByText("Cargando eventos...")).toBeInTheDocument();
    const listado = await screen.findByLabelText("Listado de eventos");
    const card = within(listado).getByRole("article");
    expect(within(card).getByText("Boda Martínez")).toBeInTheDocument();
    expect(within(card).getByText("120")).toBeInTheDocument();
    expect(within(card).getByText("Confirmado")).toBeInTheDocument();
    expect(within(card).getByText("En 4 días")).toBeInTheDocument();
    expect(within(card).getByText("2 servicios")).toBeInTheDocument();
    expect(within(card).getByText("Hay servicios sin pases.")).toBeInTheDocument();
    expect(within(card).getByRole("link", { name: "Abrir" })).toHaveAttribute("href", "/eventos?evento_id=EVT-1");
    expect(within(card).getByRole("link", { name: "Editar" })).toHaveAttribute("href", "/eventos?evento_id=EVT-1&edit=1");
    expect(screen.getByText("PAX previstos")).toBeInTheDocument();
    expect(screen.getAllByText("Avisos operativos")).toHaveLength(2);
    expect(screen.getByText("Request ID: REQ-EVENTOS-1")).toBeInTheDocument();
    expect(screen.getByText("Activo")).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/dashboard"),
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("muestra el estado vacío", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => response([]),
    } as Response);

    renderPage();
    expect(
      await screen.findByText("No hay próximos eventos disponibles."),
    ).toBeInTheDocument();
  });

  it("muestra el error seguro y conserva request_id", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({
        ok: false,
        version: "6.1",
        api_version: "1.0",
        request_id: "REQ-ERROR-1",
        modo_seguro: true,
        datos_reales_modificados: false,
        error: { message: "Servicio temporalmente no disponible." },
      }),
    } as Response);

    renderPage();
    expect(
      await screen.findByText("Servicio temporalmente no disponible."),
    ).toBeInTheDocument();
    expect(screen.getByText("Request ID: REQ-ERROR-1")).toBeInTheDocument();
  });
});
