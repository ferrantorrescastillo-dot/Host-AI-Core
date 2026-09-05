import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { HostAiApiError } from "../../api/client";
import { articulosService } from "../../services/articulosService";
import type { ArticuloCosteDerivado, ArticuloSinPrecio, CatalogoResponse, ReclassificationCandidate, ReclassificationPreview, ReferenciasImportPreview } from "../../types/articulos";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { SearchField } from "../components/SearchField";
import { SafeCatalogWritePanel } from "../components/SafeCatalogWritePanel";

export function ArticulosPage() {
  const [params, setParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [search, setSearch] = useState(params.get("q") || "");
  const [data, setData] = useState<CatalogoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const page = Number(params.get("page") || 1);
  const querySearch = params.get("q") || "";
  useEffect(() => { const articleId = params.get("article_id"); if (articleId && /^[A-Za-z0-9._-]+$/.test(articleId)) navigate(`/articulos/${encodeURIComponent(articleId)}`, { replace: true }); }, [navigate, params]);

  useEffect(() => {
    setSearch((current) => current === querySearch ? current : querySearch);
  }, [querySearch]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const next = new URLSearchParams(params);
      if (search) next.set("q", search); else next.delete("q");
      if (search !== (params.get("q") || "")) next.set("page", "1");
      setParams(next, { replace: true });
    }, 300);
    return () => window.clearTimeout(timer);
  }, [search, params, setParams]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    articulosService.list({
      q: params.get("q") || undefined,
      familia: params.get("familia") || undefined,
      proveedor: params.get("proveedor") || undefined,
      estado: params.get("estado") || undefined,
      con_stock: params.has("con_stock") ? params.get("con_stock") === "true" : undefined,
      orden: (params.get("orden") as "nombre") || "nombre",
      direccion: (params.get("direccion") as "asc") || "asc",
      page,
      page_size: 20,
    }).then((result) => active && setData(result)).catch((reason: unknown) => {
      if (active) setError(reason instanceof HostAiApiError ? reason.message : "No se pudo cargar el catálogo.");
    }).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [params, page]);

  const update = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value); else next.delete(key);
    next.set("page", "1");
    setParams(next);
  };

  return (
    <section className="panel catalog-page" aria-labelledby="catalog-title">
      <header className="dashboard-header"><div><p className="eyebrow">Catálogo maestro</p><h2 id="catalog-title">Artículos</h2><p className="meta-line">Consulta de artículos, stock y proveedores reales</p></div><button type="button" onClick={() => setCreating(true)}>+ Nuevo artículo</button></header>
      {creating ? <SafeCatalogWritePanel domain="ARTICULO" operation="CREAR" onCancel={() => setCreating(false)} onConfirmed={(record) => { setCreating(false); const id = String(record.codigo || ""); if (id) window.location.assign(`/articulos/${encodeURIComponent(id)}`); }} /> : null}
      <MissingPriceReferences autoOpen={params.get("panel") === "referencias"} />
      <LegacyReclassification />
      <div className="catalog-filters">
        <SearchField value={search} onChange={setSearch} placeholder="Nombre, código, familia o proveedor" ariaLabel="Buscar artículos" />
        <Select label="Familia" value={params.get("familia") || ""} values={data?.catalogo.filtros.familias || []} onChange={(v) => update("familia", v)} />
        <Select label="Proveedor" value={params.get("proveedor") || ""} values={data?.catalogo.filtros.proveedores || []} onChange={(v) => update("proveedor", v)} />
        <Select label="Estado" value={params.get("estado") || ""} values={data?.catalogo.filtros.estados || []} onChange={(v) => update("estado", v)} />
        <label>Stock<select value={params.get("con_stock") || ""} onChange={(e) => update("con_stock", e.target.value)}><option value="">Todos</option><option value="true">Con stock</option><option value="false">Sin stock</option></select></label>
        <label>Orden<select value={params.get("orden") || "nombre"} onChange={(e) => update("orden", e.target.value)}><option value="nombre">Nombre</option><option value="codigo">Código</option><option value="precio">Precio</option><option value="stock">Stock</option><option value="actualizacion">Actualización</option></select></label>
      </div>
      {loading ? <LoadingState label="Cargando artículos..." /> : error ? <ErrorState title="No se pudo cargar el catálogo." detail={error} /> : !data?.catalogo.items.length ? <div className="panel-state"><p>No hay artículos para los filtros seleccionados.</p></div> : (
        <>
          <p className="meta-line">{data.catalogo.total} artículos encontrados</p>
          <div className="catalog-table-wrap"><table className="catalog-table"><thead><tr><th>Código</th><th>Artículo</th><th>Familia</th><th>Proveedor</th><th>Precio</th><th>Stock</th><th>Estado</th></tr></thead><tbody>{data.catalogo.items.map((item) => <tr key={item.id}><td>{item.codigo}</td><td><Link to={`/articulos/${encodeURIComponent(item.id)}`} state={{ from: `${location.pathname}${location.search}` }}>{item.nombre}</Link></td><td>{item.familia || "—"}</td><td>{item.proveedor || "—"}</td><td>{item.precio == null ? "—" : `${item.precio.toFixed(2)} €`}</td><td>{item.stock == null ? "—" : `${item.stock} ${item.unidad_stock || ""}`}</td><td>{item.estado}</td></tr>)}</tbody></table></div>
          <nav className="catalog-pagination" aria-label="Paginación"><button disabled={page <= 1} onClick={() => update("page", String(page - 1))}>Anterior</button><span>Página {page} de {data.catalogo.total_pages || 1}</span><button disabled={page >= data.catalogo.total_pages} onClick={() => update("page", String(page + 1))}>Siguiente</button></nav>
        </>
      )}
    </section>
  );
}

function LegacyReclassification() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<ReclassificationCandidate[]>([]);
  const [selected, setSelected] = useState<ReclassificationCandidate | null>(null);
  const [preview, setPreview] = useState<ReclassificationPreview | null>(null);
  const [message, setMessage] = useState("");
  const row = selected ? { article_id: selected.article_id, tipo_entidad: "ELABORACION_INTERNA", elaboracion_id: selected.coincidencias[0]?.elaboracion_id } : null;
  async function load() { const result = await articulosService.reclassificationCandidates(); setItems(result.candidatos); setOpen(true); }
  async function review(item: ReclassificationCandidate) { setSelected(item); setPreview(null); }
  async function prepare() { if (row) setPreview(await articulosService.previewReclassification([row])); }
  async function confirm() { if (!row || !preview) return; const result = await articulosService.confirmReclassification([row], preview.preview_token); setMessage(result.idempotente ? "Clasificación ya aplicada." : "Clasificación confirmada."); setSelected(null); setPreview(null); await load(); }
  function inlineReview(item: ReclassificationCandidate) {
    if (selected?.article_id !== item.article_id) return null;
    return <section className="final-review" aria-label={`Revisión de ${item.articulo}`}>
      <h4>REGISTRO ACTUAL</h4><p>{item.articulo} · {item.article_id}</p>
      <p>Precio: {String(item.registro_actual.precio ?? "—")} · Proveedor: {String(item.registro_actual.proveedor ?? "—")}</p>
      <p>Origen: {String(item.registro_actual.origen ?? "—")} · Observaciones: {String(item.registro_actual.observaciones ?? "—")}</p>
      <h4>PROPUESTA</h4><p>Tipo nuevo: ELABORACION_INTERNA</p>
      <p>Elaboración vinculada: {item.coincidencias[0]?.elaboracion_id}</p><p>Coste: DERIVADO DE ESCANDALLO</p>
      {preview ? <><p>No modifica precio, stock ni escandallo; conserva el histórico.</p><button type="button" onClick={() => void confirm()}>Confirmar</button></> : <button type="button" onClick={() => void prepare()}>Preparar cambio</button>}
      <button type="button" className="secondary" onClick={() => { setSelected(null); setPreview(null); }}>Cancelar</button>
    </section>;
  }
  return <section className="recipe-card" aria-label="Candidatos de reclasificación">
    <div className="menu-actions"><button type="button" onClick={() => void load()}>Candidatos de reclasificación</button></div>
    {message ? <p role="status">{message}</p> : null}
    {open ? <><h3>Candidatos de reclasificación</h3><p>{items.length} registros requieren revisión humana.</p>{items.map((item) => <article className="recipe-card" data-candidate-id={item.article_id} key={item.article_id}>
      <strong>{item.articulo} · {item.article_id}</strong><p>Estado actual: artículo comprado por compatibilidad legado.</p>
      <p>Posible coincidencia: {item.coincidencias.map((match) => `${match.elaboracion_id} · ${match.nombre}`).join(", ")}</p><p>Señales: {item.senales.join(", ")}</p>
      <div className="menu-actions"><button type="button" onClick={() => void review(item)}>Revisar</button><button type="button" className="secondary" onClick={() => setMessage(`${item.article_id} se mantiene como artículo comprado.`)}>Mantener como artículo comprado</button></div>
      {inlineReview(item)}
    </article>)}</> : null}
  </section>;
}

function MissingPriceReferences({ autoOpen = false }: { autoOpen?: boolean }) {
  const [open, setOpen] = useState(false); const [items, setItems] = useState<ArticuloSinPrecio[]>([]);
  const [derived, setDerived] = useState<ArticuloCosteDerivado[]>([]);
  const [raw, setRaw] = useState(""); const [preview, setPreview] = useState<ReferenciasImportPreview | null>(null); const [workflowStatus, setWorkflowStatus] = useState<"LISTO_PARA_CONFIRMAR" | "CONFIRMADO" | null>(null); const [message, setMessage] = useState(""); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  async function load() { setBusy(true); setError(""); try { const result = await articulosService.withoutPrice(); setItems(result.articulos); setDerived(result.costes_derivados || []); setOpen(true); try { const state = await articulosService.importedReferencesState(); setPreview(state.workflow?.preview || null); setWorkflowStatus(state.workflow?.estado || null); if (state.workflow?.estado === "CONFIRMADO") setMessage("La última referencia externa confirmada se ha recuperado. El precio y el proveedor reales siguen sin modificarse."); } catch { /* La lista de artículos sigue siendo utilizable sin estado previo. */ } } catch (reason) { setError(reason instanceof Error ? reason.message : "No se pudieron cargar los artículos incompletos."); } finally { setBusy(false); } }
  useEffect(() => { if (autoOpen && !open && !busy) void load(); }, [autoOpen]);
  async function copy() { setError(""); try { const value = await articulosService.exportWithoutPrice(); await navigator.clipboard.writeText(value.texto); setMessage("Lista de artículos incompletos copiada."); } catch (reason) { setError(reason instanceof Error ? reason.message : "No se pudo copiar la exportación."); } }
  async function parse() { setBusy(true); setError(""); try { setPreview(await articulosService.previewImportedReferences(raw)); setWorkflowStatus("LISTO_PARA_CONFIRMAR"); } catch (reason) { setError(reason instanceof Error ? reason.message : "No se pudieron preparar las referencias externas."); } finally { setBusy(false); } }
  async function confirm() { if (!preview) return; setBusy(true); setError(""); try { const result = await articulosService.confirmImportedReferences(preview.listas); setMessage(`${result.confirmadas} referencias externas confirmadas. El precio y el proveedor reales siguen sin modificarse.`); setWorkflowStatus("CONFIRMADO"); setRaw(""); setItems((await articulosService.withoutPrice()).articulos); } catch (reason) { setError(reason instanceof Error ? reason.message : "No se pudieron confirmar las referencias externas."); } finally { setBusy(false); } }
  async function discard() { setBusy(true); setError(""); try { await articulosService.discardImportedReferences(); setPreview(null); setWorkflowStatus(null); setMessage("Vista previa externa descartada sin modificar datos reales."); } catch (reason) { setError(reason instanceof Error ? reason.message : "No se pudo descartar la vista previa externa."); } finally { setBusy(false); } }
  return <section className="recipe-card" aria-label="Artículos sin precio"><div className="menu-actions"><button type="button" disabled={busy} onClick={() => void load()}>Artículos incompletos</button>{open ? <button type="button" className="secondary" onClick={() => void copy()}>Copiar lista para enriquecimiento externo</button> : null}</div>
    {message ? <p role="status">{message}</p> : null}
    {error ? <p role="alert">{error}</p> : null}
    {open && derived.length ? <section aria-label="Costes derivados"><h4>Costes derivados de elaboraciones</h4>{derived.map((item) => <p key={item.article_id}><strong>{item.articulo}</strong> · {item.estado === "COSTE_DERIVADO_ESCANDALLO" ? "Coste derivado de escandallo" : "Escandallo pendiente"}</p>)}</section> : null}
    {open ? <><h3>Artículos incompletos</h3><p>{items.length} artículos canónicos sin precio real · consolidado por article_id · coste IA $0</p><p>La tienda o proveedor encontrado fuera de Host AI se conservará como referencia. No se convertirá en proveedor real ni cambiará el precio de compra.</p><div className="catalog-table-wrap"><table className="catalog-table"><thead><tr><th>Artículo</th><th>Código</th><th>Unidad base</th><th>Compra / formato</th><th>Recetas</th><th>Referencia</th><th>Estado</th></tr></thead><tbody>{items.map((item) => <tr key={item.article_id}><td>{item.articulo}</td><td>{item.codigo}</td><td>{item.unidad_base || "—"}</td><td>{item.unidad_compra || "—"} {item.cantidad_formato || ""} {item.unidad_formato || ""}</td><td>{item.usado_en_recetas}{item.recetas.length ? ` · ${item.recetas.join(", ")}` : ""}</td><td>{item.referencia ? `${item.referencia.tienda_referencia || "Referencia externa"} · ${item.referencia.precio_normalizado.toFixed(2)} €/${item.referencia.unidad_normalizada}` : "Sin referencia"}</td><td>{item.estado}</td></tr>)}</tbody></table></div>
      <label>Reimportar precio y proveedor/tienda de referencia<textarea rows={10} placeholder="Pega JSON, CSV, TSV o una tabla Markdown" value={raw} onChange={(event) => { setRaw(event.target.value); setPreview(null); }} /></label><button type="button" disabled={busy || !raw.trim()} onClick={() => void parse()}>Preparar vista previa</button>
      {preview ? <section className="final-review" aria-label="Referencias a importar"><h4>{workflowStatus === "CONFIRMADO" ? "VISTA PREVIA CONSERVADA · CONFIRMADA" : "VISTA PREVIA DE REFERENCIAS"}</h4><p>{preview.resumen.listas} listas · {preview.resumen.ambiguas} necesitan revisión · {preview.resumen.invalidas} inválidas · parser {preview.formato_detectado} · coste IA $0</p><p>{workflowStatus === "CONFIRMADO" ? "La referencia ya fue confirmada y recuperada por post-read. Precio y proveedor reales permanecen fuera de esta escritura." : "Aún no se ha escrito ninguna referencia. Precio y proveedor reales quedan fuera de esta confirmación."}</p>{preview.listas.map((row) => <article key={`${row.article_id}-${row.fila}`} className="recipe-card"><label><input type="checkbox" disabled={workflowStatus === "CONFIRMADO"} checked={row.incluir} onChange={(event) => setPreview({ ...preview, listas: preview.listas.map((item) => item.fila === row.fila ? { ...item, incluir: event.target.checked } : item) })} /> Incluir</label><strong>{row.articulo} · {row.article_id}</strong><p>Actual real: precio {row.precio_real_actual == null ? "sin informar" : `${row.precio_real_actual.toFixed(2)} €`} · proveedor {row.proveedor_real_actual || "sin informar"}</p><p>Referencia propuesta: {row.referencia.producto} · proveedor/tienda {row.referencia.tienda_referencia}</p><p>{row.referencia.precio_comercial.toFixed(2)} € · {row.referencia.cantidad_formato} {row.referencia.unidad_formato} · {row.referencia.precio_normalizado.toFixed(2)} €/{row.referencia.unidad_normalizada}</p><p>Fuente: {row.referencia.url}</p></article>)}{workflowStatus !== "CONFIRMADO" ? <button type="button" disabled={busy || !preview.listas.some((row) => row.incluir)} onClick={() => void confirm()}>Confirmar referencias seleccionadas</button> : null}<button type="button" className="secondary" onClick={() => void discard()}>{workflowStatus === "CONFIRMADO" ? "Cerrar vista conservada" : "Cancelar"}</button></section> : null}</> : null}
  </section>;
}

function Select({ label, value, values, onChange }: { label: string; value: string; values: string[]; onChange: (v: string) => void }) {
  return <label>{label}<select aria-label={label} value={value} onChange={(e) => onChange(e.target.value)}><option value="">Todos</option>{values.map((item) => <option key={item}>{item}</option>)}</select></label>;
}
