import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { HostAiApiError } from "../../api/client";
import { articulosService } from "../../services/articulosService";
import { stockService, type StockResult } from "../../services/stockService";
import type { ArticuloResumen } from "../../types/articulos";
import type { StockMovementInput, StockMovementType } from "../../types/stock";
import type {
  StockAlerta,
  StockExistencia,
  StockLote,
  StockMovimiento,
} from "../../types/api";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function StockPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorRequestId, setErrorRequestId] = useState<string | null>(null);
  const [data, setData] = useState<StockResult | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);
  const [showForm, setShowForm] = useState(false);
  const [articles, setArticles] = useState<ArticuloResumen[]>([]);
  const [search, setSearch] = useState("");
  const location = useLocation();

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
        <button type="button" onClick={() => setShowForm((value) => !value)}>Registrar inventario / ajuste</button>
      </header>

      {error ? (
        <>
          <ErrorState title="No se pudo cargar el stock." detail={error} />
          <p className="meta-line">Request ID: {errorRequestId || "No disponible"}</p>
        </>
      ) : (
        <>
          {showForm ? <StockMovementForm data={data} articles={articles} search={search} setSearch={setSearch} loadArticles={async () => { const response = await articulosService.list({ q: search, page_size: 25 }); setArticles(response.catalogo.items); }} context={new URLSearchParams(location.search)} onSaved={() => setRefreshTick((value) => value + 1)} /> : null}
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

          {data?.alertas.length ? <Alertas alertas={data.alertas} /> : null}

          {data?.existencias.length ? (
            <section className="stock-section" aria-labelledby="stock-existencias">
              <h3 id="stock-existencias">Existencias actuales</h3>
              <div className="stock-grid">
                {data.existencias.map((item, index) => (
                  <Existencia key={item.clave || item.articulo_id || `${item.nombre}-${index}`} item={item} />
                ))}
              </div>
            </section>
          ) : (
            <div className="panel-state">
              <p>No hay existencias de stock registradas.</p>
              {data?.mensaje ? <p className="meta-line">{data.mensaje}</p> : null}
            </div>
          )}

          {data?.lotes.length ? <Lotes lotes={data.lotes} /> : null}
          {data?.movimientos.length ? <Movimientos movimientos={data.movimientos} /> : null}
        </>
      )}
    </section>
  );
}

function StockMovementForm({ data, articles, search, setSearch, loadArticles, context, onSaved }: { data: StockResult | null; articles: ArticuloResumen[]; search: string; setSearch: (value: string) => void; loadArticles: () => Promise<void>; context: URLSearchParams; onSaved: () => void }) {
  const [articleId, setArticleId] = useState(context.get("article_id") || "");
  const [type, setType] = useState<StockMovementType>("INVENTARIO_INICIAL");
  const [quantity, setQuantity] = useState("");
  const [unit, setUnit] = useState("");
  const [location, setLocation] = useState("");
  const [expiry, setExpiry] = useState("");
  const [lot, setLot] = useState("");
  const [notes, setNotes] = useState("");
  const [confirmExisting, setConfirmExisting] = useState(false);
  const [busy, setBusy] = useState(false);
  const [searching, setSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const selected = articles.find((article) => article.id === articleId);
  const existing = data?.existencias.find((item) => item.articulo_id === articleId || item.clave === articleId);

  const performSearch = async () => {
    setSearching(true); setError("");
    try { await loadArticles(); setHasSearched(true); }
    catch (reason) { setError((reason as Error).message); }
    finally { setSearching(false); }
  };

  const selectArticle = (article: ArticuloResumen) => {
    setArticleId(article.id);
    setUnit(article.unidad || "");
    setConfirmExisting(false);
  };

  const save = async () => {
    setBusy(true); setError(""); setMessage("");
    const input: StockMovementInput = { article_id: articleId, tipo: type, cantidad: Number(quantity), unidad: unit, lote: lot, ubicacion: location, caducidad: expiry, observaciones: notes, production_plan_id: context.get("production_plan_id") || undefined, return_to: context.get("return_to") || undefined, confirmar_existente: confirmExisting };
    try { const response = await stockService.createMovement(input); setMessage(`${response.mensaje} Stock actual: ${formatQuantity(response.stock_actual, unit)}.`); onSaved(); }
    catch (reason) { setError((reason as Error).message); }
    finally { setBusy(false); }
  };

  return <section className="stock-section" aria-label="Registrar inventario o ajuste"><h3>Registrar inventario / ajuste</h3>
    <div className="menu-actions"><label>Buscar artículo<input value={search} onChange={(event) => setSearch(event.target.value)} /></label><button type="button" disabled={searching} onClick={() => void performSearch()}>{searching ? "Buscando..." : "Buscar"}</button></div>
    {hasSearched ? articles.length ? <ul className="clean-list" aria-label="Resultados de artículos">{articles.map((article) => <li key={article.id}><button type="button" aria-pressed={article.id === articleId} onClick={() => selectArticle(article)}>{article.nombre} · {article.codigo}</button></li>)}</ul> : <p role="status">No se encontraron artículos.</p> : null}
    <label>Artículo<select aria-label="Artículo" value={articleId} onChange={(event) => { const article = articles.find((item) => item.id === event.target.value); if (article) selectArticle(article); else setArticleId(""); }}><option value="">Selecciona un artículo</option>{articles.map((article) => <option key={article.id} value={article.id}>{article.nombre} · {article.codigo}</option>)}</select></label>
    <label>Tipo de movimiento<select aria-label="Tipo de movimiento" value={type} onChange={(event) => setType(event.target.value as StockMovementType)}><option value="INVENTARIO_INICIAL">Inventario inicial</option><option value="AJUSTE_POSITIVO">Ajuste positivo</option><option value="AJUSTE_NEGATIVO">Ajuste negativo</option></select></label>
    <label>Cantidad<input aria-label="Cantidad" type="number" min="0" step="any" value={quantity} onChange={(event) => setQuantity(event.target.value)} /></label><label>Unidad<input aria-label="Unidad" value={unit} onChange={(event) => setUnit(event.target.value)} /></label>
    <label>Lote (opcional)<input value={lot} onChange={(event) => setLot(event.target.value)} /></label><label>Ubicación (opcional)<input value={location} onChange={(event) => setLocation(event.target.value)} /></label><label>Caducidad (opcional)<input type="date" value={expiry} onChange={(event) => setExpiry(event.target.value)} /></label><label>Observaciones (opcional)<textarea value={notes} onChange={(event) => setNotes(event.target.value)} /></label>
    {type === "INVENTARIO_INICIAL" && existing && Number(existing.cantidad) > 0 ? <label className="draft-warning"><input type="checkbox" checked={confirmExisting} onChange={(event) => setConfirmExisting(event.target.checked)} />Ya existe {formatQuantity(existing.cantidad, existing.unidad)}. Confirmo que quiero corregir el inventario a la cantidad indicada.</label> : null}
    <button type="button" disabled={busy || !selected || !quantity || !unit || Boolean(type === "INVENTARIO_INICIAL" && existing && !confirmExisting)} onClick={() => void save()}>{busy ? "Registrando..." : "Guardar movimiento"}</button>
    {message ? <p role="status">{message}</p> : null}{error ? <p role="alert">{error}</p> : null}{context.get("return_to") === "produccion" && message ? <Link to="/produccion">Volver a Producción</Link> : null}
  </section>;
}

function Alertas({ alertas }: { alertas: StockAlerta[] }) {
  return (
    <section className="stock-section stock-alerts" aria-labelledby="stock-alertas">
      <h3 id="stock-alertas">Alertas de stock</h3>
      <ul className="clean-list">
        {alertas.map((alerta, index) => (
          <li key={`${alerta.tipo || "alerta"}-${index}`}>
            <strong>{readable(alerta.tipo) || "Aviso"}:</strong> {alerta.mensaje || "Sin detalle"}
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
    </article>
  );
}

function Lotes({ lotes }: { lotes: StockLote[] }) {
  return (
    <section className="stock-section" aria-labelledby="stock-lotes">
      <h3 id="stock-lotes">Lotes</h3>
      <div className="stock-table-wrap">
        <table className="stock-table">
          <thead><tr><th>Artículo</th><th>Cantidad</th><th>Ubicación</th><th>Caducidad</th></tr></thead>
          <tbody>
            {lotes.map((lote, index) => (
              <tr key={lote.id || `${lote.nombre}-${index}`}>
                <td>{lote.nombre || "No disponible"}</td>
                <td>{formatQuantity(lote.cantidad, lote.unidad)}</td>
                <td>{lote.ubicacion || "Sin ubicación"}</td>
                <td>{formatDate(lote.caducidad)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Movimientos({ movimientos }: { movimientos: StockMovimiento[] }) {
  return (
    <section className="stock-section" aria-labelledby="stock-movimientos">
      <h3 id="stock-movimientos">Movimientos recientes</h3>
      <ul className="clean-list stock-movements">
        {movimientos.map((movimiento, index) => (
          <li key={movimiento.id || `${movimiento.nombre}-${index}`}>
            <div><strong>{movimiento.nombre || "Artículo"}</strong><p className="meta-line">{readable(movimiento.tipo) || "Movimiento"} · {movimiento.motivo || "Sin motivo"}</p></div>
            <span>{formatQuantity(movimiento.cantidad, movimiento.unidad)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
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
