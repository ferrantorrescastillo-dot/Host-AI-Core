import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../ui/App";

function response(message: string, actions: unknown[] = [], modified = false, extra: Record<string, unknown> = {}) {
  return { ok: true, status: 200, json: async () => ({
    ok: true, version: "1.0", api_version: "1.0", request_id: crypto.randomUUID(),
    modo_seguro: true, datos_reales_modificados: modified, respuesta: message,
    chat: { mensaje: message, datos: { reservation_actions: actions, datos_reales_modificados: modified, ...extra } },
  }) } as Response;
}

const actions = [
  { action_id: "APPLY_PENDING_RESERVATION", label: "texto no confiable", style: "primary" },
  { action_id: "DISCARD_PENDING_RESERVATION", label: "otro texto", style: "secondary" },
];

const actionContextId = "a".repeat(32);
const pendingActions = [
  { action_id: "CONFIRM_RESERVATION", action_context_id: actionContextId }, { action_id: "EDIT_RESERVATION", action_context_id: actionContextId },
  { action_id: "CANCEL_RESERVATION", action_context_id: actionContextId }, { action_id: "OPEN_RESERVATION", action_context_id: actionContextId },
];
const confirmedActions = [
  { action_id: "EDIT_RESERVATION", action_context_id: actionContextId }, { action_id: "CANCEL_RESERVATION", action_context_id: actionContextId },
  { action_id: "MARK_RESERVATION_NO_SHOW", action_context_id: actionContextId }, { action_id: "COMPLETE_RESERVATION", action_context_id: actionContextId },
  { action_id: "OPEN_RESERVATION", action_context_id: actionContextId },
];

async function sendPreview() {
  await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Crea una reserva");
  await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
  await screen.findByRole("button", { name: "Aplicar cambio" });
}

describe("acciones estructuradas de Reservas en Chat", () => {
  beforeEach(() => {
    Object.defineProperty(Element.prototype, "scrollIntoView", { configurable: true, value: () => undefined });
    vi.spyOn(window, "open").mockReturnValue(null);
  });

  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it("renderiza solo action_id cerrados con etiquetas controladas y un mensaje normal no muestra botones", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(response("Mensaje normal"));
    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Hola");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await screen.findByText("Mensaje normal");
    expect(screen.queryByLabelText("Acciones de confirmación de reserva")).not.toBeInTheDocument();
  });

  it("aplica con el pending de sesión, evita doble request y retira las acciones tras éxito", async () => {
    let finishApply!: (value: Response) => void;
    const pendingApply = new Promise<Response>((resolve) => { finishApply = resolve; });
    const fetch = vi.spyOn(global, "fetch").mockResolvedValueOnce(response("Preview", actions)).mockImplementationOnce(() => pendingApply);
    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await sendPreview();
    const apply = screen.getByRole("button", { name: "Aplicar cambio" });
    await userEvent.dblClick(apply);
    expect(apply).toBeDisabled();
    expect(apply).toHaveTextContent("Procesando...");
    expect(fetch).toHaveBeenCalledTimes(2);
    finishApply(response("Reserva creada", pendingActions, true));
    await screen.findByText("Reserva creada");
    expect(fetch).toHaveBeenCalledTimes(2);
    const body = JSON.parse(String(fetch.mock.calls[1][1]?.body));
    expect(body.action_id).toBe("APPLY_PENDING_RESERVATION");
    expect(body).not.toHaveProperty("preview_token");
    expect(screen.queryByRole("button", { name: "Aplicar cambio" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirmar reserva" })).toBeInTheDocument();
  });

  it("descarta sin WRITE y elimina botones", async () => {
    const fetch = vi.spyOn(global, "fetch").mockResolvedValueOnce(response("Preview", actions)).mockResolvedValueOnce(response("Operación descartada"));
    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await sendPreview();
    await userEvent.click(screen.getByRole("button", { name: "Descartar" }));
    await screen.findByText("Operación descartada");
    const body = JSON.parse(String(fetch.mock.calls[1][1]?.body));
    expect(body.action_id).toBe("DISCARD_PENDING_RESERVATION");
    expect(screen.queryByRole("button", { name: "Descartar" })).not.toBeInTheDocument();
  });

  it("renderiza confirmación tipada de ubicación de lote y envía solo action_id", async () => {
    const lotActions = [
      { action_id: "APPLY_PENDING_LOT_LOCATION", label: "hostil" },
      { action_id: "DISCARD_PENDING_LOT_LOCATION", label: "hostil" },
    ];
    const fetch = vi.spyOn(global, "fetch")
      .mockResolvedValueOnce(response("Cambiar ubicación de lote", lotActions))
      .mockResolvedValueOnce(response("Ubicación actualizada correctamente."));
    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Pon el lote en Cámara 1");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await userEvent.click(await screen.findByRole("button", { name: "Confirmar" }));
    await screen.findByText("Ubicación actualizada correctamente.");
    const body = JSON.parse(String(fetch.mock.calls[1][1]?.body));
    expect(body.action_id).toBe("APPLY_PENDING_LOT_LOCATION");
    expect(body).not.toHaveProperty("preview_token");
  });

  it("ignora action_id desconocido y no interpreta URL", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(response("Preview", [{ action_id: "https://evil.test", label: "Abrir", style: "primary" }]));
    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "consulta");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await screen.findByText("Preview");
    expect(screen.queryByRole("button", { name: "Abrir" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Abrir" })).not.toBeInTheDocument();
  });

  it("retira botones de mensajes anteriores al recibir contexto nuevo", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(response("Reserva pendiente", pendingActions)).mockResolvedValueOnce(response("Contexto actualizado"));
    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "consulta reserva");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await screen.findByRole("button", { name: "Confirmar reserva" });
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "otra consulta");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await screen.findByText("Contexto actualizado");
    expect(screen.queryByRole("button", { name: "Confirmar reserva" })).not.toBeInTheDocument();
  });

  it.each([
    ["PENDIENTE", pendingActions, ["Confirmar reserva", "Modificar", "Cancelar reserva", "Abrir ficha"]],
    ["CONFIRMADA", confirmedActions, ["Modificar", "Cancelar reserva", "Marcar no-show", "Completar", "Abrir ficha"]],
    ["CANCELADA", [{ action_id: "OPEN_RESERVATION", action_context_id: actionContextId }], ["Abrir ficha"]],
    ["NO_SHOW", [{ action_id: "OPEN_RESERVATION", action_context_id: actionContextId }], ["Abrir ficha"]],
    ["COMPLETADA", [{ action_id: "OPEN_RESERVATION", action_context_id: actionContextId }], ["Abrir ficha"]],
  ])("renderiza acciones cerradas para %s", async (_state, stateActions, labels) => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(response("Reserva", stateActions));
    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "consulta");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await screen.findByText("Reserva");
    for (const label of labels) expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
  });

  it.each([
    ["Confirmar reserva", "CONFIRM_RESERVATION"],
    ["Cancelar reserva", "CANCEL_RESERVATION"],
    ["Marcar no-show", "MARK_RESERVATION_NO_SHOW"],
    ["Completar", "COMPLETE_RESERVATION"],
  ])("%s inicia preview estructurado", async (label, actionId) => {
    const initial = actionId === "CONFIRM_RESERVATION" ? pendingActions : confirmedActions;
    const fetch = vi.spyOn(global, "fetch").mockResolvedValueOnce(response("Reserva", initial)).mockResolvedValueOnce(response("Preview", actions));
    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "consulta");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await screen.findByRole("button", { name: label });
    await userEvent.click(screen.getByRole("button", { name: label }));
    await screen.findByRole("button", { name: "Aplicar cambio" });
    const body = JSON.parse(String(fetch.mock.calls[1][1]?.body));
    expect(body).toMatchObject({ action_id: actionId });
    expect(body.action_context_id).toBe(actionContextId);
    expect(body).not.toHaveProperty("reserva_id");
    expect(body).not.toHaveProperty("preview_token");
  });

  it.each(["Abrir ficha", "Modificar"])("%s reutiliza OPEN_VIEW canónico", async (label) => {
    const replace = vi.fn();
    vi.mocked(window.open).mockReturnValue({ location: { replace }, close: vi.fn(), closed: false } as unknown as Window);
    vi.spyOn(global, "fetch").mockResolvedValueOnce(response("Reserva", pendingActions)).mockResolvedValueOnce(response("Abro ficha", pendingActions, false, {
      ui_action: { type: "OPEN_VIEW", target: "RESERVAS", id: "RES-AAAAAAAAAAAA", view: "DETALLE", label: "Reserva" },
    }));
    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "consulta");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await screen.findByRole("button", { name: label });
    await userEvent.click(screen.getByRole("button", { name: label }));
    await screen.findByText("Abro ficha");
    expect(replace).toHaveBeenCalledWith("/reservas/RES-AAAAAAAAAAAA");
  });

  it("incidencia económica captura valor, muestra preview y permite descartarlo sin payload WRITE", async () => {
    const conversionContextId = "b".repeat(32);
    const economicActions = [
      { action_id: "RESOLVE_MISSING_PRICE", action_context_id: actionContextId, label: "hostil", articulo_id: "../../evil", url: "javascript:alert(1)" },
      { action_id: "RESOLVE_MISSING_CONVERSION", action_context_id: conversionContextId, label: "hostil", articulo_id: "../../evil", url: "javascript:alert(1)" },
      { action_id: "ECONOMIC_UNKNOWN", action_context_id: "c".repeat(32), label: "No mostrar" },
    ];
    const fetch = vi.spyOn(global, "fetch")
      .mockResolvedValueOnce(response("Falta el precio del artículo.", [], false, { economic_actions: economicActions }))
      .mockResolvedValueOnce(response("¿A cuánto equivale 1 u de Servilleta en kg?", [], false, { economic_actions: [] }))
      .mockResolvedValueOnce(response("He preparado el cambio.", [], false, {
        economic_actions: [
          { action_id: "APPLY_PENDING_ARTICLE_CHANGE", label: "hostil" },
          { action_id: "DISCARD_PENDING_ARTICLE_CHANGE", label: "hostil" },
        ],
        preview: {
          schema: "ARTICLE_CHANGE_PREVIEW_V1", entity_type: "ARTICULO", entity_id: "ART000285", title: "Servilleta",
          operation: "UPDATE_FORMAT", datos_reales_modificados: false,
          changes: [{ field: "cantidad_formato", label: "Cantidad por formato", before: "Sin definir", after: "200" }],
          unchanged: [{ label: "Precio del paquete sin IVA", value: "6.89 €", status: "Sin cambios" }],
          derived: [{ label: "Precio unitario sin IVA", value: "0.03445 €/u", formula: "6.89 / 200", status: "Calculado; no se persiste como campo independiente" }],
          notice: "Todavía no se ha modificado ningún dato.",
        },
      }))
      .mockResolvedValueOnce(response("Cambio descartado sin modificar el artículo.", [], false, { economic_actions: [] }));
    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "Por qué falta el coste");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await screen.findByRole("button", { name: "Completar precio" });
    const button = screen.getByRole("button", { name: "Configurar conversión" });
    expect(screen.queryByRole("button", { name: "No mostrar" })).not.toBeInTheDocument();
    await userEvent.click(button);
    await screen.findByText("¿A cuánto equivale 1 u de Servilleta en kg?");

    const body = JSON.parse(String(fetch.mock.calls[1][1]?.body));
    expect(body).toEqual(expect.objectContaining({
      mensaje: "", action_id: "RESOLVE_MISSING_CONVERSION", action_context_id: conversionContextId,
    }));
    expect(body).not.toHaveProperty("articulo_id");
    expect(body).not.toHaveProperty("precio");
    expect(body).not.toHaveProperty("scopes");
    expect(body).not.toHaveProperty("url");

    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "1 unidad pesa 0,005 kg");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    const apply = await screen.findByRole("button", { name: "Aplicar cambio" });
    const preview = screen.getByRole("region", { name: "Vista previa del cambio de artículo" });
    expect(preview).toHaveTextContent("Servilleta");
    expect(preview).toHaveTextContent("ART000285");
    expect(preview).toHaveTextContent("Cantidad por formato");
    expect(preview).toHaveTextContent("0.03445 €/u");
    expect(preview).toHaveTextContent("6.89 / 200");
    expect(preview).toHaveTextContent("Sin cambios");
    expect(preview).toHaveTextContent("Todavía no se ha modificado ningún dato.");
    expect(preview.compareDocumentPosition(apply) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    const discard = screen.getByRole("button", { name: "Descartar" });
    await userEvent.click(discard);
    await screen.findByText("Cambio descartado sin modificar el artículo.");
    const discardBody = JSON.parse(String(fetch.mock.calls[3][1]?.body));
    expect(discardBody).toEqual(expect.objectContaining({
      mensaje: "", action_id: "DISCARD_PENDING_ARTICLE_CHANGE",
    }));
    expect(discardBody).not.toHaveProperty("action_context_id");
  });

  it("comprueba el escandallo con contexto opaco y sin payload económico libre", async () => {
    const popup = {
      opener: window,
      closed: false,
      location: { replace: vi.fn() },
      close: vi.fn(),
    } as unknown as Window;
    const open = vi.spyOn(window, "open").mockReturnValue(popup);
    const checkContextId = "e".repeat(32);
    const fetch = vi.spyOn(global, "fetch")
      .mockResolvedValueOnce(response("Artículo actualizado.", [], true, {
        economic_actions: [{ action_id: "CHECK_ESCANDALLO_COST", action_context_id: checkContextId, label: "hostil", receta_id: "REC-EVIL" }],
      }))
      .mockResolvedValueOnce(response("El escandallo ahora está DISPONIBLE.", [], false, {
        economic_actions: [], ui_action_mode: "OFFER",
        ui_action: { type: "OPEN_VIEW", target: "ELABORACION", id: "REC-EXCEL-ABC123", view: "ESCANDALLO", label: "Fixture" },
      }))
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ok: false, error: { code: "fixture" } }) } as Response);
    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "confirmar");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    const check = await screen.findByRole("button", { name: "Comprobar escandallo" });
    await userEvent.dblClick(check);
    await screen.findByText("El escandallo ahora está DISPONIBLE.");
    expect(fetch).toHaveBeenCalledTimes(2);
    const body = JSON.parse(String(fetch.mock.calls[1][1]?.body));
    expect(body).toEqual(expect.objectContaining({
      mensaje: "", action_id: "CHECK_ESCANDALLO_COST", action_context_id: checkContextId,
    }));
    expect(body).not.toHaveProperty("receta_id");
    expect(body).not.toHaveProperty("articulo_id");
    expect(body).not.toHaveProperty("scopes");
    const view = screen.getByRole("button", { name: "Ver escandallo" });
    await userEvent.click(view);
    expect(open).toHaveBeenCalledWith("", "_blank");
    expect(popup.opener).toBeNull();
    expect(popup.location.replace).toHaveBeenCalledWith("/biblioteca/elaboraciones/REC-EXCEL-ABC123?tab=escandallo");
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it("ignora un preview desconocido u hostil", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(response("He preparado el cambio.", [], false, {
      economic_actions: [],
      preview: {
        schema: "ARTICLE_CHANGE_PREVIEW_EVIL",
        entity_type: "ARTICULO",
        entity_id: "<img src=x onerror=alert(1)>",
        title: "<script>alert(1)</script>",
        operation: "DELETE_ARTICLE",
        changes: [], derived: [], unchanged: [],
        notice: "hostil", datos_reales_modificados: false,
      },
    }));
    render(<MemoryRouter initialEntries={["/chat"]}><App /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText("Mensaje para Host AI"), "consulta");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await screen.findByText("He preparado el cambio.");
    expect(screen.queryByRole("region", { name: "Vista previa del cambio de artículo" })).not.toBeInTheDocument();
    expect(screen.queryByText("<script>alert(1)</script>")).not.toBeInTheDocument();
  });
});
