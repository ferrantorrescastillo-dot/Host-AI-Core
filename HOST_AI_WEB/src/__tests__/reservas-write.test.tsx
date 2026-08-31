import userEvent from "@testing-library/user-event";
import { cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

const item = { reserva_id: "RES-ABCDEF123456", nombre_cliente: "Marta", fecha: "2030-05-20", hora: "21:00", pax: 4, estado: "PENDIENTE", servicio: "CENA", evento_id: null, observaciones: "Mesa tranquila" };
const envelope = (extra: object) => ({ ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-R4", modo_seguro: true, datos_reales_modificados: false, ...extra });
const ok = (data: object) => Promise.resolve({ ok: true, json: async () => data } as Response);

describe("Reservas R4 write seguro", () => {
  beforeEach(() => vi.spyOn(console, "debug").mockImplementation(() => undefined));
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it("crea mediante formulario, preview y confirmación sin optimistic write", async () => {
    const fetch = vi.spyOn(global, "fetch")
      .mockImplementationOnce(() => ok(envelope({ reservas: { items: [], total: 0 } })))
      .mockImplementationOnce(() => ok(envelope({ estado: "LISTO_PARA_CONFIRMAR", operacion: "CREAR", reserva_id: null, antes: null, propuesto: item, preview_token: "opaque", expira_en: "2030-01-01", requiere_confirmacion: true })))
      .mockImplementationOnce(() => ok(envelope({ datos_reales_modificados: true, estado: "CONFIRMADO", operacion: "CREAR", reserva: item, idempotente: false })))
      .mockImplementationOnce(() => ok(envelope({ reservas: { items: [item], total: 1 } })));
    render(<MemoryRouter initialEntries={["/reservas"]}><App /></MemoryRouter>);
    await screen.findByText("No hay reservas registradas.");
    await userEvent.click(screen.getByRole("button", { name: "Nueva reserva" }));
    const panel = screen.getByLabelText("Nueva reserva reserva");
    expect(screen.queryByLabelText(/teléfono/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument();
    await userEvent.type(within(panel).getByLabelText("Nombre del cliente"), "Marta");
    await userEvent.type(within(panel).getByLabelText("Fecha"), "2030-05-20");
    await userEvent.type(within(panel).getByLabelText("Hora"), "21:00");
    await userEvent.clear(within(panel).getByLabelText("Personas")); await userEvent.type(within(panel).getByLabelText("Personas"), "4");
    await userEvent.selectOptions(within(panel).getByLabelText("Servicio"), "CENA");
    await userEvent.click(within(panel).getByRole("button", { name: "Revisar cambios" }));
    expect(await screen.findByRole("dialog", { name: "Confirmar operación de reserva" })).toBeInTheDocument();
    expect(screen.getByText("No hay reservas registradas.")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Confirmar operación" }));
    expect(await screen.findByText("Marta")).toBeInTheDocument();
    expect(fetch.mock.calls[1][1]?.method).toBe("POST");
    expect(fetch.mock.calls[2][1]?.body).toContain("opaque");
  });

  it("permite cancelar un preview sin escribir", async () => {
    const fetch = vi.spyOn(global, "fetch")
      .mockImplementationOnce(() => ok(envelope({ reservas: { items: [], total: 0 } })))
      .mockImplementationOnce(() => ok(envelope({ estado: "LISTO_PARA_CONFIRMAR", operacion: "CREAR", reserva_id: null, antes: null, propuesto: item, preview_token: "opaque", expira_en: "2030", requiere_confirmacion: true })));
    render(<MemoryRouter initialEntries={["/reservas"]}><App /></MemoryRouter>); await screen.findByText("No hay reservas registradas.");
    await userEvent.click(screen.getByRole("button", { name: "Nueva reserva" }));
    const panel = screen.getByLabelText("Nueva reserva reserva");
    for (const [label, value] of [["Nombre del cliente", "Marta"], ["Fecha", "2030-05-20"], ["Hora", "21:00"]]) await userEvent.type(within(panel).getByLabelText(label), value);
    await userEvent.click(within(panel).getByRole("button", { name: "Revisar cambios" }));
    await userEvent.click(await screen.findByRole("button", { name: "Cancelar preview" }));
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("button", { name: "Revisar cambios" })).toBeInTheDocument();
  });

  it("muestra edición y transiciones válidas en detalle y no escribe antes del preview", async () => {
    const confirmed = { ...item, estado: "CONFIRMADA" };
    const fetch = vi.spyOn(global, "fetch").mockImplementationOnce(() => ok(envelope({ reserva: confirmed }))).mockImplementationOnce(() => ok(envelope({ estado: "LISTO_PARA_CONFIRMAR", operacion: "NO_SHOW", reserva_id: item.reserva_id, antes: confirmed, propuesto: { ...confirmed, estado: "NO_SHOW" }, preview_token: "no-show", expira_en: "2030", requiere_confirmacion: true })));
    render(<MemoryRouter initialEntries={[`/reservas/${item.reserva_id}`]}><App /></MemoryRouter>); await screen.findByRole("heading", { name: "Marta" });
    expect(screen.getByRole("button", { name: "Editar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancelar reserva" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Marcar no-show" }));
    await userEvent.click(screen.getByRole("button", { name: "Revisar cambios" }));
    expect(await screen.findByText("NO_SHOW")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it("expone error stale sin cambiar la vista", async () => {
    vi.spyOn(global, "fetch").mockImplementationOnce(() => ok(envelope({ reserva: item }))).mockImplementationOnce(() => ok(envelope({ estado: "LISTO_PARA_CONFIRMAR", operacion: "CANCELAR", reserva_id: item.reserva_id, antes: item, propuesto: { ...item, estado: "CANCELADA" }, preview_token: "stale", expira_en: "2030", requiere_confirmacion: true }))).mockResolvedValueOnce({ ok: false, status: 409, json: async () => ({ ...envelope({}), ok: false, error: { status: 409, code: "stale_preview", message: "La reserva ha cambiado." } }) } as Response);
    render(<MemoryRouter initialEntries={[`/reservas/${item.reserva_id}`]}><App /></MemoryRouter>); await screen.findByRole("heading", { name: "Marta" });
    await userEvent.click(screen.getByRole("button", { name: "Cancelar reserva" })); await userEvent.click(screen.getByRole("button", { name: "Revisar cambios" })); await userEvent.click(await screen.findByRole("button", { name: "Confirmar operación" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("La reserva ha cambiado.");
    expect(screen.getByText("PENDIENTE")).toBeInTheDocument();
  });

  it("completa una CONFIRMADA solo despuÃ©s de preview y confirmaciÃ³n", async () => {
    const confirmed = { ...item, estado: "CONFIRMADA" };
    const completed = { ...confirmed, estado: "COMPLETADA" };
    const fetch = vi.spyOn(global, "fetch")
      .mockImplementationOnce(() => ok(envelope({ reserva: confirmed })))
      .mockImplementationOnce(() => ok(envelope({ estado: "LISTO_PARA_CONFIRMAR", operacion: "COMPLETAR", reserva_id: item.reserva_id, antes: confirmed, propuesto: completed, preview_token: "complete-1", expira_en: "2030", requiere_confirmacion: true })))
      .mockImplementationOnce(() => ok(envelope({ estado: "LISTO_PARA_CONFIRMAR", operacion: "COMPLETAR", reserva_id: item.reserva_id, antes: confirmed, propuesto: completed, preview_token: "complete-2", expira_en: "2030", requiere_confirmacion: true })))
      .mockImplementationOnce(() => ok(envelope({ datos_reales_modificados: true, estado: "CONFIRMADO", operacion: "COMPLETAR", reserva: completed, idempotente: false })));
    render(<MemoryRouter initialEntries={[`/reservas/${item.reserva_id}`]}><App /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Marta" });
    for (const label of ["Editar", "Cancelar reserva", "Marcar no-show", "Completar"]) expect(screen.getByRole("button", { name: label })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Completar" }));
    await userEvent.click(screen.getByRole("button", { name: "Revisar cambios" }));
    expect(await screen.findByText("COMPLETADA")).toBeInTheDocument();
    expect(screen.getByText("CONFIRMADA")).toBeInTheDocument();
    expect(JSON.parse(String(fetch.mock.calls[1][1]?.body))).toMatchObject({ operacion: "COMPLETAR", reserva_id: item.reserva_id, payload: {} });
    expect(fetch).toHaveBeenCalledTimes(2);

    await userEvent.click(screen.getByRole("button", { name: "Cancelar preview" }));
    expect(screen.getByText("CONFIRMADA")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledTimes(2);
    await userEvent.click(screen.getByRole("button", { name: "Revisar cambios" }));
    await screen.findByText("COMPLETADA");
    const apply = screen.getByRole("button", { name: /Confirmar operaci/ });
    await userEvent.dblClick(apply);
    expect(await screen.findByText("COMPLETADA")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledTimes(4);
    for (const label of ["Confirmar reserva", "Cancelar reserva", "Marcar no-show", "Completar"]) {
      expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    }
    expect(screen.getByRole("button", { name: "Editar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Eliminar" })).toBeInTheDocument();
  });

  it("muestra error seguro de preview al completar y no reintenta", async () => {
    const confirmed = { ...item, estado: "CONFIRMADA" };
    const fetch = vi.spyOn(global, "fetch")
      .mockImplementationOnce(() => ok(envelope({ reserva: confirmed })))
      .mockResolvedValueOnce({ ok: false, status: 409, json: async () => ({ ...envelope({}), ok: false, error: { status: 409, code: "stale_preview", message: "La reserva ha cambiado." } }) } as Response);
    render(<MemoryRouter initialEntries={[`/reservas/${item.reserva_id}`]}><App /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Marta" });
    await userEvent.click(screen.getByRole("button", { name: "Completar" }));
    const review = screen.getByRole("button", { name: "Revisar cambios" });
    await userEvent.click(review);
    expect(await screen.findByRole("alert")).toHaveTextContent("La reserva ha cambiado.");
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(review).toBeEnabled();
    expect(screen.getByText("CONFIRMADA")).toBeInTheDocument();
  });

  it("muestra un 403 seguro, no reintenta y rehabilita Revisar cambios", async () => {
    const fetch = vi.spyOn(global, "fetch")
      .mockImplementationOnce(() => ok(envelope({ reserva: item })))
      .mockResolvedValueOnce({ ok: false, status: 403, json: async () => ({ ...envelope({}), ok: false, error: { status: 403, code: "unauthorized", message: "El actor no estÃ¡ autorizado." } }) } as Response);
    render(<MemoryRouter initialEntries={[`/reservas/${item.reserva_id}`]}><App /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Marta" });
    await userEvent.click(screen.getByRole("button", { name: "Confirmar reserva" }));
    const review = screen.getByRole("button", { name: "Revisar cambios" });
    await userEvent.click(review);
    expect(await screen.findByRole("alert")).toHaveTextContent("El actor no estÃ¡ autorizado.");
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(review).toBeEnabled();
  });

  it("no envÃ­a identidad, tenant ni scopes desde el bundle web", async () => {
    const fetch = vi.spyOn(global, "fetch")
      .mockImplementationOnce(() => ok(envelope({ reserva: item })))
      .mockImplementationOnce(() => ok(envelope({ estado: "LISTO_PARA_CONFIRMAR", operacion: "CONFIRMAR", reserva_id: item.reserva_id, antes: item, propuesto: { ...item, estado: "CONFIRMADA" }, preview_token: "opaque", expira_en: "2030", requiere_confirmacion: true })));
    render(<MemoryRouter initialEntries={[`/reservas/${item.reserva_id}`]}><App /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Marta" });
    await userEvent.click(screen.getByRole("button", { name: "Confirmar reserva" }));
    await userEvent.click(screen.getByRole("button", { name: "Revisar cambios" }));
    await screen.findByRole("dialog", { name: /Confirmar operaci/ });
    const request = fetch.mock.calls[1][1];
    const serialized = JSON.stringify(request);
    expect(serialized).not.toMatch(/HOST_AI_INTERNAL|tenant|reservas:(preview|write)|user_id/i);
  });

  it.each(["CANCELADA", "NO_SHOW", "COMPLETADA"])("mantiene editar y eliminar para estado terminal %s", async (estado) => {
    vi.spyOn(global, "fetch").mockImplementationOnce(() => ok(envelope({ reserva: { ...item, estado } })));
    render(<MemoryRouter initialEntries={[`/reservas/${item.reserva_id}`]}><App /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Marta" });
    expect(screen.getByRole("button", { name: "Editar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Eliminar" })).toBeInTheDocument();
    for (const label of ["Confirmar reserva", "Cancelar reserva", "Marcar no-show", "Completar"]) expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    expect(screen.getByText(estado)).toBeInTheDocument();
  });

  it("eliminar una terminal exige preview y cancelar no confirma WRITE", async () => {
    const cancelled = { ...item, estado: "CANCELADA" };
    const fetch = vi.spyOn(global, "fetch")
      .mockImplementationOnce(() => ok(envelope({ reserva: cancelled })))
      .mockImplementationOnce(() => ok(envelope({ estado: "LISTO_PARA_CONFIRMAR", operacion: "ELIMINAR", reserva_id: item.reserva_id, antes: cancelled, propuesto: { ...cancelled, eliminada: true }, preview_token: "delete-preview", expira_en: "2030", requiere_confirmacion: true })));
    render(<MemoryRouter initialEntries={[`/reservas/${item.reserva_id}`]}><App /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Marta" });
    await userEvent.click(screen.getByRole("button", { name: "Eliminar" }));
    await userEvent.click(screen.getByRole("button", { name: "Revisar cambios" }));
    expect(await screen.findByRole("heading", { name: "Eliminar reserva" })).toBeInTheDocument();
    expect(screen.getByText(/baja lógica|sin borrar físicamente/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Cancelar preview" }));
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it.each([
    ["PENDIENTE", ["Editar", "Eliminar", "Confirmar reserva", "Cancelar reserva"]],
    ["CONFIRMADA", ["Editar", "Eliminar", "Cancelar reserva", "Marcar no-show", "Completar"]],
  ])("conserva las acciones válidas para %s", async (estado, labels) => {
    vi.spyOn(global, "fetch").mockImplementationOnce(() => ok(envelope({ reserva: { ...item, estado } })));
    render(<MemoryRouter initialEntries={[`/reservas/${item.reserva_id}`]}><App /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Marta" });
    for (const label of labels) expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
    if (estado === "PENDIENTE") expect(screen.queryByRole("button", { name: "Completar" })).not.toBeInTheDocument();
  });
});
