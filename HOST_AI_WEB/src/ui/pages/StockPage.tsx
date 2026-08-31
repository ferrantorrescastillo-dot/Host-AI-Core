import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { HostAiApiError } from "../../api/client";
import { articulosService } from "../../services/articulosService";
import { stockService, type StockResult } from "../../services/stockService";
import type { ArticuloResumen } from "../../types/articulos";
import type {
  StockAlerta,
  StockExistencia,
  StockLote,
  StockMovimiento,
} from "../../types/api";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { SearchField } from "../components/SearchField";

export function StockPage() {
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorRequestId, setErrorRequestId] = useState<string | null>(null);
  const [data, setData] = useState<StockResult | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);
  const [locationLotId, setLocationLotId] = useState("");
  const [showForm, setShowForm] = useState(() => new URLSearchParams(location.search).has("article_id"));
  const [articles, setArticles] = useState<ArticuloResumen[]>([]);
  const [search, setSearch] = useState("");
  const [listQuery, setListQuery] = useState("");
  const matches = (value: unknown) => !listQuery.trim() || JSON.stringify(value).toLocaleLowerCase("es").includes(listQuery.trim().toLocaleLowerCase("es"));
  const visibleExistencias = (data?.existencias ?? []).filter(matches);
  const visibleLotes = (data?.lotes ?? []).filter(matches);
  const visibleMovimientos = (data?.movimientos ?? []).filter(matches);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    setErrorRequestId(null);
    stockService
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
          setError("No se pudo cargar el stock.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [refreshTick]);

  useEffect(() => {
    const articleId = new URLSearchParams(location.search).get("article_id") || "";
    if (!articleId || articles.some((item) => item.id === articleId) || search === articleId) return;
    setSearch(articleId);
    articulosService.list({ q: articleId, page_size: 25 }).then((response) => setArticles(response.catalogo.items)).catch(() => setArticles([]));
  }, [location.search, articles, search]);

  if (loading && !data) return <LoadingState label="Cargando stock..." />;

  return (
    <section className="panel" role="region" aria-labelledby="stock-title">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">Inventario</p>
          <h2 id="stock-title">Stock</h2>
          <p className="meta-line">Existencias, lotes y movimientos registrados</p>
        </div>
        <button type="button" onClick={() => setRefreshTick((value) => value + 1)}>
          {error ? "Reintentar" : "Actualizar"}
        </button>
        <button type="button" onClick={() => setShowForm((value) => !value)}>Ajustar stock</button>
      </header>

      {error ? (
        <>
          <ErrorState title="No se pudo cargar el stock." detail={error} />
          <p className="meta-line">Request ID: {errorRequestId || "No disponible"}</p>
        </>
      ) : (
        <>
          {showForm ? <SafeStockAdjustmentForm articles={articles} search={search} setSearch={setSearch} loadArticles={async () => { const response = await articulosService.list({ q: search, page_size: 25 }); setArticles(response.catalogo.items); }} context={new URLSearchParams(location.search)} onSaved={() => setRefreshTick((value) => value + 1)} /> : null}
          <div className="module-toolbar"><SearchField value={listQuery} onChange={setListQuery} placeholder="Buscar artículos, lotes o ubicaciones..." ariaLabel="Buscar stock" /></div>

          {listQuery.trim() ? <StockSearchResults query={listQuery} existencias={visibleExistencias} lotes={visibleLotes} movimientos={visibleMovimientos} alertas={data?.alertas ?? []} onAssignLocation={setLocationLotId} /> : null}

          <section className="safe-mode" aria-label="Estado de seguridad">
            <p><strong>Modo seguro:</strong> {data?.modo_seguro ? "Activo" : "Inactivo"}</p>
            <p><strong>Datos reales modificados:</strong> {data?.datos_reales_modificados ? "Sí" : "No"}</p>
            <p><strong>Estado operativo:</strong> {readable(data?.estado_operativo) || readable(data?.estado) || "No disponible"}</p>
            <p className="meta-line">Request ID: {data?.request_id || "No disponible"}</p>
          </section>

          <section className="dashboard-grid" aria-label="Resumen de stock">
            <SummaryCard title="Artículos" value={data?.resumen.articulos ?? data?.existencias.length ?? 0} />
            <SummaryCard title="Lotes" value={data?.resumen.lotes ?? data?.lotes.length ?? 0} />
            <SummaryCard title="Movimientos" value={data?.resumen.movimientos ?? data?.movimientos.length ?? 0} />
            <SummaryCard title="Alertas" value={data?.resumen.alertas ?? data?.alertas.length ?? 0} />
          </section>

          {data?.alertas.length ? <Alertas
            alertas={data.alertas}
            selectedLotId={locationLotId}
            lots={data.lotes ?? []}
            onAssignLocation={setLocationLotId}
            onCancelLocation={() => setLocationLotId("")}
            onLocationSaved={() => { setLocationLotId(""); setRefreshTick((value) => value + 1); }}
          /> : null}

          {!listQuery.trim() && visibleExistencias.length ? (
            <section className="stock-section" aria-labelledby="stock-existencias">
              <h3 id="stock-existencias">Existencias actuales</h3>
              <div className="stock-grid">
                {visibleExistencias.map((item, index) => (
                  <Existencia key={item.clave || item.articulo_id || `${item.nombre}-${index}`} item={item} />
                ))}
              </div>
            </section>
          ) : !listQuery.trim() ? (
            <div className="panel-state">
              <p>{listQuery ? `No hay existencias que coincidan con “${listQuery}”.` : "No hay existencias de stock registradas."}</p>
              {data?.mensaje ? <p className="meta-line">{data.mensaje}</p> : null}
            </div>
          ) : null}

          {!listQuery.trim() && visibleLotes.length ? <Lotes lotes={visibleLotes} requestedLotId={new URLSearchParams(location.search).get("lote_id") || ""} onSaved={() => setRefreshTick((value) => value + 1)} /> : null}
          {!listQuery.trim() ? <LocationsOverview /> : null}
          {!listQuery.trim() && visibleMovimientos.length ? <Movimientos movimientos={visibleMovimientos} /> : null}
        </>
      )}
    </section>
  );
}

function StockSearchResults({ query, existencias, lotes, movimientos, alertas, onAssignLocation }: { query: string; existencias: StockExistencia[]; lotes: StockLote[]; movimientos: StockMovimiento[]; alertas: StockAlerta[]; onAssignLocation: (lotId: string) => void }) {
  const matchingAlerts = alertas.filter((item) => JSON.stringify(item).toLocaleLowerCase("es").includes(query.trim().toLocaleLowerCase("es")));
  const empty = !existencias.length && !lotes.length && !movimientos.length && !matchingAlerts.length;
  return <section className="stock-section stock-search-results" aria-labelledby="stock-search-results">
    <h3 id="stock-search-results">Resultados de búsqueda</h3>
    {empty ? <p role="status">No hay resultados que coincidan con “{query}”.</p> : <>
      {existencias.length ? <div><h4>Artículos</h4><div className="stock-grid">{existencias.map((item, index) => <article className="stock-card" key={item.clave || item.articulo_id || index}><h4>{item.nombre || "Artículo"}</h4><p className="stock-quantity">Stock: {formatQuantity(item.cantidad, item.unidad)}</p><p className="meta-line">Código: {item.articulo_id || item.clave || "No disponible"} · {item.lotes?.length ?? 0} lotes</p>{item.articulo_id ? <div className="menu-actions"><a href={`/articulos/${encodeURIComponent(item.articulo_id)}`} target="_blank" rel="noopener noreferrer">Abrir</a><a href={`/articulos/${encodeURIComponent(item.articulo_id)}?edit=1`} target="_blank" rel="noopener noreferrer">Editar ficha</a><a href={`/stock?${new URLSearchParams({ article_id: item.articulo_id })}`}>Ajustar stock</a></div> : null}</article>)}</div></div> : null}
      {lotes.length ? <div><h4>Lotes y ubicaciones</h4><ul className="clean-list">{lotes.map((lot, index) => <li key={lot.id || index}><strong>{lot.nombre}</strong> · {lot.id || "Sin código"} · {formatQuantity(lot.cantidad, lot.unidad)} · {lot.ubicacion || "Sin ubicación"}{lot.id ? <div className="menu-actions"><a href={`/stock?${new URLSearchParams({ lote_id: String(lot.id) })}`}>Abrir</a></div> : null}</li>)}</ul></div> : null}
      {movimientos.length ? <Movimientos movimientos={movimientos} /> : null}
      {matchingAlerts.length ? <Alertas alertas={matchingAlerts} onAssignLocation={onAssignLocation} /> : null}
    </>}
  </section>;
}

function SafeStockAdjustmentForm({ articles, search, setSearch, loadArticles, context, onSaved }: { articles: ArticuloResumen[]; search: string; setSearch: (value: string) => void; loadArticles: () => Promise<void>; context: URLSearchParams; onSaved: () => void }) {
  const [articleId, setArticleId] = useState(context.get("article_id") || "");
  const [quantity, setQuantity] = useState("");
  const [reason, setReason] = useState("");
  const [preview, setPreview] = useState<import("../../types/stock").StockAdjustmentPreview | null>(null);
  const [busy, setBusy] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const selected = articles.find((item) => item.id === articleId);
  const searchArticles = async () => { setBusy(true); setError(""); try { await loadArticles(); setHasSearched(true); } catch (reasonValue) { setError((reasonValue as Error).message); } finally { setBusy(false); } };
  const review = async () => { if (!selected) return; setBusy(true); setError(""); try { setPreview(await stockService.previewAdjustment({ article_id: selected.id, cantidad_objetivo: Number(quantity), unidad: selected.unidad || "", motivo: reason })); } catch (reasonValue) { setError((reasonValue as Error).message); } finally { setBusy(false); } };
  const confirm = async () => { if (!preview) return; setBusy(true); setError(""); try { const result = await stockService.confirmAdjustment(preview.preview_token); setMessage(result.mensaje || "Ajuste confirmado."); setPreview(null); onSaved(); } catch (reasonValue) { setError((reasonValue as Error).message); } finally { setBusy(false); } };
  const cancel = async () => { if (preview) { try { await stockService.discardAdjustment(preview.preview_token); } catch { /* La cancelación local sigue sin escribir. */ } } setPreview(null); };
  return <section className="stock-section" aria-label="Ajustar stock"><h3>Ajustar stock</h3>
    <div className="menu-actions"><label>Buscar artículo<input value={search} onChange={(event) => setSearch(event.target.value)} /></label><button type="button" disabled={busy} onClick={() => void searchArticles()}>Buscar</button></div>
    {hasSearched && !articles.length ? <p role="status">No se encontraron artículos.</p> : null}
    <label>Artículo<select aria-label="Artículo" value={articleId} onChange={(event) => { setArticleId(event.target.value); setPreview(null); }}><option value="">Selecciona un artículo</option>{articles.map((article) => <option key={article.id} value={article.id}>{article.nombre} · {article.codigo}</option>)}</select></label>
    <label>Cantidad real<input aria-label="Cantidad real" type="number" min="0" step="any" value={quantity} onChange={(event) => { setQuantity(event.target.value); setPreview(null); }} /></label>
    <label>Motivo obligatorio<textarea aria-label="Motivo obligatorio" value={reason} onChange={(event) => { setReason(event.target.value); setPreview(null); }} /></label>
    {!preview ? <button type="button" disabled={busy || !selected || quantity === "" || !reason.trim()} onClick={() => void review()}>Vista previa</button> : <section className="draft-warning" aria-label="Vista previa del ajuste"><p>Stock anterior: {formatQuantity(preview.stock_anterior, preview.unidad)}</p><p>Stock resultante: {formatQuantity(preview.stock_resultante, preview.unidad)}</p><p>Diferencia: {preview.diferencia > 0 ? "+" : ""}{formatQuantity(preview.diferencia, preview.unidad)}</p><p>Motivo: {preview.motivo}</p><div className="menu-actions"><button type="button" disabled={busy || !preview.requiere_confirmacion} onClick={() => void confirm()}>Confirmar ajuste</button><button type="button" onClick={() => void cancel()}>Cancelar</button></div></section>}
    {message ? <p role="status">{message}</p> : null}{error ? <p role="alert">{error}</p> : null}
  </section>;
}

function Alertas({ alertas, selectedLotId = "", lots = [], onAssignLocation, onCancelLocation = () => undefined, onLocationSaved = () => undefined }: { alertas: StockAlerta[]; selectedLotId?: string; lots?: StockLote[]; onAssignLocation: (lotId: string) => void; onCancelLocation?: () => void; onLocationSaved?: () => void }) {
  return (
    <section className="stock-section stock-alerts" aria-labelledby="stock-alertas">
      <h3 id="stock-alertas">Alertas de stock</h3>
      <ul className="clean-list">
        {alertas.map((alerta, index) => (
          <li key={`${alerta.tipo || "alerta"}-${index}`}>
            <details><summary><strong>{readable(alerta.tipo) || "Aviso"}:</strong> {alerta.mensaje || "Sin detalle"}</summary>
            <p>Severidad: {readable(alerta.nivel) || "No disponible"}</p>
            {alerta.cantidad != null && alerta.unidad ? <p className="meta-line">Cantidad: {formatQuantity(alerta.cantidad, alerta.unidad)}</p> : null}
            {alerta.ubicacion ? <p className="meta-line">Ubicación: {alerta.ubicacion}</p> : null}
            {alerta.articulo_id ? <div className="menu-actions" aria-label="Acciones de la alerta">
              {alerta.lote_id ? <a href={`/stock?${new URLSearchParams({ lote_id: alerta.lote_id })}`}>Abrir lote</a> : null}
              {alerta.lote_id && String(alerta.tipo || "").toLowerCase().includes("ubic") ? <button type="button" onClick={() => onAssignLocation(String(alerta.lote_id))}>Asignar ubicación</button> : null}
              <a className="secondary" href={`/articulos/${encodeURIComponent(alerta.articulo_id)}`} target="_blank" rel="noopener noreferrer">Abrir artículo</a>
              <a href={`/stock?${new URLSearchParams({ article_id: alerta.articulo_id })}`}>Corregir con ajuste</a>
              {String(alerta.tipo || "").toLowerCase().includes("bajo") ? <a href={`/compras?${new URLSearchParams({ article_id: alerta.articulo_id })}`} target="_blank" rel="noopener noreferrer">Preparar compra</a> : null}
            </div> : null}
            {selectedLotId && alerta.lote_id === selectedLotId ? <LotLocationPanel
              lot={lots.find((lot) => lot.id === selectedLotId) || { id: selectedLotId, nombre: alerta.mensaje?.split(" tiene un lote")[0] || "Lote", cantidad: alerta.cantidad, unidad: alerta.unidad || "", ubicacion: "" }}
              onCancel={onCancelLocation}
              onSaved={onLocationSaved}
            /> : null}</details>
          </li>
        ))}
      </ul>
    </section>
  );
}

function Existencia({ item }: { item: StockExistencia }) {
  return (
    <article className="stock-card">
      <h4>{item.nombre || "Artículo sin nombre"}</h4>
      <p className="stock-quantity">{formatQuantity(item.cantidad, item.unidad)}</p>
      <p className="meta-line">{item.familia || "Familia no disponible"} · {item.lotes?.length ?? 0} lotes</p>
      {item.articulo_id ? <div className="menu-actions"><a href={`/articulos/${encodeURIComponent(item.articulo_id)}`} target="_blank" rel="noopener noreferrer">Abrir</a><a href={`/articulos/${encodeURIComponent(item.articulo_id)}?edit=1`} target="_blank" rel="noopener noreferrer">Editar ficha</a><a href={`/stock?${new URLSearchParams({ article_id: item.articulo_id })}`}>Ajustar stock</a></div> : null}
    </article>
  );
}

function Lotes({ lotes, requestedLotId, onSaved }: { lotes: StockLote[]; requestedLotId: string; onSaved: () => void }) {
  const [selected, setSelected] = useState<StockLote | null>(null);
  useEffect(() => { if (requestedLotId) setSelected(lotes.find((lot) => lot.id === requestedLotId) || null); }, [requestedLotId, lotes]);
  return (
    <section className="stock-section" aria-labelledby="stock-lotes">
      <h3 id="stock-lotes">Lotes</h3>
      <div className="stock-table-wrap">
        <table className="stock-table">
          <thead><tr><th>Artículo</th><th>Cantidad</th><th>Ubicación</th><th>Caducidad</th><th>Acciones</th></tr></thead>
          <tbody>
            {lotes.map((lote, index) => (
              <tr key={lote.id || `${lote.nombre}-${index}`}>
                <td>{lote.nombre || "No disponible"}</td>
                <td>{formatQuantity(lote.cantidad, lote.unidad)}</td>
                <td>{lote.ubicacion || "Sin ubicación"}</td>
                <td>{formatDate(lote.caducidad)}</td>
                <td>{lote.id ? <div className="menu-actions"><button type="button" onClick={() => setSelected(lote)}>Abrir</button><button type="button" onClick={() => setSelected(lote)}>Asignar ubicación</button></div> : "Revisión manual"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {selected ? <LotLocationPanel lot={selected} onCancel={() => setSelected(null)} onSaved={() => { setSelected(null); onSaved(); }} /> : null}
    </section>
  );
}

function LotLocationPanel({ lot, onCancel, onSaved }: { lot: StockLote; onCancel: () => void; onSaved: () => void }) {
  const [locations, setLocations] = useState<Array<{ id: string; nombre: string }>>([]);
  const [locationId, setLocationId] = useState("");
  const [preview, setPreview] = useState<{ preview_token: string; lote_antes: Record<string, unknown>; lote_despues: Record<string, unknown>; requiere_confirmacion: boolean } | null>(null);
  const [error, setError] = useState("");
  const [detail, setDetail] = useState<{ lote: Record<string, unknown>; incidencias: Array<Record<string, string>>; movimientos?: Array<Record<string, unknown>> } | null>(null);
  useEffect(() => { stockService.locations().then((value) => setLocations(value.ubicaciones)).catch((reason: Error) => setError(reason.message)); }, []);
  useEffect(() => { if (lot.id) stockService.lot(String(lot.id)).then(setDetail).catch((reason: Error) => setError(reason.message)); }, [lot.id]);
  async function confirmLocation() {
    if (!preview || !lot.id) return;
    try {
      await stockService.confirmLocation(String(lot.id), locationId, preview.preview_token);
      const reread = await stockService.lot(String(lot.id));
      const persistedLocation = String(reread.lote.ubicacion || "");
      const persistedQuantity = Number(reread.lote.cantidad);
      if (persistedLocation !== locationId || (typeof lot.cantidad === "number" && persistedQuantity !== lot.cantidad)) throw new Error("La lectura posterior no confirmó la ubicación sin alterar la cantidad.");
      onSaved();
    } catch (reason) { setPreview(null); setError(reason instanceof Error ? reason.message : "No se pudo verificar la ubicación guardada."); }
  }
  return <section className="draft-warning" aria-label="Asignar ubicación">
    <h4>Asignar ubicación</h4><dl className="detail-grid"><dt>Artículo</dt><dd>{lot.nombre || "No disponible"}</dd><dt>Lote</dt><dd>{lot.id}</dd><dt>Cantidad</dt><dd>{formatQuantity(lot.cantidad, lot.unidad)}</dd><dt>Ubicación actual</dt><dd>{lot.ubicacion || "Sin ubicación"}</dd></dl>
    {detail ? <><dl className="detail-grid"><dt>Artículo</dt><dd>{String(detail.lote.nombre || detail.lote.articulo_id || lot.nombre || "No disponible")}</dd><dt>Fecha de entrada</dt><dd>{String(detail.lote.fecha_entrada || detail.lote.creado_en || "No disponible")}</dd><dt>Origen/proveedor</dt><dd>{String(detail.lote.origen || detail.lote.proveedor || "No disponible")}</dd><dt>Estado</dt><dd>{String(detail.lote.estado || "No disponible")}</dd></dl>{detail.incidencias.length ? <section><h5>Incidencias</h5><ul>{detail.incidencias.map((item, index) => <li key={String(item.code || index)}>{item.message}</li>)}</ul></section> : null}{detail.movimientos?.length ? <section><h5>Movimientos relacionados</h5><ul>{detail.movimientos.map((item, index) => <li key={String(item.id || index)}>{String(item.tipo || "Movimiento")} · {formatQuantity(item.cantidad, item.unidad)}</li>)}</ul></section> : null}</> : null}
    {detail?.lote.articulo_id ? <a href={`/stock?${new URLSearchParams({ article_id: String(detail.lote.articulo_id) })}`}>Corregir stock</a> : null}
    <label>Nueva ubicación<select aria-label="Ubicación canónica" value={locationId} onChange={(event) => { setLocationId(event.target.value); setPreview(null); }}><option value="">Seleccionar</option>{locations.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select></label>
    <button type="button" disabled={!locationId} onClick={() => stockService.previewLocation(String(lot.id), locationId).then(setPreview).catch((reason: Error) => setError(reason.message))}>Continuar</button>
    <button type="button" onClick={onCancel}>Cancelar</button>
    {preview ? <div aria-label="Vista previa de ubicación"><h5>Asignar ubicación</h5><dl className="detail-grid"><dt>Lote</dt><dd>{lot.id}</dd><dt>Ubicación anterior</dt><dd>{String(preview.lote_antes.ubicacion || "Sin ubicación")}</dd><dt>Nueva ubicación</dt><dd>{String(preview.lote_despues.ubicacion)}</dd><dt>Cantidad</dt><dd>{formatQuantity(preview.lote_antes.cantidad ?? lot.cantidad, preview.lote_antes.unidad ?? lot.unidad)}</dd></dl><button type="button" disabled={!preview.requiere_confirmacion} onClick={() => void confirmLocation()}>Confirmar</button><button type="button" onClick={() => setPreview(null)}>Cancelar</button></div> : null}
    {error ? <p role="alert">{error}</p> : null}
  </section>;
}

function Movimientos({ movimientos }: { movimientos: StockMovimiento[] }) {
  const [selected, setSelected] = useState<StockMovimiento | null>(null);
  return (
    <section className="stock-section" aria-labelledby="stock-movimientos">
      <h3 id="stock-movimientos">Movimientos recientes</h3>
      <ul className="clean-list stock-movements">
        {movimientos.map((movimiento, index) => (
          <li key={movimiento.id || `${movimiento.nombre}-${index}`}>
            <div><strong>{movimiento.nombre || "Artículo"}</strong><p className="meta-line">{readable(movimiento.tipo) || "Movimiento"} · {movimiento.motivo || "Sin motivo"}</p></div>
            <span>{formatQuantity(movimiento.cantidad, movimiento.unidad)}</span>
            <div className="menu-actions"><button type="button" onClick={() => setSelected(movimiento)}>Abrir</button>{movimiento.articulo_id ? <a href={`/stock?${new URLSearchParams({ article_id: movimiento.articulo_id })}`}>Corregir con ajuste</a> : null}</div>
          </li>
        ))}
      </ul>
      {selected ? <section className="draft-warning" aria-label="Detalle del movimiento"><h4>Movimiento {selected.id || "sin identificador"}</h4><dl className="detail-grid"><dt>Fecha/hora</dt><dd>{selected.creado_en || "No disponible"}</dd><dt>Artículo</dt><dd>{selected.nombre || selected.articulo_id || "No disponible"}</dd><dt>Lote</dt><dd>{selected.lote_id || "No disponible"}</dd><dt>Tipo</dt><dd>{readable(selected.tipo) || "No disponible"}</dd><dt>Cantidad</dt><dd>{formatQuantity(selected.cantidad, selected.unidad)}</dd><dt>Origen</dt><dd>{selected.origen || String(selected.trazabilidad?.origen || "No disponible")}</dd><dt>Destino</dt><dd>{selected.destino || String(selected.trazabilidad?.destino || "No disponible")}</dd><dt>Motivo</dt><dd>{selected.motivo || "No disponible"}</dd><dt>Actor</dt><dd>{selected.usuario || String(selected.trazabilidad?.usuario || "No disponible")}</dd><dt>Referencia</dt><dd>{selected.referencia || String(selected.trazabilidad?.referencia || "No disponible")}</dd><dt>Observaciones</dt><dd>{selected.observaciones || String(selected.trazabilidad?.observaciones || "No disponible")}</dd></dl><div className="menu-actions">{selected.articulo_id ? <a href={`/articulos/${encodeURIComponent(selected.articulo_id)}`} target="_blank" rel="noopener noreferrer">Abrir artículo</a> : null}{selected.lote_id ? <a href={`/stock?${new URLSearchParams({ lote_id: selected.lote_id })}`}>Abrir lote</a> : null}{selected.articulo_id ? <a href={`/stock?${new URLSearchParams({ article_id: selected.articulo_id })}`}>Corregir con ajuste</a> : null}<button type="button" onClick={() => setSelected(null)}>Cerrar</button></div><p className="meta-line">Este movimiento es histórico e inmutable.</p></section> : null}
    </section>
  );
}

function LocationsOverview() {
  const [locations, setLocations] = useState<Array<{ id: string; nombre: string; lotes?: Array<Record<string, unknown>>; total_lotes?: number; total_articulos?: number }>>([]);
  const [selected, setSelected] = useState("");
  useEffect(() => { stockService.locations().then((result) => setLocations(Array.isArray(result.ubicaciones) ? result.ubicaciones : [])).catch(() => setLocations([])); }, []);
  const detail = locations.find((item) => item.id === selected);
  return <section className="stock-section" aria-labelledby="stock-locations"><h3 id="stock-locations">Ubicaciones</h3>{locations.length ? <ul className="clean-list">{locations.map((item) => <li key={item.id}><strong>{item.nombre}</strong> · {item.total_lotes ?? item.lotes?.length ?? 0} lotes · {item.total_articulos ?? 0} artículos <button type="button" onClick={() => setSelected(item.id)}>Abrir</button></li>)}</ul> : <p>No hay ubicaciones derivables de lotes activos.</p>}{detail ? <section className="draft-warning" aria-label="Detalle de ubicación"><h4>{detail.nombre}</h4><ul>{(detail.lotes || []).map((lot, index) => <li key={String(lot.id || index)}>{String(lot.nombre || lot.articulo_id || "Artículo")} · {formatQuantity(lot.cantidad, lot.unidad)} {lot.id ? <a href={`/stock?${new URLSearchParams({ lote_id: String(lot.id) })}`}>Abrir lote</a> : null}</li>)}</ul><button type="button" onClick={() => setSelected("")}>Cerrar</button></section> : null}</section>;
}

function SummaryCard({ title, value }: { title: string; value: number }) {
  return <article className="data-card"><h3>{title}</h3><p className="stat-value">{value}</p></article>;
}

function readable(value: unknown): string {
  if (typeof value !== "string" || !value.trim()) return "";
  const normalized = value.trim().replaceAll("_", " ").toLowerCase();
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function formatQuantity(value: unknown, unit: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "No disponible";
  const suffix = typeof unit === "string" && unit.trim() ? ` ${unit}` : "";
  return `${new Intl.NumberFormat("es-ES").format(value)}${suffix}`;
}

function formatDate(value: unknown): string {
  if (typeof value !== "string" || !value.trim()) return "No disponible";
  const date = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-ES", { dateStyle: "medium", timeZone: "UTC" }).format(date);
}
