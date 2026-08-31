import { KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import { HostAiApiError } from "../../api/client";
import { chatService } from "../../services/chatService";
import type { ApiEnvelopeBase, ArticleChangePreview as ArticleChangePreviewData, ChatConfirmationAction, ChatConfirmationActionId, ChatOperationalIncident, ChatPurchaseGroup, ChatResponse } from "../../types/api";
import { ChatComposer, ChatMessageList, type ChatItem, type ChatSafeStatus, type ChatUiError, type NavigationTarget } from "../components/ChatConversation";

type ReservedWindowEntry = {
  handle: Window | null;
  consumed: boolean;
};

type ReservedWindowAudit = {
  turnId: string;
  event: "reserved" | "consumed" | "cleanup";
  reservedWindowCreated?: boolean;
  reservedWindowExists: boolean;
  reservedWindowConsumed: boolean;
  reservedWindowClosedBeforeCleanup?: boolean | null;
  closeAttempted?: boolean;
  closeSucceeded?: boolean | null;
  closedAfter?: boolean | null;
  handleRemoved?: boolean;
};

function getResponseText(payload: ChatResponse): string {
  if (typeof payload.respuesta === "string") {
    return payload.respuesta;
  }
  const chatText = payload.chat?.mensaje;
  return typeof chatText === "string" ? chatText : "";
}

function getSafeStatus(payload: ApiEnvelopeBase) {
  return {
    modoSeguro: payload.modo_seguro,
    datosRealesModificados: payload.datos_reales_modificados,
  };
}

const CONFIRMATION_ACTIONS: Record<ChatConfirmationActionId, ChatConfirmationAction> = {
  APPLY_PENDING_RESERVATION: { action_id: "APPLY_PENDING_RESERVATION", label: "Aplicar cambio", style: "primary" },
  DISCARD_PENDING_RESERVATION: { action_id: "DISCARD_PENDING_RESERVATION", label: "Descartar", style: "secondary" },
  CONFIRM_RESERVATION: { action_id: "CONFIRM_RESERVATION", label: "Confirmar reserva", style: "primary" },
  EDIT_RESERVATION: { action_id: "EDIT_RESERVATION", label: "Modificar", style: "secondary" },
  CANCEL_RESERVATION: { action_id: "CANCEL_RESERVATION", label: "Cancelar reserva", style: "primary" },
  MARK_RESERVATION_NO_SHOW: { action_id: "MARK_RESERVATION_NO_SHOW", label: "Marcar no-show", style: "primary" },
  COMPLETE_RESERVATION: { action_id: "COMPLETE_RESERVATION", label: "Completar", style: "primary" },
  OPEN_RESERVATION: { action_id: "OPEN_RESERVATION", label: "Abrir ficha", style: "secondary" },
  RESOLVE_MISSING_PRICE: { action_id: "RESOLVE_MISSING_PRICE", label: "Completar precio", style: "secondary" },
  RESOLVE_MISSING_CONVERSION: { action_id: "RESOLVE_MISSING_CONVERSION", label: "Configurar conversión", style: "secondary" },
  CHECK_ESCANDALLO_COST: { action_id: "CHECK_ESCANDALLO_COST", label: "Comprobar escandallo", style: "secondary" },
  APPLY_PENDING_ARTICLE_CHANGE: { action_id: "APPLY_PENDING_ARTICLE_CHANGE", label: "Aplicar cambio", style: "primary" },
  DISCARD_PENDING_ARTICLE_CHANGE: { action_id: "DISCARD_PENDING_ARTICLE_CHANGE", label: "Descartar", style: "secondary" },
  APPLY_PENDING_LOT_LOCATION: { action_id: "APPLY_PENDING_LOT_LOCATION", label: "Confirmar", style: "primary" },
  DISCARD_PENDING_LOT_LOCATION: { action_id: "DISCARD_PENDING_LOT_LOCATION", label: "Cancelar", style: "secondary" },
  APPLY_PENDING_CATALOG_CREATE: { action_id: "APPLY_PENDING_CATALOG_CREATE", label: "Confirmar", style: "primary" },
  DISCARD_PENDING_CATALOG_CREATE: { action_id: "DISCARD_PENDING_CATALOG_CREATE", label: "Cancelar", style: "secondary" },
};

function getConfirmationActions(payload: ChatResponse): ChatConfirmationAction[] {
  const data = payload.chat?.datos;
  if (!data || typeof data !== "object") return [];
  const record = data as Record<string, unknown>;
  const economic = record.economic_actions;
  const raw = Array.isArray(economic) && economic.length
    ? economic
    : record.reservation_actions ?? record.confirmation_actions;
  if (!Array.isArray(raw)) return [];
  const seen = new Set<string>();
  return raw.flatMap((value) => {
    if (!value || typeof value !== "object") return [];
    const id = String((value as Record<string, unknown>).action_id || "") as ChatConfirmationActionId;
    if (!CONFIRMATION_ACTIONS[id] || seen.has(id)) return [];
    const contextId = String((value as Record<string, unknown>).action_context_id || "");
    const isPreviewAction = id === "APPLY_PENDING_RESERVATION" || id === "DISCARD_PENDING_RESERVATION" || id === "APPLY_PENDING_ARTICLE_CHANGE" || id === "DISCARD_PENDING_ARTICLE_CHANGE" || id === "APPLY_PENDING_LOT_LOCATION" || id === "DISCARD_PENDING_LOT_LOCATION" || id === "APPLY_PENDING_CATALOG_CREATE" || id === "DISCARD_PENDING_CATALOG_CREATE";
    if (!isPreviewAction && !/^[a-f0-9]{32}$/.test(contextId)) return [];
    seen.add(id);
    return [{ ...CONFIRMATION_ACTIONS[id], ...(contextId ? { action_context_id: contextId } : {}) }];
  });
}

function getArticleChangePreview(payload: ChatResponse): ArticleChangePreviewData | undefined {
  const data = payload.chat?.datos;
  if (!data || typeof data !== "object") return undefined;
  const raw = (data as Record<string, unknown>).preview;
  if (!raw || typeof raw !== "object") return undefined;
  const value = raw as Record<string, unknown>;
  const operations = new Set(["UPDATE_PRICE", "UPDATE_CONVERSION", "UPDATE_FORMAT"]);
  if (value.schema !== "ARTICLE_CHANGE_PREVIEW_V1" || value.entity_type !== "ARTICULO" ||
      typeof value.entity_id !== "string" || typeof value.title !== "string" ||
      typeof value.operation !== "string" || !operations.has(value.operation) ||
      typeof value.notice !== "string" || value.datos_reales_modificados !== false ||
      !Array.isArray(value.changes) || !Array.isArray(value.derived) || !Array.isArray(value.unchanged)) return undefined;
  const changes = value.changes.slice(0, 10);
  const derived = value.derived.slice(0, 10);
  const unchanged = value.unchanged.slice(0, 10);
  const validChange = (item: unknown) => item !== null && typeof item === "object" && ["field", "label", "before", "after"].every((key) => typeof (item as Record<string, unknown>)[key] === "string");
  const validDetail = (item: unknown) => item !== null && typeof item === "object" && typeof (item as Record<string, unknown>).label === "string" && typeof (item as Record<string, unknown>).value === "string" && ["undefined", "string"].includes(typeof (item as Record<string, unknown>).formula) && ["undefined", "string"].includes(typeof (item as Record<string, unknown>).status);
  if (!changes.every(validChange) || !derived.every(validDetail) || !unchanged.every(validDetail)) return undefined;
  return { ...value, changes, derived, unchanged } as ArticleChangePreviewData;
}

function getCatalogPreview(payload: ChatResponse): Record<string, unknown> | undefined {
  const data = payload.chat?.datos && typeof payload.chat.datos === "object" ? payload.chat.datos as Record<string, unknown> : undefined;
  const pending = data?.pending_write;
  if (pending && typeof pending === "object" && !Array.isArray(pending)) {
    const record = pending as Record<string, unknown>;
    if (record.confirmation_required === true && record.preview && typeof record.preview === "object" && !Array.isArray(record.preview)) return record;
  }
  const actions = Array.isArray(data?.confirmation_actions) ? data.confirmation_actions : [];
  if (!actions.some((item) => item && typeof item === "object" && String((item as Record<string, unknown>).action_id || "").includes("CATALOG_CREATE"))) return undefined;
  const raw = data?.preview;
  return raw && typeof raw === "object" && !Array.isArray(raw) ? { operation: "CREAR", domain: "", preview: raw } : undefined;
}

function getPurchaseGroups(payload: ChatResponse): ChatPurchaseGroup[] {
  const raw = payload.chat?.datos?.purchase_groups;
  if (!Array.isArray(raw)) return [];
  const canonicalId = (value: unknown) => typeof value === "string" && /^[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*$/.test(value);
  return raw.slice(0, 20).flatMap((value) => {
    if (!value || typeof value !== "object") return [];
    const group = value as unknown as Record<string, unknown>;
    const provider = typeof group.proveedor === "string" && group.proveedor.trim() ? group.proveedor.trim() : "Sin proveedor asignado";
    if (!Array.isArray(group.articulos)) return [];
    const articles = group.articulos.slice(0, 100).flatMap((item) => {
      if (!item || typeof item !== "object") return [];
      const row = item as Record<string, unknown>;
      const quantity = Number(row.cantidad);
      if (typeof row.nombre !== "string" || !row.nombre.trim() || !Number.isFinite(quantity) || quantity <= 0 || typeof row.unidad !== "string") return [];
      return [{ articulo_id: typeof row.articulo_id === "string" ? row.articulo_id : "", nombre: row.nombre.trim(), cantidad: quantity, unidad: row.unidad.trim(), formato: typeof row.formato === "string" ? row.formato : null, precio_unitario: typeof row.precio_unitario === "number" && Number.isFinite(row.precio_unitario) ? row.precio_unitario : null, unidad_precio: typeof row.unidad_precio === "string" ? row.unidad_precio : null, coste_neto: typeof row.coste_neto === "number" && Number.isFinite(row.coste_neto) ? row.coste_neto : null }];
    });
    if (!articles.length) return [];
    const orderState = typeof group.estado_pedido === "string" ? group.estado_pedido.trim().toLocaleLowerCase("es-ES") : "ninguno";
    const draftState = ["borrador", "draft", "propuesta"].includes(orderState);
    const sourceAction = group.action && typeof group.action === "object" ? group.action as Record<string, unknown> : null;
    let action: ChatPurchaseGroup["action"] = null;
    if (sourceAction?.type === "OPEN_ORDER" && canonicalId(sourceAction.pedido_id)) {
      action = { type: "OPEN_ORDER", label: draftState ? "Abrir borrador" : "Abrir pedido", pedido_id: String(sourceAction.pedido_id) };
    } else if (sourceAction?.type === "PREPARE_ORDER" && canonicalId(sourceAction.menu_id)) {
      action = { type: "PREPARE_ORDER", label: "Preparar pedido", menu_id: String(sourceAction.menu_id) };
    }
    const rawOrder = group.pedido_relacionado && typeof group.pedido_relacionado === "object" ? group.pedido_relacionado as Record<string, unknown> : null;
    const relevantLines = Array.isArray(rawOrder?.lineas_relevantes) ? rawOrder.lineas_relevantes.flatMap((line) => {
      if (!line || typeof line !== "object") return [];
      const row = line as Record<string, unknown>; const planned = row.cantidad_prevista == null ? null : Number(row.cantidad_prevista);
      if (typeof row.articulo_id !== "string" || typeof row.nombre !== "string" || typeof row.unidad !== "string" || (planned !== null && !Number.isFinite(planned))) return [];
      return [{ articulo_id: row.articulo_id, nombre: row.nombre, cantidad_prevista: planned, unidad: row.unidad, cubriria_necesidad: row.cubriria_necesidad === true }];
    }) : [];
    const relatedOrder = rawOrder && typeof rawOrder.pedido_id === "string" && relevantLines.length ? { pedido_id: rawOrder.pedido_id, estado: typeof rawOrder.estado === "string" ? rawOrder.estado : "", lineas_relevantes: relevantLines } : null;
    return [{ proveedor: provider, articulos: articles, estado_pedido: orderState, pedido_relacionado: relatedOrder, action }];
  });
}

function getOperationalIncidents(payload: ChatResponse): ChatOperationalIncident[] {
  const raw = payload.chat?.datos?.operational_incidents;
  if (!Array.isArray(raw)) return [];
  return raw.slice(0, 50).flatMap((value) => {
    if (!value || typeof value !== "object") return [];
    const incident = value as Record<string, unknown>;
    if (typeof incident.reason !== "string" || !incident.reason.trim()) return [];
    return [{
      reason: incident.reason.trim(),
      articulo_id: typeof incident.articulo_id === "string" && incident.articulo_id.trim() ? incident.articulo_id.trim() : undefined,
      unidad: typeof incident.unidad === "string" && incident.unidad.trim() ? incident.unidad.trim() : undefined,
    }];
  });
}

function reserveSafeWindow(): Window | null {
  const opened = window.open("", "_blank");
  if (!opened) return null;
  opened.opener = null;
  return opened;
}

function observableClosed(opened: Window | null): boolean | null {
  if (!opened) return null;
  try {
    const value = opened.closed;
    return typeof value === "boolean" ? value : null;
  } catch {
    return null;
  }
}

function auditReservedWindow(data: ReservedWindowAudit): void {
  if (import.meta.env.DEV) {
    console.debug("host_ai_reserved_window", data);
  }
}

function navigateReservedWindow(opened: Window | null, route: string): boolean {
  if (!opened) return false;
  const closed = observableClosed(opened);
  if (closed === true) return false;
  try {
    opened.location.replace(route);
    return true;
  } catch {
    return false;
  }
}

function cleanupReservedWindow(
  windows: Map<string, ReservedWindowEntry>,
  turnId: string,
): void {
  const entry = windows.get(turnId);
  const handle = entry?.handle ?? null;
  const consumed = entry?.consumed === true;
  const closedBefore = observableClosed(handle);
  let closeAttempted = false;
  let closeSucceeded: boolean | null = null;
  try {
    if (handle && !consumed) {
      closeAttempted = true;
      handle.close();
      closeSucceeded = observableClosed(handle);
    }
  } catch {
    closeSucceeded = false;
  } finally {
    windows.delete(turnId);
    auditReservedWindow({
      turnId,
      event: "cleanup",
      reservedWindowExists: Boolean(handle),
      reservedWindowConsumed: consumed,
      reservedWindowClosedBeforeCleanup: closedBefore,
      closeAttempted,
      closeSucceeded,
      closedAfter: observableClosed(handle),
      handleRemoved: !windows.has(turnId),
    });
  }
}

function openSafeNewTab(route: string): boolean {
  return navigateReservedWindow(reserveSafeWindow(), route);
}

const MODULE_ROUTES: Record<string, NavigationTarget> = {
  CATALOGO: { to: "/articulos", label: "Abrir en Artículos" },
  COMPRAS: { to: "/compras", label: "Abrir en Compras" },
  EVENTOS: { to: "/eventos", label: "Abrir Eventos" },
  RESERVAS: { to: "/reservas", label: "Abrir Reservas" },
  PRODUCCION: { to: "/produccion", label: "Abrir Producción" },
  STOCK: { to: "/stock", label: "Abrir Stock" },
  EXECUTIVE: { to: "/executive", label: "Abrir Executive" },
  HOME: { to: "/dashboard", label: "Abrir Dashboard" },
};

function purchaseActionLabel(data: Record<string, unknown>, orderId: string, fallbackLabel: string): string {
  const groups = Array.isArray(data.purchase_groups) ? data.purchase_groups : [];
  const matchingGroup = groups.find((value) => {
    if (!value || typeof value !== "object") return false;
    const group = value as Record<string, unknown>;
    const action = group.action && typeof group.action === "object" ? group.action as Record<string, unknown> : null;
    const related = group.pedido_relacionado && typeof group.pedido_relacionado === "object" ? group.pedido_relacionado as Record<string, unknown> : null;
    return action?.pedido_id === orderId || related?.pedido_id === orderId;
  }) as Record<string, unknown> | undefined;
  const related = matchingGroup?.pedido_relacionado && typeof matchingGroup.pedido_relacionado === "object"
    ? matchingGroup.pedido_relacionado as Record<string, unknown>
    : null;
  const state = String(related?.estado ?? matchingGroup?.estado_pedido ?? "").trim().toLocaleLowerCase("es-ES");
  if (["borrador", "draft", "propuesta"].includes(state)) return "Abrir borrador";
  if (state && state !== "ninguno") return "Abrir pedido";
  return fallbackLabel.toLocaleLowerCase("es-ES").includes("borrador") ? "Abrir borrador" : "Abrir pedido";
}

function getNavigation(payload: ChatResponse): NavigationTarget | undefined {
  const data = payload.chat?.datos;
  if (!data || typeof data !== "object") return undefined;
  const offered = (data as Record<string, unknown>).ui_action_mode === "OFFER";
  const uiAction = (data as Record<string, unknown>).ui_action;
  if (uiAction && typeof uiAction === "object") {
    const action = uiAction as Record<string, unknown>;
    const type = typeof action.type === "string" ? action.type.toUpperCase() : "";
    const target = typeof action.target === "string" ? action.target.toUpperCase() : "";
    const view = typeof action.view === "string" ? action.view.toUpperCase() : "";
    const id = typeof action.id === "string" ? action.id.trim() : "";
    const label = typeof action.label === "string" && action.label.trim() ? action.label.trim() : id;
    const canonicalId = /^[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*$/.test(id);
    if (type === "OPEN_VIEW" && target === "ELABORACION" && canonicalId && ["RECETA", "ESCANDALLO"].includes(view)) {
      const tab = view === "RECETA" ? "receta" : "escandallo";
      const viewLabel = view === "RECETA" ? "Receta" : "Escandallo";
      return {
        to: `/biblioteca/elaboraciones/${encodeURIComponent(id)}?tab=${tab}`,
        label: offered && view === "ESCANDALLO" ? "Ver escandallo" : `Abrir ${viewLabel}`,
        automatic: !offered,
        openInNewTab: true,
        indication: `${label} · ${viewLabel}`,
      };
    }
    if (type === "OPEN_VIEW" && target === "ARTICULO" && canonicalId && view === "FICHA") {
      return {
        to: `/articulos/${encodeURIComponent(id)}`,
        label: "Abrir Artículo",
        automatic: true,
        openInNewTab: true,
        indication: `${label} · Ficha de artículo`,
      };
    }
    if (type === "OPEN_VIEW" && target === "LOTE" && canonicalId && view === "DETALLE") {
      const query = new URLSearchParams({ lote_id: id });
      return { to: `/stock?${query}`, label: "Abrir lote", automatic: false, openInNewTab: true, indication: `${label} · Lote` };
    }
    if (type === "OPEN_VIEW" && target === "MENU" && canonicalId && view === "DETALLE") {
      const query = new URLSearchParams({ menu_id: id });
      return { to: `/menus?${query}`, label: "Abrir Menú", automatic: true, openInNewTab: true, indication: `${label} · Menú` };
    }
    if (type === "OPEN_VIEW" && target === "PRODUCCION" && canonicalId && view === "PLAN") {
      const query = new URLSearchParams({ plan_id: id });
      return { to: `/produccion?${query}`, label: "Abrir Producción", automatic: true, openInNewTab: true, indication: `${label} · Plan de producción` };
    }
    if (type === "OPEN_VIEW" && target === "COMPRA" && view === "LISTADO" && !id) {
      return { to: "/compras", label: "Abrir Compras", automatic: true, openInNewTab: true, indication: "Compras" };
    }
    if (type === "OPEN_VIEW" && target === "EVENTOS" && view === "LISTADO" && !id) {
      return { to: "/eventos", label: "Abrir Eventos", automatic: true, openInNewTab: true, indication: "Eventos" };
    }
    if (type === "OPEN_VIEW" && target === "EVENTOS" && view === "DETALLE" && canonicalId) {
      const query = new URLSearchParams({ evento_id: id });
      return { to: `/eventos?${query}`, label: "Abrir evento", automatic: true, openInNewTab: true, indication: `${label} · Evento` };
    }
    if (type === "OPEN_VIEW" && target === "RESERVAS" && view === "LISTADO" && !id) {
      return { to: "/reservas", label: "Abrir Reservas", automatic: true, openInNewTab: true, indication: "Reservas" };
    }
    if (type === "OPEN_VIEW" && target === "RESERVAS" && view === "DETALLE" && /^RES-[A-F0-9]{12}$/.test(id)) {
      return { to: `/reservas/${encodeURIComponent(id)}`, label: "Abrir Reserva", automatic: true, openInNewTab: true, indication: `${label} · Reserva` };
    }
    if (type === "OPEN_VIEW" && target === "COMPRA" && canonicalId && view === "PEDIDO") {
      const query = new URLSearchParams({ pedido_id: id });
      const actionLabel = purchaseActionLabel(data as Record<string, unknown>, id, label);
      return { to: `/compras?${query}`, label: actionLabel, automatic: false, openInNewTab: true };
    }
  }
  const request = (data as Record<string, unknown>).navigation_request;
  if (!request || typeof request !== "object") return undefined;
  const navigationRequest = request as Record<string, unknown>;
  const target = navigationRequest.target_module;
  if (typeof target !== "string") return undefined;
  const route = MODULE_ROUTES[target.toUpperCase()];
  if (!route) return undefined;
  const filterData = navigationRequest.filter_data;
  if (target.toUpperCase() !== "CATALOGO" || !filterData || typeof filterData !== "object") return route;
  const term = (filterData as Record<string, unknown>).termino;
  if (typeof term !== "string" || !term.trim()) return route;
  const query = new URLSearchParams({ q: term.trim() });
  return { ...route, to: `${route.to}?${query.toString()}` };
}

export function ChatPage() {
  const [mensaje, setMensaje] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<ChatUiError | null>(null);
  const [items, setItems] = useState<ChatItem[]>([]);
  const [lastSent, setLastSent] = useState<string | null>(null);
  const [safeState, setSafeState] = useState<ChatSafeStatus | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const pendingWindowsRef = useRef<Map<string, ReservedWindowEntry>>(new Map());
  const sessionIdRef = useRef<string>(crypto.randomUUID());
  const actionInFlightRef = useRef(false);

  useEffect(() => () => {
    for (const turnId of Array.from(pendingWindowsRef.current.keys())) {
      cleanupReservedWindow(pendingWindowsRef.current, turnId);
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [items, sending, error]);

  const canSend = useMemo(() => Boolean(mensaje.trim()) && !sending, [mensaje, sending]);

  async function submitMessage(rawMessage: string) {
    const text = rawMessage.trim();
    if (!text || sending) {
      return;
    }

    const turnId = crypto.randomUUID();
    const pendingWindow = reserveSafeWindow();
    pendingWindowsRef.current.set(turnId, { handle: pendingWindow, consumed: false });
    auditReservedWindow({
      turnId,
      event: "reserved",
      reservedWindowCreated: Boolean(pendingWindow),
      reservedWindowExists: pendingWindowsRef.current.has(turnId),
      reservedWindowConsumed: false,
    });

    setMensaje("");
    setError(null);
    setSending(true);
    setLastSent(text);
    setItems((prev) => [...prev, { id: crypto.randomUUID(), role: "usuario", text }]);

    try {
      const response = await chatService.send({
        mensaje: text,
        contexto: { session_id: sessionIdRef.current },
      });
      const responseSafeStatus = getSafeStatus(response);
      setSafeState(responseSafeStatus);
      let navigation = getNavigation(response);
      if (navigation?.automatic && navigation.openInNewTab) {
        const opened = navigateReservedWindow(
          pendingWindow,
          navigation.to,
        );
        const reserved = pendingWindowsRef.current.get(turnId);
        if (opened && reserved) {
          reserved.consumed = true;
          auditReservedWindow({
            turnId,
            event: "consumed",
            reservedWindowExists: true,
            reservedWindowConsumed: true,
          });
        }
        navigation = {
          ...navigation,
          popupBlocked: !opened,
          indication: !opened
            ? "No se pudo abrir automáticamente. Usa el botón para abrir la ficha."
            : `Abierto en una nueva pestaña: ${navigation.indication}`,
        };
      }
      setItems((prev) => [
        ...prev.map((item) => ({ ...item, confirmationActions: undefined })),
        {
          id: crypto.randomUUID(),
          role: "host_ai",
          text: getResponseText(response),
          requestId: response.request_id,
          safeStatus: responseSafeStatus,
          navigation,
          confirmationActions: getConfirmationActions(response),
          articlePreview: getArticleChangePreview(response), catalogPreview: getCatalogPreview(response),
          purchaseGroups: getPurchaseGroups(response),
          operationalIncidents: getOperationalIncidents(response),
        },
      ]);
    } catch (err: unknown) {
      if (err instanceof HostAiApiError) {
        if (typeof err.modoSeguro === "boolean" && typeof err.datosRealesModificados === "boolean") {
          setSafeState({
            modoSeguro: err.modoSeguro,
            datosRealesModificados: err.datosRealesModificados,
          });
        }
        setError({
          kind: typeof err.statusCode === "number" ? "http" : "network",
          message: err.message,
          requestId: err.requestId,
        });
      } else {
        setError({
          kind: "network",
          message: "No se pudo enviar el mensaje.",
        });
      }
    } finally {
      cleanupReservedWindow(pendingWindowsRef.current, turnId);
      setSending(false);
      textareaRef.current?.focus();
    }
  }

  async function submitConfirmationAction(action: ChatConfirmationAction) {
    const actionId = action.action_id;
    if (sending || actionInFlightRef.current || !CONFIRMATION_ACTIONS[actionId]) return;
    const turnId = crypto.randomUUID();
    const pendingWindow = reserveSafeWindow();
    pendingWindowsRef.current.set(turnId, { handle: pendingWindow, consumed: false });
    actionInFlightRef.current = true;
    setSending(true);
    setError(null);
    try {
      const response = await chatService.send({ mensaje: "", actionId, actionContextId: action.action_context_id, contexto: { session_id: sessionIdRef.current } });
      const responseSafeStatus = getSafeStatus(response);
      setSafeState(responseSafeStatus);
      let navigation = getNavigation(response);
      if (navigation?.automatic && navigation.openInNewTab) {
        const opened = navigateReservedWindow(pendingWindow, navigation.to);
        const reserved = pendingWindowsRef.current.get(turnId);
        if (opened && reserved) reserved.consumed = true;
        navigation = { ...navigation, popupBlocked: !opened, indication: opened ? `Abierto en una nueva pestaña: ${navigation.indication}` : "No se pudo abrir automáticamente. Usa el botón para abrir la ficha." };
      }
      setItems((prev) => [
        ...prev.map((item) => ({ ...item, confirmationActions: undefined })),
        { id: crypto.randomUUID(), role: "host_ai", text: getResponseText(response), requestId: response.request_id, safeStatus: responseSafeStatus, confirmationActions: getConfirmationActions(response), articlePreview: getArticleChangePreview(response), catalogPreview: getCatalogPreview(response), purchaseGroups: getPurchaseGroups(response), operationalIncidents: getOperationalIncidents(response), navigation },
      ]);
    } catch (err: unknown) {
      setError(err instanceof HostAiApiError
        ? { kind: typeof err.statusCode === "number" ? "http" : "network", message: err.message, requestId: err.requestId }
        : { kind: "network", message: "No se pudo ejecutar la acción." });
    } finally {
      cleanupReservedWindow(pendingWindowsRef.current, turnId);
      actionInFlightRef.current = false;
      setSending(false);
    }
  }

  async function onSubmit() {
    await submitMessage(mensaje);
  }

  async function onRetry() {
    if (!lastSent || sending) {
      return;
    }
    await submitMessage(lastSent);
  }

  async function onTextareaKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      await submitMessage(mensaje);
    }
  }

  return (
    <section className="chat-page" aria-label="Chat operativo de Host AI">
      <header className="chat-header">
        <h1>Host AI</h1>
      </header>

      <ChatMessageList items={items} sending={sending} error={error} safeStatus={safeState} endRef={messagesEndRef} onRetry={() => void onRetry()} canRetry={Boolean(lastSent) && !sending} onConfirmation={(action) => void submitConfirmationAction(action)} onOpenNewTab={openSafeNewTab} />

      <div className="chat-composer-dock">
        <ChatComposer value={mensaje} sending={sending} canSend={canSend} textareaRef={textareaRef} onChange={setMensaje} onSubmit={() => void onSubmit()} onKeyDown={onTextareaKeyDown} />
      </div>
    </section>
  );
}
