import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { HostAiApiError } from "../../api/client";
import { articulosService } from "../../services/articulosService";
import { comprasService } from "../../services/comprasService";
import { menusService } from "../../services/menusService";
import type { ArticuloResumen } from "../../types/articulos";
import type { ElaboracionResumen } from "../../types/biblioteca";
import type { IntelligentMenu, MenuInput, MenuNeedLine, MenuNeedsResponse, MenuOrdersResponse, MenuProposalLine, MenuPurchaseProposalResponse, MenuState } from "../../types/menus";
import { BibliotecaNav } from "../components/BibliotecaNav";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { SearchField } from "../components/SearchField";

const DEFAULT_SECTIONS = ["Entrante", "Principal", "Postre"];

function emptyDraft(): MenuInput {
  return {
    nombre: "", estado: "BORRADOR", comensales: 1, observaciones: "",
    secciones: DEFAULT_SECTIONS.map((nombre) => ({ nombre, elaboraciones: [] })),
  };
}

export function MenusPage() {
  const [searchParams] = useSearchParams();
  const deepLinkLoaded = useRef(false);
  const [menus, setMenus] = useState<IntelligentMenu[]>([]);
  const [selected, setSelected] = useState<IntelligentMenu | null>(null);
  const [draft, setDraft] = useState<MenuInput>(emptyDraft);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<HostAiApiError | null>(null);
  const [message, setMessage] = useState("");
  const [pickerSection, setPickerSection] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [withRecipe, setWithRecipe] = useState(false);
  const [withCosting, setWithCosting] = useState(false);
  const [page, setPage] = useState(1);
  const [results, setResults] = useState<ElaboracionResumen[]>([]);
  const [catalogMeta, setCatalogMeta] = useState({ total: 0, totalPages: 0, categories: [] as string[], statuses: [] as string[] });
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [known, setKnown] = useState<Record<string, ElaboracionResumen>>({});
  const [needs, setNeeds] = useState<MenuNeedsResponse["necesidades"] | null>(null);
  const [needsFilter, setNeedsFilter] = useState("todos");
  const [needsLoading, setNeedsLoading] = useState(false);
  const [proposalLoading, setProposalLoading] = useState(false);
  const [orderLoading, setOrderLoading] = useState(false);
  const [needsError, setNeedsError] = useState("");
  const [proposal, setProposal] = useState<MenuPurchaseProposalResponse["propuesta"] | null>(null);
  const [proposalDirty, setProposalDirty] = useState(false);
  const [createdOrders, setCreatedOrders] = useState<Array<{ id: string; proveedor: string; estado: string }>>([]);
  const [orderResult, setOrderResult] = useState<Pick<MenuOrdersResponse, "lineas_incluidas" | "lineas_pendientes" | "lineas_excluidas" | "advertencias"> | null>(null);
  const [providerNames, setProviderNames] = useState<string[]>([]);
  const [productionLoading, setProductionLoading] = useState(false);
  const [productionPlanId, setProductionPlanId] = useState("");
  const [menuQuery, setMenuQuery] = useState("");

  useEffect(() => {
    void menusService.list().then(async (response) => {
      setMenus(response.menus);
      const menuId = searchParams.get("menu_id"); const proposalId = searchParams.get("proposal_id"); const purchaseView = searchParams.get("view") === "compra";
      if (!deepLinkLoaded.current && menuId) {
        deepLinkLoaded.current = true;
        const menu = response.menus.find((item) => item.id === menuId);
        if (!menu) throw new Error("No se encontr\u00f3 el men\u00fa solicitado.");
        edit(menu);
        if (proposalId) {
          const loaded = await menusService.getPurchaseProposal(menuId, proposalId);
          const normalized = normalizeProposal(loaded.propuesta);
          setProposal(normalized.proposal); setProposalDirty(normalized.changed);
          setMessage("Propuesta de Producci\u00f3n cargada para revisi\u00f3n.");
        } else if (purchaseView) {
          const [needsResponse, proposalResponse] = await Promise.all([
            menusService.needs(menuId), menusService.createPurchaseProposal(menuId),
          ]);
          const normalized = normalizeProposal(proposalResponse.propuesta);
          setNeeds(needsResponse.necesidades);
          setNeedsFilter("compra");
          setProposal(normalized.proposal); setProposalDirty(normalized.changed);
          setMessage("Propuesta de compra preparada para revisión. No se ha creado ningún pedido.");
        }
      }
    }).catch((reason) => setError(reason as HostAiApiError)).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (pickerSection === null) return;
    const timer = window.setTimeout(() => {
      setSearching(true);
      setSearchError("");
      void menusService.elaborations({
        q: query, page, page_size: 10, categoria: category, estado: status,
        tiene_receta: withRecipe || undefined,
        tiene_escandallo: withCosting || undefined,
      }).then((response) => {
        const catalog = response.elaboraciones;
        setResults(catalog.items);
        setKnown((current) => ({ ...current, ...Object.fromEntries(catalog.items.map((item) => [item.id, item])) }));
        setCatalogMeta({ total: catalog.total, totalPages: catalog.total_pages, categories: catalog.filters.categorias, statuses: catalog.filters.estados });
      }).catch((reason) => setSearchError((reason as HostAiApiError).message)).finally(() => setSearching(false));
    }, 300);
    return () => window.clearTimeout(timer);
  }, [pickerSection, query, category, status, withRecipe, withCosting, page]);

  useEffect(() => {
    if (!proposal) return;
    void comprasService.load().then((response) => {
      setProviderNames(response.proveedores.map((item) => item.nombre?.trim()).filter((name): name is string => Boolean(name)));
    }).catch(() => setProviderNames([]));
  }, [Boolean(proposal)]);

  const addedIds = useMemo(() => new Set(draft.secciones.flatMap((section) => section.elaboraciones.map((item) => item.elaboracion_id))), [draft.secciones]);
  const visibleMenus = useMemo(() => menus.filter((menu) => `${menu.nombre} ${menu.id} ${menu.estado}`.toLocaleLowerCase("es").includes(menuQuery.trim().toLocaleLowerCase("es"))), [menus, menuQuery]);

  function edit(menu: IntelligentMenu) {
    setSelected(menu);
    setDraft({
      nombre: menu.nombre, estado: menu.estado, comensales: menu.comensales,
      observaciones: menu.observaciones, version: menu.version,
      secciones: menu.secciones.map((section) => ({
        nombre: section.nombre,
        elaboraciones: section.elaboraciones.map((item, index) => ({
          elaboracion_id: item.elaboracion_id, cantidad: item.cantidad,
          orden: item.orden ?? index, observaciones: item.observaciones || "",
          version_elaboracion: item.version_elaboracion,
          coste_por_racion: item.coste_por_racion,
          coste_linea_por_comensal: item.coste_linea_por_comensal,
          coste_linea_total: item.coste_linea_total,
          estado_coste: item.estado_coste,
          motivo_coste_no_disponible: item.motivo_coste_no_disponible,
        })),
      })),
    });
    const currentOptions = menu.secciones.flatMap((section) => section.elaboraciones.map((item) => [item.elaboracion_id, {
      id: item.elaboracion_id, codigo: "", nombre: item.elaboracion_nombre, tipo: "Elaboración", estado: "", coste_por_racion: item.coste_por_racion,
      tiene_receta: true, tiene_escandallo: item.estado_coste !== "SIN_COSTE", tiene_ficha_tecnica: false, tiene_fotografia: false,
      tiene_documentos: false, tiene_produccion: false, tiene_relaciones_menu_evento: true,
    } as ElaboracionResumen] as const));
    setKnown((current) => ({ ...current, ...Object.fromEntries(currentOptions) }));
    setMessage("");
    setNeeds(null); setProposal(null); setProposalDirty(false); setCreatedOrders([]); setOrderResult(null); setNeedsError("");
  }

  async function loadNeeds() {
    if (!selected) return;
    setNeedsLoading(true); setMessage(""); setNeedsError("");
    try { setNeeds((await menusService.needs(selected.id)).necesidades); }
    catch (reason) { const detail = (reason as HostAiApiError).message; setMessage(detail); setNeedsError(detail); }
    finally { setNeedsLoading(false); }
  }

  async function generateProposal() {
    if (!selected) return;
    setProposalLoading(true); setMessage("");
    try {
      const response = await menusService.createPurchaseProposal(selected.id);
      const normalized = normalizeProposal(response.propuesta);
      setProposal(normalized.proposal); setProposalDirty(normalized.changed);
      setCreatedOrders(response.pedidos_creados ?? []);
      setOrderResult(response.lineas_incluidas && response.lineas_pendientes && response.lineas_excluidas
        ? { lineas_incluidas: response.lineas_incluidas, lineas_pendientes: response.lineas_pendientes, lineas_excluidas: response.lineas_excluidas, advertencias: response.advertencias ?? [] }
        : null);
      setMessage(response.pedidos_creados?.length
        ? `${response.pedidos_creados.length} borradores de pedido creados.`
        : "Propuesta creada. Completa las líneas pendientes para crear sus borradores.");
    }
    catch (reason) { setMessage((reason as HostAiApiError).message); }
    finally { setProposalLoading(false); }
  }

  async function saveProposal() {
    if (!selected || !proposal) return;
    setProposalLoading(true); setMessage("");
    try { setProposal((await menusService.updatePurchaseProposal(selected.id, proposal.id, { version: proposal.version, lineas: proposal.lineas })).propuesta); setProposalDirty(false); setMessage("Propuesta guardada."); }
    catch (reason) { setMessage((reason as HostAiApiError).message); }
    finally { setProposalLoading(false); }
  }

  async function generateProductionPlan() {
    if (!selected) return;
    setProductionLoading(true); setMessage("");
    try {
      const response = await menusService.createProductionPlan(selected.id);
      setProductionPlanId(response.plan.id);
      setMessage("Plan de producción generado sin modificar Stock.");
    } catch (reason) { setMessage((reason as HostAiApiError).message); }
    finally { setProductionLoading(false); }
  }

  async function createOrders() {
    if (!selected || !proposal) return;
    const ready = proposal.lineas.filter(isOrderableLine);
    const providers = new Set(ready.map((line) => line.proveedor));
    if (!window.confirm(`Se crearán ${providers.size} borradores de pedido para ${providers.size} proveedores.`)) return;
    setOrderLoading(true); setProposalLoading(true); setMessage("Creando borradores…");
    try {
      let savedProposal = proposal;
      if (proposalDirty) {
        savedProposal = (await menusService.updatePurchaseProposal(selected.id, proposal.id, { version: proposal.version, lineas: proposal.lineas })).propuesta;
        setProposal(savedProposal);
        setProposalDirty(false);
      }
      const response = await menusService.createDraftOrders(selected.id, savedProposal.id, savedProposal.version);
      setProposal(response.propuesta); setCreatedOrders(response.pedidos_creados); setOrderResult(response); setMessage("Borradores creados correctamente.");
    }
    catch (reason) { setMessage((reason as HostAiApiError).message); }
    finally { setOrderLoading(false); setProposalLoading(false); }
  }

  function updateProposalLine(id: string, changes: Record<string, unknown>) {
    setProposal((current) => current ? { ...current, lineas: current.lineas.map((line) => line.id === id ? { ...line, ...changes } : line) } : current);
    setProposalDirty(true);
    setOrderResult(null);
  }

  async function resolveArticle(lineId: string, articleId: string) {
    const article = (await articulosService.get(articleId)).articulo;
    const provider = article.proveedor || article.proveedores.find((item) => item.preferente)?.nombre || article.proveedores[0]?.nombre || null;
    setProviderNames((current) => provider && !current.some((item) => item.localeCompare(provider, undefined, { sensitivity: "accent" }) === 0) ? [...current, provider] : current);
    const quantity = proposal?.lineas.find((line) => line.id === lineId)?.cantidad_final_propuesta || 0;
    updateProposalLine(lineId, {
      articulo_id: article.id,
      articulo: article.nombre,
      proveedor: provider,
      proveedor_validado: Boolean(provider),
      formato_compra: article.unidad_compra || null,
      precio_estimado: article.precio ?? null,
      unidad_base: article.unidad_base || article.unidad || "u",
      coste_estimado: article.precio == null ? null : article.precio * quantity,
      estado: provider ? "Completo" : "Proveedor pendiente",
      advertencia: null,
    });
  }

  function updateSection(index: number, changes: Partial<MenuInput["secciones"][number]>) {
    setDraft((current) => ({ ...current, secciones: current.secciones.map((section, currentIndex) => currentIndex === index ? { ...section, ...changes } : section) }));
  }

  function addElaboration(item: ElaboracionResumen) {
    if (pickerSection === null || addedIds.has(item.id)) return;
    const section = draft.secciones[pickerSection];
    updateSection(pickerSection, { elaboraciones: [...section.elaboraciones, {
      elaboracion_id: item.id, cantidad: 1, orden: section.elaboraciones.length,
      observaciones: "", version_elaboracion: item.version,
      coste_por_racion: item.coste_por_racion,
      estado_coste: item.tiene_escandallo
        ? item.coste_completo ? "DISPONIBLE" : "INCOMPLETO"
        : "SIN_COSTE",
      motivo_coste_no_disponible: item.motivo_coste_no_disponible,
    }] });
  }

  function moveElaboration(sectionIndex: number, itemIndex: number, direction: -1 | 1) {
    const items = [...draft.secciones[sectionIndex].elaboraciones];
    const target = itemIndex + direction;
    if (target < 0 || target >= items.length) return;
    [items[itemIndex], items[target]] = [items[target], items[itemIndex]];
    updateSection(sectionIndex, { elaboraciones: items.map((item, index) => ({ ...item, orden: index })) });
  }

  async function save() {
    setSaving(true); setMessage("");
    try {
      const payload = menuPayload(draft);
      const response = selected ? await menusService.update(selected.id, { ...payload, version: selected.version }) : await menusService.create(payload);
      edit(response.menu);
      setMenus((current) => current.some((item) => item.id === response.menu.id) ? current.map((item) => item.id === response.menu.id ? response.menu : item) : [...current, response.menu]);
      setMessage("Menú guardado y costes recalculados por el backend.");
    } catch (reason) { setMessage((reason as HostAiApiError).message); } finally { setSaving(false); }
  }

  async function archive() {
    if (!selected) return;
    setSaving(true);
    try {
      await menusService.archive(selected.id, selected.version);
      setMenus((current) => current.filter((menu) => menu.id !== selected.id));
      setSelected(null); setDraft(emptyDraft()); setMessage("Menú archivado.");
    } catch (reason) { setMessage((reason as HostAiApiError).message); } finally { setSaving(false); }
  }

  if (loading) return <><BibliotecaNav /><LoadingState label="Cargando menús..." /></>;
  if (error) return <><BibliotecaNav /><ErrorState title="No se pudieron cargar los menús." detail={error.message} /></>;

  const readyLines = proposal?.lineas.filter(isOrderableLine) ?? [];
  const excludedLines = proposal?.lineas.filter((line) => !line.incluir) ?? [];
  const pendingLines = proposal?.lineas.filter((line) => line.incluir && !isOrderableLine(line)) ?? [];
  const readyProviders = new Set(readyLines.map((line) => line.proveedor));
  const createDisabledReason = orderDisabledReason(proposal, orderLoading, readyLines.length);

  return <section>
    <BibliotecaNav />
    {proposal ? <div className="menu-cost-summary" aria-label="Estado de preparación de pedidos"><strong>Líneas listas para pedido: {readyLines.length}</strong><span>Líneas pendientes: {pendingLines.length}</span><span>Líneas excluidas: {excludedLines.length}</span><span>Proveedores: {readyProviders.size}</span>{proposalDirty ? <span className="draft-warning">Los cambios se guardarán antes de crear los borradores.</span> : null}{orderResult ? <span>{orderResult.lineas_incluidas.length} incluidas · {orderResult.lineas_pendientes.length} pendientes · {orderResult.lineas_excluidas.length} excluidas</span> : null}{orderResult?.advertencias.map((warning) => <span className="draft-warning" key={warning}>{warning}</span>)}</div> : null}
    <header className="page-header"><div><p className="eyebrow">Biblioteca Culinaria</p><h2>Menús inteligentes</h2></div><button type="button" onClick={() => { setSelected(null); setDraft(emptyDraft()); }}>Nuevo menú</button></header>
    <p>Los menús referencian elaboraciones existentes. Recetas, escandallos y costes permanecen en la Biblioteca.</p>
    <div className="menu-workspace">
      <aside aria-label="Listado de menús"><h3>Menús</h3><SearchField value={menuQuery} onChange={setMenuQuery} placeholder="Buscar menús..." ariaLabel="Buscar menús" />{!menus.length ? <p>No hay menús creados.</p> : !visibleMenus.length ? <p className="module-empty-search">No hay menús que coincidan con “{menuQuery}”.</p> : visibleMenus.map((menu) => <button className={selected?.id === menu.id ? "active" : ""} key={menu.id} onClick={() => edit(menu)} type="button"><strong>{menu.nombre}</strong><span>{menu.estado} · v{menu.version}</span><span>{countElaborations(menu)} elaboraciones</span><span>{formatMoney(menu.coste_por_comensal)}/comensal · {formatMoney(menu.coste_total)} total</span><span>{menu.coste_completo ? "Coste completo" : `Coste parcial · ${menu.lineas_sin_coste} sin coste`}</span></button>)}</aside>
      <div className="menu-editor">
        <h3>{selected ? "Editar menú" : "Crear menú"}</h3>
        <label>Nombre<input aria-label="Nombre del menú" value={draft.nombre} onChange={(event) => setDraft({ ...draft, nombre: event.target.value })} /></label>
        <div className="menu-editor-row"><label>Estado<select aria-label="Estado del menú" value={draft.estado} onChange={(event) => setDraft({ ...draft, estado: event.target.value as MenuState })}><option value="BORRADOR">Borrador</option><option value="ACTIVO">Activo</option><option value="ARCHIVADO">Archivado</option></select></label><label>Comensales<input aria-label="Comensales" min="1" type="number" value={draft.comensales} onChange={(event) => setDraft({ ...draft, comensales: Number(event.target.value) })} /></label></div>
        {draft.secciones.map((section, sectionIndex) => <fieldset key={`${section.nombre}-${sectionIndex}`}><legend>Sección {sectionIndex + 1}</legend>
          <input aria-label={`Nombre sección ${sectionIndex + 1}`} value={section.nombre} onChange={(event) => updateSection(sectionIndex, { nombre: event.target.value })} />
          {section.elaboraciones.map((item, itemIndex) => { const option = known[item.elaboracion_id]; return <div className="menu-elaboration-card" key={`${item.elaboracion_id}-${itemIndex}`}>
            <div><strong>{option?.nombre || item.elaboracion_id}</strong><small>{option?.codigo || item.elaboracion_id} · {costLabel(item.estado_coste, item.coste_por_racion ?? option?.coste_por_racion)}</small>{item.coste_linea_por_comensal != null ? <span>{formatMoney(item.coste_linea_por_comensal)}/comensal · {formatMoney(item.coste_linea_total)} total de línea</span> : null}{item.motivo_coste_no_disponible ? <span className="draft-warning">{item.motivo_coste_no_disponible}</span> : null}</div>
            <input aria-label={`Cantidad ${sectionIndex + 1}-${itemIndex + 1}`} min="0.01" step="any" type="number" value={item.cantidad} onChange={(event) => updateSection(sectionIndex, { elaboraciones: section.elaboraciones.map((value, index) => index === itemIndex ? { ...value, cantidad: Number(event.target.value) } : value) })} />
            <input aria-label={`Observaciones ${sectionIndex + 1}-${itemIndex + 1}`} placeholder="Observaciones" value={item.observaciones || ""} onChange={(event) => updateSection(sectionIndex, { elaboraciones: section.elaboraciones.map((value, index) => index === itemIndex ? { ...value, observaciones: event.target.value } : value) })} />
            <div className="menu-item-actions"><button aria-label={`Subir ${option?.nombre || item.elaboracion_id}`} disabled={itemIndex === 0} type="button" onClick={() => moveElaboration(sectionIndex, itemIndex, -1)}>↑</button><button aria-label={`Bajar ${option?.nombre || item.elaboracion_id}`} disabled={itemIndex === section.elaboraciones.length - 1} type="button" onClick={() => moveElaboration(sectionIndex, itemIndex, 1)}>↓</button><button type="button" onClick={() => updateSection(sectionIndex, { elaboraciones: section.elaboraciones.filter((_, index) => index !== itemIndex) })}>Quitar</button></div>
          </div>; })}
          <button type="button" onClick={() => { setPickerSection(sectionIndex); setPage(1); }}>Añadir elaboración</button>
        </fieldset>)}
        <button type="button" onClick={() => setDraft({ ...draft, secciones: [...draft.secciones, { nombre: "Nueva sección", elaboraciones: [] }] })}>Añadir sección</button>
        <label>Observaciones<textarea aria-label="Observaciones del menú" value={draft.observaciones} onChange={(event) => setDraft({ ...draft, observaciones: event.target.value })} /></label>
        {selected ? <div className="menu-cost-summary"><strong>{selected.coste_completo ? "Coste automático completo" : "Coste parcial"}</strong><span>Total conocido: {formatMoney(selected.coste_total)}</span><span>Por comensal conocido: {formatMoney(selected.coste_por_comensal)}</span>{!selected.coste_completo ? <span className="draft-warning">{selected.lineas_sin_coste} elaboraciones sin coste. El total no es definitivo.</span> : null}{selected.advertencias.map((warning, index) => <p className="draft-warning" key={`${warning}-${index}`}>{warning}</p>)}{selected.incidencias.map((issue, index) => <p className="draft-warning" key={`${issue.tipo}-${index}`}>{issue.detalle || issue.tipo}</p>)}</div> : null}
        <section className="menu-cost-summary" aria-label="Necesidades y compras"><h3>Necesidades y compras</h3><p>Proyección informativa: no descuenta Stock ni crea pedidos.</p><button disabled={!selected || needsLoading} type="button" onClick={() => void loadNeeds()}>{needsLoading ? "Calculando..." : "Calcular necesidades"}</button>{needs ? <><div><strong>{needs.summary.articulos} artículos</strong><span>{needs.summary.cubiertos} cubiertos · {needs.summary.compra_necesaria} con faltante calculado · {needs.summary.candidatas_propuesta} candidatas o pendientes</span></div><label>Filtrar<select aria-label="Filtrar necesidades" value={needsFilter} onChange={(event) => setNeedsFilter(event.target.value)}><option value="todos">Todos</option><option value="compra">Compra necesaria</option><option value="cubiertos">Cubiertos</option><option value="pendientes">Pendientes</option></select></label>{filterNeeds(needs.lines, needsFilter).map((line, index) => <NeedCard key={`${line.articulo_id || line.ingrediente_nombre}-${index}`} line={line} />)}<button disabled={Boolean(proposalDisabledReason(selected, needs, proposalLoading, needsError))} type="button" onClick={() => void generateProposal()}>{proposalLoading ? "Generando propuesta…" : "Generar propuesta de compra"}</button></> : null}{proposalDisabledReason(selected, needs, proposalLoading, needsError) ? <p className="draft-warning">{proposalDisabledReason(selected, needs, proposalLoading, needsError)}</p> : null}{proposal ? <ProposalReview proposal={proposal} providerNames={providerNames} loading={proposalLoading} disabledReason={createDisabledReason} onUpdate={updateProposalLine} onResolveArticle={resolveArticle} onSave={() => void saveProposal()} onCreate={() => void createOrders()} /> : null}{createdOrders.length ? <div role="status"><strong>{createdOrders.length} borradores creados</strong>{createdOrders.map((order) => <span key={order.id}>{order.id} · {order.proveedor} · {order.estado}</span>)}<Link to="/compras">Abrir Compras</Link><span>Stock sin cambios. No se ha enviado ningún pedido.</span></div> : null}</section>
        <section className="menu-cost-summary" aria-label="Plan de producción"><h3>Producción</h3><p>Genera un borrador operativo. El cálculo no modifica Stock.</p><button disabled={!selected || productionLoading} type="button" onClick={() => void generateProductionPlan()}>{productionLoading ? "Generando plan..." : "Generar plan de producción"}</button>{productionPlanId ? <div role="status"><strong>Plan {productionPlanId} preparado</strong><Link to="/produccion">Abrir Producción</Link></div> : null}</section>
        <div className="menu-actions"><button disabled={saving} type="button" onClick={() => void save()}>{saving ? "Guardando..." : "Guardar menú"}</button>{selected && selected.estado !== "ARCHIVADO" ? <button disabled={saving} type="button" onClick={() => void archive()}>Archivar menú</button> : null}</div>
        {message ? <p role="status">{message}</p> : null}
      </div>
    </div>
    {pickerSection !== null ? <div className="menu-picker" role="dialog" aria-label="Seleccionar elaboraciones"><div className="menu-picker-panel">
      <header><div><p className="eyebrow">Toda la Biblioteca</p><h3>Añadir a {draft.secciones[pickerSection]?.nombre}</h3></div><button type="button" onClick={() => setPickerSection(null)}>Cerrar</button></header>
      <label>Buscar<input autoFocus aria-label="Buscar elaboraciones para menú" placeholder="Nombre, código, categoría o ingrediente" value={query} onChange={(event) => { setQuery(event.target.value); setPage(1); }} /></label>
      <div className="menu-picker-filters"><label>Categoría<select aria-label="Filtrar categoría" value={category} onChange={(event) => { setCategory(event.target.value); setPage(1); }}><option value="">Todas</option>{catalogMeta.categories.map((value) => <option key={value}>{value}</option>)}</select></label><label>Estado<select aria-label="Filtrar estado" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}><option value="">Todos</option>{catalogMeta.statuses.map((value) => <option key={value}>{value}</option>)}</select></label><label><input checked={withRecipe} type="checkbox" onChange={(event) => { setWithRecipe(event.target.checked); setPage(1); }} /> Con receta</label><label><input checked={withCosting} type="checkbox" onChange={(event) => { setWithCosting(event.target.checked); setPage(1); }} /> Con escandallo</label></div>
      {searching ? <p>Cargando elaboraciones...</p> : searchError ? <p role="alert">{searchError}</p> : !results.length ? <p>No hay elaboraciones para esta búsqueda.</p> : <div className="menu-picker-results">{results.map((item) => <article key={item.id}><div><strong>{item.nombre}</strong><small>{item.codigo} · {item.categoria || "Sin categoría"} · {item.estado}</small><span>{item.tiene_receta ? "Receta disponible" : "Sin receta"} · {item.tiene_escandallo ? "Escandallo disponible" : "Coste pendiente"} · {item.tiene_ficha_tecnica ? "Ficha técnica disponible" : "Sin ficha técnica"}</span><span>{item.rendimiento == null ? "Rendimiento no disponible" : `${item.rendimiento} ${item.unidad_rendimiento || ""}`} · {item.coste_por_racion == null ? "Coste no disponible" : `${formatMoney(item.coste_por_racion)}/ración`}</span></div><button disabled={addedIds.has(item.id)} type="button" onClick={() => addElaboration(item)}>{addedIds.has(item.id) ? "Ya añadida" : "Añadir"}</button></article>)}</div>}
      <nav className="catalog-pagination"><button disabled={page <= 1} onClick={() => setPage(page - 1)}>Anterior</button><span>Página {page} de {catalogMeta.totalPages || 1} · {catalogMeta.total} resultados</span><button disabled={page >= catalogMeta.totalPages} onClick={() => setPage(page + 1)}>Siguiente</button></nav>
    </div></div> : null}
  </section>;
}

type ProposalIssue = { type: string; message: string; field: string };

function ProposalReview({ proposal, providerNames, loading, disabledReason, onUpdate, onResolveArticle, onSave, onCreate }: {
  proposal: MenuPurchaseProposalResponse["propuesta"];
  providerNames: string[];
  loading: boolean;
  disabledReason: string;
  onUpdate: (id: string, changes: Record<string, unknown>) => void;
  onResolveArticle: (lineId: string, articleId: string) => Promise<void>;
  onSave: () => void;
  onCreate: () => void;
}) {
  const included = proposal.lineas.filter((line) => line.incluir);
  const complete = included.filter(isOrderableLine);
  const pending = included.filter((line) => !isOrderableLine(line));
  const grouped = new Map<string, Array<{ line: MenuProposalLine; issue: ProposalIssue }>>();
  for (const line of included) for (const issue of proposalLineIssues(line)) {
    grouped.set(issue.type, [...(grouped.get(issue.type) ?? []), { line, issue }]);
  }
  const goTo = (lineId: string, field: string) => {
    const card = document.getElementById(`proposal-line-${lineId}`);
    card?.scrollIntoView?.({ behavior: "smooth", block: "center" });
    card?.querySelector<HTMLElement>(`[data-field="${field}"]`)?.focus();
  };
  return <div className="purchase-proposal" aria-label="Revisar propuesta de compra">
    <header className="proposal-summary">
      <div><p className="eyebrow">Propuesta de compra</p><h3>Revisar propuesta</h3><span className="proposal-state">Propuesta {proposal.estado}</span></div>
      <dl><div><dt>Artículos</dt><dd>{proposal.lineas.length}</dd></div><div><dt>Completos</dt><dd>{complete.length}</dd></div><div><dt>Pendientes</dt><dd>{pending.length}</dd></div><div><dt>Coste estimado</dt><dd>{proposal.coste_completo ? formatMoney(proposal.coste_estimado) : `${formatMoney(proposal.coste_estimado)} parcial`}</dd></div></dl>
      {pending.length ? <p className="proposal-block-message">Hay {pending.length} {pending.length === 1 ? "artículo que requiere" : "artículos que requieren"} atención.</p> : <p className="proposal-ready-message">Las líneas incluidas están preparadas para crear borradores.</p>}
    </header>
    {grouped.size ? <aside className="proposal-issues" aria-label="Incidencias de la propuesta"><h4>Incidencias y advertencias</h4>{[...grouped.entries()].map(([type, entries]) => <div key={type}><strong>{type} ({entries.length})</strong>{entries.map(({ line, issue }) => <button key={`${line.id}-${issue.field}`} type="button" onClick={() => goTo(line.id, issue.field)}>{line.articulo || "Artículo sin relacionar"}: {issue.message}</button>)}</div>)}</aside> : null}
    {[...new Set(proposal.advertencias)].length ? <ul className="proposal-warnings">{[...new Set(proposal.advertencias)].map((warning) => <li key={warning}>{warning}</li>)}</ul> : null}
    <div className="proposal-lines">{proposal.lineas.map((line) => {
      const issues = proposalLineIssues(line);
      const blocking = line.incluir && !isOrderableLine(line);
      const tone = !line.incluir ? "excluded" : blocking ? "pending" : issues.length ? "warning" : "complete";
      return <article className={`proposal-line proposal-line-${tone}`} id={`proposal-line-${line.id}`} key={line.id}>
        <header><label className="proposal-include"><input aria-label={`Incluir ${line.articulo || line.id}`} checked={line.incluir} type="checkbox" onChange={(event) => onUpdate(line.id, { incluir: event.target.checked })} /> Incluir artículo</label><strong>{line.articulo || "Artículo sin relacionar"}</strong><span className={`proposal-badge proposal-badge-${tone}`}>{!line.incluir ? "Excluido" : blocking ? "Requiere atención" : "Completo"}</span></header>
        <div className="proposal-info-grid"><div><span>Estado</span><strong>{line.estado}</strong></div><div><span>Necesario</span><strong>{formatQuantity(line.cantidad_necesaria, line.unidad_base)}</strong></div><div><span>Disponible</span><strong>{line.cantidad_disponible == null ? "Desconocido" : formatQuantity(line.cantidad_disponible, line.unidad_base)}</strong></div><div><span>Falta calculada</span><strong>{formatQuantity(line.cantidad_faltante, line.unidad_base)}</strong></div><div><span>Formato</span><strong>{line.formato_compra || "Pendiente"}</strong></div><div><span>Precio estimado</span><strong>{line.precio_estimado == null ? "Pendiente" : `${formatMoney(line.precio_estimado)}/${line.unidad_base}`}</strong></div></div>
        {!line.articulo_id ? <ArticleResolver line={line} onResolve={onResolveArticle} /> : null}
        <div className="proposal-edit-grid"><label>Cantidad propuesta<input data-field="cantidad" aria-label={`Cantidad propuesta ${line.id}`} min="0" step="any" type="number" value={line.cantidad_final_propuesta ?? ""} onChange={(event) => onUpdate(line.id, { cantidad_final_propuesta: event.target.value === "" ? null : Number(event.target.value) })} /></label><ProviderResolver line={line} providerNames={providerNames} onUpdate={onUpdate} /><label className="proposal-observations">Observaciones<input data-field="observaciones" aria-label={`Observaciones ${line.id}`} value={line.observaciones} onChange={(event) => onUpdate(line.id, { observaciones: event.target.value })} /></label></div>
        {issues.length || line.advertencia ? <ul className="proposal-line-messages">{issues.map((issue) => <li className={isBlockingIssue(issue) ? "blocking" : "warning"} key={issue.type}>{issue.message}</li>)}{line.advertencia ? <li className="warning">{line.advertencia}</li> : null}</ul> : null}
      </article>;
    })}</div>
    <footer className="proposal-actions"><button disabled={loading} type="button" onClick={onSave}>Guardar propuesta</button><button disabled={loading || Boolean(disabledReason)} type="button" onClick={onCreate}>Crear borradores de pedido</button>{loading ? <p className="proposal-block-message">Espera a que termine la operación en curso.</p> : disabledReason ? <p className="proposal-block-message">{disabledReason}</p> : null}<span>No se ha creado ningún pedido ni modificado Stock.</span></footer>
  </div>;
}

function ProviderResolver({ line, providerNames, onUpdate }: { line: MenuProposalLine; providerNames: string[]; onUpdate: (id: string, changes: Record<string, unknown>) => void }) {
  const listId = `provider-options-${line.id}`;
  const change = (value: string) => {
    const match = providerNames.find((name) => normalizeText(name) === normalizeText(value));
    onUpdate(line.id, { proveedor: match || value, proveedor_validado: Boolean(match) });
  };
  return <label>{line.proveedor ? "Proveedor" : "Proveedor pendiente"}<input data-field="proveedor" aria-label={`Proveedor ${line.id}`} list={listId} placeholder="Buscar proveedor..." value={line.proveedor || ""} onChange={(event) => change(event.target.value)} /><datalist id={listId}>{providerNames.map((name) => <option key={name} value={name} />)}</datalist>{line.proveedor && line.proveedor_validado === false ? <small className="draft-warning">Selecciona un proveedor existente de la lista.</small> : null}</label>;
}

function ArticleResolver({ line, onResolve }: { line: MenuProposalLine; onResolve: (lineId: string, articleId: string) => Promise<void> }) {
  const [query, setQuery] = useState(line.articulo || "");
  const [results, setResults] = useState<ArticuloResumen[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (query.trim().length < 2) { setResults([]); return; }
    const timer = window.setTimeout(() => {
      setLoading(true); setError("");
      void articulosService.list({ q: query.trim(), page_size: 8 }).then((response) => setResults(response.catalogo.items)).catch((reason) => setError((reason as Error).message)).finally(() => setLoading(false));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [query]);
  const select = async (articleId: string) => {
    setLoading(true); setError("");
    try { await onResolve(line.id, articleId); setResults([]); }
    catch (reason) { setError((reason as Error).message); }
    finally { setLoading(false); }
  };
  return <section className="proposal-resolver" data-field="articulo" tabIndex={-1}><strong>Artículo pendiente</strong><label>Buscar artículo existente<input aria-label={`Buscar artículo ${line.id}`} placeholder="Nombre, código, alias o texto parcial" value={query} onChange={(event) => setQuery(event.target.value)} /></label>{loading ? <small>Buscando artículos...</small> : null}{error ? <small role="alert" className="draft-warning">{error}</small> : null}{results.length ? <ul>{results.map((article) => <li key={article.id}><button type="button" onClick={() => void select(article.id)}><strong>{article.nombre}</strong><span>{article.codigo} · {article.proveedor || "Sin proveedor"}</span></button></li>)}</ul> : query.trim().length >= 2 && !loading && !error ? <small>No hay artículos coincidentes.</small> : null}</section>;
}

function proposalLineIssues(line: MenuProposalLine): ProposalIssue[] {
  if (!line.incluir) return [];
  const issues: ProposalIssue[] = [];
  if (!line.articulo_id) issues.push({ type: "Artículo sin relacionar", field: "articulo", message: "Relaciona el artículo antes de crear el borrador." });
  if (line.cantidad_final_propuesta == null || line.cantidad_final_propuesta <= 0) issues.push({ type: "Cantidad propuesta pendiente", field: "cantidad", message: "Introduce una cantidad mayor que cero." });
  if (!line.proveedor || line.proveedor_validado === false) issues.push({ type: "Proveedor pendiente", field: "proveedor", message: "Selecciona un proveedor existente." });
  if (!line.unidad_base && !line.formato_compra) issues.push({ type: "Formato pendiente", field: "formato", message: "La línea no tiene unidad ni formato de compra." });
  if (line.precio_estimado == null) issues.push({ type: "Precio pendiente", field: "precio", message: "El coste estimado todavía no está disponible." });
  return issues;
}

function isBlockingIssue(issue: ProposalIssue): boolean {
  return ["Artículo sin relacionar", "Cantidad propuesta pendiente", "Proveedor pendiente"].includes(issue.type);
}

function NeedCard({ line }: { line: MenuNeedLine }) {
  return <article><strong>{line.articulo_nombre || line.ingrediente_nombre}</strong><span>Necesario: {formatQuantity(line.cantidad_necesaria, line.unidad_necesaria)} · Disponible: {formatQuantity(line.stock_disponible, line.unidad_stock)}</span><span>Falta: {formatQuantity(line.cantidad_faltante, line.unidad_necesaria)} · {line.estado}</span><span>Proveedor: {line.proveedor_preferente || "Pendiente"} · Compra propuesta: {formatQuantity(line.cantidad_propuesta_compra, line.unidad_necesaria)}</span>{line.motivo_no_resuelto ? <span className="draft-warning">{line.motivo_no_resuelto}</span> : null}<details><summary>Ver trazabilidad</summary>{line.origenes.map((origin, index) => <p key={`${origin.elaboracion_id}-${index}`}>{origin.seccion} · {origin.elaboracion_nombre}: {formatQuantity(origin.cantidad, origin.unidad)} (factor x{origin.factor_escalado})</p>)}</details></article>;
}

function filterNeeds(lines: MenuNeedLine[], filter: string) {
  if (filter === "compra") return lines.filter((line) => (line.cantidad_faltante || 0) > 0);
  if (filter === "cubiertos") return lines.filter((line) => line.estado === "Cubierto por stock");
  if (filter === "pendientes") return lines.filter((line) => line.cantidad_faltante == null || line.estado.includes("pendiente") || line.estado.startsWith("Sin "));
  return lines;
}

function proposalDisabledReason(selected: IntelligentMenu | null, needs: MenuNeedsResponse["necesidades"] | null, loading: boolean, technicalError: string) {
  if (!selected) return "Guarda primero el menú.";
  if (loading) return "La propuesta se está generando.";
  if (technicalError) return `Error técnico al calcular necesidades: ${technicalError}`;
  if (!needs) return "Calcula primero las necesidades.";
  if (needs.summary.candidatas_propuesta === 0) return "No existen necesidades de compra.";
  return "";
}

function isOrderableLine(line: MenuProposalLine) {
  return Boolean(
    line.incluir && line.articulo_id && line.proveedor && line.proveedor_validado !== false
    && line.cantidad_final_propuesta != null && line.cantidad_final_propuesta > 0,
  );
}

function normalizeProposal(proposal: MenuPurchaseProposalResponse["propuesta"]): { proposal: MenuPurchaseProposalResponse["propuesta"]; changed: boolean } {
  let changed = false;
  const lineas = proposal.lineas.map((line) => {
    const provider = providerName(line.proveedor) || providerName(line.proveedor_sugerido) || providerName(line.proveedor_preferente);
    const quantity = line.cantidad_final_propuesta == null && line.cantidad_necesaria > 0
      ? line.cantidad_necesaria
      : line.cantidad_final_propuesta;
    if (provider !== providerName(line.proveedor) || quantity !== line.cantidad_final_propuesta) changed = true;
    return { ...line, proveedor: provider || null, proveedor_validado: Boolean(provider), cantidad_final_propuesta: quantity };
  });
  return { proposal: { ...proposal, lineas }, changed };
}

function providerName(value: unknown): string {
  if (typeof value === "string") return value.trim();
  if (value && typeof value === "object" && "nombre" in value) return String((value as { nombre?: unknown }).nombre || "").trim();
  return "";
}

function normalizeText(value: string): string {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLocaleLowerCase("es");
}

function orderDisabledReason(proposal: MenuPurchaseProposalResponse["propuesta"] | null, loading: boolean, readyCount: number) {
  if (!proposal) return "Genera primero una propuesta.";
  if (loading) return "Creando borradores…";
  if (readyCount === 0) return "No hay líneas listas. Revisa artículo, proveedor y cantidad.";
  return "";
}

function formatQuantity(value: number | null | undefined, unit: string | null | undefined) {
  return value == null ? "Pendiente" : `${new Intl.NumberFormat("es-ES", { maximumFractionDigits: 4 }).format(value)} ${unit || ""}`.trim();
}

function formatMoney(value: number | null | undefined) {
  return new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR" }).format(value || 0);
}

function countElaborations(menu: IntelligentMenu) {
  return menu.secciones.reduce((total, section) => total + section.elaboraciones.length, 0);
}

function costLabel(state: string | undefined, value: number | null | undefined) {
  if (state === "SIN_COSTE") return "Sin escandallo";
  if (state === "INCOMPLETO") return "Coste incompleto";
  return value == null ? "Coste no disponible" : `${formatMoney(value)}/ración`;
}

function menuPayload(draft: MenuInput): MenuInput {
  return {
    nombre: draft.nombre, estado: draft.estado, comensales: draft.comensales,
    observaciones: draft.observaciones,
    secciones: draft.secciones.map((section) => ({
      nombre: section.nombre,
      elaboraciones: section.elaboraciones.map((item) => ({
        elaboracion_id: item.elaboracion_id, cantidad: item.cantidad,
        orden: item.orden, observaciones: item.observaciones,
        version_elaboracion: item.version_elaboracion,
      })),
    })),
  };
}
