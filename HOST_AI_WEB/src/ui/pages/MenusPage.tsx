import { useEffect, useMemo, useState } from "react";
import { HostAiApiError } from "../../api/client";
import { menusService } from "../../services/menusService";
import type { ElaboracionResumen } from "../../types/biblioteca";
import type { IntelligentMenu, MenuInput, MenuState } from "../../types/menus";
import { BibliotecaNav } from "../components/BibliotecaNav";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

const DEFAULT_SECTIONS = ["Entrante", "Principal", "Postre"];

function emptyDraft(): MenuInput {
  return {
    nombre: "", estado: "BORRADOR", comensales: 1, observaciones: "",
    secciones: DEFAULT_SECTIONS.map((nombre) => ({ nombre, elaboraciones: [] })),
  };
}

export function MenusPage() {
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

  useEffect(() => {
    void menusService.list().then((response) => setMenus(response.menus)).catch((reason) => setError(reason as HostAiApiError)).finally(() => setLoading(false));
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

  const addedIds = useMemo(() => new Set(draft.secciones.flatMap((section) => section.elaboraciones.map((item) => item.elaboracion_id))), [draft.secciones]);

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
        })),
      })),
    });
    const currentOptions = menu.secciones.flatMap((section) => section.elaboraciones.map((item) => [item.elaboracion_id, {
      id: item.elaboracion_id, codigo: "", nombre: item.elaboracion_nombre, tipo: "Elaboración", estado: "", coste_por_racion: item.coste_por_comensal,
      tiene_receta: true, tiene_escandallo: item.coste_por_comensal > 0, tiene_ficha_tecnica: false, tiene_fotografia: false,
      tiene_documentos: false, tiene_produccion: false, tiene_relaciones_menu_evento: true,
    } as ElaboracionResumen] as const));
    setKnown((current) => ({ ...current, ...Object.fromEntries(currentOptions) }));
    setMessage("");
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
      const response = selected ? await menusService.update(selected.id, { ...draft, version: selected.version }) : await menusService.create(draft);
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

  return <section>
    <BibliotecaNav />
    <header className="page-header"><div><p className="eyebrow">Biblioteca Culinaria</p><h2>Menús inteligentes</h2></div><button type="button" onClick={() => { setSelected(null); setDraft(emptyDraft()); }}>Nuevo menú</button></header>
    <p>Los menús referencian elaboraciones existentes. Recetas, escandallos y costes permanecen en la Biblioteca.</p>
    <div className="menu-workspace">
      <aside aria-label="Listado de menús"><h3>Menús</h3>{!menus.length ? <p>No hay menús creados.</p> : menus.map((menu) => <button className={selected?.id === menu.id ? "active" : ""} key={menu.id} onClick={() => edit(menu)} type="button"><strong>{menu.nombre}</strong><span>{menu.estado} · v{menu.version}</span><span>{formatMoney(menu.coste_total)} · {formatMoney(menu.coste_por_comensal)}/comensal</span></button>)}</aside>
      <div className="menu-editor">
        <h3>{selected ? "Editar menú" : "Crear menú"}</h3>
        <label>Nombre<input aria-label="Nombre del menú" value={draft.nombre} onChange={(event) => setDraft({ ...draft, nombre: event.target.value })} /></label>
        <div className="menu-editor-row"><label>Estado<select aria-label="Estado del menú" value={draft.estado} onChange={(event) => setDraft({ ...draft, estado: event.target.value as MenuState })}><option value="BORRADOR">Borrador</option><option value="ACTIVO">Activo</option><option value="ARCHIVADO">Archivado</option></select></label><label>Comensales<input aria-label="Comensales" min="1" type="number" value={draft.comensales} onChange={(event) => setDraft({ ...draft, comensales: Number(event.target.value) })} /></label></div>
        {draft.secciones.map((section, sectionIndex) => <fieldset key={`${section.nombre}-${sectionIndex}`}><legend>Sección {sectionIndex + 1}</legend>
          <input aria-label={`Nombre sección ${sectionIndex + 1}`} value={section.nombre} onChange={(event) => updateSection(sectionIndex, { nombre: event.target.value })} />
          {section.elaboraciones.map((item, itemIndex) => { const option = known[item.elaboracion_id]; return <div className="menu-elaboration-card" key={`${item.elaboracion_id}-${itemIndex}`}>
            <div><strong>{option?.nombre || item.elaboracion_id}</strong><small>{option?.codigo || item.elaboracion_id} · {option?.coste_por_racion == null ? "Coste no disponible" : `${formatMoney(option.coste_por_racion)}/ración`}</small></div>
            <input aria-label={`Cantidad ${sectionIndex + 1}-${itemIndex + 1}`} min="0.01" step="any" type="number" value={item.cantidad} onChange={(event) => updateSection(sectionIndex, { elaboraciones: section.elaboraciones.map((value, index) => index === itemIndex ? { ...value, cantidad: Number(event.target.value) } : value) })} />
            <input aria-label={`Observaciones ${sectionIndex + 1}-${itemIndex + 1}`} placeholder="Observaciones" value={item.observaciones || ""} onChange={(event) => updateSection(sectionIndex, { elaboraciones: section.elaboraciones.map((value, index) => index === itemIndex ? { ...value, observaciones: event.target.value } : value) })} />
            <div className="menu-item-actions"><button aria-label={`Subir ${option?.nombre || item.elaboracion_id}`} disabled={itemIndex === 0} type="button" onClick={() => moveElaboration(sectionIndex, itemIndex, -1)}>↑</button><button aria-label={`Bajar ${option?.nombre || item.elaboracion_id}`} disabled={itemIndex === section.elaboraciones.length - 1} type="button" onClick={() => moveElaboration(sectionIndex, itemIndex, 1)}>↓</button><button type="button" onClick={() => updateSection(sectionIndex, { elaboraciones: section.elaboraciones.filter((_, index) => index !== itemIndex) })}>Quitar</button></div>
          </div>; })}
          <button type="button" onClick={() => { setPickerSection(sectionIndex); setPage(1); }}>Añadir elaboración</button>
        </fieldset>)}
        <button type="button" onClick={() => setDraft({ ...draft, secciones: [...draft.secciones, { nombre: "Nueva sección", elaboraciones: [] }] })}>Añadir sección</button>
        <label>Observaciones<textarea aria-label="Observaciones del menú" value={draft.observaciones} onChange={(event) => setDraft({ ...draft, observaciones: event.target.value })} /></label>
        {selected ? <div className="menu-cost-summary"><strong>Coste automático</strong><span>Total: {formatMoney(selected.coste_total)}</span><span>Por comensal: {formatMoney(selected.coste_por_comensal)}</span>{selected.incidencias.map((issue, index) => <p className="draft-warning" key={`${issue.tipo}-${index}`}>{issue.detalle || issue.tipo}</p>)}</div> : null}
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

function formatMoney(value: number) {
  return new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR" }).format(value || 0);
}
