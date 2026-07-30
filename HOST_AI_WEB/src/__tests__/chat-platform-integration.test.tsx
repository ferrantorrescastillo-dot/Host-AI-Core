import userEvent from "@testing-library/user-event";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

describe("Chat como segunda interfaz de la plataforma", () => {
  beforeEach(() => {
    Object.defineProperty(Element.prototype, "scrollIntoView", {
      configurable: true,
      value: () => undefined,
    });
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("conserva el menú manual completo y navega desde Chat a Compras", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        ok: true,
        version: "1.0",
        api_version: "1.0",
        request_id: "REQ-CHAT-MODULES",
        modo_seguro: true,
        datos_reales_modificados: false,
        respuesta: "Consulta informativa. Hay 2 compras pendientes.",
        chat: {
          mensaje: "Consulta informativa. Hay 2 compras pendientes.",
          datos: {
            informativa: true,
            modo_lectura: true,
            navigation_request: { target_module: "COMPRAS" },
          },
        },
      }),
    } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);

    for (const label of [
      "Inicio", "Dashboard", "Chat", "Eventos", "Produccion",
      "Compras", "Stock", "Executive", "Configuracion",
    ]) {
      expect(screen.getByRole("link", { name: label })).toBeInTheDocument();
    }

    await userEvent.type(
      screen.getByLabelText("Mensaje para Host AI"),
      "¿Qué compras tengo pendientes?",
    );
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText(/Consulta informativa/)).toBeInTheDocument();
    expect(screen.getByText("Datos reales modificados: no")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("link", { name: "Abrir Compras" }));
    expect(await screen.findByRole("heading", { name: "Compras" })).toBeInTheDocument();
  });

  it("muestra el error controlado sin eliminar la navegación manual", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({
        ok: false,
        version: "1.0",
        api_version: "1.0",
        request_id: "REQ-CHAT-ERROR",
        modo_seguro: true,
        datos_reales_modificados: false,
        error: { message: "Chat temporalmente no disponible." },
      }),
    } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "estado");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("Chat temporalmente no disponible.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Executive" })).toBeInTheDocument();
  });
});
