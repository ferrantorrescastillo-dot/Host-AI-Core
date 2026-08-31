import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { buildReservasQuery } from "../services/reservasService";
import { App } from "../ui/App";

const ITEM = {
  reserva_id: "RES-A1B2C3D4E5F6", nombre_cliente: "Ana García", fecha: "2030-05-20",
  hora: "13:30", pax: 4, estado: "CONFIRMADA", servicio: "COMIDA", evento_id: null,
};

function listResponse(items: unknown[] = [ITEM]) {
  return { ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-RES-1", modo_seguro: true,
    datos_reales_modificados: false, reservas: { items, total: items.length } };
}

function detailResponse(overrides = {}) {
  return { ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-DETAIL-1", modo_seguro: true,
    datos_reales_modificados: false, reserva: { ...ITEM, observaciones: "Trona junto a la mesa", ...overrides } };
}

function mockJson(payload: unknown, ok = true, status = 200) {
  return { ok, status, json: async () => payload } as Response;
}

function renderRoute(route = "/reservas") {
  return render(<MemoryRouter initialEntries={[route]}><App /></MemoryRouter>);
}

describe("Reservas R2", () => {
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it("publica ruta y sidebar, muestra loading, listado, request_id y entrada R4 sin PII", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(mockJson(listResponse()));
    renderRoute();
    expect(screen.getByText("Cargando reservas...")).toBeInTheDocument();
    const list = await screen.findByLabelText("Listado de reservas");
    expect(within(list).getByText("Ana García")).toBeInTheDocument();
    expect(within(list).getByText("4")).toBeInTheDocument();
    expect(within(list).getByText("Comida")).toBeInTheDocument();
    expect(screen.getByText("Request ID: REQ-RES-1")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Reservas" })).toHaveAttribute("href", "/reservas");
    expect(screen.queryByText(/teléfono|email/i)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Nueva reserva" })).toBeInTheDocument();
    expect(within(list).getByRole("link", { name: "Abrir" })).toHaveAttribute("href", `/reservas/${ITEM.reserva_id}`);
    expect(within(list).getByRole("link", { name: "Editar" })).toHaveAttribute("href", `/reservas/${ITEM.reserva_id}?edit=1`);
  });

  it("muestra estado vacío sin crear datos", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(mockJson(listResponse([])));
    renderRoute();
    expect(await screen.findByText("No hay reservas registradas.")).toBeInTheDocument();
  });

  it("muestra Abrir, Editar y Eliminar para todos los estados", async () => {
    const states = ["PENDIENTE", "CONFIRMADA", "CANCELADA", "NO_SHOW", "COMPLETADA"];
    const items = states.map((estado, index) => ({ ...ITEM, reserva_id: `RES-${String(index + 1).repeat(12)}`, nombre_cliente: `Reserva ${estado}`, estado }));
    vi.spyOn(global, "fetch").mockResolvedValue(mockJson(listResponse(items)));
    renderRoute();
    const list = await screen.findByLabelText("Listado de reservas");
    for (const estado of states) {
      const card = within(list).getByText(`Reserva ${estado}`).closest("article")!;
      expect(within(card).getByRole("link", { name: "Abrir" })).toBeInTheDocument();
      expect(within(card).getByRole("link", { name: "Editar" })).toBeInTheDocument();
      expect(within(card).getByRole("link", { name: "Eliminar" })).toBeInTheDocument();
    }
  });

  it("muestra error seguro y request_id sin body ni stack", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(mockJson({ ok: false, version: "1.0", api_version: "1.0",
      request_id: "REQ-ERROR-RES", modo_seguro: true, datos_reales_modificados: false,
      error: { status: 503, code: "unavailable", message: "Servicio no disponible." } }, false, 503));
    renderRoute();
    expect(await screen.findByText("Servicio no disponible.")).toBeInTheDocument();
    expect(screen.getByText("Request ID: REQ-ERROR-RES")).toBeInTheDocument();
    expect(screen.queryByText(/Traceback|C:\\/)).not.toBeInTheDocument();
  });

  it("envía alcance, búsqueda, fecha, estado y servicio soportados", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue(mockJson(listResponse([])));
    const user = userEvent.setup(); renderRoute();
    await screen.findByText("No hay reservas registradas.");
    await user.click(screen.getByRole("button", { name: "Hoy" }));
    await waitFor(() => expect(String(fetchMock.mock.calls[fetchMock.mock.calls.length - 1]?.[0] || "")).toContain("alcance=hoy"));
    await user.click(screen.getByRole("button", { name: "Próximas" }));
    await waitFor(() => expect(String(fetchMock.mock.calls[fetchMock.mock.calls.length - 1]?.[0] || "")).toContain("alcance=proximas"));
    await user.click(screen.getByRole("button", { name: "Todas" }));
    await user.type(screen.getByLabelText("Buscar por nombre"), "Ana & familia");
    await user.type(screen.getByLabelText("Fecha"), "2030-05-20");
    await user.selectOptions(screen.getByLabelText("Estado"), "CONFIRMADA");
    await user.selectOptions(screen.getByLabelText("Servicio"), "COMIDA");
    await user.click(screen.getByRole("button", { name: "Aplicar filtros" }));
    await waitFor(() => {
      const url = String(fetchMock.mock.calls[fetchMock.mock.calls.length - 1]?.[0] || "");
      expect(url).toContain("alcance=todas"); expect(url).toContain("q=Ana+%26+familia");
      expect(url).toContain("fecha=2030-05-20"); expect(url).toContain("estado=CONFIRMADA");
      expect(url).toContain("servicio=COMIDA"); expect(url).toContain("limite=50");
    });
  });

  it("navega por ID canónico y muestra observaciones y evento solo en detalle", async () => {
    vi.spyOn(global, "fetch").mockImplementation(async (input) => String(input).includes(`/reservas/${ITEM.reserva_id}`)
      ? mockJson(detailResponse({ evento_id: "EVT-1" })) : mockJson(listResponse()));
    const user = userEvent.setup(); renderRoute();
    expect(screen.queryByText("Trona junto a la mesa")).not.toBeInTheDocument();
    await user.click(await screen.findByRole("link", { name: "Abrir" }));
    expect(await screen.findByText("Trona junto a la mesa")).toBeInTheDocument();
    expect(screen.getByText("EVT-1")).toBeInTheDocument();
    expect(screen.getByText(/Request ID: REQ-DETAIL-1/)).toBeInTheDocument();
  });

  it("abre el editor desde el listado con los datos actuales", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(mockJson(detailResponse()));
    renderRoute(`/reservas/${ITEM.reserva_id}?edit=1`);
    const panel = await screen.findByLabelText("Editar reserva");
    expect(within(panel).getByLabelText("Nombre del cliente")).toHaveValue(ITEM.nombre_cliente);
    expect(within(panel).getByLabelText("Fecha")).toHaveValue(ITEM.fecha);
    expect(within(panel).getByLabelText("Hora")).toHaveValue(ITEM.hora);
  });

  it("detalle sin evento no inventa la relación", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(mockJson(detailResponse()));
    renderRoute(`/reservas/${ITEM.reserva_id}`);
    await screen.findByText("Trona junto a la mesa");
    expect(screen.queryByText("Evento asociado")).not.toBeInTheDocument();
  });

  it("detalle inexistente muestra error y request_id", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(mockJson({ ok: false, version: "1.0", api_version: "1.0",
      request_id: "REQ-NOT-FOUND", modo_seguro: true, datos_reales_modificados: false,
      error: { status: 404, code: "reserva_not_found", message: "Reserva no encontrada." } }, false, 404));
    renderRoute(`/reservas/${ITEM.reserva_id}`);
    expect(await screen.findByText("Reserva no encontrada.")).toBeInTheDocument();
    expect(screen.getByText("Request ID: REQ-NOT-FOUND")).toBeInTheDocument();
  });

  it("rechaza IDs hostiles sin petición ni URL arbitraria", async () => {
    const fetchMock = vi.spyOn(global, "fetch");
    for (const hostile of ["javascript:alert(1)", "..%2Fadmin", "https:%2F%2Fevil.test"]) {
      const view = renderRoute(`/reservas/${hostile}`);
      expect(await screen.findByText("Identificador de reserva no válido.")).toBeInTheDocument();
      view.unmount();
    }
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("cliente construye únicamente query segura y limita el límite", () => {
    expect(buildReservasQuery({ alcance: "hoy", q: "Ana & Co", fecha: "2030-05-20", estado: "CONFIRMADA", servicio: "COMIDA", limite: 999 }))
      .toBe("?alcance=hoy&q=Ana+%26+Co&fecha=2030-05-20&estado=CONFIRMADA&servicio=COMIDA&limite=100");
  });
});
