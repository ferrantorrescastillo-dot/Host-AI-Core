import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { HostAiApiError } from "../../api/client";
import { bibliotecaService } from "../../services/bibliotecaService";
import { articulosService } from "../../services/articulosService";
import type { AICostBreakdown, ArticleCulinaryContext, ArticuloDetalle, ArticuloResumen, PrecioReferencia } from "../../types/articulos";
import type { ElaboracionDetalle, IngredienteReceta, RendimientoFisicoTeorico, RendimientoInput, RendimientoPreviewResponse } from "../../types/biblioteca";
import { BibliotecaNav } from "../components/BibliotecaNav";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { SafeCatalogWritePanel } from "../components/SafeCatalogWritePanel";
import { AiAccumulatedCost, AiCostSummary, reportAiCost } from "../components/AiCostSummary";

const tabs = [
  "resumen", "receta", "escandallo", "ficha-tecnica",
  "produccion", "documentos", "menus-eventos", "historial",
];

export function ElaboracionDetailPage() {
  const { elaboracionId = "" } = useParams();
  const [params, setParams] = useSearchParams();
  const [item, setItem] = useState<ElaboracionDetalle | null>(null);
  const [canConfirmYield, setCanConfirmYield] = useState(false);
  const [error, setError] = useState<{ message: string; status?: number } | null>(null);
  const [editingRecipe, setEditingRecipe] = useState(false);
  const [completingRecipe, setCompletingRecipe] = useState(false);
  const [archivingRecipe, setArchivingRecipe] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setItem(null);
    setError(null);
    bibliotecaService.detail(elaboracionId)
      .then((response) => {
        setItem(response.elaboracion);
        setCanConfirmYield(Boolean(response.permisos?.confirmar_rendimiento));
      })
      .catch((reason: Error) => setError({
        message: reason.message,
        status: reason instanceof HostAiApiError ? reason.statusCode : undefined,
      }));
  }, [elaboracionId]);

  useEffect(() => {
    if (params.get("complete") === "1") setEditingRecipe(true);
  }, [params]);

  if (error) {
    return <section className="panel"><ErrorState
      title={error.status === 404 ? "La elaboración no existe." : "No se pudo cargar la elaboración."}
      detail={error.message}
    /></section>;
  }
  if (!item) return <LoadingState label="Cargando elaboración..." />;

  const requestedTab = params.get("tab") || "resumen";
  const tab = tabs.includes(requestedTab) ? requestedTab : "resumen";
  return <section className="panel library-detail">
    <BibliotecaNav />
    <AiAccumulatedCost title="Gasto Host AI en esta sesión" />
    <AiAccumulatedCost entityType="RECIPE" entityId={elaboracionId} title="Coste Host AI — esta receta" />
    <Link to="/biblioteca/elaboraciones">← Volver a Elaboraciones</Link>
    {editingRecipe ? <>{completingRecipe ? <OperationalCompletionSummary item={item} /> : null}<SafeCatalogWritePanel domain="RECETA" operation="MODIFICAR" entityId={elaboracionId} initial={recipeWriteInitial(item)} onCancel={() => { setEditingRecipe(false); setCompletingRecipe(false); }} onConfirmed={() => { setEditingRecipe(false); setCompletingRecipe(false); notifyDashboardRecipeUpdated(elaboracionId); bibliotecaService.detail(elaboracionId).then((response) => setItem(response.elaboracion)); }} /></> : null}
    {archivingRecipe ? <SafeCatalogWritePanel domain="RECETA" operation="ARCHIVAR" entityId={elaboracionId} onCancel={() => setArchivingRecipe(false)} onConfirmed={() => navigate("/biblioteca/elaboraciones")} /> : null}
    <header className="recipe-hero">
      <div>
        <p className="eyebrow">{item.codigo}</p>
        <h2>{item.nombre}</h2>
        <div className="recipe-badges"><span>{item.categoria || "Sin categoría"}</span><span>{statusLabel(item.estado)}</span></div>
        {item.tiene_receta ? <div className="menu-actions"><button type="button" onClick={() => { setCompletingRecipe(true); setEditingRecipe(true); }}>Completar receta</button><button type="button" className="secondary" onClick={() => { setCompletingRecipe(false); setEditingRecipe(true); }}>Editar receta</button><button type="button" className="danger" onClick={() => setArchivingRecipe(true)}>Archivar</button></div> : null}
      </div>
      <dl className="recipe-kpis" aria-label="Indicadores de la elaboración">
        <div><dt>Rendimiento</dt><dd>{yieldText(item)}</dd></div>
        <div><dt>Coste total</dt><dd>{money(item.coste_total, "No disponible")}</dd></div>
        <div><dt>Coste por ración</dt><dd>{money(item.coste_por_racion, "No disponible")}</dd></div>
        <div><dt>Estado del coste</dt><dd>{statusLabel(item.estado_coste || "SIN_COSTE")}</dd></div>
      </dl>
    </header>
    <nav className="library-tabs" aria-label="Secciones de la elaboración">
      {tabs.map((value) => <button
        className={tab === value ? "active" : ""}
        key={value}
        onClick={() => setParams({ tab: value })}
      >{tabLabel(value)}</button>)}
    </nav>

    <MenuUsage menus={item.menus} />
    {tab === "resumen" && <Summary item={item} />}
    {tab === "receta" && <Recipe item={item} onConfirmed={async () => { notifyDashboardRecipeUpdated(elaboracionId); const response = await bibliotecaService.detail(elaboracionId); setItem(response.elaboracion); }} />}
    {tab === "escandallo" && <Costing
      item={item}
      canConfirmYield={canConfirmYield}
      onConfirmed={() => bibliotecaService.detail(elaboracionId).then((response) => {
        setItem(response.elaboracion);
        setCanConfirmYield(Boolean(response.permisos?.confirmar_rendimiento));
      })}
    />}
    {tab === "ficha-tecnica" && <TechnicalSheet item={item} />}
    {tab === "produccion" && <Production item={item} />}
    {tab === "documentos" && <Documents item={item} />}
    {tab === "menus-eventos" && <MenusEvents item={item} />}
    {tab === "historial" && <History item={item} />}
  </section>;
}

function recipeWriteInitial(item: ElaboracionDetalle): Record<string, unknown> {
  return { nombre: item.nombre, codigo: item.codigo, numero_raciones: item.receta.raciones || item.raciones || item.receta.rendimiento || item.rendimiento, unidad_rendimiento: item.receta.unidad_rendimiento || item.unidad_rendimiento || "", ingredientes: item.receta.ingredientes.map((ingredient) => ingredient.nombre_original || ingredient.nombre_articulo || ""), cantidades: item.receta.ingredientes.map((ingredient) => ingredient.cantidad_texto || `${ingredient.cantidad ?? ""} ${ingredient.unidad || ""}`.trim()), ingredientes_estructurados: item.receta.ingredientes.map((ingredient) => ({ nombre: ingredient.nombre_original, article_id: ingredient.estado_relacion === "relacionado" ? ingredient.articulo_id || null : null, codigo: ingredient.estado_relacion === "relacionado" ? ingredient.articulo_codigo : null, nombre_articulo: ingredient.estado_relacion === "relacionado" ? ingredient.articulo_nombre || ingredient.nombre_articulo : null, estado: ingredient.estado_relacion === "relacionado" ? "RESUELTO" : "SIN_VINCULAR" })), elaboracion: item.receta.procedimiento || item.receta.pasos.join("\n"), tiempo_activo: item.receta.tiempo_activo || "", tiempo_pasivo: item.receta.tiempo_pasivo || "", alergenos: item.ficha_tecnica?.alergenos || [], observaciones: item.receta.observaciones || "" };
}

function OperationalCompletionSummary({ item }: { item: ElaboracionDetalle }) {
  const linked = item.receta.ingredientes.filter((value) => value.estado_relacion === "relacionado").length;
  const priced = item.receta.ingredientes.filter((value) => value.coste_linea != null).length;
  return <section className="catalog-section" aria-label="Asistente de completitud operativa"><h3>Asistente de completitud</h3><p>Revisa únicamente lo pendiente. Las decisiones se guardarán como datos estructurados después de PREVIEW y CONFIRM.</p><dl className="detail-grid"><dt>Documentación pendiente</dt><dd>{item.pendientes.length}</dd><dt>Ingredientes</dt><dd>{item.receta.ingredientes.length}</dd><dt>Relaciones confirmadas</dt><dd>{linked}/{item.receta.ingredientes.length}</dd><dt>Ingredientes con coste</dt><dd>{priced}/{item.receta.ingredientes.length}</dd><dt>Escandallo</dt><dd>{item.escandallo ? item.estado_coste || "Pendiente" : "Pendiente"}</dd></dl></section>;
}

function notifyDashboardRecipeUpdated(recipeId: string) {
  if (window.opener && !window.opener.closed) window.opener.postMessage({ type: "host-ai-recipe-updated", recipe_id: recipeId }, window.location.origin);
}

function Summary({ item }: { item: ElaboracionDetalle }) {
  const indicators = [
    ["Receta", item.tiene_receta],
    ["Escandallo", item.tiene_escandallo],
    ["Ficha técnica", item.tiene_ficha_tecnica],
    ["Documentos", item.tiene_documentos],
    ["Producción", item.tiene_produccion],
    ["Menús o eventos", item.tiene_relaciones_menu_evento],
  ] as const;
  return <Section title="Resumen operativo">
    <p>{item.descripcion || "Sin descripción disponible."}</p>
    <dl className="detail-grid">
      <dt>Rendimiento</dt><dd>{yieldText(item)}</dd>
      <dt>Raciones</dt><dd>{item.raciones ?? "No informadas"}</dd>
      <dt>Coste total</dt><dd>{money(item.coste_total, "Coste no disponible")}</dd>
      <dt>Coste por ración</dt><dd>{money(item.coste_por_racion, "Sin coste por ración")}</dd>
      <dt>Última actualización</dt><dd>{dateText(item.actualizado_en)}</dd>
    </dl>
    <h4>Completitud</h4>
    <ul className="operational-checks">{indicators.map(([name, available]) =>
      <li key={name}><strong>{name}:</strong> {available ? "Disponible" : "Pendiente"}</li>,
    )}</ul>
    {item.completitud != null ? <p>Completitud registrada por el backend: {item.completitud}%.</p> : null}
    {item.pendientes.length ? <><h4>Campos pendientes</h4><ul>{item.pendientes.map((value) => <li key={value}>{value}</li>)}</ul></> : null}
    {item.avisos.length ? <><h4>Avisos</h4><ul>{item.avisos.map((value) => <li key={value}>{value}</li>)}</ul></> : null}
  </Section>;
}

function MenuUsage({ menus }: { menus: ElaboracionDetalle["menus"] }) {
  if (!menus.length) return null;
  return <section className="catalog-section" aria-label="Usada en menús">
    <h3>Usada en menús</h3>
    <ul>{menus.map((menu, index) => typeof menu === "string"
      ? <li key={`${menu}-${index}`}>{menu}</li>
      : <li key={menu.menu_id}><Link to={`/biblioteca/menus/${encodeURIComponent(menu.menu_id)}`}>{menu.nombre} · {menu.menu_id}</Link></li>)}</ul>
  </section>;
}

function Recipe({ item, onConfirmed }: { item: ElaboracionDetalle; onConfirmed: () => Promise<void> }) {
  if (!item.tiene_receta) return <Section title="Receta"><p>No hay una receta estructurada disponible para esta elaboración.</p></Section>;
  const proposedIngredients = item.receta.ingredientes_propuestos_no_registrados || item.receta.ingredientes_propuestos_ia;
  return <Section title="Receta">
    <div className="recipe-section-grid">
      <article className="recipe-card"><h4>Descripción</h4><OriginBadge value={item.procedencia_campos?.descripcion} /><p>{item.descripcion || "Pendiente de completar"}</p></article>
      <article className="recipe-card"><h4>Conservación</h4><OriginBadge value={item.procedencia_campos?.vida_util_refrigerado || item.procedencia_campos?.conservacion} /><p>{item.conservacion || "Pendiente de completar"}</p></article>
      <article className="recipe-card"><h4>Alérgenos</h4><OriginBadge value={item.procedencia_campos?.alergenos} /><p>{allergensText(item.alergenos)}</p></article>
    </div>
    <dl className="detail-grid recipe-facts">
      <dt>Rendimiento</dt><dd>{yieldText(item.receta)}</dd>
      <dt>Raciones</dt><dd>{item.receta.raciones ?? "No informadas"}</dd>
      <dt>Tiempo total</dt><dd>{item.receta.tiempo_total || "Pendiente de completar"}</dd>
      <dt>Tiempo activo</dt><dd>{item.receta.tiempo_activo || "Pendiente de completar"}</dd>
      <dt>Tiempo pasivo</dt><dd>{item.receta.tiempo_pasivo || "Pendiente de completar"}</dd>
      <dt>Temperaturas</dt><dd>{valuesText(item.receta.temperaturas, "Pendiente de completar")}</dd>
      <dt>Técnicas</dt><dd>{valuesText(item.receta.tecnicas, "Pendiente de completar")}</dd>
      <dt>Actualización</dt><dd>{dateText(item.actualizado_en)}</dd>
    </dl>
    <h4>Ingredientes</h4>
    <IngredientsTable ingredients={item.receta.ingredientes} costing={false} />
    <ArticleCompletionList ingredients={item.receta.ingredientes} recipeName={item.nombre} recipeCode={item.codigo} recipeProcedure={item.receta.procedimiento || item.receta.pasos.join("\n")} />
    <div className="recipe-procedure"><h4>Procedimiento</h4><OriginBadge value={item.procedencia_campos?.elaboracion} />
    {item.receta.pasos.length
      ? <ol>{item.receta.pasos.map((step, index) => <li key={index}>{displayValue(step)}</li>)}</ol>
      : <p>{item.receta.procedimiento || "Pendiente de completar"}</p>}
    </div>
    <DocumentationCompletion item={item} onConfirmed={onConfirmed} />
    {item.receta.procedimiento_propuesto_ia ? <article className="recipe-card draft-warning"><h4>Propuesta IA (no guardada)</h4><p>{item.receta.procedimiento_propuesto_ia}</p></article> : null}
    {item.receta.alergenos_posibles?.length ? <article className="recipe-card draft-warning"><h4>Posibles alérgenos a revisar</h4><p>{item.receta.alergenos_posibles.join(", ")}</p></article> : null}
    {item.receta.conservacion_propuesta_ia ? <article className="recipe-card draft-warning"><h4>Conservación propuesta (orientativa)</h4><p>{item.receta.conservacion_propuesta_ia}</p></article> : null}
    {item.receta.tiempos_estimados_ia ? <article className="recipe-card draft-warning"><h4>Tiempos estimados (orientativos)</h4><p>{displayValue(item.receta.tiempos_estimados_ia)}</p></article> : null}
    {item.receta.temperaturas_propuestas_ia?.length ? <article className="recipe-card draft-warning"><h4>Temperaturas propuestas (orientativas)</h4><p>{valuesText(item.receta.temperaturas_propuestas_ia, "Pendiente de completar")}</p></article> : null}
    {item.receta.observaciones_propuestas_ia ? <article className="recipe-card draft-warning"><h4>Observaciones propuestas (no guardadas)</h4><p>{item.receta.observaciones_propuestas_ia}</p></article> : null}
    {Array.isArray(proposedIngredients) && proposedIngredients.length ? <article className="recipe-card draft-warning"><h4>Ingredientes propuestos no registrados</h4><ul>{proposedIngredients.map((value, index) => <li key={index}>{displayValue(value)}</li>)}</ul></article> : null}
    <article className="recipe-card"><h4>Presentación y observaciones</h4><p>{item.receta.observaciones || item.ficha_tecnica.presentacion || "Pendiente de completar"}</p></article>
  </Section>;
}

function ArticleCompletionList({ ingredients, recipeName, recipeCode, recipeProcedure }: { ingredients: IngredienteReceta[]; recipeName: string; recipeCode: string; recipeProcedure: string }) {
  const linked = ingredients.filter((value) => value.estado_relacion === "relacionado" && value.articulo_id);
  if (!linked.length) return null;
  return <section className="catalog-section" aria-label="Completar artículos relacionados"><h4>Artículos relacionados</h4>{linked.map((ingredient) => <ArticleCompletionPanel key={ingredient.articulo_id} articleId={String(ingredient.articulo_id)} ingredientCost={ingredient.coste_linea} culinaryContext={{ ingrediente_original: ingredient.nombre_original, receta_nombre: recipeName, receta_id: recipeCode, uso_culinario: recipeProcedure, cantidad_receta: ingredient.cantidad_receta ?? ingredient.cantidad ?? ingredient.cantidad_texto ?? "", unidad_receta: ingredient.unidad_receta || ingredient.unidad || "", procedimiento_receta: recipeProcedure }} />)}</section>;
}

function ArticleCompletionPanel({ articleId, ingredientCost, culinaryContext }: { articleId: string; ingredientCost?: number | null; culinaryContext: ArticleCulinaryContext }) {
  const [article, setArticle] = useState<ArticuloDetalle | null>(null);
  const [selected, setSelected] = useState<Record<string, unknown>>({});
  const [previewToken, setPreviewToken] = useState("");
  const [manualOpen, setManualOpen] = useState(false);
  const [manual, setManual] = useState({ precio: "", cantidad: "1", unidad: "kg" });
  const [manualPreview, setManualPreview] = useState<PrecioReferencia | null>(null);
  const [manualToken, setManualToken] = useState("");
  const [message, setMessage] = useState("");
  const [aiCost, setAiCost] = useState<AICostBreakdown | null>(null);
  const reload = async () => setArticle((await articulosService.get(articleId)).articulo);
  useEffect(() => { void reload().catch(() => setMessage("No se pudo cargar el artículo relacionado.")); }, [articleId]);
  if (!article) return <p>Cargando artículo relacionado...</p>;
  const missing = ["familia", "unidad_base", "unidad_compra", "cantidad_formato", "unidad_formato", "observaciones"].filter((key) => article[key as keyof ArticuloDetalle] == null || article[key as keyof ArticuloDetalle] === "");
  const noRealPrice = ingredientCost == null && article.precio == null && !(article.precios?.some((value) => value.precio != null));
  return <article className="recipe-card"><h5>{article.nombre}</h5>
    {missing.length && !previewToken ? <button type="button" onClick={async () => { const response = await articulosService.proposeDocumentation(articleId, culinaryContext); setSelected(response.datos_propuestos_ia || {}); setAiCost(response.cost_breakdown || null); reportAiCost(response.cost_breakdown); }}>Completar artículo con IA</button> : null}
    <AiCostSummary cost={aiCost} title="Coste de completar artículo" />
    {Object.keys(selected).length && !previewToken ? <div><p>Propuestas IA (todavía no guardadas)</p>{Object.entries(selected).map(([key, value]) => <label key={key}>{key}<input value={String(value ?? "")} onChange={(event) => setSelected((current) => ({ ...current, [key]: event.target.value }))} /></label>)}<button type="button" onClick={async () => { const response = await articulosService.previewDocumentation(articleId, selected); setPreviewToken(response.preview_token || ""); }}>Continuar</button><button type="button" className="secondary" onClick={() => setSelected({})}>Rechazar</button></div> : null}
    {previewToken ? <div role="status"><strong>PREVIEW IA</strong><p>{Object.entries(selected).map(([key, value]) => `${key}: ${String(value)}`).join(" · ")}</p><button type="button" onClick={async () => { await articulosService.confirmDocumentation(articleId, selected, previewToken); setPreviewToken(""); setSelected({}); await reload(); setMessage("Artículo completado y verificado mediante nueva lectura."); }}>Confirmar</button><button type="button" className="secondary" onClick={() => setPreviewToken("")}>Cancelar</button></div> : null}
    {noRealPrice ? <div><p>No existe precio real disponible.</p><button type="button" onClick={() => setManualOpen(true)}>Introducir referencia manual</button><button type="button" className="secondary" onClick={() => setManualOpen(false)}>Dejar pendiente</button></div> : null}
    {manualOpen && !manualPreview ? <div><label>Precio (€)<input value={manual.precio} onChange={(e) => setManual({ ...manual, precio: e.target.value })} /></label><label>Cantidad<input value={manual.cantidad} onChange={(e) => setManual({ ...manual, cantidad: e.target.value })} /></label><label>Unidad<select value={manual.unidad} onChange={(e) => setManual({ ...manual, unidad: e.target.value })}><option>kg</option><option>g</option><option>l</option><option>ml</option><option>u</option></select></label><button type="button" onClick={async () => { const response = await articulosService.previewManualPrice(articleId, { precio: Number(manual.precio), cantidad_formato: Number(manual.cantidad), unidad: manual.unidad }); setManualPreview(response.referencia_propuesta || null); setManualToken(response.preview_token || ""); }}>Preview</button></div> : null}
    {manualPreview ? <div role="status"><strong>PRECIO DE REFERENCIA MANUAL</strong><p>Precio introducido: {manualPreview.precio_comercial.toFixed(2)} €</p><p>Formato: {manualPreview.cantidad_formato} {manualPreview.unidad_formato}</p><p>Precio normalizado: {manualPreview.precio_normalizado.toFixed(2)} €/{manualPreview.unidad_normalizada}</p><p>Origen: Usuario · Tipo: PRECIO_REFERENCIA_MANUAL</p><p><strong>NO ES PRECIO REAL DE COMPRA.</strong></p><button type="button" onClick={async () => { await articulosService.confirmManualPrice(articleId, { precio: Number(manual.precio), cantidad_formato: Number(manual.cantidad), unidad: manual.unidad }, manualToken); setManualPreview(null); setManualOpen(false); await reload(); setMessage("Referencia manual persistida y verificada mediante nueva lectura."); }}>Confirmar</button><button type="button" className="secondary" onClick={() => setManualPreview(null)}>Cancelar</button></div> : null}
    {article.precios_referencia?.length ? (() => { const reference = article.precios_referencia[article.precios_referencia.length - 1]; return <div>{reference.precio_comercial != null ? <p>Precio de referencia: {reference.precio_comercial.toFixed(2)} € / {reference.cantidad_formato} {reference.unidad_formato}</p> : null}<p>Normalizado: {reference.precio_normalizado.toFixed(2)} €/{reference.unidad_normalizada}</p>{reference.tienda_referencia ? <p>Proveedor/Tienda de referencia: {reference.tienda_referencia}</p> : null}<p>Origen: {reference.origen || "USUARIO"} · REFERENCIA · no es precio real.</p></div>; })() : null}
    {message ? <p role="status">{message}</p> : null}
  </article>;
}

function DocumentationCompletion({ item, onConfirmed }: { item: ElaboracionDetalle; onConfirmed: () => Promise<void> }) {
  const preloaded: Record<string, unknown> = {
    elaboracion: item.receta.procedimiento_propuesto_ia,
    tiempo_total: typeof item.receta.tiempos_estimados_ia === "string" ? item.receta.tiempos_estimados_ia : undefined,
    vida_util_refrigerado: item.receta.conservacion_propuesta_ia,
    observaciones: item.receta.observaciones_propuestas_ia,
    alergenos: item.receta.alergenos_posibles,
  };
  const [proposed, setProposed] = useState<Record<string, unknown>>(() => Object.fromEntries(Object.entries(preloaded).filter(([, value]) => value != null && value !== "" && (!Array.isArray(value) || value.length))));
  const available = Object.entries(proposed);
  const [open, setOpen] = useState(false); const [selected, setSelected] = useState<Record<string, unknown>>({}); const [aiCost, setAiCost] = useState<AICostBreakdown | null>(null);
  const [rejected, setRejected] = useState<string[]>([]); const [editing, setEditing] = useState<string | null>(null);
  const [preview, setPreview] = useState<{ preview_token: string; cambios_seleccionados: Record<string, unknown> } | null>(null); const [error, setError] = useState(""); const [message, setMessage] = useState(""); const [generating, setGenerating] = useState(false); const [confirming, setConfirming] = useState(false);
  const confirmationInFlight = useRef(false);
  async function generate() {
    setOpen(true); setGenerating(true); setError(""); setMessage(""); setPreview(null); setSelected({}); setRejected([]);
    try {
      const result = await bibliotecaService.proposeDocumentation(item.codigo, {});
      setAiCost(result.cost_breakdown || null); reportAiCost(result.cost_breakdown);
      const generated = result.datos_propuestos_ia || {};
      const manual = Array.isArray(result.campos_pendientes_no_proponibles) ? result.campos_pendientes_no_proponibles : [];
      setProposed(generated);
      if (!Object.keys(generated).length && manual.length) setError(`No puedo completar automáticamente estos campos: ${manual.join(", ")}. Necesitan información del usuario.`);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "No se pudieron generar propuestas."); }
    finally { setGenerating(false); }
  }
  async function confirm() {
    if (!preview || confirmationInFlight.current) return;
    const activePreview = preview;
    confirmationInFlight.current = true;
    setConfirming(true); setError(""); setMessage("");
    try {
      const result = await bibliotecaService.confirmDocumentation(item.codigo, selected, [], activePreview.preview_token);
      if (!result.datos_reales_modificados && !result.idempotente) throw new Error("La confirmación no aplicó cambios.");
      setPreview(null); setSelected({}); setRejected([]); setEditing(null); setOpen(false);
      await onConfirmed();
      setMessage("Cambios guardados.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo confirmar la documentación.");
    } finally {
      confirmationInFlight.current = false;
      setConfirming(false);
    }
  }
  if (!item.pendientes.length && !available.length) return null;
  return <section className="yield-editor" aria-label="Completar documentación con IA"><button type="button" disabled={generating || confirming} onClick={() => void generate()}>{generating ? "Generando propuestas..." : "Completar con IA"}</button><AiCostSummary cost={aiCost} title="Coste de completar receta" />{message ? <p role="status">{message}</p> : null}{open ? <div className="draft-warning"><h4>Datos existentes</h4><p>Procedimiento: {item.receta.procedimiento || "Pendiente"}</p><p>Tiempo total: {item.receta.tiempo_total || "Pendiente"}</p><h4>Propuestas IA</h4>{!generating && !available.length && !error ? <p>No se generaron propuestas seguras para los campos pendientes.</p> : null}{available.filter(([key]) => !rejected.includes(key)).map(([key, value]) => <article className="recipe-card" key={key}><strong>{fieldLabel(key)}</strong><OriginBadge value={{ tipo: "IA", estado_revision: "PROPUESTA_NO_GUARDADA" }} />{editing === key ? <textarea aria-label={`Editar ${fieldLabel(key)}`} value={String(selected[key] ?? value)} onChange={(event) => setSelected({ ...selected, [key]: event.target.value })} /> : <p>{displayValue(selected[key] ?? value)}</p>}<div className="menu-actions"><button type="button" onClick={() => { setSelected({ ...selected, [key]: selected[key] ?? value }); setEditing(null); setPreview(null); }}>Aceptar</button><button type="button" className="secondary" onClick={() => { setSelected({ ...selected, [key]: selected[key] ?? value }); setEditing(key); setPreview(null); }}>Editar</button><button type="button" className="secondary" onClick={() => { const next = { ...selected }; delete next[key]; setSelected(next); setRejected([...rejected, key]); setPreview(null); }}>Rechazar</button></div></article>)}<p>Los campos existentes no se sobrescriben. Aceptar o editar solo prepara la vista previa; no escribe.</p><button type="button" disabled={!Object.keys(selected).length || confirming} onClick={() => bibliotecaService.previewDocumentation(item.codigo, selected).then(setPreview).catch((reason: Error) => setError(reason.message))}>Continuar</button><button type="button" disabled={confirming} onClick={() => { setOpen(false); setSelected({}); setRejected([]); setPreview(null); }}>Cancelar</button>{preview ? <div aria-label="Vista previa de documentación"><h5>Vista previa</h5><dl className="detail-grid">{Object.entries(preview.cambios_seleccionados).map(([key, value]) => <div key={key}><dt>{fieldLabel(key)}</dt><dd>{displayValue(value)}</dd></div>)}</dl><button type="button" disabled={confirming} onClick={() => void confirm()}>{confirming ? "Guardando..." : "Confirmar"}</button><button type="button" disabled={confirming} onClick={() => setPreview(null)}>Cancelar</button></div> : null}{error ? <p role="alert">{error}</p> : null}</div> : null}</section>;
}

function OriginBadge({ value }: { value?: { tipo?: string | null; estado_revision?: string | null } | null }) {
  if (!value?.tipo) return null;
  const labels: Record<string, string> = { USUARIO: "Usuario", IA: "IA", WEB: "Web", SISTEMA: "Sistema", IMPORTADO: "Importado" };
  return <span className={`provenance-badge origin-${value.tipo.toLowerCase()}`}>Origen: {labels[value.tipo] || value.tipo}{value.estado_revision === "PENDIENTE_REVISION" ? " · Pendiente de revisión" : ""}</span>;
}

function CostingEditor({ item, onConfirmed }: { item: ElaboracionDetalle; onConfirmed: () => Promise<void> }) {
  const [editing, setEditing] = useState(false); const [lines, setLines] = useState<IngredienteReceta[]>(item.escandallo?.lineas.map((line) => ({ ...line })) || []);
  const [articles, setArticles] = useState<ArticuloResumen[]>([]);
  const [preview, setPreview] = useState<{ preview_token: string; escandallo_propuesto: Record<string, any> } | null>(null); const [error, setError] = useState("");
  useEffect(() => { if (editing && !articles.length) articulosService.list({ page_size: 100 }).then((response) => setArticles(response.catalogo.items)).catch(() => setArticles([])); }, [editing, articles.length]);
  if (!item.escandallo) return null;
  const changes = { numero_raciones: item.receta.rendimiento ?? item.receta.raciones ?? null, lineas: lines.map((line) => ({ producto_codigo: line.articulo_codigo || line.articulo_id || line.codigo, nombre_mostrado: line.articulo_nombre || line.nombre_articulo || line.nombre_original, cantidad_neta: line.cantidad_neta ?? line.cantidad, unidad_receta: line.unidad_receta || line.unidad })) };
  return <section className="yield-editor" aria-label="Editor de escandallo"><button type="button" onClick={() => { setEditing(!editing); setPreview(null); }}>Editar escandallo</button>{editing ? <div>{lines.map((line, index) => <div className="yield-input-row" key={`${line.articulo_id || line.nombre_original}-${index}`}><select aria-label={`Artículo ${index + 1}`} value={line.articulo_id || line.articulo_codigo || line.codigo || ""} onChange={(event) => { const article = articles.find((value) => value.id === event.target.value || value.codigo === event.target.value); const next = [...lines]; next[index] = { ...line, articulo_id: event.target.value, articulo_codigo: event.target.value, articulo_nombre: article?.nombre || "", nombre_original: article?.nombre || line.nombre_original }; setLines(next); setPreview(null); }}><option value="">Seleccionar artículo</option>{articles.map((article) => <option key={article.id} value={article.id}>{article.nombre}</option>)}</select><input aria-label={`Cantidad ${line.nombre_original || index + 1}`} type="number" min="0.000001" step="any" value={line.cantidad_neta ?? line.cantidad ?? ""} onChange={(event) => { const next = [...lines]; next[index] = { ...line, cantidad_neta: Number(event.target.value) }; setLines(next); setPreview(null); }} /><input aria-label={`Unidad ${line.nombre_original || index + 1}`} value={line.unidad_receta || line.unidad || ""} onChange={(event) => { const next = [...lines]; next[index] = { ...line, unidad_receta: event.target.value }; setLines(next); setPreview(null); }} /><button type="button" onClick={() => { setLines(lines.filter((_, position) => position !== index)); setPreview(null); }}>Quitar</button></div>)}<button type="button" onClick={() => setLines([...lines, { nombre_original: "", articulo_id: "", cantidad_neta: 1, unidad_receta: "kg", estado_relacion: "sin_relacionar" }])}>Añadir línea</button><button type="button" onClick={() => bibliotecaService.previewCosting(item.codigo, changes).then(setPreview).catch((reason: Error) => setError(reason.message))}>Guardar cambios</button><button type="button" onClick={() => { setEditing(false); setLines(item.escandallo?.lineas.map((line) => ({ ...line })) || []); setPreview(null); }}>Cancelar</button>{preview ? <div className="draft-warning" aria-label="Vista previa del escandallo"><p>{preview.escandallo_propuesto.lineas?.length || 0} líneas · coste {money(preview.escandallo_propuesto.coste_total, "No disponible")}</p><button type="button" onClick={() => bibliotecaService.confirmCosting(item.codigo, changes, preview.preview_token).then(onConfirmed).catch((reason: Error) => { setPreview(null); setError(reason.message); })}>Confirmar escandallo</button></div> : null}{error ? <p role="alert">{error}</p> : null}</div> : null}</section>;
}

function Costing({ item, canConfirmYield, onConfirmed }: {
  item: ElaboracionDetalle;
  canConfirmYield: boolean;
  onConfirmed: () => Promise<void>;
}) {
  if (!item.escandallo) return <Section title="Escandallo"><p>No hay escandallo asociado.</p></Section>;
  const esc = item.escandallo;
  return <Section title="Escandallo">
    <dl className="recipe-kpis costing-kpis" aria-label="Indicadores del escandallo">
      <div><dt>Coste total</dt><dd>{esc.coste_total == null ? money(esc.coste_total_parcial, "No disponible") : money(esc.coste_total, "No disponible")}</dd></div>
      <div><dt>Coste por ración</dt><dd>{money(esc.coste_por_racion, "No disponible")}</dd></div>
      <div><dt>Rendimiento</dt><dd>{yieldText(item)}</dd></div>
      <div><dt>Estado económico</dt><dd>{statusLabel(esc.estado_coste)}</dd></div>
    </dl>
    {esc.estado_coste !== "DISPONIBLE" || esc.ingredientes_sin_coste || esc.ingredientes_sin_conversion
      ? <div className="costing-alert"><strong>Revisión económica pendiente</strong><p>{esc.ingredientes_sin_coste} ingredientes sin coste · {esc.ingredientes_sin_conversion} sin conversión.</p></div>
      : null}
    <YieldEditor item={item} canConfirm={canConfirmYield} onConfirmed={onConfirmed} />
    <CostingEditor item={item} onConfirmed={onConfirmed} />
    <h4>Desglose de ingredientes</h4>
    <IngredientsTable ingredients={esc.lineas} costing />
    <dl className="detail-grid">
      <dt>Otros costes</dt><dd>{money(esc.otros_costes, "No informados")}</dd>
      <dt>Coste total</dt><dd>{esc.coste_total == null
        ? (esc.coste_total_parcial == null ? "Coste no disponible" : `Coste incompleto · ${money(esc.coste_total_parcial, "")} calculados`)
        : money(esc.coste_total, "Coste no disponible")}</dd>
      <dt>Rendimiento</dt><dd>{esc.rendimiento ?? "No informado"}</dd>
      <dt>Coste por ración</dt><dd>{money(esc.coste_por_racion, "Sin coste por ración")}</dd>
      <dt>Precio objetivo</dt><dd>{money(esc.precio_objetivo, "No informado")}</dd>
      <dt>Margen</dt><dd>{esc.margen == null ? "No informado" : `${esc.margen}%`}</dd>
      <dt>Fecha de cálculo</dt><dd>{dateText(esc.fecha_calculo)}</dd>
      <dt>Ingredientes sin precio</dt><dd>{esc.ingredientes_sin_coste}</dd>
      <dt>Ingredientes sin conversión</dt><dd>{esc.ingredientes_sin_conversion}</dd>
    </dl>
    {esc.incidencias.length ? <ul>{esc.incidencias.map((value, index) => <li key={index}>{displayValue(value)}</li>)}</ul> : null}
  </Section>;
}

function YieldEditor({ item, canConfirm, onConfirmed }: {
  item: ElaboracionDetalle;
  canConfirm: boolean;
  onConfirmed: () => Promise<void>;
}) {
  const declared = item.receta;
  const [mode, setMode] = useState<RendimientoInput["modo"]>("TOTAL");
  const [amount, setAmount] = useState("");
  const [unit, setUnit] = useState<RendimientoInput["unidad"]>("kg");
  const [preview, setPreview] = useState<RendimientoPreviewResponse | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [proposalOrigin, setProposalOrigin] = useState<RendimientoInput["propuesta_origen"]>("MANUAL");
  const [proposalEdited, setProposalEdited] = useState(false);
  const [partialAccepted, setPartialAccepted] = useState(false);
  const previewRequest = useRef(0);
  const perUnitAvailable = declared.unidad_rendimiento?.trim().toLowerCase() === "u";

  const normalizedAmount = () => Number(amount.trim().replace(",", "."));
  const input = (): RendimientoInput => ({
    cantidad: normalizedAmount(),
    unidad: unit,
    modo: mode,
    referencia: "Confirmación desde la ficha interna de Escandallos",
    propuesta_origen: proposalOrigin,
    acepta_estimacion_parcial: partialAccepted,
  });
  const resetPreview = () => {
    previewRequest.current += 1;
    setPreview(null);
    setError("");
    setMessage("");
    setBusy(false);
  };
  const useTheoreticalProposal = (cantidad: number, unidad: RendimientoInput["unidad"], estado: "COMPLETO" | "PARCIAL") => {
    setMode("TOTAL");
    setAmount(String(cantidad).replace(".", ","));
    setUnit(unidad);
    setProposalOrigin(estado === "PARCIAL" ? "TEORICO_PARCIAL" : "TEORICO_COMPLETO");
    setProposalEdited(false);
    setPartialAccepted(false);
    resetPreview();
  };

  async function showPreview() {
    const requestVersion = previewRequest.current + 1;
    previewRequest.current = requestVersion;
    setError(""); setMessage(""); setBusy(true);
    try {
      const value = normalizedAmount();
      if (!Number.isFinite(value) || value <= 0) throw new Error("Introduce una cantidad mayor que cero.");
      const result = await bibliotecaService.previewYield(item.codigo, input());
      if (previewRequest.current === requestVersion) setPreview(result);
    } catch (reason) {
      if (previewRequest.current === requestVersion) {
        setPreview(null);
        setError(reason instanceof Error ? reason.message : "No se pudo preparar la vista previa.");
      }
    } finally {
      if (previewRequest.current === requestVersion) setBusy(false);
    }
  }

  async function confirm() {
    if (!preview) return;
    setError(""); setMessage(""); setBusy(true);
    try {
      await bibliotecaService.confirmYield(item.codigo, input(), preview.preview_token);
      await onConfirmed();
      setPreview(null);
      setMessage("Rendimiento confirmado correctamente.");
    } catch (reason) {
      setPreview(null);
      setError(reason instanceof Error ? reason.message : "No se pudo confirmar el rendimiento.");
    } finally { setBusy(false); }
  }

  const net = declared.rendimiento_neto;
  return <section className="yield-editor" aria-label="Rendimiento de la elaboración">
    <h4>Rendimiento</h4>
    <dl className="detail-grid">
      <dt>Rendimiento declarado</dt><dd>{yieldText(declared)}</dd>
      <dt>Estado declarado</dt><dd>{statusLabel(declared.estado_rendimiento)}</dd>
      <dt>Origen declarado</dt><dd>{originText(declared.origen_rendimiento)}</dd>
      <dt>Rendimiento neto</dt><dd>{net ? `${net.cantidad} ${net.unidad}` : "No confirmado"}</dd>
      <dt>Estado neto</dt><dd>{net ? statusLabel(net.estado) : "No confirmado"}</dd>
      <dt>Origen neto</dt><dd>{originText(net?.origen)}</dd>
    </dl>
    <TheoreticalYield
      value={declared.rendimiento_fisico_teorico}
      onUseProposal={canConfirm ? useTheoreticalProposal : undefined}
    />
    {!canConfirm ? <p>No tienes permiso para confirmar el rendimiento. La información permanece disponible en modo lectura.</p> : <>
      <fieldset className="yield-form" disabled={busy}>
        <legend>Confirmar rendimiento físico neto</legend>
        <div className="yield-mode-options">
          <label><input type="radio" name="yield-mode" checked={mode === "TOTAL"} onChange={() => { setMode("TOTAL"); setProposalOrigin("MANUAL"); setProposalEdited(false); setPartialAccepted(false); resetPreview(); }} /> Rendimiento neto total</label>
          {perUnitAvailable ? <label><input type="radio" name="yield-mode" checked={mode === "POR_UNIDAD"} onChange={() => { setMode("POR_UNIDAD"); setProposalOrigin("MANUAL"); setProposalEdited(false); setPartialAccepted(false); resetPreview(); }} /> Peso o volumen por unidad</label> : null}
        </div>
        <div className="yield-input-row">
          <label>{mode === "POR_UNIDAD" ? "Cada unidad" : "Rendimiento neto total"}
            <input aria-label="Cantidad de rendimiento neto" inputMode="decimal" value={amount} onChange={(event) => { setAmount(event.target.value); if (proposalOrigin !== "MANUAL") setProposalEdited(true); setPartialAccepted(false); resetPreview(); }} />
          </label>
          <label>Unidad física<select aria-label="Unidad de rendimiento neto" value={unit} onChange={(event) => { setUnit(event.target.value as RendimientoInput["unidad"]); setProposalOrigin("MANUAL"); setProposalEdited(false); setPartialAccepted(false); resetPreview(); }}>
            {(["kg", "g", "l", "ml"] as const).map((value) => <option key={value}>{value}</option>)}
          </select></label>
        </div>
        {mode === "POR_UNIDAD" ? <p>Se almacenará un único rendimiento neto total para las {declared.rendimiento} unidades declaradas.</p> : null}
        {proposalOrigin === "TEORICO_PARCIAL" ? <p role="note">{proposalEdited ? "Valor editado a partir de una propuesta teórica parcial." : "Valor procedente de una propuesta teórica parcial."}</p> : null}
        <div className="yield-actions"><button type="button" onClick={showPreview}>{busy ? "Validando..." : "Vista previa"}</button></div>
      </fieldset>
      {preview ? <div className="draft-warning" aria-label="Vista previa del rendimiento">
        {preview.propuesta_origen === "TEORICO_PARCIAL" ? <div role="alert">
          <p>Esta propuesta procede de una estimación teórica parcial y no incluye todos los ingredientes. Confírmala solo si este valor corresponde al rendimiento físico real que deseas registrar.</p>
          <p><strong>Ingredientes excluidos:</strong></p>
          <ul>{declared.rendimiento_fisico_teorico?.ingredientes_excluidos.map((item, index) => <li key={`${item.articulo_id || item.nombre}-${index}`}>{item.nombre} — {item.cantidad ?? "desconocida"} {item.unidad || "sin unidad"}</li>)}</ul>
        </div> : null}
        {preview.propuesta_origen === "TEORICO_COMPLETO" ? <p role="note">Esta propuesta procede de una estimación teórica. Revísala antes de confirmar.</p> : null}
        <p><strong>Valor actual:</strong> {preview.rendimiento_neto_actual ? `${preview.rendimiento_neto_actual.cantidad} ${preview.rendimiento_neto_actual.unidad}` : "No confirmado"}</p>
        <p><strong>Valor propuesto:</strong> {preview.rendimiento_neto_propuesto.cantidad} {preview.rendimiento_neto_propuesto.unidad}</p>
        <p><strong>Conversión derivada:</strong> {preview.modo_entrada === "POR_UNIDAD" ? `${amount} ${unit} por unidad → ${preview.rendimiento_neto_propuesto.cantidad} ${preview.rendimiento_neto_propuesto.unidad} totales` : "Entrada total, sin conversión derivada"}</p>
        <p><strong>Estado esperado:</strong> {statusLabel(preview.rendimiento_neto_propuesto.estado)}</p>
        <p><strong>Actor:</strong> {preview.rendimiento_neto_propuesto.origen?.actor_id || "No disponible"}</p>
        <p><strong>Incidencias:</strong> {preview.incidencias.length ? preview.incidencias.map(displayValue).join(" · ") : "Ninguna"}</p>
        <p><strong>Modificará datos:</strong> {preview.requiere_confirmacion ? "Sí, al confirmar" : "No hay cambios"}</p>
        {preview.propuesta_origen === "TEORICO_PARCIAL" ? <label><input type="checkbox" checked={partialAccepted} onChange={(event) => setPartialAccepted(event.target.checked)} /> Confirmo que este valor corresponde al rendimiento físico real que quiero guardar</label> : null}
        <button type="button" disabled={busy || !preview.requiere_confirmacion || (preview.propuesta_origen === "TEORICO_PARCIAL" && !partialAccepted)} onClick={confirm}>Confirmar rendimiento</button>
      </div> : null}
    </>}
    {error ? <p role="alert">{error}</p> : null}
    {message ? <p role="status">{message}</p> : null}
  </section>;
}

function TheoreticalYield({ value, onUseProposal }: {
  value?: RendimientoFisicoTeorico | null;
  onUseProposal?: (cantidad: number, unidad: RendimientoInput["unidad"], estado: "COMPLETO" | "PARCIAL") => void;
}) {
  if (!value) return null;
  const magnitudes = Object.values(value.magnitudes);
  const proposal = value.estado !== "NO_CALCULABLE" && magnitudes.length === 1 ? magnitudes[0] : null;
  const excludedCount = value.ingredientes_excluidos.length;
  return <section className="yield-theoretical" aria-label="Rendimiento físico teórico">
    <h5>Rendimiento físico teórico</h5>
    <p>{value.cantidad == null ? "No existe una única magnitud combinable." : `${value.cantidad} ${value.unidad}`}</p>
    {magnitudes.length > 1 ? <ul>{magnitudes.map((item) => <li key={item.unidad}>{item.cantidad} {item.unidad}</li>)}</ul> : null}
    <p><strong>Estado del rendimiento físico:</strong> Sugerido · {value.estado.toLowerCase()}</p>
    {value.por_unidad ? <p><strong>Teórico por unidad:</strong> {formatTheoreticalPerUnit(value.por_unidad.cantidad, value.por_unidad.unidad)}{value.por_unidad.calculo_parcial ? " (cálculo parcial)" : ""}</p> : null}
    {value.estado === "COMPLETO" ? <p>Estimación teórica basada en todos los ingredientes.</p> : null}
    {value.estado === "PARCIAL" ? <p role="note">Estimación parcial: no incluye {excludedCount} {excludedCount === 1 ? "ingrediente" : "ingredientes"} sin equivalencia física.</p> : null}
    {proposal && onUseProposal ? <button type="button" onClick={() => onUseProposal(proposal.cantidad, proposal.unidad as RendimientoInput["unidad"], value.estado as "COMPLETO" | "PARCIAL")}>Usar como propuesta</button> : null}
    <details>
      <summary>Ingredientes incluidos: {value.ingredientes_incluidos.length}</summary>
      <ul>{value.ingredientes_incluidos.map((item, index) => <li key={`${item.articulo_id || item.nombre}-${index}`}>{item.nombre}: {item.cantidad_original} {item.unidad_original} → {item.cantidad_normalizada} {item.unidad_normalizada}</li>)}</ul>
    </details>
    {value.ingredientes_excluidos.length ? <details>
      <summary>Ingredientes no convertibles: {value.ingredientes_excluidos.length}</summary>
      <ul>{value.ingredientes_excluidos.map((item, index) => <li key={`${item.articulo_id || item.nombre}-${index}`}>{item.nombre}: {item.cantidad ?? "desconocida"} {item.unidad || "sin unidad"} · {item.motivo}</li>)}</ul>
    </details> : null}
    <p>Es una estimación de solo lectura; no sustituye el rendimiento neto confirmado.</p>
  </section>;
}

function formatTheoreticalPerUnit(cantidad: number, unidad: string): string {
  const normalized = unidad.trim().toLowerCase();
  if (normalized === "kg/u" && Math.abs(cantidad) < 1) return `${formatDisplayNumber(cantidad * 1000, 0)} g/u`;
  if (normalized === "l/u" && Math.abs(cantidad) < 1) return `${formatDisplayNumber(cantidad * 1000, 0)} ml/u`;
  return `${formatDisplayNumber(cantidad, 3)} ${unidad}`;
}

function formatDisplayNumber(value: number, maximumFractionDigits: number): string {
  return new Intl.NumberFormat("es-ES", { maximumFractionDigits }).format(value);
}

function TechnicalSheet({ item }: { item: ElaboracionDetalle }) {
  const sheet = item.ficha_tecnica;
  return <Section title="Ficha técnica estructurada">
    <p><strong>{sheet.persistida ? "Ficha persistida" : "Ficha técnica en construcción"}</strong></p>
    <p>Origen: {sheet.origen === "proyeccion_datos_existentes" ? "Proyección de datos existentes" : "Ficha técnica registrada"}.</p>
    <dl className="detail-grid">
      <dt>Descripción</dt><dd>{sheet.descripcion || "Pendiente"}</dd>
      <dt>Rendimiento</dt><dd>{yieldText(sheet)}</dd>
      <dt>Raciones</dt><dd>{sheet.raciones ?? "Pendientes"}</dd>
      <dt>Procedimiento</dt><dd>{sheet.proceso.procedimiento || "Pendiente"}</dd>
      <dt>Tiempo total</dt><dd>{sheet.tiempos.total || "Pendiente"}</dd>
      <dt>Temperaturas</dt><dd>{valuesText(sheet.temperaturas, "Pendientes")}</dd>
      <dt>Coste total</dt><dd>{money(sheet.escandallo?.coste_total, "Pendiente")}</dd>
      <dt>Coste por ración</dt><dd>{money(sheet.escandallo?.coste_por_racion, "Pendiente")}</dd>
      <dt>Alérgenos</dt><dd>{allergensText(sheet.alergenos, "No informados")}</dd>
      <dt>Conservación</dt><dd>{sheet.conservacion || "Pendiente"}</dd>
      <dt>Caducidad</dt><dd>{sheet.caducidad || "Pendiente"}</dd>
      <dt>Regeneración</dt><dd>{sheet.regeneracion || "Pendiente"}</dd>
      <dt>Presentación</dt><dd>{sheet.presentacion || "Pendiente"}</dd>
      <dt>Utensilios</dt><dd>{sheet.utensilios.length ? sheet.utensilios.join(", ") : "Pendientes"}</dd>
      <dt>Versión</dt><dd>{sheet.version ?? "Sin versión registrada"}</dd>
      <dt>Actualización</dt><dd>{dateText(sheet.actualizado_en)}</dd>
    </dl>
    <h4>Ingredientes</h4>
    <IngredientsTable ingredients={sheet.ingredientes} costing={false} />
    {sheet.campos_pendientes.length ? <><h4>Campos pendientes</h4><ul>{sheet.campos_pendientes.map((value) => <li key={value}>{value}</li>)}</ul></> : null}
  </Section>;
}

function Production({ item }: { item: ElaboracionDetalle }) {
  const { indicaciones, ordenes, necesidades, historial } = item.produccion;
  const indications = Object.entries(indicaciones).filter(([, value]) =>
    value != null && value !== "" && (!Array.isArray(value) || value.length),
  );
  if (!indications.length && !ordenes.length && !necesidades.length && !historial.length) {
    return <Section title="Producción"><p>No hay registros de producción asociados.</p></Section>;
  }
  return <Section title="Producción">
    <dl className="detail-grid">{indications.map(([key, value]) => <>
      <dt key={`${key}-key`}>{fieldLabel(key)}</dt><dd key={`${key}-value`}>{displayValue(value)}</dd>
    </>)}</dl>
    <RelationList title="Órdenes" values={ordenes} />
    <RelationList title="Necesidades" values={necesidades} />
    <RelationList title="Historial de producción" values={historial} />
    <p><Link to="/produccion">Abrir Producción</Link></p>
  </Section>;
}

function Documents({ item }: { item: ElaboracionDetalle }) {
  return <Section title="Documentos">{item.documentos.length
    ? <ul>{item.documentos.map((doc) => <li key={doc.referencia}><strong>{doc.nombre}</strong> · {doc.tipo}{doc.fecha ? ` · ${dateText(doc.fecha)}` : ""}</li>)}</ul>
    : <p>No hay documentos asociados a esta elaboración.</p>}
  </Section>;
}

function MenusEvents({ item }: { item: ElaboracionDetalle }) {
  return <Section title="Menús y eventos">
    <div><h4>Usada en menús</h4>{item.menus.length ? <ul>{item.menus.map((menu, index) => typeof menu === "string"
      ? <li key={`${menu}-${index}`}>{menu}</li>
      : <li key={menu.menu_id}><Link to={`/biblioteca/menus/${encodeURIComponent(menu.menu_id)}`}>{menu.nombre} · {menu.menu_id}</Link></li>)}</ul> : <p>No hay menús relacionados.</p>}</div>
    <RelationList title="Eventos" values={item.eventos} empty="No hay eventos relacionados." />
    {item.eventos.length ? <p><Link to="/eventos">Abrir Eventos</Link></p> : null}
  </Section>;
}

function History({ item }: { item: ElaboracionDetalle }) {
  return <Section title="Historial">
    {item.versiones.length ? <RelationList title="Versiones" values={item.versiones} /> : null}
    {item.historial.length
      ? <RelationList title="Cambios registrados" values={item.historial} />
      : <p>No hay historial estructurado disponible.</p>}
  </Section>;
}

function IngredientsTable({ ingredients, costing }: { ingredients: IngredienteReceta[]; costing: boolean }) {
  if (!ingredients.length) return <p>No hay ingredientes registrados.</p>;
  return <div className="catalog-table-wrap"><table className="catalog-table">
    <thead><tr><th>Ingrediente</th><th>Cantidad</th><th>Unidad</th><th>Merma</th>{costing ? <><th>Precio aplicado</th><th>Origen</th><th>Coste de línea</th></> : null}<th>Relación</th></tr></thead>
    <tbody>{ingredients.map((ingredient, index) => <tr key={`${ingredient.nombre_original}-${index}`}>
      <td>{ingredient.articulo_id ? <Link to={`/articulos/${encodeURIComponent(ingredient.articulo_id)}`}>{ingredient.nombre_original}</Link> : ingredient.nombre_original}</td>
      <td>{ingredient.cantidad ?? ingredient.cantidad_texto ?? "No informada"}</td>
      <td>{ingredient.unidad || "No informada"}</td>
      <td>{ingredient.merma == null ? "Sin merma registrada" : `${ingredient.merma}%`}</td>
      {costing ? <>
        <PriceCell ingredient={ingredient} />
        <td>{priceOrigin(ingredient.origen_precio)}
          {ingredient.fecha_precio ? <small>{dateText(ingredient.fecha_precio)}</small> : null}
          {ingredient.tipo_conversion && ingredient.tipo_conversion !== "no_disponible"
            ? <small>{conversionLabel(ingredient.tipo_conversion, ingredient.unidad_receta || ingredient.unidad, ingredient.unidad_precio_aplicado || ingredient.unidad_precio, ingredient.factor_conversion)}</small>
            : null}
        </td>
        <td>{ingredient.coste_linea == null ? (ingredient.motivo_sin_coste || "No disponible") : money(ingredient.coste_linea, "")}</td>
      </> : null}
      <td>{relationLabel(ingredient)}</td>
    </tr>)}</tbody>
  </table></div>;
}

function PriceCell({ ingredient }: { ingredient: IngredienteReceta }) {
  const applied = ingredient.precio_aplicado ?? ingredient.precio_unitario ?? ingredient.coste_unitario;
  const appliedUnit = ingredient.unidad_precio_aplicado ?? ingredient.unidad_precio;
  if (applied == null) return <td>No disponible</td>;
  const showOriginal = ingredient.precio_original != null && (
    ingredient.precio_original !== applied
    || ingredient.unidad_precio_original !== appliedUnit
  );
  return <td>{money(applied, "")}{appliedUnit ? ` / ${appliedUnit}` : ""}
    {showOriginal ? <small>Original: {money(ingredient.precio_original, "")}{ingredient.unidad_precio_original ? ` / ${ingredient.unidad_precio_original}` : " · unidad no registrada"}</small> : null}
  </td>;
}

function conversionLabel(type: string, from?: string | null, to?: string | null, factor?: number | null) {
  if (type === "normalizacion_heredada") return "Normalización heredada";
  if (type === "envase") return `Envase → ${to || "unidad base"}`;
  if (type === "metrica") return `Métrica ${from || "origen"} → ${to || "destino"}${factor == null ? "" : ` · factor ${factor}`}`;
  if (type === "directa") return `Directa ${from || to || "unidad"} → ${to || from || "unidad"}`;
  return "Sin conversión disponible";
}

function RelationList({ title, values, empty = "Sin registros." }: { title: string; values: unknown[]; empty?: string }) {
  return <div><h4>{title}</h4>{values.length
    ? <ul>{values.map((value, index) => <li key={index}>{displayValue(value)}</li>)}</ul>
    : <p>{empty}</p>}</div>;
}

function Section({ title, children }: React.PropsWithChildren<{ title: string }>) {
  return <section className="catalog-section"><h3>{title}</h3>{children}</section>;
}

function statusLabel(value?: string | null) {
  if (!value) return "No informado";
  const labels: Record<string, string> = {
    PENDIENTE_DE_COMPLETAR: "Pendiente de completar",
    EN_CONSTRUCCION: "En construcción", SIN_COSTE: "Sin coste",
    PARCIAL: "Parcial", DISPONIBLE: "Disponible", COMPLETO: "Completo",
    BORRADOR: "Borrador", ACTIVO: "Activo", INACTIVO: "Inactivo",
    DESACTUALIZADO: "Desactualizado", OPERATIVA: "Operativa", ARCHIVADA: "Archivada",
  };
  return labels[value] || value.replaceAll("_", " ").toLowerCase().replace(/^./, (x) => x.toUpperCase());
}
function relationLabel(ingredient: IngredienteReceta) {
  if (ingredient.tipo_componente === "ELABORACION") {
    return ingredient.escandallo_hijo_id ? "Subelaboración" : "Subelaboración sin relacionar";
  }
  const value = ingredient.estado_relacion;
  return value === "relacionado" ? "Relacionado" : value === "coincidencia_dudosa" ? "Coincidencia dudosa" : "Sin relacionar";
}
function priceOrigin(value?: string | null) {
  const labels: Record<string, string> = {
    tarifa_proveedor: "Tarifa de proveedor",
    historico_compras: "Histórico de compras",
    catalogo_articulos: "Catálogo de Artículos",
    escandallo_hijo: "Escandallo hijo",
    no_disponible: "Sistema",
  };
  return labels[value || ""] || value || "Sistema";
}
function tabLabel(value: string) {
  const labels: Record<string, string> = {
    "ficha-tecnica": "Ficha técnica",
    "menus-eventos": "Menús y eventos",
    produccion: "Producción",
  };
  return labels[value] || value[0].toUpperCase() + value.slice(1);
}
function money(value: number | null | undefined, empty: string) { return value == null ? empty : `${value.toFixed(2)} €`; }
function dateText(value?: string | null) {
  if (!value) return "No registrada";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat("es-ES").format(date);
}
function originText(value?: { tipo?: string | null; actor_id?: string | null; fecha?: string | null } | null) {
  if (!value?.tipo) return "No registrado";
  return [value.tipo, value.actor_id, value.fecha ? dateText(value.fecha) : null].filter(Boolean).join(" · ");
}
function yieldText(value: { rendimiento?: number | null; unidad_rendimiento?: string | null }) {
  return value.rendimiento == null || value.rendimiento <= 0 ? "Rendimiento pendiente" : `${value.rendimiento} ${value.unidad_rendimiento || ""}`.trim();
}
function valuesText(values: unknown[] | null | undefined, empty: string) { return values?.length ? values.map(displayValue).join(", ") : empty; }
function allergensText(values: string[] | null | undefined, empty = "Pendiente de completar") {
  if (values == null) return empty;
  return values.length ? values.join(", ") : "Sin alérgenos confirmados";
}
function displayValue(value: unknown): string {
  if (Array.isArray(value)) return value.map(displayValue).join(", ");
  if (value && typeof value === "object") return Object.entries(value as Record<string, unknown>).map(([key, item]) => `${fieldLabel(key)}: ${displayValue(item)}`).join(" · ");
  return String(value ?? "");
}
function fieldLabel(value: string) { return value.replaceAll("_", " ").replace(/^./, (x) => x.toUpperCase()); }
