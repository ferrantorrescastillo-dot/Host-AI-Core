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
import type { CompraDraft, CompraDraftLine, CompraDraftRevision, PurchaseReception, ReceptionExtractionLine, ReceptionLine } from "../../types/compras";
import { articulosService } from "../../services/articulosService";
import type { ArticuloResumen } from "../../types/articulos";

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
      <ManualOrderSection providers={proveedores} onSaved={onSaved} />
      <DraftsSection items={pedidos} onSaved={onSaved} />
      <RecepcionesSection items={pedidos} onSaved={onSaved} />
      <ProveedoresSection items={proveedores} />
      <HistorialSection items={historial} />
    </>
  );
}

function ManualOrderSection({ providers, onSaved }: { providers: ProveedorCompraListItem[]; onSaved: () => void }) {
  const [open, setOpen] = useState(false);
  const [providerQuery, setProviderQuery] = useState("");
  const [provider, setProvider] = useState<ProveedorCompraListItem | null>(null);
  const [articleQuery, setArticleQuery] = useState("");
  const [articles, setArticles] = useState<ArticuloResumen[]>([]);
  const [lines, setLines] = useState<CompraDraftLine[]>([]);
  const [fecha, setFecha] = useState(() => new Date().toISOString().slice(0, 10));
  const [referencia, setReferencia] = useState("");
  const [observaciones, setObservaciones] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const matchingProviders = providers.filter((item) => (item.nombre || "").toLocaleLowerCase("es").includes(providerQuery.toLocaleLowerCase("es")));
  const searchArticles = async () => { setBusy(true); setMessage(""); try { const response = await articulosService.list({ q: articleQuery, page_size: 20 }); setArticles(response.catalogo.items); } catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo buscar en Artículos."); } finally { setBusy(false); } };
  const addArticle = async (item: ArticuloResumen) => { if (!provider) return; setBusy(true); try { const detail = (await articulosService.get(item.id)).articulo; const relation = detail.proveedores.find((row) => row.id === provider.id || row.nombre?.toLocaleLowerCase("es") === provider.nombre?.toLocaleLowerCase("es")); setLines((current) => [...current, { articulo_id: item.id, nombre: detail.nombre, cantidad: 1, unidad: detail.unidad_compra || detail.unidad_base || "kg", precio_unitario: relation?.precio ?? detail.precio ?? 0, observaciones: "" }]); setArticles([]); setArticleQuery(""); } catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo seleccionar el artículo."); } finally { setBusy(false); } };
  const changeLine = (index: number, field: keyof CompraDraftLine, value: string) => setLines((current) => current.map((line, position) => position === index ? { ...line, [field]: field === "cantidad" || field === "precio_unitario" ? Number(value || 0) : value } : line));
  const total = lines.reduce((sum, line) => sum + line.cantidad * line.precio_unitario, 0);
  const save = async () => { if (!provider) { setMessage("Selecciona un proveedor real."); return; } setBusy(true); setMessage(""); try { const response = await comprasService.createManualDraft({ proveedor: provider.nombre || "", proveedor_id: provider.id, fecha, referencia, observaciones, lineas: lines }); setMessage(`Borrador ${response.borrador.id} guardado. Stock sin cambios. Ábrelo en Borradores y pedidos para revisarlo y confirmarlo.`); setOpen(false); setLines([]); onSaved(); } catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo guardar el pedido."); } finally { setBusy(false); } };
  return <section className="feature-block" aria-label="Nuevo pedido manual"><button type="button" onClick={() => setOpen((value) => !value)}>Nuevo pedido</button>{message ? <p role="status">{message}</p> : null}{open ? <div className="menu-editor"><h3>Nuevo pedido</h3><label>Buscar proveedor<input value={providerQuery} onChange={(event) => setProviderQuery(event.target.value)} /></label><ul>{matchingProviders.map((item) => <li key={item.id || item.nombre}><button type="button" onClick={() => setProvider(item)}>{item.nombre}</button></li>)}</ul><p>Proveedor seleccionado: <strong>{provider?.nombre || "Ninguno"}</strong></p><label>Fecha<input type="date" value={fecha} onChange={(event) => setFecha(event.target.value)} /></label><label>Referencia<input value={referencia} onChange={(event) => setReferencia(event.target.value)} /></label><label>Observaciones<input value={observaciones} onChange={(event) => setObservaciones(event.target.value)} /></label><h4>Artículos</h4><label>Buscar artículo<input value={articleQuery} onChange={(event) => setArticleQuery(event.target.value)} /></label><button type="button" disabled={busy || !provider || !articleQuery.trim()} onClick={() => void searchArticles()}>Añadir artículo</button><ul>{articles.map((item) => <li key={item.id}><button type="button" onClick={() => void addArticle(item)}>{item.nombre} · {item.codigo}</button></li>)}</ul>{lines.map((line, index) => <fieldset key={`${line.articulo_id}-${index}`}><legend>{line.nombre}</legend><p>article_id: {line.articulo_id}</p><label>Cantidad<input aria-label={`Cantidad manual ${index + 1}`} type="number" min="0.001" step="any" value={line.cantidad} onChange={(event) => changeLine(index, "cantidad", event.target.value)} /></label><label>Unidad<input aria-label={`Unidad manual ${index + 1}`} value={line.unidad} onChange={(event) => changeLine(index, "unidad", event.target.value)} /></label><label>Precio unitario<input aria-label={`Precio manual ${index + 1}`} type="number" min="0" step="any" value={line.precio_unitario} onChange={(event) => changeLine(index, "precio_unitario", event.target.value)} /></label><label>Observaciones de línea<input value={line.observaciones || ""} onChange={(event) => changeLine(index, "observaciones", event.target.value)} /></label><p>Subtotal: {money(line.cantidad * line.precio_unitario)}</p><button type="button" onClick={() => setLines((current) => current.filter((_, position) => position !== index))}>Eliminar línea</button></fieldset>)}<p><strong>Total pedido: {money(total)}</strong></p><button type="button" disabled={busy || !provider || !lines.length} onClick={() => void save()}>Guardar borrador</button><p className="meta-line">Guardar el borrador no modifica Stock.</p></div> : null}</section>;
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
  const [extractionLines, setExtractionLines] = useState<ReceptionExtractionLine[]>([]); const [ocrText, setOcrText] = useState("");
  const [busy, setBusy] = useState(false); const [message, setMessage] = useState(""); const confirming = useRef(false);
  const start = async (orderId: string) => { setBusy(true); setMessage(""); try { const next = (await comprasService.createReception(orderId)).recepcion; setReception(next); setExtractionLines(next.extraccion_documental?.lines || []); setMessage("Borrador de recepción preparado. Stock sin cambios."); } catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo iniciar la recepción."); } finally { setBusy(false); } };
  const change = (index: number, field: keyof ReceptionLine, value: string) => { if (!reception) return; setReception({ ...reception, lineas: reception.lineas.map((line, position) => position === index ? { ...line, [field]: field === "received_quantity" ? Number(value || 0) : field === "received_price" ? (value === "" ? null : Number(value)) : value } as ReceptionLine : line) }); };
  const save = async () => { if (!reception) return; setBusy(true); setMessage(""); try { setReception((await comprasService.saveReception(reception.id, reception.lineas, { fecha: reception.fecha, referencia: reception.referencia, observaciones: reception.observaciones })).recepcion); setMessage("Borrador guardado. Stock sin cambios."); } catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo guardar la recepción."); } finally { setBusy(false); } };
  const confirm = async () => { if (!reception || confirming.current || reception.estado === "CONFIRMADA") return; if (!window.confirm("Se confirmará esta revisión y se registrará en Stock exactamente lo visible.")) return; confirming.current = true; setBusy(true); setMessage(""); try { const response = await comprasService.confirmReception(reception); setReception(response.recepcion); setMessage(response.idempotente ? "La recepción ya estaba confirmada; Stock no se duplicó." : "Recepción confirmada con los valores visibles y Stock actualizado."); onSaved(); } catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo confirmar la recepción."); } finally { confirming.current = false; setBusy(false); } };
  const attachDocument = async (file?: File) => { if (!reception || !file) return; setBusy(true); setMessage("Adjuntando albarán..."); try { const response = await comprasService.attachReceptionDocument(reception.id, file, reception.referencia); if (response.recepcion) setReception(response.recepcion); setMessage(response.idempotente ? "Este documento ya estaba adjunto." : "Albarán adjunto. Pendiente de revisión; Stock sin cambios."); } catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo adjuntar el albarán."); } finally { setBusy(false); } };
  const viewDocument = async () => { if (!reception) return; setBusy(true); try { const response = await comprasService.getReceptionDocument(reception.id); const encoded = response.documento.contenido_base64 || ""; const binary = atob(encoded); const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0)); const url = URL.createObjectURL(new Blob([bytes], { type: response.documento.tipo_mime })); window.open(url, "_blank", "noopener,noreferrer"); window.setTimeout(() => URL.revokeObjectURL(url), 60_000); } catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo abrir el documento."); } finally { setBusy(false); } };
  const removeDocument = async () => { if (!reception) return; setBusy(true); try { setReception((await comprasService.removeReceptionDocument(reception.id)).recepcion); setMessage("Documento quitado. Stock sin cambios."); } catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo quitar el documento."); } finally { setBusy(false); } };
  const analyzeDocument = async () => { if (!reception) return; setBusy(true); setMessage("Analizando albarán..."); try { const response = await comprasService.analyzeReceptionDocument(reception.id, ocrText); setReception({ ...response.recepcion, extraccion_documental: response.extraccion }); setExtractionLines(response.extraccion.lines); setMessage("Albarán analizado. Revisa la propuesta; Stock sin cambios."); } catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo analizar el albarán."); } finally { setBusy(false); } };
  const updateExtraction = (index: number, patch: Partial<ReceptionExtractionLine>) => setExtractionLines((items) => items.map((item, position) => position === index ? { ...item, ...patch } : item));
  const chooseCandidate = (index: number, articleId: string) => { const line = extractionLines[index]; const candidate = line.candidates.find((item) => item.article_id === articleId); if (!candidate) return; updateExtraction(index, { matched_article_id: candidate.article_id, article_name: candidate.name, match_status: candidate.score === 100 ? "MATCH_EXACTO" : "MATCH_PROPUESTO", issues: line.issues.filter((issue) => !["AMBIGUO", "SIN_MATCH"].includes(issue.code)), accepted: true }); };
  const applyExtraction = async () => { if (!reception?.extraccion_documental) return; setBusy(true); try { const response = await comprasService.applyReceptionExtraction(reception.id, reception.extraccion_documental.extraction_id, extractionLines); setReception({ ...response.recepcion, extraccion_documental: response.extraccion }); setMessage("Propuesta aplicada al borrador. Revisa y confirma manualmente; Stock sin cambios."); } catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo aplicar la propuesta."); } finally { setBusy(false); } };
  const extractionPanel = reception?.documento && reception.estado !== "CONFIRMADA" ? <section aria-label="Análisis del albarán"><h5>Extracción inteligente</h5><label>Texto OCR o transcripción opcional<textarea aria-label="Texto OCR del albarán" value={ocrText} onChange={(event) => setOcrText(event.target.value)} placeholder="Para fotos o PDF escaneados cuando no hay OCR real conectado" /></label><button type="button" disabled={busy} onClick={() => void analyzeDocument()}>{reception.extraccion_documental ? "Volver a analizar" : "Analizar albarán"}</button>{reception.extraccion_documental ? <section aria-label="Propuesta de recepción"><h6>Albarán analizado</h6><p>Proveedor: {reception.extraccion_documental.supplier_name || "No detectado"} · Confianza: {Math.round(reception.extraccion_documental.confidence)} %</p><p>Estado proveedor: {reception.extraccion_documental.provider_match.status}</p>{reception.extraccion_documental.provider_match.issues.length ? <ul>{reception.extraccion_documental.provider_match.issues.map((issue) => <li key={issue.code}>{issue.blocking ? "Bloqueante: " : "Aviso: "}{issue.message}</li>)}</ul> : null}<p>Número: {reception.extraccion_documental.delivery_note_number || "No detectado"} · Fecha: {reception.extraccion_documental.delivery_date || "No detectada"}</p><p>Líneas detectadas: {reception.extraccion_documental.summary.detected_lines} · Coincidencias exactas: {reception.extraccion_documental.summary.exact_matches} · Revisión: {reception.extraccion_documental.summary.requires_review} · Bloqueantes: {reception.extraccion_documental.summary.blocking_issues}</p>{extractionLines.map((line, index) => <fieldset key={`${line.source_text}-${index}`}><legend>{line.article_name || line.source_text}</legend><p>Documento: {line.quantity} {line.unit} · {money(line.unit_price)}/{line.unit}</p><p>Pedido: {line.pending_quantity} {line.order_unit} · {money(line.order_price)}/{line.order_unit}</p>{line.price_variation_pct !== null ? <p>Variación de precio: {line.price_variation_pct > 0 ? "+" : ""}{line.price_variation_pct} %</p> : null}<p>Artículo: {line.matched_article_id || "Sin relacionar"} · Estado: {line.comparison_status}</p><label>Cantidad propuesta<input aria-label={`Cantidad propuesta ${index + 1}`} type="number" step="any" value={line.quantity} onChange={(event) => updateExtraction(index, { quantity: Number(event.target.value) })} /></label><label>Unidad propuesta<input aria-label={`Unidad propuesta ${index + 1}`} value={line.unit} onChange={(event) => updateExtraction(index, { unit: event.target.value })} /></label><label>Precio propuesto<input aria-label={`Precio propuesto ${index + 1}`} type="number" step="any" value={line.unit_price} onChange={(event) => updateExtraction(index, { unit_price: Number(event.target.value) })} /></label>{line.candidates.length > 1 || !line.matched_article_id ? <label>Artículo relacionado<select aria-label={`Artículo relacionado ${index + 1}`} value={line.matched_article_id} onChange={(event) => chooseCandidate(index, event.target.value)}><option value="">Selecciona</option>{line.candidates.map((candidate) => <option key={candidate.article_id} value={candidate.article_id}>{candidate.name} · {candidate.article_id} · {Math.round(candidate.score)} %</option>)}</select></label> : null}{line.issues.length ? <ul>{line.issues.map((issue) => <li key={issue.code}>{issue.blocking ? "Bloqueante: " : "Aviso: "}{issue.message}</li>)}</ul> : null}</fieldset>)}<button type="button" disabled={busy || extractionLines.some((line) => line.issues.some((issue) => issue.blocking)) || reception.extraccion_documental.provider_match.issues.some((issue) => issue.blocking)} onClick={() => void applyExtraction()}>Aplicar al borrador de recepción</button></section> : null}</section> : null;
  const receivable = items.filter((item) => ["preparado", "enviado", "parcialmente_recibido"].includes(item.estado));
  return <section className="feature-block" aria-label="Recepciones de mercancía"><h3>Recepciones de mercancía</h3>{receivable.map((order) => <button key={order.id} disabled={busy} onClick={() => void start(order.id)}>Registrar recepción de {order.id}</button>)}{!receivable.length ? <p>No hay pedidos preparados pendientes de recepción.</p> : null}{message ? <p role="status">{message}</p> : null}{reception ? <section className="menu-editor" aria-label="Revisar recepción"><h4>Recepción {reception.reception_id}</h4><p>Proveedor: {reception.proveedor} · Pedido: {reception.order_id}</p><strong>Estado: {reception.estado}</strong><label>Fecha de recepción<input type="date" disabled={reception.estado === "CONFIRMADA"} value={reception.fecha || ""} onChange={(event) => setReception({ ...reception, fecha: event.target.value })} /></label><label>Referencia del albarán<input disabled={reception.estado === "CONFIRMADA"} value={reception.referencia || ""} onChange={(event) => setReception({ ...reception, referencia: event.target.value })} /></label><section aria-label="Documento adjunto"><h5>Documento adjunto</h5>{reception.documento ? <><p><strong>Nombre:</strong> {reception.documento.nombre}</p><p>Proveedor: {reception.documento.proveedor} · Pedido: {reception.documento.order_id}</p><p>Estado: {reception.documento.estado === "PENDIENTE_REVISION" ? "Pendiente de revisión" : reception.documento.estado}</p><button type="button" disabled={busy} onClick={() => void viewDocument()}>Ver documento</button>{reception.estado !== "CONFIRMADA" ? <button type="button" disabled={busy} onClick={() => void removeDocument()}>Quitar documento</button> : null}<a href="#lineas-recepcion">Continuar recepción</a></> : <label>Adjuntar albarán<input aria-label="Adjuntar albarán" type="file" disabled={busy || reception.estado === "CONFIRMADA"} accept=".pdf,.docx,.xlsx,.jpg,.jpeg,.png,.txt" onChange={(event) => void attachDocument(event.target.files?.[0])} /></label>}</section>{extractionPanel}<div id="lineas-recepcion">{reception.lineas.map((line, index) => <fieldset disabled={reception.estado === "CONFIRMADA"} key={line.order_line_id}><legend>{line.article_name}</legend><p>Pedido: {line.ordered_quantity} {line.unit} · Ya recibido: {line.previously_received} {line.unit} · Pendiente: {line.pending_quantity} {line.unit}</p><label>Cantidad recibida ahora<input aria-label={`Cantidad recibida ${index + 1}`} type="number" min="0" step="any" value={line.received_quantity} onChange={(event) => change(index, "received_quantity", event.target.value)} /></label><label>Unidad<input aria-label={`Unidad recibida ${index + 1}`} value={line.unit} onChange={(event) => change(index, "unit", event.target.value)} /></label>{line.canonical_unit && line.canonical_unit !== line.unit ? <p className="meta-line">Stock: {line.stock_quantity} {line.canonical_unit}</p> : null}<p>Precio pedido: {money(line.order_price)}</p><label>Precio recibido<input aria-label={`Precio recibido ${index + 1}`} type="number" min="0" step="any" value={line.received_price ?? ""} onChange={(event) => change(index, "received_price", event.target.value)} /></label><label>Lote<input aria-label={`Lote ${index + 1}`} value={line.lot} onChange={(event) => change(index, "lot", event.target.value)} /></label><label>Caducidad<input aria-label={`Caducidad ${index + 1}`} type="date" value={line.expiry} onChange={(event) => change(index, "expiry", event.target.value)} /></label><label>Ubicación<input aria-label={`Ubicación ${index + 1}`} value={line.location} onChange={(event) => change(index, "location", event.target.value)} /></label><label>Observaciones<input aria-label={`Observaciones recepción ${index + 1}`} value={line.observations} onChange={(event) => change(index, "observations", event.target.value)} /></label>{line.incidences.length ? <ul>{line.incidences.map((issue) => <li key={issue.code}>{issue.message}</li>)}</ul> : null}</fieldset>)}</div>{reception.incidencias.some((issue) => issue.bloqueante) ? <p role="alert">Hay incidencias que impiden confirmar la recepción.</p> : null}{reception.estado === "CONFIRMADA" ? <p role="status">Recepción CONFIRMADA. Los movimientos de Stock son inmutables.</p> : <div><button disabled={busy} onClick={() => void save()}>Guardar borrador de recepción</button><button disabled={busy || !reception.confirmable} onClick={() => void confirm()}>Confirmar recepción</button></div>}</section> : null}</section>;
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
