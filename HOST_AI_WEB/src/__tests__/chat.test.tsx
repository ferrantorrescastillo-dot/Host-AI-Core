import userEvent from "@testing-library/user-event";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { HostAiApiError } from "../api/client";
import { chatService } from "../services/chatService";
import { App } from "../ui/App";

vi.mock("../services/chatService", () => ({
  chatService: {
    send: vi.fn(),
  },
}));

function chatSuccessPayload(overrides?: Partial<Record<string, unknown>>) {
  return {
    ok: true,
    version: "1.0",
    api_version: "1.0",
    request_id: "REQ-CHAT",
    modo_seguro: true,
    datos_reales_modificados: false,
    respuesta: "Respuesta exacta API",
    chat: { mensaje: "Respuesta exacta API" },
    contexto: { contexto_activo: "HOME" },
    ...overrides,
  };
}

const mockedChatService = vi.mocked(chatService);

describe("chat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    if (!(global as any).crypto) {
      (global as any).crypto = {
        randomUUID: () => "uuid-test",
      };
    }
    mockedChatService.send.mockResolvedValue(chatSuccessPayload());
  });

  it("render inicial con estado vacio", () => {
    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByText("Chat operativo")).toBeInTheDocument();
    expect(screen.getByText("Sin mensajes todavia.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
  });

  it("envio muestra respuesta correcta exacta", async () => {
    mockedChatService.send.mockResolvedValue(chatSuccessPayload({ respuesta: "Texto exacto devuelto por API." }));

    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "hola");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("Texto exacto devuelto por API.")).toBeInTheDocument();
    expect(screen.getByText("Request ID: REQ-CHAT")).toBeInTheDocument();
  });

  it("envia con Enter", async () => {
    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    const input = screen.getByLabelText("Mensaje para Host AI");
    await userEvent.type(input, "consulta{enter}");

    await waitFor(() => {
      expect(mockedChatService.send).toHaveBeenCalledTimes(1);
    });
  });

  it("Shift+Enter inserta salto de linea sin enviar", async () => {
    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    const input = screen.getByLabelText("Mensaje para Host AI") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "Linea 1" } });
    fireEvent.keyDown(input, { key: "Enter", code: "Enter", shiftKey: true });

    expect(mockedChatService.send).not.toHaveBeenCalled();
  });

  it("bloquea doble envio mientras hay peticion activa", async () => {
    let resolver: ((value: ReturnType<typeof chatSuccessPayload>) => void) | null = null;
    mockedChatService.send.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolver = resolve;
        }),
    );

    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    const input = screen.getByLabelText("Mensaje para Host AI");
    await userEvent.type(input, "hola");
    const button = screen.getByRole("button", { name: "Enviar" });
    await userEvent.click(button);
    await userEvent.click(button);

    expect(mockedChatService.send).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: "Enviando..." })).toBeDisabled();
    expect(screen.getByText("Cargando respuesta...")).toBeInTheDocument();

    resolver?.(chatSuccessPayload());

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Enviar" })).toBeEnabled();
    });
  });

  it("muestra error HTTP, request_id y permite reintentar", async () => {
    mockedChatService.send
      .mockRejectedValueOnce(
        new HostAiApiError("Error interno de API", {
          statusCode: 500,
          requestId: "REQ-HTTP-500",
          modoSeguro: true,
          datosRealesModificados: false,
        }),
      )
      .mockResolvedValueOnce(chatSuccessPayload({ request_id: "REQ-RECOVER", respuesta: "Recuperado" }));

    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "hola");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("Error HTTP")).toBeInTheDocument();
    expect(screen.getByText("Error interno de API")).toBeInTheDocument();
    expect(screen.getByText("Request ID: REQ-HTTP-500")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Reintentar" }));

    expect(await screen.findByText("Recuperado")).toBeInTheDocument();
    expect(mockedChatService.send).toHaveBeenCalledTimes(2);
  });

  it("muestra error de red", async () => {
    mockedChatService.send.mockRejectedValueOnce(new HostAiApiError("No se pudo conectar con la API."));

    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "hola");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("Error de red")).toBeInTheDocument();
  });

  it("muestra modo seguro con datos_reales_modificados=false", async () => {
    mockedChatService.send.mockResolvedValueOnce(
      chatSuccessPayload({
        modo_seguro: true,
        datos_reales_modificados: false,
      }),
    );

    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "hola");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("Datos reales modificados: no")).toBeInTheDocument();
  });

  it("muestra aviso visible si datos_reales_modificados=true", async () => {
    mockedChatService.send.mockResolvedValueOnce(
      chatSuccessPayload({
        modo_seguro: false,
        datos_reales_modificados: true,
      }),
    );

    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "hola");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("Alerta tecnica de seguridad")).toBeInTheDocument();
  });

  it("muestra indicador de carga mientras espera respuesta", async () => {
    let resolver: ((value: ReturnType<typeof chatSuccessPayload>) => void) | null = null;
    mockedChatService.send.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolver = resolve;
        }),
    );

    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "hola");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(screen.getByRole("status", { name: "Indicador de carga" })).toBeInTheDocument();

    resolver?.(chatSuccessPayload());

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Enviar" })).toBeEnabled();
    });
  });
});
