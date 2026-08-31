import userEvent from "@testing-library/user-event";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

function popupWindow() {
  let closed = false;
  const popup = {
    opener: window,
    get closed() { return closed; },
    location: { replace: vi.fn() },
    close: vi.fn(() => { closed = true; }),
  };
  return popup as unknown as Window;
}

describe("Chat como segunda interfaz de la plataforma", () => {
  beforeEach(() => {
    vi.spyOn(console, "debug").mockImplementation(() => undefined);
    Object.defineProperty(Element.prototype, "scrollIntoView", {
      configurable: true,
      value: () => undefined,
    });
    Object.defineProperty(window, "open", {
      configurable: true,
      writable: true,
      value: vi.fn(() => null),
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
    await userEvent.click(screen.getByText("Detalles"));
    expect(screen.getByText("Datos reales modificados")).toBeInTheDocument();
    const comprasLink = screen.getByRole("link", { name: "Abrir en Compras" });
    expect(comprasLink).toHaveAttribute("href", "/compras");
    await userEvent.click(comprasLink);
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

  it("abre el borrador en otra pestaña y conserva el chat y su scroll", async () => {
    const reservedPopup = popupWindow();
    const destinationPopup = popupWindow();
    const open = vi.spyOn(window, "open")
      .mockReturnValueOnce(reservedPopup)
      .mockReturnValueOnce(destinationPopup);
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-DRAFT",
      modo_seguro: true, datos_reales_modificados: false, respuesta: "Compra necesaria.",
      chat: { mensaje: "Compra necesaria.", datos: {
        purchase_groups: [{ proveedor: "SARDA", estado_pedido: "draft", articulos: [{ articulo_id: "ART-AZUCAR", nombre: "Azúcar", cantidad: .1, unidad: "kg" }], action: { type: "OPEN_ORDER", pedido_id: "PED-0AD463508C", label: "Abrir pedido" } }],
        ui_action: { type: "OPEN_VIEW", target: "COMPRA", id: "PED-0AD463508C", view: "PEDIDO", label: "Abrir pedido" },
      } },
    }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Analiza la compra");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    const action = await screen.findByRole("button", { name: "Abrir borrador" });
    const conversation = screen.getByLabelText("Conversación");
    conversation.scrollTop = 137;

    await userEvent.click(action);

    expect(open).toHaveBeenCalledTimes(2);
    expect(open).toHaveBeenLastCalledWith("", "_blank");
    expect(destinationPopup.opener).toBeNull();
    expect(destinationPopup.location.replace).toHaveBeenCalledWith("/compras?pedido_id=PED-0AD463508C");
    expect(screen.getByRole("link", { name: "Chat" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByText("Analiza la compra")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Compra necesaria/ })).toBeInTheDocument();
    expect(conversation.scrollTop).toBe(137);
  });

  it.each([
    ["leche", "/articulos?q=leche"],
    ["Patata Monalisa", "/articulos?q=Patata+Monalisa"],
  ])("abre en Artículos con la búsqueda segura %s", async (termino, ruta) => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        ok: true,
        version: "1.0",
        api_version: "1.0",
        request_id: "REQ-CHAT-CATALOGO",
        modo_seguro: true,
        datos_reales_modificados: false,
        respuesta: "Resultados del catálogo.",
        chat: {
          mensaje: "Resultados del catálogo.",
          datos: {
            navigation_request: {
              target_module: "CATALOGO",
              filter_data: { termino },
            },
          },
        },
      }),
    } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), `Busca artículos de ${termino}`);
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    const link = await screen.findByRole("link", { name: "Abrir en Artículos" });
    expect(link).toHaveAttribute("href", ruta);
  });

  it.each([
    ["receta", "RECETA", "Receta"],
    ["escandallo", "ESCANDALLO", "Escandallo"],
  ])("abre la elaboración %s en nueva pestaña y conserva el Chat", async (tab, view, heading) => {
    const popup = popupWindow();
    const open = vi.spyOn(window, "open").mockReturnValue(popup);
    const mock = vi.spyOn(global, "fetch").mockResolvedValueOnce({ ok: true, json: async () => ({
        ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-OPEN-VIEW",
        modo_seguro: true, datos_reales_modificados: false, respuesta: "Te he abierto la ficha.",
        chat: { mensaje: "Te he abierto la ficha.", datos: { ui_action: {
          type: "OPEN_VIEW", target: "ELABORACION", id: "REC-ENSALADILLA", view,
          label: "Ensaladilla de gamba", url: "javascript:alert(1)",
        } } },
      }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), `Enséñame ${tab}`);
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText(`Abierto en una nueva pestaña: Ensaladilla de gamba · ${heading}`)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Host AI" })).toBeInTheDocument();
    expect(open).toHaveBeenCalledWith(
      "", "_blank",
    );
    expect(popup.opener).toBeNull();
    expect(popup.location.replace).toHaveBeenCalledWith(`/biblioteca/elaboraciones/REC-ENSALADILLA?tab=${tab}`);
    expect(mock).toHaveBeenCalledTimes(1);
  });

  it("conserva historial y permite una segunda UI action en otra pestaña", async () => {
    const firstPopup = popupWindow();
    const secondPopup = popupWindow();
    const open = vi.spyOn(window, "open")
      .mockReturnValueOnce(firstPopup)
      .mockReturnValueOnce(secondPopup);
    vi.spyOn(global, "fetch")
      .mockResolvedValueOnce({ ok: true, json: async () => ({
        ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-1", modo_seguro: true, datos_reales_modificados: false,
        respuesta: "Escandallo abierto.",
        chat: { mensaje: "Escandallo abierto.", datos: { ui_action: {
          type: "OPEN_VIEW", target: "ELABORACION", id: "REC-ENSALADILLA", view: "ESCANDALLO", label: "Ensaladilla de gamba",
        } } },
      }) } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => ({
        ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-2", modo_seguro: true, datos_reales_modificados: false,
        respuesta: "Receta abierta.",
        chat: { mensaje: "Receta abierta.", datos: { ui_action: {
          type: "OPEN_VIEW", target: "ELABORACION", id: "REC-ENSALADILLA", view: "RECETA", label: "Ensaladilla de gamba",
        } } },
      }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    const input = screen.getByLabelText("Mensaje para Host AI");
    await userEvent.type(input, "Enséñame el escandallo");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await screen.findByText("Escandallo abierto.");
    await userEvent.type(input, "Enséñame la receta");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("Receta abierta.")).toBeInTheDocument();
    expect(screen.getByText("Enséñame el escandallo")).toBeInTheDocument();
    expect(screen.getByText("Escandallo abierto.")).toBeInTheDocument();
    expect(open).toHaveBeenCalledTimes(2);
    expect(firstPopup.location.replace).toHaveBeenCalledWith(
      "/biblioteca/elaboraciones/REC-ENSALADILLA?tab=escandallo",
    );
    expect(secondPopup.location.replace).toHaveBeenCalledWith(
      "/biblioteca/elaboraciones/REC-ENSALADILLA?tab=receta",
    );
  });

  it("muestra fallback seguro cuando el navegador bloquea la pestaña", async () => {
    const popup = popupWindow();
    const open = vi.spyOn(window, "open").mockReturnValueOnce(null).mockReturnValueOnce(popup);
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-BLOCKED", modo_seguro: true, datos_reales_modificados: false,
      respuesta: "Ficha preparada.",
      chat: { mensaje: "Ficha preparada.", datos: { ui_action: {
        type: "OPEN_VIEW", target: "ELABORACION", id: "REC-ENSALADILLA", view: "ESCANDALLO", label: "Ensaladilla de gamba",
      } } },
    }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Muéstrame el escandallo");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("No se pudo abrir automáticamente. Usa el botón para abrir la ficha.")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Abrir Escandallo" }));
    expect(open).toHaveBeenLastCalledWith(
      "", "_blank",
    );
    expect(popup.location.replace).toHaveBeenCalledWith(
      "/biblioteca/elaboraciones/REC-ENSALADILLA?tab=escandallo",
    );
  });

  it("reserva la pestaña durante el gesto y cierra el handle si no llega OPEN_VIEW", async () => {
    const popup = popupWindow();
    const open = vi.spyOn(window, "open").mockReturnValue(popup);
    let resolveResponse!: (value: Response) => void;
    const response = new Promise<Response>((resolve) => { resolveResponse = resolve; });
    vi.spyOn(global, "fetch").mockReturnValue(response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "¿Cuánto cuesta?");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(open).toHaveBeenCalledWith("", "_blank");
    expect(popup.opener).toBeNull();
    expect(popup.location.replace).not.toHaveBeenCalled();

    resolveResponse({ ok: true, json: async () => ({
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-READ",
      modo_seguro: true, datos_reales_modificados: false, respuesta: "Cuesta 5 euros.",
      chat: { mensaje: "Cuesta 5 euros.", datos: {} },
    }) } as Response);

    expect(await screen.findByText("Cuesta 5 euros.")).toBeInTheDocument();
    expect(popup.close).toHaveBeenCalledOnce();
  });

  it("cierra la pestaña reservada cuando una búsqueda de stock resulta ambigua", async () => {
    const popup = popupWindow();
    vi.spyOn(window, "open").mockReturnValue(popup);
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-GAMBA-AMBIGUA",
      modo_seguro: true, datos_reales_modificados: false,
      respuesta: "He encontrado varios artículos con gamba. ¿A cuál te refieres?",
      chat: { mensaje: "He encontrado varios artículos con gamba. ¿A cuál te refieres?", datos: {
        estado: "AMBIGUO",
        candidatos: [
          { article_id: "ART000006", nombre: "A.P BROCHETA DE GAMBA XL" },
          { article_id: "ART000351", nombre: "Ensaladilla de Gamba" },
          { article_id: "ART000323", nombre: "Gamba paella" },
        ],
      } },
    }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Enséñame el stock de gamba.");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText(/He encontrado varios artículos con gamba/)).toBeInTheDocument();
    expect(popup.location.replace).not.toHaveBeenCalled();
    expect(popup.close).toHaveBeenCalledOnce();
    expect(screen.getByRole("heading", { name: "Host AI" })).toBeInTheDocument();
  });

  it("mantiene el handle hasta intentar el cierre y audita su eliminación posterior", async () => {
    const popup = popupWindow();
    const debug = vi.spyOn(console, "debug").mockImplementation(() => undefined);
    vi.spyOn(window, "open").mockReturnValue(popup);
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-CLEANUP-ORDER",
      modo_seguro: true, datos_reales_modificados: false, respuesta: "Respuesta ambigua.",
      chat: { mensaje: "Respuesta ambigua.", datos: { estado: "AMBIGUO" } },
    }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Enséñame el stock de gamba");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await screen.findByText("Respuesta ambigua.");

    const cleanup = debug.mock.calls.find((call) => (
      call[0] === "host_ai_reserved_window"
      && (call[1] as { event?: string }).event === "cleanup"
    ))?.[1] as Record<string, unknown>;
    expect(popup.close).toHaveBeenCalledOnce();
    expect(cleanup).toMatchObject({
      reservedWindowExists: true,
      reservedWindowConsumed: false,
      reservedWindowClosedBeforeCleanup: false,
      closeAttempted: true,
      closeSucceeded: true,
      closedAfter: true,
      handleRemoved: true,
    });
    const auditOrder = debug.mock.invocationCallOrder[debug.mock.invocationCallOrder.length - 1] ?? 0;
    expect(vi.mocked(popup.close).mock.invocationCallOrder[0]).toBeLessThan(auditOrder);
  });

  it("intenta cerrar aunque WindowProxy.closed no sea observable", async () => {
    const close = vi.fn();
    const popup = {
      opener: window,
      get closed() { throw new DOMException("WindowProxy unavailable"); },
      location: { replace: vi.fn() },
      close,
    } as unknown as Window;
    const debug = vi.spyOn(console, "debug").mockImplementation(() => undefined);
    vi.spyOn(window, "open").mockReturnValue(popup);
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-UNRELIABLE-CLOSED",
      modo_seguro: true, datos_reales_modificados: false, respuesta: "Solo lectura.",
      chat: { mensaje: "Solo lectura.", datos: {} },
    }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Consulta informativa");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await screen.findByText("Solo lectura.");

    expect(close).toHaveBeenCalledOnce();
    expect(debug.mock.calls.some((call) => (
      call[0] === "host_ai_reserved_window"
      && (call[1] as { event?: string; closeAttempted?: boolean }).event === "cleanup"
      && (call[1] as { closeAttempted?: boolean }).closeAttempted === true
    ))).toBe(true);
  });

  it("navega OPEN_VIEW aunque WindowProxy.closed no sea observable", async () => {
    const close = vi.fn();
    const popup = {
      opener: window,
      get closed() { throw new DOMException("WindowProxy unavailable"); },
      location: { replace: vi.fn() },
      close,
    } as unknown as Window;
    vi.spyOn(window, "open").mockReturnValue(popup);
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-UNOBSERVABLE-OPEN",
      modo_seguro: true, datos_reales_modificados: false,
      respuesta: "Te he abierto la receta.",
      chat: { mensaje: "Te he abierto la receta.", datos: { ui_action: {
        type: "OPEN_VIEW", target: "ELABORACION", id: "REC-ENSALADILLA", view: "RECETA", label: "Ensaladilla",
      } } },
    }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Enséñame la receta");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("Te he abierto la receta.")).toBeInTheDocument();
    expect(popup.location.replace).toHaveBeenCalledWith("/biblioteca/elaboraciones/REC-ENSALADILLA?tab=receta");
    expect(close).not.toHaveBeenCalled();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("el error de close no rompe el turno y elimina el handle", async () => {
    const popup = popupWindow();
    vi.mocked(popup.close).mockImplementation(() => { throw new DOMException("close blocked"); });
    const debug = vi.spyOn(console, "debug").mockImplementation(() => undefined);
    vi.spyOn(window, "open").mockReturnValue(popup);
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-CLOSE-ERROR",
      modo_seguro: true, datos_reales_modificados: false, respuesta: "Turno completado.",
      chat: { mensaje: "Turno completado.", datos: {} },
    }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Consulta");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("Turno completado.")).toBeInTheDocument();
    expect(popup.close).toHaveBeenCalledOnce();
    expect(debug.mock.calls.some((call) => (
      call[0] === "host_ai_reserved_window"
      && (call[1] as { event?: string; closeSucceeded?: boolean; handleRemoved?: boolean }).event === "cleanup"
      && (call[1] as { closeSucceeded?: boolean }).closeSucceeded === false
      && (call[1] as { handleRemoved?: boolean }).handleRemoved === true
    ))).toBe(true);
  });

  it("tolera un handle que ya informa closed=true y aun ejecuta cleanup terminal", async () => {
    const close = vi.fn();
    const popup = {
      opener: window, closed: true, location: { replace: vi.fn() }, close,
    } as unknown as Window;
    vi.spyOn(window, "open").mockReturnValue(popup);
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-ALREADY-CLOSED",
      modo_seguro: true, datos_reales_modificados: false, respuesta: "Sin navegación.",
      chat: { mensaje: "Sin navegación.", datos: {} },
    }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Consulta");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await screen.findByText("Sin navegación.");

    expect(close).toHaveBeenCalledOnce();
  });

  it("popup bloqueado conserva null y no intenta cerrar ningún handle", async () => {
    const debug = vi.spyOn(console, "debug").mockImplementation(() => undefined);
    vi.spyOn(window, "open").mockReturnValue(null);
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-NULL-HANDLE",
      modo_seguro: true, datos_reales_modificados: false, respuesta: "Respuesta READ.",
      chat: { mensaje: "Respuesta READ.", datos: {} },
    }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Consulta");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await screen.findByText("Respuesta READ.");

    expect(debug.mock.calls.some((call) => (
      call[0] === "host_ai_reserved_window"
      && (call[1] as { event?: string; reservedWindowExists?: boolean; closeAttempted?: boolean }).event === "cleanup"
      && (call[1] as { reservedWindowExists?: boolean }).reservedWindowExists === false
      && (call[1] as { closeAttempted?: boolean }).closeAttempted === false
    ))).toBe(true);
  });

  it("usa un handle nuevo en el follow-up y no reutiliza el de la ambigüedad", async () => {
    const ambiguousPopup = popupWindow();
    const resolvedPopup = popupWindow();
    vi.spyOn(window, "open")
      .mockReturnValueOnce(ambiguousPopup)
      .mockReturnValueOnce(resolvedPopup);
    vi.spyOn(global, "fetch")
      .mockResolvedValueOnce({ ok: true, json: async () => ({
        ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-GAMBA-1",
        modo_seguro: true, datos_reales_modificados: false,
        respuesta: "He encontrado varios artículos con gamba.",
        chat: { mensaje: "He encontrado varios artículos con gamba.", datos: { estado: "AMBIGUO" } },
      }) } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => ({
        ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-GAMBA-2",
        modo_seguro: true, datos_reales_modificados: false,
        respuesta: "He abierto Gamba paella.",
        chat: { mensaje: "He abierto Gamba paella.", datos: { ui_action: {
          type: "OPEN_VIEW", target: "ARTICULO", id: "ART000323", view: "FICHA", label: "Gamba paella",
        } } },
      }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    const input = screen.getByLabelText("Mensaje para Host AI");
    await userEvent.type(input, "Enséñame el stock de gamba.");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await screen.findByText("He encontrado varios artículos con gamba.");
    await userEvent.type(input, "Me refiero a Gamba paella.");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("He abierto Gamba paella.")).toBeInTheDocument();
    expect(ambiguousPopup.close).toHaveBeenCalledOnce();
    expect(ambiguousPopup.location.replace).not.toHaveBeenCalled();
    expect(resolvedPopup.location.replace).toHaveBeenCalledWith("/articulos/ART000323");
    expect(resolvedPopup.close).not.toHaveBeenCalled();
  });

  it("no muestra fallback de popup para una consulta READ sin navegación", async () => {
    vi.spyOn(window, "open").mockReturnValue(null);
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-GAMBA-READ",
      modo_seguro: true, datos_reales_modificados: false,
      respuesta: "Gamba paella tiene stock conocido.",
      chat: { mensaje: "Gamba paella tiene stock conocido.", datos: { cantidad: 1.5, unidad: "kg" } },
    }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "¿Cuánto stock queda de Gamba paella?");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("Gamba paella tiene stock conocido.")).toBeInTheDocument();
    expect(screen.queryByText(/No se pudo abrir automáticamente/)).not.toBeInTheDocument();
  });

  it("cierra la pestaña reservada si falla el backend", async () => {
    const popup = popupWindow();
    vi.spyOn(window, "open").mockReturnValue(popup);
    vi.spyOn(global, "fetch").mockRejectedValue(new TypeError("network"));

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Enséñame la receta");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Error de red");
    expect(popup.close).toHaveBeenCalledOnce();
    expect(popup.location.replace).not.toHaveBeenCalled();
  });

  it("cierra la pestaña reservada al desmontar el Chat", async () => {
    const popup = popupWindow();
    vi.spyOn(window, "open").mockReturnValue(popup);
    vi.spyOn(global, "fetch").mockReturnValue(new Promise<Response>(() => undefined));

    const rendered = render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Enséñame la receta");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    rendered.unmount();

    expect(popup.close).toHaveBeenCalledOnce();
    expect(popup.location.replace).not.toHaveBeenCalled();
  });

  it.each([
    [{ target: "ARTICULO", id: "ART-GAMBA", view: "FICHA", label: "Gamba paella" }, "/articulos/ART-GAMBA"],
    [{ target: "MENU", id: "MENU601-000003", view: "DETALLE", label: "pbd" }, "/menus?menu_id=MENU601-000003"],
    [{ target: "PRODUCCION", id: "PLANPR-FCEB14E386", view: "PLAN", label: "Producción · pbd" }, "/produccion?plan_id=PLANPR-FCEB14E386"],
    [{ target: "COMPRA", id: "", view: "LISTADO", label: "Compras" }, "/compras"],
    [{ target: "EVENTOS", id: "", view: "LISTADO", label: "Eventos" }, "/eventos"],
    [{ target: "EVENTOS", id: "EVT-ABC123", view: "DETALLE", label: "Boda Marta" }, "/eventos?evento_id=EVT-ABC123"],
  ])("resuelve OPEN_VIEW %o a una ruta interna cerrada", async (action, route) => {
    const popup = popupWindow();
    const open = vi.spyOn(window, "open").mockReturnValue(popup);
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-MODULE-VIEW",
      modo_seguro: true, datos_reales_modificados: false, respuesta: "Vista abierta.",
      chat: { mensaje: "Vista abierta.", datos: { ui_action: { type: "OPEN_VIEW", ...action, url: "javascript:alert(1)" } } },
    }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Enséñamelo");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    expect(await screen.findByText("Vista abierta.")).toBeInTheDocument();
    expect(open).toHaveBeenCalledWith("", "_blank");
    expect(popup.opener).toBeNull();
    expect(popup.location.replace).toHaveBeenCalledWith(route);
    expect(popup.location.replace).not.toHaveBeenCalledWith("about:blank");
    expect(popup.close).not.toHaveBeenCalled();
    expect(screen.getByRole("heading", { name: "Host AI" })).toBeInTheDocument();
  });

  it("una consulta READ informativa de Eventos no consume ni deja abierta la pestaña reservada", async () => {
    const popup = popupWindow();
    vi.spyOn(window, "open").mockReturnValue(popup);
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-EVENTOS-READ",
      modo_seguro: true, datos_reales_modificados: false, respuesta: "Estos son los eventos de esta semana.",
      chat: { mensaje: "Estos son los eventos de esta semana.", datos: {
        general_agent: { tools_executed: ["consultar_eventos"] },
      } },
    }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "¿Qué eventos tenemos esta semana?");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    expect(await screen.findByText("Estos son los eventos de esta semana.")).toBeInTheDocument();
    expect(popup.location.replace).not.toHaveBeenCalled();
    expect(popup.close).toHaveBeenCalledOnce();
  });

  it.each([
    ["URL", "ADMIN"],
    ["ELABORACION", "RESUMEN"],
    ["EVENTOS", "ADMIN"],
  ])("ignora una UI action con target %s o vista %s no permitidos", async (target, view) => {
    const popup = popupWindow();
    const open = vi.spyOn(window, "open").mockReturnValue(popup);
    const mock = vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-BAD-VIEW",
      modo_seguro: true, datos_reales_modificados: false, respuesta: "Destino no disponible.",
      chat: { mensaje: "Destino no disponible.", datos: { ui_action: {
        type: "OPEN_VIEW", target, id: "REC-ENSALADILLA", view,
      } } },
    }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Abre una ruta");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("Destino no disponible.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Host AI" })).toBeInTheDocument();
    expect(mock).toHaveBeenCalledTimes(1);
    expect(open).toHaveBeenCalledOnce();
    expect(popup.location.replace).not.toHaveBeenCalled();
    expect(popup.close).toHaveBeenCalledOnce();
  });

  it.each(["../../admin", "javascript:alert(1)", "REC/OTRA"])("rechaza el id no canónico %s", async (id) => {
    const popup = popupWindow();
    const open = vi.spyOn(window, "open").mockReturnValue(popup);
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true, json: async () => ({
      ok: true, version: "1.0", api_version: "1.0", request_id: "REQ-BAD-ID", modo_seguro: true, datos_reales_modificados: false,
      respuesta: "Destino rechazado.",
      chat: { mensaje: "Destino rechazado.", datos: { ui_action: {
        type: "OPEN_VIEW", target: "ELABORACION", id, view: "RECETA", url: "javascript:alert(1)",
      } } },
    }) } as Response);

    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Abre ficha");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    expect(await screen.findByText("Destino rechazado.")).toBeInTheDocument();
    expect(open).toHaveBeenCalledOnce();
    expect(popup.location.replace).not.toHaveBeenCalled();
    expect(popup.close).toHaveBeenCalledOnce();
  });
});
