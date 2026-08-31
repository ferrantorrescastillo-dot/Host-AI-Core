import userEvent from "@testing-library/user-event";
import {
  fireEvent,
  cleanup,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import {
  beforeEach,
  afterEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import { HostAiApiError } from "../api/client";
import { chatService } from "../services/chatService";
import { App } from "../ui/App";

vi.mock("../services/chatService", () => ({
  chatService: {
    send: vi.fn(),
  },
}));

function chatSuccessPayload(
  overrides?: Partial<Record<string, unknown>>,
) {
  return {
    ok: true,
    version: "1.0",
    api_version: "1.0",
    request_id: "REQ-CHAT",
    modo_seguro: true,
    datos_reales_modificados: false,
    respuesta: "Respuesta exacta API",
    chat: {
      mensaje: "Respuesta exacta API",
    },
    contexto: {
      contexto_activo: "HOME",
    },
    ...overrides,
  };
}

type ChatResponse = ReturnType<typeof chatSuccessPayload>;

const mockedChatService = vi.mocked(chatService);

afterEach(() => {
  cleanup();
});

describe("chat", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    Object.defineProperty(Element.prototype, "scrollIntoView", {
      configurable: true,
      value: () => undefined,
    });
    Object.defineProperty(window, "open", {
      configurable: true,
      writable: true,
      value: vi.fn(() => null),
    });

    if (!(global as any).crypto) {
      (global as any).crypto = {
        randomUUID: () => "uuid-test",
      };
    }

    mockedChatService.send.mockResolvedValue(
      chatSuccessPayload(),
    );
  });

  it("render inicial con estado vacio", () => {
    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { name: "Host AI" }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", { name: "¿En qué puedo ayudarte?" }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", {
        name: "Enviar",
      }),
    ).toBeDisabled();
  });

  it("envio muestra respuesta correcta exacta", async () => {
    mockedChatService.send.mockResolvedValue(
      chatSuccessPayload({
        respuesta: "Texto exacto devuelto por API.",
      }),
    );

    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    await userEvent.type(
      screen.getByLabelText("Mensaje para Host AI"),
      "hola",
    );

    await userEvent.click(
      screen.getByRole("button", {
        name: "Enviar",
      }),
    );

    expect(
      await screen.findByText(
        "Texto exacto devuelto por API.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText("REQ-CHAT"),
    ).toBeInTheDocument();

    const firstCall = mockedChatService.send.mock.calls[0]?.[0] as { contexto?: Record<string, unknown> };
    expect(typeof firstCall?.contexto?.session_id).toBe("string");
    expect(String(firstCall.contexto?.session_id || "").length).toBeGreaterThan(0);
  });

  it("envia con Enter", async () => {
    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    const input = screen.getByLabelText(
      "Mensaje para Host AI",
    );

    await userEvent.type(input, "consulta{enter}");

    await waitFor(() => {
      expect(
        mockedChatService.send,
      ).toHaveBeenCalledTimes(1);
    });
  });

  it("Shift+Enter inserta salto de linea sin enviar", async () => {
    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    const input = screen.getByLabelText(
      "Mensaje para Host AI",
    ) as HTMLTextAreaElement;

    fireEvent.change(input, {
      target: {
        value: "Linea 1",
      },
    });

    fireEvent.keyDown(input, {
      key: "Enter",
      code: "Enter",
      shiftKey: true,
    });

    expect(
      mockedChatService.send,
    ).not.toHaveBeenCalled();
  });

  it("bloquea doble envio mientras hay peticion activa", async () => {
    let resolver:
      | ((value: ChatResponse) => void)
      | undefined;

    mockedChatService.send.mockImplementation(
      () =>
        new Promise<ChatResponse>((resolve) => {
          resolver = resolve;
        }),
    );

    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    const input = screen.getByLabelText(
      "Mensaje para Host AI",
    );

    await userEvent.type(input, "hola");

    const button = screen.getByRole("button", {
      name: "Enviar",
    });

    await userEvent.click(button);
    await userEvent.click(button);

    expect(
      mockedChatService.send,
    ).toHaveBeenCalledTimes(1);

    expect(
      screen.getByRole("button", {
        name: "Enviando...",
      }),
    ).toBeDisabled();

    expect(
      screen.getByText("Analizando"),
    ).toBeInTheDocument();

    if (resolver) {
      resolver(chatSuccessPayload());
    }

    await waitFor(() => {
      expect(
        screen.getByRole("button", {
          name: "Enviar",
        }),
      ).toBeDisabled();
      expect(
        screen.queryByText("Analizando"),
      ).not.toBeInTheDocument();
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
      .mockResolvedValueOnce(
        chatSuccessPayload({
          request_id: "REQ-RECOVER",
          respuesta: "Recuperado",
        }),
      );

    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    await userEvent.type(
      screen.getByLabelText("Mensaje para Host AI"),
      "hola",
    );

    await userEvent.click(
      screen.getByRole("button", {
        name: "Enviar",
      }),
    );

    expect(
      await screen.findByText("No he podido completar esta consulta."),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByText("Detalles"));
    expect(screen.getByText("Error interno de API")).toBeInTheDocument();
    expect(screen.getByText("REQ-HTTP-500")).toBeInTheDocument();

    await userEvent.click(
      screen.getByRole("button", {
        name: "Reintentar",
      }),
    );

    expect(
      await screen.findByText("Recuperado"),
    ).toBeInTheDocument();

    expect(
      mockedChatService.send,
    ).toHaveBeenCalledTimes(2);
  });

  it("muestra error de red", async () => {
    mockedChatService.send.mockRejectedValueOnce(
      new HostAiApiError(
        "No se pudo conectar con la API.",
      ),
    );

    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    await userEvent.type(
      screen.getByLabelText("Mensaje para Host AI"),
      "hola",
    );

    await userEvent.click(
      screen.getByRole("button", {
        name: "Enviar",
      }),
    );

    expect(
      await screen.findByText("No he podido completar esta consulta."),
    ).toBeInTheDocument();
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

    await userEvent.type(
      screen.getByLabelText("Mensaje para Host AI"),
      "hola",
    );

    await userEvent.click(
      screen.getByRole("button", {
        name: "Enviar",
      }),
    );

    expect(await screen.findByText("Respuesta exacta API")).toBeInTheDocument();
    await userEvent.click(screen.getByText("Detalles"));
    expect(screen.getByText("Datos reales modificados")).toBeInTheDocument();
    expect(screen.getAllByText("No").length).toBeGreaterThan(0);
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

    await userEvent.type(
      screen.getByLabelText("Mensaje para Host AI"),
      "hola",
    );

    await userEvent.click(
      screen.getByRole("button", {
        name: "Enviar",
      }),
    );

    expect(
      await screen.findByText(
        "Alerta técnica de seguridad",
      ),
    ).toBeInTheDocument();
  });

  it("muestra indicador de carga mientras espera respuesta", async () => {
    let resolver:
      | ((value: ChatResponse) => void)
      | undefined;

    mockedChatService.send.mockImplementation(
      () =>
        new Promise<ChatResponse>((resolve) => {
          resolver = resolve;
        }),
    );

    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>,
    );

    await userEvent.type(
      screen.getByLabelText("Mensaje para Host AI"),
      "hola",
    );

    await userEvent.click(
      screen.getByRole("button", {
        name: "Enviar",
      }),
    );

    expect(
      screen.getByRole("status", {
        name: "Indicador de carga",
      }),
    ).toBeInTheDocument();

    if (resolver) {
      resolver(chatSuccessPayload());
    }

    await waitFor(() => {
      expect(
        screen.getByRole("button", {
          name: "Enviar",
        }),
      ).toBeDisabled();
      expect(
        screen.queryByRole("status", {
          name: "Indicador de carga",
        }),
      ).not.toBeInTheDocument();
    });
  });

  it("muestra preview de CREATE y envía confirmación estructurada sin exponer token", async () => {
    mockedChatService.send.mockResolvedValueOnce(chatSuccessPayload({ respuesta: "Revisa la creación.", chat: { mensaje: "Revisa la creación.", datos: { preview: { nombre: "Boda Marta", fecha: "2030-09-12", pax: 30 }, confirmation_actions: [
      { action_id: "APPLY_PENDING_CATALOG_CREATE", action_context_id: "abcdef123456", label: "Confirmar", style: "primary" },
      { action_id: "DISCARD_PENDING_CATALOG_CREATE", action_context_id: "abcdef123456", label: "Cancelar", style: "secondary" },
    ] } } }) as any);
    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByRole("textbox"), "Crea un evento"); await userEvent.click(screen.getByRole("button", { name: /enviar/i }));
    expect(await screen.findByRole("heading", { name: "Crear registro" })).toBeInTheDocument();
    expect(screen.getByText("Boda Marta")).toBeInTheDocument(); expect(screen.queryByText(/abcdef123456/)).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Confirmar" }));
    expect(mockedChatService.send).toHaveBeenLastCalledWith(expect.objectContaining({ actionId: "APPLY_PENDING_CATALOG_CREATE", actionContextId: "abcdef123456" }));
  });

  it("prioriza pending_write y oculta el mensaje técnico simulado", async () => {
    mockedChatService.send.mockResolvedValueOnce(chatSuccessPayload({
      respuesta: "SIMULACION: la acción requiere confirmación explícita.",
      chat: { mensaje: "SIMULACION: la acción requiere confirmación explícita.", datos: {
        pending_write: { operation: "CREAR", domain: "EVENTO", confirmation_required: true, preview: { nombre: "Evento de prueba", fecha: "2030-09-12", hora_inicio: "18:00", pax: 20 } },
        confirmation_actions: [
          { action_id: "APPLY_PENDING_CATALOG_CREATE", action_context_id: "abcdef123456", label: "Confirmar", style: "primary" },
          { action_id: "DISCARD_PENDING_CATALOG_CREATE", action_context_id: "abcdef123456", label: "Cancelar", style: "secondary" },
        ],
      } },
    }) as any);
    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByRole("textbox"), "Crea un evento");
    await userEvent.click(screen.getByRole("button", { name: /enviar/i }));
    expect(await screen.findByRole("heading", { name: "Crear evento" })).toBeInTheDocument();
    expect(screen.getByText("Evento de prueba")).toBeInTheDocument();
    expect(screen.getByText("18:00")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirmar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancelar" })).toBeInTheDocument();
    expect(screen.queryByText(/SIMULACION:/)).not.toBeInTheDocument();
  });

  it("renderiza los grupos de compra estructurados del contrato del chat", async () => {
    mockedChatService.send.mockResolvedValueOnce(chatSuccessPayload({
      chat: { mensaje: "He calculado la compra neta.", datos: { purchase_groups: [{
        proveedor: "SARDA", estado_pedido: "ninguno",
        articulos: [{ articulo_id: "ART-1", nombre: "Azúcar", cantidad: .1, unidad: "kg" }],
        action: { type: "PREPARE_ORDER", label: "texto no confiable", menu_id: "MENU-1" },
      }] } },
    }));
    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Calcula la compra");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByRole("heading", { name: "SARDA" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Preparar pedido" })).toHaveAttribute("href", "/menus?menu_id=MENU-1&view=compra");
    expect(screen.queryByText("texto no confiable")).not.toBeInTheDocument();
  });
});
