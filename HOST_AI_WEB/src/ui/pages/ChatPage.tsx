import { FormEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import { HostAiApiError } from "../../api/client";
import { chatService } from "../../services/chatService";
import type { ApiEnvelopeBase, ChatResponse } from "../../types/api";

type ChatItem = {
  id: string;
  role: "usuario" | "host_ai";
  text: string;
  requestId?: string;
};

type ChatUiError = {
  kind: "network" | "http";
  message: string;
  requestId?: string;
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

export function ChatPage() {
  const [mensaje, setMensaje] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<ChatUiError | null>(null);
  const [items, setItems] = useState<ChatItem[]>([]);
  const [lastSent, setLastSent] = useState<string | null>(null);
  const [safeState, setSafeState] = useState<{
    modoSeguro: boolean;
    datosRealesModificados: boolean;
  } | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [items, sending, error]);

  const canSend = useMemo(() => Boolean(mensaje.trim()) && !sending, [mensaje, sending]);

  async function submitMessage(rawMessage: string) {
    const text = rawMessage.trim();
    if (!text || sending) {
      return;
    }

    setMensaje("");
    setError(null);
    setSending(true);
    setLastSent(text);
    setItems((prev) => [...prev, { id: crypto.randomUUID(), role: "usuario", text }]);

    try {
      const response = await chatService.send({ mensaje: text, contexto: {} });
      setSafeState(getSafeStatus(response));
      setItems((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "host_ai",
          text: getResponseText(response),
          requestId: response.request_id,
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
      setSending(false);
      textareaRef.current?.focus();
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
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
    <section className="panel chat-panel" aria-label="Chat operativo de Host AI">
      <div className="chat-header">
        <h2>Chat operativo</h2>
        <p className="meta-line">Conversacion profesional via API</p>
      </div>

      {safeState ? (
        <div className="safe-mode" role="status" aria-live="polite">
          <p className="meta-line">Modo seguro: {safeState.modoSeguro ? "activo" : "inactivo"}</p>
          <p className="meta-line">
            Datos reales modificados: {safeState.datosRealesModificados ? "si" : "no"}
          </p>
        </div>
      ) : null}

      {safeState?.datosRealesModificados ? (
        <div className="panel-state panel-error" role="alert" aria-live="assertive">
          <p className="panel-error-title">Alerta tecnica de seguridad</p>
          <p className="panel-error-detail">La API indica datos_reales_modificados=true.</p>
        </div>
      ) : null}

      <form onSubmit={onSubmit} className="chat-form">
        <label htmlFor="mensaje">Mensaje para Host AI</label>
        <textarea
          id="mensaje"
          ref={textareaRef}
          value={mensaje}
          onChange={(e) => setMensaje(e.target.value)}
          onKeyDown={onTextareaKeyDown}
          placeholder="Escribe tu consulta operativa"
          rows={3}
          disabled={sending}
          aria-describedby="chat-hint"
        />
        <p id="chat-hint" className="meta-line">
          Enter envia. Shift+Enter inserta salto de linea.
        </p>
        <button type="submit" disabled={!canSend}>
          {sending ? "Enviando..." : "Enviar"}
        </button>
      </form>

      {sending ? (
        <div className="panel-state" role="status" aria-live="polite" aria-label="Indicador de carga">
          <span className="spinner" aria-hidden="true" />
          <span>Cargando respuesta...</span>
        </div>
      ) : null}

      {error ? (
        <div className="panel-state panel-error" role="alert" aria-live="assertive">
          <p className="panel-error-title">{error.kind === "network" ? "Error de red" : "Error HTTP"}</p>
          <p className="panel-error-detail">{error.message}</p>
          {error.requestId ? <p className="panel-error-detail">Request ID: {error.requestId}</p> : null}
          <button type="button" className="button-link-secondary" onClick={onRetry} disabled={!lastSent || sending}>
            Reintentar
          </button>
        </div>
      ) : null}

      <div className="chat-log" aria-live="polite" aria-label="Panel de mensajes">
        {items.length === 0 ? <p className="chat-empty">Sin mensajes todavia.</p> : null}
        {items.map((item) => (
          <article key={item.id} className={`chat-item chat-item-${item.role}`}>
            <p>{item.text}</p>
            {item.requestId ? <small>Request ID: {item.requestId}</small> : null}
          </article>
        ))}
        <div ref={messagesEndRef} aria-hidden="true" />
      </div>
    </section>
  );
}
