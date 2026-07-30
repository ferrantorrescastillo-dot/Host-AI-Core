import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { HostAiApiError } from "../../api/client";
import { bibliotecaService } from "../../services/bibliotecaService";
import type { ElaboracionDetalle, IngredienteReceta } from "../../types/biblioteca";
import { BibliotecaNav } from "../components/BibliotecaNav";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

const tabs = [
  "resumen", "receta", "escandallo", "ficha-tecnica",
  "produccion", "documentos", "menus-eventos", "historial",
];

export function ElaboracionDetailPage() {
  const { elaboracionId = "" } = useParams();
  const [params, setParams] = useSearchParams();
  const [item, setItem] = useState<ElaboracionDetalle | null>(null);
  const [error, setError] = useState<{ message: string; status?: number } | null>(null);

  useEffect(() => {
    setItem(null);
    setError(null);
    bibliotecaService.detail(elaboracionId)
      .then((response) => setItem(response.elaboracion))
      .catch((reason: Error) => setError({
        message: reason.message,
        status: reason instanceof HostAiApiError ? reason.statusCode : undefined,
      }));
  }, [elaboracionId]);

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
    <Link to="/biblioteca/elaboraciones">← Volver a Elaboraciones</Link>
    <header>
      <p className="eyebrow">{item.codigo}</p>
      <h2>{item.nombre}</h2>
      <p>{item.categoria || "Sin categoría"} · {statusLabel(item.estado)}</p>
      <p>{yieldText(item)} · Coste total: {money(item.coste_total, "Coste no disponible")}</p>
    </header>
    <nav className="library-tabs" aria-label="Secciones de la elaboración">
      {tabs.map((value) => <button
        className={tab === value ? "active" : ""}
        key={value}
        onClick={() => setParams({ tab: value })}
      >{tabLabel(value)}</button>)}
    </nav>

    {tab === "resumen" && <Summary item={item} />}
    {tab === "receta" && <Recipe item={item} />}
    {tab === "escandallo" && <Costing item={item} />}
    {tab === "ficha-tecnica" && <TechnicalSheet item={item} />}
    {tab === "produccion" && <Production item={item} />}
    {tab === "documentos" && <Documents item={item} />}
    {tab === "menus-eventos" && <MenusEvents item={item} />}
    {tab === "historial" && <History item={item} />}
  </section>;
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

function Recipe({ item }: { item: ElaboracionDetalle }) {
  if (!item.tiene_receta) return <Section title="Receta"><p>No hay una receta estructurada disponible para esta elaboración.</p></Section>;
  return <Section title="Receta">
    <dl className="detail-grid">
      <dt>Rendimiento</dt><dd>{yieldText(item.receta)}</dd>
      <dt>Raciones</dt><dd>{item.receta.raciones ?? "No informadas"}</dd>
      <dt>Tiempo total</dt><dd>{item.receta.tiempo_total || "No informado"}</dd>
      <dt>Temperaturas</dt><dd>{valuesText(item.receta.temperaturas, "No informadas")}</dd>
      <dt>Actualización</dt><dd>{dateText(item.actualizado_en)}</dd>
    </dl>
    <IngredientsTable ingredients={item.receta.ingredientes} costing={false} />
    <h4>Procedimiento</h4>
    {item.receta.pasos.length
      ? <ol>{item.receta.pasos.map((step, index) => <li key={index}>{displayValue(step)}</li>)}</ol>
      : <p>{item.receta.procedimiento || "Sin procedimiento estructurado."}</p>}
    {item.receta.observaciones ? <p><strong>Observaciones:</strong> {item.receta.observaciones}</p> : null}
  </Section>;
}

function Costing({ item }: { item: ElaboracionDetalle }) {
  if (!item.escandallo) return <Section title="Escandallo"><p>No hay escandallo asociado.</p></Section>;
  const esc = item.escandallo;
  return <Section title="Escandallo">
    <p>Estado del coste: {statusLabel(esc.estado_coste)}.</p>
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
      <dt>Alérgenos</dt><dd>{sheet.alergenos.length ? sheet.alergenos.join(", ") : "No informados"}</dd>
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
    <RelationList title="Menús" values={item.menus} empty="No hay menús relacionados." />
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
    <thead><tr><th>Ingrediente</th><th>Cantidad</th><th>Unidad</th><th>Merma</th>{costing ? <><th>Precio aplicado</th><th>Coste de línea</th></> : null}<th>Relación</th></tr></thead>
    <tbody>{ingredients.map((ingredient, index) => <tr key={`${ingredient.nombre_original}-${index}`}>
      <td>{ingredient.articulo_id ? <Link to={`/articulos/${encodeURIComponent(ingredient.articulo_id)}`}>{ingredient.nombre_original}</Link> : ingredient.nombre_original}</td>
      <td>{ingredient.cantidad ?? ingredient.cantidad_texto ?? "No informada"}</td>
      <td>{ingredient.unidad || "No informada"}</td>
      <td>{ingredient.merma == null ? "Sin merma registrada" : `${ingredient.merma}%`}</td>
      {costing ? <>
        <td>{ingredient.coste_unitario == null
          ? (ingredient.motivo_sin_coste || "Sin precio vigente")
          : <>{money(ingredient.coste_unitario, "")}{ingredient.unidad_precio ? ` / ${ingredient.unidad_precio}` : ""}<small>{priceOrigin(ingredient.origen_precio)}{ingredient.fecha_precio ? ` · ${dateText(ingredient.fecha_precio)}` : ""}</small></>}</td>
        <td>{ingredient.coste_linea == null ? (ingredient.motivo_sin_coste || "Sin coste") : money(ingredient.coste_linea, "")}</td>
      </> : null}
      <td>{relationLabel(ingredient.estado_relacion)}</td>
    </tr>)}</tbody>
  </table></div>;
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
function relationLabel(value: IngredienteReceta["estado_relacion"]) {
  return value === "relacionado" ? "Relacionado" : value === "coincidencia_dudosa" ? "Coincidencia dudosa" : "Sin relacionar";
}
function priceOrigin(value?: string | null) {
  const labels: Record<string, string> = {
    tarifa_proveedor: "Tarifa de proveedor",
    historico_compras: "Histórico de compras",
    catalogo_articulos: "Catálogo de Artículos",
    no_disponible: "Origen no disponible",
  };
  return labels[value || ""] || value || "Origen no disponible";
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
function yieldText(value: { rendimiento?: number | null; unidad_rendimiento?: string | null }) {
  return value.rendimiento == null ? "Rendimiento no disponible" : `${value.rendimiento} ${value.unidad_rendimiento || ""}`.trim();
}
function valuesText(values: unknown[], empty: string) { return values.length ? values.map(displayValue).join(", ") : empty; }
function displayValue(value: unknown): string {
  if (Array.isArray(value)) return value.map(displayValue).join(", ");
  if (value && typeof value === "object") return Object.entries(value as Record<string, unknown>).map(([key, item]) => `${fieldLabel(key)}: ${displayValue(item)}`).join(" · ");
  return String(value ?? "");
}
function fieldLabel(value: string) { return value.replaceAll("_", " ").replace(/^./, (x) => x.toUpperCase()); }
