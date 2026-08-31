import { FormEvent, useRef, useState } from "react";
import { HostAiApiError } from "../../api/client";
import { reservasService } from "../../services/reservasService";
import type { ReservaDetalle, ReservaPreviewResponse, ReservaServicio, ReservaWriteInput, ReservaWriteOperation } from "../../types/reservas";

const EMPTY: ReservaWriteInput = { nombre_cliente: "", fecha: "", hora: "", pax: 1, servicio: "COMIDA", observaciones: "", evento_id: null };

export function ReservaWritePanel({ operation, reservaId = "", initial, label, onConfirmed, defaultOpen = false }: {
  operation: ReservaWriteOperation; reservaId?: string; initial?: Partial<ReservaDetalle>;
  label: string; onConfirmed: (item: ReservaDetalle) => void; defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const [draft, setDraft] = useState<ReservaWriteInput>({ ...EMPTY, ...initial });
  const [preview, setPreview] = useState<ReservaPreviewResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const sessionId = useRef(crypto.randomUUID());
  const formOperation = operation === "CREAR" || operation === "MODIFICAR";

  async function prepare(event?: FormEvent) {
    event?.preventDefault(); setBusy(true); setError("");
    const payload = operation === "CREAR" ? draft : operation === "MODIFICAR" ? editableChanges(draft, initial) : {};
    try { setPreview(await reservasService.preview(operation, payload, reservaId, sessionId.current)); }
    catch (reason) { setError(reason instanceof HostAiApiError ? reason.message : "No se pudo preparar la operación."); }
    finally { setBusy(false); }
  }
  async function confirm() {
    if (!preview) return; setBusy(true); setError("");
    try { const result = await reservasService.confirm(preview.preview_token, sessionId.current); setPreview(null); setOpen(false); onConfirmed(result.reserva); }
    catch (reason) { setError(reason instanceof HostAiApiError ? reason.message : "No se pudo confirmar la operación."); }
    finally { setBusy(false); }
  }
  if (!open) return <button type="button" onClick={() => setOpen(true)}>{label}</button>;
  return <section className="reserva-write-panel" aria-label={`${label} reserva`}>
    {!preview ? <form onSubmit={prepare}>
      {formOperation ? <>
        <label>Nombre del cliente<input required value={draft.nombre_cliente} onChange={(e) => setDraft({ ...draft, nombre_cliente: e.target.value })} /></label>
        <label>Fecha<input required type="date" value={draft.fecha} onChange={(e) => setDraft({ ...draft, fecha: e.target.value })} /></label>
        <label>Hora<input required type="time" value={draft.hora} onChange={(e) => setDraft({ ...draft, hora: e.target.value })} /></label>
        <label>Personas<input required type="number" min="1" value={draft.pax} onChange={(e) => setDraft({ ...draft, pax: Number(e.target.value) })} /></label>
        <label>Servicio<select value={draft.servicio} onChange={(e) => setDraft({ ...draft, servicio: e.target.value as ReservaServicio })}><option value="COMIDA">Comida</option><option value="CENA">Cena</option></select></label>
        <label>Observaciones<textarea value={draft.observaciones || ""} onChange={(e) => setDraft({ ...draft, observaciones: e.target.value })} /></label>
        <label>Evento asociado<input value={draft.evento_id || ""} onChange={(e) => setDraft({ ...draft, evento_id: e.target.value || null })} /></label>
      </> : operation === "ELIMINAR" ? <p>Se preparará la baja lógica de la reserva. Se conservarán su historial, referencias y trazabilidad.</p> : <p>Se preparará el cambio de estado. La reserva no se modificará hasta confirmar.</p>}
      <button type="submit" disabled={busy}>{busy ? "Preparando…" : "Revisar cambios"}</button>
      <button type="button" onClick={() => { setOpen(false); setError(""); }}>Cerrar</button>
    </form> : <div role="dialog" aria-label="Confirmar operación de reserva">
      <h3>{operation === "ELIMINAR" ? "Eliminar reserva" : "Revisa antes de confirmar"}</h3>
      <dl><dt>Cliente</dt><dd>{preview.propuesto.nombre_cliente}</dd><dt>Fecha</dt><dd>{preview.propuesto.fecha}</dd><dt>Hora</dt><dd>{preview.propuesto.hora}</dd><dt>Personas</dt><dd>{preview.propuesto.pax}</dd><dt>Servicio</dt><dd>{preview.propuesto.servicio}</dd><dt>Estado</dt><dd>{preview.propuesto.estado}</dd></dl>
      {preview.propuesto.observaciones ? <p>Observaciones: {preview.propuesto.observaciones}</p> : null}
      {operation === "ELIMINAR" ? <p>Consecuencia: dejará de aparecer en la operativa activa sin borrar físicamente el registro.</p> : null}
      <button type="button" disabled={busy} onClick={confirm}>{busy ? "Confirmando…" : operation === "ELIMINAR" ? "Confirmar eliminación" : "Confirmar operación"}</button>
      <button type="button" disabled={busy} onClick={() => setPreview(null)}>Cancelar preview</button>
    </div>}
    {error ? <p role="alert">{error}</p> : null}
  </section>;
}

function editableChanges(draft: ReservaWriteInput, initial?: Partial<ReservaDetalle>): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const key of ["nombre_cliente", "fecha", "hora", "pax", "servicio", "observaciones", "evento_id"] as const) {
    if (draft[key] !== initial?.[key]) result[key] = draft[key];
  }
  return result;
}
