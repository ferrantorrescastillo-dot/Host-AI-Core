import userEvent from "@testing-library/user-event";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

function popupWindow() {
  let closed = false;
  return {
    opener: window,
    get closed() { return closed; },
    location: { replace: vi.fn() },
    close: vi.fn(() => { closed = true; }),
  } as unknown as Window;
}

function response(uiAction?: Record<string, unknown>) {
  return {
    ok: true, json: async () => ({
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-RESERVAS-R3",
      modo_seguro: true, datos_reales_modificados: false, respuesta: "Consulta de reservas completada.",
      chat: { mensaje: "Consulta de reservas completada.", datos: uiAction ? { ui_action: uiAction } : { solo_lectura: true } },
    }),
  } as Response;
}

async function send() {
  render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
  await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Enseñame las reservas");
  await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
  await screen.findByText("Consulta de reservas completada.");
}

describe("Chat Reservas R3", () => {
  beforeEach(() => {
    vi.spyOn(console, "debug").mockImplementation(() => undefined);
    Object.defineProperty(Element.prototype, "scrollIntoView", { configurable: true, value: () => undefined });
  });
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it.each([
    [{ type: "OPEN_VIEW", target: "RESERVAS", id: "", view: "LISTADO", label: "Reservas" }, "/reservas"],
    [{ type: "OPEN_VIEW", target: "RESERVAS", id: "RES-ABCDEF123456", view: "DETALLE", label: "Marta" }, "/reservas/RES-ABCDEF123456"],
    [{ type: "OPEN_VIEW", target: "EVENTOS", id: "", view: "LISTADO", label: "Eventos" }, "/eventos"],
    [{ type: "OPEN_VIEW", target: "ARTICULO", id: "ART-1", view: "FICHA", label: "Arroz" }, "/articulos/ART-1"],
    [{ type: "OPEN_VIEW", target: "MENU", id: "MENU-1", view: "DETALLE", label: "Diario" }, "/menus?menu_id=MENU-1"],
    [{ type: "OPEN_VIEW", target: "PRODUCCION", id: "PLAN-1", view: "PLAN", label: "Plan" }, "/produccion?plan_id=PLAN-1"],
  ])("consume la ventana reservada para el mapping cerrado %#", async (action, route) => {
    const popup = popupWindow();
    vi.spyOn(window, "open").mockReturnValue(popup);
    vi.spyOn(global, "fetch").mockResolvedValue(response(action));
    await send();
    expect(popup.location.replace).toHaveBeenCalledWith(route);
    expect(popup.close).not.toHaveBeenCalled();
    expect(popup.opener).toBeNull();
  });

  it("abre el detalle canónico de lote en la pestaña reservada al pulsar la acción", async () => {
    const reserved = popupWindow();
    const popup = popupWindow();
    vi.spyOn(window, "open").mockReturnValueOnce(reserved).mockReturnValueOnce(popup);
    vi.spyOn(global, "fetch").mockResolvedValue(response({ type: "OPEN_VIEW", target: "LOTE", id: "LOT-ABC123", view: "DETALLE", label: "Lote" }));
    await send();
    await userEvent.click(screen.getByRole("button", { name: "Abrir lote" }));
    expect(popup.location.replace).toHaveBeenCalledWith("/stock?lote_id=LOT-ABC123");
    expect(popup.opener).toBeNull();
  });

  it.each([
    { type: "OPEN_VIEW", target: "RESERVAS", id: "../../evil", view: "DETALLE", url: "https://evil.example" },
    { type: "OPEN_VIEW", target: "RESERVAS", id: "RES-ABCDEF123456", view: "EDITAR", pathname: "/evil" },
    { type: "OPEN_VIEW", target: "LOTE", id: "../../evil", view: "DETALLE", url: "https://evil.example" },
  ])("rechaza payload hostil o vista no soportada %#", async (action) => {
    const popup = popupWindow();
    vi.spyOn(window, "open").mockReturnValue(popup);
    vi.spyOn(global, "fetch").mockResolvedValue(response(action));
    await send();
    await waitFor(() => expect(popup.close).toHaveBeenCalled());
    expect(popup.location.replace).not.toHaveBeenCalled();
  });

  it("cierra la ventana reservada ante READ sin UI_ACTION", async () => {
    const popup = popupWindow();
    vi.spyOn(window, "open").mockReturnValue(popup);
    vi.spyOn(global, "fetch").mockResolvedValue(response());
    await send();
    await waitFor(() => expect(popup.close).toHaveBeenCalled());
    expect(popup.location.replace).not.toHaveBeenCalled();
  });
});
