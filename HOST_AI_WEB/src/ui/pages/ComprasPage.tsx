import { useEffect, useRef, useState } from "react";
import { HostAiApiError } from "../../api/client";
import {
  comprasService,
  type ComprasResult,
} from "../../services/comprasService";
import type {
  CompraHistorialListItem,
  CompraListItem,
  PropuestaCompraListItem,
  ProveedorCompraListItem,
} from "../../types/api";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import type { CompraDraft, CompraDraftLine, CompraDraftRevision, PurchaseReception, ReceptionLine } from "../../types/compras";

export function ComprasPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorRequestId, setErrorRequestId] = useState<string | null>(null);
  const [data, setData] = useState<ComprasResult | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let active = true;

    setLoading(true);
    setError(null);
    setErrorRequestId(null);

    comprasService
      .load()
      .then((result) => {
        if (active) setData(result);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setData(null);
        if (err instanceof HostAiApiError) {
          setError(err.message);
          setErrorRequestId(err.requestId || null);
        } else {
          setError("No se pudo cargar la información de compras.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [refreshTick]);

  if (loading) {
    return <LoadingState label="Cargando compras..." />;
  }

  return (
    <section
      className="panel"
      role="region"
      aria-labelledby="compras-title"
    >
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">Operativa</p>
          <h2 id="compras-title">Compras</h2>
          <p className="meta-line">
            Necesidades pendientes y seguimiento de aprovisionamiento
          </p>
        </div>
        <button
          type="button"
          onClick={() => setRefreshTick((value) => value + 1)}
        >
          {error ? "Reintentar" : "Actualizar"}
        </button>
      </header>

      {error ? (
        <>
          <ErrorState
            title="No se pudo cargar la información de compras."
            detail={error}
          />
          <p className="meta-line">
            Request ID: {errorRequestId || "No disponible"}
          </p>
        </>
      ) : (
        <ComprasContent data={data} onSaved={() => setRefreshTick((value) => value + 1)} />
      )}
    </section>
  );
}

function ComprasContent({ data, onSaved }: { data: ComprasResult | null; onSaved: () => void }) {
  const compras = data?.compras ?? [];
  const propuestas = data?.propuestas ?? [];
  const proveedores = data?.proveedores ?? [];
  const historial = data?.historial ?? [];
  const pedidos = data?.pedidos ?? [];

  return (
    <>
      <section className="safe-mode" aria-label="Estado de seguridad">
        <p>
          <strong>Modo seguro:</strong>{" "}
          {data?.modo_seguro ? "Activo" : "Inactivo"}
        </p>
        <p>
          <strong>Datos reales modificados:</strong>{" "}
          {data?.datos_reales_modificados ? "Sí" : "No"}
        </p>
        <p className="meta-line">
          Request ID: {data?.request_id || "No disponible"}
        </p>
      </section>

      {data?.datos_reales_modificados ? (
        <div className="panel-state panel-error" role="alert">
          <p className="panel-error-title">
            La API indica que se han modificado datos reales.
          </p>
        </div>
      ) : null}

      <section className="dashboard-grid" aria-label="Resumen de compras">
        <SummaryCard title="Necesidades abiertas" value={data?.total ?? 0} />
        <SummaryCard title="Propuestas pendientes" value={propuestas.length} />
        <SummaryCard title="Proveedores activos" value={proveedores.length} />
        <SummaryCard title="Compras registradas" value={historial.length} />
        <SummaryCard
          title="Estado del módulo"
          value={readable(data?.estado) || "No disponible"}
        />
      </section>

      <section className="feature-block" aria-label="Compras pendientes">
        <h3>Compras pendientes</h3>
        {compras.length ? (
          <ul className="clean-list compras-list">
            {compras.map((compra, index) => (
              <CompraItem
                key={compra.id || `${compra.nombre || "compra"}-${index}`}
                compra={compra}
              />
            ))}
          </ul>
        ) : (
          <div className="panel-state">
            <p>No hay necesidades de compra pendientes.</p>
            {data?.mensaje ? (
              <p className="meta-line">{data.mensaje}</p>
            ) : null}
          </div>
        )}
      </section>

      <PropuestasSection items={propuestas} />
      <DraftsSection items={pedidos} onSaved={onSaved} />
      <RecepcionesSection items={pedidos} onSaved={onSaved} />
      <ProveedoresSection items={proveedores} />
      <HistorialSection items={historial} />
    </>
  );
}

function DraftsSection({ items, onSaved }: { items: ComprasResult["pedidos"]; onSaved: () => void }) {
  const [draft, setDraft] = useState<CompraDraft | null>(null);
  const [revision, setRevision] = useState<CompraDraftRevision | null>(null);
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [message, setMessage] = useState("");
  const confirming = useRef(false);
  const open = async (id: string) => {
    setBusy(true); setMessage("");
    try { const response = await comprasService.getDraft(id); setDraft(response.borrador); setRevision(response.revision || null); setDirty(false); }
    catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo abrir el borrador."); }
    finally { setBusy(false); }
  };
  const updateDraft = (next: CompraDraft) => { setDraft(next); setDirty(true); };
  const changeLine = (index: number, field: keyof CompraDraftLine, value: string) => {
    if (!draft) return;
    updateDraft({ ...draft, lineas: draft.lineas.map((line, position) => position === index ? { ...line, [field]: field === "cantidad" || field === "precio_unitario" ? Number(value) : value } : line) });
  };
  const save = async () => {
    if (!draft) return;
    setBusy(true); setMessage("");
    try { const response = await comprasService.saveDraft(draft.id, { proveedor: draft.proveedor, observaciones: draft.observaciones, lineas: draft.lineas }); setDraft(response.borrador); setRevision(response.revision || null); setDirty(false); setMessage("Borrador guardado y validado."); onSaved(); }
    catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo guardar el borrador."); }
    finally { setBusy(false); }
  };
  const confirm = async () => {
    if (!draft || dirty || confirming.current || revision?.errores_bloqueantes.length) return;
    const total = draft.lineas.reduce((sum, line) => sum + line.cantidad * line.precio_unitario, 0);
    if (!window.confirm(`Se creará un pedido real para ${draft.proveedor} con ${draft.lineas.length} líneas y total estimado ${money(total)}.`)) return;
    confirming.current = true; setBusy(true); setMessage("Creando pedido...");
    try { const response = await comprasService.confirmDraft(draft.id, draft.actualizado_en); setDraft(response.pedido); setRevision({ valido: true, errores_bloqueantes: [], advertencias: response.advertencias }); setDirty(false); setMessage(response.idempotente ? "Este borrador ya estaba convertido; se muestra el pedido existente." : "Pedido creado correctamente en estado preparado."); onSaved(); }
    catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo crear el pedido."); }
    finally { confirming.current = false; setBusy(false); }
  };
  const editable = draft?.estado === "borrador";
  const orderStatusMessage = draft?.estado === "parcialmente_recibido"
    ? "Estado: parcialmente recibido. Quedan cantidades pendientes y puede registrarse otra recepción."
    : draft?.estado === "recibido"
      ? "Estado: recibido. El pedido está completamente recibido."
      : "Estado preparado: pendiente de recepción.";
  const total = draft?.lineas.reduce((sum, line) => sum + line.cantidad * line.precio_unitario, 0) || 0;
  return <section className="feature-block" aria-label="Borradores de pedido"><h3>Borradores y pedidos</h3>{items.length ? <ul className="clean-list compras-list">{items.map((item) => <li className="compra-item" key={item.id}><div><strong>{item.proveedor}</strong><p className="meta-line">{item.estado} · {item.observaciones || "Sin referencia"}</p></div><div><p>{item.lineas.length} líneas · {money(item.importe_estimado)}</p><button type="button" onClick={() => void open(item.id)}>{item.estado === "borrador" ? "Abrir borrador" : "Abrir pedido"}</button></div></li>)}</ul> : <div className="panel-state"><p>No hay borradores ni pedidos.</p></div>}{busy ? <p aria-live="polite">Procesando...</p> : null}{message ? <p role="status">{message}</p> : null}{draft ? <div className="menu-editor" id={`pedido-${draft.id}`}><h4>{editable ? "Editar borrador" : "Pedido"} {draft.id}</h4><p className="meta-line">Menú origen: {draft.origen.id || "No disponible"} · versión {draft.origen.version || "No disponible"} · propuesta {draft.origen.propuesta_id || "No disponible"} · {formatDate(draft.creado_en)}</p><label>Proveedor<input disabled={!editable} value={draft.proveedor} onChange={(event) => updateDraft({ ...draft, proveedor: event.target.value })} /></label>{editable ? <p className="meta-line">Cambiar el proveedor reagrupará todas las líneas de este borrador.</p> : null}{draft.lineas.map((line, index) => <fieldset disabled={!editable} key={line.id || index}><legend>Artículo {index + 1}</legend><label>Artículo<input value={line.nombre} onChange={(event) => changeLine(index, "nombre", event.target.value)} /></label><label>Cantidad<input aria-label={`Cantidad ${index + 1}`} type="number" min="0.001" step="any" value={line.cantidad} onChange={(event) => changeLine(index, "cantidad", event.target.value)} /></label><label>Unidad<input value={line.unidad} onChange={(event) => changeLine(index, "unidad", event.target.value)} /></label><label>Precio unitario<input aria-label={`Precio ${index + 1}`} type="number" min="0" step="any" value={line.precio_unitario} onChange={(event) => changeLine(index, "precio_unitario", event.target.value)} /></label><label>Observaciones<input value={line.observaciones || ""} onChange={(event) => changeLine(index, "observaciones", event.target.value)} /></label>{editable ? <button type="button" onClick={() => updateDraft({ ...draft, lineas: draft.lineas.filter((_, position) => position !== index) })}>Eliminar línea</button> : null}</fieldset>)}{editable ? <button type="button" onClick={() => updateDraft({ ...draft, lineas: [...draft.lineas, { nombre: "", cantidad: 1, unidad: "u", precio_unitario: 0 }] })}>Añadir línea</button> : null}<section className="final-review" aria-label="Revisión final"><h5>Revisión final</h5><dl><div><dt>Proveedor</dt><dd>{draft.proveedor}</dd></div><div><dt>Líneas</dt><dd>{draft.lineas.length}</dd></div><div><dt>Subtotal</dt><dd>{money(total)}</dd></div><div><dt>Impuestos</dt><dd>No desglosados</dd></div><div><dt>Total estimado</dt><dd>{money(total)}</dd></div><div><dt>Estado</dt><dd>{draft.estado}</dd></div></dl>{revision?.errores_bloqueantes.length ? <div role="alert"><strong>Errores que impiden crear el pedido</strong><ul>{revision.errores_bloqueantes.map((issue, index) => <li key={`${issue.code}-${index}`}>{issue.message}</li>)}</ul></div> : null}{revision?.advertencias.length ? <div><strong>Advertencias</strong><ul>{revision.advertencias.map((issue, index) => <li key={`${issue.code}-${index}`}>{issue.message}</li>)}</ul></div> : null}{dirty ? <p className="draft-warning">Guarda los cambios antes de confirmar.</p> : null}{editable ? <><button type="button" disabled={busy || dirty || !revision?.valido} onClick={() => void confirm()}>Confirmar y crear pedido</button><p className="meta-line">El pedido quedará preparado, no enviado. Stock e inventario no cambiarán.</p></> : <><p><strong>Pedido:</strong> {draft.id}</p><a href={`#pedido-${draft.id}`}>Ver pedido</a><p className="meta-line">{orderStatusMessage}</p></>}</section>{editable ? <button type="button" disabled={busy} onClick={() => void save()}>Guardar borrador</button> : null}</div> : null}</section>;
}

function RecepcionesSection({ items, onSaved }: { items: ComprasResult["pedidos"]; onSaved: () => void }) {
  const [reception, setReception] = useState<PurchaseReception | null>(null);
  const [busy, setBusy] = useState(false); const [message, setMessage] = useState(""); const confirming = useRef(false);
  const start = async (orderId: string) => { setBusy(true); setMessage(""); try { setReception((await comprasService.createReception(orderId)).recepcion); setMessage("Borrador de recepción preparado. Stock sin cambios."); } catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo iniciar la recepción."); } finally { setBusy(false); } };
  const change = (index: number, field: keyof ReceptionLine, value: string) => { if (!reception) return; setReception({ ...reception, lineas: reception.lineas.map((line, position) => position === index ? { ...line, [field]: field === "received_quantity" ? Number(value || 0) : field === "received_price" ? (value === "" ? null : Number(value)) : value } as ReceptionLine : line) }); };
  const save = async () => { if (!reception) return; setBusy(true); setMessage(""); try { setReception((await comprasService.saveReception(reception.id, reception.lineas, { fecha: reception.fecha, referencia: reception.referencia, observaciones: reception.observaciones })).recepcion); setMessage("Borrador guardado. Stock sin cambios."); } catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo guardar la recepción."); } finally { setBusy(false); } };
  const confirm = async () => { if (!reception || confirming.current || reception.estado === "CONFIRMADA") return; if (!window.confirm("Se guardará la revisión visible y se registrará en Stock exactamente lo recibido.")) return; confirming.current = true; setBusy(true); setMessage(""); try { const saved = await comprasService.saveReception(reception.id, reception.lineas, { fecha: reception.fecha, referencia: reception.referencia, observaciones: reception.observaciones }); setReception(saved.recepcion); if (!saved.recepcion.confirmable) { setMessage("La revisión se guardó, pero contiene incidencias que impiden confirmarla."); return; } const response = await comprasService.confirmReception(saved.recepcion.id); setReception(response.recepcion); setMessage(response.idempotente ? "La recepción ya estaba confirmada; Stock no se duplicó." : "Recepción confirmada y Stock actualizado."); onSaved(); } catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo confirmar la recepción."); } finally { confirming.current = false; setBusy(false); } };
  const receivable = items.filter((item) => ["preparado", "enviado", "parcialmente_recibido"].includes(item.estado));
  return <section className="feature-block" aria-label="Recepciones de mercancía"><h3>Recepciones de mercancía</h3>{receivable.map((order) => <button key={order.id} disabled={busy} onClick={() => void start(order.id)}>Registrar recepción de {order.id}</button>)}{!receivable.length ? <p>No hay pedidos preparados pendientes de recepción.</p> : null}{message ? <p role="status">{message}</p> : null}{reception ? <section className="menu-editor" aria-label="Revisar recepción"><h4>Recepción {reception.reception_id}</h4><p>Proveedor: {reception.proveedor} · Pedido: {reception.order_id}</p><strong>Estado: {reception.estado}</strong><label>Fecha de recepción<input type="date" disabled={reception.estado === "CONFIRMADA"} value={reception.fecha || ""} onChange={(event) => setReception({ ...reception, fecha: event.target.value })} /></label><label>Referencia del albarán<input disabled={reception.estado === "CONFIRMADA"} value={reception.referencia || ""} onChange={(event) => setReception({ ...reception, referencia: event.target.value })} /></label>{reception.lineas.map((line, index) => <fieldset disabled={reception.estado === "CONFIRMADA"} key={line.order_line_id}><legend>{line.article_name}</legend><p>Pedido: {line.ordered_quantity} {line.unit} · Ya recibido: {line.previously_received} {line.unit} · Pendiente: {line.pending_quantity} {line.unit}</p><label>Cantidad recibida ahora<input aria-label={`Cantidad recibida ${index + 1}`} type="number" min="0" step="any" value={line.received_quantity} onChange={(event) => change(index, "received_quantity", event.target.value)} /></label><label>Unidad<input aria-label={`Unidad recibida ${index + 1}`} value={line.unit} onChange={(event) => change(index, "unit", event.target.value)} /></label>{line.canonical_unit && line.canonical_unit !== line.unit ? <p className="meta-line">Stock: {line.stock_quantity} {line.canonical_unit}</p> : null}<p>Precio pedido: {money(line.order_price)}</p><label>Precio recibido<input aria-label={`Precio recibido ${index + 1}`} type="number" min="0" step="any" value={line.received_price ?? ""} onChange={(event) => change(index, "received_price", event.target.value)} /></label><label>Lote<input aria-label={`Lote ${index + 1}`} value={line.lot} onChange={(event) => change(index, "lot", event.target.value)} /></label><label>Caducidad<input aria-label={`Caducidad ${index + 1}`} type="date" value={line.expiry} onChange={(event) => change(index, "expiry", event.target.value)} /></label><label>Ubicación<input aria-label={`Ubicación ${index + 1}`} value={line.location} onChange={(event) => change(index, "location", event.target.value)} /></label><label>Observaciones<input aria-label={`Observaciones recepción ${index + 1}`} value={line.observations} onChange={(event) => change(index, "observations", event.target.value)} /></label>{line.incidences.length ? <ul>{line.incidences.map((issue) => <li key={issue.code}>{issue.message}</li>)}</ul> : null}</fieldset>)}{reception.incidencias.some((issue) => issue.bloqueante) ? <p role="alert">Hay incidencias que impiden confirmar la recepción.</p> : null}{reception.estado === "CONFIRMADA" ? <p role="status">Recepción CONFIRMADA. Los movimientos de Stock son inmutables.</p> : <div><button disabled={busy} onClick={() => void save()}>Guardar borrador de recepción</button><button disabled={busy || !reception.confirmable} onClick={() => void confirm()}>Confirmar recepción</button></div>}</section> : null}</section>;
}

function money(value: number): string { return value.toLocaleString("es-ES", { style: "currency", currency: "EUR" }); }

function SummaryCard({
  title,
  value,
}: {
  title: string;
  value: string | number;
}) {
  return (
    <article className="data-card">
      <h3>{title}</h3>
      <p className="stat-value">{value}</p>
    </article>
  );
}

function CompraItem({ compra }: { compra: CompraListItem }) {
  return (
    <li className="compra-item">
      <div>
        <strong>{text(compra.nombre) || "Compra sin nombre"}</strong>
        <p className="meta-line">
          Estado: {readable(compra.estado) || "No disponible"}
        </p>
      </div>
      <dl className="compra-meta">
        <div>
          <dt>Prioridad</dt>
          <dd>{formatPriority(compra.prioridad)}</dd>
        </div>
        <div>
          <dt>Fecha necesaria</dt>
          <dd>{formatDate(compra.fecha_necesaria) || "No disponible"}</dd>
        </div>
      </dl>
    </li>
  );
}

function PropuestasSection({
  items,
}: {
  items: PropuestaCompraListItem[];
}) {
  return (
    <section className="feature-block" aria-label="Propuestas de compra">
      <h3>Propuestas de compra</h3>
      {items.length ? (
        <ul className="clean-list compras-list">
          {items.map((item, index) => (
            <li
              className="compra-item"
              key={item.id || `${item.producto || "propuesta"}-${index}`}
            >
              <div>
                <strong>{text(item.producto) || "Producto sin nombre"}</strong>
                <p className="meta-line">
                  Estado: {readable(item.estado) || "No disponible"}
                </p>
              </div>
              <p>
                {formatQuantity(item.comprar, item.unidad)}
                {" · "}
                {text(item.proveedor_sugerido) || "Sin proveedor sugerido"}
              </p>
            </li>
          ))}
        </ul>
      ) : (
        <div className="panel-state">
          <p>No hay propuestas de compra pendientes.</p>
        </div>
      )}
    </section>
  );
}

function ProveedoresSection({
  items,
}: {
  items: ProveedorCompraListItem[];
}) {
  return (
    <section className="feature-block" aria-label="Proveedores activos">
      <h3>Proveedores activos</h3>
      {items.length ? (
        <ul className="clean-list compras-list">
          {items.map((item, index) => (
            <li
              className="compra-item"
              key={item.id || `${item.nombre || "proveedor"}-${index}`}
            >
              <div>
                <strong>{text(item.nombre) || "Proveedor sin nombre"}</strong>
                <p className="meta-line">
                  Estado: {readable(item.estado) || "No disponible"}
                </p>
              </div>
              <p>{text(item.email) || text(item.telefono) || "Sin contacto"}</p>
            </li>
          ))}
        </ul>
      ) : (
        <div className="panel-state">
          <p>No hay proveedores activos.</p>
        </div>
      )}
    </section>
  );
}

function HistorialSection({
  items,
}: {
  items: CompraHistorialListItem[];
}) {
  return (
    <section className="feature-block" aria-label="Historial de compras">
      <h3>Historial de compras</h3>
      {items.length ? (
        <ul className="clean-list compras-list">
          {items.map((item, index) => (
            <li
              className="compra-item"
              key={item.id || `${item.producto || "compra"}-${index}`}
            >
              <div>
                <strong>{text(item.producto) || "Producto sin nombre"}</strong>
                <p className="meta-line">
                  {text(item.proveedor) || "Sin proveedor"}
                </p>
              </div>
              <p>
                {formatQuantity(item.cantidad, item.unidad)}
                {" · "}
                {formatDate(item.creado_en) || "Fecha no disponible"}
              </p>
            </li>
          ))}
        </ul>
      ) : (
        <div className="panel-state">
          <p>No hay compras registradas.</p>
        </div>
      )}
    </section>
  );
}

function UnavailableSection({
  title,
  text: detail,
}: {
  title: string;
  text: string;
}) {
  return (
    <section className="feature-block" aria-label={title}>
      <h3>{title}</h3>
      <p className="meta-line">{detail}</p>
    </section>
  );
}

function text(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function readable(value: unknown): string {
  const valueText = text(value);
  if (!valueText) return "";
  const normalized = valueText.replaceAll("_", " ").toLowerCase();
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function formatPriority(value: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "No disponible";
  }
  return String(value);
}

function formatQuantity(value: unknown, unit: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "Cantidad no disponible";
  }
  return `${value.toLocaleString("es-ES")} ${text(unit)}`.trim();
}

function formatDate(value: unknown): string {
  const valueText = text(value);
  if (!valueText) return "";
  const isoDate = /^\d{4}-\d{2}-\d{2}$/.test(valueText);
  const date = new Date(isoDate ? `${valueText}T00:00:00Z` : valueText);
  if (Number.isNaN(date.getTime())) return valueText;
  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "medium",
    timeZone: isoDate ? "UTC" : undefined,
  }).format(date);
}
