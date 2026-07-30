import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { bibliotecaService } from "../../services/bibliotecaService";
import type { ElaboracionDetalle } from "../../types/biblioteca";
import { BibliotecaNav } from "../components/BibliotecaNav";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

export function ElaboracionDetailPage() {
  const { elaboracionId = "" } = useParams();
  const [params, setParams] = useSearchParams();
  const [item, setItem] = useState<ElaboracionDetalle | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { bibliotecaService.detail(elaboracionId).then((x) => setItem(x.elaboracion)).catch((e: Error) => setError(e.message)); }, [elaboracionId]);
  if (error) return <section className="panel"><ErrorState title="No se pudo cargar la elaboración." detail={error} /></section>;
  if (!item) return <LoadingState label="Cargando elaboración..." />;
  const tab = params.get("tab") || "resumen";
  const tabs = ["resumen", "receta", "escandallo", "ficha-tecnica", "produccion", "documentos", "versiones", "menus-eventos"];
  return <section className="panel library-detail"><BibliotecaNav /><Link to="/biblioteca/elaboraciones">← Volver a Elaboraciones</Link>
    <header><p className="eyebrow">{item.codigo}</p><h2>{item.nombre}</h2><p>{item.categoria || "Sin categoría"} · {item.estado} · {item.completitud ?? 0}% completo</p></header>
    <nav className="library-tabs">{tabs.map((x) => <button className={tab === x ? "active" : ""} key={x} onClick={() => setParams({ tab: x })}>{label(x)}</button>)}</nav>
    {tab === "resumen" && <Section title="Resumen"><p>{item.descripcion || "Sin descripción."}</p>{item.pendientes.length ? <p>Datos pendientes: {item.pendientes.join(", ")}.</p> : null}</Section>}
    {tab === "receta" && <Section title="Receta">{item.receta.ingredientes.length ? <table className="catalog-table"><thead><tr><th>Ingrediente</th><th>Cantidad</th><th>Relación</th></tr></thead><tbody>{item.receta.ingredientes.map((x, i) => <tr key={`${x.nombre_original}-${i}`}><td>{x.articulo_id ? <Link to={`/articulos/${encodeURIComponent(x.articulo_id)}`}>{x.nombre_original}</Link> : x.nombre_original}</td><td>{x.cantidad_texto || "—"}</td><td>{x.estado_relacion}</td></tr>)}</tbody></table> : <p>Receta sin ingredientes registrados.</p>}<h4>Procedimiento</h4><p>{item.receta.procedimiento || "Sin procedimiento."}</p></Section>}
    {tab === "escandallo" && <Section title="Escandallo">{item.escandallo ? <dl className="detail-grid"><dt>Coste total</dt><dd>{money(item.escandallo.coste_total)}</dd><dt>Coste por ración</dt><dd>{money(item.escandallo.coste_por_racion)}</dd><dt>Rendimiento</dt><dd>{item.escandallo.rendimiento ?? "—"}</dd><dt>Estado</dt><dd>{item.escandallo.estado || "—"}</dd></dl> : <p>No hay escandallo asociado.</p>}</Section>}
    {tab === "ficha-tecnica" && <Section title="Ficha técnica"><p>{item.ficha_tecnica ? "Ficha técnica estructurada disponible." : "Ficha técnica pendiente de completar."}</p><p>Alérgenos: {item.alergenos.length ? item.alergenos.join(", ") : "No informados"}</p><p>Conservación: {item.conservacion || "No informada"}</p></Section>}
    {tab === "produccion" && <Section title="Producción"><JsonValues value={item.produccion} empty="No hay indicaciones de producción." /></Section>}
    {tab === "documentos" && <Section title="Documentos">{item.documentos.length ? <ul>{item.documentos.map((x) => <li key={x.referencia}>{x.tipo}: {x.nombre}</li>)}</ul> : <p>No hay documentos asociados.</p>}</Section>}
    {tab === "versiones" && <Section title="Versiones">{item.versiones.length ? <p>Versión actual: {item.versiones[0].version}</p> : <p>No hay versionado disponible.</p>}</Section>}
    {tab === "menus-eventos" && <Section title="Menús y eventos"><p>Menús: {item.menus.length ? item.menus.join(", ") : "Sin relaciones"}</p><p>Eventos: {item.eventos.length ? item.eventos.join(", ") : "Sin relaciones"}</p></Section>}
  </section>;
}
function Section({ title, children }: React.PropsWithChildren<{ title: string }>) { return <section className="catalog-section"><h3>{title}</h3>{children}</section>; }
function label(x: string) { return x.split("-").map((v) => v[0].toUpperCase() + v.slice(1)).join(" "); }
function money(value?: number | null) { return value == null ? "—" : `${value.toFixed(2)} €`; }
function JsonValues({ value, empty }: { value: Record<string, unknown>; empty: string }) { const entries = Object.entries(value).filter(([, v]) => v !== null && v !== "" && (!Array.isArray(v) || v.length)); return entries.length ? <dl className="detail-grid">{entries.map(([k, v]) => <><dt key={`${k}-k`}>{label(k.replaceAll("_", "-"))}</dt><dd key={`${k}-v`}>{Array.isArray(v) ? v.join(", ") : String(v)}</dd></>)}</dl> : <p>{empty}</p>; }
