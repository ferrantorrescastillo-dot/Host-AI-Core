import { useEffect, useState } from "react";
import { HostAiApiError } from "../../api/client";
import { menusService } from "../../services/menusService";
import type {
  IntelligentMenu,
  MenuElaborationOption,
  MenuInput,
  MenuState,
} from "../../types/menus";
import { BibliotecaNav } from "../components/BibliotecaNav";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

const DEFAULT_SECTIONS = ["Entrante", "Principal", "Postre"];

function emptyDraft(): MenuInput {
  return {
    nombre: "",
    estado: "BORRADOR",
    comensales: 1,
    observaciones: "",
    secciones: DEFAULT_SECTIONS.map((nombre) => ({ nombre, elaboraciones: [] })),
  };
}

export function MenusPage() {
  const [menus, setMenus] = useState<IntelligentMenu[]>([]);
  const [options, setOptions] = useState<MenuElaborationOption[]>([]);
  const [selected, setSelected] = useState<IntelligentMenu | null>(null);
  const [draft, setDraft] = useState<MenuInput>(emptyDraft);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<HostAiApiError | null>(null);
  const [message, setMessage] = useState("");

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [menuResponse, elaborationResponse] = await Promise.all([
        menusService.list(), menusService.elaborations(),
      ]);
      setMenus(menuResponse.menus);
      setOptions(elaborationResponse.elaboraciones);
    } catch (reason) {
      setError(reason as HostAiApiError);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, []);

  function edit(menu: IntelligentMenu) {
    setSelected(menu);
    setDraft({
      nombre: menu.nombre,
      estado: menu.estado,
      comensales: menu.comensales,
      observaciones: menu.observaciones,
      version: menu.version,
      secciones: menu.secciones.map((section) => ({
        nombre: section.nombre,
        elaboraciones: section.elaboraciones.map((item) => ({
          elaboracion_id: item.elaboracion_id,
          cantidad: item.cantidad,
        })),
      })),
    });
    setMessage("");
  }

  function updateSection(index: number, changes: Partial<MenuInput["secciones"][number]>) {
    setDraft((current) => ({
      ...current,
      secciones: current.secciones.map((section, currentIndex) =>
        currentIndex === index ? { ...section, ...changes } : section
      ),
    }));
  }

  function addElaboration(sectionIndex: number) {
    const first = options[0];
    if (!first) return;
    const section = draft.secciones[sectionIndex];
    updateSection(sectionIndex, {
      elaboraciones: [...section.elaboraciones, { elaboracion_id: first.id, cantidad: 1 }],
    });
  }

  async function save() {
    setSaving(true);
    setMessage("");
    try {
      const response = selected
        ? await menusService.update(selected.id, { ...draft, version: selected.version })
        : await menusService.create(draft);
      setSelected(response.menu);
      edit(response.menu);
      setMenus((current) => {
        const exists = current.some((item) => item.id === response.menu.id);
        return exists
          ? current.map((item) => item.id === response.menu.id ? response.menu : item)
          : [...current, response.menu];
      });
      setMessage("Menú guardado y costes recalculados por el backend.");
    } catch (reason) {
      setMessage((reason as HostAiApiError).message);
    } finally {
      setSaving(false);
    }
  }

  async function archive() {
    if (!selected) return;
    setSaving(true);
    try {
      await menusService.archive(selected.id, selected.version);
      setSelected(null);
      setDraft(emptyDraft());
      setMessage("Menú archivado.");
      await load();
    } catch (reason) {
      setMessage((reason as HostAiApiError).message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <><BibliotecaNav /><LoadingState label="Cargando menús..." /></>;
  if (error) return <><BibliotecaNav /><ErrorState title="No se pudieron cargar los menús." detail={error.message} /></>;

  return <section>
    <BibliotecaNav />
    <header className="page-header">
      <div><p className="eyebrow">Biblioteca Culinaria</p><h2>Menús inteligentes</h2></div>
      <button type="button" onClick={() => { setSelected(null); setDraft(emptyDraft()); }}>Nuevo menú</button>
    </header>
    <p>Los menús referencian elaboraciones existentes. Recetas, escandallos y costes permanecen en la Biblioteca.</p>
    <div className="menu-workspace">
      <aside aria-label="Listado de menús">
        <h3>Menús</h3>
        {!menus.length ? <p>No hay menús creados.</p> : menus.map((menu) => <button
          className={selected?.id === menu.id ? "active" : ""}
          key={menu.id}
          onClick={() => edit(menu)}
          type="button"
        >
          <strong>{menu.nombre}</strong>
          <span>{menu.estado} · v{menu.version}</span>
          <span>{formatMoney(menu.coste_total)} · {formatMoney(menu.coste_por_comensal)}/comensal</span>
        </button>)}
      </aside>
      <div className="menu-editor">
        <h3>{selected ? "Editar menú" : "Crear menú"}</h3>
        <label>Nombre
          <input aria-label="Nombre del menú" value={draft.nombre} onChange={(event) => setDraft({ ...draft, nombre: event.target.value })} />
        </label>
        <div className="menu-editor-row">
          <label>Estado
            <select aria-label="Estado del menú" value={draft.estado} onChange={(event) => setDraft({ ...draft, estado: event.target.value as MenuState })}>
              <option value="BORRADOR">Borrador</option><option value="ACTIVO">Activo</option><option value="ARCHIVADO">Archivado</option>
            </select>
          </label>
          <label>Comensales
            <input aria-label="Comensales" min="1" type="number" value={draft.comensales} onChange={(event) => setDraft({ ...draft, comensales: Number(event.target.value) })} />
          </label>
        </div>
        {draft.secciones.map((section, sectionIndex) => <fieldset key={`${section.nombre}-${sectionIndex}`}>
          <legend>Sección {sectionIndex + 1}</legend>
          <input aria-label={`Nombre sección ${sectionIndex + 1}`} value={section.nombre} onChange={(event) => updateSection(sectionIndex, { nombre: event.target.value })} />
          {section.elaboraciones.map((item, itemIndex) => <div className="menu-editor-row" key={`${item.elaboracion_id}-${itemIndex}`}>
            <select aria-label={`Elaboración ${sectionIndex + 1}-${itemIndex + 1}`} value={item.elaboracion_id} onChange={(event) => updateSection(sectionIndex, {
              elaboraciones: section.elaboraciones.map((value, index) => index === itemIndex ? { ...value, elaboracion_id: event.target.value } : value),
            })}>
              {options.map((option) => <option key={option.id} value={option.id}>{option.nombre}</option>)}
            </select>
            <input aria-label={`Cantidad ${sectionIndex + 1}-${itemIndex + 1}`} min="0.01" step="any" type="number" value={item.cantidad} onChange={(event) => updateSection(sectionIndex, {
              elaboraciones: section.elaboraciones.map((value, index) => index === itemIndex ? { ...value, cantidad: Number(event.target.value) } : value),
            })} />
            <button type="button" onClick={() => updateSection(sectionIndex, { elaboraciones: section.elaboraciones.filter((_, index) => index !== itemIndex) })}>Quitar</button>
          </div>)}
          <button disabled={!options.length} type="button" onClick={() => addElaboration(sectionIndex)}>Añadir elaboración</button>
        </fieldset>)}
        <button type="button" onClick={() => setDraft({ ...draft, secciones: [...draft.secciones, { nombre: "Nueva sección", elaboraciones: [] }] })}>Añadir sección</button>
        <label>Observaciones<textarea aria-label="Observaciones del menú" value={draft.observaciones} onChange={(event) => setDraft({ ...draft, observaciones: event.target.value })} /></label>
        {selected ? <div className="menu-cost-summary">
          <strong>Coste automático</strong>
          <span>Total: {formatMoney(selected.coste_total)}</span>
          <span>Por comensal: {formatMoney(selected.coste_por_comensal)}</span>
          {selected.incidencias.map((issue, index) => <p className="draft-warning" key={`${issue.tipo}-${index}`}>{issue.detalle || issue.tipo}</p>)}
        </div> : null}
        <div className="menu-actions">
          <button disabled={saving} type="button" onClick={() => void save()}>{saving ? "Guardando..." : "Guardar menú"}</button>
          {selected && selected.estado !== "ARCHIVADO" ? <button disabled={saving} type="button" onClick={() => void archive()}>Archivar menú</button> : null}
        </div>
        {message ? <p role="status">{message}</p> : null}
      </div>
    </div>
  </section>;
}

function formatMoney(value: number) {
  return new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR" }).format(value || 0);
}
