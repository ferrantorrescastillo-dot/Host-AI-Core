import { KeyboardEvent, RefObject, useLayoutEffect } from "react";
import { Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ArticleChangePreview as ArticleChangePreviewData, ChatConfirmationAction, ChatOperationalIncident, ChatPurchaseGroup } from "../../types/api";
import { ArticleChangePreview } from "./ArticleChangePreview";

export type NavigationTarget = {
  to: string;
  label: string;
  automatic?: boolean;
  indication?: string;
  openInNewTab?: boolean;
  popupBlocked?: boolean;
};

export type ChatSafeStatus = { modoSeguro: boolean; datosRealesModificados: boolean };

export type ChatItem = {
  id: string;
  role: "usuario" | "host_ai";
  text: string;
  requestId?: string;
  safeStatus?: ChatSafeStatus;
  navigation?: NavigationTarget;
  confirmationActions?: ChatConfirmationAction[];
  articlePreview?: ArticleChangePreviewData;
  catalogPreview?: Record<string, unknown>;
  purchaseGroups?: ChatPurchaseGroup[];
  operationalIncidents?: ChatOperationalIncident[];
};

export type ChatUiError = {
  kind: "network" | "http";
  message: string;
  requestId?: string;
};

function equivalentNavigation(left?: string, right?: string) {
  if (!left || !right) return false;
  try {
    const base = "https://host-ai.local";
    const a = new URL(left, base);
    const b = new URL(right, base);
    return a.pathname === b.pathname && a.search === b.search && a.hash === b.hash;
  } catch {
    return false;
  }
}

export function MarkdownContent({ children, actionRoute }: { children: string; actionRoute?: string }) {
  return (
    <div className="chat-markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        skipHtml
        components={{
          table: ({ children: tableChildren, ...props }) => (
            <div className="chat-table-wrap" tabIndex={0} aria-label="Tabla desplazable">
              <table {...props}>{tableChildren}</table>
            </div>
          ),
          a: ({ children: linkChildren, href, ...props }) => equivalentNavigation(href, actionRoute)
            ? null
            : <a {...props} href={href} target="_blank" rel="noreferrer noopener">{linkChildren}</a>,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}

export function ChatTechnicalDetails({ requestId, safeStatus, error }: {
  requestId?: string;
  safeStatus?: ChatSafeStatus;
  error?: ChatUiError;
}) {
  if (!requestId && !safeStatus && !error) return null;
  return (
    <details className="chat-technical-details">
      <summary>Detalles</summary>
      <dl>
        {requestId ? <><dt>Request ID</dt><dd>{requestId}</dd></> : null}
        {safeStatus ? <><dt>Modo seguro</dt><dd>{safeStatus.modoSeguro ? "Activo" : "Inactivo"}</dd></> : null}
        {safeStatus ? <><dt>Datos reales modificados</dt><dd>{safeStatus.datosRealesModificados ? "Sí" : "No"}</dd></> : null}
        {error ? <><dt>Tipo</dt><dd>{error.kind === "network" ? "Error de red" : "Error HTTP"}</dd></> : null}
        {error ? <><dt>Mensaje técnico</dt><dd>{error.message}</dd></> : null}
      </dl>
    </details>
  );
}

export function ChatActionBar({ item, sending, onConfirmation, onOpenNewTab }: {
  item: ChatItem;
  sending: boolean;
  onConfirmation: (action: ChatConfirmationAction) => void;
  onOpenNewTab: (route: string) => void;
}) {
  const hasActions = Boolean(item.confirmationActions?.length || item.navigation);
  if (!hasActions) return item.navigation?.indication ? <p className="chat-navigation-status">{item.navigation.indication}</p> : null;
  return (
    <div className="chat-action-area">
      {item.navigation?.indication ? <p className="chat-navigation-status">{item.navigation.indication}</p> : null}
      <div className="chat-actions" aria-label="Acciones de la respuesta">
        {item.confirmationActions?.map((action) => (
          <button key={action.action_id} type="button" className={action.style === "secondary" ? "chat-action-secondary" : "chat-action-primary"} disabled={sending} onClick={() => onConfirmation(action)}>
            {sending ? "Procesando..." : action.label}
          </button>
        ))}
        {item.navigation ? item.navigation.openInNewTab ? (
          <button type="button" className="chat-action-secondary" onClick={() => onOpenNewTab(item.navigation!.to)}>{item.navigation.label}</button>
        ) : (
          <Link className="chat-action-secondary" to={item.navigation.to}>{item.navigation.label}</Link>
        ) : null}
      </div>
    </div>
  );
}

export function UserMessage({ item }: { item: ChatItem }) {
  return <article className="chat-turn chat-turn-user"><div className="chat-user-bubble">{item.text}</div></article>;
}

function formatPurchaseQuantity(value: number, unit: string) {
  return `${new Intl.NumberFormat("es-ES", { maximumFractionDigits: 3 }).format(value)} ${unit}`.trim();
}

export function ChatPurchaseGroups({ groups, actionRoute }: { groups: ChatPurchaseGroup[]; actionRoute?: string }) {
  if (!groups.length) return null;
  return (
    <section className="chat-purchase-groups" aria-label="Compra necesaria por proveedor">
      <h2>🛒 Compra necesaria</h2>
      {groups.map((group) => {
        const action = group.action;
        const route = action?.type === "OPEN_ORDER" && action.pedido_id
          ? `/compras?${new URLSearchParams({ pedido_id: action.pedido_id })}`
          : action?.type === "PREPARE_ORDER" && action.menu_id
            ? `/menus?${new URLSearchParams({ menu_id: action.menu_id, view: "compra" })}`
            : "";
        return (
          <article className="chat-purchase-group" key={group.proveedor}>
            <h3>{group.proveedor}</h3>
            <ul>{group.articulos.map((item) => (
              <li key={`${item.articulo_id}-${item.nombre}`}>
                <p><strong>{item.nombre} — faltan {formatPurchaseQuantity(item.cantidad, item.unidad)}</strong></p>
                <ul>
                  <li>Unidad: {item.unidad}</li>
                  {typeof item.precio_unitario === "number" && item.unidad_precio ? <li>Precio: {item.precio_unitario.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}/{item.unidad_precio}</li> : null}
                  {typeof item.coste_neto === "number" ? <li>Coste estimado: {item.coste_neto.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}</li> : null}
                  <li>Formato de compra: {item.formato || "pendiente"}</li>
                </ul>
              </li>
            ))}</ul>
            {group.pedido_relacionado && group.estado_pedido.toLocaleLowerCase().includes("borrador") ? <div className="chat-purchase-order-note">{group.pedido_relacionado.lineas_relevantes.map((line) => <p key={line.articulo_id}>Ya existe un borrador de {group.proveedor}{line.cantidad_prevista !== null ? ` con ${formatPurchaseQuantity(line.cantidad_prevista, line.unidad)} de ${line.nombre.toLocaleLowerCase("es-ES")}` : ` relacionado con ${line.nombre}`}. El borrador no cuenta como cobertura confirmada{line.cubriria_necesidad ? ", pero su cantidad prevista sería suficiente para cubrir esta necesidad si decides utilizarlo" : ""}.</p>)}</div> : null}
            {route && action && !equivalentNavigation(route, actionRoute) ? <Link className="chat-action-primary" to={route}>{action.label}</Link> : null}
          </article>
        );
      })}
    </section>
  );
}

export function AssistantMessage({ item, sending, onConfirmation, onOpenNewTab }: {
  item: ChatItem;
  sending: boolean;
  onConfirmation: (action: ChatConfirmationAction) => void;
  onOpenNewTab: (route: string) => void;
}) {
  const hasOperationalPresentation = Boolean(item.purchaseGroups?.length || item.operationalIncidents?.length || item.catalogPreview);
  return (
    <article className="chat-turn chat-turn-assistant">
      <div className="chat-assistant-mark" aria-hidden="true">H</div>
      <div className="chat-assistant-body">
        <p className="chat-speaker">Host AI</p>
        {!hasOperationalPresentation ? <MarkdownContent actionRoute={item.navigation?.to}>{item.text}</MarkdownContent> : null}
        {item.purchaseGroups ? <ChatPurchaseGroups groups={item.purchaseGroups} actionRoute={item.navigation?.to} /> : null}
        {item.operationalIncidents?.length ? <section className="chat-operational-incidents" aria-label="Incidencias operativas"><h2>Requiere tu atención</h2><ul>{item.operationalIncidents.map((incident, index) => <li key={`${incident.articulo_id || "incident"}-${index}`}>{incident.articulo_id ? `${incident.articulo_id}: ` : ""}{incident.reason}{incident.unidad ? ` (${incident.unidad})` : ""}</li>)}</ul></section> : null}
        {item.articlePreview ? <ArticleChangePreview preview={item.articlePreview} /> : null}
        {item.catalogPreview && Object.keys(item.catalogPreview).length ? <CatalogCreatePreview value={item.catalogPreview} /> : null}
        <ChatActionBar item={item} sending={sending} onConfirmation={onConfirmation} onOpenNewTab={onOpenNewTab} />
        <ChatTechnicalDetails requestId={item.requestId} safeStatus={item.safeStatus} />
      </div>
    </article>
  );
}

function CatalogCreatePreview({ value }: { value: Record<string, unknown> }) {
  const hidden = new Set(["id", "creado_en", "actualizado_en", "fecha_importacion", "origen"]);
  const preview = value.preview && typeof value.preview === "object" && !Array.isArray(value.preview) ? value.preview as Record<string, unknown> : value;
  const domain = String(value.domain || "registro").toLocaleLowerCase("es-ES");
  const displayOne = (raw: unknown): string => raw && typeof raw === "object" ? [String((raw as Record<string, unknown>).nombre || "Ingrediente"), (raw as Record<string, unknown>).cantidad, (raw as Record<string, unknown>).unidad, (raw as Record<string, unknown>).estado].filter(Boolean).join(" · ") : String(raw ?? "—");
  const display = (raw: unknown): string => Array.isArray(raw) ? raw.map(displayOne).join(" · ") : displayOne(raw);
  return <section className="final-review" aria-label="Vista previa de creación"><h2>Crear {domain}</h2><dl>{Object.entries(preview).filter(([key]) => !hidden.has(key)).map(([key, raw]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{display(raw)}</dd></div>)}</dl><p>Revisa los datos antes de continuar. No se modificarán datos hasta confirmar.</p></section>;
}

export function ChatStatusMessage({ kind, error, safeStatus, onRetry, canRetry }: {
  kind: "loading" | "error" | "security";
  error?: ChatUiError;
  safeStatus?: ChatSafeStatus;
  onRetry?: () => void;
  canRetry?: boolean;
}) {
  const label = kind === "loading" ? "Analizando" : kind === "security" ? "Alerta técnica de seguridad" : "No he podido completar esta consulta.";
  return (
    <article className={`chat-turn chat-turn-assistant chat-status-turn chat-status-${kind}`} role={kind === "error" || kind === "security" ? "alert" : "status"} aria-label={kind === "loading" ? "Indicador de carga" : undefined}>
      <div className="chat-assistant-mark" aria-hidden="true">H</div>
      <div className="chat-assistant-body">
        <p className="chat-speaker">Host AI</p>
        <p className="chat-status-label">{label}{kind === "loading" ? <span className="thinking-dots" aria-hidden="true"><i /><i /><i /></span> : null}</p>
        {kind === "security" ? <p>La API indica que se han modificado datos reales.</p> : null}
        {kind === "error" && onRetry ? <button type="button" className="chat-action-secondary" onClick={onRetry} disabled={!canRetry}>Reintentar</button> : null}
        <ChatTechnicalDetails requestId={error?.requestId} safeStatus={safeStatus} error={error} />
      </div>
    </article>
  );
}

export function ChatMessageList({ items, sending, error, safeStatus, endRef, onRetry, canRetry, onConfirmation, onOpenNewTab }: {
  items: ChatItem[];
  sending: boolean;
  error: ChatUiError | null;
  safeStatus: ChatSafeStatus | null;
  endRef: RefObject<HTMLDivElement>;
  onRetry: () => void;
  canRetry: boolean;
  onConfirmation: (action: ChatConfirmationAction) => void;
  onOpenNewTab: (route: string) => void;
}) {
  return (
    <div className="chat-log" aria-live="polite" aria-label="Conversación">
      {items.length === 0 && !sending && !error ? (
        <div className="chat-empty"><div className="chat-empty-mark" aria-hidden="true">H</div><h2>¿En qué puedo ayudarte?</h2><p>Consulta recetas, producción, stock, compras y la operativa diaria.</p></div>
      ) : null}
      {items.map((item) => item.role === "usuario" ? <UserMessage key={item.id} item={item} /> : (
        <AssistantMessage key={item.id} item={item} sending={sending} onConfirmation={onConfirmation} onOpenNewTab={onOpenNewTab} />
      ))}
      {sending ? <ChatStatusMessage kind="loading" /> : null}
      {error ? <ChatStatusMessage kind="error" error={error} safeStatus={safeStatus || undefined} onRetry={onRetry} canRetry={canRetry} /> : null}
      {safeStatus?.datosRealesModificados ? <ChatStatusMessage kind="security" safeStatus={safeStatus} /> : null}
      <div ref={endRef} aria-hidden="true" />
    </div>
  );
}

export function ChatComposer({ value, sending, canSend, textareaRef, onChange, onSubmit, onKeyDown }: {
  value: string;
  sending: boolean;
  canSend: boolean;
  textareaRef: RefObject<HTMLTextAreaElement>;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onKeyDown: (event: KeyboardEvent<HTMLTextAreaElement>) => void;
}) {
  useLayoutEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 176)}px`;
    textarea.style.overflowY = textarea.scrollHeight > 176 ? "auto" : "hidden";
  }, [value, textareaRef]);

  return (
    <form className="chat-composer" onSubmit={(event) => { event.preventDefault(); onSubmit(); }}>
      <label className="sr-only" htmlFor="mensaje">Mensaje para Host AI</label>
      <textarea id="mensaje" ref={textareaRef} value={value} onChange={(event) => onChange(event.target.value)} onKeyDown={onKeyDown} placeholder="Escribe a Host AI…" rows={1} disabled={sending} aria-describedby="chat-hint" />
      <button type="submit" className="chat-send-button" disabled={!canSend} aria-label={sending ? "Enviando..." : "Enviar"}>
        <span aria-hidden="true">↑</span>
      </button>
      <p id="chat-hint" className="chat-composer-hint">Enter para enviar · Shift+Enter para nueva línea</p>
    </form>
  );
}
